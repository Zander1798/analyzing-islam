# Handoff — Entry Migration & Site Update
**Date:** 2026-05-30  
**Branch:** main (deployed to analyzingislam.com via GitHub Pages)  
**Status:** Complete and live

---

## What was done this session

### 1. Full entry replacement from 7 book HTML sources
All 1,541 catalog entries were replaced with the final published book versions. The authoritative source files live here:

| Volume | Source | HTML file |
|--------|--------|-----------|
| Vol I  | The Quran | `C:\...\Analyzing Islam Books\output\book.html` |
| Vol II | Sahih al-Bukhari | `C:\...\Analyzing Islam Books\output\book_v2.html` |
| Vol III | Sahih Muslim | `C:\...\Analyzing Islam Books\output\book_vol3.html` |
| Vol IV | Sunan Abu Dawud | `C:\...\Analyzing Islam Books\output\book_vol4.html` |
| Vol V  | Sunan al-Tirmidhi | `C:\...\Analyzing Islam Books\output\book_vol5.html` |
| Vol VI | Sunan al-Nasa'i | `C:\...\Analyzing Islam Books\output\book_vol6.html` |
| Vol VII | Sunan Ibn Majah | `C:\...\Analyzing Islam Books\output\book_vol7.html` |

The books add two sections not previously on the site: **THE MUSLIM RESPONSE** and **WHY IT FAILS**, each grounded in real scholarly citations (Spencer, WikiIslam, Ibn Kathir, al-Nawawi, al-Tabari, al-Qurtubi, Ibn Hajar, Patricia Crone, Nerina Rustomji, Sam Shamoun, etc.).

**Entry counts:**
| Source | Count |
|--------|-------|
| Quran | 262 |
| Bukhari | 301 |
| Muslim | 250 |
| Abu Dawud | 178 |
| Tirmidhi | 230 |
| Nasai | 146 |
| Ibn Majah | 174 |
| **Total** | **1,541** |

(Down from 1,549 — 8 removed by deduplication already done in the books.)

### 2. Files changed
- `site/catalog/*.html` (7 files) — full entries replaced
- `site/assets/data/catalog-entries.json` — rebuilt from scratch
- `site/category/science.html` — new (Cosmology renamed to Science)
- `site/index.html` — total count, category counts, spotlight links, science card
- `site/about.html` — count and Cosmology→Science
- `site/stats.html` — all hardcoded numbers recalculated
- `site/assets/js/build-editor.js` — ct-cosmology → ct-science
- `site/build.html`, `site/compare.html`, `site/faq.html`, `site/goat.html`, `site/play.html`, `site/stats.html`, `site/catalog.html` — count updates

### 3. Cosmology → Science rename
- Category slug changed from `cosmology` to `science` everywhere
- `site/category/science.html` created (was `cosmology.html`)
- All 7 catalog filter chips updated
- `build-editor.js` entry updated
- `index.html` category card updated (123 entries)
- `about.html` category list updated
- Old `category/cosmology.html` left in place as dead page (returns 0 results since no entries have `cosmology` slug — fine for backward compat, no 404)

### 4. Verse/hadith/Bible ref links in entry bodies
**1,321 cite-link hyperlinks added** to inline body-text citations across all 7 catalog files:
- Quran: `Q S:V` patterns → `../read/quran.html#sSvV` (1,008 in quran.html alone)
- Hadith cross-refs (e.g. Bukhari ref in a Muslim entry) → appropriate reader
- OT Bible (Genesis, Isaiah, Deuteronomy, etc.) → `../read-external/tanakh.html#{book}-{C}-{V}`
- NT Bible (Matthew, Revelation, etc.) → `../read-external/new-testament.html#{book}-{C}-{V}`

Blockquote text (the quoted verse/hadith) was intentionally NOT linked — display text preserved exactly as written.

### 5. Stats page recalculation
All hardcoded numbers in `stats.html` were recalculated:
- Overall strength: Basic 376 (24%), Moderate 688 (45%), Strong 477 (31%)
- Rank table rebuilt (17 categories ≥40% Strong with ≥10 entries)
- All cat-meta counts and stack bars updated

### 6. Commits deployed
| Commit | Description |
|--------|-------------|
| `cf48fb4` | feat: replace all 1,541 catalog entries with book-authoritative versions |
| `fb3057a` | fix: update all hardcoded numbers in stats.html to match new entry counts |
| `a1ac024` | feat: add cite-link hyperlinks to all inline verse refs in entry bodies |

All deployed successfully via GitHub Actions (~1m30s each).

---

## Build tools committed to repo
These scripts are in the project root and can be re-run if entries need re-migrating:
- `update_stats.py` — recalculates all stats.html numbers from catalog-entries.json
- `link_inline_refs.py` — adds cite-link anchors to body text refs (safe to re-run: skips existing links)

The main migration scripts (`migrate_entries.py`, `update_site_files.py`) were deleted after use but are documented in memory.

---

## Known outstanding items

### Stats page prose descriptions
The `stats.html` deep-dive section has analytical prose with inline counts (e.g. *"Seventeen of twenty-two are Strong-tier"* for Child Marriage, which now has 14 entries). These were not auto-fixed because they're in authored narrative text. A manual proofreading pass on `stats.html` sections would clean these up.

### Codeberg mirror quota exceeded
The Codeberg mirror (`https://codeberg.org/Zandervv0610/Analysing-Islam.git`) rejects all pushes with `Forgejo: Quota exceeded`. Pre-existing, non-blocking — GitHub Pages is the only live deployment target.

### category/cosmology.html
Left in place as a dead page. It still exists as a file but the `cosmology` category slug no longer exists in any entry, so it renders empty. Could be deleted or turned into a redirect to `science.html` in a future cleanup.

---

## Architecture notes

### Entry ID preservation
Entry IDs were preserved by matching titles between the books and the original `catalog-entries.json` (loaded from `git show HEAD:site/assets/data/catalog-entries.json`). ~1,542 of 1,541 entries matched and kept their original IDs. Truly new entries got fresh generated IDs (`{source}-{hadith-number}-{title-slug}`).

### Verse link anchor formats
- Quran reader: `../read/quran.html#s{surah}v{verse}` (e.g. `#s2v65`)
- Hadith readers: `../read/{source}.html#h{number}` (e.g. `../read/bukhari.html#h224`)
- Tanakh reader: `../read-external/tanakh.html#{book}-{chapter}-{verse}` (e.g. `#genesis-1-26`)
- NT reader: `../read-external/new-testament.html#{book}-{chapter}-{verse}` (e.g. `#matthew-24-29`)
- Bible individual files: `../read-external/bible/{3-letter-code}.html#{code}-{chapter}-{verse}` (alternate path, not used in catalog entries)

### Book entry format vs site entry format
The books use `class="entry-page section-body"` divs with sequential `id="entry-NNN"` IDs. The site uses `class="entry"` divs with semantic `id="{source}-{ref}-{title-slug}"` IDs. `migrate_entries.py` handled the full conversion.

### Category counts (new)
| Category | Count | % Strong |
|----------|-------|----------|
| strange | 566 | 9% |
| women | 338 | 34% |
| prophet | 321 | 48% |
| logic | 222 | 37% |
| disbelievers | 179 | 49% |
| science | 123 | 29% |
| contradiction | 102 | 40% |
| morality | 89 | 69% |
| eschatology | 82 | 41% |
| governance | 77 | 65% |
| warfare | 59 | 63% |
| jesus | 55 | 35% |
| allah | 52 | 85% |
| hudud | 44 | 75% |
| ritual | 43 | 35% |
| abrogation | 42 | 50% |
| antisemitism | 42 | 62% |
| magic | 41 | 12% |
| sexual | 38 | 58% |
| scripture | 34 | 79% |
| privileges | 33 | 21% |
| slavery | 31 | 45% |
| preislamic | 26 | 54% |
| hell | 25 | 28% |
| paradise | 25 | 16% |
| apostasy | 23 | 65% |
| lgbtq | 16 | 31% |
| childmarriage | 14 | 79% |
| gross-vile | 8 | 62% |
| incest | 3 | 67% |
| animals | 2 | 100% |
