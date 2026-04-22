#!/usr/bin/env python3
"""Extract all catalog entries that don't yet have a 'Muslim response' section.

Outputs: needs-response.json — one record per entry with:
  { file, title, category, strength, ref, verse_says, problem, entry_start_line }

Used to feed bespoke response+refutation content generation.
"""
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CATALOG_DIR = Path(__file__).parent / "site" / "catalog"

ENTRY_RE = re.compile(
    r'<div class="entry"[^>]*>\s*\n'
    r'\s*<div class="entry-header">(?P<header>.*?)</div>\s*\n'
    r'\s*<section>(?P<body>.*?)</section>',
    re.DOTALL,
)

TITLE_RE = re.compile(r'<span class="entry-title">(.*?)</span>', re.DOTALL)
TAG_RE = re.compile(r'<span class="tag(?:\s+strength-(?P<strength>\w+))?">(.*?)</span>', re.DOTALL)
REF_RE = re.compile(r'<span class="ref">(.*?)</span>', re.DOTALL)
CATEGORY_RE = re.compile(r'data-category="([^"]+)"')
STRENGTH_RE = re.compile(r'data-strength="(\w+)"')

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()

results = []
for f in sorted(CATALOG_DIR.glob("*.html")):
    text = f.read_text(encoding="utf-8")
    entry_start = 0
    for m in ENTRY_RE.finditer(text):
        header = m.group("header")
        body = m.group("body")

        # Skip if it already has the Muslim response section
        if "<h4>The Muslim response</h4>" in body:
            continue

        title_m = TITLE_RE.search(header)
        title = strip_tags(title_m.group(1)) if title_m else "(untitled)"

        ref_m = REF_RE.search(header)
        ref = strip_tags(ref_m.group(1)) if ref_m else ""

        # Extract full entry block including the <div class="entry" ... > line to find data attrs
        entry_div_start = text.rfind('<div class="entry"', 0, m.start() + 1)
        entry_div_end = text.find(">", entry_div_start) + 1
        div_tag = text[entry_div_start:entry_div_end]
        cat_m = CATEGORY_RE.search(div_tag)
        str_m = STRENGTH_RE.search(div_tag)

        # Line number (1-based) where the entry div starts
        line_no = text.count("\n", 0, entry_div_start) + 1

        results.append({
            "file": str(f.relative_to(Path(__file__).parent)).replace("\\", "/"),
            "title": title,
            "category": cat_m.group(1) if cat_m else "",
            "strength": str_m.group(1) if str_m else "",
            "ref": ref,
            "line": line_no,
            "body": body.strip(),
        })

# Save
out = Path(__file__).parent / "needs-response.json"
with out.open("w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Summary
print(f"Total entries needing response+refutation: {len(results)}")
by_file = {}
for r in results:
    by_file[r["file"]] = by_file.get(r["file"], 0) + 1
for f, n in sorted(by_file.items()):
    print(f"  {f}: {n}")
