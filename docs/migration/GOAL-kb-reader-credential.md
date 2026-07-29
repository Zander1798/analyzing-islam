# /goal — a scoped credential so Zander can evaluate retrieval

## Mission

Zander needs to iterate on chatbot retrieval quality. He must **not** be given
`SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_DB_URL` — the first bypasses RLS on the
whole production database and the second is the Postgres superuser password. The
live database holds **six real users' bcrypt password hashes, private direct
messages, notes and bookmarks**.

Build him the narrowest credential that lets him do the job, prove it is narrow,
and document how he uses it.

Read first: `docs/migration/CHATBOT-HANDOFF.md`, then `supabase/chatbot-kb.sql`.

## Hard constraints — violating any of these is a failure, not a trade-off

1. **The site is LIVE on this box.** `analyzingislam.com` serves from the VPS
   `72.60.17.245` as of 2026-07-28. Do not restart services casually; if you
   restart anything in the compose stack, **restart `kong` too** — it caches
   container IPs and will 502 otherwise.
2. **Never commit a secret. The repo is PUBLIC.** Grant statements may be
   committed (idempotent, no secret). The role's **password must never** appear in
   a file under the repo, in a commit message, or in a chat window.
3. **Do not touch Supabase Cloud.** It is the rollback target until 2026-08-11.
4. **Do not revoke or move the Cloudflare token.** The apex TLS certificate renews
   via DNS-01 against `/home/deploy/secrets/cloudflare.ini`; removing it breaks
   HTTPS silently around 2026-09-26.
5. **Evidence before claims.** `docker exec` **without `-i` silently discards
   stdin and exits 0** — always `-i` for SQL, and re-query to confirm a write.

## What to build

### 1. A `kb_reader` Postgres role

Exactly enough privilege to evaluate retrieval, and nothing more:

- `LOGIN`, with a strong generated password
- `CONNECT` on the database, `USAGE` on schema `public`
- `SELECT` on `public.kb_docs` and `public.kb_chunks`
- `EXECUTE` on `public.match_corpus(...)` and `public.kb_find_ref(...)`
- **Nothing else.** No write anywhere, no `auth` schema, no `storage` schema, no
  other `public` table, no object creation.

> ⚠ **`match_corpus` and `kb_find_ref` are `SECURITY DEFINER`.** Granting EXECUTE
> to a low-privilege role means the body runs with the *owner's* rights — a
> superuser. Before granting, read both function bodies and confirm they contain
> **no dynamic SQL** and interpolate no caller-supplied string into an executed
> statement. They should be plain SQL with parameters only. If either ever gains
> an `EXECUTE format(...)`, this grant becomes privilege escalation. State
> explicitly in your report that you checked this.

Also check what `public` (i.e. `PUBLIC`) already grants by default — a role can
inherit more than you think. Verify the *effective* privilege, not the statements
you wrote.

### 2. Decide how he actually connects — and justify it

Postgres on the VPS is **not publicly reachable**, deliberately (Stage 3
loopback-binding; the external port scan of 5432/6543 must keep returning
refused). Port 5432 on the host is **Supavisor**, not Postgres — connecting as a
plain `postgres` user there fails with *"no tenant identifier"*. Tunnel to the
`supabase-db` container IP instead, or use Supavisor's `user.tenant` form.

Pick one and say why you rejected the others:

- **SSH key restricted to a port-forward** (`command=""`,
  `permitopen="<db-ip>:5432"` in `authorized_keys`) — no new public surface.
- **Expose 5432 to his IP only** via ufw — simplest for him, but remember **ufw
  does not govern Docker's published ports**, so verify from off-box that you
  have not opened it to the world.
- **A small read-only HTTP endpoint** — most work, least credential handling.

Whatever you choose, **re-run the external port scan afterwards**: 3000, 4000,
5432, 6543, 8000, 8443 must still refuse from off-box; only 22, 80, 443 answer.

### 3. Solve the embedding half

Retrieval needs a query vector, and the `embed` Edge Function is **service-role
only on purpose** — the runtime's `verify_jwt` checks the signature but not the
role, so the anon key (which ships in the public site's `config.js`) reached it
until the function started checking the `role` claim itself. On a 2-vCPU box
that was a free DoS. **Do not simply reopen it.**

Two acceptable routes — choose and justify:

- **Pre-embed a query set.** He supplies `retrieval_questions.json`; you embed the
  questions once and store the vectors where he can read them. Zero new
  credential surface. Best if his loop is "edit questions, re-run".
- **A distinct role claim.** Mint a token whose `role` claim is neither `anon` nor
  `service_role`, and have the embed function accept it *for embedding only*.
  Verify it is useless against PostgREST and Kong before believing it is scoped.

### 4. Documentation

A short section in `docs/migration/CHATBOT-HANDOFF.md` (or its own file) telling
Zander exactly how to connect and run an evaluation, with a worked example. Say
plainly what the credential can and cannot do — he should be able to reason about
blast radius without reading the grants.

## Verification — the negative tests are the point

A positive test ("he can query `kb_docs`") proves almost nothing. **Prove the
things that must be impossible**, connected *as `kb_reader`*, and paste the actual
errors into your report:

```
select * from auth.users limit 1;                  -- must be permission denied
select * from public.profiles limit 1;             -- must be permission denied
select * from public.direct_messages limit 1;      -- must be permission denied
select * from public.bookmarks limit 1;            -- must be permission denied
insert into public.kb_docs (...) values (...);     -- must be permission denied
update public.kb_chunks set embedding = null;      -- must be permission denied
delete from public.kb_docs;                        -- must be permission denied
create table public.zz_probe (x int);              -- must be permission denied
select current_setting('is_superuser');            -- must be off
```

Then prove it *does* work: connect as `kb_reader`, embed a real question, call
`match_corpus`, and get a sensible document back.

Finally, confirm you changed nothing else: `auth.users` still 6,
`public.profiles` still 5, `storage.objects` still 26, and the live site still
returns 200 over HTTPS.

## Stop and ask when

- Anything would change live DNS, the live site, or Supabase Cloud data.
- A real user's account or data would be modified.
- The only way you can see to make it work requires giving Zander more privilege
  than "read the KB, run the two retrieval functions". Say so rather than
  quietly widening the grant — the whole point of the task is the narrowness.

## Deliverable

Committed and pushed: the idempotent grant SQL (no password), the documentation,
and an honest report covering what the credential can do, what you proved it
cannot do, which connection method you chose and why, and how the password
reaches Zander **without** passing through the repo or a chat window.
