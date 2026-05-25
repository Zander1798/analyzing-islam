"""
Builds Vol I redesign based on screenshots.
Key change: body/paragraph text → amber (#BF7B3A) to match screenshot design.
Blockquote border → amber. Overflow fixed. Saved as v2 file then opened.
"""
import os, re

SRC = r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran.html"
DST = r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran v2.html"

AMBER = '#BF7B3A'
AMBER_LIGHT = '#C98B4E'   # for em/italic within amber text

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# ── Extract CSS block ────────────────────────────────────────
style_open  = html.index('<style>') + len('<style>')
style_close = html.index('</style>')
css = html[style_open:style_close]

original_css = css  # keep for diff check

# ─────────────────────────────────────────────────────────────
# 1.  PAGE SHELL — min-height + no overflow clipping
# ─────────────────────────────────────────────────────────────
css = css.replace(
    'width: 665px; height: 945px; background: #000; color: #f5f5f5; position: relative; overflow: hidden;',
    'width: 665px; min-height: 945px; background: #000; color: #f5f5f5; position: relative; overflow: visible;'
)
css = css.replace(
    'top: 76px; bottom: 76px; left: 68px; right: 53px; overflow: hidden;',
    'top: 76px; bottom: 76px; left: 68px; right: 53px; overflow: visible;'
)
css = css.replace(
    '.entry-page { height: 945px; overflow: hidden; }',
    '.entry-page { min-height: 945px; overflow: visible; }'
)

# ─────────────────────────────────────────────────────────────
# 2.  PAGE-INNER P  (source intro, abbreviations, foreword plain p)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    'font-size: 11px; line-height: 1.85; color: #d0d0d0; margin-bottom: 10px; }',
    f'font-size: 11px; line-height: 1.85; color: {AMBER}; margin-bottom: 10px; }}'
)

# ─────────────────────────────────────────────────────────────
# 3.  ENTRY P  (body paragraphs inside entries)
# ─────────────────────────────────────────────────────────────
# first definition (line ~220 in original — uses #f5f5f5)
css = css.replace(
    'font-size: 13.5px; line-height: 1.75; color: #f5f5f5; margin-bottom: 8px; font-family: system-ui, sans-serif; }',
    f'font-size: 12px; line-height: 1.75; color: {AMBER}; margin-bottom: 8px; font-family: system-ui, sans-serif; }}'
)
# second definition (line ~271 in original — uses #d8d8d8)
css = css.replace(
    'font-size: 13.5px; line-height: 1.75; color: #d8d8d8; margin-bottom: 8px; }',
    f'font-size: 12px; line-height: 1.75; color: {AMBER}; margin-bottom: 8px; }}'
)
# em inside entry p
css = css.replace(
    '.entry p em { font-style: italic; color: #d0d0d0; }',
    f'.entry p em {{ font-style: italic; color: {AMBER_LIGHT}; }}'
)

# ─────────────────────────────────────────────────────────────
# 4.  ENTRY H4  (section labels: WHAT THE VERSE SAYS, etc.)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    'font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase; color: #5a5a5a; font-weight: 700; margin: 14px 0 6px; }',
    f'font-size: 9px; letter-spacing: 0.22em; text-transform: uppercase; color: {AMBER}; font-weight: 700; margin: 14px 0 6px; }}'
)

# ─────────────────────────────────────────────────────────────
# 5.  FOREWORD / ABBREVIATIONS section-heading
# ─────────────────────────────────────────────────────────────
css = css.replace(
    'font-size: 11px; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; color: #f5f5f5; margin-top: 26px; margin-bottom: 10px; }',
    f'font-size: 9px; font-weight: 700; letter-spacing: 0.22em; text-transform: uppercase; color: {AMBER}; margin-top: 24px; margin-bottom: 8px; }}'
)

# ─────────────────────────────────────────────────────────────
# 6.  CHAPTER DESC  +  PART DESC
# ─────────────────────────────────────────────────────────────
css = css.replace(
    'font-size: 13.5px; line-height: 1.8; color: #9a9a9a; max-width: 460px; }',
    f'font-size: 12px; line-height: 1.8; color: {AMBER}; max-width: 460px; }}'
)
css = css.replace(
    'font-size: 11px; line-height: 1.8; color: #9a9a9a; max-width: 420px; }',
    f'font-size: 11px; line-height: 1.8; color: {AMBER}; max-width: 420px; }}'
)

# ─────────────────────────────────────────────────────────────
# 7.  BLOCKQUOTE  (amber border; keep italic text in lighter amber)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    'border-left: 2px solid #7aa2f7; margin: 0 0 14px 0; padding: 8px 16px; font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-style: italic; font-size: 13px; color: #9a9a9a; line-height: 1.6; }',
    f'border-left: 2px solid {AMBER}; margin: 0 0 14px 0; padding: 8px 16px; font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-style: italic; font-size: 12px; color: #9a9a9a; line-height: 1.6; }}'
)
# second blockquote rule (entry blockquote)
css = css.replace(
    'border-left: 2px solid #7aa2f7; margin: 0 0 14px 0; padding: 8px 16px; font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-style: italic; font-size: 13.5px; color: #9a9a9a; line-height: 1.6; }',
    f'border-left: 2px solid {AMBER}; margin: 0 0 14px 0; padding: 8px 16px; font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-style: italic; font-size: 12px; color: #9a9a9a; line-height: 1.6; }}'
)

# ─────────────────────────────────────────────────────────────
# 8.  TOC CHAPTER LABELS
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.toc-ch-label { font-family: system-ui,sans-serif; font-size: 11px; color: #d0d0d0; white-space: nowrap; }',
    f'.toc-ch-label {{ font-family: system-ui,sans-serif; font-size: 11px; color: {AMBER}; white-space: nowrap; }}'
)

# ─────────────────────────────────────────────────────────────
# 9.  RATING TABLE  (foreword / abbreviations)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    'font-size: 11.5px; line-height: 1.7; color: #d0d0d0; padding: 6px 0; vertical-align: top; border-bottom: 1px solid #1a1a1a; }',
    f'font-size: 11px; line-height: 1.7; color: {AMBER}; padding: 6px 0; vertical-align: top; border-bottom: 1px solid #1a1a1a; }}'
)

# ─────────────────────────────────────────────────────────────
# 10. ABBREVIATION TABLE definitions
# ─────────────────────────────────────────────────────────────
css = css.replace(
    'font-size: 11.5px; line-height: 1.6; padding: 5px 0; vertical-align: top; border-bottom: 1px solid #111; color: #d0d0d0; }',
    f'font-size: 11px; line-height: 1.6; padding: 5px 0; vertical-align: top; border-bottom: 1px solid #111; color: {AMBER}; }}'
)

# ─────────────────────────────────────────────────────────────
# 11. ANATOMY BLOCK (how-to-read-an-entry table)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.anatomy-desc { font-size: 11.5px; color: #d0d0d0; line-height: 1.6; }',
    f'.anatomy-desc {{ font-size: 11px; color: {AMBER}; line-height: 1.6; }}'
)

# ─────────────────────────────────────────────────────────────
# 12. GENERAL INDEX sub-labels
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.gi-sub-label { font-size: 11px; line-height: 1.55; color: #9a9a9a;',
    f'.gi-sub-label {{ font-size: 11px; line-height: 1.55; color: {AMBER};'
)

# ─────────────────────────────────────────────────────────────
# 13. CHAPTER FOOTER text + source label
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.chapter-entry-count { font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; color: #5a5a5a; }',
    f'.chapter-entry-count {{ font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; color: {AMBER}; }}'
)
css = css.replace(
    '.chapter-entry-count span { color: #9a9a9a; font-weight: 600; }',
    f'.chapter-entry-count span {{ color: #f5f5f5; font-weight: 600; }}'
)

# ─────────────────────────────────────────────────────────────
# 14. FACTS STRIP labels (source intro bottom)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.fact-label { font-size: 9px; letter-spacing: 0.18em; text-transform: uppercase; color: #5a5a5a; }',
    f'.fact-label {{ font-size: 9px; letter-spacing: 0.18em; text-transform: uppercase; color: {AMBER}; }}'
)

# ─────────────────────────────────────────────────────────────
# 15. PART COUNT text
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.part-count-text { font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; color: #5a5a5a; }',
    f'.part-count-text {{ font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; color: {AMBER}; }}'
)

# ─────────────────────────────────────────────────────────────
# 16. SOURCE EYEBROW
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.source-eyebrow { font-size: 9px; letter-spacing: 0.28em; text-transform: uppercase; color: #5a5a5a; margin-bottom: 10px; }',
    f'.source-eyebrow {{ font-size: 9px; letter-spacing: 0.28em; text-transform: uppercase; color: {AMBER}; margin-bottom: 10px; }}'
)

# ─────────────────────────────────────────────────────────────
# 17. CHAPTER BREADCRUMB
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.chapter-breadcrumb { font-size: 9px; letter-spacing: 0.25em; text-transform: uppercase; color: #5a5a5a; margin-bottom: 12px; }',
    f'.chapter-breadcrumb {{ font-size: 9px; letter-spacing: 0.25em; text-transform: uppercase; color: {AMBER}; margin-bottom: 12px; }}'
)

# ─────────────────────────────────────────────────────────────
# 18. ENTRY ROW TITLE (chapter opener entry list)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.entry-row-title { font-size: 11.5px; color: #c0c0c0; flex: 1; line-height: 1.4; }',
    f'.entry-row-title {{ font-size: 11px; color: {AMBER}; flex: 1; line-height: 1.4; }}'
)

# ─────────────────────────────────────────────────────────────
# 19. SECTION LABEL (abbreviations section headers)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.section-label { font-size: 9px; letter-spacing: 0.22em; text-transform: uppercase; color: #5a5a5a; margin-bottom: 10px; margin-top: 20px; }',
    f'.section-label {{ font-size: 9px; letter-spacing: 0.22em; text-transform: uppercase; color: {AMBER}; margin-bottom: 10px; margin-top: 20px; }}'
)

# ─────────────────────────────────────────────────────────────
# 20. PAGE-SUBHEADING (abbreviations subtitle)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.page-subheading { font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: #9a9a9a; margin-bottom: 24px; }',
    f'.page-subheading {{ font-size: 9px; letter-spacing: 0.18em; text-transform: uppercase; color: {AMBER}; margin-bottom: 24px; }}'
)

# ─────────────────────────────────────────────────────────────
# 21. INDEX-SUB (quran verse index subtitle)
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.index-sub { font-size: 9px; letter-spacing: 0.2em; text-transform: uppercase; color: #5a5a5a; margin-bottom: 16px; }',
    f'.index-sub {{ font-size: 9px; letter-spacing: 0.2em; text-transform: uppercase; color: {AMBER}; margin-bottom: 16px; }}'
)

# ─────────────────────────────────────────────────────────────
# 22. NOTICE paragraphs on copyright page
# ─────────────────────────────────────────────────────────────
css = css.replace(
    '.notice { font-family: system-ui, sans-serif; font-size: 10px; color: #9a9a9a; line-height: 1.8; margin-bottom: 16px; }',
    f'.notice {{ font-family: system-ui, sans-serif; font-size: 10px; color: {AMBER}; line-height: 1.8; margin-bottom: 16px; }}'
)

# ─────────────────────────────────────────────────────────────
# Diff report
# ─────────────────────────────────────────────────────────────
changes = sum(1 for a, b in zip(original_css.splitlines(), css.splitlines()) if a != b)
print(f'CSS lines changed: {changes}')

# ─────────────────────────────────────────────────────────────
# Write output
# ─────────────────────────────────────────────────────────────
new_html = html[:style_open] + css + html[style_close:]
with open(DST, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'Saved: {DST}')
os.startfile(DST)
print('Opened in default browser.')
