# Retrieval evaluation with `kb_reader`

`kb_reader` is a direct PostgreSQL login for evaluating the self-hosted chatbot
knowledge base. It is not a Supabase API role and must never be given either the
service-role JWT or the superuser database URL.

## Blast radius

The credential can:

- connect to the self-hosted `postgres` database through one restricted SSH
  port-forward;
- read `public.kb_docs` and `public.kb_chunks`;
- execute `public.match_corpus(...)` and `public.kb_find_ref(text)`.

It cannot read `auth.users`, profiles, messages, bookmarks, or any other
application table. It cannot insert, update, or delete rows; create permanent or
temporary objects; use `auth` or `storage`; execute another application function;
inherit another database role; or call the service-role-only embed endpoint.

The role is intentionally not exposed through PostgREST, Supavisor, or a new
public database port.

## Connection: restricted SSH forwarding

The selected route is an SSH key restricted in `authorized_keys` to forwarding
only the current `supabase-db` container address on port 5432. It exposes no new
public socket. A forced command prevents that key from opening a shell, and
`permitopen` prevents forwarding to Kong, Studio, or any other container.

The container address can change after a compose restart. That failure mode is
closed: the tunnel stops working until Hein re-reads the address with
`docker inspect` and updates `permitopen`. If any compose service is restarted,
restart `kong` in the same operation because Kong caches container IPs.

The alternatives were rejected:

- Publishing 5432 for one source IP creates an unnecessary network surface, and
  UFW does not govern Docker-published ports. Every firewall change would also
  require a fresh off-box scan to prove the port was not open globally.
- Port 5432 on the host is Supavisor, not PostgreSQL. A plain `kb_reader` login
  there fails with `no tenant identifier`; using `user.tenant` adds pooler
  configuration without improving the privilege boundary.
- A read-only HTTP API duplicates the two existing retrieval RPCs and adds
  another credential-bearing service to operate.

For the initial handoff, Hein generated one dedicated keypair outside the
repository and installed its public half with options equivalent to:

```text
restrict,port-forwarding,permitopen="<supabase-db-ip>:5432",command="echo 'This key is restricted to the kb_reader database tunnel.'" ssh-ed25519 <public-key> zander-kb-reader
```

Zander starts the tunnel:

```bash
ssh -i ~/.ssh/analyzing-islam-kb-reader \
  -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes \
  -N -L 15432:<supabase-db-ip>:5432 deploy@72.60.17.245
```

In a second terminal, read the password without placing it in shell history:

```bash
read -rsp 'kb_reader password: ' KB_READER_PASSWORD
echo
PGPASSWORD="$KB_READER_PASSWORD" \
  psql "host=127.0.0.1 port=15432 dbname=postgres user=kb_reader sslmode=disable"
```

The private SSH key and database password are separate factors. Hein stores the
generated plaintext only in owner-readable files outside this public repository,
imports both into a 1Password item, and gives Zander an expiring one-time share.
The plaintext operator copies are deleted after Zander confirms receipt. Neither
secret is pasted into a commit, issue, pull request, or chat window.

At the first convenient rotation, Zander should generate the replacement keypair
himself and send Hein only its public half. Hein then replaces the restricted
`authorized_keys` entry; the private key never leaves Zander's machine.

## Embeddings: pre-embed the query set

The embed Edge Function remains `service_role` only. Letting `kb_reader` or the
public anon JWT call it would restore a cheap denial-of-service path on the live
2-vCPU VPS.

Instead, Zander maintains a non-secret `retrieval_questions.json`:

```json
{
  "questions": [
    {
      "id": "injeel",
      "question": "What does the site say the Injeel is?"
    }
  ]
}
```

On Hein's authorized machine, the service-role holder pre-embeds the set:

```bash
export SUPABASE_EMBED_URL=https://api.analyzingislam.com/functions/v1/embed
export SUPABASE_SERVICE_ROLE_KEY=...  # operator only; never sent to Zander
python preembed-kb-questions.py \
  retrieval_questions.json retrieval_questions.embedded.json
```

`retrieval_questions.embedded.json` contains questions and 384-dimensional
gte-small vectors, but no credential. It can be sent through the normal project
channel. Zander can edit the questions; Hein reruns this one bounded step.

## Worked retrieval

With the tunnel running and `retrieval_questions.embedded.json` present:

```bash
QUERY_TEXT="$(jq -r '.questions[0].question' retrieval_questions.embedded.json)"
QUERY_VECTOR="$(jq -c '.questions[0].embedding' retrieval_questions.embedded.json)"

read -rsp 'kb_reader password: ' KB_READER_PASSWORD
echo
PGPASSWORD="$KB_READER_PASSWORD" psql \
  "host=127.0.0.1 port=15432 dbname=postgres user=kb_reader sslmode=disable" \
  -v q_text="$QUERY_TEXT" -v q_embedding="$QUERY_VECTOR" <<'SQL'
select title, url, round(score::numeric, 6) as score
from public.match_corpus(
  :'q_text',
  :'q_embedding'::vector,
  5
);
SQL
```

Exact-reference lookup does not need an embedding:

```sql
select title, ref, url
from public.kb_find_ref('Quran 4:34');
```

If evaluation ever appears to require another table, function, schema, or the
service-role key, stop. Expanding `kb_reader` is not an acceptable shortcut;
review the evaluation design instead.
