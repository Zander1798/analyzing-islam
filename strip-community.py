"""Remove every Community nav link from every HTML page under site/.

Strips lines that look like:

    <a href="community.html">Community</a>
    <a href="../community.html">Community</a>
    <a href="../../community.html" class="active">Community</a>
    <a href="/community.html">Community</a>

…regardless of relative-path prefix, leading whitespace, or the
optional `class="active"` attribute. Other Community-tab refs (asset
loads, in-body copy) are handled separately.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"

# Match a whole line whose only content is the Community anchor.
COMMUNITY_LINE_RE = re.compile(
    r'^[ \t]*<a\s+href="(?:[./]*)community\.html"(?:\s+class="active")?\s*>'
    r'Community</a>\s*\r?\n',
    re.IGNORECASE | re.MULTILINE,
)


def process(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    new_text, count = COMMUNITY_LINE_RE.subn("", text)
    if count == 0 or new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    changed = 0
    skipped = 0
    for path in SITE.rglob("*.html"):
        if process(path):
            changed += 1
        else:
            skipped += 1
    print(f"Stripped Community nav link in {changed} file(s); left {skipped} alone.")


if __name__ == "__main__":
    main()
