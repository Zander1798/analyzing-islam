"""
remove_remaining_dupes.py

Part 1: Remove 8 Quran entries from quran.html AND catalog-entries.json.
        These IDs are in the book's EXCLUDE_IDS but were not yet removed from the site.

Part 2: Remove the SECOND occurrence of 2 Tirmidhi exact-ID duplicates from tirmidhi.html.
        Leave the first occurrence of each intact.

Backups: quran.html -> quran.html.bak2
         tirmidhi.html -> tirmidhi.html.bak2
         catalog-entries.json: NOT backed up again (backup already exists)
"""

import re
import json
import shutil
from pathlib import Path

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG_DIR = BASE / "site" / "catalog"
JSON_PATH = BASE / "site" / "assets" / "data" / "catalog-entries.json"

# ---------------------------------------------------------------------------
# Part 1: IDs to remove from quran.html AND catalog-entries.json
# ---------------------------------------------------------------------------

QURAN_REMOVE_IDS = [
    "amputate-the-hand-of-the-thief-regardless-of-circumstance-4104d45b",
    "one-hundred-lashes-for-fornication-yet-the-hadith-demands-st-f805f912",
    "quran-right-hand-sex-captive-wife",
    "quran-children-spoils-war",
    "quran-number-of-sleepers",
    "quran-how-long-sleepers-slept",
    "quran-muhammad-mutah-private-wife",
    "quran-prophet-captives-war-booty",
]

# ---------------------------------------------------------------------------
# Part 2: Tirmidhi IDs whose SECOND occurrence must be removed
# ---------------------------------------------------------------------------

TIRMIDHI_DEDUP_IDS = [
    "tirmidhi-masturbation-punishment",
    "tirmidhi-prophets-body-no-decay",
]


# ---------------------------------------------------------------------------
# Core div removal function — reused from remove_dupes_from_site.py approach
# ---------------------------------------------------------------------------

def remove_entry_div(html: str, entry_id: str) -> tuple:
    """
    Find the FIRST entry <div> with the given id and remove it from the HTML.

    Uses a div-depth counter to handle deeply nested divs inside the entry.
    Strips the preceding newline before the div as well.

    Returns (modified_html, was_found: bool).
    """
    pattern = re.compile(
        r'<div\b[^>]*\bid=["\']' + re.escape(entry_id) + r'["\'][^>]*>',
        re.DOTALL,
    )

    m = pattern.search(html)
    if m is None:
        return html, False

    tag_start = m.start()
    tag_end = m.end()

    depth = 1
    pos = tag_end

    open_tag = re.compile(r'<div\b', re.IGNORECASE)
    close_tag = re.compile(r'</div\s*>', re.IGNORECASE)

    while pos < len(html) and depth > 0:
        open_m = open_tag.search(html, pos)
        close_m = close_tag.search(html, pos)

        if close_m is None:
            # Malformed HTML — bail without removing
            return html, False

        if open_m is not None and open_m.start() < close_m.start():
            depth += 1
            pos = open_m.end()
        else:
            depth -= 1
            pos = close_m.end()

    div_end = pos

    # Strip the newline immediately before this div
    newline_before = html.rfind('\n', 0, tag_start)
    if newline_before != -1:
        remove_from = newline_before
    else:
        remove_from = tag_start

    modified = html[:remove_from] + html[div_end:]
    return modified, True


def remove_second_entry_div(html: str, entry_id: str) -> tuple:
    """
    Find the SECOND <div class="entry" id="entry_id"> and remove it.

    Only div-level opening tags that contain the exact id are considered
    actual entry starts (not body-text references to the same ID).

    Returns (modified_html, status_str).
      status_str is one of: "removed", "only_one_found", "none_found", "too_few_div_entries"
    """
    # Find all positions where this id appears inside a proper opening <div> tag.
    open_pattern = re.compile(
        r'<div\b[^>]*\bid=["\']' + re.escape(entry_id) + r'["\'][^>]*>',
        re.DOTALL,
    )

    div_entry_starts = list(open_pattern.finditer(html))

    if len(div_entry_starts) == 0:
        return html, "none_found"
    if len(div_entry_starts) == 1:
        return html, "only_one_found"

    # We have >= 2 actual div entries with this id — remove the second one.
    second_match = div_entry_starts[1]
    tag_start = second_match.start()
    tag_end = second_match.end()

    depth = 1
    pos = tag_end

    open_tag = re.compile(r'<div\b', re.IGNORECASE)
    close_tag = re.compile(r'</div\s*>', re.IGNORECASE)

    while pos < len(html) and depth > 0:
        open_m = open_tag.search(html, pos)
        close_m = close_tag.search(html, pos)

        if close_m is None:
            return html, "malformed_html"

        if open_m is not None and open_m.start() < close_m.start():
            depth += 1
            pos = open_m.end()
        else:
            depth -= 1
            pos = close_m.end()

    div_end = pos

    # Strip the newline immediately before this div
    newline_before = html.rfind('\n', 0, tag_start)
    if newline_before != -1:
        remove_from = newline_before
    else:
        remove_from = tag_start

    modified = html[:remove_from] + html[div_end:]
    return modified, "removed"


# ---------------------------------------------------------------------------
# Verification helpers
# ---------------------------------------------------------------------------

def count_id_in_html(html: str, entry_id: str) -> int:
    """Count how many times entry_id appears as an opening div id attribute."""
    pattern = re.compile(
        r'<div\b[^>]*\bid=["\']' + re.escape(entry_id) + r'["\'][^>]*>',
        re.DOTALL,
    )
    return len(pattern.findall(html))


def count_id_in_json(entries: list, entry_id: str) -> int:
    return sum(1 for e in entries if e.get('id') == entry_id)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 65)
    print("remove_remaining_dupes.py")
    print("=" * 65)

    # --- Part 1: quran.html + catalog-entries.json ---

    quran_path = CATALOG_DIR / "quran.html"
    quran_bak2 = quran_path.with_suffix(".html.bak2")

    print(f"\nBacking up quran.html -> {quran_bak2.name}")
    shutil.copy2(quran_path, quran_bak2)

    quran_html = quran_path.read_text(encoding='utf-8', errors='ignore')
    quran_removed = 0
    quran_not_found = []

    print("\nPart 1 — Removing 8 excluded Quran entries from quran.html:")
    for eid in QURAN_REMOVE_IDS:
        quran_html, found = remove_entry_div(quran_html, eid)
        if found:
            quran_removed += 1
            print(f"  [OK]   {eid}")
        else:
            quran_not_found.append(eid)
            print(f"  [MISS] {eid} — not found in quran.html")

    quran_path.write_text(quran_html, encoding='utf-8')
    print(f"\n  quran.html: {quran_removed} / {len(QURAN_REMOVE_IDS)} divs removed")

    # catalog-entries.json
    print("\nPart 1 — Removing same 8 IDs from catalog-entries.json:")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    json_before = len(entries)
    remove_set = set(QURAN_REMOVE_IDS)
    kept = [e for e in entries if e.get('id') not in remove_set]
    json_after = len(kept)
    json_removed = json_before - json_after

    json_not_found = [eid for eid in QURAN_REMOVE_IDS
                      if not any(e.get('id') == eid for e in entries)]
    for eid in json_not_found:
        print(f"  [MISS] {eid} — not found in catalog-entries.json")
    if not json_not_found:
        print(f"  All 8 IDs found and removed.")

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    print(f"  catalog-entries.json: {json_before} -> {json_after} "
          f"({json_removed} removed)")

    # --- Part 2: tirmidhi.html second-occurrence removal ---

    tirmidhi_path = CATALOG_DIR / "tirmidhi.html"
    tirmidhi_bak2 = tirmidhi_path.with_suffix(".html.bak2")

    print(f"\nBacking up tirmidhi.html -> {tirmidhi_bak2.name}")
    shutil.copy2(tirmidhi_path, tirmidhi_bak2)

    tirmidhi_html = tirmidhi_path.read_text(encoding='utf-8', errors='ignore')
    tirmidhi_removed = 0

    print("\nPart 2 — Removing second occurrences of Tirmidhi duplicate IDs:")
    for eid in TIRMIDHI_DEDUP_IDS:
        tirmidhi_html, status = remove_second_entry_div(tirmidhi_html, eid)
        if status == "removed":
            tirmidhi_removed += 1
            print(f"  [OK]   {eid} — second copy removed")
        elif status == "only_one_found":
            print(f"  [SKIP] {eid} — only one div entry found, nothing to deduplicate")
        elif status == "none_found":
            print(f"  [MISS] {eid} — no div entry found at all")
        else:
            print(f"  [WARN] {eid} — status: {status}")

    tirmidhi_path.write_text(tirmidhi_html, encoding='utf-8')
    print(f"\n  tirmidhi.html: {tirmidhi_removed} second-copy divs removed")

    # --- Verification ---

    print("\n" + "=" * 65)
    print("VERIFICATION")
    print("=" * 65)

    # Re-read the written files for verification
    quran_html_final = quran_path.read_text(encoding='utf-8', errors='ignore')
    tirmidhi_html_final = tirmidhi_path.read_text(encoding='utf-8', errors='ignore')
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        entries_final = json.load(f)

    print("\nPart 1 — quran.html: 8 IDs must be absent (count = 0)")
    all_quran_clean = True
    for eid in QURAN_REMOVE_IDS:
        n = count_id_in_html(quran_html_final, eid)
        status = "PASS" if n == 0 else "FAIL"
        if n != 0:
            all_quran_clean = False
        print(f"  [{status}] {eid}: {n} occurrences")

    print("\nPart 1 — catalog-entries.json: 8 IDs must be absent (count = 0)")
    all_json_clean = True
    for eid in QURAN_REMOVE_IDS:
        n = count_id_in_json(entries_final, eid)
        status = "PASS" if n == 0 else "FAIL"
        if n != 0:
            all_json_clean = False
        print(f"  [{status}] {eid}: {n} occurrences")

    print("\nPart 2 — tirmidhi.html: dedup IDs must appear exactly 1 time")
    all_tirmidhi_clean = True
    for eid in TIRMIDHI_DEDUP_IDS:
        n = count_id_in_html(tirmidhi_html_final, eid)
        status = "PASS" if n == 1 else "FAIL"
        if n != 1:
            all_tirmidhi_clean = False
        print(f"  [{status}] {eid}: {n} occurrences (expected 1)")

    print(f"\nFinal catalog-entries.json count: {len(entries_final)}")

    # --- Summary ---

    print("\n" + "=" * 65)
    print("SUMMARY")
    print("=" * 65)
    print(f"  quran.html entries removed:           {quran_removed}")
    print(f"  catalog-entries.json entries removed: {json_removed}")
    print(f"  tirmidhi.html second-copies removed:  {tirmidhi_removed}")
    print(f"  Final catalog-entries.json count:     {len(entries_final)}")

    overall = all_quran_clean and all_json_clean and all_tirmidhi_clean
    print(f"\n  Overall verification: {'ALL PASS' if overall else 'SOME FAILURES — check above'}")
    print("\nDone.")


if __name__ == "__main__":
    main()
