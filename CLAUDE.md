# Analyzing Islam — agent instructions

Canonical agent-facing documentation for this repository.

**`CLAUDE.md` and any nested `.claude.md` files are canonical. `AGENTS.md` files are
generated mirrors — never hand-edit them.** After editing a canonical file, run
`node scripts/mirror-agents-md.mjs` and commit the regenerated mirror. The
`agent-docs` workflow checks every pull request and every push to `main`; a stale
mirror makes that check red. Whether the check blocks a merge or direct push depends
on the repository's current branch rules, so do not treat the workflow as branch
protection. Two hand-maintained rule sets disagree within a week, and whichever one
an agent reads, it believes it is compliant.

---

## What this repository is

A **pre-rendered static site plus Python build/maintenance scripts**, backed by a
**self-hosted Supabase** stack. The published website has no application server or
site framework, but the repository also contains a Deno Supabase Edge Function at
`supabase/functions/embed/index.ts` and an isolated React/Remotion video project
under `video/`.

- `site/` — the generated website tree: **746 MB** and 989 pre-rendered HTML files
  in this checkout. GitHub Pages uploads this tree as-is; the staged VPS rsync
  deliberately excludes `site/assets/js/config.js`.
- The repository root contains 165 `*.py` files. They are a mix of builders,
  migration/fix scripts, audits, backup tooling and chatbot ingest code; the count
  does **not** mean all 165 are site generators or safe to run.
- `supabase/` — SQL schema, RLS policies, RPCs, an Edge Function, test SQL and demo
  seed SQL. Do not infer that every file is production schema or safe to replay.
- `tests/` — 23 `test_*.py` pytest modules plus four `test_*.mjs` Node test files.
  `tests/__init__.py` is not a test module.

**This repository is PUBLIC** (`Zander1798/analyzing-islam`, verified via
`gh repo view --json visibility` → `PUBLIC`). Never commit `.env`, the Supabase
service-role key, database URL/password, any database dump, or any API token.
Database dumps can contain password hashes, refresh tokens and private messages.

### Dependency manifests are split

There is no root Python dependency or test-runner manifest: no `requirements.txt`,
`pyproject.toml`, `setup.py`, `pytest.ini`, `tox.ini`, `setup.cfg`, `conftest.py` or
`Makefile`. Python dependencies are therefore implicit. Root scripts and tests
currently import `beautifulsoup4`, `requests`, `psycopg2`, `pytest`, Pillow,
python-docx and Playwright.

`video/package.json` and `video/package-lock.json` define an npm subproject using
React 18, Remotion 4 and TypeScript 5.5. There is no root `package.json`, so the
`agents:mirror` / `agents:check` npm scripts described in some agent-docs workflows
do not apply at the root; call the mirror script directly.

No repository-wide runtime version is pinned. The 2026-07-29 audit machine reports
Python 3.12.3, pytest 9.0.2, Node 20.20.1 and npm 10.8.2; the mirror CI explicitly
uses Node 22.

---

## Running the tests

```bash
python -m pytest tests/ -q                   # all Python tests
node --test tests/*.mjs                      # all Node tests
python -m pytest tests/test_kb_parsers.py -q   # one file
```

The Python and Node commands are both required for the full repository test set;
pytest alone omits four JavaScript checks. There is no root pytest configuration, so
pytest defaults apply. On the audit machine `pytest-timeout` is not installed and
`--timeout` is an immediate usage error.

Some pytest modules invoke generators. The full run can rewrite
`book-design/vol1-quran/book.html` and create ignored `site/read/*.orig.html` files
before failing. Inspect `git status` and ignored reader backups after a run; remove
or restore only artifacts that your run created.

### The clean-checkout Python baseline is not green or portable

Verified on a clean checkout on 2026-07-29:
`26 failed, 143 passed in 22.07s`. The four Node test files pass.

| Test file or group | Failures | Verified cause or boundary |
|---|---:|---|
| `tests/test_book_docx.py` | 5 | `build-book-docx.py` hard-codes a Windows checkout path that does not exist on this machine. |
| `tests/test_book_html.py` | 3 | Assertions still expect the older 262-entry/chapter/index shape; the current builder reads 275 entries. |
| `tests/test_build_catalog_pages.py` | 1 | Requires the untracked sibling Analyzing Islam Books data directory, absent on this machine. |
| `tests/test_catalog_stats.py` | 1 | Generated category totals differ from the asserted taxonomy. |
| Reader/link group: `test_quiz_links_resolve.py`, `test_read_anchors.py`, `test_refs_integration.py`, `test_split_readers.py`, `test_validate_links.py` | 14 | The tracked readers are split shells while pristine monolith `.orig.html` inputs are git-ignored and absent in a fresh clone. |
| `tests/test_site_counts.py`, `tests/test_stats_page.py` | 2 | The tracked homepage markup does not contain the asserted static 1,524/31 number spans. |

Do not label every failure outside this snapshot as introduced by the current
change. Compare against a clean checkout in the same environment, identify missing
external data, and prioritize tests covering the files you changed.

There is no repo-wide lint, type-check or build aggregator. The `video/` subproject
has strict `video/tsconfig.json` configuration and `npm run render:*` scripts, while
the website has many individual generators rather than one safe full-build command.

---

## Rules that will cost you if you get them wrong

Each of these is conditional. The boundary is the important part.

### The first chatbot ingest needs Hein's authorized machine

As of the 2026-07-29 handoff, Tasks 1–8 are implemented but the live `kb_docs` and
`kb_chunks` tables have not received the real corpus. `python build-kb.py --dry-run`
needs no credential and currently reports 39,106 documents and 43,016 chunks.

A real ingest requires all three secrets/endpoints below and must run only from
Hein's authorized machine, never from a general contributor or browser-facing
environment:

```bash
export SUPABASE_DB_URL=postgresql://...
export SUPABASE_EMBED_URL=https://api.analyzingislam.com/functions/v1/embed
export SUPABASE_SERVICE_ROLE_KEY=...   # never the public anon key

python build-kb.py --only doctrine     # three-document smoke test
python build-kb.py --only doctrine     # second run must be unchanged
```

The live embed endpoint returns 403 for the public anon role; `build-kb.py` and
`kb_client.py` require the service-role key deliberately. Run bulk ingestion
off-peak because the 2-vCPU VPS also serves the live site. After ingestion, run the
Task 10 retrieval/recall evaluation before treating the user-facing chatbot design
as validated.

### `build-catalog-pages.py` reverts a site-only reclassification

Do not assume a `build-*.py` script is safe merely because it is named like a
builder. `build-catalog-pages.py` reads entry JSON from the untracked sibling
Analyzing Islam Books data directory, which is absent on the audit machine, and
renders each entry's `strength` value directly. It does not consume the repository's
`strength_ratings_for_books.json`.

If the sibling book JSON has not received the site-only Basic/Moderate/Strong
reclassification, running the builder overwrites current catalog ratings with the
older book values. Run it only when that external input is present and authoritative,
then re-apply and verify the intended ratings.

### Never replay all of `supabase/*.sql`

Applying one reviewed schema file deliberately can be fine. **A naive replay of the
whole directory is destructive**, and two files prove why:

- `supabase/analytics-verify.sql` is a **test script, not schema**. Verified at
  lines 1–20: it inserts probe rows, then deletes every pageview using visitors
  `v1`/`v2` and every search whose query is `aisha`; matching real rows are not
  distinguished from its probes.
- `supabase/community-schema.sql` carries a six-community demo seed.

`scripts/vps/stage10a-sync.sh` excludes `analytics-verify.sql` by name and snapshots
the real community IDs so it can remove exactly the demo communities added by the
replay. That compensation is specific to this script. Any new replay path must
exclude test SQL and explicitly handle seeds; if the stage-10 loop is reused, it
will execute every other top-level `supabase/*.sql` file.

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
`split_readers.py` pass. The splitter always prefers `site/read/<slug>.orig.html`
once it exists. After deliberately rebuilding a monolithic reader, delete that
reader's stale `.orig.html` before running the splitter or the new monolith is
ignored.

On a fresh clone those backups are absent because `site/read/*.orig.html` is
git-ignored, while the tracked `site/read/<slug>.html` files are already split
shells. Running `split_readers.py` or `build-split-readers.sh` alone then creates a
bad backup from a shell and fails with `no blocks found`. First run the appropriate
monolithic reader builder and decorators, then split.

### `apply-source-links.py` must run after any catalog HTML rebuild

The external source-link anchors and destinations live **in the generated HTML
only**, not in the JSON. After rebuilding catalog, category or arguments pages, run
`apply-source-links.py` (it reads `source-link-map.json`) or managed links can revert
to fragile Internet-Archive URLs. Then run
`python apply-source-links.py --check`.

The check exits 1 when rewrites are still required, but unmapped archive identifiers
are warnings and do not change its exit status. A clean result therefore requires
both zero rewrites and deliberate review of any `Unmapped archive.org identifiers`
section; the 2026-07-29 audit printed seven unmapped identifiers.

### Pushing to `main` touching `site/**` deploys to GitHub Pages

Verified in `.github/workflows/pages.yml`: `on: push: branches: [main], paths:
["site/**", ".github/workflows/pages.yml"]`.

Since cutover the live site is served from the VPS, so a Pages deploy no longer
changes what visitors see — but Pages remains the **rollback target** until
decommissioning, so keep it deployable. Nothing in the active workflows deploys to
the live VPS; until Stage 12, live-site updates are manual.

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
decommissioned before 2026-08-11.** That date is a minimum, not automatic approval:
run the Stage 12 prerequisites in `docs/migration/EXECUTION-PLAN.md` and verify the
current rollback procedure and DNS TTL before decommissioning.

While Certbot's apex-certificate renewal still uses the DNS-01 credentials in the
VPS deploy user's private Cloudflare file, do not revoke or delete the Cloudflare
API token: renewal otherwise fails without affecting the currently valid
certificate. Switch to and verify a replacement authenticator first; only then is
revocation safe.

---

## Where the real detail lives

This file is the rules. The reasoning is in:

| Path | What it covers |
|---|---|
| `docs/migration/EXECUTION-PLAN.md` | The migration, stage by stage, with 16 recorded corrections and the execution log |
| `docs/HANDOFF-2026-07-29.md` | Current session state: first ingest still pending, then Tasks 10 and 9 |
| `docs/migration/CHATBOT-HANDOFF.md` | Chatbot Phase 1 history: embedding capacity, the chunking bake-off and four traps; its old “Task 8 next” passages predate the implemented ingest |
| `docs/migration/MIGRATION-PLAN.md` | Orientation and rationale |
| `docs/migration/GOAL-kb-reader-credential.md` | Proposed least-privilege retrieval-evaluation credential; a goal, not evidence that the role exists |
| `docs/superpowers/specs/2026-07-27-ai-chatbot-design.md` | Product design intent; later handoffs and deployed implementation win for current operational details |
| `docs/superpowers/plans/2026-07-27-chatbot-phase1-kb-retrieval.md` | Phase 1 task plan; Tasks 1–8 are implemented, but parts predate service-role auth and chunking |

All seven paths verified to resolve.

---

## Working habits that matter here

- **Use `docker exec -i` when the command reads piped or heredoc stdin.** Without
  `-i`, Docker does not keep stdin open; `psql` can receive no SQL and still exit 0.
  Commands that do not read stdin do not need `-i`. Re-query to confirm every write.
- Line-ending settings differ across contributors. If `git status` shows a large
  generated-tree diff, use `git diff --numstat` and inspect content before assuming
  hundreds of real edits.
- This repository is edited from multiple machines. Run `git fetch` before trusting
  local migration/chatbot state or handoff documents; the remote advanced during the
  2026-07-29 audit itself.
