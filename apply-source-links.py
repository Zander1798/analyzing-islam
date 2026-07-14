#!/usr/bin/env python3
"""Canonical external-source link normaliser (idempotent pipeline stage).

The scholarly-source links inside catalog entries and dossiers are baked into
the rendered HTML as  <a class="src-link" href="…">…</a> .  Historically some
of those hrefs pointed at fragile "opensource"/"community" Internet-Archive
uploads (pirate copies of in-copyright books) that return "Bad Request" or get
removed.  This script rewrites every src-link href to the single best
PERMANENT, READABLE, LEGAL target defined in source-link-map.json.

Run AFTER build-catalog-pages.py / build-category-pages.py / build-arguments.py
(those regenerate entry HTML from link-less book data, so this re-applies the
canonical links).  Idempotent: running twice changes nothing the second time.

    python apply-source-links.py            # rewrite in place
    python apply-source-links.py --check     # report only, exit 1 if changes needed
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
MAP_FILE = ROOT / "source-link-map.json"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CHECK = "--check" in sys.argv

cfg = json.loads(MAP_FILE.read_text(encoding="utf-8"))
MAP = cfg["map"]              # old_archive_id -> {url, tier, ...} OR {rules:[{contains,url}], default_url}

# Match a full src-link anchor so we can see both href and visible text.
ANCHOR = re.compile(r'(<a\s+class="src-link"\s+href=")([^"]+)("[^>]*>)(.*?)(</a>)', re.S)
ARCHIVE_ID = re.compile(r'archive\.org/details/([A-Za-z0-9._-]+)')
OPENLIB_ID = re.compile(r'openlibrary\.org/works/(OL\d+W)')
OPENLIB_ISBN = re.compile(r'openlibrary\.org/isbn/(\d[\dXx]+)')
TAGS = re.compile(r"<[^>]+>")


def href_key(href: str):
    """The map is keyed by the identifier inside a book href: an Internet-Archive
    item id (archive.org/details/<id>), an OpenLibrary work id
    (openlibrary.org/works/<OLxxxW>), or an OpenLibrary ISBN
    (openlibrary.org/isbn/<isbn> -> "ISBN<isbn>"). Return that key, or None."""
    m = ARCHIVE_ID.search(href)
    if m:
        return m.group(1)
    m = OPENLIB_ID.search(href)
    if m:
        return m.group(1)
    m = OPENLIB_ISBN.search(href)
    if m:
        return "ISBN" + m.group(1)
    return None


def resolve(old_id: str, anchor_text: str) -> str | None:
    """Return the replacement URL for this archive identifier, or None if no rule."""
    entry = MAP.get(old_id)
    if entry is None:
        return None
    if "rules" in entry:
        plain = TAGS.sub("", anchor_text)
        for rule in entry["rules"]:
            if rule["contains"].lower() in plain.lower():
                return rule["url"]
        return entry.get("default_url")
    return entry["url"]


def process(html: str) -> tuple[str, int, list[str]]:
    changed = 0
    unresolved: list[str] = []

    def repl(m: re.Match) -> str:
        nonlocal changed
        pre, href, mid, inner, close = m.groups()
        old_id = href_key(href)
        if not old_id:
            return m.group(0)                      # not a book link we manage — leave
        new_url = resolve(old_id, inner)
        if new_url is None:
            if old_id not in MAP:
                unresolved.append(old_id)
            return m.group(0)
        if href == new_url:
            return m.group(0)                      # already canonical
        changed += 1
        return f"{pre}{new_url}{mid}{inner}{close}"

    out = ANCHOR.sub(repl, html)
    return out, changed, unresolved


def main() -> int:
    total_changed = 0
    files_changed = 0
    all_unresolved: dict[str, int] = {}
    for path in SITE.rglob("*.html"):
        html = path.read_text(encoding="utf-8", errors="ignore")
        if 'class="src-link"' not in html:
            continue
        out, changed, unresolved = process(html)
        for u in unresolved:
            all_unresolved[u] = all_unresolved.get(u, 0) + 1
        if changed:
            total_changed += changed
            files_changed += 1
            if not CHECK:
                path.write_text(out, encoding="utf-8")

    print(f"src-link hrefs rewritten: {total_changed} across {files_changed} files"
          + (" (check-only, nothing written)" if CHECK else ""))
    if all_unresolved:
        # archive identifiers on the site that are NOT in the map — good ones map to
        # themselves in the map, so anything here is an unmapped archive link to review.
        print(f"\nUnmapped archive.org identifiers still on site ({len(all_unresolved)}):")
        for u, n in sorted(all_unresolved.items(), key=lambda kv: -kv[1]):
            print(f"  x{n:>4}  {u}")
    if CHECK and total_changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
