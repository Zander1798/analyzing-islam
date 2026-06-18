#!/usr/bin/env python3
"""Surgery-based category page rebuild.
Replaces only the #entries-container content and section-title count
in each existing category page. Preserves all chrome unchanged.
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"
CATALOG_DIR = SITE / "catalog"
CATEGORY_DIR = SITE / "category"

CATEGORIES = [
    "abrogation", "scripture", "contradiction", "logic", "morality",
    "allah", "cosmology", "science", "preislamic", "magic", "ritual",
    "prophet", "privileges", "jesus", "women", "sexual", "childmarriage",
    "lgbtq", "slavery", "hudud", "warfare", "apostasy", "governance",
    "disbelievers", "antisemitism", "paradise", "hell", "eschatology",
    "strange", "incest", "gross-vile", "animals",
]

CATALOG_FILES = [
    "quran.html",
    "bukhari.html",
    "muslim.html",
    "abu-dawud.html",
    "tirmidhi.html",
    "nasai.html",
    "ibn-majah.html",
]

ENTRY_START_RE = re.compile(r'<div class="entry"[^>]*data-category="([^"]+)"[^>]*>')


def extract_entries(html: str):
    """Return list of (categories_set, entry_html) tuples."""
    results = []
    i = 0
    while True:
        m = ENTRY_START_RE.search(html, i)
        if not m:
            break
        cats = set(m.group(1).split())
        start = m.start()
        depth = 1
        j = m.end()
        while depth > 0 and j < len(html):
            next_open = html.find("<div", j)
            next_close = html.find("</div>", j)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                j = next_open + len("<div")
            else:
                depth -= 1
                j = next_close + len("</div>")
        entry_html = html[start:j]
        results.append((cats, entry_html))
        i = j
    return results


# Gather all entries from all catalog files.
all_entries = []
for fname in CATALOG_FILES:
    path = CATALOG_DIR / fname
    if not path.exists():
        print(f"WARN: {path} missing, skipping")
        continue
    html = path.read_text(encoding="utf-8")
    entries = extract_entries(html)
    all_entries.extend(entries)
    print(f"  {fname}: {len(entries)} entries extracted")

print(f"Total entries across all catalogs: {len(all_entries)}")


def replace_entries_container(page_html: str, new_entries: list, token: str) -> str:
    """Replace #entries-container content and section-title count in page HTML."""
    # Replace section-title count
    total = len(new_entries)
    plural = "y" if total == 1 else "ies"
    new_title = f'<div class="section-title">{total} entr{plural} in this category</div>'
    page_html = re.sub(
        r'<div class="section-title">\d+ entr(?:y|ies) in this category</div>',
        new_title,
        page_html,
    )

    # Find entries-container opening tag
    ec_open_tag = '<div id="entries-container">'
    ec_start = page_html.find(ec_open_tag)
    if ec_start == -1:
        raise ValueError(f"#entries-container not found")
    content_start = ec_start + len(ec_open_tag)

    # Find the closing of entries-container.
    # The container ends with:  \n    </div>\n  </section>
    # i.e. entries-container closing </div>, then section closing </div>
    ec_close_marker = "\n    </div>\n  </section>"
    ec_close_pos = page_html.find(ec_close_marker, content_start)
    if ec_close_pos == -1:
        raise ValueError(f"entries-container close not found")

    # Build new content
    if new_entries:
        entries_block = "\n\n".join(new_entries)
        new_content = f"\n\n{entries_block}\n\n"
    else:
        new_content = '\n\n<div class="empty">No entries in this category yet.</div>\n\n'

    new_html = page_html[:content_start] + new_content + page_html[ec_close_pos:]
    return new_html


changes = {}
for token in CATEGORIES:
    page_path = CATEGORY_DIR / f"{token}.html"
    if not page_path.exists():
        print(f"WARN: {page_path} missing, skipping")
        continue

    matched = [h for cats, h in all_entries if token in cats]
    page_html = page_path.read_text(encoding="utf-8")

    try:
        new_html = replace_entries_container(page_html, matched, token)
    except ValueError as e:
        print(f"ERROR on {token}: {e}")
        continue

    page_path.write_text(new_html, encoding="utf-8")
    changes[token] = len(matched)
    print(f"  {token}.html: {len(matched)} entries")

print(f"\nUpdated {len(changes)} category pages in {CATEGORY_DIR}")
