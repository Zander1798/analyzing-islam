#!/usr/bin/env python3
"""Inject bookmarks.js + entry-actions.js into catalog/ and category/ pages.
These are the pages that contain <div class="entry"> blocks and need the
Save-button + Note-toggle UI.

Idempotent: skips files that already have entry-actions.js.
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SITE = Path(__file__).parent / "site"

# Already-present marker
MARKER = "entry-actions.js"

# Insert before auth-ui.js since bookmarks.js depends on auth.js + the supabase
# client, and entry-actions.js depends on bookmarks.js.
# We place them immediately BEFORE the goat.js line so the relative prefix is consistent.
GOAT_RE = re.compile(
    r'(\s*)<script src="([^"]*assets/js/goat\.js)"[^>]*></script>'
)


def process(path):
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return "skip (already injected)"

    m = GOAT_RE.search(text)
    if not m:
        return "skip (no goat.js anchor)"

    goat_path = m.group(2)
    idx = goat_path.rfind("js/")
    prefix = goat_path[: idx + 3]
    indent = m.group(1) or "\n"

    block = (
        f'<script src="{prefix}bookmarks.js" defer></script>\n'
        f'<script src="{prefix}entry-actions.js" defer></script>\n'
    )

    new = text[: m.start()] + indent + block.rstrip() + m.group(0) + text[m.end():]
    new = re.sub(r"\n{4,}", "\n\n\n", new)
    path.write_text(new, encoding="utf-8")
    return f"injected"


def main():
    targets = []
    targets.extend(sorted((SITE / "catalog").glob("*.html")))
    targets.extend(sorted((SITE / "category").glob("*.html")))
    counts = {"injected": 0, "skipped": 0}
    for f in targets:
        result = process(f)
        if result.startswith("injected"):
            counts["injected"] += 1
        else:
            counts["skipped"] += 1
        print(f"  {f.relative_to(SITE).as_posix()}: {result}")
    print(f"\nSummary: {counts['injected']} injected, {counts['skipped']} skipped.")


if __name__ == "__main__":
    main()
