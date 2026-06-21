# Lazy-load scripture readers — design

**Date:** 2026-06-21
**Status:** Approved (pending spec review)
**Issue:** Clicking a scripture citation is too slow. Each "readable source" is a
single monolithic HTML file (`read/bukhari.html` 16 MB, `read/muslim.html` 14 MB,
`read/nasai|abu-dawud|tirmidhi|ibn-majah.html` 7–10 MB, `read/quran.html` 3.2 MB).
A citation like `read/bukhari.html#h299` forces the browser to download and parse
the entire collection before scrolling to one hadith — several seconds on mobile.

## Goal

Make clicking any scripture citation land on the cited verse/hadith **near-instantly**,
**without changing any of the ~31,812 existing inbound links** (across 292 files) that
point at `read/{reader}.html#{anchor}`.

## Constraints discovered during exploration

- **Anchors are stable and unique.** Quran verses are `<li id="s{n}v{m}">` inside
  `<article class="surah" id="surah-{n}">`. Hadith are `<article id="h{num}">` inside
  `<section class="hadith-book" id="book-{cid}">`. Hadith ids are globally unique within
  a collection (verified: bukhari.html has 7,563 ids, all unique — they are the
  sunnah.com reference numbers, non-contiguous but unique).
- **Search** (`assets/js/reader-search.js`) already supports two modes: DOM-scan for
  single-page readers, and a **prebuilt-JSON-index mode** (`INDEXED_SOURCES`) for
  multi-page readers (bible-interlinear, quran-interlinear, ibn-kathir, talmud). The
  multi-page mode navigates to `contentBase + entry.href`.
- **Highlights** (`assets/js/highlights.js`) anchor by element `id` + text offsets and
  silently drop if the anchor isn't in the DOM. They work natively when the anchor IS
  present.
- **snap-to-hash** (`assets/js/snap-to-hash.js`) does `getElementById(hash)` then
  force-scrolls; it does nothing if the target isn't in the DOM. Exposes
  `window.__snapToHash`.
- **The site already uses the per-chapter-page pattern**: `read-external/bible/{book}.html`
  and `read-external/quran/surah-{NNN}.html` are small standalone pages. This design
  generalises that proven pattern to the main Quran + hadith readers.
- **Builders + inputs exist**: `build-quran-reader.py` (input `quran-json/chapters/{1..114}.json`),
  `build-hadith-readers.py` (canonical builder for all 6 hadith readers; input
  `hadith-json/{collection}.json`). `build-compare-index.py` exists. Post-build decorators:
  `add-favicon-links.py`, `add-reader-search.py`, `inject-splitters.py`,
  `inject-auth-scripts.py`/`sync-auth-scripts.py`, `add-og-tags.py`.

## Chosen approach

**Small standalone pages + a smart shell at the old URL.** (Chosen over single-page
inject-on-scroll because it reuses the site's proven multi-page reader pattern, has no
layout-shift/scroll-jump risk, and lets search/highlights/snap work natively per page.)

### 1. File layout

- **Quran:** `read/quran/{n}.html`, one page per surah, `n = 1..114`. Verse anchors
  `#s{n}v{m}` unchanged.
- **Hadith:** `read/{collection}/{cid}.html`, one page per book/chapter (`cid` = the
  `chapterId` already used to build `id="book-{cid}"`). Hadith anchors `#h{num}` unchanged.
- Each page is ~20–150 KB.

### 2. The old URLs become smart shells (keeps every inbound link working)

`read/quran.html` and `read/{collection}.html` remain at their exact paths but are
replaced by a tiny shell page whose inline script runs on load and on `hashchange`:

- **With a verse/hadith anchor** → resolve the owning sub-page and
  `location.replace(subPage + "#" + anchor)`:
  - Quran: parse `s{n}v{m}` → surah `n` → `read/quran/{n}.html`. No manifest needed.
  - Hadith: look the anchor up in a small per-collection manifest
    `read/{collection}/anchors.json` (`{ "h299": "3", ... }` mapping anchor → `cid`) →
    `read/{collection}/{cid}.html`. The manifest is fetched once, cached.
- **No anchor** → render as a **landing page**: the collection's table of contents
  (every surah/book as a link to its sub-page) + the existing reader search box. This
  matches the existing `read-external/quran.html` interlinear landing and is recognised
  by `reader-search.js` `isIndexLandingPage()`.

`location.replace` (not `location.href`) so the shell does not become a back-button trap.

### 3. Sub-pages are full standalone readers

Each sub-page carries the normal reader chrome: site nav, the collection's TOC sidebar
(links to sibling sub-pages, current one marked), the search box, the single surah/book
content, **prev/next chapter links** (top and bottom), and the highlights card. Because
the target anchor is physically present in the small DOM:

- `snap-to-hash.js` scrolls to it natively and instantly — no change needed.
- `highlights.js` paints natively (anchor in DOM) — no re-injection plumbing.
- `verse-parser.js` `candidateIds()` gives instant in-page jumps for the search box.

### 4. Search

- Add `quran` and the 6 hadith slugs to `reader-search.js` `INDEXED_SOURCES`, each with
  `indexPath: assets/compare-index/{reader}.json` and the appropriate `contentBase`
  (`read/quran/`, `read/bukhari/`, …).
- Extend `isIndexLandingPage()` / slug routing so the new landing pages (`read/quran.html`,
  `read/{collection}.html`) and the sub-pages both route search through the index.
- Build a compact index JSON per reader: array of `{ ref, text, href }` where `href` is
  `{cid-or-n}.html#{anchor}` relative to `contentBase`. Generate via an extension to
  `build-compare-index.py`.
- Within a loaded sub-page, casual refs still resolve instantly through
  `VERSE_PARSER.candidateIds()` against the local DOM; cross-page refs fall through to the
  index and navigate.

### 5. Build pipeline changes

- `build-quran-reader.py`: emit 114 surah pages (`read/quran/{n}.html`) + the
  `read/quran.html` shell/landing. Add prev/next + per-page TOC. No manifest.
- `build-hadith-readers.py`: emit per-book pages (`read/{collection}/{cid}.html`) + the
  `read/{collection}.html` shell/landing + `read/{collection}/anchors.json`. Add
  prev/next + per-page TOC.
- Fold the post-build decorators (favicons, reader-search, splitters, auth scripts, og
  tags, highlights wiring) into the builders, or re-run them across the new tree, so every
  generated page is fully decorated and idempotent.
- Extend `build-compare-index.py` to emit `assets/compare-index/{reader}.json` for quran +
  the 6 hadith collections.
- A single orchestration step (or documented run order) regenerates everything.

### 6. Verification

- After build, spot-check a representative sample of real inbound links from dossiers
  (e.g. `read/quran.html#s23v13`, `read/bukhari.html#h299`, plus links to the last
  book/surah and to verses deep in a chapter) and confirm each resolves to the correct
  sub-page and scrolls to the anchor.
- Confirm search from a landing page and from a sub-page jumps correctly.
- Confirm a saved highlight restores on a sub-page.
- Confirm prev/next + TOC navigation.
- Local run before deploy; then push `site/` (GitHub Pages auto-deploys).

### 7. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Extra hop (shell → sub-page) for cited links | `location.replace`, tiny shell, manifest cached |
| Many more files (~114 + ~600) | Fine for GitHub Pages; each tiny |
| Loss of continuous cross-chapter scroll | Prev/next links (trade-off accepted) |
| Old monolithic files | Replaced by shell at same filename; sample inbound links verified pre-deploy |
| Decorator drift between pages | Fold decorators into builders; keep idempotent |
| Hadith manifest size | One small JSON per collection (anchor→cid); gzips well; cached |

## Out of scope

- The `read-external/*` readers (bible, interlinear, ibn-kathir, talmud, etc.) already use
  the per-page pattern and are unaffected.
- No change to the citation links themselves, the catalog, dossiers, or book builders.
- No change to highlight storage schema or auth.
