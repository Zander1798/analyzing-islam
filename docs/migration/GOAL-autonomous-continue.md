# /goal — Take the Hostinger migration as far as possible without human input

## Mission

Continue the analyzingislam.com migration to VPS **72.60.17.245**, autonomously, up to
but **NOT including** cutover. Maximise verified progress; leave a state where the only
remaining work genuinely requires a human.

Read first, in this order:
1. `docs/migration/EXECUTION-PLAN.md` — the live plan, stage numbering, and the
   execution log of what is already done (Stages 2,3,4,5,6,7,8,9c complete).
2. `docs/migration/MIGRATION-PLAN.md` — orientation, traps, rationale.
3. Memory: `hostinger-migration-state.md`.

## Hard constraints — violating any of these is a failure, not a trade-off

1. **DO NOT CUT OVER.** Never delete, edit, or repoint the apex `A` records or the
   `www` CNAME for analyzingislam.com. The live site must keep serving from GitHub
   Pages throughout. Stage 10 is out of scope entirely.
2. **DO NOT touch DNS for analyzingislam.com at all.** The zone lives in Zander's
   Cloudflare account, which we have no credential for. The key in
   `~/secrets/analyzingislam/cloudflare.ini` is a *different* account (11 zones, none
   of them this domain) — do not try to make it work, and do not add records anywhere.
3. **Never commit secrets.** The repo is PUBLIC. No `.env`, no dumps (they contain 6
   users' password hashes, refresh tokens, private messages), no keys, no passwords.
   Secrets live in `~/secrets/analyzingislam/` (mode 600) and on the VPS only.
4. **Do not write to Supabase Cloud.** It is the rollback target and the live
   database. Read-only: dumps and queries only.
5. **Evidence before claims.** Never mark something done without command output
   proving it. `docker exec` **without `-i` silently discards stdin and exits 0** —
   always `-i` for SQL, and always re-query to confirm a write landed.

## Objectives, in priority order

### A. Prove the stack works end-to-end without DNS  ← highest value
DNS is blocked, but testing is not. Map the hostnames locally instead:

- Add to the **workstation** `/etc/hosts` (sudo; this is local-only and affects nobody
  else): `72.60.17.245  new.analyzingislam.com api.analyzingislam.com`
- Issue a **self-signed cert** on the VPS for `new.` and `api.`, wire up nginx 443
  vhosts, and trust it locally for the test run — or drive tests over plain HTTP by
  temporarily serving a config.js variant with `http://api.analyzingislam.com`.
  Either way: **do not leave a self-signed cert in the path that Stage 9e/10 will
  use** — document and revert whatever you add.
- Then work the **Stage 9d test matrix** in `EXECUTION-PLAN.md` as far as it goes,
  using real browser automation (Chrome tools are available) rather than curl alone,
  because the point is to exercise supabase-js, not the API.

Must-prove items, in order of how badly they would hurt if broken:
- Sign up a new account; confirm the confirmation email path works.
- **Log in as a pre-existing migrated user.** You do not know their passwords — use
  the GoTrue **admin API** with the service-role key to set a known password on a
  throwaway *copy* of a user, or create a user and verify RLS-scoped reads. Do NOT
  change any real user's password.
- **Session continuity:** verify the refresh-token path works — mint a session, then
  confirm a client recovers via `auth.refresh_tokens`. This is the open question the
  ES256 finding left behind.
- Bookmarks, notes, highlights, quiz progress, shared builds — write and read back.
- **Admin dashboard gating both directions**: loads for the admin, refused for a
  non-admin. A dashboard that loads for everyone is a failure, not a pass.
- Existing avatars and banners render from the rewritten URLs.
- Extensionless routing, 404 page, sitemap, robots, mobile viewport.

Record every result honestly in the plan's execution log, including anything that
fails or that you could not test. A short honest matrix beats a long optimistic one.

### B. Stage 11 — make it survivable (fully unblocked)
- Backup script per `EXECUTION-PLAN.md` 11a — note the corrected bind-mount path
  `~/supabase-selfhost/volumes/storage`, prune **both** `*.sql` and `*.tar.gz`, no
  swallowed failures. Cron it.
- **Test-restore a backup into a scratch database and prove row counts match.** An
  untested backup is a hope. This is a Stage 12 gate — clear it now.
- Off-box copy: pull nightly from the workstation, or rclone. Implement whichever
  needs no new account.
- `restart: unless-stopped` on every service; confirm by rebooting the VPS and
  watching the whole stack come back healthy on its own.

### C. Rehearse Stage 10a (the final sync) without cutting over
The final sync is the riskiest unrehearsed step, because a `--clean` restore silently
undoes grants, URL rewrites and storage. Rehearse the **whole** sequence against the
VPS: fresh dump → restore → ownership/grants repair → schema replay **excluding
`analytics-verify.sql`** → seed reconcile → URL rewrite → storage re-upload → restart
`auth rest storage` → full verification. Time it, script it as a single idempotent
`stage10a-sync.sh` on the VPS, and prove the end state matches cloud exactly.

### D. Harden and tidy
- `unattended-upgrades`, `fail2ban` for SSH, and a swap file (8GB RAM, 2 vCPU).
- Re-verify the external port scan: 3000/8000/8443/5432/6543 must all refuse from
  off-box; only 22/80/443 answer.
- Write the Stage 12 replacement deploy workflow (rsync to VPS) **as a file, not
  enabled** — do not modify `.github/workflows/pages.yml` while Pages is still live
  and is the rollback target.

### E. Unblock the chatbot (the actual reason for this migration)
`pgvector` is live on the VPS. Chatbot Phase 1 tasks 1, 2, 8, 9, 10 were parked
pending "whichever Postgres wins". That question is now answered. See
`docs/superpowers/plans/2026-07-27-chatbot-phase1-kb-retrieval.md`. Land what is
safely landable — schema and embedding groundwork against the VPS Postgres — without
touching the live site. Respect the recorded `embed_text` truncation risk on Task 10.

## Stop and ask the human when

- Anything would change live DNS, the live site, or Supabase Cloud data.
- A real user's account, password, or data would be modified.
- A test fails in a way that suggests the migration plan itself is wrong (report the
  evidence; do not paper over it).
- You need a credential that does not exist in `~/secrets/analyzingislam/`.

## Deliverable

Commit and push documentation updates as you go (small, honest commits). Finish with a
written status in `EXECUTION-PLAN.md` covering: what is proven, what failed, what
remains, and the exact shortest list of things a human must still do — which should be
essentially "Zander's Cloudflare token, then Stages 9a/9b/9e and 10."
