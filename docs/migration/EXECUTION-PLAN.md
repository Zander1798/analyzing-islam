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

### 9a. Staging DNS — **DONE 2026-07-28, from Zander's Windows PC**

Add `A new → 72.60.17.245` and `A api → 72.60.17.245`, both DNS-only. **Touch
nothing else.**

**The Cloudflare token blocker is cleared.** Zander minted a new token on the correct
account; it is verified working. Executed over the Cloudflare REST API — records
created, zone read back, resolution confirmed on public DNS.

| Item | Value |
|---|---|
| Zone ID | `7136f649b2c92b633c6bcf805721116f` |
| Nameservers | `dell.ns.cloudflare.com`, `zahir.ns.cloudflare.com` — match the recorded pair |
| Token scope | Zone→DNS→Edit **+ Zone→Zone→Read**, single zone `analyzingislam.com`, no IP filter, no expiry |
| Token location (Windows PC) | `~/secrets/cf-analyzingislam.txt`, mode 600 |
| Record `new` | id `803059386b884197f8809daed0b15563`, A → 72.60.17.245, TTL 300, proxied **false** |
| Record `api` | id `837954585e39adb39985bd2afa228484`, A → 72.60.17.245, TTL 300, proxied **false** |

**Verified after the write — the live site was not touched:**

```
total records: 7   (was 5, +2)
A      analyzingislam.com       185.199.108/109/110/111.153   ttl auto   proxied false
A      api.analyzingislam.com   72.60.17.245                  ttl 300    proxied false
A      new.analyzingislam.com   72.60.17.245                  ttl 300    proxied false
CNAME  www.analyzingislam.com   zander1798.github.io          ttl auto   proxied false
APEX UNCHANGED: True     WWW UNCHANGED: True     MX: still none
```

Public resolution: `new.` returns 72.60.17.245 on both 1.1.1.1 and 8.8.8.8; `api.`
returns it on 8.8.8.8 but **1.1.1.1 briefly served NXDOMAIN from its negative cache**
(the zone SOA default TTL is **1800s**, so allow up to 30 minutes). This is cache
staleness, not a missing record — the authoritative read-back above shows both.
**Re-check from the workstation before running 9b**, since certbot's HTTP-01 challenge
needs the name resolving wherever Let's Encrypt's validators look:

```bash
dig +short new.analyzingislam.com @1.1.1.1   # expect 72.60.17.245
dig +short api.analyzingislam.com @1.1.1.1   # expect 72.60.17.245
```

> **[HEIN] The token still has to land on the workstation** for 9b/9e. Overwrite the
> wrong-account file at `~/secrets/analyzingislam/cloudflare.ini` (mode 600) with:
> ```
> dns_cloudflare_api_token = <the new token>
> ```
> Zander has the value; it is deliberately not in this repo. The old file's token had
> 11 zones, none of them this domain — that is what blocked 9a until now.

### 9b. Staging certs — **DONE 2026-07-28**

```bash
sudo certbot --nginx -d new.analyzingislam.com -d api.analyzingislam.com \
  --non-interactive --agree-tos -m ai@velocityfibre.co.za --redirect --no-eff-email
```

| Item | Result |
|---|---|
| Certificate | Let's Encrypt (issuer CN=YE1), SAN covers **both** names, expires 2026-10-26 |
| Validation | full chain verifies from the workstation with **no pinning and no `-k`** (`ssl_verify_result=0`) |
| Redirect | `http://…/about` → **301** → `https://…/about` on both hosts |
| **Renewal** | **`certbot renew --dry-run`: "all simulated renewals succeeded"**; `certbot.timer` enabled and active |
| Apex/www | **untouched** — still port 80 only, zero `ssl_certificate` directives, `/about` returns 200 not 301 |

**Re-ran the whole 9d matrix against the real certificate with validation ON:
50/50 API and 54/54 browser.** The earlier 104/104 was against a self-signed cert
with verification disabled; this is the same matrix with nothing switched off.

> ### ⚠ Two things had to be fixed BEFORE certbot would have behaved
>
> **1. The three hostnames shared one nginx `server` block.** Running
> `certbot --nginx -d new.analyzingislam.com` against that would have attached a
> certificate valid only for `new.` to a block that also answers for
> `analyzingislam.com` and `www` — entangling this stage with Stage 9e's apex
> certificate. Split into three blocks first (apex+www / new. / api.), so certbot
> edits exactly the block it is asked to. `analyzingislam.pre-9b.bak` holds the old
> version.
>
> **2. `api.` proxies `location /` to Kong, so ACME challenges never touch disk** —
> `http://api.analyzingislam.com/.well-known/acme-challenge/test` returns **401**
> from Kong, not 404. `certbot --nginx` survives this because it injects a *regex*
> location block, and regex locations beat prefix locations in nginx's matching
> order. **`--webroot` would have failed here.** Worth remembering at 9e.

> **Certificate Transparency:** issuing this certificate publishes
> `new.analyzingislam.com` and `api.analyzingislam.com` to public CT logs
> permanently. Unavoidable for `api.` (it needs a public certificate anyway) and
> accepted for `new.`.

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

### 9d. Test matrix — **DONE 2026-07-27, 104/104, without DNS**

Executed against `https://new.analyzingislam.com` and `https://api.analyzingislam.com`
— the *real* production origins — by pointing the workstation's `/etc/hosts` at
72.60.17.245 and serving a throwaway self-signed cert. Both were reverted afterwards
(see "Temporary test rig" below). Harnesses: a 50-check API suite and a 54-check
Playwright suite driving real Chromium, so **supabase-js itself** was exercised, not
just curl. Re-run after the Stage 10a rehearsal: still 104/104.

- [x] Home, catalog, arguments, compare, faq, sources, entry, dossier; Quran/hadith/
      Bible/interlinear readers; goat, play, stats, build, login, signup,
      forgot-password, contact, profile, saved — **21 pages, all 200 with real content**
- [x] Extensionless `/about` resolves; sitemap, robots, favicons, webmanifest; custom
      404 returns HTTP 404 *and* renders; mobile 390px with zero horizontal overflow
- [x] `config.js` serves new URL **and** new JWT key, and no longer mentions Cloud
- [x] Sign up (`confirmation_sent_at` set, SMTP path exercised) · **log in** ·
      password-reset link built on the staging host, accepted, establishes a session
- [x] Bookmark, note, highlight, quiz progress, build; share link **opened signed-out**
- [x] Change own username; **cannot** change someone else's; existing avatars and
      banners decode in the browser from the rewritten `api.` URLs
- [x] Admin dashboard **loads for the admin and bounces the non-admin** —
      `creator_kpis()` returns data for one and `403 forbidden` for the other and
      for anon. Tested in both directions, in a real browser.
- [x] Anonymous pageview insert; anon reads of `public_profiles` / `shared_builds`
- Community/messenger pages: not tested — deleted from the site (`19456d24`).

**Two things worth stating plainly, because they are the questions this stage existed
to answer.**

**1. Migrated passwords work.** All six real users carry Cloud-produced `$2a$10$`
bcrypt hashes. We cannot know their passwords, so instead a throwaway user was given
an *externally generated* `$2a$10$` hash — same algorithm, same cost, produced outside
GoTrue — and logging in with it succeeded, while a wrong password was rejected. No
real user's password or data was touched at any point, and every table was verified
back at its exact baseline afterwards.

**2. Session continuity — the ES256 question — had a real defect. See correction #14.**

### 9d-bis. Temporary test rig — added and REVERTED the same session

Recorded so nobody hunts for leftovers, and so this is repeatable:

| Added | Removed |
|---|---|
| `/etc/hosts` on the **workstation**: `72.60.17.245 new. api.` | yes — `new.analyzingislam.com` is NXDOMAIN again |
| `/etc/nginx/sites-{available,enabled}/staging-tls-TEMP` (443 vhosts) | yes |
| `/etc/ssl/analyzingislam-staging-TEMP/` (self-signed, 30d) | yes |

Verified after removal: nothing listens on 443, no nginx config mentions `ssl`, and
no `*analyzingislam*` cert material exists under `/etc/ssl` or `/etc/letsencrypt`.
**Stage 9b/9e certbot therefore starts from a clean slate** — which was the whole
point of not leaving a self-signed cert in the path.

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

### 10a. Final sync — **now a single rehearsed script. Do not do this by hand.**

Freeze content deploys from here to Stage 10d. Then, from the workstation:

```bash
./scripts/stage10a-final-sync.sh            # dump → ship → sync → verify → shred
./scripts/stage10a-final-sync.sh --dry-run  # dump + ship only, no restore
```

**Rehearsed end to end four times on 2026-07-27.** Last two runs: **29s and 31s** on
the VPS, plus ~48s for the dump and ship — call it **under three minutes**, idempotent,
and it exits non-zero rather than half-finishing.

The manual sequence this replaces is preserved below for understanding, but running it
by hand is how this goes wrong: corrections **#11, #12 and #13** are all defects in
that sequence, and all three were found only by rehearsing it. Two of them
(no privileges restored; Kong pointing at a dead container IP) produce a stack that
is broken for *users* while every row count looks perfect.

What the script does, in order — each step verified before the next runs:

0. Preflight: dump has an `auth.users` COPY block and is >100KB; schema sources present
1. **Safety backup of the current state first** — refuses to restore over unbacked-up data
2. Restore as `supabase_admin`; only a documented, asserted set of errors is tolerated
3. Ownership **and privileges** repair (correction #12), verified by role, over TCP
   (correction #11)
4. Schema replay, **excluding `analytics-verify.sql`** by name, always
5. Seed reconcile — derives the real community id set from the fresh dump instead of
   hardcoding "keep 8 and 9", then **fails** if any other table drifted
6. URL rewrite across **every text column in `public`**, not four named ones
7. Restart `auth rest storage` **then `kong`**, and assert Kong resolves storage to
   the current container IP (correction #13)
8. Storage re-upload through the API, then **read every object back** — the POST
   status is what the API claimed; the read-back is what a browser will get
9. Verify: REST, RPC, auth health, storage, zero Cloud URLs, row counts == Cloud

Post-sync, the full 9d matrix was re-run against the result: **104/104**.

> One known behaviour: each run writes a new object version, so the storage directory
> grows (~4MB per run; it was 25MB for 4MB of live data after four rehearsals, on 79GB
> free). Harmless, but do not mistake it for corruption.

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

## Stage 11 — Own what Supabase used to do — **DONE 2026-07-27**

Everything in Stage 11 is implemented, cronned and proven. The scripts are in the
repo (`scripts/vps/`) and deployed to the VPS.

| Item | State | Evidence |
|---|---|---|
| Backup script | `scripts/vps/backup.sh`, cron `03:15` daily | runs in 0.8s; DB 431KB + roles + 26-file storage tar |
| Failure paths | **tested, not assumed** | empty dump → exit 1, `FAIL` in `LAST_RUN`, no `.partial` left; missing bind mount → same |
| Prune | both `*.sql` **and** `*.tar.gz`, 14 days | correction #5 |
| **Test-restore** | `scripts/vps/test-restore.sh`, cron Sunday `03:45` | **55/55 tables, 1245 rows, and 546 schema objects identical** |
| Off-box copy | workstation cron `04:10`, **pull** not push | 60-day retention; warns if the newest copy is >2 days old |
| `restart: unless-stopped` | all 11 containers | verified by inspection |
| **Reboot survival** | **proven** | VPS rebooted; SSH back in ~40s, **11/11 healthy in ~30s, no intervention**; swap, nginx, fail2ban all back |
| Swap | 4GB `/swapfile`, `vm.swappiness=10`, in `/etc/fstab` | survived the reboot |
| `unattended-upgrades` | enabled + active | `20auto-upgrades` present |
| `fail2ban` | enabled + active, `sshd` jail | `fail2ban-client status` |
| External port scan | re-verified **after** the reboot | 3000/4000/5432/6543/8000/8443/9999/2375/2376 all refused; only 22/80/443 answer |

The test-restore is the one that matters most: row counts can match while every index
and RLS policy is missing, so it diffs **schema objects by name** too — 180 indexes,
89 RLS policies, 204 functions, 24 triggers, 1 view, 48 RLS-enabled tables. Zero
missing. **This clears the Stage 12 "one test-restored backup" gate.**

> Uptime monitoring: probe `https://api.analyzingislam.com/auth/v1/.well-known/jwks.json`,
> **not** `/auth/v1/health` — see correction #10.

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

- [x] Backups running **and one test-restored** — cleared 2026-07-27 by
      `scripts/vps/test-restore.sh` (55 tables, 1245 rows, 546 schema objects identical)
- [ ] Two weeks clean on the VPS
- [ ] Confirm `fix/session-continuity-guard` is merged, so the rsync below cannot
      revert the VPS's hand-deployed `auth.js` (see Stage 10's warning)
- [ ] Retire the Pages deploy **first**: replace `.github/workflows/pages.yml` with an
      rsync-to-VPS deploy (or delete it) so the next step cannot trigger Pages
- [ ] Commit `config.js` — both lines — to the repo
- [ ] Remove `--exclude='assets/js/config.js'` from the rsync/deploy script
- [ ] Remove `site/CNAME`, disable GitHub Pages
- [ ] First post-Stage-12 deploy: re-check `config.js` on the live site
- [ ] Final absolute-URL sweep (runbook Stage 12 SQL) — must be 0
- [ ] Only now pause the Supabase Cloud project. Keep Zander's Stage 1 backup forever.

---

## STATUS — 2026-07-27, end of the autonomous session

### What is proven

| Stage | State |
|---|---|
| 2, 3, 4, 5, 6, 7, 8, 9c | done and verified (earlier session) |
| **9d — full test matrix** | **DONE, 104/104, twice** (once before and once after the 10a rehearsal), in a real browser against the production origins, without touching DNS |
| **10a — final sync** | **scripted and rehearsed 4× end to end**, 29–31s, idempotent, self-verifying. Three real defects in the documented procedure found and fixed. |
| **11 — survivability** | **DONE.** Backups cronned, failure paths tested, **backup test-restored** (55 tables / 1245 rows / 546 schema objects identical), off-box copy running, **VPS rebooted and the whole stack returned healthy unattended in ~30s** |
| **12 groundwork** | rsync deploy workflow written to `.github/workflows-staged/`, deliberately **not** enabled |
| **Chatbot Phase 1** | tasks 1–2 landed on the VPS; **the blocker is cleared** — `gte-small` works on the self-hosted edge runtime and semantic retrieval returns the right document |
| Hardening | `unattended-upgrades`, `fail2ban` (sshd jail), 4GB swap; external port scan clean after reboot |

Throughout: **the live site was never touched.** `analyzingislam.com` still resolves
to the four `185.199.*` GitHub Pages IPs, `www` still CNAMEs to `zander1798.github.io`,
and no DNS record was created, edited or deleted anywhere. Supabase Cloud was read
only — `pg_dump` and `psql SELECT`, nothing else. No real user's password, session or
data was modified; after every test run the database was verified back at its exact
baseline across all 17 tracked tables.

### What failed, honestly

1. **Session continuity was half-broken** (correction #14) — the one thing Stage 9d
   existed to answer. A returning user holding a *non-expired* Cloud token gets a UI
   that says signed-in while nothing loads, for up to an hour. Fixed on a branch,
   proven fixed on the VPS, **not merged** — merging deploys to the live site.
2. **The documented Stage 10a would have failed at cutover** in three separate ways
   (corrections #11, #12, #13). All three are now fixed in the script. Worth sitting
   with: every one of them was invisible to a row-count check, and two of them produce
   a stack that is broken for users while every count looks perfect.
3. **The embed Edge Function was reachable with the anon key** (fixed: it now checks
   the role claim itself, because the runtime's `verify_jwt` only checks the
   *signature*, not the role).
4. Nothing else failed. Where a check could not be run, it is listed below rather than
   quietly dropped.

### What could NOT be tested, and why

- **Real email delivery.** The reset link was proven to be built on the correct host,
  accepted, and to establish a session — but nobody read the Gmail inbox. Stage 7
  already proved SMTP separately (real STARTTLS login + a real signup returning
  `confirmation_sent_at`). Test mail went to `analyzingislam2026+migtest-*@gmail.com`,
  the project's own mailbox.
- **A real user's refresh token surviving.** Using one *rotates and revokes* it, which
  would disturb a real person's session. The mechanism was proven end to end on a
  throwaway user instead (rotation is ON: the old row is marked revoked on use).
- **Real cutover DNS behaviour, TLS from a public CA, and CDN/edge caching.** All
  require the Cloudflare token.
- **Contact form delivery** (needs the inbox).
- Avatar upload size *was* a latent 413: the `api.` vhost had no
  `client_max_body_size`, so nginx's 1MB default applied and any decent-sized photo
  would have failed after cutover. **Found and fixed this session** —
  `client_max_body_size 50m;` added to the `api.` block, verified by pushing a 3MB
  object through the vhost (200; previously 413). The Storage API still enforces the
  real per-bucket limit.

### The shortest list of things a human must still do

1. ~~**Get the Cloudflare DNS-edit API token from Zander**~~ — **DONE 2026-07-28.**
   Correct-account token minted, verified active, zone `analyzingislam.com` resolves
   (id `7136f649b2c92b633c6bcf805721116f`). **Stage 9a is executed** — see that stage
   for record ids and the post-write verification. Remaining: **[HEIN]** copy the token
   into `~/secrets/analyzingislam/cloudflare.ini` on the workstation (the file there is
   still the wrong account), then **9b, 9e** and **10** are mechanical.
2. **Decide on `fix/session-continuity-guard`.** Merging it to `main` deploys to the
   live site, so it is a human call. It is a no-op on the live site today. Cutting
   over *without* it means correction #14 happens to real users.

   > ### ⚠ THE VPS COPY OF `auth.js` IS ONE RSYNC AWAY FROM BEING SILENTLY REVERTED
   >
   > The guard was deployed to the VPS by hand so 9d could prove it works. It is
   > **not** on `main`. `site/assets/js/auth.js` is therefore the *only* file where
   > the VPS and the repo differ — confirmed by `rsync --dry-run`.
   >
   > Any Stage 8a rsync (`rsync -avz --delete --exclude='assets/js/config.js' site/ …`)
   > overwrites it with main's unguarded version, and nothing will tell you: the site
   > keeps working, and the breakage only appears at cutover, only for users holding a
   > live Cloud token. **Check it after every rsync until the branch is merged:**
   > ```bash
   > ssh deploy@72.60.17.245 'grep -c reconcileForeignSession /var/www/analyzingislam/assets/js/auth.js'
   > # must print 1
   > ```
   > Merging the branch is what makes this go away permanently. Until then, treat
   > `auth.js` like `config.js`: a hand-managed file on the server.
3. **Rotate the Supabase Cloud database password** after the Stage 10a final sync — it
   was pasted into a chat window.
4. **At cutover**, run `./scripts/stage10a-final-sync.sh`, then flip DNS (10b). Do not
   perform the sync by hand.

Everything else is done, cronned, and proven.

---

## Execution log — what actually happened (2026-07-27)

**Stages 2, 3, 4, 5, 6, 7, 8 and 9c are DONE and verified.** ~~Remaining and blocked on
one credential: 9a/9b/9e and 10 need the Cloudflare DNS-edit API token.~~

**Update 2026-07-28 (from Zander's Windows PC):** the token blocker is cleared and
**Stage 9a is DONE** — `new.` and `api.` both A → 72.60.17.245, DNS-only, apex and
`www` verified untouched. Full detail and record ids under Stage 9a above. Next:
**9b** (one certbot command, once `api.` clears 1.1.1.1's 30-minute negative cache),
then **9e**, then **10**.

- **Stage 7 ✅** SMTP configured against Gmail. Verified in two independent ways: a
  direct `smtplib` STARTTLS login (Gmail accepted the app password), then a **real
  signup through GoTrue** which returned `confirmation_sent_at` and logged
  `user_confirmation_requested` with no SMTP error. Test user deleted afterwards;
  `auth.users` back to **6**. `ENABLE_EMAIL_AUTOCONFIRM=false`, so signups do send mail.

> ### ⚠ CORRECTION #9 — reset links on the staging domain would point at the OLD site
>
> GoTrue logs: *"Request received external host in … Host headers, but the values have
> not been added to GOTRUE_MAILER_EXTERNAL_HOSTS and will not be used."* Unlisted hosts
> are ignored and GoTrue falls back to `SITE_URL`. At Stage 9d that means a password-
> reset email triggered from `new.analyzingislam.com` would carry a link to
> **`analyzingislam.com` — the old GitHub Pages site** — so the tester "receives the
> email, clicks, and lands somewhere that works", proving nothing.
>
> Fixed: `GOTRUE_MAILER_EXTERNAL_HOSTS` added to the auth service, fed by
> `MAILER_EXTERNAL_HOSTS=analyzingislam.com,www.analyzingislam.com,new.analyzingislam.com`.
> Note this is a **different setting** from `ADDITIONAL_REDIRECT_URLS`
> (`GOTRUE_URI_ALLOW_LIST`): the allow-list decides whether a redirect is *permitted*,
> the external-hosts list decides which host the link is *built from*. Stage 9d needs
> both, and they fail in different ways.

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
(schema-cache insurance — but see correction #13, the ordering was wrong); the final
sync re-runs grants, URL rewrites **and** the storage upload loop;
`ADDITIONAL_REDIRECT_URLS` covers the staging domain so password reset is testable
at 9d.

---

## Corrections 10–15 — found by *rehearsing* Stage 10a and by real-browser 9d testing

Corrections 1–8 came from reading the runbook against the official sources.
These six came from running the thing. Each was measured on the VPS.

### 10. `/auth/v1/health` is **not** an unauthenticated endpoint on this stack

Stage 11b says "the auth health endpoint returns 200 unauthenticated". It does not:
Kong's `kong.yml` opens only `/auth/v1/verify`, `/callback`, `/authorize`,
`/.well-known/jwks.json` and the SAML routes. `/auth/v1/health` falls through to the
authenticated `auth-v1` service and returns **401 `{"message":"No API key found in
request"}`**. An uptime monitor pointed at it would alert forever.

Use either `https://api.analyzingislam.com/auth/v1/.well-known/jwks.json` (genuinely
open, 200) or send the `apikey` header. Note the JWKS body is `{"keys":[]}` — correct
and expected, because the self-hosted stack signs HS256 with a symmetric secret.

### 11. Stage 4b2's own verify command can never succeed

```bash
docker exec supabase-db psql -U supabase_auth_admin -d postgres -c 'select …'
# FATAL: Peer authentication failed for user "supabase_auth_admin"
```

`docker exec` runs as **root** inside the container, and the image's `pg_hba.conf` is:

```
local all supabase_admin  trust
local all all             peer map=supabase_map
host  all all 127.0.0.1/32 trust
```

so a unix-socket connection as `supabase_auth_admin` fails *peer authentication* —
which reads exactly like the grants failure the check is looking for, but is not.
**Add `-h 127.0.0.1`** and the check becomes meaningful (it then returns 6).

### 12. Stage 4b2 restores ownership but **not privileges** — and privileges are what break

This is the big one. `--clean` emits `DROP SCHEMA IF EXISTS "auth"` and `"storage"`,
and the dump is `--no-privileges`, so after a restore both schemas come back owned by
the restoring superuser with an **empty ACL**. Reassigning ownership does not bring
back a single `GRANT`. Two consequences, both silent in a row-count diff:

- `anon` and `authenticated` lose `USAGE ON SCHEMA auth`. Every RLS policy in the
  database calls `auth.uid()`. Without schema USAGE they cannot.
- The storage API loses its table grants. Measured: **26/26 uploads failed** with
  `permission denied for table buckets` (Postgres hint: *"Grant the required
  privileges to the current role with: GRANT SELECT ON storage.buckets TO
  service_role"*).

The fix is in `scripts/vps/stage10a-sync.sh` step 3, with values taken verbatim from
the `supabase/postgres` image's own `init-scripts`. Granting the API roles table
access on `storage` is what a fresh self-host does and is safe: `service_role` has
`BYPASSRLS`, and `anon`/`authenticated` are gated by the 12 RLS policies on
`storage.objects` (`storage.buckets` has RLS on with **no** policies, so clients
cannot enumerate buckets). Both facts were verified, not assumed.

### 13. The restart is in the wrong place, and Kong must be restarted too

Stage 10a lists `docker compose restart auth rest storage` as step 5 — *after* the
storage upload loop. Two things are wrong:

- **It must come before.** `storage-api` caches its schema/connection view; against a
  freshly `--clean`-restored database every upload fails until it is restarted.
- **Kong must be restarted as well.** `docker compose restart` gives each container a
  **new IP** on the bridge network and Kong caches the old one in its DNS resolver.
  Measured in `kong` error log: `connect() failed (111: Connection refused) while
  connecting to upstream, upstream: "http://172.19.0.9:5000/..."` while storage had
  moved to `172.19.0.7`. The symptom is *bursts* of 502s that no amount of retrying
  clears until Kong's DNS TTL happens to expire — which at cutover is intermittent
  502s on the live API. This is the same failure class already recorded for
  `docker swarm leave` breaking Docker's embedded DNS.

Measured effect of getting this right, over four consecutive rehearsals:

| Configuration | Storage uploads |
|---|---|
| no restart before upload | 0/26 |
| restart storage, no retry | 11/26 |
| restart storage, 4 tries, 1–3s backoff | 25/26 |
| **restart storage + kong, DNS asserted** | **26/26, no retries consumed** |

The script now asserts `kong`'s resolution of `storage` equals the container's
current IP rather than discovering it one 502 at a time.

### 14. supabase-js does **not** recover from an unexpired foreign-issuer token

Correction #7 established that Cloud signs ES256, so sessions must ride on the
restored refresh-token rows, and said *"verify at Stage 9d, do not assume."* Verified
— and it half-failed:

| Returning user's stored access token | Result |
|---|---|
| Cloud ES256, **already expired** | supabase-js refreshes silently → HS256 → everything works |
| Cloud ES256, **not yet expired** | **broken** |

In the second case supabase-js sees a non-expired token and keeps presenting it.
`getSession()` reports a live session and the nav renders "Account", while every
request fails: PostgREST `No suitable key or wrong key type`, GoTrue `invalid JWT:
… signing method ES256 is invalid`. A 401 is not a refresh trigger, so the account
looks signed in and nothing loads — for up to a full token lifetime (1 hour).

Blast radius is small (only users active in the hour before cutover) but it lands on
the most engaged users at the worst moment. Fix on branch
**`fix/session-continuity-guard`** (`site/assets/js/auth.js`): if the stored token's
`iss` host differs from the configured API host, mark the session expired so
supabase-js takes the refresh path. It is a no-op when they agree, which is the case
on the live site today, so it is safe to ship before cutover as well as after.

**Not merged to main:** any push to `main` touching `site/**` deploys to GitHub Pages,
which is still the live site and the rollback target. Merging is a human decision.
The VPS copy already carries the guard, and with it the stale-token case goes from
`{alg: ES256, error: "No suitable key…", rows: -1}` to
`{alg: HS256, error: null, rows: 2}`.

### 15. Two smaller findings

- **`public.bookmarks` and `public.notes` have no foreign key to `auth.users`.** All
  28 other user-owned tables cascade on user delete; these two orphan their rows
  forever. Pre-existing and identical on Cloud, so not a migration defect — but any
  cleanup script must sweep them explicitly, and it is worth fixing one day.
- **The favicons 404 on the *live* site and serve fine from the VPS.**
  `/assets/icons/favicon.ico`, `-32.png`, `apple-touch-icon.png` and
  `site.webmanifest` are all tracked in git and all return 404 from GitHub Pages
  today. The migration silently fixes this; it is not a regression to chase.
