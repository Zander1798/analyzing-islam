"""One-shot fix: every page on the site should carry the full 8-item
site nav (Home, Catalog, Read, Compare, Build, Stats, About, FAQ).
Category pages and the Interlinear Bible's index + sub-pages still
carry an older 5-item version — this script rewrites their
<div class="site-nav-links">…</div> block, preserving the relative
path prefix ("../" vs "../../") and the `class="active"` attribute on
whichever link was currently marked active.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"

# (order matches how the nav should render)
NAV_LINKS = [
    ("Home",      "index.html"),
    ("Catalog",   "catalog.html"),
    ("Read",      "read.html"),
    ("Compare",   "compare.html"),
    ("Build",     "build.html"),
    ("Stats",     "stats.html"),
    ("About",     "about.html"),
    ("FAQ",       "faq.html"),
]

NAV_BLOCK_RE = re.compile(
    r'(<div class="site-nav-links">)(.*?)(</div>)', re.DOTALL
)
LINK_RE = re.compile(
    r'<a\s+href="([^"]+?)"(?:\s+class="active")?\s*>([^<]+)</a>',
    re.IGNORECASE,
)


def rewrite_nav(block_inner: str, indent: str) -> str | None:
    """Return a full-nav replacement, or None if the block is already
    the 8-item version (no rewrite needed)."""
    links = LINK_RE.findall(block_inner)
    if not links:
        return None

    # Detect prefix (everything before the terminal filename). Assume
    # consistent within a single nav block.
    first_href = links[0][0]
    if "/" in first_href:
        prefix = first_href.rsplit("/", 1)[0] + "/"
    else:
        prefix = ""

    # Current active target, if any.
    active_raw = re.search(
        r'<a\s+href="([^"]+)"\s+class="active"\s*>', block_inner
    )
    active_file = None
    if active_raw:
        active_file = active_raw.group(1).rsplit("/", 1)[-1]

    # Already the full 8-item nav? Skip.
    have_files = {href.rsplit("/", 1)[-1].lower() for href, _ in links}
    wanted_files = {f for _, f in NAV_LINKS}
    if wanted_files <= have_files:
        return None

    lines = []
    for label, filename in NAV_LINKS:
        href = prefix + filename
        extra = ' class="active"' if filename == active_file else ""
        lines.append(f'{indent}  <a href="{href}"{extra}>{label}</a>')
    return "\n" + "\n".join(lines) + f"\n{indent}"


def indent_of(html: str, match_start: int) -> str:
    line_start = html.rfind("\n", 0, match_start) + 1
    # Indent up to the "<" character.
    return html[line_start:match_start]


def process(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    m = NAV_BLOCK_RE.search(html)
    if not m:
        return False
    ind = indent_of(html, m.start())
    replacement = rewrite_nav(m.group(2), ind)
    if replacement is None:
        return False
    new_block = m.group(1) + replacement + m.group(3)
    new_html = html[:m.start()] + new_block + html[m.end():]
    if new_html == html:
        return False
    path.write_text(new_html, encoding="utf-8")
    return True


def main() -> None:
    targets = []
    for pattern in (
        "category/*.html",
        "read-external/*.html",
        "read-external/bible/*.html",
        "*.html",
        "catalog/*.html",
        "read/*.html",
    ):
        targets.extend(sorted(SITE.glob(pattern)))

    changed = 0
    skipped = 0
    for path in targets:
        if process(path):
            changed += 1
        else:
            skipped += 1
    print(f"Rewrote nav on {changed} file(s); left {skipped} alone.")


if __name__ == "__main__":
    main()
