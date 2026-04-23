#!/usr/bin/env python3
"""Inject verse-parser.js + reader-search.js into every reader page so
casual verse refs ("John 3:16", "Bukhari 2749", "Sanhedrin 4:5", …) can
jump the user to the right anchor. Idempotent — skips pages that already
reference reader-search.js."""
import re
from pathlib import Path

ROOT = Path(__file__).parent / "site"

# Only reader pages want this search UI — the Compare and Build pages
# already carry their own search, and other chrome pages (catalog,
# about, faq, etc.) don't have anchor-per-verse content.
TARGET_DIRS = [ROOT / "read", ROOT / "read-external"]

# Try to anchor the injection right after goat.js (loaded on every
# reader page) so reader-search.js has the same defer timing and can
# pick up the DOM cleanly. Keep the same indentation as the sibling.
GOAT_RE = re.compile(
    r'(\s*)<script src="((?:\.\./)*)assets/js/goat\.js" defer></script>'
)

changed = 0
skipped = 0
missing = 0
for subdir in TARGET_DIRS:
    if not subdir.exists():
        continue
    for html in subdir.rglob("*.html"):
        text = html.read_text(encoding="utf-8")
        if "reader-search.js" in text:
            skipped += 1
            continue
        m = GOAT_RE.search(text)
        if not m:
            missing += 1
            continue
        indent = m.group(1) or "\n"
        prefix = m.group(2) or ""
        insertion = (
            indent + f'<script src="{prefix}assets/js/verse-parser.js" defer></script>' +
            indent + f'<script src="{prefix}assets/js/reader-search.js" defer></script>'
        )
        new_text = text[: m.end()] + insertion + text[m.end():]
        html.write_text(new_text, encoding="utf-8")
        changed += 1

print(f"Updated: {changed} · Skipped (already injected): {skipped} · Missing goat.js anchor: {missing}")
