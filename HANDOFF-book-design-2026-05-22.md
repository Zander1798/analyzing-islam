# Analyzing Islam Vol I — Book Design Handoff
**Date:** 2026-05-22  
**Project:** `C:\Users\zande\Documents\AI Workspace\Analyzing Islam`

---

## What this is

A Python build script (`build-book.py`) generates a complete B5 book mockup as a single HTML file. The HTML is opened in Chrome and exported to PDF via Ctrl+P → Save as PDF (paper size: custom 176×250mm, margins: none). No editing is done in the HTML directly — all changes go through `build-book.py` and then you run a rebuild.

---

## Key Files

| File | Purpose |
|---|---|
| `build-book.py` | Master build script — all logic lives here |
| `book-design/vol1-quran/Analyzing Islam Vol I — The Quran.html` | Output file — regenerated on every build. **CSS lives here and is preserved across builds** |
| `site/assets/data/catalog-entries.json` | Source of entry metadata (title, ref, strength, categories) |
| `site/catalog/quran.html` | Source of entry body content (blockquotes, h4 sections, paragraphs) |

---

## How to Rebuild

```
cd "C:\Users\zande\Documents\AI Workspace\Analyzing Islam"
python build-book.py
```

Then open the output HTML in Chrome. Build takes ~2 seconds.

---

## Page Layout Constants (B5 at 96dpi)

| Dimension | Value |
|---|---|
| Page outer | 665 × 945 px |
| Top/bottom margin | 76 px each |
| Inner margin (spine) | 68 px |
| Outer margin | 53 px |
| Page-inner height | 793 px |
| Page-inner width | 544 px |
| Running header (rh-row) | ~37 px |
| **Available for entry content** | **756 px** |

---

## Font Sizes (updated in HTML CSS — do not change in build script)

| Element | Size |
|---|---|
| Entry body paragraphs (`.entry p`, `.page-inner p`) | 12.5px |
| Entry title (`.entry-title`) | 20px |
| Entry blockquote | 13.5px |
| Entry h4 section headings | 10px |
| Front matter / back cover / TOC text | 12.5px |

---

## build-book.py — Key Functions

### `CHAPTERS` dict (lines ~45–136)
Maps chapter number → `(name, description)`. Chapter names now use plain `&` (not `&amp;`) — `html_mod.escape()` handles encoding downstream.

### `parse_entries()` (line ~206)
Reads `site/catalog/quran.html`, extracts entry content into a dict keyed by entry ID. Sections extracted: `quote`, `says`, `problem`, `response`, `fails`.

### `entry_html(e, content, ch_name)` (line ~260)
Builds the full HTML for one entry: title div, meta div, blockquote, then h4+paragraphs for each section. h4 labels are plain text: `"What the verse says"`, `"Why this is a problem"`, `"The Muslim response"`, `"Why it fails"`.

### `chapter_opener_html(ch_num, ch_name, ch_desc, entries)` (line ~295)
Generates the chapter opener page(s). **Paginated**: page 1 shows up to 18 entries with full chapter header+description; continuation pages show up to 22 entries each with only a running header. All entries are listed — no truncation.

### `_est_h(html)` (line ~363)
Estimates rendered pixel height of an HTML fragment. Used for page-fill decisions. **Conservative estimates run ~11% above real heights** (K≈1.11). Current parameters:

| Element | Chars/line | Per-line px | Fixed overhead |
|---|---|---|---|
| Entry title (Didot 20px) | 56 | 25 | +10px mb |
| Entry meta | — | — | fixed 27px |
| Blockquote (Didot 13.5px italic) | 84 | 22 | +26px padding+margin |
| H4 heading | — | — | fixed 33px each |
| Body paragraph (system-ui 12.5px) | 88 | 22 | +8px mb |

### `_fine_chunks(inner_html)` (line ~389)
Splits entry inner HTML into page-fill chunks:
- **Chunk 1**: header block (entry-title + entry-meta + blockquote) — everything before first h4
- **Per section**: h4 emitted as **standalone chunk** (so heading stays on page 1 if space permits), then each `<p>` as its own chunk

### `_sentence_split(para_html)` (line ~425)
Splits a `<p>...</p>` chunk into individual sentence texts. Returns `(open_tag, [sentences], close_tag)` or `None` if paragraph has only one sentence. Used as fallback when a whole paragraph doesn't fit.

### `chapter_entry_pages(ch_num, ch_name, entries, contents)` (line ~436)
Main page-generation function. For each entry:

1. **Greedy fill loop** — adds chunks to page 1 until `h_used + chunk_h > PAGE_H`
2. **Sentence-level fallback** — when a paragraph doesn't fit whole, tries to fit individual sentences from it; remaining sentences go to page 2
3. **Orphan h4 check** — after fill, if page 1 ends with a standalone h4 (no paragraph following it on page 1), moves that h4 to page 2

**`PAGE_H = 840`** — estimated-px budget. With K≈1.11, this corresponds to ~756px real fill (right to the bottom border).

**Critical bug that was fixed:** The orphan regex previously used `.*?` with `re.DOTALL`, which caused it to match from the **first** h4 to the last h4 in p1, moving all section content to page 2 and leaving only the header block on page 1. Fixed by using `[^<]*` (cannot cross element boundaries).

Current orphan check (line ~496):
```python
orphan = re.search(r'(<h4[^>]*>[^<]*</h4>\s*)$', p1_inner.rstrip())
```

---

## Book Structure

- **23 chapters**, **282 Quran entries** assigned
- Chapters 13, 14 (Slavery & Captives is ch14), some others have fewer entries
- Ch.11 (Women & Sexual Issues): 50 entries — largest chapter, needs 3 opener pages
- Ch.6 (Cosmology): 36 entries

---

## Splice Mechanism

`build-book.py` reads the output HTML, finds markers `<!-- SECTION 10 -->` and `<!-- SECTION 12 -->`, and replaces everything between them with the freshly generated chapter HTML. Everything outside those markers (CSS, front matter, back cover) is preserved unchanged.

---

## Known Edge Cases / Remaining Work

- **Entries with only 1 sentence in a paragraph**: `_sentence_split` returns `None`, so if the whole paragraph doesn't fit it goes entirely to page 2. In practice these are rare.
- **Very short entries** (e.g. Ch.12 Child Marriage has 1 entry, Ch.16/17 have 1-5 entries): these typically fit entirely on page 1 with no overflow — working correctly.
- **Page 2 overflow** (entries that need 3+ pages): not currently handled — content after page 2 is silently dropped. No entries appear to need this right now.
- **CSS is in the HTML file** — if someone regenerates the HTML from scratch the CSS would be lost. The splice mechanism prevents this, but be careful not to overwrite the HTML manually.
- **PDF export**: Ctrl+P in Chrome → Save as PDF → custom paper size 176×250mm → margins None. Output matches browser exactly.
