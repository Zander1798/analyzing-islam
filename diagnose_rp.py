#!/usr/bin/env python3
"""Diagnose the running-page span count mismatch."""
import re
from pathlib import Path

html = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran.html').read_text(encoding='utf-8', errors='ignore')

sec_pos = {}
for m in re.finditer(r'SECTION (\d+)', html):
    n = int(m.group(1))
    if n not in sec_pos:
        sec_pos[n] = m.start()

print('Sections found:', sorted(sec_pos.keys()))

PAGE_RE = re.compile(r'<div class="page(?:\s+entry-page)?">')

arabic_page_positions = []
for sec in [10, 12, 13]:
    start = sec_pos[sec]
    later = [k for k in sorted(sec_pos) if k > sec]
    end   = sec_pos[later[0]] if later else len(html)
    chunk = html[start:end]
    for m in PAGE_RE.finditer(chunk):
        is_entry = 'entry-page' in m.group(0)
        arabic_page_positions.append((start + m.start(), is_entry, sec))

arabic_page_positions.sort(key=lambda x: x[0])
print(f'Total Arabic pages: {len(arabic_page_positions)}')
entry_count = sum(1 for _, ie, _ in arabic_page_positions if ie)
opener_count = sum(1 for _, ie, _ in arabic_page_positions if not ie)
print(f'  Entry pages: {entry_count}, Opener pages: {opener_count}')

# Find all empty running-page spans in sections 10, 12, 13
all_rp = []
for sec in [10, 12, 13]:
    start = sec_pos[sec]
    later = [k for k in sorted(sec_pos) if k > sec]
    end   = sec_pos[later[0]] if later else len(html)
    chunk = html[start:end]
    for m in re.finditer(r'<span class="running-page"></span>', chunk):
        all_rp.append(start + m.start())

print(f'Empty running-page spans: {len(all_rp)}')
print(f'Mismatch: {len(all_rp) - entry_count}')

# Find the extra spans - check which page they're in (entry vs opener)
# For each empty span, check if it's inside an entry-page or a regular page
# Look backwards for the nearest page div
extra_spans = []
entry_positions = {pos for pos, ie, sec in arabic_page_positions if ie}

for rp_pos in all_rp:
    # Find nearest preceding page div
    # Search backwards from rp_pos
    last_page_m = None
    for pos, is_entry, sec in arabic_page_positions:
        if pos < rp_pos:
            last_page_m = (pos, is_entry, sec)
        else:
            break
    if last_page_m:
        _, is_entry, sec = last_page_m
        if not is_entry:
            ctx = html[rp_pos-50:rp_pos+50]
            print(f'EXTRA SPAN (not in entry-page): sec={sec}, pos={rp_pos}')
            print(f'  context: {repr(ctx)}')
