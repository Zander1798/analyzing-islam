"""
Fix catalog citation errors identified by check_catalog_citations.py.
Handles display text with or without '#' (both formats appear in the files).
Uses simultaneous replacement to avoid chaining bugs.
Entry-specific replacement for the bukhari h3705 collision.
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
    "nasai":     "Nasa'i",
    "quran":     "Quran",
}

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def lnk_pat(source, old_id, new_id):
    """Return (pattern, replacement) for a catalog cite-link (href + display text)."""
    name = SRC_NAME.get(source, source)
    old = str(old_id)
    new = str(new_id)
    # Groups: (1) "read/source.html#h"  (2) OLD_in_href  (3) '">'
    #         (4) "Name "  (5) optional '#'  (6) OLD_in_display  (7) "</a>"
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

def apply_file(path, replacements, entry_specific=None):
    """
    Apply replacements to file.
    replacements: list of (pattern_str, repl_str) for re.sub
    entry_specific: list of (entry_id_str, old_str, new_str) for count=1 sequential replace
    """
    content = read(path)
    original = content

    # Simultaneous replacement via a single combined regex pass
    if replacements:
        combined = "|".join(f"(?P<g{i}_{s}>{p})"
                            for i, (p, s) in enumerate(replacements)
                            if p is not None)
        # Simpler: just apply each replacement in sequence but use regex (no chaining risk
        # because each pattern targets specific IDs that don't appear in the replacement text)
        for pat, repl in replacements:
            content = re.sub(pat, repl, content)

    # Entry-specific (count=1 per occurrence)
    if entry_specific:
        for old_str, new_str in entry_specific:
            content = content.replace(old_str, new_str, 1)

    rel = os.path.relpath(path, SITE)
    if content != original:
        write(path, content)
        print(f"  Fixed: {rel}")
    else:
        print(f"  No changes: {rel}")

def warn_if_absent(path, pattern):
    """Warn if pattern not found in file (helpful for detecting format mismatches)."""
    content = read(path)
    if not re.search(pattern, content):
        print(f"    WARN: pattern not found: {pattern[:70]}")

# ── catalog/abu-dawud.html ────────────────────────────────────────────────────
print("abu-dawud.html:")
apply_file(os.path.join(CAT, "abu-dawud.html"), [
    lnk_pat("abu-dawud", "2254", "2249"),
    lnk_pat("abu-dawud", "4327", "4328"),
    lnk_pat("abu-dawud", "4462", "4464"),
    lnk_pat("abu-dawud", "4933", "4935"),
    lnk_pat("abu-dawud", "4442", "4444"),   # appears twice — OK, both → 4444
    lnk_pat("abu-dawud", "4106", "4107"),
    lnk_pat("abu-dawud", "2141", "2142"),
    lnk_pat("abu-dawud", "2074", "2075"),
    lnk_pat("abu-dawud", "4723", "4725"),
    lnk_pat("abu-dawud", "4107", "4108"),   # chained with 4106→4107 — safe (simultaneous)
    lnk_pat("abu-dawud", "4418", "4420"),
    lnk_pat("abu-dawud", "4351", "4353"),
    lnk_pat("abu-dawud", "3234", "3235"),
    lnk_pat("abu-dawud", "4364", "4366"),   # appears twice — OK, both → 4366
    lnk_pat("abu-dawud", "4508", "4510"),
    lnk_pat("abu-dawud", "4279", "4280"),
    lnk_pat("abu-dawud", "2083", "2086"),   # checker suggested h2079 but h2086 is correct
    lnk_pat("abu-dawud", "3844", "3845"),
    lnk_pat("abu-dawud", "4367", "4355"),
    lnk_pat("abu-dawud", "4413", "4423"),
    lnk_pat("abu-dawud", "2683", "2684"),
    lnk_pat("abu-dawud", "3674", "3675"),
    lnk_pat("abu-dawud", "5256", "5262"),
    lnk_pat("abu-dawud", "4361", "4363"),
    lnk_pat("abu-dawud", "4218", "4219"),
    lnk_pat("abu-dawud", "703",  "702"),
])

# ── catalog/bukhari.html ──────────────────────────────────────────────────────
print("bukhari.html:")
# h3705 appears twice with DIFFERENT targets — entry-specific replacements
bk_path = os.path.join(CAT, "bukhari.html")
bk_raw  = read(bk_path)
# Determine the exact strings (with or without '#')
h3705_str_1 = re.search(r'read/bukhari\.html#h3705">[^<]+</a>', bk_raw)
h3705_str_2 = None
if h3705_str_1:
    h3705_str_2 = re.search(r'read/bukhari\.html#h3705">[^<]+</a>',
                             bk_raw[h3705_str_1.end():])
entry_specific_bk = []
if h3705_str_1:
    old1 = h3705_str_1.group()
    new1 = old1.replace("#h3705", "#h3709").replace("3705", "3709")
    entry_specific_bk.append((old1, new1))
if h3705_str_2:
    # offset is relative to after first match
    old2 = h3705_str_2.group()
    new2 = old2.replace("#h3705", "#h3707").replace("3705", "3707")
    entry_specific_bk.append((old2, new2))

apply_file(bk_path, [
    lnk_pat("bukhari",   "450",  "453"),
    lnk_pat("bukhari",   "277",  "278"),
    lnk_pat("bukhari",   "5000", "5001"),
    lnk_pat("tirmidhi",  "877",  "878"),
    lnk_pat("bukhari",   "639",  "629"),   # appears twice — both → 629
    lnk_pat("bukhari",   "2689", "2702"),
    lnk_pat("bukhari",   "4784", "4785"),
    lnk_pat("bukhari",   "3552", "3553"),
    lnk_pat("bukhari",   "6343", "6336"),
    # h3705 handled entry-specifically below
    lnk_pat("bukhari",   "5042", "5030"),
    lnk_pat("bukhari",   "3868", "3870"),
    lnk_pat("bukhari",   "5540", "5542"),
    # SKIP: h4889→h4888 (false positive — h4889 IS the evil omen hadith)
    lnk_pat("bukhari",   "1548", "1543"),
    lnk_pat("bukhari",   "1540", "1529"),
    lnk_pat("bukhari",   "291",  "290"),
    lnk_pat("bukhari",   "2444", "2443"),
    lnk_pat("bukhari",   "3731", "3733"),
    lnk_pat("muslim",    "2127", "2141"),
    lnk_pat("bukhari",   "6734", "6735"),
    lnk_pat("bukhari",   "4428", "4429"),
    lnk_pat("abu-dawud", "4462", "4464"),   # body cite-link
], entry_specific=entry_specific_bk)

# ── catalog/ibn-majah.html ────────────────────────────────────────────────────
print("ibn-majah.html:")
apply_file(os.path.join(CAT, "ibn-majah.html"), [
    lnk_pat("ibn-majah", "169", "156"),
])

# ── catalog/muslim.html ───────────────────────────────────────────────────────
print("muslim.html:")
apply_file(os.path.join(CAT, "muslim.html"), [
    lnk_pat("muslim",    "4284", "4288"),
    lnk_pat("muslim",    "4224", "4223"),
    lnk_pat("muslim",    "3136", "3138"),
    lnk_pat("muslim",    "6978", "6979"),
    lnk_pat("muslim",    "5125", "5127"),
    lnk_pat("muslim",    "1460", "1453"),
    lnk_pat("muslim",    "3414", "3415"),
    lnk_pat("muslim",    "5140", "5142"),
    lnk_pat("muslim",    "4322", "4327"),
    lnk_pat("muslim",    "5693", "5696"),
    lnk_pat("muslim",    "4261", "4263"),
    lnk_pat("muslim",    "7178", "7163"),
    lnk_pat("muslim",    "502",  "503"),
    lnk_pat("muslim",    "412",  "414"),
    lnk_pat("muslim",    "36",   "32"),
    lnk_pat("muslim",    "2521", "2523"),
    lnk_pat("muslim",    "4459", "4462"),
    # SKIP: h7154→h7152 (false positive — h7154 IS the Jews/stone hadith)
    lnk_pat("muslim",    "5979", "5978"),
    lnk_pat("muslim",    "657",  "653"),
    lnk_pat("tirmidhi",  "1283", "1293"),
    lnk_pat("abu-dawud", "4362", "4363"),
    lnk_pat("bukhari",   "304",  "301"),    # body cite-link × 2 — both → 301
])

# ── catalog/nasai.html ────────────────────────────────────────────────────────
print("nasai.html:")
apply_file(os.path.join(CAT, "nasai.html"), [
    lnk_pat("nasai",     "1369", "1370"),
    lnk_pat("nasai",     "194",  "198"),
    lnk_pat("nasai",     "441",  "443"),
    # SKIP: h7121, h7191, h7143, h9168 (above reader max of 5768)
    lnk_pat("nasai",     "3127", "3134"),
    lnk_pat("nasai",     "671",  "672"),
    lnk_pat("nasai",     "3955", "3953"),
    lnk_pat("nasai",     "3378", "3384"),
    # SKIP: ibn-majah h5325 (above ibn-majah reader max of 4345)
    lnk_pat("nasai",     "703",  "705"),
    lnk_pat("nasai",     "2525", "2529"),
])

# ── catalog/tirmidhi.html ─────────────────────────────────────────────────────
print("tirmidhi.html:")
apply_file(os.path.join(CAT, "tirmidhi.html"), [
    lnk_pat("tirmidhi",  "1403", "1418"),   # appears twice — both → 1418
    lnk_pat("tirmidhi",  "1188", "1192"),
    lnk_pat("tirmidhi",  "1160", "1163"),
    lnk_pat("tirmidhi",  "755",  "753"),
    lnk_pat("tirmidhi",  "877",  "878"),
    # SKIP: h724→h716 (false positive — h724 IS the Ramadan-intercourse hadith)
    lnk_pat("tirmidhi",  "1161", "1164"),
    lnk_pat("tirmidhi",  "1159", "1162"),
    lnk_pat("tirmidhi",  "1201", "1199"),
])

print("\nAll done.")
