# Handoff — migrating Analyzing Islam to Hostinger

**For:** whoever is taking over the migration
**From:** prior session, 2026-07-27
**Owner:** Zander (non-specialist — explain rather than assume)

---

## What you're being asked to do

Move **analyzingislam.com** off GitHub Pages + Supabase Cloud, onto a **Hostinger
VPS**, self-hosting everything including the database and auth.

The owner's reasons, in his words: **cost, control/data ownership, and
consolidation** (one bill, one dashboard rather than site on GitHub, database on
Supabase, DNS on Cloudflare).

**Nothing may break.** The site must stay live throughout.

---

## Start here

**`docs/migration/2026-07-27-supabase-github-to-hostinger-runbook.md`**

Thirteen stages (0–12), each ending in a verification step, with rollback where one
exists. Stages 0 and 1 are **already done** (see below). Stage 2 is next and needs a
VPS, which did not exist at handoff.

Read that runbook before doing anything. This file is only orientation.

---

## Current state of the world

| Thing | Where it is now |
|---|---|
| Static site, 995 pages | GitHub Pages, from `site/` in this repo, deployed by `.github/workflows/pages.yml` |
| Database, auth, storage, realtime | Supabase Cloud, project ref `cndmksrilytnpgstvmxb`, region **eu-west-1** |
| DNS | **Cloudflare** (`dell.ns.cloudflare.com`, `zahir.ns.cloudflare.com`) — owner has access |
| Domain registrar | Unknown, and **irrelevant** — the cutover only touches Cloudflare |
| Email on the domain | **None.** No MX records, so DNS changes cannot break mail |

### DNS specifics (verified, don't re-derive)

- Four `A` records on the apex → `185.199.108.153`, `.109.153`, `.110.153`, `.111.153`
- One `CNAME` on `www` → `zander1798.github.io`
- **TTL is already 300s.** Cloudflare "Auto" for DNS-only records means 300. No TTL
  change is needed and no 24-hour wait. Rollback propagates in ~5 minutes.
- Cloudflare proxy is **off** (grey cloud). Turning it on post-migration would be a
  free upgrade (CDN, SSL, DDoS).

---

## What is already done

### Stage 0 — local tooling ✅
PostgreSQL 18.4 client tools installed on the owner's Windows machine at
`C:\Program Files\PostgreSQL\18\bin`, added to PATH via `~/.bashrc`, with a
`~/.bash_profile` created to source it (Git Bash starts as a *login* shell and
otherwise never reads `.bashrc`).

### Stage 1 — full backup ✅
Taken 2026-07-27, living at **`C:\Users\zande\Documents\analyzingislam-migration`**
on the owner's PC. **Not in this repo, and must never be** — see Security below.

- `supabase-backup.sql` — 401KB, 53 tables, schemas `public` + `auth` + `storage`
- `storage-backup/` — 3.8MB, 26 files across 4 buckets
- `storage-paths.txt` — the manifest

**Baseline row counts. Stage 4's restore must match these exactly:**

| Table | Rows | | Table | Rows |
|---|---:|---|---|---:|
| `auth.users` | **6** | | `public.shared_builds` | 5 |
| `auth.identities` | 6 | | `public.community_members` | 4 |
| `auth.sessions` | 10 | | `public.community_posts` | 2 |
| `auth.refresh_tokens` | 73 | | `public.communities` | 2 |
| `public.profiles` | 5 | | `public.community_join_requests` | 2 |
| `public.pageviews` | 858 | | `public.post_comments` | 8 |
| `storage.objects` | 26 | | `public.post_votes` | 1 |
| `storage.buckets` | 5 | | `bookmarks` / `notes` / `quiz_progress` | 1 each |
| `public.admins` | 1 | | `friendships` / `direct_threads` / `direct_messages` | 1 each |

26 of 52 tables carry data.

---

## ⚠ Security — read before pushing anything

**This repo is PUBLIC** (`github.com/Zander1798/analyzing-islam`).

`supabase-backup.sql` contains 6 users' email addresses, bcrypt password hashes,
refresh tokens, private direct messages and notes. **It must never be committed.**
Pushing it once puts it in the git history and in every clone, permanently.

Same for: the Supabase service-role key, the database password, `.env` from the
self-hosted stack, and any SSH private key.

The owner has been told not to paste credentials into chat. Please keep that up.

---

## Two silent-breakage traps already identified

Both would pass every test and fail weeks later. Both are handled in the runbook —
do not skip them.

### 1. Avatar URLs are absolute and point at the old project

`site/assets/js/auth.js:382` and `:426` call
`storage.from("avatars").getPublicUrl(path)`, which returns a full
`https://cndmksrilytnpgstvmxb.supabase.co/...` URL, and `:430` writes that string
into `profiles.avatar_url`.

After cutover these **still resolve**, because the old Supabase project is
deliberately left running as rollback. They break the day it is deleted — weeks
later, with nothing linking the failure to the migration.

Runbook Stage 6 rewrites them. **It must be re-run after the Stage 10a final sync**,
because the re-restore reintroduces the old URLs.

Also check `banner_url`, which may store absolute URLs the same way.

### 2. A fresh JWT secret logs every user out

Sessions are signed with the project's JWT secret. Generate a new one for the
self-hosted stack and every active session dies at cutover.

Runbook Stage 3b reuses the existing secret (Supabase dashboard → Settings → API →
JWT Secret). A side effect worth confirming empirically: the existing `ANON_KEY`
should also stay valid, since it is itself a JWT signed with that secret — which
would make `config.js` a one-line change.

---

## Gotchas found the hard way

- **Windows `psql.exe` writes CRLF.** Any `psql.exe > file` redirect produces
  carriage returns that silently corrupt URLs and filenames downstream. This failed
  all 26 storage downloads on the first attempt while the URLs themselves were fine.
  Always `tr -d '\r'` afterwards.
- **Git Bash is a login shell** — reads `.bash_profile`, never `.bashrc` unless the
  former sources it.
- **`core.autocrlf=true`** on this machine, so `git status` routinely shows hundreds
  of "modified" files under `site/read/` that have zero content change. Confirm with
  `git diff --numstat` before believing them.
- **Supabase direct connection is IPv6-only** for this project. Use the **session
  pooler** (`aws-0-eu-west-1.pooler.supabase.com:5432`, user
  `postgres.cndmksrilytnpgstvmxb`). The transaction pooler fails partway through a
  `pg_dump`.
- **Four buckets have files**, not one: `avatars` (16), `community-icons` (2),
  `community-banners` (2), `community-post-images` (6). `dm-attachments` exists but
  is empty. All five are public.

---

## Why self-hosting the whole Supabase stack, not just Postgres

Supabase is Postgres **plus** GoTrue (auth), PostgREST (the REST API the browser
talks to), Storage and Realtime. Every page loads `supabase-js`, which calls
PostgREST with a JWT issued by GoTrue.

Move only the database and the site breaks completely — sign-in, bookmarks,
highlights, notes, quiz progress, saved builds, community, messenger, profiles and
the admin dashboard all stop. There would be a database with the data in it and
nothing able to serve it.

Self-hosting the full stack keeps all 18 SQL files in `supabase/`, every RLS policy
and every `auth.uid()` call working unchanged. Only `site/assets/js/config.js` needs
to change — it is the **only** file that hardcodes the Supabase URL.

---

## Site features that must all still work after cutover

Runbook Stage 9 has the full test matrix. Summary of what exists:

Auth (signup, login, **password reset via email**), profiles with avatar and banner
upload, bookmarks, notes, highlights, quiz progress, build editor with shareable
builds, communities (posts, comments, votes, join requests), direct messenger
(**realtime**), friendships, creator analytics dashboard gated by an `admins` table
and `is_creator()` RPC, anonymous pageview tracking, contact form via FormSubmit.

**Password reset is the one most likely to be silently broken.** Self-hosted GoTrue
sends nothing until SMTP is configured (Stage 7). Test it with a real reset, do not
assume.

---

## A judgement call worth revisiting with the owner

The database is **small**: 6 user accounts, 5 profiles, 1 bookmark, 1 note, 401KB.

Full self-hosting means the owner takes on 13 Docker containers, an auth server,
SMTP, backups and uptime — to protect six accounts. That may still be right for the
control and ownership reasons, and he has been clear he wants it.

But a smaller option was offered and declined, and is worth re-raising if the
migration stalls: **move the site to Hostinger and leave Supabase where it is.**
Runbook stages 2, 8, 9, 10 only. An afternoon rather than a multi-day project. It
delivers consolidation and web-tier control; Supabase keeps doing auth, backups and
uptime free. Self-hosting the rest stays possible later.

---

## Unrelated work in flight (don't be surprised by it)

A separate project is underway: an **AI chatbot** for the site, specced in
`docs/superpowers/specs/2026-07-27-ai-chatbot-design.md` with a Phase 1 plan in
`docs/superpowers/plans/2026-07-27-chatbot-phase1-kb-retrieval.md`.

Tasks 3–7 are **merged and complete** — five pure Python parsers in `kb_parsers.py`
with 31 passing tests in `tests/test_kb_parsers.py`, plus `kb-doctrine/`. They are
portable to any Postgres and unaffected by the hosting decision.

Tasks 1, 2, 8, 9 and 10 (schema, embedding function, ingest, video ingest, retrieval
recall fixture) are **deliberately deferred pending this migration**, since they
target whichever Postgres wins. The chatbot needs `pgvector`.

An SDD ledger for that work is at
`.superpowers/sdd/2026-07-27-chatbot-phase1-kb-retrieval/progress.md` (gitignored,
local to the owner's machine).

---

## Repo orientation

| Path | What it is |
|---|---|
| `site/` | The entire static site, 995 pages. Deployed as-is. |
| `site/assets/js/config.js` | **The only file hardcoding the Supabase URL** |
| `supabase/*.sql` | 18 schema files — tables, RLS, RPCs. Apply to the new Postgres. |
| `docs/migration/` | The runbook and this handoff |
| `build-*.py` | Site generators. **Do not run casually** — `build-catalog-pages.py` reverts a site-only strength reclassification. |
| `tests/` | pytest. ~23 pre-existing failures unrelated to migration (book-builder, split-readers, link-validation) — that is the baseline, not a regression. |
| `.github/workflows/pages.yml` | Current GitHub Pages deploy. Replace with rsync-to-VPS at Stage 12. |

---

## Immediate next step

**Provision the VPS.** Hostinger **KVM** (not shared hosting — it cannot run Docker
or Postgres). **8GB RAM minimum**, 16GB preferred since the chatbot's embedding model
will later share the box. **Ubuntu 24.04 LTS**.

Then start at runbook Stage 2.
