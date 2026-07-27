#!/usr/bin/env python3
"""
Fix four issues in the book HTML:
1. Add front/back covers as Section 1 (missing)
2. Fix half-title (Section 2) to use proper CSS class names
3. Fix title page (Section 3) to use proper CSS class names
4. Fix index CSS so columns cannot overflow (min-width: 0 + flex: 1)
"""
import re
from pathlib import Path

SEC_DIR = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran')

# Find the book file (name has em-dash, use glob to avoid encoding issues)
BOOK_FILE = next(f for f in SEC_DIR.iterdir() if 'Analyzing' in f.name and f.suffix == '.html' and 'Vol' in f.name)
print(f'Book file: {BOOK_FILE.name}')

html = BOOK_FILE.read_text(encoding='utf-8', errors='ignore')
print(f'Original length: {len(html):,}')

sep = '═' * 54  # ══...══

# ── 1. Fix index CSS ─────────────────────────────────────────────────────────
# Problem: grid column divs have no min-width: 0 (content overflows)
#          .idx-term lacks flex: 1; min-width: 0 (flex truncation doesn't kick in)

old_idx_term = '.idx-term { font-size: 10.5px; line-height: 1.5; color: #d0d0d0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }'
new_idx_term = '.idx-term { font-size: 10.5px; line-height: 1.5; color: #d0d0d0; flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }'
if old_idx_term in html:
    html = html.replace(old_idx_term, new_idx_term)
    print('Fixed .idx-term CSS.')
else:
    print('WARNING: .idx-term CSS not found — skipping')

old_verse_cols = '.verse-columns { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0 20px; }'
new_verse_cols = (
    '.verse-columns { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0 20px; }\n'
    '  .idx-col, .vi-col { min-width: 0; overflow: hidden; }'
)
if old_verse_cols in html:
    html = html.replace(old_verse_cols, new_verse_cols)
    print('Added min-width: 0 to index column divs.')
else:
    print('WARNING: .verse-columns CSS not found — skipping')

# ── 2. Locate section comment boundaries ─────────────────────────────────────
secs = {}
for m in re.finditer(r'SECTION (\d+)', html):
    n = int(m.group(1))
    if n not in secs:
        secs[n] = m.start()

def sec_comment_start(n):
    s = secs[n]
    return html.rfind('<!--', max(0, s - 200), s)

s2_start = sec_comment_start(2)
s3_start = sec_comment_start(3)
s4_start = sec_comment_start(4)

print(f'Section 2 comment at: {s2_start:,}')
print(f'Section 3 comment at: {s3_start:,}')
print(f'Section 4 comment at: {s4_start:,}')

# ── 3. New half-title (Section 2) ─────────────────────────────────────────────
new_sec2 = (
    f'<!-- {sep}\n'
    f'     SECTION 2 — HALF-TITLE\n'
    f'     {sep} -->\n'
    f'<div class="section-divider">Section 2 — Half-Title</div>\n\n'
    f'<div class="page">\n'
    f'  <div class="page-inner">\n'
    f'    <div class="ht-volume">Volume I</div>\n'
    f'    <div class="ht-title">Analyzing Islam</div>\n'
    f'    <div class="ht-source-label">The Quran</div>\n'
    f'    <span class="running-page">i</span>\n'
    f'  </div>\n'
    f'</div>\n\n\n\n'
)

# ── 4. New title page (Section 3) ─────────────────────────────────────────────
new_sec3 = (
    f'<!-- {sep}\n'
    f'     SECTION 3 — TITLE PAGE\n'
    f'     {sep} -->\n'
    f'<div class="section-divider">Section 3 — Title Page</div>\n\n'
    f'<div class="page">\n'
    f'  <div class="page-inner">\n'
    f'    <div class="title-block">\n'
    f'      <div class="title-main">Analyzing Islam</div>\n'
    f'      <div class="title-red-rule"></div>\n'
    f'      <div class="title-source-subtitle">The Quran</div>\n'
    f'      <div class="title-source-descriptor">A Critical Reference Guide</div>\n'
    f'    </div>\n'
    f'    <div class="title-colophon">\n'
    f'      <div class="title-colophon-rule"></div>\n'
    f'      <div class="title-colophon-row">\n'
    f'        <div class="title-colophon-text">analyzingislam.com</div>\n'
    f'        <div class="title-colophon-text">2026</div>\n'
    f'      </div>\n'
    f'    </div>\n'
    f'    <span class="running-page">ii</span>\n'
    f'  </div>\n'
    f'</div>\n\n\n\n'
)

# ── 5. Section 1 (covers) from 13-covers.html ─────────────────────────────────
covers_html = (SEC_DIR / '13-covers.html').read_text(encoding='utf-8', errors='ignore')
body_start   = covers_html.find('<body')
body_tag_end = covers_html.find('>', body_start) + 1
body_end     = covers_html.rfind('</body>')
covers_body  = covers_html[body_tag_end:body_end].strip()

new_sec1 = (
    f'<!-- {sep}\n'
    f'     SECTION 1 — COVERS (FRONT + BACK)\n'
    f'     {sep} -->\n'
    f'<div class="section-divider">Section 1 — Covers (Front + Back)</div>\n\n'
    + covers_body + '\n\n\n\n'
)

# ── 6. Assemble: before-sec2 | sec1 | sec2 | sec3 | sec4-onwards ─────────────
before_sec2  = html[:s2_start]
after_sec3   = html[s4_start:]

new_html = before_sec2 + new_sec1 + new_sec2 + new_sec3 + after_sec3

print(f'New length: {len(new_html):,}')

# Verify section markers
found_secs = sorted(set(int(m.group(1)) for m in re.finditer(r'SECTION (\d+)', new_html)))
print(f'Sections in new HTML: {found_secs}')

BOOK_FILE.write_text(new_html, encoding='utf-8')
print('Done.')
