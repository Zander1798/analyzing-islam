"""
remove_dupes_from_site.py

Removes duplicate entry <div> blocks from site catalog HTML files and
(for Category 2) also removes those entries from catalog-entries.json.

Category 1: HTML-only removal (already removed from JSON by apply_dedup.py).
Category 2: Remove from quran.html AND catalog-entries.json (near-duplicates).
"""

import re
import json
import shutil
from pathlib import Path

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG_DIR = BASE / "site" / "catalog"
JSON_PATH = BASE / "site" / "assets" / "data" / "catalog-entries.json"

# ---------------------------------------------------------------------------
# Category 1: Remove from HTML only (already gone from catalog-entries.json)
# ---------------------------------------------------------------------------

CAT1 = {
    "quran.html": [
        "quran-recite-jealousy-envy-refuge",
        "quran-unjust-acquittal-womens-lashes",
        "quran-slaves-half-hudud",
        "quran-private-parts-except-captives",
        "quran-adultery-hundred-lashes",
        "quran-harut-marut-teaching-magic",
        "quran-qiblah-abrogation",
        "quran-qisas-slave-free-unequal",
        "quran-wives-tilth-field",
        "quran-halala-intermediate-husband",
        "quran-two-women-one-man-witness",
        "quran-zaynab-detailed",
        "quran-male-double-inheritance",
        "quran-muhsanat-captive-exception",
        "quran-marry-two-three-four",
        "quran-beat-wife-after-admonish",
        "quran-moon-split-miracle",
        "quran-jews-most-hostile",
        "quran-iddah-prepubescent-divorce",
        "quran-no-changing-words",
        "quran-strike-necks-polytheists",
        "quran-20-vs-200-abrogated",
        "quran-captives-massacre-first",
        "quran-allah-locks-hearts",
        "do-not-compel-your-slave-girls-to-prostitution-if-they-desir-40074e30",
        "quran-good-evil-from-yourself-contradiction",
        "quran-arabs-lovers-of-arabic",
    ],
    "bukhari.html": [
        "fly-wing-dip-drink-cure",
        "prophet-fondled-menstruating-wife",
        "flee-battle-major-sin",
        "nine-wives-one-round",
        "muslim-not-killed-for-kafir-diya",
        "allah-visits-earth-third-of-night",
        "prophet-kissed-aisha-during-fast",
        "prophet-cursed-those-making-pictures",
        "bukhari-3151-satan-touches-every-newborn-except-jesus",
        "angels-avoid-dog-picture",
        "uthman-burned-variant-codices",
        "bukhari-4785-quran-seven-recitations-both-valid",
        "dog-donkey-women-pass-prayer",
        "bukhari-5659-effeminate-cursed-expelled",
        "muhammad-threats-burn-houses",
        "banu-qurayza-massacre-detail",
        "bukhari-2807-stones-betray-jews",
        "aisha-six-nine-consummation",
        "bukhari-2076-slave-girl-flogged-sold",
        "muhammad-suicide",
        "allah-changes-mind-prayer-count",
        "allah-changed-mind-prayers",
        "urine-splash-torture",
        "cupping-specific-days",
    ],
    "muslim.html": [
        "the-dajjal-will-be-followed-by-70-000-jews-of-isfahan-wearin-882183da",
        "muslim-kill-jews-dajjal-army",
        "muslim-silver-gold-utensils-forbidden-men",
        "muslim-jesus-descends-kills-swine-breaks-cross",
        "expel-arabia-multi-religion",
        "tree-stone-tell-hiding-jew",
        "gecko-hundred-rewards",
        "ibn-sayyad-dajjal-child",
        "satan-blood-circulation",
        "muslim-apostate-three-categories-kill",
        "muslim-spit-left-after-dream",
        "muslim-sun-prostrates-beneath-throne",
        "the-sun-prostrates-under-allah-s-throne-every-night-and-asks-b0b69753",
        "muslim-women-children-night-raid-incidental",
        "muslim-woman-refuses-bed-angels-curse",
    ],
    "abu-dawud.html": [
        "fly-dunk-dawud-confirms",
        "convert-circumcision-hair",
        "abu-dawud-riba-curses",
        "whoever-changes-religion-execute",
        "four-month-waiting-period",
        "hell-seven-gates-dawud",
        "safiyyah-emancipation-mahr-dawud",
        "abu-dawud-4404-hand-theft-quarter-dinar",
        "black-dog-shaitan-invalidates-prayer",
        "night-raid-children-women-dawud",
    ],
    "tirmidhi.html": [
        "tirmidhi-food-mention-allah",
        "tirmidhi-hijab-cover-face",
        "tirmidhi-hell-complains-breath-heat",
        "tirmidhi-prayer-fire-paradise",
        "tirmidhi-sodomy-death-penalty",
        "tirmidhi-seventy-thousand-paradise-no-reckoning",
        "tirmidhi-kaaba-black-stone",
        "tirmidhi-cat-pure-unique-ruling",
        "tirmidhi-adultery-100-lashes",
        "tirmidhi-3617-jesus-buried-next-to-muhammad",
        "tirmidhi-newborn-cry-satan-pinch",
        "tirmidhi-evil-eye-touching",
    ],
    "nasai.html": [
        "nasai-whoever-changes-religion-kill-him",
        "nasai-fornicator-flogged-exiled",
        "nasai-slave-marriage-no-wali-fornicator",
        "nasai-wife-ghusl-husband-command",
        "nasai-wife-as-tilth-however-you-wish",
        "nasai-khutbah-last-words-final-sermon",
        "nasai-urine-left-hand-not-right",
        "nasai-jihad-women-cannot-lead-prayer",
        "nasai-wife-deserts-bed-angels-curse",
    ],
    "ibn-majah.html": [
        "ibnmajah-kill-whoever-abandons-islam",
        "ibnmajah-pen-first-created-write",
        "ibnmajah-prophet-cursed-paint-artist",
        "ibnmajah-allah-descends-end-night-cry",
        "ibnmajah-amputation-thief-hand-dinar",
        "ibnmajah-aisha-young",
        "ibnmajah-jinn-eavesdrop-soothsayers",
        "ibnmajah-wife-refuse-bed-angels-curse-morning",
    ],
}

# ---------------------------------------------------------------------------
# Category 2: Remove from quran.html AND catalog-entries.json
# ---------------------------------------------------------------------------

CAT2_IDS = [
    "jews-transformed-into-apes-a205d9d7",
    "the-sun-runs-to-a-fixed-resting-place-5f69c2e2",
    "quran-fire-punishment-to-skin-replace",
    "polytheists-are-unclean-and-forbidden-from-the-sacred-mosque-793234d0",
    "fabricated-quote-jews-say-ezra-is-the-son-of-allah-df9200f3",
    "quran-menstruating-retreat",
    "quran-cow-that-killed",
    "quran-iblis-command-prostrate",
    "jinn-listen-to-the-quran-in-a-tree-and-convert-63828ff4",
    "creation-in-six-days-or-eight-a-day-count-contradiction-201b57cd",
    "quran-predestination-but-punishment",
    "quran-allah-best-plotters-jesus",
    "quran-pharaoh-wall-building",
    "quran-do-not-befriend-kafir",
]

# IDs that must NEVER be removed (keeper side of pairs / standalone)
NEVER_REMOVE = {
    "quran-right-hand-sex-captive-wife",
    "one-hundred-lashes-for-fornication-yet-the-hadith-demands-st-f805f912",
    "amputate-the-hand-of-the-thief-regardless-of-circumstance-4104d45b",
    "quran-children-spoils-war",
    "quran-number-of-sleepers",
    "quran-how-long-sleepers-slept",
    "quran-muhammad-mutah-private-wife",
    "quran-prophet-captives-war-booty",
}


def remove_entry_div(html: str, entry_id: str) -> tuple:
    """
    Find the entry <div> with the given id and remove it from the HTML.

    Uses a div-depth counter to handle deeply nested divs inside the entry.
    Strips the leading newline/whitespace before the div as well.

    Returns (modified_html, was_found: bool).
    """
    # Build a pattern that matches the opening tag of this specific entry.
    # The id attribute can appear before or after class, and quotes can be
    # single or double. We anchor on the id value being an exact match.
    pattern = re.compile(
        r'<div\b[^>]*\bid=["\']' + re.escape(entry_id) + r'["\'][^>]*>',
        re.DOTALL,
    )

    m = pattern.search(html)
    if m is None:
        return html, False

    tag_start = m.start()
    tag_end = m.end()

    # Walk forward from the end of the opening tag, tracking div depth.
    # We start at depth=1 (we are inside the opening div we just matched).
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
            # Next tag is an open <div>
            depth += 1
            pos = open_m.end()
        else:
            # Next tag is </div>
            depth -= 1
            pos = close_m.end()

    # pos is now just past the closing </div> of the entry
    div_end = pos

    # Also strip any whitespace/newline that immediately precedes the opening tag
    strip_start = tag_start
    while strip_start > 0 and html[strip_start - 1] in (' ', '\t', '\r', '\n'):
        strip_start -= 1

    # But only strip the single preceding newline (keep paragraph spacing above)
    # We want to remove \n<div...>...\n so we strip back to the newline before it
    # Actually: remove the newline that separates this div from the prior entry,
    # keeping the whitespace structure intact for the entries that remain.
    # Strategy: remove from the last \n before the div (exclusive) through div_end.
    newline_before = html.rfind('\n', 0, tag_start)
    if newline_before != -1:
        remove_from = newline_before  # keep the \n itself? No — include it
        # We want to delete "\n<div...></div>" so remove from newline_before (inclusive)
        remove_from = newline_before
    else:
        remove_from = tag_start

    modified = html[:remove_from] + html[div_end:]
    return modified, True


def process_html_file(fname: str, ids_to_remove: list) -> int:
    """
    Back up the HTML file, remove the specified entry divs, write result.
    Returns count of divs actually removed.
    """
    path = CATALOG_DIR / fname
    html = path.read_text(encoding='utf-8', errors='ignore')

    # Back up before any modification
    bak_path = path.with_suffix(path.suffix + '.bak')
    shutil.copy2(path, bak_path)

    removed_count = 0
    not_found = []

    for eid in ids_to_remove:
        # Safety guard
        if eid in NEVER_REMOVE:
            print(f"  [SKIP] {eid} is in NEVER_REMOVE — skipping")
            continue

        html, found = remove_entry_div(html, eid)
        if found:
            removed_count += 1
        else:
            not_found.append(eid)

    if not_found:
        print(f"  [WARN] {fname}: {len(not_found)} IDs not found in HTML:")
        for eid in not_found:
            print(f"    - {eid}")

    path.write_text(html, encoding='utf-8')
    return removed_count


def update_json(ids_to_remove: list) -> tuple:
    """
    Remove the given IDs from catalog-entries.json.
    Returns (original_count, new_count).
    NOTE: backup2 already exists — do NOT overwrite it.
    """
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    original_count = len(entries)
    remove_set = set(ids_to_remove)

    kept = [e for e in entries if e['id'] not in remove_set]
    removed_ids = {e['id'] for e in entries if e['id'] in remove_set}

    not_found_in_json = [eid for eid in ids_to_remove if eid not in removed_ids]
    if not_found_in_json:
        print(f"  [WARN] JSON: {len(not_found_in_json)} IDs not found in catalog-entries.json:")
        for eid in not_found_in_json:
            print(f"    - {eid}")

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    return original_count, len(kept)


def verify_entry_counts(files: dict):
    """Count entry divs in each HTML file and print summary."""
    print("\nEntry div counts after modification:")
    for fname in files:
        path = CATALOG_DIR / fname
        html = path.read_text(encoding='utf-8', errors='ignore')
        count = len(re.findall('<div[^>]+class="[^"]*entry[^"]*"[^>]+id="[^"]+"', html))
        print(f"  {fname}: {count} entries")


def main():
    print("=" * 60)
    print("remove_dupes_from_site.py")
    print("=" * 60)

    total_html_removed = 0

    # --- Category 1: HTML only ---
    print("\nCategory 1: HTML-only removal (7 files)")
    cat1_totals = {}
    for fname, ids in CAT1.items():
        count = process_html_file(fname, ids)
        cat1_totals[fname] = count
        print(f"  {fname}: removed {count} / {len(ids)} divs")
        total_html_removed += count

    # --- Category 2: quran.html + JSON ---
    print("\nCategory 2: quran.html + catalog-entries.json removal (14 entries)")
    quran_cat2_count = process_html_file("quran.html", CAT2_IDS)
    print(f"  quran.html: removed {quran_cat2_count} / {len(CAT2_IDS)} divs")
    total_html_removed += quran_cat2_count

    json_before, json_after = update_json(CAT2_IDS)
    json_removed = json_before - json_after
    print(f"  catalog-entries.json: {json_before} -> {json_after} entries ({json_removed} removed)")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total HTML entry divs removed: {total_html_removed}")
    print()
    print("Per-file breakdown:")

    all_files = list(CAT1.keys())
    for fname in all_files:
        cat1_count = cat1_totals.get(fname, 0)
        cat2_count = quran_cat2_count if fname == "quran.html" else 0
        total = cat1_count + cat2_count
        if fname == "quran.html":
            print(f"  {fname}: {total} total ({cat1_count} cat1 + {cat2_count} cat2)")
        else:
            print(f"  {fname}: {total} divs removed")

    print()
    print(f"catalog-entries.json: {json_before} -> {json_after} entries ({json_removed} removed)")

    verify_entry_counts(CAT1)

    print("\nDone.")


if __name__ == "__main__":
    main()
