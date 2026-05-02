"""
Dossier citation fixes v3: 28 wrong hadith IDs across dossier files,
plus Quran anchor misuse fixes in q09 and q19.

Sources of errors:
 - Wider ±50 window revealed new errors the ±15 checker missed
 - Chaining: previous fixes landed on IDs that are also wrong
   (d18: h4587→h4544 now h4544→h4505; b09: h5158→h4881 now h4881→h4914;
    i02: h1942→h1677 now h1677→h1666)
"""

import os

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
A    = os.path.join(SITE, "arguments")

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
            print(f"  WARN: not found in {os.path.relpath(path, SITE)}: {repr(old[:80])}")
            continue
        content = content.replace(old, new)
    if content != original:
        write(path, content)
        print(f"  Fixed: {os.path.relpath(path, SITE)}")
    else:
        print(f"  No changes: {os.path.relpath(path, SITE)}")

SRC = {
    "abu-dawud": "Abu Dawud",
    "bukhari":   "Bukhari",
    "muslim":    "Muslim",
    "tirmidhi":  "Tirmidhi",
    "ibn-majah": "Ibn Majah",
    "nasai":     "Nasa'i",
}

def lnk(source, old_id, new_id):
    name = SRC.get(source, source)
    old = f'read/{source}.html#h{old_id}">{name} {old_id}</a>'
    new = f'read/{source}.html#h{new_id}">{name} {new_id}</a>'
    return (old, new)

def bare(source, old_id, new_id):
    old = f'read/{source}.html#h{old_id}">{old_id}</a>'
    new = f'read/{source}.html#h{new_id}">{new_id}</a>'
    return (old, new)

# ── d05: abu-dawud h4582 → h4586 ─────────────────────────────────────────────
# h4582 = slave price; correct = blood-money differential
print("d05:")
apply(os.path.join(A, "abu-dawud/d05-female-blood-money-half.html"), [
    lnk("abu-dawud", "4582", "4586"),
    bare("abu-dawud", "4582", "4586"),
])

# ── d06: h4933→h4935, h4934→h4935, bukhari h5134→h5110 ───────────────────────
print("d06:")
apply(os.path.join(A, "abu-dawud/d06-prepubescent-marriage-normalised.html"), [
    lnk("abu-dawud", "4933", "4935"),
    bare("abu-dawud", "4933", "4935"),
    lnk("abu-dawud", "4934", "4935"),
    bare("abu-dawud", "4934", "4935"),
    lnk("bukhari",   "5134", "5110"),
    bare("bukhari",  "5134", "5110"),
])

# ── d07: abu-dawud h570→h569, bukhari h869→h848 ──────────────────────────────
# h869 = siwak/tooth-stick story; correct = Aisha on women at mosque
print("d07:")
apply(os.path.join(A, "abu-dawud/d07-women-prayer-inner-rooms.html"), [
    lnk("abu-dawud", "570", "569"),
    bare("abu-dawud", "570", "569"),
    lnk("bukhari",   "869", "848"),
    bare("bukhari",  "869", "848"),
])

# ── d09: h3038→h2988, h3041→h3000 ────────────────────────────────────────────
print("d09:")
apply(os.path.join(A, "abu-dawud/d09-jizya-humiliation-tax.html"), [
    lnk("abu-dawud", "3038", "2988"),
    bare("abu-dawud", "3038", "2988"),
    lnk("abu-dawud", "3041", "3000"),
    bare("abu-dawud", "3041", "3000"),
])

# ── d10: h4448 → h4417 ───────────────────────────────────────────────────────
print("d10:")
apply(os.path.join(A, "abu-dawud/d10-lashes-plus-stoning.html"), [
    lnk("abu-dawud", "4448", "4417"),
    bare("abu-dawud", "4448", "4417"),
])

# ── d12: muslim h49 → h84 ────────────────────────────────────────────────────
# h49 = death-bed visit; correct = change evil with your hand
print("d12:")
apply(os.path.join(A, "abu-dawud/d12-vigilantism-warrant.html"), [
    lnk("muslim", "49", "84"),
    bare("muslim", "49", "84"),
])

# ── d14: bukhari h1041→h1013, h1059→h1013 ────────────────────────────────────
print("d14:")
apply(os.path.join(A, "abu-dawud/d14-eclipses-deaths.html"), [
    lnk("bukhari", "1041", "1013"),
    bare("bukhari", "1041", "1013"),
    lnk("bukhari", "1059", "1013"),
    bare("bukhari", "1059", "1013"),
])

# ── d15: abu-dawud h2050 → h2084 ─────────────────────────────────────────────
print("d15:")
apply(os.path.join(A, "abu-dawud/d15-no-marriage-without-wali.html"), [
    lnk("abu-dawud", "2050", "2084"),
    bare("abu-dawud", "2050", "2084"),
])

# ── d16: bukhari h2237 → h2197 ───────────────────────────────────────────────
# h2237 = date palms distribution; correct = forbidden earnings
print("d16:")
apply(os.path.join(A, "abu-dawud/d16-forbidden-earnings.html"), [
    lnk("bukhari", "2237", "2197"),
    bare("bukhari", "2237", "2197"),
])

# ── d17: h1577→h1613, bukhari h1503→h1459 ────────────────────────────────────
print("d17:")
apply(os.path.join(A, "abu-dawud/d17-zakat-on-slaves.html"), [
    lnk("abu-dawud", "1577", "1613"),
    bare("abu-dawud", "1577", "1613"),
    lnk("bukhari",   "1503", "1459"),
    bare("bukhari",  "1503", "1459"),
])

# ── d18: h4544 → h4505 (chaining: h4587→h4544 done, h4544 also wrong) ────────
print("d18:")
apply(os.path.join(A, "abu-dawud/d18-diyya-by-religion.html"), [
    lnk("abu-dawud", "4544", "4505"),
    bare("abu-dawud", "4544", "4505"),
])

# ── b04: bukhari h1462 → h1412 ───────────────────────────────────────────────
# h1462 = donkey-riding; correct = fitna from women hadith
print("b04:")
apply(os.path.join(A, "bukhari/b04-fitna-women.html"), [
    lnk("bukhari", "1462", "1412"),
    bare("bukhari", "1462", "1412"),
])

# ── b05: bukhari h1462 → h1412 ───────────────────────────────────────────────
print("b05:")
apply(os.path.join(A, "bukhari/b05-women-deficient.html"), [
    lnk("bukhari", "1462", "1412"),
    bare("bukhari", "1462", "1412"),
])

# ── b08: bukhari h4028 → h4069 ───────────────────────────────────────────────
# h4028 = chain-narrators only; correct = Banu Qurayza massacre
print("b08:")
apply(os.path.join(A, "bukhari/b08-banu-qurayza.html"), [
    lnk("bukhari", "4028", "4069"),
    bare("bukhari", "4028", "4069"),
])

# ── b09: bukhari h4881 → h4914 (chaining: h5158→h4881 done, h4881 also wrong)
print("b09:")
apply(os.path.join(A, "bukhari/b09-safiyya-khaybar.html"), [
    lnk("bukhari", "4881", "4914"),
    bare("bukhari", "4881", "4914"),
])

# ── i02: ibn-majah h1677→h1666 (chaining), muslim h1453→h1411 ────────────────
print("i02:")
apply(os.path.join(A, "ibn-majah/i02-sahla-salim-breastfeeding.html"), [
    lnk("ibn-majah", "1677", "1666"),
    bare("ibn-majah", "1677", "1666"),
    lnk("muslim",    "1453", "1411"),
    bare("muslim",   "1453", "1411"),
])

# ── i03: ibn-majah h1852→h1824, h1853→h1824 ──────────────────────────────────
print("i03:")
apply(os.path.join(A, "ibn-majah/i03-wife-prostration-husband.html"), [
    lnk("ibn-majah", "1852", "1824"),
    bare("ibn-majah", "1852", "1824"),
    lnk("ibn-majah", "1853", "1824"),
    bare("ibn-majah", "1853", "1824"),
])

# ── m02: muslim h1438 → h1468 ────────────────────────────────────────────────
print("m02:")
apply(os.path.join(A, "muslim/m02-azl-with-captives.html"), [
    lnk("muslim", "1438", "1468"),
    bare("muslim", "1438", "1468"),
])

# ── m06: muslim h17 → h33 ────────────────────────────────────────────────────
# h17 = death-bed / cross-reference hadith; correct = "fight people" hadith
print("m06:")
apply(os.path.join(A, "muslim/m06-three-options-non-muslims.html"), [
    lnk("muslim", "17", "33"),
    bare("muslim", "17", "33"),
])

# ── m08: muslim h1452→h1411, h1453→h1411, h1454→h1411 ───────────────────────
print("m08:")
apply(os.path.join(A, "muslim/m08-adult-breastfeeding.html"), [
    lnk("muslim", "1452", "1411"),
    bare("muslim", "1452", "1411"),
    lnk("muslim", "1453", "1411"),
    bare("muslim", "1453", "1411"),
    lnk("muslim", "1454", "1411"),
    bare("muslim", "1454", "1411"),
])

# ── m10: muslim h2767 → h2737 ────────────────────────────────────────────────
print("m10:")
apply(os.path.join(A, "muslim/m10-jew-christian-replaces-muslim-hell.html"), [
    lnk("muslim", "2767", "2737"),
    bare("muslim", "2767", "2737"),
])

# ── m13: muslim h510 → h558 ──────────────────────────────────────────────────
print("m13:")
apply(os.path.join(A, "muslim/m13-black-dogs-devils.html"), [
    lnk("muslim", "510", "558"),
    bare("muslim", "510", "558"),
])

# ── m14: bukhari h3318 → h3336 ───────────────────────────────────────────────
print("m14:")
apply(os.path.join(A, "muslim/m14-cat-confined-hell.html"), [
    lnk("bukhari", "3318", "3336"),
    bare("bukhari", "3318", "3336"),
])

# ── m15: bukhari h3199 → h3201 ───────────────────────────────────────────────
# Different file from b06 (which fixed h3199→h3066 for sun prostrates)
print("m15:")
apply(os.path.join(A, "muslim/m15-suns-prostration-throne.html"), [
    lnk("bukhari", "3199", "3201"),
    bare("bukhari", "3199", "3201"),
])

# ── m17: bukhari h3053 → h3023 ───────────────────────────────────────────────
print("m17:")
apply(os.path.join(A, "muslim/m17-expel-jews-christians.html"), [
    lnk("bukhari", "3053", "3023"),
    bare("bukhari", "3053", "3023"),
])

# ── t10: tirmidhi h2484 → h2451 ──────────────────────────────────────────────
print("t10:")
apply(os.path.join(A, "tirmidhi/t10-prostration-mark-protects.html"), [
    lnk("tirmidhi", "2484", "2451"),
    bare("tirmidhi", "2484", "2451"),
])

# ── t13: bukhari h7122 → h7154 ───────────────────────────────────────────────
print("t13:")
apply(os.path.join(A, "tirmidhi/t13-dajjal-eschatology.html"), [
    lnk("bukhari", "7122", "7154"),
    bare("bukhari", "7122", "7154"),
])

# ── t19: tirmidhi h2209 → h2205 ──────────────────────────────────────────────
print("t19:")
apply(os.path.join(A, "tirmidhi/t19-predestination-effort-futile.html"), [
    lnk("tirmidhi", "2209", "2205"),
    bare("tirmidhi", "2209", "2205"),
])

# ── Quran anchor fixes ────────────────────────────────────────────────────────

# q09: "1:10" and "1:2" are display ratios linked to non-existent or wrong
# Quran anchors. Fix hrefs to the actual verses being discussed (Q 8:65/8:66).
print("q09 (quran ratio anchors):")
apply(os.path.join(A, "quran/q09-abrogation.html"), [
    ('href="../../read/quran.html#s1v10">',  'href="../../read/quran.html#s8v65">'),
    ('href="../../read/quran.html#s1v2">',   'href="../../read/quran.html#s8v66">'),
])

# q19: "1:205" is a reference to Ibn Saʿd's Tabaqat (book 1, p.205),
# not a Quran verse. Remove the broken Quran reader link.
print("q19 (non-quran citation):")
apply(os.path.join(A, "quran/q19-satanic-verses.html"), [
    ('<a class="cite-link" href="../../read/quran.html#s1v205">1:205</a>', '1:205'),
])

print("\nAll done.")
