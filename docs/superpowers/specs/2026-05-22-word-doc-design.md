# Analyzing Islam Vol I — Word Document Build

**Date:** 2026-05-22  
**Status:** Approved

---

## Goal

Generate a fully editable `.docx` version of *Analyzing Islam Vol I — The Quran* that:
- Matches the visual design of the HTML book (B5, Didot/Georgia, chapter openers, entry layout)
- Never truncates entry content — Word handles pagination natively, eliminating the height-estimation problem in `build-book.py`
- Is fully editable in Word (named styles, real TOC, adjustable page setup)

---

## Output

`book-design/vol1-quran/Analyzing Islam Vol I — The Quran.docx`

---

## Sources (same as HTML build)

| File | Role |
|---|---|
| `site/assets/data/catalog-entries.json` | Entry metadata: id, title, ref, categories, strength |
| `site/catalog/quran.html` | Entry body: blockquote, h4 sections, paragraphs |
| `build-book.py` `CHAPTERS` dict | Chapter names, descriptions, entry assignments |

---

## Script

`build-book-word.py` — new file in project root, alongside `build-book.py`.  
Run: `python build-book-word.py`  
Dependency: `pip install python-docx`

---

## Document Structure

1. Half-title page — book title centered
2. Table of contents — Word TOC field (auto-updates with F9)
3. For each of 23 chapters:
   - Chapter opener (page break before): chapter number + name + description + list of entry titles in the chapter
   - Entry pages: each entry flows naturally; Word paginates automatically
4. Back matter — single page with centered "End of Volume I"

---

## Page Setup

| Setting | Value |
|---|---|
| Paper size | B5 — 176 × 250 mm |
| Margins | Mirrored: top 20mm, bottom 20mm, inner 18mm, outer 14mm |
| Header | Chapter name (right-aligned on recto, left-aligned on verso) |

---

## Named Styles

All styles defined programmatically at document creation. User can modify globally in Word's Styles pane.

| Style name | Mapped from | Appearance |
|---|---|---|
| `Book Title` | Half-title page | Georgia 28pt bold, centered |
| `Chapter Number` | Chapter opener | Georgia 11pt, centered, gray |
| `Chapter Name` | `<h1>` / CHAPTERS key | Georgia 22pt bold, centered — used for TOC |
| `Chapter Description` | CHAPTERS description | Georgia 11pt italic, centered, space below |
| `Chapter Entry List` | Entry titles on opener | Georgia 9pt, centered, tight spacing |
| `Entry Title` | `.entry-title` | Georgia 14pt bold, space before 14pt |
| `Entry Meta` | `.ref` + strength | Georgia 9pt, gray (RGB 120,120,120) |
| `Blockquote` | `<blockquote>` | Georgia 11pt italic, left indent 0.8cm, right indent 0.8cm, left border 3pt dark gray |
| `Section Heading` | `<h4>` | Georgia 9pt bold small-caps, space before 8pt |
| `Body Text` | `<p>` | Calibri 10.5pt, space after 4pt, justified |

---

## Parsing Logic

Reuse the same parsing approach as `build-book.py`:

- **`parse_entries()`** — reads `quran.html`, extracts per-entry content keyed by entry ID. Sections: `quote`, `says`, `problem`, `response`, `fails`.
- **`CHAPTERS` dict** — same chapter definitions copied from `build-book.py`, mapping chapter number → `(name, description)`.
- **Chapter→entry assignment** — same category-based assignment logic as `build-book.py`.

The Word script does **not** need `_est_h()`, `_fine_chunks()`, or `_sentence_split()` — those exist only to estimate page fill for the static HTML layout. Word reflows content automatically.

---

## Entry Structure (per entry)

```
[Entry Title paragraph]       ← "Entry Title" style
[Entry Meta paragraph]        ← "Entry Meta" style  — ref + strength
[Blockquote paragraph(s)]     ← "Blockquote" style
[Section Heading]             ← "Section Heading" — "What the verses say"
[Body Text paragraph(s)]
[Section Heading]             ← "Why this is a problem"
[Body Text paragraph(s)]
[Section Heading]             ← "The Muslim response"
[Body Text paragraph(s)]
[Section Heading]             ← "Why it fails"
[Body Text paragraph(s)]
```

No explicit page break between entries — Word flows them naturally. A `keep_with_next` setting on `Entry Title` prevents the title orphaning at the bottom of a page.

---

## Chapter Opener Structure

```
[page break before]
[Chapter Number]    ← "Chapter X"
[Chapter Name]      ← chapter name — TOC picks this up
[Chapter Description paragraph(s)]
[divider rule or blank line]
[Chapter Entry List — one paragraph per entry title in this chapter]
[page break after opener, before first entry]
```

---

## Error Handling

- If an entry ID from the chapter assignment list is not found in `parse_entries()`, log a warning and skip — same behaviour as `build-book.py`.
- If `python-docx` is not installed, print a clear install instruction and exit.

---

## Known Constraints / Non-Goals

- Exact font: Didot is not bundled; Georgia is the fallback. If the user has Didot installed they can update the style in Word.
- No syntax highlighting or special Quranic Arabic script — entries are English-only prose.
- Page 3+ overflow (entries needing 3+ pages): handled naturally by Word — not a constraint here.
- PDF export: user exports from Word via File → Export or print to PDF.
