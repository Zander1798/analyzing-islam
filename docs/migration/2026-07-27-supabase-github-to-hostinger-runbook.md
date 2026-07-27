# Migration runbook — GitHub Pages + Supabase Cloud → Hostinger VPS

Date: 2026-07-27
Status: not started

## What this migrates

| From | To |
|---|---|
| GitHub Pages (static site, 995 pages) | nginx on a Hostinger VPS |
| Supabase Cloud Postgres | Self-hosted Postgres (Docker) |
| Supabase Cloud Auth (GoTrue) | Self-hosted GoTrue |
| Supabase Cloud REST API (PostgREST) | Self-hosted PostgREST |
| Supabase Cloud Storage (avatars) | Self-hosted Storage |
| Supabase Cloud Realtime (messenger) | Self-hosted Realtime |
| Cloudflare DNS → GitHub IPs | Cloudflare DNS → VPS IP |

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
- Only **one** file hardcodes the Supabase URL: `site/assets/js/config.js` line 6.
  Everything else reads `window.SUPABASE_CONFIG`.
- The Supabase CLI's `storage` command has **`ls` only, no `cp`** — file migration
  goes over HTTP.

## Two silent-breakage traps found before starting

Both would pass every test and fail weeks later. Both are handled in-line below.

1. **Avatar URLs are absolute and point at the old project.** `auth.js:382` and
   `:426` call `storage.from("avatars").getPublicUrl(path)`, which returns a full
   `https://cndmksrilytnpgstvmxb.supabase.co/...` URL, and `:430` writes it into
   `profiles.avatar_url`. After cutover these still resolve — because the old project
   is deliberately still running — and break the day it is deleted. Fixed in Stage 6.

2. **A new JWT secret logs everyone out.** Sessions are signed with the project's
   JWT secret. Generate a fresh one and every active session dies at cutover. Fixed
   in Stage 3 by reusing the existing secret.

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

### 1d. Record the JWT secret

Dashboard → **Settings → API → JWT Settings → JWT Secret**. Copy it somewhere safe
(password manager, not a file in the repo). Stage 3 needs it.

- [ ] Copy the backup, the storage folder and `avatar-paths.txt` somewhere off this
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

### 3b. Set the secrets in `.env`

**`JWT_SECRET` — paste the value from Stage 1d, not a new one.**

This is what keeps everyone logged in. It also means your existing `ANON_KEY` and
`SERVICE_ROLE_KEY` remain valid, because those are themselves JWTs signed with that
secret — so `config.js` may need only its URL changed. Confirm during Stage 8 rather
than assuming.

Also set:
- `POSTGRES_PASSWORD` — a new strong password
- `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD` — for Supabase Studio
- `SITE_URL=https://analyzingislam.com`
- `API_EXTERNAL_URL=https://api.analyzingislam.com`
- `SUPABASE_PUBLIC_URL=https://api.analyzingislam.com`

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
`public.highlights`, `public.notes`. **Do not proceed on a mismatch.**

---

## Stage 5 — Restore storage files

```bash
scp -r storage-backup/avatars deploy@VPS_IP:~/
docker cp ~/avatars supabase-storage:/var/lib/storage/stub/stub/avatars
```

The exact container path depends on the storage backend configured in `.env`
(`STORAGE_BACKEND=file`). Check `docker exec supabase-storage ls /var/lib/storage`
and place files to match the structure already there.

**Verify:** file count matches Stage 1c, and one avatar loads in a browser via the
new API URL.

---

## Stage 6 — Rewrite the avatar URLs (silent-breakage fix #1)

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

Repeat for `banner_url` if that column also stores absolute URLs — check first:
```sql
select count(*) from public.profiles where banner_url like '%supabase.co%';
```

**Verify:** zero rows still matching the old host, and an avatar renders in the
staging site at Stage 8.

---

## Stage 7 — Auth email (SMTP)

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
rsync -avz --delete "site/" deploy@VPS_IP:/var/www/analyzingislam/
```

### 8b. nginx — must replicate GitHub Pages' URL behaviour

GitHub Pages serves `/about` and `/about.html` interchangeably. nginx does not by
default, and 995 pages of internal links depend on it.

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

On the VPS only — not in the repo yet:
```bash
sudo nano /var/www/analyzingislam/assets/js/config.js
```
Change `url` to `https://api.analyzingislam.com`. Leave `anonKey` as-is initially
(it should still validate, since the JWT secret was reused). If auth fails, replace
it with the `ANON_KEY` from `.env`.

### 9d. Test matrix — every one, on `https://new.analyzingislam.com`

- [ ] Home, catalog, a category page, an entry page, a dossier
- [ ] Read pages: Quran, a hadith collection, Bible
- [ ] Extensionless URL (`/about`) resolves
- [ ] **Sign up** a brand-new test account
- [ ] **Log in** as an existing account (proves the auth data migrated)
- [ ] **Password reset** — email actually arrives (proves Stage 7)
- [ ] Bookmark an entry; confirm it appears on Saved
- [ ] Create a highlight and a note
- [ ] Quiz progress saves
- [ ] Profile: change username, **upload a new avatar**
- [ ] **Existing avatars render** (proves Stage 6)
- [ ] Build editor: create and share a build
- [ ] Community pages
- [ ] Messenger — send a message, confirm realtime delivery
- [ ] Admin dashboard loads for the owner account and is refused for others
- [ ] Contact form
- [ ] Goat skins, favicon, sitemap.xml, robots.txt
- [ ] Mobile viewport

**Do not proceed to cutover until every box is ticked.** This is where problems are
free to fix.

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
Then **re-run Stage 6** (the avatar URL rewrite) — the fresh restore reintroduces
the old URLs.

**Verify:** row counts match again.

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

- [ ] Confirm two weeks of clean operation
- [ ] Confirm backups have been running and one has been **test-restored**
- [ ] Commit the `config.js` URL change to the repo (until now it exists only on the
      server)
- [ ] Remove `site/CNAME` and disable GitHub Pages
- [ ] Update `.github/workflows/pages.yml` — replace the Pages deploy with an rsync
      deploy to the VPS, or retire it
- [ ] **Only now** consider pausing the Supabase Cloud project. Keep the Stage 1
      backup permanently regardless.

---

## Known gotchas

| Trap | Consequence | Handled in |
|---|---|---|
| New JWT secret | Everyone logged out at cutover | Stage 3b |
| Absolute avatar URLs | Images break when old project is deleted | Stage 6, re-run at 10a |
| No SMTP | Password reset silently does nothing | Stage 7 |
| nginx default routing | Extensionless links 404 across 995 pages | Stage 8b |
| Transaction pooler for pg_dump | Dump fails partway | Stage 1a |
| Dump omits `auth` schema | Every user account lost | Stage 1b |
| Final sync skipped | Data written during migration lost | Stage 10a |
| Avatar rewrite not repeated after final sync | Fix silently undone | Stage 10a |
| Backups only on the VPS | One disk failure loses everything | Stage 11a |
| Supabase project deleted early | No rollback | Stage 12 |

## Open questions

1. VPS not yet purchased at time of writing — Stage 2a is the first blocker.
2. `banner_url` may or may not store absolute URLs; Stage 6 checks before assuming.
3. Whether the existing `ANON_KEY` validates against the self-hosted stack — expected
   yes given JWT secret reuse, confirmed empirically at Stage 9c.
