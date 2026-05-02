"""
Entry-specific citation fixer.
Replaces href ONLY within the named entry's HTML block, preventing collateral damage.
"""

import os, re, html as html_mod

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT  = os.path.join(SITE, "catalog")
REPORT = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/apply_report6.txt"

SOURCE_NAME = {
    "bukhari": "Bukhari", "muslim": "Muslim", "abu-dawud": "Abu Dawud",
    "tirmidhi": "Tirmidhi", "ibn-majah": "Ibn Majah", "nasai": "Nasa'i",
}

ENTRY_RE = re.compile(r'<div[^>]+class="entry[^"]*"[^>]+id="([^"]+)"', re.I)

def fix_entry_citation(cat_file, entry_id, old_src, old_anc, new_src, new_anc):
    """Replace citation within a specific entry block only."""
    cat_path = os.path.join(CAT, cat_file)
    if not os.path.exists(cat_path):
        return f"SKIP: catalog not found: {cat_file}"

    with open(cat_path, encoding="utf-8") as f:
        html = f.read()

    # Find the entry by ID
    starts = [(m.group(1), m.start()) for m in ENTRY_RE.finditer(html)]
    entry_start = None
    entry_end = None
    for i, (eid, start) in enumerate(starts):
        if eid == entry_id:
            entry_start = start
            entry_end = starts[i+1][1] if i+1 < len(starts) else len(html)
            break

    if entry_start is None:
        return f"SKIP: entry '{entry_id}' not found in {cat_file}"

    old_href = f"../read/{old_src}.html#{old_anc}"
    new_href = f"../read/{new_src}.html#{new_anc}"
    new_display = f"{SOURCE_NAME.get(new_src, new_src.title())} #{new_anc[1:]}"

    entry_block = html[entry_start:entry_end]

    if old_href not in entry_block:
        return f"SKIP: old href not in entry block ({old_src}#{old_anc})"

    link_re = re.compile(
        rf'href="{re.escape(old_href)}"[^>]*>(.*?)</a>',
        re.IGNORECASE
    )
    new_block, count = link_re.subn(
        lambda m: f'href="{new_href}">{new_display}</a>',
        entry_block
    )

    if count == 0:
        return f"SKIP: link pattern not found in entry block"

    new_html = html[:entry_start] + new_block + html[entry_end:]

    with open(cat_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    return f"APPLIED: {old_src}#{old_anc} -> {new_src}#{new_anc} ({count} replacement(s))"


# Targeted fixes: (cat_file, entry_id, old_src, old_anc, new_src, new_anc)
FIXES = [
    # Contamination fixes (global replace damaged these)
    ("abu-dawud.html",  "abu-dawud-black-magic-ruling",      "muslim",    "h29",    "bukhari",   "h6538"),
    ("muslim.html",     "adam-friday-best",                   "muslim",    "h1376",  "muslim",    "h1868"),
    ("tirmidhi.html",   "tirmidhi-fasting-mouth-stink",       "tirmidhi",  "h765",   "tirmidhi",  "h2945"),
    ("tirmidhi.html",   "tirmidhi-drinking-blood",            "tirmidhi",  "h22",    "tirmidhi",  "h2042"),
    ("tirmidhi.html",   "tirmidhi-sex-camel-goat",            "bukhari",   "h1119",  "ibn-majah", "h2300"),
    ("tirmidhi.html",   "tirmidhi-killing-children-conqueror-allowed", "bukhari", "h1335", "muslim", "h4417"),
    ("tirmidhi.html",   "tirmidhi-miswak-with-every-wudu",   "tirmidhi",  "h22",    "ibn-majah", "h23"),
    ("tirmidhi.html",   "tirmidhi-prohibition-silver-gold-vessels", "tirmidhi", "h765", "muslim", "h5249"),
    ("muslim.html",     "muslim-paradise-lowest-ten-worlds",  "muslim",    "h4787",  "muslim",    "h293"),
    # New correct anchors found
    ("ibn-majah.html",  "ibnmajah-gossip-no-paradise",        "ibn-majah", "h3974",  "ibn-majah", "h81"),
    ("tirmidhi.html",   "best-sadaqa-give-family",            "tirmidhi",  "h1663",  "ibn-majah", "h2535"),
    ("nasai.html",      "nasai-khawarij-dogs-of-hellfire",    "abu-dawud", "h4769",  "bukhari",   "h1174"),
    ("tirmidhi.html",   "tirmidhi-angel-prayer-rejected-drink","tirmidhi", "h1862",  "bukhari",   "h5362"),
    ("tirmidhi.html",   "tirmidhi-wind-speak",                "tirmidhi",  "h2252",  "abu-dawud", "h5097"),
    ("nasai.html",      "nasai-no-first-greeting-ahl-kitab",  "muslim",    "h1667",  "muslim",    "h5515"),
]

applied, skipped = [], []

for cat_file, entry_id, old_src, old_anc, new_src, new_anc in FIXES:
    result = fix_entry_citation(cat_file, entry_id, old_src, old_anc, new_src, new_anc)
    if result.startswith("APPLIED"):
        applied.append(f"  {entry_id}: {result}")
        print(f"APPLIED: {entry_id}")
    else:
        skipped.append(f"  {entry_id}: {result}")
        print(f"SKIP: {entry_id}: {result}")

print(f"\nApplied: {len(applied)}, Skipped: {len(skipped)}")

with open(REPORT, "w", encoding="utf-8") as f:
    f.write(f"PASS 6 REPORT (entry-specific)\n{'='*60}\n\n")
    f.write(f"=== APPLIED ({len(applied)}) ===\n")
    for l in applied: f.write(l + "\n")
    f.write(f"\n=== SKIPPED ({len(skipped)}) ===\n")
    for l in skipped: f.write(l + "\n")
print("Done.")
