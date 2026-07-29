# `kb_reader` live verification — 2026-07-29

## Result

The self-hosted production database now has one direct login named `kb_reader`.
Its effective application-data privilege is exactly:

- `SELECT` on `public.kb_docs` and `public.kb_chunks`;
- `EXECUTE` on `public.match_corpus(text, vector, integer, jsonb, text[], text[])`;
- `EXECUTE` on `public.kb_find_ref(text)`.

It is not a superuser, does not bypass RLS, inherits no role, cannot create
permanent or temporary objects, and has no `auth` or `storage` schema usage.
The password is a 48-character generated secret stored outside the repository
with mode `0600`; PostgreSQL stores a SCRAM-SHA-256 verifier.

No service was restarted. No firewall, DNS, Supabase Cloud data, user row,
corpus row, live-site file, or Cloudflare credential was changed.

## `SECURITY DEFINER` audit

Both allowed functions are owned by `supabase_admin`, which is a superuser, so
their `SECURITY DEFINER` status is material. The live `pg_proc` bodies and the
repository SQL were both inspected.

- Both are `LANGUAGE sql`, use parameters in plain SQL, and contain no dynamic
  `EXECUTE`, `format(...)`, or caller-supplied string executed as SQL.
- `match_corpus` only reads `kb_docs`/`kb_chunks` and uses its parameters as
  query values and filters.
- `kb_find_ref` only reads `kb_docs`; its concatenation builds an `ILIKE`
  pattern value, not SQL text.
- Both now set `search_path = public, pg_temp`. Listing `pg_temp` last prevents
  a caller's temporary object from shadowing the trusted KB tables.

This grant is safe because those bodies have those properties. Adding dynamic
execution later would invalidate the conclusion and requires revoking/reviewing
`kb_reader` before deployment.

## Effective `PUBLIC` privilege

Before installation, `PUBLIC` could execute 18 non-extension application
functions in `public`; nine were superuser-owned `SECURITY DEFINER` functions.
A role-specific `REVOKE` cannot override a `PUBLIC` grant.

The migration preserved execution for `anon`, `authenticated`, and
`service_role`, then removed the legacy `PUBLIC` application-function grants.
Afterward:

```text
public_application_executes = 0
kb_reader_effective_application_functions = 2
```

Extension-owned vector and trigram computational functions retain their normal
`PUBLIC` execution. They are not application RPCs, are not security definers,
and expose no table data. `kb_reader` cannot execute unrelated application
functions such as `is_member(...)` or `search_all(...)`.

The database's default `PUBLIC TEMPORARY` privilege was also material: a direct
per-role revoke would not override it. The migration first preserved that
effective privilege explicitly for every existing role, then removed it from
`PUBLIC`. `kb_reader` consequently cannot create temp objects; every pre-existing
role retained its prior capability.

## Connection decision and SSH restriction

The database remains unexposed. The selected route is a restricted SSH
port-forward to the current `supabase-db` address `172.19.0.3:5432`.

- The dedicated key has fingerprint
  `SHA256:pA0upvmSps8yMoEotbPRi2SG7T8QnQs4bZOA4YOV9fs`.
- A forced command prevents a shell.
- `permitopen="172.19.0.3:5432"` prevents forwarding to any other destination.
- The wrong database password is rejected even through the permitted tunnel.

Actual restriction evidence:

```text
RESTRICTED SSH COMMAND TEST
This key is restricted to the kb_reader database tunnel.

UNAUTHORIZED FORWARD TEST
refused as required

WRONG PASSWORD TEST
FATAL:  password authentication failed for user "kb_reader"
```

Publishing 5432 was rejected because it adds a public surface and UFW does not
govern Docker-published ports. Supavisor was rejected because host port 5432
requires the `user.tenant` form and adds no privilege benefit. A new HTTP
retrieval API was rejected because it duplicates the two reviewed RPCs and adds
another service to operate.

## Embedding decision

The embed Edge Function remains service-role only. Zander receives pre-embedded
query sets produced with `preembed-kb-questions.py`, not an embedding bearer
token and never the service-role key.

Actual boundary and artifact checks:

```text
anonymous embed request: HTTP 403
pre-embed artifact: 1 question, 384 dimensions, no credential fields
```

This route adds no callable credential surface on the live 2-vCPU box. Zander
edits `retrieval_questions.json`; Hein runs the bounded pre-embed step and sends
back the non-secret vector artifact.

## Required negative tests

Every statement below was sent through the restricted tunnel in a PostgreSQL
session authenticated as `kb_reader`.

Identity:

```text
current_user | is_superuser
-------------+-------------
kb_reader    | off
```

Sensitive reads:

```text
select * from auth.users limit 1;
ERROR:  permission denied for schema auth

select * from public.profiles limit 1;
ERROR:  permission denied for table profiles

select * from public.direct_messages limit 1;
ERROR:  permission denied for table direct_messages

select * from public.bookmarks limit 1;
ERROR:  permission denied for table bookmarks
```

Every requested write/object path:

```text
insert into public.kb_docs
  (kind, slug, title, url, body, content_hash)
values
  ('doctrine','zz-probe','probe','/zz-probe','probe','probe');
ERROR:  permission denied for table kb_docs

update public.kb_chunks set embedding = null;
ERROR:  permission denied for table kb_chunks

delete from public.kb_docs;
ERROR:  permission denied for table kb_docs

create table public.zz_probe (x int);
ERROR:  permission denied for schema public

create temporary table zz_temp_probe (x int);
ERROR:  permission denied to create temporary tables in database "postgres"
```

Inherited application execution was also denied:

```text
select public.is_member(1, null);
ERROR:  permission denied for function is_member

select * from public.search_all('probe', 1);
ERROR:  permission denied for function search_all
```

Neither probe table exists after the tests.

## Positive retrieval

The service-role holder pre-embedded the real question:

```text
What does the site say the Injeel is?
```

`kb_reader` then supplied that vector to `match_corpus`. The expected document
ranked first:

```text
title                                           score
----------------------------------------------  --------
What is the Injeel?                             0.016393
"Begets not" and what eternal generation means  0.016129
The Trinity is not three gods                   0.015873
```

Direct KB reading also returned `3` documents, and `kb_find_ref(...)` executed
successfully (the current three-document doctrine smoke corpus has no Quran
reference row, so that lookup correctly returned zero rows).

## Invariants and external reachability

Counts were taken before the role change and again after all negative and
positive tests:

| Object | Before | After |
|---|---:|---:|
| `public.kb_docs` | 3 | 3 |
| `public.kb_chunks` | 3 | 3 |
| `auth.users` | 6 | 6 |
| `public.profiles` | 6 | 6 |
| `storage.objects` | 26 | 26 |

The goal prompt expected five profiles, but the live pre-change baseline was
already six. No profile was added, removed, or modified by this work.

The post-change off-box scan found 22, 80, and 443 reachable. Ports 3000, 4000,
5432, 6543, 8000, and 8443 all timed out (filtered/unreachable); none accepted a
connection. The live site returned:

```text
https://analyzingislam.com/ HTTP 200
```

All eleven Supabase containers remained up; every container with a health check
reported healthy. No restart occurred, so no Kong restart was needed.

## Secret handoff

The chosen human channel is an expiring 1Password one-time share containing the
dedicated private tunnel key and the database password. Until Zander confirms
receipt:

- the private key remains owner-readable at
  `/home/hein/.local/share/analyzing-islam/kb-reader-zander`;
- the password remains mode `0600` at
  `/home/deploy/secrets/kb_reader.password` on the VPS.

Hein deletes both plaintext operator copies after confirmed import. Secret
contents never pass through this repository, a commit message, or a chat window.
