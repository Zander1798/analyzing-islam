# Design — Rebuild AnalyzingIslam.com from the Final Seven-Volume Book Series

**Date:** 2026-06-18
**Status:** Approved (design); pending spec review → implementation plan

## Goal

Bring the live site into exact agreement with the final, campaign-verified
seven-volume "Analyzing Islam" book series. Three layers must align so that the
entry a reader sees, the source verse/hadith it cites, and every published count
all come from one authority:

1. **Entries** — replace the site catalog with the books' corrected entries.
2. **Source text ("read" pages)** — rebuild the Qur'an and hadith reader pages
   from the exact sources the books were verified against.
3. **Links + counts** — every citation resolves to the precise verse/hadith, and
   every site-wide figure reflects the new data.

The goat quiz **questions** are out of scope (they are sourced from verses, not
entries); only the quiz's source-anchor links are re-validated.

## Sources of truth (read-only inputs)

| Input | Location | Role |
|---|---|---|
| Book entries (1,524) | `../Analyzing Islam Books/data/*_v2.json` | Entry content authority |
| Hadith source text | `hadith-json/*.json` (6 collections, AhmedBaset dataset, scraped from sunnah.com) | Hadith reader text |
| Qur'an source text | `quran-json/chapters/*.json` (Saheeh International, tanzil origin) | Qur'an reader text |

- **Only the `_v2` book files** are authoritative; legacy `*_entries.json` and
  `v2_backup_*` in the book repo are stale and must not be read.
- Volume → file map: I Qur'an `quran_entries_v2.json` (275) · II Bukhari +
  III Muslim share `hadith_entries_v2.json` split by `source` (315 + 264) ·
  IV Abu Dawud `abudawud_entries_v2.json` (181) · V Tirmidhi
  `tirmidhi_entries_v2.json` (226) · VI Nasa'i `nasai_entries_v2.json` (113) ·
  VII Ibn Majah `ibnmajah_entries_v2.json` (150). **Total 1,524.**
- Qur'an translation confirmed: **Saheeh International** (stated in the book
  front-matter/cover; verse quotes carry its signature bracketed glosses).

## The numbering contract (the linchpin)

Everything is bound by one deterministic ref → anchor mapping:

- **Qur'an:** `Q s:v` → `#s{s}v{v}` (e.g. `Q 2:25` → `#s2v25`).
- **Hadith:** `<Collection> N` → `#h{idInBook=N}` (e.g. `Bukhari 224` → `#h224`).

Verified: book ref `Bukhari 224` ("Muhammad urinated standing up at a dump") ==
`hadith-json` `idInBook 224` ("Once the Prophet (ﷺ) went to the dumps... and
passed urine while standing"). Bukhari `idInBook` runs 1–7277 continuously.

Because readers are generated *from* `hadith-json` keyed on `idInBook`, the anchor
a citation targets exists **by construction** — no fragile text-fingerprint
matching for links. (A residual risk remains where a book ref uses a number that
is not the `idInBook` for that collection; the validator in §4 catches these.)

## Component design

### 1. Read-page rebuild (the "HTML sources")

- **Unified hadith builder.** One script generates all six hadith readers from
  `hadith-json/*.json`, full collections, with `#h{idInBook}` anchors and markup
  matching the existing reader CSS. This moves **Bukhari & Muslim off the Muhsin
  Khan PDF** (`bukhari-re.txt`, `en_Sahih_*.pdf`) onto sunnah.com text — the core
  source fix. Existing `build-hadith-readers.py` already does this for the other
  four collections and is the basis to extend.
- **Retire** `build-bukhari-reader.py` and `build-ocr-hadith-readers.py` (PDF/OCR
  paths) once the unified builder covers all six.
- **Qur'an** regenerated from `quran-json` with `#s{s}v{v}` anchors (already
  Saheeh International and already this anchor scheme — effectively a verify/refresh
  via the existing `build-quran-reader.py`).
- **Out of scope:** external readers (`read-external/` — Bible, Ibn Kathir,
  Talmud, Tanakh, Josephus, etc.) are untouched.

### 2. PDF removal + "Go to site" card

- Delete the download-PDF feature entirely: the per-volume PDF reader pages
  (`read/*-vN.html`, built by `build-volume-readers.py`) and any "Download PDF"
  buttons/cards.
- Where those cards appeared, render a **"Go to site" card linking out to
  sunnah.com** at the specific hadith (external source-verification affordance).
  Exact sunnah.com URL scheme and card placement resolved during implementation.

### 3. Entry sync — mirror the books exactly (1,524)

- **Full regeneration**, not in-place patching: render the 1,524 book entries into
  the 7 `catalog/*.html` pages and rebuild `catalog-entries.json` (the lightweight
  index: id, source, title, ref, categories, strength, url) from the same data.
- **Final state = exactly the 1,524 book entries.** Book-only entries are added;
  site-only entries (dropped/merged during the book campaign) are removed. The site
  ends as a faithful mirror of the books.
- **All-new content and all-new slugs.** Nothing old is retained. Slugs are
  generated deterministically from the new title/ref. Consequence accepted: old
  external deep links to specific entry URLs may no longer resolve; all *internal*
  links are regenerated so nothing breaks inside the site.
- **Reporting map (not a merge):** produce a book↔site content-key map (key =
  source/volume + normalized `verse_refs[0]` + normalized title) purely to report
  matched / book-only / site-only counts for human eyeballing. **Never match or
  merge by `id`** — a prior ID-match scrambled 1,182 `muslim_response` fields.
- **Verbatim transfer.** Preserve `\n\n` paragraph breaks, en-dashes,
  transliterations, the ﷺ glyph, and `"...partial quote"` ellipses. Do not
  re-edit, paraphrase, or "clean up."
- **Citation-framing policy (binding).** Polemical sources (WikiIslam, Shamoun,
  Spencer, Wood, Bat Ye'or, etc.) stay framed as critics/commentators, never as
  scholars, never removed.

### 4. Link alignment + validation (hard gate)

- Every citation — entry headings, inline body verse/hadith refs, and goat-quiz
  `source` links — is rendered from its ref via the single ref→anchor function
  (§ numbering contract).
- A validator asserts **every** such link resolves to an anchor that exists in the
  regenerated read pages. **Zero unresolved links is a hard gate** before publish.
  Unresolved refs are reported for manual reconciliation (likely book-ref vs
  `idInBook` mismatches).

### 5. Site-wide counts / information

Recompute every hardcoded figure from the new data and update in place:

- `stats.html` — total (1,541 → new), per-category counts, strength-tier
  percentages, word-frequency tables, and all derived prose figures.
- `meta`/OG descriptions and image-alt on `stats.html` and `goat.html`
  ("1,541 entries across 30 categories" → new values).
- Home/index, about, and per-category pages — any catalog figures.

Counts should be computed programmatically from the regenerated catalog data, not
hand-typed, so they cannot drift again.

### 6. Goat quiz

Questions unchanged. Only the per-question `source` anchor links
(`read/quran.html#s…v…`, and any hadith links) are re-pointed and run through the
§4 validator against the rebuilt read pages.

## Safety & process

- **Dedicated branch off a clean base.** The current working tree is very dirty
  (many untracked one-off scripts and modified files); none of that is swept into
  this work.
- **Back up** current `catalog/*.html`, `catalog-entries.json`, and `read/*.html`
  before writing.
- **Pilot Vol VI (Nasa'i, 113 entries)** end-to-end — entries + reader + links +
  counts — and verify before the full rollout. Verify entries with and without
  `muslim_response`/`why_fails` and ones citing polemical sources.
- **Confirm the site deploy path** (static host? Supabase?) during early recon; it
  affects how changes go live but not this design.
- **Post-rollout audit:** per-volume site counts == book counts; stratified
  random sample (~30–50) checked against the JSON; all category/index links and
  the link validator clean.

## Testing

- Unit tests for the ref→anchor function (Qur'an and each hadith collection,
  including ranges and letter-suffixed numbers like `Muslim 2020a`).
- Link-resolution validator (entries + quiz) — must report zero unresolved.
- Count reconciliation: regenerated catalog totals == book `_v2` counts per volume
  and per category.
- Existing `tests/` continue to pass.

## Out of scope

- Goat quiz **question content** (verse-sourced, unchanged).
- External `read-external/` reader pages.
- The book PDFs themselves (this is a site sync, not a book edit).
- Any content re-editing of the book text (faithful transfer only).

## Open items to resolve in implementation (not blocking design)

- Exact sunnah.com URL scheme for the "Go to site" card and where the card renders.
- Site deployment/publish mechanism.
- Confirm each collection's book-ref numbering == `idInBook` (validator-driven);
  handle any collection that uses a different reference number.
