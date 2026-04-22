#!/usr/bin/env python3
"""Add a 'Compare' link to every site nav. Inserts right after the 'Read'
link in each .site-nav-links block. Idempotent — skips files that already
have compare.html in their nav."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent / "site"

# Pattern matches: <a href="some/path/read.html"[optional class]>Read</a>
# Captures the path prefix (e.g. "", "../", "../../") so we can reuse it.
NAV_READ_RE = re.compile(
    r'(<a\s+href="((?:\.\./)*)read\.html"(?:\s+class="active")?\s*>Read</a>)'
)

changed = 0
skipped = 0
for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8")
    if "compare.html" in text:
        skipped += 1
        continue

    # Only insert inside pages that have the Read link in their nav.
    if not NAV_READ_RE.search(text):
        continue

    def repl(m):
        read_anchor = m.group(1)
        prefix = m.group(2) or ""
        return read_anchor + f'\n      <a href="{prefix}compare.html">Compare</a>'

    new_text = NAV_READ_RE.sub(repl, text, count=1)
    if new_text != text:
        html.write_text(new_text, encoding="utf-8")
        changed += 1

print(f"Updated: {changed} files. Skipped (already had compare.html): {skipped}")
