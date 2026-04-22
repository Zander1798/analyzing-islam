#!/usr/bin/env python3
"""Migrate catalog citations from the old Muhsin Khan / Abd al-Baqi anchor
schemes to sunnah.com's idInBook scheme.

Reads:
  anchor-map-bukhari.json  — {"v5b58n234": 3731, ...}
  anchor-map-muslim.json   — {"b8n3309": 2577, ...}

Rewrites in-place across site/catalog/*.html:

  Header refs:
    <span class="ref"><a href="../read/bukhari.html#v5b58n234">Bukhari Vol 5, Book 58, #234</a>...</span>
    →
    <span class="ref"><a href="../read/bukhari.html#h3731">Bukhari 3731</a>...</span>

  Body citations:
    <a class="cite-link" href="../read/bukhari.html#v5b58n234">Bukhari Vol 5, Book 58, #234</a>
    →
    <a class="cite-link" href="../read/bukhari.html#h3731">Bukhari 3731</a>

Any anchor whose mapping is unknown is logged and left untouched.
"""
import html
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
CATALOG_DIR = ROOT / "site" / "catalog"
MAP_B = json.loads((ROOT / "anchor-map-bukhari.json").read_text(encoding="utf-8"))["map"]
MAP_M = json.loads((ROOT / "anchor-map-muslim.json").read_text(encoding="utf-8"))["map"]

# Matches <a ...href="../read/bukhari.html#v{V}b{B}n{N}"...>TEXT</a>
# The TEXT varies ("Bukhari Vol 5, Book 58, #234", "Vol 1, Book 1, #3", etc.).
BUKHARI_LINK_RE = re.compile(
    r'<a\s+([^>]*?)href="(\.\./read/bukhari\.html)#(?P<anchor>v\d+b\d+n\d+)"([^>]*)>'
    r'(?P<text>[^<]*?)</a>'
)
MUSLIM_LINK_RE = re.compile(
    r'<a\s+([^>]*?)href="(\.\./read/muslim\.html)#(?P<anchor>b\d+n\d+)"([^>]*)>'
    r'(?P<text>[^<]*?)</a>'
)


def migrate_bukhari_text(old_text: str, new_id: int) -> str:
    """Replace 'Bukhari Vol X, Book Y, #Z' (or 'Vol X, Book Y, #Z') with 'Bukhari {new_id}'.
    Preserve surrounding punctuation / narrative."""
    s = old_text
    # Full form: "Bukhari Vol 5, Book 58, #234[–236]"
    s = re.sub(
        r'Bukhari\s+Vol\s+\d+,\s+Book\s+\d+,\s+#\d+(?:[-–]\d+)?',
        f'Bukhari {new_id}',
        s,
    )
    # Standalone "Vol X, Book Y, #Z" (no Bukhari prefix, when the link text
    # omitted it — rare but possible).
    s = re.sub(
        r'Vol\s+\d+,\s+Book\s+\d+,\s+#\d+(?:[-–]\d+)?',
        f'Bukhari {new_id}',
        s,
    )
    # Extra form sometimes seen inline: "#V:B:N"
    return s


def migrate_muslim_text(old_text: str, new_id: int) -> str:
    """Replace 'Muslim Book N, #M' / 'Book N, #M' with 'Muslim {new_id}'."""
    s = old_text
    s = re.sub(
        r'Muslim\s+Book\s+\d+,\s+#\d+(?:[-–]\d+)?',
        f'Muslim {new_id}',
        s,
    )
    s = re.sub(
        r'Book\s+\d+,\s+#\d+(?:[-–]\d+)?',
        f'Muslim {new_id}',
        s,
    )
    return s


def process_bukhari(html_text: str) -> tuple[str, int, int]:
    """Return (new_html, migrated, unmapped). Unmapped entries drop the
    fragment so the link still lands on the reader top rather than on a
    dead anchor."""
    migrated = 0
    unmapped = 0

    def repl(m: re.Match) -> str:
        nonlocal migrated, unmapped
        anchor = m.group("anchor")
        old_text = m.group("text")
        pre = m.group(1)
        post = m.group(4)
        href_prefix = m.group(2)

        new_id = MAP_B.get(anchor)
        if new_id is None:
            # Unmapped: keep display text, strip the fragment so the link still
            # opens the reader top-of-page.
            unmapped += 1
            return f'<a {pre}href="{href_prefix}"{post}>{old_text}</a>'
        new_text = migrate_bukhari_text(old_text, new_id)
        migrated += 1
        return f'<a {pre}href="{href_prefix}#h{new_id}"{post}>{new_text}</a>'

    out = BUKHARI_LINK_RE.sub(repl, html_text)
    return out, migrated, unmapped


def process_muslim(html_text: str) -> tuple[str, int, int]:
    migrated = 0
    unmapped = 0

    def repl(m: re.Match) -> str:
        nonlocal migrated, unmapped
        anchor = m.group("anchor")
        old_text = m.group("text")
        pre = m.group(1)
        post = m.group(4)
        href_prefix = m.group(2)

        new_id = MAP_M.get(anchor)
        if new_id is None:
            unmapped += 1
            return f'<a {pre}href="{href_prefix}"{post}>{old_text}</a>'
        new_text = migrate_muslim_text(old_text, new_id)
        migrated += 1
        return f'<a {pre}href="{href_prefix}#h{new_id}"{post}>{new_text}</a>'

    out = MUSLIM_LINK_RE.sub(repl, html_text)
    return out, migrated, unmapped


def main() -> None:
    totals = {"b_migrated": 0, "b_unmapped": 0, "m_migrated": 0, "m_unmapped": 0}
    for path in sorted(CATALOG_DIR.glob("*.html")):
        original = path.read_text(encoding="utf-8")
        text, bm, bu = process_bukhari(original)
        text, mm, mu = process_muslim(text)
        if text != original:
            path.write_text(text, encoding="utf-8")
        totals["b_migrated"] += bm
        totals["b_unmapped"] += bu
        totals["m_migrated"] += mm
        totals["m_unmapped"] += mu
        if bm or mm or bu or mu:
            print(f"  {path.name}: bukhari {bm} migrated / {bu} unmapped · "
                  f"muslim {mm} migrated / {mu} unmapped")
    print()
    print(f"Bukhari: {totals['b_migrated']} migrated, {totals['b_unmapped']} unmapped")
    print(f"Muslim:  {totals['m_migrated']} migrated, {totals['m_unmapped']} unmapped")
    print()
    print("Next: run  python build-category-pages.py  to propagate.")


if __name__ == "__main__":
    main()
