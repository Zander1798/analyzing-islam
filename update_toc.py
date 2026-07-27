#!/usr/bin/env python3
"""Update TOC page numbers after index rebuild."""
import re
from pathlib import Path

BOOK_FILE = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran.html')
html = BOOK_FILE.read_text(encoding='utf-8', errors='ignore')

# Find section comment positions
sec_pos = {}
for m in re.finditer(r'SECTION (\d+)', html):
    n = int(m.group(1))
    if n not in sec_pos:
        sec_pos[n] = m.start()

print('Sections found:', sorted(sec_pos.keys()))

# Show General Index and Quran Verse Index in TOC
gi_idx = html.find('General Index')
vi_idx = html.find('Quran Verse Index')
print(f'General Index appears at: {gi_idx}')
print(f'Quran Verse Index appears at: {vi_idx}')

# Show context around first occurrence of each
if gi_idx > 0:
    print('GI context:', repr(html[gi_idx:gi_idx+120]))
if vi_idx > 0:
    print('VI context:', repr(html[vi_idx:vi_idx+120]))

# Search for all toc-page patterns
toc_page_matches = list(re.finditer(r'toc-page">[^<]*</span>', html))
print(f'\nAll toc-page spans: {len(toc_page_matches)}')
for m in toc_page_matches:
    ctx = html[max(0,m.start()-80):m.end()]
    print(f'  {ctx[-80:]}')
