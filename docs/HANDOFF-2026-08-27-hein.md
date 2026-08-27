# Handoff for Hein — 2026-08-27

**PR:** https://github.com/Zander1798/analyzing-islam/pull/8
**Branch:** `stage12/repo-side` → `main`

Written from Zander's Windows checkout, which has no SSH key the VPS accepts.
Everything below that touches the VPS, the GitHub repo settings, or the Supabase
dashboard is yours to do.

---

## 1. The site on the VPS is a month behind `main`

Nothing pushed to `main` since the 2026-07-28 cutover has reached the VPS. I
checked by hashing every file changed since cutover on the live site against
`origin/main`:

| File | Live vs repo |
|---|---|
| `assets/css/quran-reader.css` | stale |
| `assets/css/style.css` | stale |
| `assets/data/quran-ar-index.json` | stale |
| `assets/js/bookmarks.js` | stale |
| `assets/js/build-editor.js` | stale |
| `assets/js/quran-lookup.js` | stale |
| `assets/js/quran-reader.js` | stale |
| `build-editor.html` | stale |
| `read-external/quran/data/concordance.json` | stale |
| `read-external/quran/surah-008.html` | stale |
| `read-external/quran/surah-037.html` | stale |
| `saved.html` | stale |
| `index.html` *(control)* | identical |
| `assets/js/auth.js` *(control)* | identical |

The two controls matching means the comparison is sound, not a hashing artifact.

### What those commits are

| Commit | Area | What users get |
|---|---|---|
| `1059d876` | Saved entries | Stalled bookmarks query times out at 15 s and shows *Try again* instead of a permanent spinner |
| `5490f087` | Saved entries | `list()` backward-compatible + cache-busted script URL, so a cached old `saved.html` with a fresh `bookmarks.js` cannot break mid-deploy |
| `3aa68a3b` | Build editor | Arabic scripture resolves to the site's own Saheeh International text instead of a word-by-word machine translation (fixes "These are the verses of the") |
| `37c6d0b5` | Build editor | Hadith lookup path tested; ambiguous citations reported rather than silently picked |
| `a879096a` | Interlinear | Morphology/meaning realigned to the correct word in 8:6 and 37:130; concordance repaired |

**No database migration is needed for any of these.** The only `supabase/*.sql`
files changed since cutover are `chatbot-kb.sql` and `kb-reader-credential.sql`,
which you already applied for the KB ingest.

## 2. What the PR adds

| Commit | Area | What changes |
|---|---|---|
| `a9b52cb4` | Link-preview card | New OG image built from the hero footage with the current counts (1,524 entries / 31 categories). JPEG at 111 KB — the PNG was ~360 KB and WhatsApp silently drops previews over roughly 300 KB. 166 pages repointed at the **versioned** `og-image-v2.jpg`; scrapers cache by URL, so the old filename would never refresh. Old `og-image.png` left in place so cached previews don't 404. |
| `315d9e1b` | Stage 12, repo side | `site/assets/js/config.js` now matches what the VPS serves, byte for byte. `--exclude='assets/js/config.js'` removed from the staged `deploy-vps.yml`. `site/CNAME` removed. `CLAUDE.md`, `AGENTS.md`, `EXECUTION-PLAN.md` updated. New `docs/migration/STAGE-12-EXECUTOR-CHECKLIST.md`. |

The `agent-docs` check runs on the PR. The mirror passed locally; if it's red on
your side it's a line-ending artifact — `node scripts/mirror-agents-md.mjs` fixes
it.

Merging will trigger a GitHub Pages build because `site/**` changed. Harmless —
Pages no longer feeds the live site — but you'll see it in Actions. **It is not
the deploy.**

## 3. Deploy

```bash
git checkout main && git pull
rsync -az --delete -e ssh site/ deploy@72.60.17.245:/var/www/analyzingislam/
```

**Drop the `--exclude='assets/js/config.js'` from your rsync.** The repo copy is
now identical to the server's, so today the exclude does nothing — but it would
silently swallow the next real `config.js` change. That is the trap the runbook's
Stage 12 warns about.

Post-deploy:

```bash
curl -s  https://analyzingislam.com/assets/js/config.js | grep -c api.analyzingislam.com   # 1
curl -s  https://analyzingislam.com/assets/js/config.js | grep -c cndmksrilytnpgstvmxb    # 0
curl -sI https://analyzingislam.com/assets/og-image-v2.jpg | head -1                       # HTTP/1.1 200
curl -s  https://analyzingislam.com/ | grep -o 'og-image-v2.jpg' | head -1                 # present
curl -s  https://analyzingislam.com/saved.html | grep -o 'bookmarks.js[^"]*'               # has ?v= cache-bust
```

Then re-scrape `https://analyzingislam.com/` in Facebook's Sharing Debugger
(https://developers.facebook.com/tools/debug/) so their cache picks up the new
card. WhatsApp uses the same cache.

## 4. Two things I found that need you, not the repo

### Supabase Cloud does not resolve

```
cndmksrilytnpgstvmxb.supabase.co
  local resolver → NXDOMAIN      8.8.8.8 → NXDOMAIN
  1.1.1.1        → NXDOMAIN      DoH     → {"Status":3}
supabase.co      → 76.76.21.21   (control — resolves normally)
```

A *paused* project still resolves. NXDOMAIN is what a *deleted* one looks like.
Nothing in `EXECUTION-PLAN.md`, the handoffs, or any commit since cutover records
pausing or deleting it. **Please check the dashboard** — and confirm the Stage 1
backup still exists, because if the project was deleted, that backup is the only
remaining copy of the pre-migration state. Keep it permanently either way.

Also still open from the cutover notes: rotating the Cloud database password
(pasted into a chat). Moot if the project is gone — confirm which.

### GitHub Pages TLS is broken for the apex

`gh api repos/Zander1798/analyzing-islam/pages` → `"state": "bad_authz"`.
Expected once the apex A records moved to the VPS; Let's Encrypt can no longer
validate for Pages. Together with the above it means **the rollback path Stage 12
was protecting had already expired before anyone chose to abandon it.** Recorded
as correction #17 in `EXECUTION-PLAN.md`.

## 5. Rest of Stage 12 — in this order

Full detail: `docs/migration/STAGE-12-EXECUTOR-CHECKLIST.md`.

1. **Add the three repository secrets.** `gh secret list` currently returns
   nothing.

   ```
   VPS_SSH_KEY   private key for deploy@VPS
   VPS_HOST      72.60.17.245
   VPS_USER      deploy
   ```

   **Do not do steps 2–3 before this.** Retiring `pages.yml` while the secrets
   are missing leaves every `site/**` push deploying nowhere. The static site
   keeps serving from the VPS, so nothing looks broken — the pipeline is just
   dead and silent.

2. `gh auth refresh -s workflow` (needed to push anything under
   `.github/workflows/`), then
   `git mv .github/workflows-staged/deploy-vps.yml .github/workflows/`

3. `git rm .github/workflows/pages.yml`

4. Disable Pages: `gh api -X DELETE repos/Zander1798/analyzing-islam/pages`

5. First workflow deploy — its "Verify the deploy actually landed" step asserts
   `config.js` on the live site names the self-hosted API and not the Cloud host.

6. Absolute-URL sweep against the **live** DB, must be 0. Use `docker exec -i`
   — without `-i`, `psql` can receive no SQL from a heredoc and still exit 0.

   ```sql
   select count(*) from public.profiles
   where avatar_url like '%cndmksrilytnpgstvmxb%'
      or banner_url like '%cndmksrilytnpgstvmxb%';
   ```

   Any hit is *already* a broken image on the live site, since the Cloud host
   is gone. Fix rather than just count.

7. Record what happened to the Cloud project.

**Do not revoke the Cloudflare API token** — correction #16. Apex cert renewal
is DNS-01 against `/home/deploy/secrets/cloudflare.ini`; revoking breaks renewal
without touching the current cert, so it surfaces weeks later.

## 6. Not in this PR, deliberately

- Chatbot branches (`feature/chatbot-retrieval-quality`, `feature/chatbot-video-ingest-clean` / PR #6) — separate track, owner-only, unchanged.
- Zander's Quran book prototype files (`book-design/vol1-quran/*`) — uncommitted local work, untouched.
- `backup-supabase.py` still hard-codes the Cloud URL. It's the pre-migration JSON dump tool and is now dead code; left as-is for a separate cleanup.
