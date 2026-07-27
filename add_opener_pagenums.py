#!/usr/bin/env python3
"""
Insert <span class="running-page">N</span> into the page-inner of:
  - Front matter pages (sections 2-9): Roman numerals i through xi
  - Chapter opener pages (regular pages in sections 10, 12, 13): Arabic numbers

Entry pages already have the span from the previous numbering pass.
"""

import re
from pathlib import Path

BOOK_FILE = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran.html')

PAGE_RE       = re.compile(r'<div class="page(?:\s+entry-page)?">')
OPENER_RE     = re.compile(r'<div class="page">')        # regular (non-entry) pages only
INNER_OPEN    = '<div class="page-inner">'

def to_roman(n):
    val  = [1000,900,500,400,100,90,50,40,10,9,5,4,1]
    syms = ['m','cm','d','cd','c','xc','l','xl','x','ix','v','iv','i']
    r = ''
    for v, s in zip(val, syms):
        while n >= v: r += s; n -= v
    return r

def find_inner_close(html, inner_content_start):
    """Return the char position of the </div> that closes page-inner."""
    depth = 1
    pos   = inner_content_start
    while depth > 0:
        open_div  = html.find('<div', pos)
        close_div = html.find('</div>', pos)
        if close_div == -1:
            break
        if open_div != -1 and open_div < close_div:
            depth += 1
            pos = open_div + 4
        else:
            depth -= 1
            if depth == 0:
                return close_div   # this </div> closes page-inner
            pos = close_div + 6
    return -1

html = BOOK_FILE.read_text(encoding='utf-8', errors='ignore')

# Locate section boundaries
sec_pos = {int(m.group(1)): m.start()
           for m in re.finditer(r'SECTION (\d+)', html)}
sec_sorted = sorted(sec_pos)

def section_slice(n):
    start = sec_pos[n]
    later = [k for k in sec_sorted if k > n]
    end   = sec_pos[later[0]] if later else len(html)
    return start, end

# ── Build list of (abs_position_of_page_inner_close, page_num_str) ───────────
insertions = []   # (pos_of_page_inner_close_div, span_text)

# --- Front matter: sections 2-9, Roman numerals ---
roman_counter = 0
for sec in range(2, 10):
    s, e = section_slice(sec)
    chunk = html[s:e]
    for m in OPENER_RE.finditer(chunk):
        roman_counter += 1
        rm = to_roman(roman_counter)
        abs_page_start = s + m.start()
        inner_start_rel = chunk.find(INNER_OPEN, m.start())
        inner_content_start = s + inner_start_rel + len(INNER_OPEN)
        close_pos = find_inner_close(html, inner_content_start)
        if close_pos != -1:
            insertions.append((close_pos, f'<span class="running-page">{rm}</span>\n  '))

print(f'Front matter insertions: {len(insertions)}')

# --- Chapter/back matter openers: sections 10, 12, 13, Arabic numbers ---
arabic_counter = 0
ch_insertions = []
for sec in [10, 12, 13]:
    s, e = section_slice(sec)
    chunk = html[s:e]
    for m in PAGE_RE.finditer(chunk):
        arabic_counter += 1
        is_entry = 'entry-page' in m.group(0)
        if not is_entry:
            # This is a regular opener page — needs a page number
            abs_page_start = s + m.start()
            inner_start_rel = chunk.find(INNER_OPEN, m.start())
            inner_content_start = s + inner_start_rel + len(INNER_OPEN)
            close_pos = find_inner_close(html, inner_content_start)
            if close_pos != -1:
                ch_insertions.append((close_pos, f'<span class="running-page">{arabic_counter}</span>\n  '))

print(f'Chapter/back-matter opener insertions: {len(ch_insertions)}')
insertions.extend(ch_insertions)

# ── Apply all insertions from end to start ────────────────────────────────────
insertions.sort(key=lambda x: x[0], reverse=True)

new_html = html
for pos, span in insertions:
    new_html = new_html[:pos] + span + new_html[pos:]

BOOK_FILE.write_text(new_html, encoding='utf-8')
print(f'Done — {len(insertions)} page number spans added.')
