#!/usr/bin/env python3
"""Add a 'Build' link to every site nav. Inserts right after the 'Compare'
link in each .site-nav-links block. Idempotent — skips files that already
have build.html in their nav."""
import re
from pathlib import Path

ROOT = Path(__file__).parent / "site"

# Pattern matches: <a href="some/path/compare.html"[optional class]>Compare</a>
# Captures the path prefix (e.g. "", "../", "../../") so we can reuse it.
NAV_COMPARE_RE = re.compile(
    r'(<a\s+href="((?:\.\./)*)compare\.html"(?:\s+class="active")?\s*>Compare</a>)'
)

changed = 0
skipped = 0
for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8")
    if re.search(r'<a\s+href="(?:\.\./)*build\.html"', text):
        skipped += 1
        continue

    if not NAV_COMPARE_RE.search(text):
        continue

    def repl(m):
        compare_anchor = m.group(1)
        prefix = m.group(2) or ""
        return compare_anchor + f'\n      <a href="{prefix}build.html">Build</a>'

    new_text = NAV_COMPARE_RE.sub(repl, text, count=1)
    if new_text != text:
        html.write_text(new_text, encoding="utf-8")
        changed += 1

print(f"Updated: {changed} files. Skipped (already had build.html): {skipped}")
