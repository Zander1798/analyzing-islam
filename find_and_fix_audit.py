"""
Find-and-fix script for audit-identified citation errors.
For each known (file, old_href, new_href) triple, finds every entry block
that contains old_href and replaces it entry-specifically.
"""

import os, re

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT  = os.path.join(SITE, "catalog")
REPORT = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/audit_fix_report.txt"

SOURCE_NAME = {
    "bukhari": "Bukhari", "muslim": "Muslim", "abu-dawud": "Abu Dawud",
    "tirmidhi": "Tirmidhi", "ibn-majah": "Ibn Majah", "nasai": "Nasa'i",
}

ENTRY_RE = re.compile(r'<div[^>]+class="entry[^"]*"[^>]+id="([^"]+)"', re.I)

def find_and_fix(cat_file, old_src, old_anc, new_src, new_anc, entry_id_hint=None):
    """
    Find every entry in cat_file that contains old_href and replace with new_href.
    If entry_id_hint is given, only fix that specific entry.
    Returns list of result strings.
    """
    cat_path = os.path.join(CAT, cat_file)
    if not os.path.exists(cat_path):
        return [f"SKIP: {cat_file} not found"]

    with open(cat_path, encoding="utf-8") as f:
        html = f.read()

    old_href = f"../read/{old_src}.html#{old_anc}"
    new_href = f"../read/{new_src}.html#{new_anc}"
    new_display = f"{SOURCE_NAME.get(new_src, new_src.title())} #{new_anc[1:]}"

    if old_href not in html:
        return [f"SKIP: {old_src}#{old_anc} not found in {cat_file}"]

    starts = [(m.group(1), m.start()) for m in ENTRY_RE.finditer(html)]
    results = []
    modified = False

    for i, (eid, entry_start) in enumerate(starts):
        if entry_id_hint and eid != entry_id_hint:
            continue
        entry_end = starts[i+1][1] if i+1 < len(starts) else len(html)
        entry_block = html[entry_start:entry_end]

        if old_href not in entry_block:
            continue

        link_re = re.compile(
            rf'href="{re.escape(old_href)}"[^>]*>(.*?)</a>',
            re.IGNORECASE
        )
        new_block, count = link_re.subn(
            lambda m: f'href="{new_href}">{new_display}</a>',
            entry_block
        )
        if count > 0:
            html = html[:entry_start] + new_block + html[entry_end:]
            # Recalculate starts since html changed length
            starts = [(m.group(1), m.start()) for m in ENTRY_RE.finditer(html)]
            results.append(f"APPLIED: {eid} | {old_src}#{old_anc} -> {new_src}#{new_anc} ({count} replace)")
            modified = True

    if modified:
        with open(cat_path, "w", encoding="utf-8") as f:
            f.write(html)

    if not results:
        results.append(f"SKIP: {old_src}#{old_anc} found in {cat_file} but no entry block matched")
    return results


# ============================================================
# ALL STRUCTURAL ERRORS from check_all_citations_v3.py output
# (file, old_src, old_anc, new_src, new_anc)
# ============================================================
STRUCTURAL_FIXES = [
    # abu-dawud.html
    ("abu-dawud.html",  "abu-dawud", "h2086", "abu-dawud", "h2079"),
    ("abu-dawud.html",  "abu-dawud", "h4354", "abu-dawud", "h4350"),
    # Note: h4354 appears twice for different quotes — both get fixed to nearby correct anchor
    ("abu-dawud.html",  "bukhari",   "h5546", "bukhari",   "h5545"),

    # bukhari.html
    ("bukhari.html",    "bukhari",   "h26",   "bukhari",   "h43"),
    ("bukhari.html",    "bukhari",   "h4889", "bukhari",   "h4888"),

    # ibn-majah.html
    ("ibn-majah.html",  "ibn-majah", "h1122", "ibn-majah", "h1100"),
    ("ibn-majah.html",  "ibn-majah", "h1611", "ibn-majah", "h1610"),
    ("ibn-majah.html",  "ibn-majah", "h1637", "ibn-majah", "h1638"),
    ("ibn-majah.html",  "ibn-majah", "h2321", "ibn-majah", "h2322"),

    # muslim.html
    ("muslim.html",     "muslim",    "h298",  "muslim",    "h296"),
    ("muslim.html",     "muslim",    "h7154", "muslim",    "h7107"),
    ("muslim.html",     "muslim",    "h752",  "muslim",    "h736"),

    # tirmidhi.html
    ("tirmidhi.html",   "abu-dawud", "h4286", "abu-dawud", "h4283"),
    ("tirmidhi.html",   "bukhari",   "h5532", "bukhari",   "h5549"),
    ("tirmidhi.html",   "muslim",    "h4284", "muslim",    "h4286"),
    ("tirmidhi.html",   "muslim",    "h4417", "muslim",    "h4415"),
    ("tirmidhi.html",   "tirmidhi",  "h1241", "tirmidhi",  "h1277"),
    ("tirmidhi.html",   "tirmidhi",  "h1446", "tirmidhi",  "h1428"),
    ("tirmidhi.html",   "tirmidhi",  "h724",  "tirmidhi",  "h691"),
]

all_results = []

print("Applying structural fixes...")
for cat_file, old_src, old_anc, new_src, new_anc in STRUCTURAL_FIXES:
    results = find_and_fix(cat_file, old_src, old_anc, new_src, new_anc)
    for r in results:
        print(f"  {r}")
        all_results.append(r)

applied = [r for r in all_results if r.startswith("APPLIED")]
skipped = [r for r in all_results if r.startswith("SKIP")]

print(f"\nApplied: {len(applied)}, Skipped: {len(skipped)}")

with open(REPORT, "w", encoding="utf-8") as f:
    f.write(f"AUDIT FIX REPORT\n{'='*60}\n\n")
    f.write(f"=== APPLIED ({len(applied)}) ===\n")
    for l in applied: f.write(l + "\n")
    f.write(f"\n=== SKIPPED ({len(skipped)}) ===\n")
    for l in skipped: f.write(l + "\n")

print(f"Report: {REPORT}")
