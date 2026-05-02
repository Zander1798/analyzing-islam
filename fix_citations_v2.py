"""
Comprehensive citation fixes: 30 confirmed wrong hadith IDs across 26 dossier files.
Each replacement is targeted to exact href+text patterns to avoid collateral changes.
"""

import os

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def apply(path, replacements):
    content = read(path)
    original = content
    for old, new in replacements:
        if old not in content:
            rel = os.path.relpath(path, SITE)
            print(f"  WARN: not found in {rel}: {repr(old[:80])}")
            continue
        count = content.count(old)
        content = content.replace(old, new)
    if content != original:
        write(path, content)
        print(f"  Fixed: {os.path.relpath(path, SITE)}")
    else:
        print(f"  No changes: {os.path.relpath(path, SITE)}")

def p(source, old, new):
    """Build both href-anchor and bare-number replacement pairs for a cite-link."""
    return [
        (f'read/{source}.html#h{old}">{source.replace("-"," ").title().replace(" ","_").replace("_"," ")} {old}</a>',
         f'read/{source}.html#h{new}">{source.replace("-"," ").title().replace(" ","_").replace("_"," ")} {new}</a>'),
    ]

A = os.path.join(SITE, "arguments")

# Helper: build a replacement pair for a full cite-link
def lnk(source, old_id, new_id, label_old=None, label_new=None):
    """
    Returns (old_str, new_str) for the cite-link anchor.
    label_old/label_new override the display text (default: "Source NNN").
    """
    src_map = {
        "abu-dawud": "Abu Dawud",
        "bukhari":   "Bukhari",
        "muslim":    "Muslim",
        "tirmidhi":  "Tirmidhi",
        "ibn-majah": "Ibn Majah",
        "nasai":     "Nasa'i",
        "quran":     "Quran",
    }
    name = src_map.get(source, source)
    lo = label_old if label_old is not None else f"{name} {old_id}"
    ln = label_new if label_new is not None else f"{name} {new_id}"
    old = f'read/{source}.html#h{old_id}">{lo}</a>'
    new = f'read/{source}.html#h{new_id}">{ln}</a>'
    return (old, new)

def bare(source, old_id, new_id):
    """Returns (old_str, new_str) for a bare-number cite-link like ">2150</a>"."""
    old = f'read/{source}.html#h{old_id}">{old_id}</a>'
    new = f'read/{source}.html#h{new_id}">{new_id}</a>'
    return (old, new)

# ── d01: abu-dawud h2150 → h2158 ─────────────────────────────────────────────
print("d01:")
apply(os.path.join(A, "abu-dawud/d01-awtas-captives-iddah.html"), [
    lnk("abu-dawud", "2150", "2158"),
    bare("abu-dawud", "2150", "2158"),
])

# ── d03: abu-dawud h4361 → h4363 ─────────────────────────────────────────────
print("d03:")
apply(os.path.join(A, "abu-dawud/d03-blind-man-umm-walad.html"), [
    lnk("abu-dawud", "4361", "4363"),
    bare("abu-dawud", "4361", "4363"),
])

# ── d06: abu-dawud h2128 → h2122 ─────────────────────────────────────────────
print("d06:")
apply(os.path.join(A, "abu-dawud/d06-prepubescent-marriage-normalised.html"), [
    lnk("abu-dawud", "2128", "2122"),
    bare("abu-dawud", "2128", "2122"),
])

# ── d08: abu-dawud h4607 → h4609 ─────────────────────────────────────────────
print("d08:")
apply(os.path.join(A, "abu-dawud/d08-bidaa-misguidance.html"), [
    lnk("abu-dawud", "4607", "4609"),
    bare("abu-dawud", "4607", "4609"),
])

# ── d12: abu-dawud h4344 → h1141 ─────────────────────────────────────────────
print("d12:")
apply(os.path.join(A, "abu-dawud/d12-vigilantism-warrant.html"), [
    lnk("abu-dawud", "4344", "1141"),
    bare("abu-dawud", "4344", "1141"),
])

# ── d14: abu-dawud h1144 → h1179 ─────────────────────────────────────────────
print("d14:")
apply(os.path.join(A, "abu-dawud/d14-eclipses-deaths.html"), [
    lnk("abu-dawud", "1144", "1179"),
    bare("abu-dawud", "1144", "1179"),
])

# ── d15: tirmidhi h1102 → h1104 ──────────────────────────────────────────────
print("d15:")
apply(os.path.join(A, "abu-dawud/d15-no-marriage-without-wali.html"), [
    lnk("tirmidhi", "1102", "1104"),
    bare("tirmidhi", "1102", "1104"),
])

# ── d17: bukhari h1463 → h1451 ───────────────────────────────────────────────
print("d17:")
apply(os.path.join(A, "abu-dawud/d17-zakat-on-slaves.html"), [
    lnk("bukhari", "1463", "1451"),
    bare("bukhari", "1463", "1451"),
])

# ── d18: abu-dawud h4587 → h4544 ─────────────────────────────────────────────
print("d18:")
apply(os.path.join(A, "abu-dawud/d18-diyya-by-religion.html"), [
    lnk("abu-dawud", "4587", "4544"),
    bare("abu-dawud", "4587", "4544"),
])

# ── b03: bukhari h6829 → h6580 AND h6830 → h6580 ─────────────────────────────
print("b03:")
apply(os.path.join(A, "bukhari/b03-stoning-verse-lost.html"), [
    lnk("bukhari", "6829", "6580"),
    bare("bukhari", "6829", "6580"),
    lnk("bukhari", "6830", "6580"),
    bare("bukhari", "6830", "6580"),
])

# ── b04: bukhari h304 → h301 ─────────────────────────────────────────────────
print("b04:")
apply(os.path.join(A, "bukhari/b04-fitna-women.html"), [
    lnk("bukhari", "304", "301"),
    bare("bukhari", "304", "301"),
])

# ── b05: bukhari h304 → h301 ─────────────────────────────────────────────────
print("b05:")
apply(os.path.join(A, "bukhari/b05-women-deficient.html"), [
    lnk("bukhari", "304", "301"),
    bare("bukhari", "304", "301"),
])

# ── b06: bukhari h3199 → h3066 AND h7424 → h7141 ─────────────────────────────
print("b06:")
apply(os.path.join(A, "bukhari/b06-sun-prostrates.html"), [
    lnk("bukhari", "3199", "3066"),
    bare("bukhari", "3199", "3066"),
    lnk("bukhari", "7424", "7141"),
    bare("bukhari", "7424", "7141"),
])

# ── b08: bukhari h4119 → h2918 ───────────────────────────────────────────────
print("b08:")
apply(os.path.join(A, "bukhari/b08-banu-qurayza.html"), [
    lnk("bukhari", "4119", "2918"),
    bare("bukhari", "4119", "2918"),
])

# ── b09: bukhari h5158 → h4881 ───────────────────────────────────────────────
print("b09:")
apply(os.path.join(A, "bukhari/b09-safiyya-khaybar.html"), [
    lnk("bukhari", "5158", "4881"),
    bare("bukhari", "5158", "4881"),
])

# ── b12: bukhari h6878 → h6623 AND tirmidhi h1402 → h1417 ───────────────────
print("b12:")
apply(os.path.join(A, "bukhari/b12-three-lawful-kills.html"), [
    lnk("bukhari", "6878", "6623"),
    bare("bukhari", "6878", "6623"),
    lnk("tirmidhi", "1402", "1417"),
    bare("tirmidhi", "1402", "1417"),
])

# ── b13: bukhari h7517 → h268 ────────────────────────────────────────────────
print("b13:")
apply(os.path.join(A, "bukhari/b13-strength-thirty-men.html"), [
    lnk("bukhari", "7517", "268"),
    bare("bukhari", "7517", "268"),
])

# ── i02: ibn-majah h1942 → h1677 ─────────────────────────────────────────────
print("i02:")
apply(os.path.join(A, "ibn-majah/i02-sahla-salim-breastfeeding.html"), [
    lnk("ibn-majah", "1942", "1677"),
    bare("ibn-majah", "1942", "1677"),
])

# ── i03: tirmidhi h1159 → h1162 ──────────────────────────────────────────────
print("i03:")
apply(os.path.join(A, "ibn-majah/i03-wife-prostration-husband.html"), [
    lnk("tirmidhi", "1159", "1162"),
    bare("tirmidhi", "1159", "1162"),
])

# ── m06: muslim h1731 → h4390 ────────────────────────────────────────────────
print("m06:")
apply(os.path.join(A, "muslim/m06-three-options-non-muslims.html"), [
    lnk("muslim", "1731", "4390"),
    bare("muslim", "1731", "4390"),
])

# ── m16: bukhari h7510 → h7154 ───────────────────────────────────────────────
print("m16:")
apply(os.path.join(A, "muslim/m16-hell-emptied-of-believers.html"), [
    lnk("bukhari", "7510", "7154"),
    bare("bukhari", "7510", "7154"),
])

# ── m19: bukhari h7437 → h7154 ───────────────────────────────────────────────
print("m19:")
apply(os.path.join(A, "muslim/m19-allah-two-forms.html"), [
    lnk("bukhari", "7437", "7154"),
    bare("bukhari", "7437", "7154"),
])

# ── q15: bukhari h7420 → h7137 ───────────────────────────────────────────────
print("q15:")
apply(os.path.join(A, "quran/q15-zayd-zaynab-marriage.html"), [
    lnk("bukhari", "7420", "7137"),
    bare("bukhari", "7420", "7137"),
])

# ── t06: bukhari h5950 → h5722 ───────────────────────────────────────────────
print("t06:")
apply(os.path.join(A, "tirmidhi/t06-angels-houses-images.html"), [
    lnk("bukhari", "5950", "5722"),
    bare("bukhari", "5950", "5722"),
])

# ── t12: abu-dawud h4282 → h4283 ─────────────────────────────────────────────
print("t12:")
apply(os.path.join(A, "tirmidhi/t12-mahdi-eschatology.html"), [
    lnk("abu-dawud", "4282", "4283"),
    bare("abu-dawud", "4282", "4283"),
])

# ── t16: tirmidhi h2003 → h1667 ──────────────────────────────────────────────
print("t16:")
apply(os.path.join(A, "tirmidhi/t16-jihad-supreme-deed.html"), [
    lnk("tirmidhi", "2003", "1667"),
    bare("tirmidhi", "2003", "1667"),
])

# ── t19: bukhari h3208 → h3194 ───────────────────────────────────────────────
print("t19:")
apply(os.path.join(A, "tirmidhi/t19-predestination-effort-futile.html"), [
    lnk("bukhari", "3208", "3194"),
    bare("bukhari", "3208", "3194"),
])

print("\nAll done.")
