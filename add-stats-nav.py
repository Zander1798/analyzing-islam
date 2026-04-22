#!/usr/bin/env python3
"""Insert `<a href="...stats.html">Stats</a>` after the Compare nav link
across every site page that has the main nav. Computes the correct
relative path (./stats.html, ../stats.html, ../../stats.html) based on
each file's depth below /site/.
"""
import re
from pathlib import Path
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"

# Every HTML file under site/ gets this treatment.
targets = list(SITE.rglob("*.html"))

# Match a <a...>Compare</a> link, capturing its href so we can keep the
# same relative prefix for Stats. Insert a new <a> for Stats right after
# it, with the same class (active or not — we use the default "not
# active" form; only stats.html itself is marked active when on the
# page, which it doesn't need because stats.html's own nav is already
# correct).
COMPARE_RE = re.compile(
    r'(<a\s+href="([^"]*)compare\.html"(?:\s+class="active")?>\s*Compare\s*</a>)'
)


def transform(text: str) -> tuple[str, int]:
    changed = 0

    def replace(m: re.Match) -> str:
        nonlocal changed
        full = m.group(1)
        prefix = m.group(2)
        # Don't double-add — check surrounding context
        # If the next ~100 chars after the match already contain a
        # "Stats" <a>, skip.
        end = m.end()
        trailing = text[end:end + 120]
        if re.search(r'<a\s+href="[^"]*stats\.html"', trailing):
            return full
        changed += 1
        new_link = f'<a href="{prefix}stats.html">Stats</a>'
        return full + "\n      " + new_link

    new_text = COMPARE_RE.sub(replace, text)
    return new_text, changed


def main():
    total = 0
    touched = 0
    for p in targets:
        txt = p.read_text(encoding="utf-8", errors="replace")
        new_txt, n = transform(txt)
        if n:
            p.write_text(new_txt, encoding="utf-8")
            touched += 1
            total += n
    print(f"Added Stats link: {total} insertions across {touched} files.")


if __name__ == "__main__":
    main()
