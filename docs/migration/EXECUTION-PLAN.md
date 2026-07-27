# Execution Plan — analyzingislam.com → Hostinger VPS

Date: 2026-07-27
VPS: **72.60.17.245** (`srv1092611`, Ubuntu 24.04.4 LTS, 8GB RAM, 2 vCPU, 96GB disk)
Executor: **Hein's Linux workstation** (`/home/hein/Workspace/analyzing-islam`), root key
auth to the VPS already verified working.
Companion docs: `MIGRATION-PLAN.md` (orientation, traps, rationale) and
`2026-07-27-supabase-github-to-hostinger-runbook.md` (the original runbook). This plan
is the executable version: same stage numbers, VPS filled in, and five verified
corrections folded in (see Appendix).

**The one principle stands: nothing is decommissioned until its replacement is proven
in production.** The old stack keeps running; cutover is one reversible DNS change.
Every stage ends in a Verify. Do not proceed past a failed verify.

Owner actions are marked **[ZANDER]**. Everything else runs from this workstation.

---

## Part A — What Zander must provide (privately — never chat, never the repo)

1. **[ZANDER] Session-pooler connection string** (Supabase dashboard → Connect →
   Session pooler). Fresh dumps are taken from this workstation, so the old Windows
   backup never needs to move. Store it here as
   `~/secrets/analyzingislam/pooler.env` (`chmod 700` the dir, `600` the file):
   ```
   POOLER_URL='postgresql://postgres.cndmksrilytnpgstvmxb:PASSWORD@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
   ```
2. ~~**[ZANDER] JWT secret + signing scheme**~~ — **RESOLVED 2026-07-27, no longer
   needed.** Answered empirically from the project's own public JWKS endpoint:
   ```bash
   curl -s https://cndmksrilytnpgstvmxb.supabase.co/auth/v1/.well-known/jwks.json
   # -> {"keys":[{"alg":"ES256","kty":"EC","crv":"P-256", ... }]}
   ```
   The project signs user access tokens with an **ES256 asymmetric key**, whose
   private half Supabase holds and never exposes. Three consequences:
   - **Reusing the legacy JWT secret cannot preserve sessions** — the entire Stage 3b
     "everyone stays logged in" mitigation is void for this project. Do not chase it.
   - **We therefore do not need Zander's JWT secret at all.** The randomly generated
     `JWT_SECRET` already on the VPS is correct and final. No swap before Stage 4.
   - **Sessions should still survive, by a different mechanism:** refresh tokens are
     opaque **database rows**, not signed tokens. All 79 restore. When a client's
     ES256 access token fails against the self-hosted stack, supabase-js silently
     refreshes, GoTrue looks the refresh token up in the restored table and mints a
     new HS256 token. Expected to be seamless — **verify at Stage 9d, do not assume.**
3. **[ZANDER] Cloudflare API token**, scoped to Zone → DNS → Edit for
   `analyzingislam.com` (dash.cloudflare.com → My Profile → API Tokens). This lets the
   plan do staging DNS, the zero-downtime pre-issued certificate (Stage 9e), and the
   cutover flip without waiting on manual clicks. Fallback: Zander does each DNS edit
   on instruction. Store as `~/secrets/analyzingislam/cloudflare.ini`:
   ```
   dns_cloudflare_api_token = TOKEN
   ```
4. **[ZANDER] Gmail App Password** for `analyzingislam2026@gmail.com` (Google
   Account → Security → 2-Step Verification → App passwords) — Stage 7 SMTP.
5. **[ZANDER]** Keep the existing backup at
   `C:\Users\zande\Documents\analyzingislam-migration` as the permanent archive. It
   never gets committed — the repo is public and it contains password hashes, tokens
   and private messages.

## Part B — Workstation pre-flight (done 2026-07-27)

- [x] VPS reachable, root SSH key auth works from this machine
- [x] `site/` present, 746MB, repo in sync with what Pages serves
- [ ] **pg_dump major version must be ≥ the cloud server's.** Local `pg_dump` is 16.
      After Part A item 1 arrives, check:
      ```bash
      source ~/secrets/analyzingislam/pooler.env
      psql "$POOLER_URL" -tAc 'show server_version;'
      ```
      If it prints 17.x: `sudo apt install postgresql-client-17` and use
      `/usr/lib/postgresql/17/bin/pg_dump` everywhere this plan says `pg_dump`.

RAM note: 8GB meets the Supabase self-host minimum and is fine for this site. The
chatbot's embedding model will want more later — Hostinger KVM plans resize without
reinstalling, so this is a future upgrade, not a blocker.

---

## Stage 2 — Harden the VPS

```bash
ssh root@72.60.17.245

adduser deploy
usermod -aG sudo deploy
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys
```

`/etc/ssh/sshd_config`: set `PermitRootLogin no` and `PasswordAuthentication no`,
then `systemctl restart ssh`.

**Verify — in a NEW terminal before closing this one:**
```bash
ssh deploy@72.60.17.245     # must succeed
ssh root@72.60.17.245       # must be refused
```

Firewall and Docker (as deploy):
```bash
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp
sudo ufw enable && sudo ufw status
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy   # then log out and back in
docker run --rm hello-world
```

> **ufw does NOT protect Docker-published ports** — Docker's iptables rules bypass
> it. The real protection is Stage 3's loopback bindings. Do not skip them.

---

## Stage 3 — Self-hosted Supabase

### 3a. Fetch, then bind every published port to loopback (correction #1)

```bash
git clone --depth 1 https://github.com/supabase/supabase
mkdir -p ~/supabase-selfhost && cp -r supabase/docker/* ~/supabase-selfhost/
cd ~/supabase-selfhost && cp .env.example .env

grep -n -A3 'ports:' docker-compose.yml
```

For **every** host port mapping found (at minimum Kong `8000`/`8443` and Supavisor
`5432`/`6543`; also `4000` if the analytics service publishes it), prefix the host
side with `127.0.0.1:`  — e.g. `"127.0.0.1:8000:8000/tcp"`. nginx proxies to them
locally; nothing needs them public, and without this Postgres password auth is open
to the internet.

Also record from `docker-compose.yml`:
- [ ] the pinned **GoTrue (`supabase/gotrue` / `auth`) image tag** — Stage 4e needs it
- [ ] optionally comment out the **realtime** service (site makes zero `.channel()`
      calls) and remove its route from the Kong config

### 3b. `.env`

- `JWT_SECRET` — **a freshly generated random secret. Do NOT chase the cloud one.**
  Cloud signs with ES256 asymmetric keys (see Part A item 2), so reusing its legacy
  HS256 secret preserves nothing. Mint `ANON_KEY`/`SERVICE_ROLE_KEY` as HS256 JWTs
  (`{"role":"anon"|"service_role","iss":"supabase","iat":…,"exp":…}`) against it.
- **Also randomize `SUPABASE_PUBLISHABLE_KEY` and `SUPABASE_SECRET_KEY`.** The
  `.env.example` ships placeholder values that `volumes/api/kong.yml` registers as
  **live Kong credentials** — leaving them means publicly-known keys authenticate
  against your API the moment it is reachable.
- `POSTGRES_PASSWORD` — new strong password
- `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD`
- `SITE_URL=https://analyzingislam.com`
- `API_EXTERNAL_URL=https://api.analyzingislam.com`
- `SUPABASE_PUBLIC_URL=https://api.analyzingislam.com`
- `ADDITIONAL_REDIRECT_URLS=https://new.analyzingislam.com/**` — without this,
  password reset on staging fails in a way that impersonates broken SMTP
  (`auth.js` builds `redirectTo` from `location.origin`)

Record the generated `ANON_KEY` and `SERVICE_ROLE_KEY`. The site's current key is
`sb_publishable_…` — **not a JWT, meaningless to this stack**. `config.js` is a
two-line change at Stage 9c: URL *and* key. The `SERVICE_ROLE_KEY` never leaves the
server.

### 3c. Start and verify

```bash
docker compose up -d && docker compose ps        # all running/healthy
docker exec supabase-db psql -U supabase_admin -d postgres \
  -c 'create extension if not exists vector;'    # chatbot Phase 1, trivial now
```

**Verify the loopback bindings from the workstation:**
```bash
for p in 8000 8443 5432 6543 4000 3000; do nc -zv -w3 72.60.17.245 $p; done
```
Every one must **fail**. Only 22 (and later 80/443) may answer.

---

## Stage 4 — Restore the database

### 4a. Fresh dump from this workstation

```bash
source ~/secrets/analyzingislam/pooler.env
pg_dump --clean --if-exists --quote-all-identifiers --no-owner --no-privileges \
  --schema=public --schema=auth --schema=storage \
  "$POOLER_URL" > /tmp/claude/supabase-backup-$(date +%Y%m%d).sql

grep -c "auth\.users" /tmp/claude/supabase-backup-*.sql   # MUST be > 0
scp /tmp/claude/supabase-backup-*.sql deploy@72.60.17.245:~/
```

### 4b. Restore **as `supabase_admin`** (correction #2, part 1)

`supabase_admin` is the image's guaranteed superuser; restoring as `postgres` risks
failed drops on tables owned by the service roles.

```bash
cat ~/supabase-backup-*.sql | docker exec -i supabase-db \
  psql -U supabase_admin -d postgres 2>&1 | tee ~/restore.log
grep -iv "already exists\|does not exist" ~/restore.log | grep -i error
```
Role/extension errors are normal. Errors naming **your** tables are not.

### 4b2. Repair `auth`/`storage` ownership and grants (correction #2, part 2)

The dump was `--no-owner --no-privileges`, so recreated tables belong to the restore
user with no grants — but GoTrue runs as `supabase_auth_admin` and storage as
`supabase_storage_admin` (verified in the official compose). Row counts cannot see
this; login 500s can.

```bash
docker exec -i supabase-db psql -U supabase_admin -d postgres <<'SQL'
do $$ declare r record; begin
  for r in select tablename from pg_tables where schemaname='auth' loop
    execute format('alter table auth.%I owner to supabase_auth_admin', r.tablename);
  end loop;
  for r in select sequencename from pg_sequences where schemaname='auth' loop
    execute format('alter sequence auth.%I owner to supabase_auth_admin', r.sequencename);
  end loop;
  for r in select tablename from pg_tables where schemaname='storage' loop
    execute format('alter table storage.%I owner to supabase_storage_admin', r.tablename);
  end loop;
  for r in select sequencename from pg_sequences where schemaname='storage' loop
    execute format('alter sequence storage.%I owner to supabase_storage_admin', r.sequencename);
  end loop;
end $$;
grant usage on schema auth to supabase_auth_admin;
grant usage on schema storage to supabase_storage_admin;
SQL
```

**Verify the service roles can actually read:**
```bash
docker exec supabase-db psql -U supabase_auth_admin -d postgres \
  -c 'select count(*) from auth.users;'          # must print 6, not permission denied
docker exec supabase-db psql -U supabase_storage_admin -d postgres \
  -c 'select count(*) from storage.objects;'     # must print 26
```

### 4c. Row counts vs cloud

Same query both sides, `diff` must be empty (see runbook 4c for the SQL). Baseline:
`auth.users` 6, `auth.refresh_tokens` 73, `public.profiles` 5, `storage.objects` 26,
`public.pageviews` 858. Do not proceed on a mismatch.

### 4d. Replay the schema files (public-schema grants)

> ### ⚠ CORRECTION #6 — "replay all 18 files" is DESTRUCTIVE. Learned the hard way.
>
> `supabase/` is not 18 files of idempotent DDL. Replaying the whole directory on
> 2026-07-27 **deleted a real row and inserted five fake ones**, and the row-count
> check is what caught it:
>
> - **`analytics-verify.sql` is a manual test script, not schema.** It seeds fake
>   pageviews, calls the creator RPCs (the three `ERROR: forbidden` lines are the
>   admin gate working correctly), then cleans up with
>   `delete from public.search_queries where q = 'aisha'`. The database's one real
>   search row *was* `q='aisha'` — `search_queries` went 1 → 0. **Never replay this
>   file.**
> - **`community-schema.sql:684` carries a demo seed block** inserting six
>   communities `on conflict (slug) do nothing`. Five landed: `communities` 2 → 7,
>   and the owner-membership trigger took `community_members` 4 → 9.
>
> **So: exclude `analytics-verify.sql`, and expect the community seed.** Reconcile
> after replaying, then re-check counts — a clean diff is the only proof.

```bash
scp -r supabase/ deploy@72.60.17.245:~/schema-src/
# on the VPS — every file EXCEPT the test script:
for f in ~/schema-src/*.sql; do
  [ "$(basename $f)" = "analytics-verify.sql" ] && { echo "SKIP (test script): $f"; continue; }
  echo "=== $f"
  docker exec -i supabase-db psql -U supabase_admin -d postgres -v ON_ERROR_STOP=0 < "$f"
done 2>&1 | tee ~/schema-replay.log
```

Then remove the demo seed and restore parity (community ids 8 `general` and
9 `warfare` are the only legitimate ones as of this dump — re-derive from the dump
if it has moved):

```bash
docker exec -i supabase-db psql -U supabase_admin -d postgres <<'SQL'
begin;
delete from public.community_members where community_id not in (8,9);
delete from public.communities        where id           not in (8,9);
commit;
select setval('public.communities_id_seq', 9, true);      -- seed advanced it to 15
select setval('public.search_queries_id_seq', 1, true);
SQL
```

`policy "…" already exists` errors during replay are expected; anything else in
`schema-replay.log` deserves a read.
`policy "…" already exists` errors are expected; anything else in the log deserves a
read. Then restart the API layer so no schema cache is stale:

```bash
docker compose restart auth rest storage
```

**Verify at the API level** (the check row counts can't do):
```bash
ANON='<ANON_KEY from .env>'
curl -s -w '\n-> %{http_code}\n' -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
  "http://localhost:8000/rest/v1/public_profiles?select=username&limit=1"
curl -s -w '\n-> %{http_code}\n' -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
  -H "Content-Type: application/json" -d '{}' \
  "http://localhost:8000/rest/v1/rpc/is_creator"
curl -s -w '\n-> %{http_code}\n' "http://localhost:8000/auth/v1/health"
```
All 2xx. A body containing `permission denied` means 4b2/4d did not land.

### 4e. If auth fights you — GoTrue version skew

Symptoms: `supabase-auth` restart-looping, migration errors, login 500 over a healthy
DB. Remedies in order (runbook 4e has detail): bump the GoTrue tag to ≥ Cloud's;
or let GoTrue create a clean `auth` schema and load only table data; last resort,
recreate 6 accounts via the Admin API (loses password hashes — warn users first).
Never hand-edit `auth.schema_migrations`. Check `docker compose ps` twice, 60s apart.

---

## Stage 5 — Storage files via the Storage API (correction #3)

Do **not** `docker cp` flat files: the file backend stores and reads objects at
`bucket/key/version` (verified in storage source), and the restored metadata carries
Cloud's version UUIDs — flat files will 400/404. Re-uploading through the API keeps
disk and metadata consistent. All buckets are public, so downloads need no auth.
Run **on the VPS**:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -At \
  -c "select bucket_id || '/' || name from storage.objects" > ~/storage-paths.txt
# 26 lines expected

SERVICE='<SERVICE_ROLE_KEY from .env>'
CLOUD='https://cndmksrilytnpgstvmxb.supabase.co/storage/v1/object/public'
mkdir -p ~/storage-backup
while IFS= read -r p; do
  [ -z "$p" ] && continue
  curl -sfL --create-dirs -o ~/storage-backup/"$p" "$CLOUD/$p" || { echo "DL-FAILED: $p"; continue; }
  ctype=$(file -b --mime-type ~/storage-backup/"$p")
  curl -sf -X POST "http://localhost:8000/storage/v1/object/$p" \
    -H "Authorization: Bearer $SERVICE" -H "apikey: $SERVICE" \
    -H "x-upsert: true" -H "Content-Type: $ctype" \
    --data-binary @~/storage-backup/"$p" > /dev/null || echo "UP-FAILED: $p"
done < ~/storage-paths.txt
```

**Verify:** no `FAILED` lines, and one avatar serves through the new stack:
```bash
head -1 ~/storage-paths.txt   # take an avatars/ path from the list
curl -s -o /dev/null -w '%{http_code}\n' \
  "http://localhost:8000/storage/v1/object/public/<that-path>"   # 200
```

---

## Stage 6 — Rewrite absolute avatar/banner URLs

Both `profiles.avatar_url` and `profiles.banner_url` are confirmed to hold absolute
`https://cndmksrilytnpgstvmxb.supabase.co/...` URLs; the community tables too. Run
the rewrites and the four-way zero-count verify exactly as runbook Stage 6 (replace →
`https://api.analyzingislam.com`). Every count must end at **0**.

---

## Stage 7 — SMTP

In `.env` (App Password from Part A item 4):
```
SMTP_ADMIN_EMAIL=analyzingislam2026@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=analyzingislam2026@gmail.com
SMTP_PASS=<app password>
SMTP_SENDER_NAME=Analyzing Islam
```
`docker compose down && docker compose up -d`. Verified by a **real** password reset
at Stage 9d — not assumed.

---

## Stage 8 — Static site + nginx

### 8a. Deploy (from the workstation, inside tmux — first sync is 746MB)

```bash
ssh deploy@72.60.17.245 'sudo mkdir -p /var/www/analyzingislam && sudo chown -R deploy:deploy /var/www/analyzingislam'
rsync -avz --delete --exclude='assets/js/config.js' \
  site/ deploy@72.60.17.245:/var/www/analyzingislam/
```

> The `--exclude` is trap-3 protection: the repo's `config.js` must keep pointing at
> Supabase Cloud while GitHub Pages is the rollback target. It stays until Stage 12.
> A genuine `config.js` change must be copied up by hand until then.

### 8b. nginx

Use the runbook 8b config verbatim (apex/www server with
`try_files $uri $uri.html $uri/ =404;` — 989 pages depend on extensionless URLs —
plus the `api.analyzingislam.com` proxy to `http://localhost:8000`).

**Verify:** `curl -I http://72.60.17.245/` → 200 and
`curl -H 'Host: analyzingislam.com' -sI http://72.60.17.245/about` → 200 (not 404).

---

## Stage 9 — Staging proof

### 9a. Staging DNS (Cloudflare, token or [ZANDER])
Add `A new → 72.60.17.245` and `A api → 72.60.17.245`, both DNS-only. **Touch
nothing else.**

### 9b. Staging certs
```bash
sudo apt install certbot python3-certbot-nginx python3-certbot-dns-cloudflare
sudo certbot --nginx -d new.analyzingislam.com -d api.analyzingislam.com
```
(nginx needs a `server_name new.analyzingislam.com` block serving the same root —
add it beside the apex block.)

### 9c. Point the server copy of `config.js` at the new stack — both lines

```js
window.SUPABASE_CONFIG = {
  url: "https://api.analyzingislam.com",
  anonKey: "<ANON_KEY from the VPS .env>",   // NOT the old sb_publishable_ key
};
```
After every rsync during the migration window:
```bash
curl -s https://new.analyzingislam.com/assets/js/config.js | grep -o 'url: "[^"]*"'
# must print https://api.analyzingislam.com — if it prints cndmksri…, the exclude was lost
```

### 9d. Test matrix — every box, on https://new.analyzingislam.com

- [ ] Home, catalog, category, entry, dossier; Quran/hadith/Bible readers
- [ ] Extensionless `/about` resolves; goat skins, favicon, sitemap, robots; mobile
- [ ] `config.js` serves new URL **and** new key
- [ ] Sign up new test account · log in as existing account · **password reset email
      arrives and its link works** (link rejected → redirect allow-list, not SMTP)
- [ ] Note whether a pre-existing session survived (answers the signing-scheme question
      empirically — record it either way)
- [ ] Bookmark, note, highlight, quiz progress; build editor create + share link
      opened signed-out
- [ ] Change username; upload new avatar + banner; **existing avatars/banners render**
- [ ] Admin dashboard loads for owner, **refused** for non-admin (test both ways)
- [ ] Anonymous pageview writes; contact form
- Community/messenger pages: **do not test — they were deleted from the site**
  (commit `19456d24`). Nothing to tick.

### 9e. Pre-issue the LIVE certificate — before any DNS flip (correction #4)

```bash
sudo certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials ~/secrets-cloudflare.ini \
  -d analyzingislam.com -d www.analyzingislam.com
```
Add the 443 server block for apex+www (same root/try_files, plus 80→443 redirect),
`nginx -t && reload`. **Verify without touching DNS:**
```bash
curl --resolve analyzingislam.com:443:72.60.17.245 -sI https://analyzingislam.com/about
# 200 with a valid certificate — the live vhost is proven BEFORE cutover
```
This removes the original runbook's minutes-long TLS-mismatch window at 10b/10c.

---

## Stage 10 — Cutover

### 10a. Final sync — then re-run everything the restore undoes

Freeze content deploys from here to Stage 10d. Fresh dump from the workstation,
restore on the VPS as `supabase_admin` (Stage 4a/4b commands). Then **in order**:

1. Re-run **4b2** (ownership/grants — the fresh `--clean` restore dropped them again)
2. Re-run **4d** (schema replay + the three `curl` checks)
3. Re-run **Stage 6** (URL rewrites; four-way verify all zeros)
4. Re-run **Stage 5's loop** (restored metadata carries Cloud version IDs again, and
   any file uploaded since the last sync exists only in Cloud)
5. `docker compose restart auth rest storage`

**Verify:** row counts match, the three curls return 2xx, Stage 6 query all zeros,
one avatar serves via `https://api.analyzingislam.com`.

### 10b. Flip DNS (Cloudflare, token or [ZANDER])

1. Delete the four apex `A` records (`185.199.108–111.153`)
2. Add `A @ → 72.60.17.245`, DNS-only
3. Edit `www` CNAME: `zander1798.github.io` → `analyzingislam.com`

**Verify (~2 min later):**
```bash
nslookup analyzingislam.com 1.1.1.1        # 72.60.17.245
curl -sI https://analyzingislam.com/about   # 200, valid cert — already installed at 9e
```

### 10c. Smoke test live
Repeat the 9d matrix against `https://analyzingislam.com`, including the `config.js`
curl check against the live domain.

### ROLLBACK
Restore the four `185.199.*` A records, set `www` back to `zander1798.github.io`.
Live again in ~5 minutes (300s TTL). The old stack was never touched.

---

## Stage 11 — Own what Supabase used to do (within 24h)

### 11a. Backups (correction #5)

The storage files live in the **bind mount** `~/supabase-selfhost/volumes/storage`
(not `/var/lib/docker/volumes`), so no root needed and the tar targets the real data:

```bash
mkdir -p ~/backups
cat > ~/backup.sh <<'EOF'
#!/bin/bash
set -euo pipefail
STAMP=$(date +%Y%m%d-%H%M)
docker exec supabase-db pg_dump -U supabase_admin -d postgres \
  --schema=public --schema=auth --schema=storage > ~/backups/db-$STAMP.sql
tar czf ~/backups/storage-$STAMP.tar.gz -C ~/supabase-selfhost/volumes storage
find ~/backups \( -name '*.sql' -o -name '*.tar.gz' \) -mtime +14 -delete
EOF
chmod +x ~/backup.sh
crontab -e   # 0 3 * * * /home/deploy/backup.sh
```

**Verify:** run it by hand; `tar tzf` the archive and see the 26 files;
`grep -c 'auth' db-*.sql` > 0. **A backup on the same box is not a backup** — add an
off-box copy (rclone to a cloud drive, or a nightly pull from this workstation), and
test-restore one before Stage 12.

### 11b/11c. Resilience
Every service `restart: unless-stopped`. Uptime monitor on
`https://analyzingislam.com` and `https://api.analyzingislam.com/auth/v1/health`
(the auth health endpoint returns 200 unauthenticated; `rest/v1/` returns 401
without an apikey and makes a bad probe).

---

## Stage 12 — Decommission (two weeks after cutover, not before)

This is the deliberate abandonment of the rollback path.

- [ ] Two weeks clean; backups running **and one test-restored**
- [ ] Retire the Pages deploy **first**: replace `.github/workflows/pages.yml` with an
      rsync-to-VPS deploy (or delete it) so the next step cannot trigger Pages
- [ ] Commit `config.js` — both lines — to the repo
- [ ] Remove `--exclude='assets/js/config.js'` from the rsync/deploy script
- [ ] Remove `site/CNAME`, disable GitHub Pages
- [ ] First post-Stage-12 deploy: re-check `config.js` on the live site
- [ ] Final absolute-URL sweep (runbook Stage 12 SQL) — must be 0
- [ ] Only now pause the Supabase Cloud project. Keep Zander's Stage 1 backup forever.

---

## Execution log — what actually happened (2026-07-27)

**Stages 2, 3, 4, 5, 6, 8 and 9c are DONE and verified.** Remaining and **blocked only
on two credentials from Zander**: 7 (SMTP — Gmail app password), 9a/9b/9e (staging DNS
+ certs — Cloudflare token), 10 (cutover — Cloudflare), then 11 and 12.

End-to-end through nginx on the VPS, exactly as a browser would hit it: homepage 200,
extensionless `/about` 200, `config.js` 200 serving the self-hosted URL and a
correctly-formatted JWT anon key, `api.` vhost → auth health 200, avatar via the `api.`
vhost 200. Box is comfortable: 1.6GB of 7.8GB RAM, 13GB of 96GB disk.

> **Trap worth remembering: `docker exec` without `-i` silently discards stdin.**
> A heredoc of SQL piped into `docker exec supabase-db psql` (no `-i`) runs psql with
> no input, prints nothing, and **exits 0** — so an `UPDATE` appears to succeed while
> doing nothing. This bit the first Stage 6 attempt; only re-reading a sample row
> caught it. Always `docker exec -i` when feeding SQL, and verify by re-querying.

- **Stage 2 ✅** deploy user + key-only SSH, root login refused, ufw 22/80/443, Docker.
- **Stage 3 ✅** 11 containers healthy. All published ports loopback-bound; external
  scan of 3000/8000/8443/5432/6543 from off-box: all refused. `pgvector` enabled.
  GoTrue `v2.189.0`, Postgres `17.6.1.136` — **same 17.6 major/minor as cloud**.
- **Stage 4 ✅** dump 396K, restored as `supabase_admin`, ownership/grants repaired,
  schema replayed, seed damage reconciled. **All 53 cloud tables match exactly**
  (`auth.users` 6, `refresh_tokens` 79, `profiles` 5, `pageviews` 860,
  `storage.objects` 26). Only VPS-side extras are two empty `storage.iceberg_*`
  tables from the newer storage-api. API checks: `public_profiles` 200,
  `rpc/is_creator` 200, `profiles` 200, anon `pageviews` insert 201, storage 200,
  auth health 200.
- **Stage 5 ✅** all 26 objects across the four buckets re-uploaded through the Storage
  API with `x-upsert: true` (never `docker cp`): 26 uploaded, 0 failed, 26 files on
  disk, 26 `storage.objects` rows — disk and metadata consistent.
- **Stage 6 ✅** absolute-URL sweep run; all four counts (`profiles.avatar_url`,
  `profiles.banner_url`, `communities.icon_url`, `communities.banner_url`) now **0**,
  and a rewritten avatar URL fetches 200 from the self-hosted stack. Note
  `communities.banner_url` did hold one — the community sweep was not optional.
- **Stage 8 ✅** 746MB rsynced with `--exclude config.js`; nginx serving; `/about`
  (extensionless) returns 200.
- **Stage 9c ✅** the exclude means `config.js` was **never copied** to the VPS — the
  site there had no Supabase config at all until it was written by hand. It now points
  at `https://api.analyzingislam.com` with the self-hosted JWT `ANON_KEY`. The repo
  copy still points at Supabase Cloud, deliberately, until Stage 12.

**The GoTrue version-skew risk (old Stage 4e) is closed.** Cloud carried exactly one
migration the pinned GoTrue lacked (`20260625000000`), whose only schema effect is an
additive `custom_claims_allowlist text[] DEFAULT '{}'` column on
`auth.custom_oauth_providers` — a table this site never uses. GoTrue logged
*"Migrations already up to date, nothing to apply"* against the restored cloud schema
and came up healthy. No image bump was needed.

**Environment surprise:** the VPS shipped with **Dokploy** preinstalled — Traefik held
80/443 and an unclaimed admin panel was exposed on `:3000`. Removed with the owner's
approval. Note that `docker swarm leave` broke Docker's embedded DNS for the running
compose stack (Kong could not resolve `auth`, PostgREST could not resolve `db`); a
`docker compose down && up -d` rebuilt the network and everything returned healthy.

---

## Appendix — corrections vs the original runbook (all verified 2026-07-27)

1. **Loopback-bind all Docker-published ports (Stage 3a).** ufw does not govern
   Docker's iptables rules; the stock compose publishes Kong 8000/8443 and Postgres
   5432/6543 on all interfaces. Verified against the official `docker-compose.yml`.
2. **Restore as `supabase_admin` + repair `auth`/`storage` ownership/grants (4b/4b2).**
   All 18 repo schema files grant only `public` objects (verified by grep); GoTrue and
   storage connect as `supabase_auth_admin`/`supabase_storage_admin` (verified in
   compose). Without 4b2, login can 500 over a perfect row-count diff.
3. **Upload storage files via the API, never flat `docker cp` (Stage 5).** The file
   backend reads `bucket/key/version` (verified in storage source); restored metadata
   carries Cloud version UUIDs that flat files can't satisfy.
4. **Pre-issue the live cert via DNS-01 before the flip (Stage 9e).** The original
   order (flip, then certbot) served a mismatched cert to every visitor for several
   minutes and its own verify couldn't pass.
5. **Backup script fixed (11a).** Original tarred `/var/lib/docker/volumes` (wrong
   path — storage is a bind mount), as a user who couldn't read it, with the failure
   swallowed by `|| true`, and never pruned the tars.
6. **"Replay all 18 schema files" is destructive (4d).** `analytics-verify.sql` is a
   test script whose cleanup deletes the real `search_queries` row; and
   `community-schema.sql` carries a six-community demo seed. Proven by row-count diff
   during the real restore, then repaired. Exclude the test script; reconcile the seed.
7. **The cloud project uses ES256 asymmetric signing (Part A item 2, Stage 3b).**
   Proven from its public JWKS endpoint. Reusing the legacy JWT secret cannot keep
   anyone logged in, so the secret is not needed at all; session continuity instead
   rides on the 79 restored refresh-token rows.
8. **`.env.example`'s publishable/secret keys are live Kong credentials (3b).**
   Shipping defaults would let publicly-known keys authenticate. Randomize both.

Plus: every restore is followed by `docker compose restart auth rest storage`
(schema-cache insurance); the final sync re-runs grants, URL rewrites **and** the
storage upload loop; `ADDITIONAL_REDIRECT_URLS` covers the staging domain so password
reset is testable at 9d.
