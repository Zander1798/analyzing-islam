"""
Catalog citation fixes v3: ~70 wrong hadith IDs revealed by ±50 search window,
plus Quran anchor fixes in catalog/quran.html.

Skipped (confirmed false positives from previous sessions):
  abu-dawud h2086, bukhari h4889, tirmidhi h724, muslim h7154, bukhari h26
Skipped (above Nasai/Ibn Majah reader max):
  nasai h7121, h7191, h7143, h9168, h5913; ibn-majah h5325
"""

import os, re

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT  = os.path.join(SITE, "catalog")

SRC_NAME = {
    "abu-dawud": "Abu Dawud",
    "bukhari":   "Bukhari",
    "muslim":    "Muslim",
    "tirmidhi":  "Tirmidhi",
    "ibn-majah": "Ibn Majah",
    "nasai":     "Nasai",   # catalog uses "Nasai" (no apostrophe)
}

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def lnk_pat(source, old_id, new_id):
    """Regex pattern+replacement for a catalog cite-link (href AND display text)."""
    name = SRC_NAME.get(source, source)
    old = str(old_id)
    new = str(new_id)
    pat = (
        rf'(read/{re.escape(source)}\.html#h)'
        rf'({old})'
        rf'(">)'
        rf'({re.escape(name)} )'
        rf'(#?)'
        rf'({old})'
        rf'(</a>)'
    )
    repl = rf'\g<1>{new}\g<3>\g<4>\g<5>{new}\g<7>'
    return pat, repl

def fix_entry_pat(content, entry_id, pat, repl):
    """Apply regex pat→repl only within the named entry block."""
    entry_start = content.find(f'id="{entry_id}"')
    if entry_start < 0:
        print(f"    WARN: entry '{entry_id}' not found")
        return content
    rest = content[entry_start:]
    next_entry = re.search(r'<div\s+class="entry[\s">]', rest[100:])
    entry_end = entry_start + 100 + (next_entry.start() if next_entry else len(rest))
    entry_block = content[entry_start:entry_end]
    new_block = re.sub(pat, repl, entry_block)
    if new_block == entry_block:
        print(f"    WARN: pattern not found in entry '{entry_id}'")
    return content[:entry_start] + new_block + content[entry_end:]

def apply(path, global_pats=None, entry_pats=None, literal_fixes=None):
    content = read(path)
    original = content
    for pat, repl in (global_pats or []):
        content = re.sub(pat, repl, content)
    for entry_id, pat, repl in (entry_pats or []):
        content = fix_entry_pat(content, entry_id, pat, repl)
    for old, new in (literal_fixes or []):
        if old not in content:
            print(f"    WARN (literal): not found: {repr(old[:70])}")
        else:
            content = content.replace(old, new)
    rel = os.path.relpath(path, SITE)
    if content != original:
        write(path, content)
        print(f"  Fixed: {rel}")
    else:
        print(f"  No changes: {rel}")

# ── catalog/abu-dawud.html ────────────────────────────────────────────────────
print("abu-dawud.html:")
apply(
    os.path.join(CAT, "abu-dawud.html"),
    global_pats=[
        lnk_pat("abu-dawud", "1042", "997"),
        lnk_pat("abu-dawud", "2072", "2111"),
        # h2086 → SKIP (confirmed false positive: h2086 IS the no-guardian hadith)
    ],
)

# ── catalog/bukhari.html ──────────────────────────────────────────────────────
print("bukhari.html:")
apply(
    os.path.join(CAT, "bukhari.html"),
    global_pats=[
        lnk_pat("bukhari",  "1117", "1115"),
        lnk_pat("bukhari",  "1250", "1246"),
        lnk_pat("bukhari",  "1585", "1543"),
        lnk_pat("bukhari",  "1881", "1882"),
        lnk_pat("bukhari",  "2078", "2080"),
        lnk_pat("bukhari",  "2749", "2717"),
        lnk_pat("bukhari",  "3063", "3062"),
        lnk_pat("bukhari",  "3291", "3293"),
        lnk_pat("bukhari",  "5471", "5505"),
        lnk_pat("bukhari",  "5604", "5638"),
        lnk_pat("bukhari",  "5732", "5721"),
        lnk_pat("bukhari",  "6588", "6569"),
        lnk_pat("ibn-majah","3486", "3534"),
        lnk_pat("tirmidhi", "1159", "1162"),
        lnk_pat("tirmidhi", "1456", "1478"),
        # h4889 → SKIP (confirmed false positive)
        # h26   → SKIP (entry explicitly compares h26 vs h43 as distinct hadiths)
    ],
)

# ── catalog/ibn-majah.html ────────────────────────────────────────────────────
print("ibn-majah.html:")
apply(
    os.path.join(CAT, "ibn-majah.html"),
    global_pats=[
        lnk_pat("ibn-majah", "1625", "1654"),
        lnk_pat("ibn-majah", "2051", "2016"),
        # h2151 appears in TWO entries with DIFFERENT targets → entry-specific below
        lnk_pat("ibn-majah", "3776", "3820"),
        lnk_pat("ibn-majah", "3786", "3820"),
        lnk_pat("ibn-majah", "4068", "4088"),
        lnk_pat("ibn-majah", "4311", "4262"),
        lnk_pat("ibn-majah", "4324", "4341"),
    ],
    entry_pats=[
        # "The makers of images will be punished..." → h2107
        ("ibnmajah-cursed-pictures",
         *lnk_pat("ibn-majah", "2151", "2107")),
        # "The makers of these pictures will be punished... bring to life..." → h2176
        ("ibnmajah-prophet-cursed-paint-artist",
         *lnk_pat("ibn-majah", "2151", "2176")),
    ],
)

# ── catalog/muslim.html ───────────────────────────────────────────────────────
print("muslim.html:")
apply(
    os.path.join(CAT, "muslim.html"),
    global_pats=[
        lnk_pat("abu-dawud", "2162", "2163"),
        lnk_pat("muslim",    "576",  "584"),
        lnk_pat("muslim",    "768",  "757"),   # two entries, both → h757
        lnk_pat("muslim",    "1090", "1064"),
        lnk_pat("muslim",    "1416", "1376"),
        lnk_pat("muslim",    "1726", "1711"),
        lnk_pat("muslim",    "1794", "1791"),
        lnk_pat("muslim",    "1798", "1791"),
        lnk_pat("muslim",    "1954", "1979"),
        lnk_pat("muslim",    "1967", "1968"),
        lnk_pat("muslim",    "2041", "2032"),
        lnk_pat("muslim",    "4777", "4750"),
        lnk_pat("muslim",    "5533", "5531"),
        lnk_pat("muslim",    "5649", "5640"),
        lnk_pat("muslim",    "5912", "5932"),
        lnk_pat("muslim",    "6198", "6187"),
        lnk_pat("muslim",    "6344", "6341"),
        lnk_pat("muslim",    "7127", "7126"),
        lnk_pat("muslim",    "7205", "7202"),
        lnk_pat("tirmidhi",  "1456", "1478"),
        # h7154 → SKIP (confirmed false positive)
    ],
)

# ── catalog/nasai.html ────────────────────────────────────────────────────────
print("nasai.html:")
apply(
    os.path.join(CAT, "nasai.html"),
    global_pats=[
        lnk_pat("nasai",     "99",   "68"),
        lnk_pat("nasai",     "184",  "172"),
        lnk_pat("nasai",     "202",  "216"),
        lnk_pat("nasai",     "295",  "285"),
        # h24 appears in THREE entries with DIFFERENT targets → entry-specific below
        lnk_pat("nasai",     "817",  "822"),
        lnk_pat("nasai",     "935",  "939"),
        lnk_pat("nasai",     "1493", "1498"),
        lnk_pat("nasai",     "2215", "2216"),
        lnk_pat("nasai",     "3362", "3396"),
        lnk_pat("nasai",     "4337", "4342"),
        lnk_pat("ibn-majah", "4068", "4088"),
        # h5913, h7121, h7191, h7143, h9168, ibn-majah h5325 → SKIP (above reader max)
    ],
    entry_pats=[
        # "The Prophet urinated while standing up" → h18
        ("nasai-urine-standing",
         *lnk_pat("nasai", "24", "18")),
        # "None of you should touch his penis with right hand while urinating" → h25
        ("nasai-right-hand-private-parts",
         *lnk_pat("nasai", "24", "25")),
        # Third entry (elaboration of right-hand topic) → h25
        ("nasai-urine-left-hand-not-right",
         *lnk_pat("nasai", "24", "25")),
    ],
)

# ── catalog/tirmidhi.html ─────────────────────────────────────────────────────
print("tirmidhi.html:")
apply(
    os.path.join(CAT, "tirmidhi.html"),
    global_pats=[
        lnk_pat("tirmidhi", "1435", "1455"),
        lnk_pat("tirmidhi", "1456", "1478"),
        lnk_pat("tirmidhi", "1522", "1555"),
        lnk_pat("tirmidhi", "1553", "1590"),
        lnk_pat("tirmidhi", "1610", "1656"),
        lnk_pat("tirmidhi", "2562", "2608"),
        lnk_pat("tirmidhi", "3963", "3934"),
        # h724 → SKIP (confirmed false positive)
    ],
)

# ── catalog/quran.html: range-start and misuse fixes ─────────────────────────
print("quran.html (range starts + misused anchors):")
apply(
    os.path.join(CAT, "quran.html"),
    literal_fixes=[
        # Range anchors should point to the START verse of the cited range
        ('href="../read/quran.html#s2v144"',  'href="../read/quran.html#s2v142"'),
        ('href="../read/quran.html#s38v33"',  'href="../read/quran.html#s38v31"'),
        ('href="../read/quran.html#s69v32"',  'href="../read/quran.html#s69v30"'),
        ('href="../read/quran.html#s89v7"',   'href="../read/quran.html#s89v6"'),
        # s1v26 is a Bible citation (Luke 1:26–35), not a Quran verse — remove link
        ('<a class="cite-link" href="../read/quran.html#s1v26">1:26–35</a>',
         '1:26–35'),
    ],
)

print("\nAll done.")
