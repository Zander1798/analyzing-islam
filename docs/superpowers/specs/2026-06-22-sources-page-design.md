# Sources page (secondary-scholarship bibliography) — design

**Date:** 2026-06-22
**Status:** Approved (pending spec review)

## Goal

A new standalone page, `site/sources.html`, listing every **secondary source** —
scholarship, apologetics, and polemics from all sides (Muslim, Christian, secular/atheist,
academic) — that is **referenced inside** the catalog entries and dossiers. Linked from a
new "Sources" section on the About page. This surfaces the body of scholarship the project
leans on, which is currently invisible (buried, unlinked, in entry prose).

## Scope

- **In scope:** secondary works cited in entry/dossier prose — classical tafsirs, hadith
  commentaries, fiqh manuals, sira, academic monographs, named apologists/polemicists,
  and comparative (biblical/Jewish) scholarship.
- **Out of scope:** the readable scripture sources (Quran translation, the six hadith
  collections, the external comparative readers). Those are already documented in the
  About page's "The sources" section and are NOT repeated here.

## Decisions (from brainstorming)

- **Grouping:** by **type of work**, four groups —
  1. **Classical Islamic scholarship** (tafsir, hadith commentary, fiqh, sira)
  2. **Academic & historical scholarship** (Western/secular study of Islam)
  3. **Apologetics & polemics** (modern writers/debaters, all sides)
  4. **Other / comparative** (biblical, Jewish, cross-tradition)
  Alphabetical within each group.
- **Detail per source:** author/title **+ a one-line neutral descriptor** (e.g. "Tafsir
  Ibn Kathir — 14th-c. mainstream Sunni Qurʾanic commentary"). No citation counts shown,
  no per-source link-backs (kept internally for verification only).
- **Placement:** a "Sources" section on `about.html` directly under "Who this is for",
  with a short intro line + a link/button that opens `sources.html` in a **new tab**
  (`target="_blank" rel="noopener"`).

## Corpus (what gets mined)

- **Catalog: 1,524 entries** — prose lives in the 7 `site/catalog/*.html` files (the
  `site/category/*.html` files are a duplicate view → ignore to avoid double-counting).
  Per entry, the relevant prose is the `<p>` text under the "Why this is a problem / The
  Muslim response / Why it fails" sections, keyed by the entry's `id`.
- **Dossiers: 140 arguments** — prose lives in `arguments-data/*.json` (7 files), fields
  `context`, `premises`, `conclusion`, and `muslim_responses[].response/.counter`, keyed
  by argument `id`.

Total ≈ **1,664 prose blocks**. No structured source/bibliography data exists; scholarly
mentions are free-form prose with no markup, so they must be extracted from the text.

## Architecture / build pipeline

A new build script (`build-sources.py`) orchestrates four stages; the data is curated into
a JSON source-of-truth, then rendered to static HTML.

1. **Gather corpus** → `sources-corpus.json`: a list of `{entry_id, origin, text}` where
   `origin` is the catalog file or dossier slug. (Pure parsing: BeautifulSoup over
   `catalog/*.html`, JSON read over `arguments-data/*.json`. Dedupe catalog entries by id.)
2. **Extract — completeness-first (parallel agents over 100% of blocks)** →
   `sources-raw.json`. Recall is the priority (the user requires that no source be missed),
   so extraction is built as a wide net, not a sample:
   - **Total coverage:** *every* one of the ≈1,664 prose blocks is read — no sampling, no
     truncation, no top-N. Coverage is logged and asserted (see Completeness below).
   - **Pattern candidate net (deterministic, runs first):** a regex pass over the FULL
     corpus surfaces a superset of candidate mentions — capitalized multi-word name
     sequences, book-title shapes ("X's '<Title>' (<Year>)", "in <Title> (<Publisher>,
     <Year>)", "Tafsir <Name>", "Sahih/Sunan …"), and a seed controlled-vocabulary of
     known scholars/works (Ibn Kathir, al-Tabari, al-Qurtubi, Ibn Hajar, al-Nawawi, Kecia
     Ali, Mernissi, Leila Ahmed, Goldziher, Reliance of the Traveller, Fath al-Bari, …).
     This guarantees the known long tail is caught regardless of LLM judgment.
   - **Agent pass (per block):** each agent reads its blocks AND is handed that block's
     pattern-net candidates, and emits a record `{raw_mention, normalized_name, group,
     descriptor, entry_id}` for every secondary work named — **grounding rule:** only works
     literally present in the text, nothing invented; and it must not *drop* a pattern-net
     candidate without explicitly classifying it as a non-source (so dropped candidates are
     auditable, not silent).
   - **Second independent pass:** a different agent re-reads each block to catch anything
     the first missed; new captures are added. Repeated until a round yields nothing new
     (loop-until-dry).
3. **Normalize + curate** → `sources.json`: merge duplicates (same work, many phrasings)
   into one canonical record `{name, descriptor, group, aliases[], entry_ids[]}`; resolve
   group/descriptor conflicts; classify each pattern-net candidate as either a real source
   or an explicitly-recorded non-source (so nothing is silently discarded).
4. **Render** → `sources.html`: a static page in the site's dark style, grouped by the
   four types, alphabetical within each, each row = `name` + `descriptor`. Standard site
   nav/footer chrome. Built from `sources.json` so it is regenerable.

`sources.json` is the editable source-of-truth — corrections are made there, then re-render.

## Data model (`site/assets/data/sources.json`)

```json
{
  "groups": [
    { "key": "classical-islamic", "title": "Classical Islamic scholarship" },
    { "key": "academic",          "title": "Academic & historical scholarship" },
    { "key": "apologetics",       "title": "Apologetics & polemics" },
    { "key": "comparative",       "title": "Other / comparative" }
  ],
  "sources": [
    {
      "name": "Tafsir Ibn Kathir",
      "descriptor": "14th-c. mainstream Sunni Qurʾanic commentary",
      "group": "classical-islamic",
      "aliases": ["Ibn Kathir", "Tafsir Ibn Kathīr"],
      "entry_ids": ["...", "..."]
    }
  ]
}
```
`entry_ids` is retained for verification/spot-checking; it is NOT displayed on the page.

## Completeness (the hard requirement: no source may be missed)

100% recall on free prose cannot be *mathematically proven*, but the pipeline is built so
that coverage is total and any miss is **surfaced for review rather than silently dropped**:

- **Total block coverage, asserted.** A coverage ledger records every prose block id that
  was processed; the build FAILS if the processed set ≠ the full corpus set (no block may
  be skipped or truncated).
- **No silent candidate drops.** Every pattern-net candidate must be resolved to either a
  source or an explicit non-source with a reason; an unresolved candidate FAILS the build.
- **Completeness audit (the backstop).** After `sources.json` is built, an audit re-scans
  the ENTIRE corpus for any name-/title-shaped token (capitalized multi-word sequence,
  book-title pattern, honorific/`al-`/`Ibn`/`Tafsir`/author-year shapes) that is **not**
  covered by some source's `name`/`aliases` and **not** on the explicit non-source list.
  Anything it finds is written to `sources-unresolved.json` for human confirmation. The
  feature is **not considered done while `sources-unresolved.json` is non-empty** — each
  item is triaged into a source or the non-source list, then the audit re-runs, until it is
  empty. This converts "a miss" from invisible into a build-blocking item.
- **Grounded + reviewable.** Every listed source traces to ≥1 entry whose text contains one
  of its aliases (asserted), so nothing is fabricated. Descriptors are neutral/factual from
  general knowledge of each work; any the curator is unsure of are flagged, not guessed.
- Corrections go into `sources.json` and the page re-renders — the data file is the
  editable source of truth.

## Components / files

- Create: `build-sources.py` (gather + render; orchestrates extraction/curation).
- Create: `site/assets/data/sources.json` (curated source-of-truth, generated then editable).
- Create: `site/sources.html` (rendered page).
- Create: `site/assets/css/` additions or a small block in `sources.html` for the list styling
  (reuse `style.css` tokens; minimal new CSS).
- Modify: `site/about.html` — add the "Sources" section under "Who this is for".
- Scratch (not shipped): `sources-corpus.json` (+ coverage ledger), `sources-raw.json`,
  `sources-unresolved.json` (completeness-audit output; must be emptied before done),
  and a `non-sources.json` list of pattern-net candidates explicitly judged not to be
  sources (so they stay resolved on re-runs).

## Testing

- **Coverage (completeness):** assert the processed-block ledger equals the full corpus
  block set — every one of the ≈1,664 blocks was extracted (build fails otherwise).
- **Completeness audit:** assert `sources-unresolved.json` is empty — i.e. the corpus
  contains no name-/title-shaped token that isn't either a known source alias or an
  explicit non-source. (This is the "nothing slipped" gate.)
- **Grounding/verification:** every `sources.json` source has ≥1 `entry_id` whose corpus
  text contains one of the source's `aliases`/`name` (no orphan/invented sources).
- **Render:** `sources.html` contains all four group headings, every source from
  `sources.json` appears under its group, output is HTML-escaped, alphabetical within group.
- **About link:** the new "Sources" section exists under "Who this is for" and links to
  `sources.html` with `target="_blank"`.
- The extraction stage is LLM-based and not unit-tested; its recall is enforced by the
  coverage + completeness-audit gates above, not by sampling.

## Out of scope (future)

- Per-source link-backs to the citing entries on the page. Citation-count display.
- Re-listing the readable scripture sources. Search/filter on the sources page.
- Auto-linking scholarly mentions inside entry prose to this page.
