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
2. **Extract (parallel agents)** → `sources-raw.json`: each agent reads a batch of prose
   blocks and emits, for every secondary work actually named in the text, a record
   `{raw_mention, normalized_name, group, descriptor, entry_id}`. **Grounding rule:** only
   works literally named in the provided text may be emitted — nothing invented. The
   `entry_id` ties each capture back to where it appears.
3. **Normalize + curate** → `sources.json`: merge duplicates (same work, many phrasings)
   into one canonical record `{name, descriptor, group, aliases[], entry_ids[]}`; resolve
   group/descriptor conflicts; drop false positives (e.g. a person who isn't a cited
   source). A controlled vocabulary of the known high-frequency names (Ibn Kathir,
   al-Tabari, al-Qurtubi, Ibn Hajar, al-Nawawi, Kecia Ali, Mernissi, Leila Ahmed,
   Goldziher, Reliance of the Traveller, Fath al-Bari, …) seeds high-recall matching;
   the agents catch the long tail.
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

## Accuracy & caveats

- **Best-effort, grounded, reviewable.** Every listed source traces to ≥1 entry that names
  it, so the list is verifiable and nothing is fabricated. A verification step asserts each
  `sources.json` entry's `entry_ids` actually contain the mention.
- A handful of obscure one-off mentions may be missed (recall < 100%), and a few
  type-classifications are judgment calls. Descriptors come from general knowledge of each
  work, kept neutral/factual; uncertain ones are flagged for review rather than guessed.
- The result is refinable: corrections go into `sources.json` and the page re-renders.

## Components / files

- Create: `build-sources.py` (gather + render; orchestrates extraction/curation).
- Create: `site/assets/data/sources.json` (curated source-of-truth, generated then editable).
- Create: `site/sources.html` (rendered page).
- Create: `site/assets/css/` additions or a small block in `sources.html` for the list styling
  (reuse `style.css` tokens; minimal new CSS).
- Modify: `site/about.html` — add the "Sources" section under "Who this is for".
- Scratch (not shipped): `sources-corpus.json`, `sources-raw.json`.

## Testing

- **Grounding/verification:** a check that every `sources.json` source has ≥1 `entry_id`
  whose corpus text contains one of the source's `aliases`/`name` (no orphan/invented
  sources).
- **Render:** `sources.html` contains all four group headings, every source from
  `sources.json` appears under its group, output is HTML-escaped, alphabetical within group.
- **About link:** the new "Sources" section exists under "Who this is for" and links to
  `sources.html` with `target="_blank"`.
- The extraction stage is LLM-based and not unit-tested; its output is gated by the
  grounding verification above and human spot-check.

## Out of scope (future)

- Per-source link-backs to the citing entries on the page. Citation-count display.
- Re-listing the readable scripture sources. Search/filter on the sources page.
- Auto-linking scholarly mentions inside entry prose to this page.
