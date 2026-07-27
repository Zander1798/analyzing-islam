#!/usr/bin/env python3
"""Patch .vx-ref CSS to enable proper overflow truncation."""
from pathlib import Path

p = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran')
f = next(x for x in p.iterdir() if 'Analyzing' in x.name and x.suffix == '.html' and 'Vol' in x.name)

html = f.read_text(encoding='utf-8', errors='ignore')

old = '.vx-ref { font-size: 10px; color: #d0d0d0; white-space: nowrap; min-width: 42px; }'
new = '.vx-ref { font-size: 10px; color: #d0d0d0; white-space: nowrap; min-width: 0; max-width: 110px; overflow: hidden; text-overflow: ellipsis; }'

if old in html:
    html = html.replace(old, new)
    print('Patched .vx-ref CSS.')
else:
    print('WARNING: .vx-ref CSS not found — already patched or changed.')

f.write_text(html, encoding='utf-8')
print('Done.')
