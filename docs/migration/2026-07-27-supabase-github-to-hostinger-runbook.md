# Migration runbook — GitHub Pages + Supabase Cloud → Hostinger VPS

Date: 2026-07-27
Last revised: 2026-07-27 (post-review — see "Four silent-breakage traps" below)
Status: **Stages 0 and 1 complete. Stage 2 is next and needs a VPS.**

> **If you have read an earlier copy of this file, re-read Stage 3b and Stage 4.**
> Two claims in the original were wrong — the anon key is not a JWT, and
> `--no-privileges` silently drops every GRANT — and two further traps were missed.
> Corrections are marked inline.

## What this migrates

| From | To |
|---|---|
| GitHub Pages (static site, 989 pages, 746MB) | nginx on a Hostinger VPS |
| Supabase Cloud Postgres | Self-hosted Postgres (Docker) |
| Supabase Cloud Auth (GoTrue) | Self-hosted GoTrue |
| Supabase Cloud REST API (PostgREST) | Self-hosted PostgREST |
| Supabase Cloud Storage (avatars) | Self-hosted Storage |
| Supabase Cloud Realtime | **Nothing — unused, see below** |
| Cloudflare DNS → GitHub IPs | Cloudflare DNS → VPS IP |

**Realtime is not used by the site.** Verified by grep: zero `.channel()` calls
anywhere under `site/`. The community and messenger front ends that once used it were
deleted in commit `19456d24 "Remove community feature entirely"`. You may drop the
Realtime container from the self-hosted stack — one fewer service to run, monitor and
patch. Its database tables still restore, harmlessly, so the feature can come back
later.

**Not migrated:** the domain registration itself. You never touch your registrar.
Only Cloudflare DNS changes.

## The one principle

**Nothing is decommissioned until its replacement is proven in production.**

The old stack (GitHub Pages + Supabase Cloud) keeps running throughout. The entire
new stack is built and tested in parallel. The migration is a single DNS change that
takes ~30 seconds and is reversible in ~5 minutes.

Every stage below ends with a **Verify** step. Do not proceed past a failed verify.

## Established facts (already checked — do not re-derive)

- DNS is managed at **Cloudflare**. Nameservers `dell.ns.cloudflare.com`,
  `zahir.ns.cloudflare.com`.
- Five records matter: four `A` records on the apex → `185.199.108.153`,
  `185.199.109.153`, `185.199.110.153`, `185.199.111.153`; one `CNAME` on `www` →
  `zander1798.github.io`.
- **TTL is already 300s** (Cloudflare "Auto" for DNS-only records). No TTL change
  needed, no 24-hour wait. Rollback reaches everyone in ~5 minutes.
- Cloudflare proxy is **off** (grey cloud) — GitHub's real IPs are visible through it.
- **No MX records.** No email on this domain, so DNS changes cannot break mail.
- Only **one site file** hardcodes the Supabase URL: `site/assets/js/config.js` line 6.
  Everything else reads `window.SUPABASE_CONFIG`. (`backup-supabase.py` also contains
  the project ref, but it is a local script, never shipped to the browser.)
- **`config.js` needs BOTH lines changed** — the URL *and* the key. The key is not a
  JWT; see trap 2 below.
- The Supabase CLI's `storage` command has **`ls` only, no `cp`** — file migration
  goes over HTTP.
- **Realtime is unused** (zero `.channel()` calls in `site/`). The front end calls
  GoTrue, PostgREST and Storage only.

## Four silent-breakage traps found before starting

Each one passes the verification this runbook would otherwise run, and fails later.
All four are handled in-line below.

1. **Avatar AND banner URLs are absolute and point at the old project.**
   `auth.js:382` (banner) and `:426` (avatar) both call
   `storage.from("avatars").getPublicUrl(path)`, which returns a full
   `https://cndmksrilytnpgstvmxb.supabase.co/...` URL. That string is written into
   `profiles.banner_url` (via `updateProfile` at `:386`) and `profiles.avatar_url`
   (at `:430`). **Both columns are confirmed affected, not suspected.** After cutover
   these still resolve — because the old project is deliberately still running — and
   break the day it is deleted. Fixed in Stage 6, **re-run after Stage 10a**.

2. **The API key is not a JWT, so "reuse the secret and nobody is logged out" is
   ~~unproven~~ — SETTLED 2026-07-27: it cannot work. Plan for the logout.**
   `config.js:7` holds `sb_publishable_9rJKQFSBSA12YijYfGtD5g_7h4WD8wa` —
   one segment, no dots, no `eyJ` prefix. That is Supabase's newer publishable-key
   format, **not** a legacy JWT anon key. So `config.js` needs both lines changed,
   not one.

   **The signing-scheme question is now answered empirically, no dashboard check
   required.** The project's public JWKS endpoint,
   `https://cndmksrilytnpgstvmxb.supabase.co/auth/v1/.well-known/jwks.json`,
   returns:

   ```json
   {"keys":[{"alg":"ES256","kty":"EC","crv":"P-256","use":"sig",
             "kid":"eee256ab-8d14-4704-8040-9ee7ff92d7a3", ...}]}
   ```

   An **ES256 elliptic-curve key pair** — asymmetric JWT signing keys, not a legacy
   HS256 shared secret. Self-hosted GoTrue signs HS256 from `JWT_SECRET` and cannot
   reproduce an ES256 signature from a cloud-managed private key.

   **Therefore: all 6 users are logged out at cutover and log in once.** Accounts and
   passwords are unaffected. Take the second row of Stage 1d's table, not the first.
   Tell the owner in advance so it reads as expected rather than as a fault.

3. **`config.js` diverges between repo and server, and any content deploy silently
   reverts it.** Stage 9c edits it on the VPS; Stage 8a's `rsync --delete` overwrites
   it; `.github/workflows/pages.yml` auto-deploys on any push touching `site/**`.
   Deploy a content change and the server silently points back at Supabase Cloud —
   which still works, so nobody notices, while new user data lands in the old
   database. Fixed in Stage 9c by committing the change immediately, plus an rsync
   `--exclude`. **This is the likeliest of the four to fire**, because pushing a
   content update is the most routine thing that happens to this repo.

4. **`pg_dump --no-privileges` drops every GRANT, and a row-count check cannot see
   it.** RLS policies survive a `pg_dump`; GRANTs do not. The schema has 10+ explicit
   grants, including `grant execute on function public.is_creator() to anon,
   authenticated` (`analytics.sql:27` — the admin-dashboard gate). The restore can
   produce a perfect row-count diff while PostgREST returns permission-denied. Fixed
   in Stage 4d.

---

## Baseline row counts (captured 2026-07-27 — Stage 4 must match these exactly)

| Table | Rows | | Table | Rows |
|---|---:|---|---|---:|
| `auth.users` | **6** | | `public.shared_builds` | 5 |
| `auth.identities` | 6 | | `public.community_members` | 4 |
| `auth.sessions` | 10 | | `public.community_posts` | 2 |
| `auth.refresh_tokens` | 73 | | `public.communities` | 2 |
| `public.profiles` | 5 | | `public.community_join_requests` | 2 |
| `public.pageviews` | 858 | | `public.post_comments` | 8 |
| `storage.objects` | 26 | | `public.post_votes` | 1 |
| `storage.buckets` | 5 | | `public.bookmarks` | 1 |
| `public.admins` | 1 | | `public.notes` | 1 |
| `public.quiz_progress` | 1 | | `public.friendships` | 1 |
| `public.search_queries` | 1 | | `public.direct_threads` / `direct_messages` | 1 / 1 |

26 of 52 tables carry data. Total dump 401KB — this is a small database, so restores
are fast and mistakes are cheap to redo.

## Stage 0 — Local tooling

On your Windows machine.

- [ ] Install PostgreSQL **client tools only**
  - postgresql.org/download/windows → installer
  - On **Select Components**, untick everything except **Command Line Tools**.
    You do not want a local Postgres server.
- [ ] Reopen the terminal

**Verify:**
```bash
pg_dump --version
psql --version
```
Both must print a version. If "not recognised", add the install's `bin` directory to
PATH (typically `C:\Program Files\PostgreSQL\17\bin`).

---

## Stage 1 — Full backup from Supabase Cloud

Read-only. Nothing changes on the live site.

### 1a. Get the connection string

Supabase dashboard → **Connect** (top bar) → **Session pooler** tab.

> Use **Session pooler**, not Transaction pooler. `pg_dump` needs session-level
> features and the transaction pooler fails partway through. Session pooler also
> works over IPv4; the direct connection may be IPv6-only.

**Never paste this string into a chat, commit, or screenshot — it contains your
database password.**

### 1b. Dump the database

```bash
pg_dump --clean --if-exists --quote-all-identifiers --no-owner --no-privileges \
  --schema=public --schema=auth --schema=storage \
  "SESSION_POOLER_URL" \
  > supabase-backup-$(date +%Y%m%d).sql
```

The three schemas each matter:
- `public` — profiles, bookmarks, notes, highlights, quiz progress, builds,
  shared_builds, shared_entries, community, messenger, friendships, pageviews,
  search_queries, admins
- `auth` — **your users and their password hashes. Omit and everyone loses their
  account.**
- `storage` — file metadata (not the files themselves; see 1c)

**Verify:**
```bash
ls -lh supabase-backup-*.sql
grep -c "CREATE TABLE" supabase-backup-*.sql      # expect ~20+
grep -c "COPY \|INSERT INTO" supabase-backup-*.sql # expect > 0
grep -c "auth\.users" supabase-backup-*.sql        # MUST be > 0
```
If `auth.users` is 0, the auth schema did not dump — stop and fix before continuing.

### 1c. Download the storage files

> **There are FOUR buckets with files, not one.** `avatars` (16), `community-icons`
> (2), `community-banners` (2), `community-post-images` (6) — 26 objects, 3.8MB.
> A fifth bucket, `dm-attachments`, exists but is empty. All five are `public = t`,
> so plain HTTP fetch works with no auth.
>
> **⚠ CRLF trap — this will bite on every stage that writes a file with `psql.exe`.**
> The Windows `psql.exe` writes files with CRLF line endings. Feed such a file into
> a `while read` loop and every value carries a trailing `\r`, which silently
> corrupts URLs and filenames. The first attempt here failed all 26 downloads for
> exactly this reason while the URLs themselves were fine (verified HTTP 200).
> **Always pipe through `tr -d '\r'` after any `psql.exe > file` redirect.**

```bash
PGPASSWORD='PASSWORD' psql -h aws-0-eu-west-1.pooler.supabase.com -p 5432 \
  -U postgres.cndmksrilytnpgstvmxb -d postgres -At \
  -c "select bucket_id || '/' || name from storage.objects" \
  > storage-paths.txt

tr -d '\r' < storage-paths.txt > tmp && mv tmp storage-paths.txt   # CRLF fix — required

BASE="https://cndmksrilytnpgstvmxb.supabase.co/storage/v1/object/public"
mkdir -p storage-backup
while IFS= read -r p; do
  [ -z "$p" ] && continue
  curl -sfL --create-dirs -o "storage-backup/$p" "$BASE/$p" || echo "FAILED: $p"
done < storage-paths.txt
```

**Verify:** file count matches row count, and no `FAILED:` lines.
```bash
grep -c '' storage-paths.txt          # expect 26
find storage-backup -type f | wc -l   # must match
du -sh storage-backup                 # expect ~3.8MB
```

**Actual result 2026-07-27:** 26/26 downloaded, 0 failed, 3.8MB.

### 1d. Record the JWT secret — signing scheme ALREADY DETERMINED

> **✅ ANSWERED 2026-07-27 — this project uses ASYMMETRIC signing keys (ES256).**
> No dashboard check needed. The public JWKS endpoint
> `/auth/v1/.well-known/jwks.json` returns an EC P-256 key
> (`kid eee256ab-8d14-4704-8040-9ee7ff92d7a3`, `alg ES256`). Verify yourself in one
> command if you want — it needs no credentials:
> ```bash
> curl -s https://cndmksrilytnpgstvmxb.supabase.co/auth/v1/.well-known/jwks.json
> ```
> **Take the second row of the table below. Sessions will not survive. Plan the
> re-login rather than trying to prevent it.**

Dashboard → **Settings → API**.

- [ ] Copy the **JWT Secret** somewhere safe (password manager, not a file in the
      repo). Stage 3 needs it.
- [ ] ~~Also record which signing scheme this project uses.~~ Already determined —
      see the box above.

The scheme decides whether Stage 3b's "everyone stays logged in" mitigation can work
at all. For this project it cannot:

| Scheme | Consequence of reusing the secret |
|---|---|
| Legacy shared HS256 secret | Self-hosted GoTrue can validate existing tokens. Sessions likely survive. |
| Asymmetric signing keys | Self-hosted GoTrue signs HS256 with `JWT_SECRET`. Existing access tokens will **not** validate. Plan for sessions to end. |

Either way the 73 restored `auth.refresh_tokens` rows give clients a chance to
recover silently on their next refresh. Treat that as a *maybe*, verify at Stage 9d,
and if the project is on asymmetric keys, tell the six users to expect one re-login
rather than letting it surprise them.

- [ ] Also copy the current **publishable/anon key** from this page for reference. You
      will be **replacing** it in `config.js` with the self-hosted `ANON_KEY`, not
      reusing it.
- [ ] Copy the backup, the storage folder and `storage-paths.txt` somewhere off this
      PC — cloud drive or external disk.

---

## Stage 2 — Provision and harden the VPS

### 2a. Buy the VPS

Hostinger **KVM**, not shared hosting. Shared cannot run Postgres or Docker.

- **RAM: 8GB minimum**, 16GB recommended. Supabase self-hosted wants 8GB for
  production, and the chatbot's embedding model lands on the same box later.
- **OS: Ubuntu 24.04 LTS**
- Note the **IPv4 address** — call it `VPS_IP` below.

### 2b. First login and hardening

```bash
ssh root@VPS_IP

adduser deploy
usermod -aG sudo deploy

mkdir -p /home/deploy/.ssh
# paste your public key into /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys
```

Disable password login — `/etc/ssh/sshd_config`:
```
PermitRootLogin no
PasswordAuthentication no
```
```bash
systemctl restart ssh
```

**Verify — in a NEW terminal, before closing this one:**
```bash
ssh deploy@VPS_IP        # must succeed
ssh root@VPS_IP          # must be refused
```
Keep the original session open until the new one works, or you can lock yourself out.

### 2c. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Note: Supabase's Kong gateway listens on 8000 and Studio on 3000. **Do not open
those to the internet** — nginx will reverse-proxy to them locally.

### 2d. Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy
# log out and back in for the group to apply
```

**Verify:** `docker run --rm hello-world`

---

## Stage 3 — Self-hosted Supabase

### 3a. Fetch and configure

```bash
git clone --depth 1 https://github.com/supabase/supabase
mkdir -p ~/supabase-selfhost
cp -r supabase/docker/* ~/supabase-selfhost/
cd ~/supabase-selfhost
cp .env.example .env
```

> The self-host setup changes between releases. Read
> https://supabase.com/docs/guides/self-hosting/docker alongside this runbook and
> prefer its current instructions where they differ.

**Before going further, record two things from `docker-compose.yml`:**

- [ ] The pinned **GoTrue / `supabase/gotrue` image tag**. Stage 4e needs it, and it
      is the single most likely cause of a failed auth restore.
- [ ] Whether you are keeping the **`realtime`** service. The site makes zero
      `.channel()` calls, so you may comment it out. If you do, also drop its entry
      from the Kong config so the gateway does not route to a dead upstream.

**Optionally also add `pgvector` now.** The chatbot's Phase 1 needs it, and enabling
the extension on a database with 401KB of data is trivial today and fiddlier once the
site is live on it. `create extension if not exists vector;` — the Supabase Postgres
image already ships the binary.

### 3b. Set the secrets in `.env`

**`JWT_SECRET` — paste the value from Stage 1d, not a new one.**

This gives existing sessions their best chance of surviving cutover. **It is not a
guarantee** — whether it works depends on the signing scheme you recorded at Stage 1d.
Re-read that table now if you skipped it. Reusing the secret costs nothing and can
only help, so do it regardless.

> ### ⚠ Correction to an earlier draft — read this
>
> An earlier version of this runbook said the existing `ANON_KEY` and
> `SERVICE_ROLE_KEY` "remain valid, because those are themselves JWTs signed with that
> secret", making `config.js` a one-line change. **That is wrong for this project.**
>
> `config.js:7` holds `sb_publishable_9rJKQFSBSA12YijYfGtD5g_7h4WD8wa` — a single
> segment, no dots, no `eyJ` prefix. It is a **publishable key**, not a JWT, and it is
> meaningless to the self-hosted stack.
>
> **Use the `ANON_KEY` that this `.env` generates.** `config.js` is a two-line change:
> URL *and* key. Do not carry the old key across.

Also set:
- `POSTGRES_PASSWORD` — a new strong password
- `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD` — for Supabase Studio
- `SITE_URL=https://analyzingislam.com`
- `API_EXTERNAL_URL=https://api.analyzingislam.com`
- `SUPABASE_PUBLIC_URL=https://api.analyzingislam.com`
- **`ADDITIONAL_REDIRECT_URLS=https://new.analyzingislam.com/**`** — required, see below

Record the generated `ANON_KEY` and `SERVICE_ROLE_KEY` from this `.env`. Stage 9c
needs the `ANON_KEY`. The `SERVICE_ROLE_KEY` never leaves the server.

> **Why `ADDITIONAL_REDIRECT_URLS` matters at Stage 9.** `auth.js:180` and `:208` build
> their redirect targets from `location.origin`:
>
> ```js
> redirectTo: new URL("reset-password.html", location.origin + location.pathname)
> ```
>
> On the staging domain that resolves to `https://new.analyzingislam.com/reset-password.html`,
> which does **not** match `SITE_URL`. GoTrue rejects redirect targets that are not
> allow-listed, so **password reset and email confirmation will fail at Stage 9d for a
> reason that looks like broken SMTP but isn't.** Add the staging domain here now. You
> can remove it after Stage 10.

### 3c. Start

```bash
docker compose up -d
docker compose ps
```

**Verify:** every container `running` / `healthy`. Investigate any restart loop
before continuing — `docker compose logs <service>`.

---

## Stage 4 — Restore the database

### 4a. Copy the dump up

```bash
scp supabase-backup-*.sql deploy@VPS_IP:~/
```

### 4b. Restore

```bash
cat supabase-backup-*.sql | docker exec -i supabase-db \
  psql -U postgres -d postgres
```

Expect some errors on roles and extensions that already exist — those are normal.
Errors mentioning **your** tables are not.

### 4c. Verify row counts against cloud — the critical check

Run the same query against both and compare.

```sql
select schemaname, relname, n_live_tup
from pg_stat_user_tables
where schemaname in ('public','auth','storage')
order by schemaname, relname;
```

On cloud:
```bash
psql "SESSION_POOLER_URL" -f rowcounts.sql > counts-cloud.txt
```
On the VPS:
```bash
docker exec -i supabase-db psql -U postgres -d postgres -f - < rowcounts.sql > counts-vps.txt
```

**Verify:** `diff counts-cloud.txt counts-vps.txt` — must be empty.
Pay closest attention to `auth.users`, `public.profiles`, `public.bookmarks`,
`public.notes`. **Do not proceed on a mismatch.**

(`public.highlights` exists — `supabase/highlights.sql` — but is empty, so it will not
appear in `pg_stat_user_tables` output. Its absence from the diff is expected, not a
failure.)

> ### ⚠ A clean row-count diff does NOT mean the restore is good
>
> This check proves the **data** arrived. It cannot see **permissions**, and the dump
> was taken with `--no-privileges`. Do Stage 4d before you believe this stage passed.

### 4d. Re-apply the schema files — silent-breakage fix #4

`pg_dump --no-privileges` omits every `GRANT`. RLS policies survive a dump; grants do
not. The schema depends on at least ten explicit grants, including:

- `supabase/analytics.sql:27` — `grant execute on function public.is_creator() to anon, authenticated` — **this is the admin-dashboard gate**
- `supabase/profile-community-extensions.sql:156` — `grant select on public.public_profiles to anon, authenticated`
- `supabase/friendships.sql:154`, `supabase/profile-extensions.sql:89`,
  `supabase/messenger-schema.sql:185` and `:208`, and others

Without them the database has every row in the right place and the browser gets
`permission denied`. Row counts will not tell you.

Copy the schema directory up and replay all 18 files:

```bash
scp -r supabase/ deploy@VPS_IP:~/schema/
```
On the VPS, in filename order:
```bash
for f in ~/schema/*.sql; do
  echo "=== $f"
  docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=0 < "$f"
done 2>&1 | tee ~/schema-replay.log
```

The files are written to be re-runnable (`create table if not exists`,
`create or replace function`, `add column if not exists`, and grants, which are
idempotent). **Expect — and ignore — errors of the form `policy "..." already
exists`**, because `create policy` has no `if not exists` form. Anything else in
`schema-replay.log` deserves a read.

**Verify — at the API level, not just in psql.** This is the check that would have
caught the missing grants:

```bash
ANON='<ANON_KEY from ~/supabase-selfhost/.env>'

# anon read of a view that should be publicly selectable
curl -s -w '\n-> %{http_code}\n' \
  -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
  "http://localhost:8000/rest/v1/public_profiles?select=username&limit=1"

# the admin-dashboard RPC — must not fail on its grant
curl -s -w '\n-> %{http_code}\n' \
  -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
  -H "Content-Type: application/json" -d '{}' \
  "http://localhost:8000/rest/v1/rpc/is_creator"
```
Both must return 2xx. A `401`, `403` or a body containing `permission denied for
function` means the grants did not land — do not proceed.

### 4e. If the auth restore fights you — GoTrue version skew

You are restoring a Supabase **Cloud** `auth` schema into a **self-hosted** GoTrue
pinned to whatever tag you recorded at Stage 3a. Cloud generally runs a newer GoTrue.
When `auth.schema_migrations` records migrations the pinned GoTrue does not know
about, the usual symptoms are:

- the `supabase-auth` container restart-looping at startup
- log lines about migrations failing, or a dirty/unknown migration version
- login returning 500 while the database itself looks perfectly healthy

This stage either preserves or destroys all 6 accounts, so do not improvise. In
rough order of preference:

1. **Bump GoTrue** in `docker-compose.yml` to a tag at or above what Cloud used, then
   `docker compose up -d auth`. Usually sufficient on its own.
2. **Let GoTrue own its own schema.** Restore `public` and `storage` first, start the
   stack so GoTrue creates a clean `auth` schema at its own version, then load *only
   the auth table data* (not the DDL, not `auth.schema_migrations`) from the dump.
3. **Last resort — recreate the six accounts by hand** via the Admin API and have
   users reset their passwords. Six accounts makes this survivable. Note it loses the
   password hashes, so warn the users first.

**Do not** hand-edit `auth.schema_migrations` to make an error go away. That produces
an auth server that starts and then misbehaves subtly.

**Verify:** `docker compose ps` shows `supabase-auth` healthy and *stable* — check it
twice, sixty seconds apart, to catch a restart loop. Then `select count(*) from
auth.users;` must return **6**.

---

## Stage 5 — Restore storage files

> **Restore all four buckets, not just `avatars`.** An earlier draft of this stage
> copied `storage-backup/avatars` only, contradicting Stage 1c which correctly found
> **four** buckets holding files: `avatars` (16), `community-icons` (2),
> `community-banners` (2), `community-post-images` (6).
>
> The three community buckets are currently orphaned — the front end that displayed
> them was deleted in commit `19456d24` — so skipping them breaks nothing visible
> today. Restore them anyway: it is 3.8MB total, `storage.objects` has 26 rows that
> should have 26 matching files, and if the community feature ever returns you will
> not be hunting for images that quietly never made the trip.

```bash
scp -r storage-backup deploy@VPS_IP:~/
```
On the VPS — copy every bucket directory, not one:
```bash
for b in avatars community-icons community-banners community-post-images; do
  [ -d ~/storage-backup/$b ] && docker cp ~/storage-backup/$b \
    supabase-storage:/var/lib/storage/stub/stub/$b
done
```

The exact container path depends on the storage backend configured in `.env`
(`STORAGE_BACKEND=file`). Check `docker exec supabase-storage ls /var/lib/storage`
and place files to match the structure already there.

**Verify:** total file count matches Stage 1c's 26, and one avatar loads in a browser
via the new API URL.
```bash
docker exec supabase-storage sh -c 'find /var/lib/storage -type f | wc -l'   # expect 26
```

---

## Stage 6 — Rewrite the avatar AND banner URLs (silent-breakage fix #1)

Existing rows point at the old project. Rewrite them to the new host.

```sql
-- inspect first
select id, avatar_url from public.profiles
where avatar_url like '%supabase.co%' limit 10;

-- count what will change
select count(*) from public.profiles where avatar_url like '%cndmksrilytnpgstvmxb.supabase.co%';

-- rewrite
update public.profiles
set avatar_url = replace(avatar_url,
      'https://cndmksrilytnpgstvmxb.supabase.co',
      'https://api.analyzingislam.com')
where avatar_url like '%cndmksrilytnpgstvmxb.supabase.co%';
```

**`banner_url` is affected too — this is confirmed, not conditional.** `auth.js:382`
resolves a public URL exactly like the avatar path and `:386` writes it to
`profiles.banner_url`. Rewrite it as well:

```sql
update public.profiles
set banner_url = replace(banner_url,
      'https://cndmksrilytnpgstvmxb.supabase.co',
      'https://api.analyzingislam.com')
where banner_url like '%cndmksrilytnpgstvmxb.supabase.co%';
```

Do the same sweep on the community tables. They are orphaned (no front end since
commit `19456d24`) but the rows are still there and cost nothing to fix:

```sql
update public.communities
set icon_url   = replace(icon_url,   'https://cndmksrilytnpgstvmxb.supabase.co', 'https://api.analyzingislam.com'),
    banner_url = replace(banner_url, 'https://cndmksrilytnpgstvmxb.supabase.co', 'https://api.analyzingislam.com')
where icon_url like '%cndmksrilytnpgstvmxb.supabase.co%'
   or banner_url like '%cndmksrilytnpgstvmxb.supabase.co%';
```

**Verify:** nothing anywhere still references the old host, and an avatar renders on
the staging site at Stage 9.

```sql
select 'profiles.avatar_url' src, count(*) from public.profiles where avatar_url like '%cndmksrilytnpgstvmxb%'
union all select 'profiles.banner_url',   count(*) from public.profiles    where banner_url like '%cndmksrilytnpgstvmxb%'
union all select 'communities.icon_url',  count(*) from public.communities where icon_url   like '%cndmksrilytnpgstvmxb%'
union all select 'communities.banner_url',count(*) from public.communities where banner_url like '%cndmksrilytnpgstvmxb%';
```
Every count must be **0**.

---

## Stage 7 — Auth email (SMTP)

> **⚠ SMTP IS BLOCKING, NOT A FINISHING TOUCH — verified 2026-07-27.**
>
> `https://cndmksrilytnpgstvmxb.supabase.co/auth/v1/settings` returns
> **`"mailer_autoconfirm": false`**, meaning **email confirmation is REQUIRED** on
> this project. Until SMTP works on the new server, **no signup can complete at
> all** — the confirmation mail never arrives and the account stays unconfirmed.
> Password reset is equally dead.
>
> Do not schedule this stage after cutover, and do not let Stage 9's signup test be
> the thing that discovers it. Verify with a real signup and a real password reset.
>
> Same endpoint, same check, no credentials needed:
> ```bash
> curl -s https://cndmksrilytnpgstvmxb.supabase.co/auth/v1/settings >   -H "apikey: sb_publishable_9rJKQFSBSA12YijYfGtD5g_7h4WD8wa"
> ```
>
> Two further settings from it, to mirror on the new server:
> - `"disable_signup": false` — signups are open
> - **Email is the only auth provider.** Every OAuth provider is `false`, so there
>   are no external redirect URLs to migrate. (`ADDITIONAL_REDIRECT_URLS` is still
>   needed for the staging domain — that is a different concern.)


Self-hosted GoTrue sends nothing until SMTP is configured. Password reset and email
confirmation silently do nothing without this.

In `.env`:
```
SMTP_ADMIN_EMAIL=analyzingislam2026@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=analyzingislam2026@gmail.com
SMTP_PASS=<Gmail App Password, not your account password>
SMTP_SENDER_NAME=Analyzing Islam
```

Gmail requires an **App Password** (Google Account → Security → 2-Step Verification →
App passwords). Your normal password will not work.

```bash
docker compose down && docker compose up -d
```

**Verify — actually do this, don't assume:** trigger a real password reset from the
staging site in Stage 8 and confirm the email arrives.

---

## Stage 8 — Static site + nginx

### 8a. Deploy the files

```bash
sudo mkdir -p /var/www/analyzingislam
sudo chown -R deploy:deploy /var/www/analyzingislam
```
From your PC:
```bash
rsync -avz --delete --exclude='assets/js/config.js' \
  "site/" deploy@VPS_IP:/var/www/analyzingislam/
```

> **The `--exclude` is the fix for trap 3. Do not drop it before Stage 12.**
>
> Without it, every content deploy overwrites the server's `config.js` and silently
> points the live site back at Supabase Cloud — which keeps working, because the old
> project is deliberately still running, while new user data lands in the wrong
> database.
>
> **Why not just commit the new URL to the repo instead?** Because GitHub Pages
> deploys from the repo on every push to `site/**`, and Pages is your rollback target.
> A repo whose `config.js` points at the VPS gives you a rollback that fails the same
> way the thing you are rolling back from failed. The repo must keep pointing at
> Supabase Cloud for as long as the rollback window is open. **The divergence is
> correct and intentional; it was simply unprotected.** It is resolved at Stage 12,
> when rollback is abandoned.
>
> Consequence to remember: while the exclude is in place, a genuine change to
> `config.js` must be copied up by hand.

`site/` is **746MB** (435MB `assets/`, 178MB `read-external/`, 74MB `read/`). The
first sync takes a while; later ones are incremental and quick. Run it inside `tmux`
or `screen` so a dropped SSH session does not kill it halfway.

### 8b. nginx — must replicate GitHub Pages' URL behaviour

GitHub Pages serves `/about` and `/about.html` interchangeably. nginx does not by
default, and 989 pages of internal links depend on it.

`/etc/nginx/sites-available/analyzingislam`:
```nginx
server {
    listen 80;
    server_name analyzingislam.com www.analyzingislam.com;
    root /var/www/analyzingislam;
    index index.html;

    # Pages-compatible: try the extensionless form too
    location / {
        try_files $uri $uri.html $uri/ =404;
    }

    error_page 404 /404.html;
}

server {
    listen 80;
    server_name api.analyzingislam.com;

    location / {
        proxy_pass http://localhost:8000;   # Kong
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/analyzingislam /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**Verify:** `curl -I http://VPS_IP/` returns 200, and `curl -I http://VPS_IP/about`
returns 200 (not 404) — that proves the extensionless routing works.

---

## Stage 9 — Staging test (the stage that catches everything)

### 9a. Staging DNS

In Cloudflare, add two records pointing at the VPS. **Do not touch the existing
apex or www records.**

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | `new` | `VPS_IP` | DNS only |
| A | `api` | `VPS_IP` | DNS only |

### 9b. Certificates for staging

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d new.analyzingislam.com -d api.analyzingislam.com
```

### 9c. Point the staging site at the new backend

On the VPS only — **deliberately not in the repo yet**, because GitHub Pages still
serves production from the repo and is your rollback target. See the note at Stage 8a.

```bash
sudo nano /var/www/analyzingislam/assets/js/config.js
```

**Change both lines:**

```js
window.SUPABASE_CONFIG = {
  url: "https://api.analyzingislam.com",
  anonKey: "<the ANON_KEY from ~/supabase-selfhost/.env>",
};
```

> **Do not keep the existing `anonKey`.** An earlier draft said to leave it as-is
> because "it should still validate, since the JWT secret was reused". It will not.
> The current key is `sb_publishable_…` — a publishable key, not a JWT — and the
> self-hosted stack has never heard of it. Replace it now rather than debugging a
> confusing 401 later.

**Post-deploy check — run this after every rsync during the migration window.** It is
two seconds and it is the thing that catches trap 3 if the exclude is ever lost:

```bash
curl -s https://new.analyzingislam.com/assets/js/config.js | grep -o 'url: "[^"]*"'
```
Must print `url: "https://api.analyzingislam.com"`. If it prints the
`cndmksrilytnpgstvmxb` URL, the exclude was dropped — restore the file and fix the
rsync before doing anything else.

### 9d. Test matrix — every one, on `https://new.analyzingislam.com`

**Static site**
- [ ] Home, catalog, a category page, an entry page, a dossier
- [ ] Read pages: Quran, a hadith collection, Bible
- [ ] Extensionless URL (`/about`) resolves — proves Stage 8b
- [ ] Goat skins, favicon, sitemap.xml, robots.txt
- [ ] Mobile viewport
- [ ] `config.js` serves the **new** URL and the **new** key — proves trap 3 is held

**Auth** — the highest-risk group
- [ ] **Sign up** a brand-new test account
- [ ] **Log in** as an existing account — proves the auth data migrated (Stage 4e)
- [ ] **Password reset — email actually arrives and the link works.** Proves Stage 7
      (SMTP) *and* the `ADDITIONAL_REDIRECT_URLS` entry from Stage 3b. If the mail
      arrives but the link is rejected, that is the redirect allow-list, not SMTP.
- [ ] **Were you logged out?** Note whether a session that was live before cutover
      survived. This is the Stage 1d signing-scheme question answered empirically —
      record the answer either way.

**Data**
- [ ] Bookmark an entry; confirm it appears on Saved
- [ ] Create a highlight and a note
- [ ] Quiz progress saves
- [ ] Build editor: create and share a build; open the share link signed out

**Profiles and storage**
- [ ] Change username
- [ ] **Upload a new avatar** and a new banner
- [ ] **Existing avatars and banners render** — proves Stage 6

**Permissions** — proves Stage 4d
- [ ] Admin dashboard loads for the owner account
- [ ] Admin dashboard is **refused** for a non-admin account (test both directions —
      a dashboard that loads for everyone is a failure, not a pass)
- [ ] Anonymous pageview tracking still writes
- [ ] Contact form (FormSubmit — external, should be unaffected)

**Do not proceed to cutover until every box is ticked.** This is where problems are
free to fix.

> **Removed from this matrix:** earlier drafts listed "Community pages" and
> "Messenger — send a message, confirm realtime delivery". **Those features no longer
> exist** — commit `19456d24 "Remove community feature entirely"` deleted 19 community
> JS modules and 5 community pages, and there is no messenger front end. There is
> nothing to test and no Realtime in use. If you find yourself hunting for these
> pages, stop: they are gone by design. Their database tables remain and restore
> harmlessly.

---

## Stage 10 — Cutover

Total elapsed: about a minute.

### 10a. Final data sync

Users may have written data since Stage 1. Re-dump and restore so nothing is lost.

```bash
# fresh dump from cloud
pg_dump --clean --if-exists --quote-all-identifiers --no-owner --no-privileges \
  --schema=public --schema=auth --schema=storage \
  "SESSION_POOLER_URL" > final-sync.sql

scp final-sync.sql deploy@VPS_IP:~/
```
On the VPS:
```bash
cat final-sync.sql | docker exec -i supabase-db psql -U postgres -d postgres
```
The re-restore undoes two earlier stages. **Re-run both, in this order:**

1. **Re-run Stage 4d** — the dump is still `--no-privileges` and the restore still
   uses `--clean --if-exists`, so it drops and recreates the objects and **the grants
   are lost again**. Replay the schema files and re-run the two `curl` permission
   checks.
2. **Re-run Stage 6** — the fresh restore reintroduces the old absolute avatar and
   banner URLs. Run the full four-table verification query; every count must be 0.

Skipping either silently undoes work you already verified, which is exactly the class
of failure this runbook exists to prevent.

**Verify:** row counts match again, both `curl` permission checks return 2xx, and the
Stage 6 verification query returns all zeros.

### 10b. Flip DNS

Cloudflare → DNS → Records:

1. **Delete** the four apex `A` records pointing at `185.199.*`
2. **Add** one `A` record: name `@`, content `VPS_IP`, **DNS only**
3. **Edit** the `www` CNAME: change content from `zander1798.github.io` to
   `analyzingislam.com`

**Verify** (from your PC, ~2 minutes later):
```bash
nslookup analyzingislam.com 1.1.1.1     # must show VPS_IP
curl -I https://analyzingislam.com
```

### 10c. Certificate for the live domain

```bash
sudo certbot --nginx -d analyzingislam.com -d www.analyzingislam.com
```

### 10d. Smoke test live

Repeat the Stage 9d matrix against `https://analyzingislam.com`.

### ROLLBACK

If anything is wrong: in Cloudflare, restore the four `185.199.*` A records and set
`www` back to `zander1798.github.io`. Live again within ~5 minutes (300s TTL).
The old stack was never touched.

---

## Stage 11 — Make it survivable

Do these within 24 hours of cutover. You now own what Supabase used to do.

### 11a. Automated backups

```bash
mkdir -p ~/backups
cat > ~/backup.sh <<'EOF'
#!/bin/bash
set -e
STAMP=$(date +%Y%m%d-%H%M)
docker exec supabase-db pg_dump -U postgres -d postgres \
  --schema=public --schema=auth --schema=storage \
  > ~/backups/db-$STAMP.sql
tar czf ~/backups/storage-$STAMP.tar.gz -C /var/lib/docker/volumes . 2>/dev/null || true
find ~/backups -name '*.sql' -mtime +14 -delete
EOF
chmod +x ~/backup.sh
crontab -e   # add:  0 3 * * * /home/deploy/backup.sh
```

**A backup on the same box is not a backup.** Add off-box copying — rclone to a
cloud drive, or `scp` to your PC on a schedule.

**Verify:** run `~/backup.sh` by hand; confirm a non-empty file appears.

### 11b. Restart on failure

```bash
# in docker-compose.yml, every service should carry:
restart: unless-stopped
```

### 11c. Uptime alert

Point a free monitor (UptimeRobot or similar) at `https://analyzingislam.com` and
`https://api.analyzingislam.com/rest/v1/` so you learn about outages from an alert,
not from a user.

---

## Stage 12 — Decommission (two weeks after cutover, not before)

Reaching this stage means **you are giving up the rollback path**. Everything below
assumes that is a deliberate decision, not a drift.

- [ ] Confirm two weeks of clean operation
- [ ] Confirm backups have been running and one has been **test-restored** — an
      untested backup is a hope, not a backup

**Then close the `config.js` divergence — these three go together, in this order:**

- [ ] Retire the Pages deploy first: update `.github/workflows/pages.yml` to rsync to
      the VPS instead, or delete it. Do this **before** the next item, so committing
      the new config cannot trigger a Pages deploy.
- [ ] Commit the `config.js` change to the repo — **both lines**, URL and key. Until
      now it has existed only on the server, deliberately (see Stage 8a).
- [ ] **Remove the `--exclude='assets/js/config.js'` from the rsync command**, and
      from any deploy script you wrote. Repo and server now agree, so the exclude is
      no longer protecting anything — it is just a trap for the next person, who will
      change `config.js`, deploy, and watch nothing happen.

- [ ] Remove `site/CNAME` and disable GitHub Pages
- [ ] Verify the live site still serves the correct `config.js` after the first
      post-Stage-12 deploy. This is the last chance for trap 3 to bite.
- [ ] **Only now** consider pausing the Supabase Cloud project. Keep the Stage 1
      backup permanently regardless.

> **Before pausing Supabase Cloud, do one final check for absolute URLs:**
> ```sql
> select count(*) from public.profiles
> where avatar_url like '%cndmksrilytnpgstvmxb%' or banner_url like '%cndmksrilytnpgstvmxb%';
> ```
> Must be 0. If anyone uploaded an avatar between the Stage 10a sync and now — before
> the client was pointed at the new host — this catches it. Zero here is what makes
> deleting the old project safe.

---

## Known gotchas

| Trap | Consequence | Handled in |
|---|---|---|
| New JWT secret | Everyone logged out at cutover | Stage 3b |
| **Assuming the anon key is a JWT** | **Auth 401s; `config.js` needs both lines changed** | **Stage 1d, 3b, 9c** |
| **`--no-privileges` drops all GRANTs** | **Row counts pass, PostgREST returns permission-denied** | **Stage 4d, re-run at 10a** |
| **GoTrue version skew on auth restore** | **Auth container restart-loops; 6 accounts at risk** | **Stage 3a, 4e** |
| **`config.js` clobbered by a content deploy** | **Live site silently writes to the OLD database** | **Stage 8a exclude + 9c check** |
| Absolute avatar **and banner** URLs | Images break when old project is deleted | Stage 6, re-run at 10a |
| Staging domain not in `ADDITIONAL_REDIRECT_URLS` | Password reset fails, looks like broken SMTP | Stage 3b |
| No SMTP | Password reset silently does nothing | Stage 7 |
| nginx default routing | Extensionless links 404 across 989 pages | Stage 8b |
| Transaction pooler for pg_dump | Dump fails partway | Stage 1a |
| Dump omits `auth` schema | Every user account lost | Stage 1b |
| Only `avatars` restored, not all 4 buckets | 10 orphaned files silently absent | Stage 5 |
| Final sync skipped | Data written during migration lost | Stage 10a |
| Avatar rewrite **or grant replay** not repeated after final sync | Verified fixes silently undone | Stage 10a |
| Backups only on the VPS | One disk failure loses everything | Stage 11a |
| `--exclude` left in place after Stage 12 | Future `config.js` changes never deploy | Stage 12 |
| Supabase project deleted early | No rollback | Stage 12 |

## Open questions

1. **VPS not yet purchased** at time of writing — Stage 2a is the first blocker and
   nothing downstream can be tested without it.
2. **Which JWT signing scheme the Cloud project uses** — legacy shared HS256 secret,
   or asymmetric signing keys. This decides whether Stage 3b's "everyone stays logged
   in" mitigation can work at all. **Answer it at Stage 1d, from the dashboard, before
   relying on it.** The presence of an `sb_publishable_…` key suggests the project is
   on the newer API-key system, which makes asymmetric signing plausible — but that is
   an inference, not a verified fact.
3. **Whether existing sessions survive cutover.** Follows from (2). Answered
   empirically at Stage 9d — the test matrix now asks you to record it either way.
   Six users, so a forced re-login is survivable if you warn them.
4. **Whether the pinned self-hosted GoTrue can accept the Cloud auth schema.** Cannot
   be tested without the VPS. Contingencies are at Stage 4e.
5. **Whether Supabase's default privileges backfill any of the dropped GRANTs.** They
   may, for tables in `public`. Stage 4d does not depend on the answer — it replays
   the schema files regardless, which is cheap insurance either way.

## Resolved — previously open, now settled

- ~~`banner_url` may or may not store absolute URLs~~ — **it does.** `auth.js:382`
  resolves a public URL and `:386` writes it to `profiles.banner_url`. Stage 6 rewrites
  it unconditionally.
- ~~Whether the existing `ANON_KEY` validates against the self-hosted stack~~ —
  **it will not.** It is not a JWT. Replace it at Stage 9c.
- ~~Whether Realtime is needed~~ — **it is not.** Zero `.channel()` calls in `site/`.
