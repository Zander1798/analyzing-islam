# Source-link readability fix — 2026-07-14

## Problem
Cited source links (catalog entries + dossiers) pointed heavily at Internet
Archive. A large share pointed at **pirate `opensource`/`community` uploads of
in-copyright books** (e.g. `the-truth-about-muhammad-robert-spencer_202605`,
399 uses). Those are unstable — Internet Archive darkens/removes them and they
intermittently return **"Bad Request — could not currently be handled by the
service."** Goal: every source link must open to the actual, readable, legal,
permanent document.

## Root cause of the "no pipeline" situation
The external-source `<a class="src-link">` links live **only in the rendered
HTML** (added in commit `37dba3e`). They are NOT in the book data
(`../Analyzing Islam Books/data/*_entries_v2.json`) nor in `arguments-data/*.json`.
So `build-catalog-pages.py` / `build-category-pages.py` / `build-arguments.py`
(which regenerate entry HTML from that link-less data) would **wipe** the links.
There was no re-runnable stage that reproduced them.

## The fix — a new canonical, idempotent pipeline stage
1. **`source-link-map.json`** — canonical map. Key = the archive.org identifier
   that appears in a `src-link` href; value = the single best readable target.
   - `tier: open` — fully readable, no login (public-domain / folkscanomy / OAPEN / DLI scans)
   - `tier: cdl`  — readable after a free Internet Archive borrow (in-copyright books; the only *legal* full-read option)
   - `tier: openlibrary` / `publisher` — obtain page, used only when no legal readable scan exists
   - `tier: reader` — points at the site's own hadith reader (sunnah.com)
   - One key can carry `rules[]` + `default_url` to split a single identifier that
     was reused for two different books (see `tolerance-and-coercion-…`: Cook's
     *Forbidding Wrong* vs Friedmann's *Tolerance and Coercion*).
   - Already-good scans are self-mapped so coverage can be asserted at 100%.
2. **`apply-source-links.py`** — idempotent. Rewrites every `src-link` href to its
   canonical target. `--check` reports drift and lists any unmapped archive id
   (exit 1 if changes needed). All duplicate variants of a book converge to one link.

### REQUIRED run order (this is the "proper pipeline")
```
python build-catalog-pages.py      # or build-category-pages.py / build-arguments.py
python apply-source-links.py       # RE-APPLY canonical source links (they live in HTML only)
python apply-source-links.py --check   # must print 0 rewrites, 0 unmapped
```
If `--check` lists an unmapped archive identifier, add it to `source-link-map.json`
(resolve the best readable target first — verify via `https://archive.org/metadata/<id>`;
avoid any item whose `collection` is only `opensource`/`community`).

## What changed this pass
- 35 pirate books remapped → **594 `src-link` hrefs rewritten across 87 HTML files**.
- 12 remapped to legitimate scans we already host; 22 web-verified to open/CDL/OpenLibrary; 1 hadith → sunnah.com.
- `source-urls.json` master map updated (129 entries) to match.
- **Verified:** 135 unique archive.org links now on site — 0 dead, **0 pirate/opensource-only remaining**.

## Known trade-offs (for review)
- A few **open** targets are folkscanomy uploads of in-copyright books
  (Ehrman *How Jesus Became God* / *Text of the NT*, Wansbrough, Hagarism). They are
  fully readable now but *could* be removed later. CDL fallbacks exist if you prefer
  maximum permanence over no-login reading (see per-book notes in git history / agent output).
- `Historical-Jesus` (a Great Courses lecture course) has **no legal free full copy**;
  it points to the publisher product page.
- Goldziher *Muslim Studies II* open scan is the **German** original (public domain);
  the English (Stern, 1971) is CDL-only (`muslimstudiesmuh0000gold`) if an English link is wanted.
- ~96 CDL books (borrow after free login) were left as-is: for in-copyright academic
  titles that is the only legal full-read option, and those pages open reliably (no Bad Request).

## NOT yet done
- Not committed / not deployed — working tree only.
- Books repo (`../Analyzing Islam Books`) not touched; this is site-side (same pattern as
  the strength-reframe/site-rebuild passes — fold into the next site→books sync).
