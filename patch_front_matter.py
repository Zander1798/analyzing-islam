#!/usr/bin/env python3
"""
Fix three front-matter CSS/class bugs in the book HTML:
1. Copyright .rule → .cr-rule  (class doesn't exist in book CSS)
2. Abbreviations tables need class="abbrev-table"  (CSS targets .abbrev-table td)
3. .page-inner p font-size 13.5px → 11px  (overrides front-matter designs; entry
   pages keep their size via the more-specific .entry p { font-size: 13.5px } rule)
"""
from pathlib import Path
import re

p = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran')
f = next(x for x in p.iterdir() if 'Analyzing' in x.name and x.suffix == '.html' and 'Vol' in x.name)
html = f.read_text(encoding='utf-8', errors='ignore')
print(f'File : {f.name}')
print(f'Length: {len(html):,}')

changes = 0

# ── 1. .page-inner p font-size 13.5px → 11px ────────────────────────────────
#    Entry pages override to 13.5px via the more-specific .entry p rule (line ~264).
#    Front-matter p tags (foreword, source-intro) will correctly inherit 11px.
OLD_P = '  .page-inner p { font-family: system-ui, sans-serif; font-size: 13.5px; line-height: 1.85; color: #d0d0d0; margin-bottom: 10px; }'
NEW_P = '  .page-inner p { font-family: system-ui, sans-serif; font-size: 11px; line-height: 1.85; color: #d0d0d0; margin-bottom: 10px; }'
if OLD_P in html:
    html = html.replace(OLD_P, NEW_P)
    print('1. Fixed .page-inner p: font-size 13.5px -> 11px')
    changes += 1
else:
    print('WARNING 1: .page-inner p rule not found — already patched or changed')

# ── 2. Copyright rule: .rule → .cr-rule ─────────────────────────────────────
#    Section 4 copyright block uses <div class="rule"> but book CSS only has .cr-rule
OLD_RULE = '<div class="rule"></div>'
NEW_RULE = '<div class="cr-rule"></div>'
if OLD_RULE in html:
    html = html.replace(OLD_RULE, NEW_RULE, 1)   # only one occurrence
    print('2. Fixed copyright: .rule -> .cr-rule')
    changes += 1
else:
    print('WARNING 2: copyright <div class="rule"> not found — already patched or changed')

# ── 3. Abbreviations tables: add class="abbrev-table" ───────────────────────
#    Section 7 has bare <table> elements; book CSS targets .abbrev-table td
#    Locate section 7 boundaries, then add the class only within that region.
SEC7_START = html.find('SECTION 7')
SEC8_START = html.find('SECTION 8')
if SEC7_START == -1 or SEC8_START == -1 or SEC7_START >= SEC8_START:
    print('WARNING 3: Cannot locate section 7 boundaries')
else:
    segment = html[SEC7_START:SEC8_START]
    # Replace bare <table> with <table class="abbrev-table">
    # (rating-table in foreword is already classed; these are all unclassed)
    patched = segment.replace('<table>', '<table class="abbrev-table">')
    n = patched.count('abbrev-table') - segment.count('abbrev-table')
    if n > 0:
        html = html[:SEC7_START] + patched + html[SEC8_START:]
        print(f'3. Added class="abbrev-table" to {n} table(s) in section 7')
        changes += 1
    else:
        print('WARNING 3: No bare <table> found in section 7 — already patched or changed')

# ── Write ────────────────────────────────────────────────────────────────────
f.write_text(html, encoding='utf-8')
print(f'\nTotal changes applied: {changes}')
print('Done.')
