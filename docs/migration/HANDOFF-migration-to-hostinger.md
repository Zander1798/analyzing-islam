# Handoff — migrating Analyzing Islam to Hostinger

**For:** whoever is taking over the migration
**From:** prior session, 2026-07-27
**Revised:** 2026-07-27, after a review that checked every claim against the code
**Owner:** Zander (non-specialist — explain rather than assume)

> **If you were sent an earlier copy of this file, use this one.** The review found
> that two load-bearing claims in the original were wrong (the anon key is not a JWT;
> `pg_dump --no-privileges` silently drops every GRANT), that two further silent-
> breakage traps had been missed, and that the feature list described a community and
> messenger front end that was deleted from the site months ago. All corrected below
> and in the runbook, marked inline.

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
| Static site, 989 pages (746MB) | GitHub Pages, from `site/` in this repo, deployed by `.github/workflows/pages.yml` |
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

## Four silent-breakage traps already identified

Each one passes the verification the runbook would otherwise run, and fails later.
All four are handled in the runbook — do not skip them.

### 1. Avatar and banner URLs are absolute and point at the old project

`site/assets/js/auth.js:382` (banner) and `:426` (avatar) both call
`storage.from("avatars").getPublicUrl(path)`, which returns a full
`https://cndmksrilytnpgstvmxb.supabase.co/...` URL. That string is then written into
`profiles.banner_url` (via `updateProfile` at `:386`) and `profiles.avatar_url`
(at `:430`).

**Both columns are affected — this is confirmed, not suspected.**

After cutover these **still resolve**, because the old Supabase project is
deliberately left running as rollback. They break the day it is deleted — weeks
later, with nothing linking the failure to the migration.

Runbook Stage 6 rewrites both columns. **It must be re-run after the Stage 10a final
sync**, because the re-restore reintroduces the old URLs.

### 2. The API keys are NOT JWTs — so "reuse the secret and nobody is logged out" is unproven

An earlier draft of this handoff claimed the existing `ANON_KEY` is a JWT signed with
the project's JWT secret, and that reusing the secret would therefore keep every
session alive and make `config.js` a one-line change. **That is wrong for this
project.**

`site/assets/js/config.js:7` holds:

```
sb_publishable_9rJKQFSBSA12YijYfGtD5g_7h4WD8wa
```

One segment, no dots, no `eyJ` prefix. That is Supabase's **newer publishable-key
format**, not a legacy JWT anon key. Two consequences:

- **`config.js` needs both lines changed**, not one. The self-hosted stack issues
  legacy JWT-format `ANON_KEY` / `SERVICE_ROLE_KEY` from its `.env`. Use those.
- **More important:** being on the new key system means the dashboard's legacy "JWT
  Secret" may no longer be what signs live user sessions. Newer projects can use
  asymmetric signing keys instead of the shared HS256 secret. Runbook Stage 3b's
  entire "reuse the secret and nobody gets logged out" mitigation rests on that
  assumption.

**Check this at the Supabase dashboard before relying on it** (Settings → API →
JWT Keys — note whether the project is on a legacy shared secret or on asymmetric
signing keys). If it is on asymmetric keys, plan for sessions to end at cutover and
tell users, rather than being surprised.

Softener worth knowing: the 73 rows in `auth.refresh_tokens` do get restored, so even
if access tokens stop validating, clients may recover silently on their next refresh.
That is a *maybe*, not a guarantee. Verify at Stage 9, do not assume.

### 3. `config.js` diverges between repo and server, and any content deploy silently reverts it

This is the likeliest of the four to actually fire, because it is triggered by the
most routine thing that happens to this repo: pushing a content update.

The mechanism:

- Stage 9c edits `config.js` **on the VPS only**, deliberately not in the repo.
- Stage 8a deploys with `rsync -avz --delete "site/"` — which overwrites it.
- `.github/workflows/pages.yml` auto-deploys on any push touching `site/**`.

So the repo's `config.js` points at Supabase Cloud while the server's points at the
VPS. Deploy any content change in that window and the server's copy is overwritten
with the Cloud URL.

**The site does not break when this happens** — the old Supabase project is
deliberately still running. New signups, bookmarks and notes simply flow into the
*old* database while the VPS database sits idle. Nobody notices. Then Stage 12 pauses
the old project and breakage plus data loss arrive together, with nothing pointing at
the cause.

**Fixed by an rsync `--exclude='assets/js/config.js'` at Stage 8a**, plus a two-second
`curl` check after every deploy at Stage 9c.

Note the fix is *not* "commit the change to the repo early". That looks obvious and is
wrong: GitHub Pages deploys from the repo, and Pages is the rollback target. A repo
pointing at the VPS gives you a rollback that fails the same way the thing you are
rolling back from failed. **The divergence is correct and intentional — it was simply
unprotected.** It gets resolved at Stage 12, when rollback is deliberately abandoned,
and the `--exclude` is removed at the same time.

### 4. `pg_dump --no-privileges` drops every GRANT, and a row-count check cannot see it

The Stage 1b dump command uses `--no-privileges`. RLS policies survive a `pg_dump`;
**GRANTs do not**. The schema in `supabase/` contains at least ten explicit grants,
including:

- `supabase/analytics.sql:27` — `grant execute on function public.is_creator() to anon, authenticated` (this is the admin-dashboard gate)
- `supabase/profile-community-extensions.sql:156` — `grant select on public.public_profiles to anon, authenticated`

So the restore can produce a **perfectly clean row-count diff** — which is Stage 4c's
only check — while PostgREST returns permission-denied to the browser.

Fixed at Stage 4d by re-applying the 18 files in `supabase/` after the restore, and by
adding an API-level verify alongside the `psql`-level one.

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
  is empty. All five are public. Only `avatars` is still reachable from the live site
  (see "Features that no longer exist" below) — restore all four anyway, they are 3.8MB.
- **GoTrue version skew is a real risk at Stage 4** and is not something we could test
  without the VPS. You are restoring a Supabase *Cloud* `auth` schema into a
  *self-hosted* GoTrue whose docker-compose pins an older version. If
  `auth.schema_migrations` disagrees with what that GoTrue expects, the container can
  fail to start or fail its own migrations. This is the stage that either preserves or
  destroys all 6 accounts — see Stage 4e for the contingency.
- **The site loads `@supabase/supabase-js@2` from jsDelivr** — a floating major tag.
  The client library can change under a pinned self-hosted server at any time. Pin it
  to an exact version for the duration of the migration so you are not debugging a
  moving target.
- **`site/` is 746MB** (435MB `assets/`, 178MB `read-external/`, 74MB `read/`). Size
  the VPS disk for it and expect the first rsync to take a while. Subsequent ones are
  incremental and fast.

---

## Why self-hosting the whole Supabase stack, not just Postgres

Supabase is Postgres **plus** GoTrue (auth), PostgREST (the REST API the browser
talks to), Storage and Realtime. Every page loads `supabase-js`, which calls
PostgREST with a token issued by GoTrue.

Move only the database and the site breaks completely — sign-in, bookmarks,
highlights, notes, quiz progress, saved builds, profiles and the admin dashboard all
stop. There would be a database with the data in it and nothing able to serve it.

Self-hosting the full stack keeps all 18 SQL files in `supabase/`, every RLS policy
and every `auth.uid()` call working unchanged.

**What the front end actually calls** (verified by grep across `site/`, not assumed):

| Service | Used? | Evidence |
|---|---|---|
| GoTrue (auth) | **Yes** | 8 `client.auth.*` call sites |
| PostgREST (REST) | **Yes** | `from()` and `rpc()` call sites |
| Storage | **Yes** | 2 `storage.from("avatars")` call sites, both in `auth.js` |
| Realtime | **No** | **zero `.channel()` calls anywhere in `site/`** |

**Realtime can be dropped from the self-hosted stack.** Nothing on the live site
subscribes to it. That is one fewer container to run, monitor, back up and patch. If
the community/messenger feature is ever restored (see below), add it back then.

`site/assets/js/config.js` is the only *site* file that hardcodes the Supabase URL —
`backup-supabase.py` also contains the project ref, but it is a local script, not
shipped to the browser. **`config.js` needs both of its lines changed, not just the
URL** — see trap #2 above.

---

## Site features that must all still work after cutover

Runbook Stage 9 has the full test matrix. Summary of what exists **on the live site
today**:

Auth (signup, login, **password reset via email**), profiles with avatar and banner
upload, bookmarks, notes, highlights, quiz progress, build editor with shareable
builds, creator analytics dashboard gated by an `admins` table and `is_creator()`
RPC, anonymous pageview tracking, contact form via FormSubmit.

**Password reset is the one most likely to be silently broken.** Self-hosted GoTrue
sends nothing until SMTP is configured (Stage 7). Test it with a real reset, do not
assume.

### Features that no longer exist — do not go looking for them

An earlier draft of this handoff listed communities, direct messenger and friendships
as live features that must keep working. **They were removed from the site.** Commit
`19456d24 "Remove community feature entirely"` deleted 19 community JS modules and 5
community HTML pages. There is no messenger front end either.

What this means for you:

- There are **no community or messenger pages to test.** An earlier Stage 9d test
  matrix asked you to verify them; those rows have been removed. A matrix with rows
  that cannot be ticked honestly is worse than a shorter one.
- **Realtime is unused** — see the table above. Consider dropping the container.
- The DB tables and their rows (2 communities, 8 comments, 1 direct message, etc.)
  **still exist and still restore.** That is harmless — leave them. Restoring them
  costs nothing and keeps the option open.
- The SQL files (`community-schema.sql`, `messenger-schema.sql`, `friendships.sql`
  and friends) are still in `supabase/` and should still be applied at Stage 4d. They
  define tables the dump expects.

If anyone is quoting this job from the old feature list, the scope is smaller than it
looked.

---

## Why this migration is worth doing — the real reason

The decision is made: everything moves to the VPS. This section exists so you
understand *why*, because an earlier draft framed it in a way that undersold it.

The user-data argument is weak on its own. The database is **small**: 6 user accounts,
5 profiles, 1 bookmark, 1 note, 401KB. Taking on ~12 Docker containers, an auth
server, SMTP, backups and uptime to protect six accounts is a poor trade read purely
on those numbers.

**The stronger argument is the chatbot.** Phase 1 needs `pgvector` and, later, an
embedding model running next to the database. Tasks 1, 2, 8, 9 and 10 of that plan are
already parked pending this migration precisely because they target whichever Postgres
wins (see "Unrelated work in flight" below). That is the workload Supabase's hosted
tiers would actually constrain, and it is the reason to size the box at 16GB rather
than 8GB.

So: this is a migration about the chatbot's future home and about cost, control and
consolidation — not about six user accounts. Plan and size it accordingly.

**Fallback if the migration stalls badly.** A smaller option exists and remains
available: move the site to Hostinger and leave Supabase where it is — runbook stages
2, 8, 9, 10 only, an afternoon rather than a multi-day project. It delivers
consolidation and web-tier control while Supabase keeps doing auth, backups and uptime
free. It does **not** solve the `pgvector` problem, so treat it as a retreat position,
not the plan.

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
| `site/` | The entire static site, 989 pages, 746MB. Deployed as-is. |
| `site/assets/js/config.js` | The only *site* file hardcoding the Supabase URL. **Both lines change** — URL and key. See trap #2. |
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
