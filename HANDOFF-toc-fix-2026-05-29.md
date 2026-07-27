# Handoff — Reader TOC fix in Compare/Build panes
**Date:** 2026-05-29  
**Branch:** main (deployed to analyzingislam.com via GitHub Pages)  
**Status:** Complete and live

---

## What was fixed

The chapter/surah/book list (the `.reader-toc` sidebar) was completely invisible inside the Compare and Build source panes. Users had no way to navigate between chapters of any source — the Quran, the New Testament, the Tanakh, any hadith collection, etc.

---

## Root cause (two layers)

### Primary bug — `highlights.css` (commit `f119c26`)
When compare.js or build-editor.js attaches the highlights system to a reader iframe, it stamps `hl-in-compare` on the iframe's `<html>` element. An intentional CSS rule in `highlights.css` then fires:

```css
/* OLD — wrong decision */
html.embed-mode.hl-in-compare .reader-toc,
body.embed-mode.hl-in-compare .reader-toc {
  display: none !important;
}
```

This hid the entire chapter list across **all 23 reader sources** in both Compare and Build panes. The comment at the time said "not useful inside a compare pane" — wrong call.

**Fix applied:**
- Removed `.reader-toc` from the `display: none` rule. Only the drag handle (`.splitter[data-splitter-key="reader-toc"]`) is still hidden in embed mode — it truly serves no purpose in a narrow pane.
- Updated the desktop `hl-in-compare` grid from 3-col (`content | HL-splitter | HL-panel`) to 4-col (`200px TOC | content | HL-splitter | HL-panel`) so the TOC column has room alongside the HL panel on ultra-wide screens (>1100px).
- Added `position: static; max-height: 280px` in the ≤1100px media query so the TOC appears as a scrollable strip above the content (typical narrow-pane case).

### Secondary bug — `splitter.js` (commit `243cb95`)
`splitter.js` runs inside every reader iframe and restores the TOC's collapsed/expanded state from `localStorage["splitter:reader-toc"]`. If a user had previously dragged the TOC to 0 (collapsed it) on a standalone reader page, the same collapsed state would be restored inside the embed pane — triggering a CSS `:has()` rule that sets `visibility: hidden` on the TOC.

**Fix applied:** In embed mode (`?embed=1`), the `px === 0` (collapsed) restore branch is skipped. The TOC always starts visible in the embed pane. Custom non-zero widths are still restored.

---

## Files changed

| File | Commit | Change |
|------|--------|--------|
| `site/assets/css/highlights.css` | `f119c26` | Remove `.reader-toc` from embed `display:none`; fix 4-col desktop grid; add static strip CSS for ≤1100px |
| `site/assets/js/splitter.js` | `243cb95` | Skip localStorage collapsed-state restore when `?embed=1` |

---

## Coverage

The fix covers **all 23 reader pages** that have a `.reader-toc` sidebar (every page that loads `splitter.js`):

- **Qurʾān:** `read/quran.html`
- **Six hadith collections:** bukhari, muslim, abu-dawud, tirmidhi, nasai, ibn-majah
- **Comparative scripture:** tanakh, new-testament, mishnah, josephus, apocryphal-gospels, book-of-enoch, talmud-1 through talmud-10

Multi-page index pages (bible.html landing, quran.html interlinear landing, ibn-kathir.html landing) have no `.reader-toc` — they were unaffected and remain unchanged.

---

## Architecture notes for future work

The reader embed mode is orchestrated by three layers that must stay in sync:

1. **`goat.js`** — detects `?embed=1` and stamps `.embed-mode` on `<html>` and `<body>`.
2. **`compare.js` / `build-editor.js`** — stamps `.hl-in-compare` on the iframe's `<html>` when highlights are attached. This is what triggers the `hl-in-compare` CSS rules.
3. **`highlights.css`** — cascades of `!important` rules for `.embed-mode` and `.embed-mode.hl-in-compare` that control the reader grid layout and what's shown/hidden.

The grid layout chain for a typical narrow compare pane (< 1100px, `has-hl-card`, `hl-in-compare`, `embed-mode`):
- Base: 5-col (`toc | toc-split | content | hl-split | hl-card`)
- `@media ≤1100px`: 3-col (`toc | toc-split | content`)
- `embed-mode.hl-in-compare @media ≤1100px`: **1-col** (`1fr`)
- TOC appears above content as `position: static; max-height: 280px` scrollable strip ✓

---

## Outstanding / unrelated issues

- **Codeberg push always fails** — `remote: Forgejo: Quota exceeded`. The repo on Codeberg (https://codeberg.org/Zandervv0610/Analysing-Islam.git) has exceeded its storage quota. Not blocking — GitHub Pages (the live site) is the only deployment target. Someone will need to clean up or upgrade the Codeberg quota to restore that mirror.

---

## Deployment

Both commits are on `main` and deployed live. GitHub Actions run IDs:
- `f119c26` → run `26645823xxx` (deploy ~1m27s, all green)
- `243cb95` → run `26645640373` (deploy ~2m11s, all green)

Site is live at **analyzingislam.com**.
