#!/usr/bin/env python3
"""Scan the built HTML for page-1 entry content that may overflow 756px real height."""

import re, math
from pathlib import Path

BOOK_FILE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran.html")
# .entry p { line-height: 1.75 } → real = 13.5*1.75 = 23.625px; estimate = 26px → K_para = 1.10
# Fixed overhead (title, meta, blockquote, h4) also overestimated (K_overhead ~1.11)
# Minimum K for any page = 1.10 (all-paragraph page), typical > 1.10
K = 1.10           # conservative (minimum expected K)
REAL_LIMIT = 756   # available content height in px
WARN_AT    = 740   # flag if estimated real height >= this

def _est_h(html):
    h = 0
    m = re.search(r'class="entry-title"[^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        h += max(1, math.ceil(len(text) / 56)) * 25 + 10
    if 'entry-meta' in html:
        h += 27
    bq = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', html, re.DOTALL)
    if bq:
        text = re.sub(r'<[^>]+>', '', bq.group(1)).strip()
        h += max(1, math.ceil(len(text) / 84)) * 22 + 26
    h += len(re.findall(r'<h4[^>]*>', html)) * 33
    for pm in re.finditer(r'<p[^>]*>(.*?)</p>', html, re.DOTALL):
        text = re.sub(r'<[^>]+>', '', pm.group(1)).strip()
        if text:
            h += max(1, math.ceil(len(text) / 82)) * 26 + 8
    return h

raw = BOOK_FILE.read_text(encoding='utf-8', errors='ignore')

# Find all entry-pages (page 1 of each entry has class "entry-page")
page_pattern = re.compile(
    r'<div class="page entry-page">\s*<div class="page-inner">(.*?)</div>\s*</div>',
    re.DOTALL
)

warnings = []
ok = 0

for i, m in enumerate(page_pattern.finditer(raw)):
    page_inner = m.group(1)
    # Skip pages with no entry-title (continuation pages / chapter openers)
    if 'entry-title' not in page_inner:
        continue

    est = _est_h(page_inner)
    real = est / K

    # Extract title for reporting
    t = re.search(r'class="entry-title"[^>]*>(.*?)</div>', page_inner, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', t.group(1)).strip() if t else f'page {i}'

    if real >= WARN_AT:
        warnings.append((real, est, title))
    else:
        ok += 1

warnings.sort(reverse=True)

print(f"\n{'='*70}")
print(f"  Overflow check — {len(warnings)} warnings, {ok} pages OK")
print(f"{'='*70}")
for real, est, title in warnings:
    flag = '*** OVERFLOW ***' if real > REAL_LIMIT else 'warn'
    print(f"  [{flag}]  real~{real:.0f}px  est={est}px")
    print(f"           {title[:70]}")
print()
