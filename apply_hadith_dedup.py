"""
apply_hadith_dedup.py
Removes confirmed intra-source duplicate entries from the 6 hadith catalog
HTML files and rebuilds catalog-entries.json.

Run from project root:
    python apply_hadith_dedup.py
"""
import re, json, shutil
from pathlib import Path
from collections import defaultdict

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG_DIR = BASE / "site/catalog"
CATALOG_JSON = BASE / "site/assets/data/catalog-entries.json"

# ---------------------------------------------------------------------------
# Confirmed removes — 21 intra-source duplicates
# Format: ("drop_id", "keep_id")  — keep_id for documentation only
# ---------------------------------------------------------------------------
CONFIRMED_REMOVES = [
    # BUKHARI (7)
    ("wife-beating-camel",                "beat-slave-sleep-with-her"),
    ("two-fasting-doors",                 "devils-chained-ramadan"),
    ("number-of-dates-odd-seven",         "seven-ajwa"),
    ("cursed-effeminate-men-masculine-women", "effeminate-men-cursed"),
    ("kiss-black-stone",                  "hajj-pagan-rituals-preserved-explicit"),
    ("grave-torture-urine",               "grave-torture-for-gossip-urine"),
    ("jews-expelled-medina-khaybar",      "expel-jews-arabia"),
    # TIRMIDHI (4)
    ("tirmidhi-cat-urine-food",           "tirmidhi-cat-pure-purity"),
    ("tirmidhi-men-saved-only-women-damned", "tirmidhi-most-women-ungrateful"),
    ("paradise-smell-40-years",           "tirmidhi-dhimmi-killed-hellfire-smell"),
    ("tirmidhi-victorious-through-terror","tirmidhi-muhammad-six-special-privileges"),
    # MUSLIM (3)
    ("adhan-satan-flee-distance-rauha",   "devil-farts-at-adhan"),
    ("bani-israel-eating-vermin",         "muslim-rat-milk-test"),
    ("muslim-prophet-kissed-black-stone-sunnah",
                                          "umar-kissed-the-black-stone-knowing-it-was-just-a-stone-e8396c69"),
    # ABU DAWUD (2)
    ("abu-dawud-shia-ali-emergence",      "twelve-caliphs-quraysh"),
    ("abu-dawud-salat-child-age-seven",   "beat-children-prayer-ten"),
    # NASAI (1)
    ("nasai-homosexual-execution-both",   "nasai-homosexual-execution"),
    # IBN MAJAH (4)
    ("ibnmajah-prophet-anus-forbidden-woman",  "ibnmajah-intercourse-anus-cursed"),
    ("ibnmajah-mahdi-from-family-appears",     "ibnmajah-mahdi-7-years-descendant"),
    ("ibnmajah-sodomy-kill-both-doer-done-to", "ibnmajah-kill-doer-done-to"),
    ("ibnmajah-seventy-three-sects-one-saved", "ibnmajah-seventy-three-sects"),
]

REMOVE_IDS = {drop for drop, _ in CONFIRMED_REMOVES}

SOURCE_MAP = {
    "bukhari.html":   "bukhari",
    "muslim.html":    "muslim",
    "abu-dawud.html": "abu-dawud",
    "tirmidhi.html":  "tirmidhi",
    "nasai.html":     "nasai",
    "ibn-majah.html": "ibn-majah",
}

# ---------------------------------------------------------------------------
# HTML div removal — bracket-counting to handle nested divs
# ---------------------------------------------------------------------------

ENTRY_OPEN = re.compile(
    r'<div\s+class=["\'][^"\']*\bentry\b[^"\']*["\'][^>]+id=["\']([^"\']+)["\'][^>]*>',
    re.DOTALL,
)
DIV_OPEN  = re.compile(r'<div\b',  re.IGNORECASE)
DIV_CLOSE = re.compile(r'</div\s*>', re.IGNORECASE)


def remove_entry_divs(html: str, target_ids: set) -> tuple[str, int]:
    """
    Remove all <div class="entry" id="TARGET_ID">…</div> blocks.
    Uses bracket-counting to handle arbitrary nesting depth.
    Returns (new_html, count_removed).
    """
    removed = 0
    out = []
    pos = 0

    while pos < len(html):
        m = ENTRY_OPEN.search(html, pos)
        if not m:
            out.append(html[pos:])
            break

        eid = m.group(1)
        if eid not in target_ids:
            # Not a target — advance one character past the start so we
            # don't re-match the same tag infinitely.
            out.append(html[pos:m.start() + 1])
            pos = m.start() + 1
            continue

        # Target found — emit everything before it, then consume the block.
        out.append(html[pos:m.start()])
        depth = 1
        scan = m.end()
        while scan < len(html) and depth > 0:
            o = DIV_OPEN.search(html, scan)
            c = DIV_CLOSE.search(html, scan)
            if not c:
                # Malformed HTML — consume to end of file
                scan = len(html)
                break
            if o and o.start() < c.start():
                depth += 1
                scan = o.end()
            else:
                depth -= 1
                scan = c.end()
        pos = scan
        removed += 1

    return "".join(out), removed


# ---------------------------------------------------------------------------
# Pass 1 — Remove divs from HTML files
# ---------------------------------------------------------------------------
print("Pass 1: Removing entry divs from HTML files")
total_html_removed = 0

for fname, source in SOURCE_MAP.items():
    path = CATALOG_DIR / fname
    html = path.read_text(encoding="utf-8", errors="ignore")

    new_html, count = remove_entry_divs(html, REMOVE_IDS)

    if count > 0:
        bak = path.with_name(fname.replace(".html", ".html.bak3"))
        shutil.copy(path, bak)
        path.write_text(new_html, encoding="utf-8")
        print(f"  {fname}: removed {count} entries  (backup: {bak.name})")
        total_html_removed += count
    else:
        # Count how many of REMOVE_IDS were expected in this source
        expected = sum(
            1 for drop, _ in CONFIRMED_REMOVES
            if drop in {m.group(1) for m in ENTRY_OPEN.finditer(html)}
        )
        print(f"  {fname}: 0 removed (none of the target IDs found here)")

print(f"\n  Total HTML entries removed: {total_html_removed}")
if total_html_removed != len(CONFIRMED_REMOVES):
    print(f"  WARNING: expected {len(CONFIRMED_REMOVES)}, got {total_html_removed}")
    print("  IDs not found in any HTML file:")
    # Find which ones were missed
    found = set()
    for fname in SOURCE_MAP:
        html = (CATALOG_DIR / fname).read_text(encoding="utf-8", errors="ignore")
        for m in ENTRY_OPEN.finditer(html):
            found.add(m.group(1))
    # Also check what we just wrote (re-read)
    for drop, _ in CONFIRMED_REMOVES:
        if drop not in found:
            # Check the backup files
            in_backup = False
            for fname in SOURCE_MAP:
                bak = CATALOG_DIR / fname.replace(".html", ".html.bak3")
                if bak.exists():
                    content = bak.read_text(encoding="utf-8", errors="ignore")
                    if drop in content:
                        in_backup = True
                        break
            status = "(was in backup — successfully removed)" if in_backup else "(NOT FOUND anywhere)"
            print(f"    {drop} {status}")

# ---------------------------------------------------------------------------
# Pass 2 — Rebuild catalog-entries.json
# ---------------------------------------------------------------------------
print("\nPass 2: Rebuilding catalog-entries.json")
shutil.copy(CATALOG_JSON, CATALOG_JSON.with_name("catalog-entries.backup3.json"))

with open(CATALOG_JSON, encoding="utf-8") as f:
    catalog = json.load(f)

original_count = len(catalog)
final = [e for e in catalog if e["id"] not in REMOVE_IDS]

with open(CATALOG_JSON, "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

by_source = defaultdict(int)
for e in final:
    by_source[e.get("source", "?")] += 1

print(f"\n  Original JSON count: {original_count}")
print(f"  Final JSON count:    {len(final)}")
print(f"  Removed from JSON:   {original_count - len(final)}")
print(f"\n  Breakdown by source:")
for s, c in sorted(by_source.items()):
    print(f"    {s}: {c}")

# ---------------------------------------------------------------------------
# Pass 3 — Verify HTML counts match JSON counts
# ---------------------------------------------------------------------------
print("\nPass 3: Verification — HTML entry counts vs JSON counts")
print(f"  {'Source':<14} {'HTML':>5}  {'JSON':>5}  Match")
all_ok = True
for fname, source in SOURCE_MAP.items():
    content = (CATALOG_DIR / fname).read_text(encoding="utf-8", errors="ignore")
    html_count = len(ENTRY_OPEN.findall(content))
    json_count = by_source.get(source, 0)
    ok = html_count == json_count
    if not ok:
        all_ok = False
    mark = "✓" if ok else "✗ MISMATCH"
    print(f"  {source:<14} {html_count:>5}  {json_count:>5}  {mark}")

if all_ok:
    print("\n  All counts match. Ready to commit.")
else:
    print("\n  MISMATCHES FOUND — investigate before committing.")
