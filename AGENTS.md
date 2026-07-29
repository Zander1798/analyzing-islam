<!-- GENERATED — do not edit. Canonical source: CLAUDE.md -->
<!-- Regenerate: node scripts/mirror-agents-md.mjs -->
<!-- You are reading the AGENTS.md view of the Claude-facing docs. Prose
     below may refer to ".claude.md" when describing the canonical side;
     that is accurate — only PATH references are rewritten to AGENTS.md. -->
# Analyzing Islam — agent instructions

Canonical agent-facing documentation for this repository.

**`CLAUDE.md` and any nested `.claude.md` files are canonical. `AGENTS.md` files are
generated mirrors — never hand-edit them.** After editing a canonical file, run
`node scripts/mirror-agents-md.mjs` and commit the regenerated mirror. CI fails the
pull request otherwise. Two hand-maintained rule sets disagree within a week, and
whichever one an agent reads, it believes it is compliant.

---

## What this repository is

A **static site plus Python build scripts**, backed by a **self-hosted Supabase**
stack. There is no application server and no framework.

- `site/` — the entire published site, **813 MB**, ~989 pages of pre-rendered HTML.
  Deployed as-is. Verified: `du -sh site` → `813M`.
- 165 `*.py` scripts at the repository root are the generators that produce `site/`.
  Verified: `ls *.py | wc -l` → `165`.
- `supabase/` — SQL schema, RLS policies and RPCs applied to the self-hosted Postgres.
- `tests/` — 24 pytest files. Verified: `ls tests/*.py | wc -l` → `24`.

**This repository is PUBLIC** (`Zander1798/analyzing-islam`, verified via
`gh repo view --json visibility` → `PUBLIC`). Never commit `.env`, the Supabase
service-role key, any database dump, or any API token. The dumps contain six users'
password hashes, refresh tokens and private messages.

### There is no dependency manifest

No `requirements.txt`, `pyproject.toml`, `setup.py`, `pytest.ini`, `tox.ini`,
`setup.cfg`, `conftest.py`, `Makefile` or `package.json` exists. Verified by `ls`.
Dependencies are implicit; the ones the code actually imports are `beautifulsoup4`,
`requests`, `psycopg2` and `pytest`. Python 3.13.5 locally.

**This is not an npm repository**, so the `agents:mirror` / `agents:check` npm scripts
described in some agent-docs workflows do not apply here. Call the script directly.

---

## Running the tests

```bash
python -m pytest tests/ -q          # full suite, ~4m25s
python -m pytest tests/test_kb_parsers.py -q   # one file
```

There is no test runner configuration, so pytest defaults apply and `--timeout` is
**not** available (`pytest-timeout` is not installed — passing it is an immediate
usage error).

### The baseline is 13 failed, 156 passed — not zero

Verified 2026-07-29: `13 failed, 156 passed in 265.30s`.

**These 13 failures are pre-existing and are not caused by your change.** Do not
"fix" them reflexively and do not treat a red suite as proof you broke something —
check whether your failure is in this list first:

| Test file | Failing tests |
|---|---|
| `tests/test_book_docx.py` | `test_entry_count` |
| `tests/test_book_html.py` | `test_entry_count`, `test_all_chapters_populated`, `test_verse_index_sorted_and_present` |
| `tests/test_catalog_stats.py` | `test_stats_total_and_taxonomy` |
| `tests/test_quiz_links_resolve.py` | `test_quiz_source_links_resolve` |
| `tests/test_read_anchors.py` | `test_quran_has_known_anchor`, `test_bukhari_has_known_anchor` |
| `tests/test_refs_integration.py` | `test_sampled_refs_resolve_to_existing_anchors` |
| `tests/test_site_counts.py` | `test_index_hero_number` |
| `tests/test_stats_page.py` | `test_index_category_count_widget` |
| `tests/test_validate_links.py` | `test_unresolved_flags_missing_anchor`, `test_scan_site_baseline_zero_unresolved` |

The `test_read_anchors` and `test_validate_links` failures follow from the scripture
readers having been split into per-chapter pages; the assertions still expect the
single-page layout.

**If a test outside this table fails, that is yours.**

There is no lint, type-check or build step configured in this repository. Do not
report running one.

---

## Rules that will cost you if you get them wrong

Each of these is conditional. The boundary is the important part.

### `build-catalog-pages.py` reverts a site-only reclassification

Most `build-*.py` scripts are safe to re-run. **`build-catalog-pages.py` is not**:
the Basic/Moderate/Strong ratings were re-derived for the site only and were never
written back to the book sources, so re-running it silently restores the old
ratings across all 1,524 entries.

Run it only when you intend to regenerate ratings from the book data, and expect to
re-apply the reclassification afterwards.

### Never replay all of `supabase/*.sql`

Applying one schema file deliberately is fine. **Replaying the whole directory is
destructive**, and two files are the reason:

- `supabase/analytics-verify.sql` is a **test script, not schema**. Verified at
  lines 19–20: it ends with `delete from public.pageviews where visitor in
  ('v1','v2')` and `delete from public.search_queries where q = 'aisha'`. The one
  real row in `search_queries` was `'aisha'`. It has destroyed data once already.
- `supabase/community-schema.sql` carries a demo seed that inserts communities.

`scripts/vps/stage10a-sync.sh` excludes `analytics-verify.sql` by name. Any new
replay path must do the same. If you add seed data to a file in `supabase/`, the
sync will replay it into production.

### `site/assets/js/config.js` points at Supabase Cloud on purpose

Verified: the repo copy reads `url: "https://cndmksrilytnpgstvmxb.supabase.co"`,
while the live site serves `https://api.analyzingislam.com`.

**This divergence is intentional and must not be "fixed" before Stage 12.** GitHub
Pages deploys from this repo and Pages is the rollback target; a repo pointing at
the VPS gives you a rollback that fails the same way the thing you are rolling back
from failed. The deploy rsync carries `--exclude='assets/js/config.js'` for this
reason.

### Re-running the reader builders needs the backups deleted first

The scripture readers are split into per-chapter pages by a post-build
`split_readers.py` pass, which leaves `.orig.html` backups behind. Re-running a
reader builder without deleting those first produces wrong output.

### `apply-source-links.py` must run after any catalog HTML rebuild

The readable source-link text lives **in the generated HTML only**, not in the JSON.
After rebuilding catalog, category or arguments pages, run `apply-source-links.py`
(it reads `source-link-map.json`) or 594 source links revert to fragile
Internet-Archive URLs.

### Pushing to `main` touching `site/**` deploys to GitHub Pages

Verified in `.github/workflows/pages.yml`: `on: push: branches: [main], paths:
["site/**", ".github/workflows/pages.yml"]`.

Since cutover the live site is served from the VPS, so a Pages deploy no longer
changes what visitors see — but Pages remains the **rollback target** until
decommissioning, so keep it deployable.

---

## Where the site actually runs

`analyzingislam.com` is served from a **Hostinger VPS at 72.60.17.245**, with a
self-hosted Supabase stack behind `api.analyzingislam.com`. Verified:
`curl https://analyzingislam.com/` → `200 via 72.60.17.245`.

- `.github/workflows/pages.yml` — the **active** workflow, still deploying to
  GitHub Pages (the rollback path).
- `.github/workflows-staged/deploy-vps.yml` — the rsync-to-VPS replacement,
  deliberately **not enabled**. Staged, not live.
- `scripts/vps/backup.sh`, `scripts/vps/test-restore.sh`,
  `scripts/vps/stage10a-sync.sh`, `scripts/stage10a-final-sync.sh` — operational
  scripts that run on or against the VPS.

**GitHub Pages and Supabase Cloud are the rollback path and must not be
decommissioned before 2026-08-11.** Rollback is a DNS change of about five minutes.

Do not revoke or delete the Cloudflare API token: the site's TLS certificate renews
via a DNS-01 challenge against it, and removing it fails **silently** — the first
symptom is an expired certificate on the live site.

---

## Where the real detail lives

This file is the rules. The reasoning is in:

| Path | What it covers |
|---|---|
| `docs/migration/EXECUTION-PLAN.md` | The migration, stage by stage, with 16 recorded corrections and the execution log |
| `docs/migration/CHATBOT-HANDOFF.md` | Chatbot Phase 1: embedding capacity, the chunking bake-off, four traps |
| `docs/migration/MIGRATION-PLAN.md` | Orientation and rationale |
| `docs/superpowers/specs/2026-07-27-ai-chatbot-design.md` | Chatbot design spec — wins where docs disagree |
| `docs/superpowers/plans/2026-07-27-chatbot-phase1-kb-retrieval.md` | Phase 1 task plan (Tasks 1–8 done; parts of it predate the chunking decision) |

All five paths verified to resolve.

---

## Working habits that matter here

- **`docker exec` without `-i` silently discards stdin and exits 0.** A heredoc of
  SQL piped into it runs `psql` with no input, prints nothing, and reports success
  while doing nothing. Always `-i`, and re-query to confirm a write landed.
- **`core.autocrlf=true` on the primary machine**, so `git status` routinely shows
  hundreds of modified files under `site/read/` with zero content change. Confirm
  with `git diff --numstat` before believing them.
- **Migration and chatbot work is executed from a second machine** and pushed to
  `origin/main`. Run `git fetch` before trusting the local copy's status docs.
