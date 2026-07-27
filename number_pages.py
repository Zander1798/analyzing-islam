#!/usr/bin/env python3
"""
Assign page numbers to all pages in the book HTML and update the TOC.

Front matter Roman numerals:
  Section 1  (Covers)         - no numbers
  Section 2  (Half-title)     - i
  Section 3  (Title page)     - ii
  Section 4  (Copyright)      - iii
  Section 5  (TOC)            - iv
  Section 6  (Foreword)       - v, vi, vii
  Section 7  (Abbreviations)  - viii, ix
  Section 8  (Part opener)    - x
  Section 9  (Source intro)   - xi

Arabic numbers start at 1 with Section 10 (chapters) and continue through back matter.
"""

import re
from pathlib import Path

BOOK_FILE = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran.html')

PAGE_RE = re.compile(r'<div class="page(?:\s+entry-page)?">')

def to_roman(n):
    val  = [1000,900,500,400,100,90,50,40,10,9,5,4,1]
    syms = ['m','cm','d','cd','c','xc','l','xl','x','ix','v','iv','i']
    r = ''
    for v, s in zip(val, syms):
        while n >= v:
            r += s; n -= v
    return r

html = BOOK_FILE.read_text(encoding='utf-8', errors='ignore')

# Locate all section boundaries
sec_pos = {int(m.group(1)): m.start()
           for m in re.finditer(r'SECTION (\d+)', html)}
sec_sorted = sorted(sec_pos)

def section_slice(n):
    start = sec_pos[n]
    later = [k for k in sec_sorted if k > n]
    end   = sec_pos[later[0]] if later else len(html)
    return start, end

# ── Front matter Roman numerals ──────────────────────────────────────────────
roman_counter = 0
fm_roman = {}  # section -> [roman_str, ...]
for sec in range(2, 10):
    s, e = section_slice(sec)
    chunk = html[s:e]
    n = len(PAGE_RE.findall(chunk))
    pages = []
    for _ in range(n):
        roman_counter += 1
        pages.append(to_roman(roman_counter))
    fm_roman[sec] = pages

foreword_page = fm_roman[6][0]   # 'v'
abbrev_page   = fm_roman[7][0]   # 'viii'

print('Front matter page numbers:')
for sec, pages in fm_roman.items():
    print(f'  Sec {sec}: {pages}')

# ── Arabic: count all page divs in sections 10, 12, 13 in document order ─────
# Collect absolute positions of all page divs in those sections
arabic_page_positions = []  # (abs_pos_in_html, is_entry, section)
for sec in [10, 12, 13]:
    s, e = section_slice(sec)
    chunk = html[s:e]
    for m in PAGE_RE.finditer(chunk):
        is_entry = 'entry-page' in m.group(0)
        arabic_page_positions.append((s + m.start(), is_entry, sec))

arabic_page_positions.sort(key=lambda x: x[0])

arabic_counter = 0
chapter_start  = {}
gidx_start     = None
vidx_start     = None

for abs_pos, is_entry, sec in arabic_page_positions:
    arabic_counter += 1
    if not is_entry:
        after = html[abs_pos:abs_pos+600]
        m = re.search(r'class="chapter-breadcrumb"[^>]*>[^<]*Chapter\s+(\d+)', after)
        if m:
            ch = int(m.group(1))
            if ch not in chapter_start:
                chapter_start[ch] = arabic_counter
        if sec == 12 and gidx_start is None:
            gidx_start = arabic_counter
        if sec == 13 and vidx_start is None:
            vidx_start = arabic_counter

print(f'\nTotal Arabic pages: {arabic_counter}')
print(f'Chapter starts: {chapter_start}')
print(f'General Index: p{gidx_start}  |  Quran Verse Index: p{vidx_start}')
print(f'Foreword: {foreword_page}  |  Abbreviations: {abbrev_page}')

# ── Update running-page spans ─────────────────────────────────────────────────
# All running-page spans in sections 10, 12, 13 appear in order of Arabic pages.
# Each entry-page has exactly one running-page span.
# Collect all empty running-page span positions within those sections, in order.

all_rp_positions = []  # absolute position of each <span class="running-page"></span>
for sec in [10, 12, 13]:
    s, e = section_slice(sec)
    chunk = html[s:e]
    for m in re.finditer(r'<span class="running-page"></span>', chunk):
        all_rp_positions.append(s + m.start())

all_rp_positions.sort()
print(f'\nrunning-page spans to update: {len(all_rp_positions)}')

# Build span -> arabic_page_number map.
# Each page (entry or opener continuation) that has a running-page span gets
# the arabic counter value for its page position in the document.
# Match each span to the page it belongs to by finding the page whose start
# position most closely precedes the span position.
page_positions_sorted = sorted(arabic_page_positions, key=lambda x: x[0])

def get_arabic_for_span(span_pos, page_list):
    """Return the arabic page number for the page that contains span_pos."""
    arab = 0
    for i, (ppos, is_entry, sec) in enumerate(page_list):
        arab = i + 1  # 1-based arabic counter (includes all pages)
        next_ppos = page_list[i+1][0] if i+1 < len(page_list) else len(html)
        if ppos <= span_pos < next_ppos:
            return arab
    return arab

span_to_arabic = {}
for sp in all_rp_positions:
    span_to_arabic[sp] = get_arabic_for_span(sp, page_positions_sorted)

print(f'Spans mapped to arabic pages: {len(span_to_arabic)}')

# Build replacements list (end-to-start for safe string surgery)
rp_tag = '<span class="running-page"></span>'
replacements = []
for pos, num in span_to_arabic.items():
    replacements.append((pos, pos + len(rp_tag),
                         f'<span class="running-page">{num}</span>'))

replacements.sort(key=lambda x: x[0], reverse=True)
new_html = html
for start, end, text in replacements:
    new_html = new_html[:start] + text + new_html[end:]

print('Applied running-page numbers.')

# ── Update TOC ────────────────────────────────────────────────────────────────
toc_updates = {}

# Front matter items
toc_updates[r'(<div class="toc-item"><span class="toc-item-label">Foreword</span>.*?<span class="toc-page">)[^<]*(</span>)'] = \
    r'\g<1>' + foreword_page + r'\2'
toc_updates[r'(<div class="toc-item"><span class="toc-item-label">Abbreviations &amp; Reference Guide</span>.*?<span class="toc-page">)[^<]*(</span>)'] = \
    r'\g<1>' + abbrev_page + r'\2'

# Chapters
for ch in sorted(chapter_start):
    toc_updates[
        r'(<div class="toc-chapter"><span class="toc-ch-num">' + str(ch) +
        r'</span>.*?<span class="toc-ch-page">)[^<]*(</span>)'
    ] = r'\g<1>' + str(chapter_start[ch]) + r'\2'

# Back matter
if gidx_start:
    toc_updates[r'(<div class="toc-item"><span class="toc-item-label">General Index</span>.*?<span class="toc-page">)[^<]*(</span>)'] = \
        r'\g<1>' + str(gidx_start) + r'\2'
if vidx_start:
    toc_updates[r'(<div class="toc-item"><span class="toc-item-label">Quran Verse Index</span>.*?<span class="toc-page">)[^<]*(</span>)'] = \
        r'\g<1>' + str(vidx_start) + r'\2'

for pat, repl in toc_updates.items():
    new_html, count = re.subn(pat, repl, new_html, flags=re.DOTALL)
    if count != 1:
        print(f'  WARNING: TOC pattern matched {count}x — check pattern')

print(f'Updated {len(toc_updates)} TOC entries.')

# ── Write back ────────────────────────────────────────────────────────────────
BOOK_FILE.write_text(new_html, encoding='utf-8')
print('Done.')
