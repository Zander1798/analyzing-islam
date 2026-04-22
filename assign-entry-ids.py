#!/usr/bin/env python3
"""Ensure every catalog entry <div class="entry"> has a stable `id` attribute.

Strategy:
  - If the entry already has an id, leave it alone.
  - Otherwise, derive a slug from the entry-title + a short stable hash
    of the full entry HTML (so re-running on the same content reproduces
    the same id).

Operates on site/catalog/*.html — the catalog pages are the source of
truth for entries. Category pages are generated from these by
build-category-pages.py, so we re-run that afterward to propagate.
"""
import hashlib
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SITE = Path(__file__).parent / "site"
CATALOG = SITE / "catalog"

# Match <div class="entry" ...> — we care about three cases:
#   data-category + data-strength, no id    -> inject id
#   id already present                       -> leave alone
ENTRY_START_RE = re.compile(
    r'<div class="entry"([^>]*)>',
)
TITLE_RE = re.compile(r'<span class="entry-title">(.*?)</span>', re.DOTALL)


def slugify(s: str, max_len: int = 60) -> str:
    # lowercase, remove tags, strip punctuation, collapse whitespace to dashes
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[̀-ͯ]", "", s)  # combining marks
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:max_len].rstrip("-")


def short_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def find_entry_end(text: str, start_idx: int) -> int:
    """Walk forward counting <div> opens/closes to find the matching </div>."""
    depth = 1
    j = start_idx
    while depth > 0 and j < len(text):
        next_open = text.find("<div", j)
        next_close = text.find("</div>", j)
        if next_close == -1:
            return len(text)
        if next_open != -1 and next_open < next_close:
            depth += 1
            j = next_open + len("<div")
        else:
            depth -= 1
            j = next_close + len("</div>")
    return j


def process_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    out = []
    i = 0
    injected = 0
    kept = 0
    total = 0

    while True:
        m = ENTRY_START_RE.search(text, i)
        if not m:
            out.append(text[i:])
            break

        total += 1
        attrs = m.group(1)
        out.append(text[i:m.start()])

        if re.search(r'\bid=', attrs):
            # Already has id — leave unchanged
            out.append(m.group(0))
            i = m.end()
            kept += 1
            continue

        # Find the full entry block to hash for stable id
        end = find_entry_end(text, m.end())
        block = text[m.start():end]

        # Extract title for slug
        tm = TITLE_RE.search(block)
        title = tm.group(1).strip() if tm else "entry"
        slug = slugify(title) or "entry"

        # Hash: source file stem + title (keeps ids unique across catalogs
        # and stable across minor edits that don't touch the title).
        payload = f"{path.stem}::{title}"
        hsh = short_hash(payload)
        new_id = f"{slug}-{hsh}"

        new_open = f'<div class="entry" id="{new_id}"{attrs}>'
        out.append(new_open)
        out.append(text[m.end():end])
        i = end
        injected += 1

    new_text = "".join(out)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")

    return {"total": total, "injected": injected, "kept": kept}


def main():
    totals = {"total": 0, "injected": 0, "kept": 0}
    for f in sorted(CATALOG.glob("*.html")):
        r = process_file(f)
        print(f"  {f.name}: {r['total']} entries — {r['injected']} new ids, {r['kept']} kept")
        for k in totals:
            totals[k] += r[k]
    print(f"\nTotal: {totals['total']} entries, {totals['injected']} new ids injected, "
          f"{totals['kept']} kept.")


if __name__ == "__main__":
    main()
