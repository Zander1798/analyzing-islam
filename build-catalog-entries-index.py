#!/usr/bin/env python3
"""Scan site/catalog/*.html and build a lightweight JSON index of every
entry for the community post editor's reference picker.

Each output row:
    {
      "id":        "islamic-dilemma",
      "source":    "quran",
      "title":     "The Islamic Dilemma — ...",
      "ref":       "Quran 5:43-48, 5:68, ...",
      "categories": ["scripture", "contradiction", ...],
      "strength":  "strong",
      "url":       "catalog/quran.html#islamic-dilemma"
    }
"""

import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent / "site"
CATALOG_DIR = SITE / "catalog"
OUT = SITE / "assets" / "data" / "catalog-entries.json"

ENTRY_RE = re.compile(
    r'<div\s+class="entry"\s+id="([^"]+)"\s+data-category="([^"]*)"\s+data-strength="([^"]*)"[^>]*>',
    re.I,
)
TITLE_RE = re.compile(r'<span\s+class="entry-title"[^>]*>(.*?)</span>', re.I | re.S)
REF_RE = re.compile(r'<span\s+class="ref"[^>]*>(.*?)</span>', re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean(s):
    s = TAG_RE.sub("", s or "")
    return WS_RE.sub(" ", s).strip()


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not CATALOG_DIR.is_dir():
        raise SystemExit(f"No catalog directory at {CATALOG_DIR}")

    entries = []
    for f in sorted(CATALOG_DIR.glob("*.html")):
        source = f.stem  # "quran", "bukhari", ...
        text = f.read_text(encoding="utf-8", errors="ignore")

        for m in ENTRY_RE.finditer(text):
            entry_id = m.group(1)
            categories = [c for c in m.group(2).split() if c]
            strength = m.group(3).strip() or None

            # Only consider the first ~6 KB after the entry opener so we
            # don't drift into the next entry's header when titles are
            # missing. Entries are typically well under that.
            tail = text[m.end(): m.end() + 6000]

            t = TITLE_RE.search(tail)
            r = REF_RE.search(tail)

            title = clean(t.group(1)) if t else entry_id.replace("-", " ").title()
            ref = clean(r.group(1)) if r else ""

            entries.append({
                "id": entry_id,
                "source": source,
                "title": title,
                "ref": ref,
                "categories": categories,
                "strength": strength,
                "url": f"catalog/{source}.html#{entry_id}",
            })

    # Stable sort: by source then by title. The picker will sort again
    # based on relevance, but this gives a deterministic baseline.
    entries.sort(key=lambda e: (e["source"], e["title"].lower()))

    OUT.write_text(
        json.dumps(entries, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
        newline="\n",
    )
    # Human-friendly status line on stdout.
    by_source = {}
    for e in entries:
        by_source[e["source"]] = by_source.get(e["source"], 0) + 1
    total = sum(by_source.values())
    print(f"Wrote {OUT.relative_to(SITE.parent)} — {total} entries")
    for src in sorted(by_source):
        print(f"  {src:12} {by_source[src]:>5}")


if __name__ == "__main__":
    main()
