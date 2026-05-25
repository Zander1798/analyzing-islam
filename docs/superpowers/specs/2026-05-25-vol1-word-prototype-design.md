# Design Spec: Analyzing Islam Vol I — Word Structural Prototype → HTML Final

**Date:** 2026-05-25  
**Project:** Analyzing Islam — Volume I: The Quran  
**Phase covered:** Phase 1 (Word .docx structural prototype) + Phase 2 overview (HTML final)

---

## Purpose

The goal is a publishable book containing every Quran-side entry from AnalyzingIslam.com (282 entries across 23 chapters — 284 in the catalog minus 2 known superseded duplicates). The build happens in two phases:

1. **Word .docx prototype** — establishes correct page geometry, text reflow, and pagination using Word's native layout engine. No content is cut off; sentences flow naturally to the next page. This is the structural truth of the book.
2. **HTML final** — a pixel-perfect dark-themed HTML book (matching the design screenshots) built using the Word prototype's page geometry as its blueprint. This is the publishable deliverable sent to a printer/publisher.

---

## Phase 1: Word Structural Prototype

### Page Geometry

| Property | Value |
|---|---|
| Page size | B5 (176 mm × 250 mm / 6.93" × 9.84") |
| Top margin | 20 mm |
| Bottom margin | 25 mm (accommodates page number) |
| Inner margin (gutter) | 25 mm |
| Outer margin | 18 mm |
| Mirror margins | Yes (recto/verso) |
| Text area | ~133 mm × 205 mm |
| Page number position | Footer, centred |

This geometry matches standard trade paperback book printing for B5 trim size.

### Typography

| Element | Font | Size | Style | Notes |
|---|---|---|---|---|
| Body text | Georgia | 11 pt | Regular | 1.3× line spacing, 6 pt space after |
| Entry title | Georgia | 14 pt | Bold | 4 pt before, 6 pt after |
| Chapter title | Georgia | 22 pt | Bold | Page break before, 16 pt after |
| Chapter intro | Georgia | 11 pt | Italic | Slightly indented |
| Section header | Calibri | 8 pt | Bold, all-caps | 10 pt before, 4 pt after (WHAT THE VERSE SAYS etc.) |
| Blockquote | Georgia | 10 pt | Italic | 12 mm left+right indent, 8 pt before/after |
| Breadcrumb | Calibri | 8 pt | Regular, all-caps | Gray, letter-spaced |
| Q reference | Calibri | 9 pt | Regular | Right-aligned on same row as badges |
| Index chapter | Georgia | 11 pt | Bold | Category heading in index |
| Index entry | Georgia | 10 pt | Regular | Tab stop at right margin for page number |

Georgia is used as the primary serif — widely available, close to the design's book-serif feel. Calibri covers labels and UI elements.

### Word Paragraph Styles

The script defines these named styles via python-docx:

| Style name | Role |
|---|---|
| `AI_Normal` | Standard body paragraph |
| `AI_EntryTitle` | Entry headline |
| `AI_ChapterTitle` | Chapter heading (triggers page break) |
| `AI_ChapterIntro` | Italic intro paragraph on chapter opener page |
| `AI_SectionHeader` | WHAT THE VERSE SAYS / WHY THIS IS A PROBLEM / etc. |
| `AI_Blockquote` | Indented italic verse quotation |
| `AI_Breadcrumb` | Running location label at top of entry |
| `AI_StrengthLabel` | Inline text label: [BASIC] / [MODERATE] / [STRONG] |
| `AI_QRef` | Right-aligned Quran reference |
| `AI_IndexChapter` | Bold category name in General Index |
| `AI_IndexEntry` | Indented entry title + tab to page number |
| `AI_PageNum` | Footer page number |

### Content Pipeline

**Inputs:**
- `site/assets/data/catalog-entries.json` — 284 Quran entries: `id`, `title`, `ref`, `categories`, `strength`
- `site/catalog/quran.html` — full entry bodies: verse passage (blockquote), *What the verse says*, *Why this is a problem*, *The Muslim response*, *Why it fails*

**Parsing:** Reuse `parse_entries()` and `assign_chapter()` from `build-book-final.py` verbatim. These functions are already tested and correct.

**Chapter assignment:** `assign_chapter()` uses `TAG_PRIORITY` (23 category→chapter mappings) and `ID_OVERRIDES` for edge cases. Entries not matching any tag default to chapter 18 (Disbelievers & Moral Problems).

**Sort order within chapters:** basic → moderate → strong (ascending difficulty).

**Exclusions:** `EXCLUDE_IDS` removes 2 known duplicate/superseded entries, giving 282 entries in the final book (matching the design mockup count).

### Document Structure

All sections in order, with expected roman/arabic page numbering:

| # | Section | Page style |
|---|---|---|
| 1 | Half-title page | Roman (i) |
| 2 | Blank verso | Roman (ii) |
| 3 | Copyright page | Roman (iii) |
| 4 | Blank verso | Roman (iv) |
| 5 | Table of Contents | Roman (v–vi) |
| 6 | Foreword | Roman (vii–ix) — 3 sub-sections |
| 7 | Abbreviations & Reference Guide | Roman (x–xi) |
| 8 | Part Opener: The Quran | Arabic (1), section break |
| 9 | Source Introduction: The Quran | Arabic (2) |
| 10–32 | Chapters 1–23 | Arabic (continuous) |
| 33 | General Index | Arabic (back matter) |
| 34 | Quran Verse Index | Arabic (back matter) |

### Front Matter Content

**Half-title (p. i):** "Analyzing Islam" title, "Volume I — The Quran" subtitle. Minimal.

**Copyright (p. iii):**
> Analyzing Islam — Volume I: The Quran  
> A Critical Reference Guide  
> © 2026 Analyzing Islam. All rights reserved.  
> analyzingislam.com  
> First edition, 2026.  
> All Quranic verses quoted from the *Saheeh International* English translation.  
> ISBN — [placeholder]

**Table of Contents:** Built using a Word TOC field that auto-generates entries and page numbers. When the user first opens the document in Word, they must click "Update Table" / press F9 to populate correct page numbers. Foreword + Abbreviations listed first, then the 23 chapters, then back matter.

**Foreword (3 pages):**
- Page 1: What This Is / How Entries Are Organized / How to Read an Entry
- Page 2: Strength Ratings / Sources and Translations
- Page 3: A Note on Tone / How to Use This Book

**Abbreviations & Reference Guide (2 pages):** Citation format, strength rating definitions, Quranic terminology table, Arabic/Islamic terminology table. Content is hardcoded from the reference screenshots (full text is visible and fixed — citation format, strength definitions, and all terminology entries).

### Chapter Structure

Each chapter begins with a **chapter opener page**:
- Breadcrumb: `THE QURAN · CHAPTER N`
- Chapter title (large)
- Horizontal rule
- Intro paragraph (italic)
- Numbered list of entries: `N. Entry title ........ Q X:Y [STRENGTH]`

Entries then flow continuously (no forced page breaks between entries). Each entry:
1. Breadcrumb: `THE QURAN · CHAPTER N · CHAPTER NAME`
2. Entry title (`AI_EntryTitle`)
3. Category label + strength label + Q reference (on one line)
4. Blockquote (`AI_Blockquote`)
5. Section: WHAT THE VERSE SAYS + paragraphs
6. Section: WHY THIS IS A PROBLEM + paragraphs
7. Section: THE MUSLIM RESPONSE + paragraphs *(if present)*
8. Section: WHY IT FAILS + paragraphs *(if present)*

Word handles all page breaks automatically. No entry is ever cut off.

### Back Matter

**General Index:**
- Alphabetical letter dividers (A, B, C…)
- For each chapter: bold chapter name + starting page number
- Indented list of all entry titles under that chapter, each with a right-tab page number
- Tab stop set at text-area right edge

**Quran Verse Index:**
- Two-column layout (Word's built-in column support)
- Entries grouped by Surah number + name
- Format: `4:34 ......... 212`

### Script Architecture

**File:** `build-book-docx.py` (new file in project root)

**Functions:**

```
setup_styles(doc)            — defines all AI_* paragraph and character styles
add_half_title(doc)          — half-title page
add_copyright(doc)           — copyright page
add_toc_placeholder(doc)     — TOC (Word field, auto-updates on open)
add_foreword(doc)            — 3-page foreword
add_abbreviations(doc)       — 2-page reference guide
add_part_opener(doc)         — The Quran part intro page
add_source_intro(doc)        — source introduction
add_chapter_opener(doc, n, title, intro, entries)  — chapter opener page
add_entry(doc, meta, content, chapter_name)        — single entry
add_general_index(doc, chapters)                   — back matter index
add_quran_verse_index(doc, entries, page_map)      — back matter verse index
main()                       — parse → assign → build → save
```

**Output:** `book-design/vol1-quran/Analyzing Islam Vol I — Word Prototype.docx`

**Dependencies:** `python-docx` (pip install python-docx)

---

## Phase 2: HTML Final (future phase)

After the Word prototype is reviewed and confirmed:

1. Extract the page geometry from Word: text area ~133 mm × 205 mm → at 96 dpi ≈ 500 px × 774 px inner area; at print 96 dpi B5 page ≈ 665 px × 945 px (matching existing build-book-final.py page dimensions — already correct).
2. Use the same font sizes (converted pt → px: 11 pt body = ~14.7 px, 14 pt title = ~18.7 px).
3. Build fixed-page HTML divs with black backgrounds, white text, amber section headers.
4. Use the Word-informed pagination to pre-split entries across pages — no content ever overflows a page box.
5. Output: single HTML file, opening in any browser, printable to PDF for publisher submission.

---

## Success Criteria

### Word Prototype
- [ ] Opens in Microsoft Word without errors
- [ ] B5 page size confirmed in Page Layout
- [ ] Mirror margins confirmed (inner/outer different)
- [ ] All 282 entries present, none missing
- [ ] No entry is cut mid-sentence — all text flows to next page naturally
- [ ] Chapter openers each start on a new page
- [ ] Roman numerals for front matter, Arabic for body
- [ ] Page numbers appear in footer
- [ ] Table of Contents lists all 23 chapters with correct page numbers
- [ ] General Index is alphabetically ordered
- [ ] Quran Verse Index is in surah order

### HTML Final (Phase 2 criteria)
- [ ] Matches dark design from screenshots exactly
- [ ] No content cut off at page bottom
- [ ] Prints correctly to PDF from browser
- [ ] All 282 entries present
