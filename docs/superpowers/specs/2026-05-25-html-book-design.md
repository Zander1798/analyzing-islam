# HTML Book Design Spec — Analyzing Islam Vol I

**Date:** 2026-05-25  
**Project:** Analyzing Islam, Volume I: The Quran  
**Output:** `book-design/vol1-quran/book.html` (single self-contained file)  
**Generator:** `build-book-html.py`

---

## Goal

Generate a single HTML file containing all 569 pages of *Analyzing Islam Vol I* — front matter, 22 chapters, 262 entries, and back matter. The file serves two purposes simultaneously:

1. **Browser design/review mode** — scrollable, dark-themed, with a right-side page navigator
2. **Print/PDF export** — CSS `@page` paginates into real ISO B5 (176×250 mm) pages; the navigator is hidden

---

## Design Decisions

| Decision | Choice |
|---|---|
| Page rendering | Scrollable sections + CSS `@page` (Option B) |
| Color theme | Dark throughout — black bg, white text, gold accents |
| Typography | Libre Baskerville + Montserrat + EB Garamond |
| Right-side navigator | Dense page-tick scrollbar (one tick per entry, chapter ticks brighter) |

---

## Typography

All fonts loaded via single Google Fonts `@import` in `<head>`:

```
https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Montserrat:wght@400;600&family=EB+Garamond:ital,wght@0,400;1,400&display=swap
```

| Role | Font | Size | Weight | Color |
|---|---|---|---|---|
| Entry title | Libre Baskerville | 15px | 700 | `#ffffff` |
| Chapter title (opener) | Libre Baskerville | 22px | 700 | `#ffffff` |
| Body text | Libre Baskerville | 10px | 400 | `#cccccc` |
| Quran quote | EB Garamond italic | 11px | 400 | `#bbbbbb` |
| Breadcrumb / labels / tags | Montserrat | 7–8px | 400/600 | `#666` / `#c8963c` |
| Page number | Montserrat | 8px | 400 | `#333333` |
| Front matter headings | Libre Baskerville | 18px | 700 | `#ffffff` |
| Front matter body | Libre Baskerville | 10px | 400 | `#cccccc` |

---

## Color Palette

```css
--bg:          #0d0d0d;   /* page background */
--surface:     #111111;   /* slightly lighter surface (chapter openers) */
--border:      #1e1e1e;   /* dividers, rules */
--quote-bar:   #2a2a2a;   /* left border on quote blocks */
--text-body:   #cccccc;   /* body text */
--text-dim:    #888888;   /* secondary text */
--text-faint:  #555555;   /* section labels */
--text-ghost:  #333333;   /* page numbers, deemphasis */
--gold:        #c8963c;   /* tag badges, accent */
--white:       #ffffff;   /* headings */
```

---

## Page Layout (CSS)

### Print

```css
@page {
  size: 176mm 250mm;          /* ISO B5 */
  margin: 20mm 18mm 22mm 18mm; /* top right bottom left */
}

@media print {
  #page-nav { display: none; }
  body { background: #000; color: #ccc; }
}
```

### Screen

```css
body {
  background: var(--bg);
  color: var(--text-body);
  margin: 0;
  padding: 0 52px 0 0;   /* right padding = navigator width (36px) + 16px gap */
}
```

Each page section:

```css
.page {
  width: 176mm;
  min-height: 250mm;
  margin: 0 auto;
  padding: 20mm 18mm 22mm 18mm;
  box-sizing: border-box;
  break-before: page;
  position: relative;
}
```

---

## Section Types

### 1. Front Matter Pages (`.fm-page`)

One `<section class="page fm-page">` per logical front-matter page. Pages:

| Page | Content |
|---|---|
| Half-title (i) | "Analyzing Islam" centred, large; "Volume I — The Quran" subtitle |
| Title (ii) | Title + subtitle + horizontal rule + author name + rule + publisher URL |
| Copyright (iii) | Standard copyright block, edition note, ISBN placeholder, website |
| TOC (iv) | Chapter list with leader dots and page numbers (static, matching Word output) |
| Foreword (v–vii) | Full foreword text, section heading "FOREWORD" |
| Abbreviations (viii–ix) | Two-column abbreviation list, heading "ABBREVIATIONS" |

Front matter pages use roman numeral page numbers (i–ix), shown centered at the bottom in Montserrat 8px `#333`.

### 2. Chapter Openers (`.chapter-opener`)

One `<section class="page chapter-opener">` per chapter. Layout:

```
[top third]  Chapter number — Montserrat 10px / 3px tracking / #555
             Chapter name   — Libre Baskerville bold 28px / #fff
             Thin gold rule (1px, 40% width, left-aligned)
             Entry count    — Montserrat 8px / #555  e.g. "14 entries"

[lower 2/3]  Entry list — two columns, Montserrat 8px / #444
             Each line:  entry number  ·  title (truncated to ~60 chars)
             Active/current entry highlighted in #666 on hover
```

Chapter openers use arabic page numbers continuing from front matter.

### 3. Entry Pages (`.entry`)

One `<section class="page entry">` per entry. Entries may overflow onto a continuation page — see Overflow section.

**Structure (top to bottom):**

```
breadcrumb      THE QURAN  ·  CHAPTER {N}  ·  {CATEGORY}
                Montserrat 7px / 2px tracking / #666

title           {entry title}
                Libre Baskerville bold 15px / #fff / line-height 1.35

tags            [{category badge}]  [{strength badge}]  {verse ref}
                Montserrat 7.5px / #c8963c / 1px tracking

quote block     "{verse text}"
                EB Garamond italic 11px / #bbb
                left border: 2px solid #2a2a2a / padding-left: 12px
                margin: 8px 0

─── sections (each: label then body) ───────────────────────

WHAT THE VERSE SAYS
                Montserrat 7px / 2px tracking / #555 (section label)
                Libre Baskerville 10px / #ccc / line-height 1.65 (body)

WHY THIS IS A PROBLEM
                same label style
                same body style

THE MUSLIM RESPONSE          (present in most entries)
                same label style
                same body style

WHY IT FAILS                 (present in many entries)
                same label style
                same body style

─────────────────────────────────────────────────────────────

page number     {N}
                Montserrat 8px / #333 / centered / margin-top: auto
                top border: 1px solid #1e1e1e
```

**Strength badge colors:**

| Strength | Background | Text |
|---|---|---|
| STRONG | `#1a3a1a` | `#4caf50` |
| MODERATE | `#2a2a0a` | `#cddc39` |
| WEAK | `#3a1a0a` | `#ff7043` |

**Category badge:** `#1a1a2e` background / `#7986cb` text (indigo, same for all categories).

### 4. Back Matter

**General Index** — one or more `.page` sections. Header "GENERAL INDEX" (Libre Baskerville bold 18px). Two-column layout: category name left, entry titles with page numbers right. Montserrat 8px for category headers, Libre Baskerville 9px for entries.

**Quran Verse Index** — header "QURAN VERSE INDEX". Entries sorted by surah:ayah, two columns. Montserrat 8px.

---

## Right-Side Page Navigator (`#page-nav`)

### HTML

```html
<div id="page-nav">
  <div id="pn-counter">1 / 569</div>
  <div id="pn-track">
    <!-- one .pn-tick per <section class="page"> (~292 total):
         6 front-matter ticks, 22 chapter-opener ticks (.chapter class),
         262 entry ticks, 2 back-matter ticks -->
  </div>
</div>
```

### CSS

```css
#page-nav {
  position: fixed;
  right: 0; top: 0;
  width: 36px; height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  background: #0a0a0a;
  border-left: 1px solid #1a1a1a;
  z-index: 100;
}
#pn-counter {
  font-family: 'Montserrat', sans-serif;
  font-size: 6.5px; color: #555;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}
#pn-track {
  flex: 1; width: 10px;
  background: #161616;
  border-radius: 5px;
  border: 1px solid #222;
  position: relative;
  overflow: hidden;
}
.pn-tick {
  position: absolute;
  left: 0; right: 0;
  height: 1px;
  background: #2a2a2a;
  cursor: pointer;
}
.pn-tick.chapter { background: #3d3d3d; height: 2px; }
.pn-tick.active  { background: #c8963c; }
#pn-thumb {
  position: absolute;
  left: 0; right: 0;
  height: 20px;
  background: rgba(200, 150, 60, 0.15);
  border: 1px solid rgba(200, 150, 60, 0.5);
  border-radius: 3px;
  pointer-events: none;
}
```

### JavaScript behaviour

1. On load: collect all `<section class="page">` elements into an ordered array `pages[]` (~292 total: 6 front-matter + 22 chapter-openers + 262 entries + 2 back-matter).
2. Place one `.pn-tick` per section in `#pn-track`, spaced proportionally by index. Chapter-opener sections and the first entry of each chapter get the `.chapter` class (brighter tick). "First entry of a chapter" means the entry section immediately following a `.chapter-opener` section.
3. `IntersectionObserver` on each `.page` section — when a section enters the viewport, mark its tick `.active`, update `#pn-counter` with the estimated page number, and slide `#pn-thumb` to that tick's position.
4. Click on any tick → `section.scrollIntoView({ behavior: 'smooth' })`.
5. `@media print { #page-nav { display: none; } }` — hidden in PDF.

**Page number estimation:** The generator pre-computes the page number for each section (same logic as the Word builder) and embeds it as a `data-page` attribute on each `<section>`. The JS reads this for the counter display rather than estimating from scroll position.

---

## Overflow Handling

Some entries are longer than one B5 page. When printed, CSS handles this automatically (content overflows into the next physical page within the same `<section>`). No artificial splitting is needed.

In browser scroll view, entries simply grow taller than 250mm. This is correct behavior — the goal is print fidelity, not pixel-perfect browser pagination.

---

## Python Generator (`build-book-html.py`)

### Inputs

- `site/assets/data/catalog-entries.json` — same source as Word builder
- `book-design/vol1-quran/foreword.txt` — foreword text (plain text, paragraph-separated)
- `book-design/vol1-quran/abbreviations.json` — `[{"abbr": "...", "meaning": "..."}]`

If `foreword.txt` or `abbreviations.json` do not exist, the generator uses placeholder text and logs a warning.

### Outputs

- `book-design/vol1-quran/book.html` — the generated file

### Structure

```python
build-book-html.py
├── load_entries()          → list[dict]  (same as Word builder)
├── group_by_chapter()      → dict[int, list[dict]]
├── compute_page_numbers()  → dict[str, int]  section_id → page_num
├── render_front_matter()   → str  (HTML sections)
├── render_chapter_opener() → str  (HTML section)
├── render_entry()          → str  (HTML section)
├── render_back_matter()    → str  (HTML sections)
├── render_navigator()      → str  (HTML #page-nav div + inline JS)
├── render_styles()         → str  (full CSS as <style> block)
└── main()                  → writes book.html
```

No external template engine required — all rendering is Python f-strings. The file is self-contained: all CSS and JS are inlined; the only external dependency is the Google Fonts CDN URL.

### Page number computation

Front matter pages: i–ix (roman). Content pages: 1–N (arabic). Page number increments by 1 per section, with multi-page sections (foreword, back matter) given a range. The Word builder's page counts are used as ground truth for the TOC numbers.

---

## File Output

```
book-design/vol1-quran/book.html   ~8–12 MB (all inline CSS/JS, no images)
```

The file opens directly in any browser without a local server.

---

## Out of Scope

- Search / filter functionality
- Interactive entry links within the document
- Image assets or diagrams
- Any server-side component
- Editing entries from the browser
