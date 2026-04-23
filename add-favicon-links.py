#!/usr/bin/env python3
"""Inject favicon <link> tags into every HTML page under site/.

Uses absolute /assets/icons/... paths so the same block works for root
pages (index.html) and sub-directory pages (category/*, read/*,
read-external/*) without needing to compute relative prefixes per file.

Anchor: the existing <meta name="description"> tag (present on every
templated page). Idempotent — skips files that already reference
favicon.ico."""
import re
from pathlib import Path

ROOT = Path(__file__).parent / "site"

FAVICON_BLOCK = """
<!-- Favicon + app-icon set (browser tab, iOS home-screen, Android manifest) -->
<link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16.png">
<link rel="icon" href="/assets/icons/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/assets/icons/site.webmanifest">
<meta name="theme-color" content="#0a0a0a">"""

# Insert right after the <meta name="description"> tag. Covers the vast
# majority of the generated pages; any without a description meta get
# skipped and reported.
DESC_RE = re.compile(
    r'(<meta\s+name="description"\s+content="[^"]*"\s*/?>)',
    re.IGNORECASE,
)

changed = 0
skipped = 0
missing = 0
for html in ROOT.rglob("*.html"):
    text = html.read_text(encoding="utf-8")
    if "favicon.ico" in text or "/assets/icons/" in text:
        skipped += 1
        continue
    m = DESC_RE.search(text)
    if not m:
        missing += 1
        continue
    new_text = DESC_RE.sub(lambda mm: mm.group(1) + FAVICON_BLOCK, text, count=1)
    html.write_text(new_text, encoding="utf-8")
    changed += 1

print(f"Updated: {changed} · Skipped (already had favicon): {skipped} · Missing description anchor: {missing}")
