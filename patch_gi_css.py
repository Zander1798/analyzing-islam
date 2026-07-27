#!/usr/bin/env python3
"""
Update General Index CSS: allow sub-entry text to wrap fully.
Dots + page number align to the bottom of the last wrapped line.
"""
from pathlib import Path

p = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran')
f = next(x for x in p.iterdir() if 'Analyzing' in x.name and x.suffix == '.html' and 'Vol' in x.name)
html = f.read_text(encoding='utf-8', errors='ignore')

GI_CSS_OLD = """
  /* ═══════════════════════════════════════
     GENERAL INDEX — single-column TOC-style
  ═══════════════════════════════════════ */
  .gi-list { width: 100%; }
  .gi-letter { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 14px; font-weight: bold; color: #f5f5f5; margin-top: 16px; margin-bottom: 4px; padding-bottom: 4px; border-bottom: 1px solid #1e1e1e; line-height: 1; }
  .gi-letter:first-child { margin-top: 0; }
  .gi-cat-row { display: flex; align-items: baseline; margin-top: 3px; margin-bottom: 5px; }
  .gi-cat-label { font-size: 12px; font-weight: 600; color: #d0d0d0; white-space: nowrap; }
  .gi-sub-row { display: flex; align-items: baseline; margin-bottom: 3px; padding-left: 14px; }
  .gi-sub-label { font-size: 11px; color: #9a9a9a; white-space: nowrap; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
  .gi-ldots { flex: 1; border-bottom: 1px dotted #2a2a2a; margin: 0 6px 2px; min-width: 8px; }
  .gi-pg { font-size: 11px; color: #5a5a5a; white-space: nowrap; font-style: italic; }"""

GI_CSS_NEW = """
  /* ═══════════════════════════════════════
     GENERAL INDEX — single-column TOC-style
  ═══════════════════════════════════════ */
  .gi-list { width: 100%; }
  .gi-letter { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 14px; font-weight: bold; color: #f5f5f5; margin-top: 16px; margin-bottom: 4px; padding-bottom: 4px; border-bottom: 1px solid #1e1e1e; line-height: 1; }
  .gi-letter:first-child { margin-top: 0; }
  .gi-cat-row { display: flex; align-items: baseline; margin-top: 3px; margin-bottom: 5px; }
  .gi-cat-label { font-size: 12px; font-weight: 600; color: #d0d0d0; white-space: nowrap; }
  .gi-sub-row { display: flex; align-items: flex-end; margin-bottom: 4px; padding-left: 14px; }
  .gi-sub-label { font-size: 11px; line-height: 1.55; color: #9a9a9a; flex: 1; min-width: 0; overflow-wrap: break-word; word-break: break-word; }
  .gi-ldots { flex-shrink: 0; width: 28px; border-bottom: 1px dotted #2a2a2a; margin: 0 4px 3px; }
  .gi-pg { font-size: 11px; color: #5a5a5a; white-space: nowrap; font-style: italic; flex-shrink: 0; }"""

if GI_CSS_OLD in html:
    html = html.replace(GI_CSS_OLD, GI_CSS_NEW)
    print('Updated GI CSS: text now wraps fully, page aligns to last line.')
else:
    print('ERROR: old GI CSS block not found — check for prior patch.')

f.write_text(html, encoding='utf-8')
print('Done.')
