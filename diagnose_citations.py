"""
For each flagged citation: print the dossier's claim, the content at the
cited (wrong) ID, and the content at the suggested correct ID — so every
case can be evaluated as a real error or false positive.
"""
import os, re, html as html_mod

SITE     = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
ARGS_DIR = os.path.join(SITE, "arguments")
READ_DIR = os.path.join(SITE, "read")

_reader_cache: dict = {}

def reader_html(source):
    if source not in _reader_cache:
        p = os.path.join(READ_DIR, f"{source}.html")
        _reader_cache[source] = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    return _reader_cache[source]

_hadith_index: dict = {}

def hadith_index(source):
    if source in _hadith_index:
        return _hadith_index[source]
    content = reader_html(source)
    idx = {}
    pat = re.compile(r'id="(h\d+)"', re.IGNORECASE)
    positions = [(m.group(1), m.start()) for m in pat.finditer(content)]
    for i, (hid, start) in enumerate(positions):
        end = positions[i+1][1] if i+1 < len(positions) else len(content)
        block = content[start:end]
        text = re.sub(r"<[^>]+>", " ", block)
        text = html_mod.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        idx[hid] = text
    _hadith_index[source] = idx
    return idx

def safe(s, n=180):
    return s[:n].encode('ascii', 'replace').decode('ascii')

# ── Every flagged case from v2 output ────────────────────────────────────────
cases = [
    # (file_rel, source, cited_id, claimed_correct)
    ("arguments/abu-dawud/d01-awtas-captives-iddah.html",              "abu-dawud", "h2150",  "h2156"),
    ("arguments/abu-dawud/d03-blind-man-umm-walad.html",               "abu-dawud", "h4361",  "h4363"),
    ("arguments/abu-dawud/d05-female-blood-money-half.html",           "abu-dawud", "h4582",  "h4586"),
    ("arguments/abu-dawud/d06-prepubescent-marriage-normalised.html",  "abu-dawud", "h4933",  "h4935"),
    ("arguments/abu-dawud/d06-prepubescent-marriage-normalised.html",  "abu-dawud", "h4934",  "h4935"),
    ("arguments/abu-dawud/d06-prepubescent-marriage-normalised.html",  "abu-dawud", "h2128",  "h2122"),
    ("arguments/abu-dawud/d07-women-prayer-inner-rooms.html",          "abu-dawud", "h570",   "h569"),
    ("arguments/abu-dawud/d08-bidaa-misguidance.html",                 "abu-dawud", "h4607",  "h4609"),
    ("arguments/abu-dawud/d12-vigilantism-warrant.html",               "abu-dawud", "h4344",  "h4331"),
    ("arguments/abu-dawud/d14-eclipses-deaths.html",                   "abu-dawud", "h1144",  "h1151"),
    ("arguments/abu-dawud/d15-no-marriage-without-wali.html",          "tirmidhi",  "h1102",  "h1104"),
    ("arguments/abu-dawud/d17-zakat-on-slaves.html",                   "bukhari",   "h1463",  "h1451"),
    ("arguments/abu-dawud/d18-diyya-by-religion.html",                 "abu-dawud", "h4587",  "h4586"),
    ("arguments/bukhari/b03-stoning-verse-lost.html",                  "bukhari",   "h6830",  "h6844"),
    ("arguments/bukhari/b03-stoning-verse-lost.html",                  "bukhari",   "h6829",  "h6844"),
    ("arguments/bukhari/b04-fitna-women.html",                         "bukhari",   "h304",   "h301"),
    ("arguments/bukhari/b05-women-deficient.html",                     "bukhari",   "h304",   "h301"),
    ("arguments/bukhari/b06-sun-prostrates.html",                      "bukhari",   "h7424",  None),
    ("arguments/bukhari/b06-sun-prostrates.html",                      "bukhari",   "h3199",  "h3201"),
    ("arguments/bukhari/b08-banu-qurayza.html",                        "bukhari",   "h4119",  "h4131"),
    ("arguments/bukhari/b09-safiyya-khaybar.html",                     "bukhari",   "h5158",  "h5154"),
    ("arguments/bukhari/b12-three-lawful-kills.html",                  "bukhari",   "h6878",  "h6866"),
    ("arguments/bukhari/b12-three-lawful-kills.html",                  "tirmidhi",  "h1402",  "h1417"),
    ("arguments/bukhari/b13-strength-thirty-men.html",                 "bukhari",   "h7517",  None),
    ("arguments/ibn-majah/i02-sahla-salim-breastfeeding.html",        "ibn-majah", "h1942",  "h1938"),
    ("arguments/ibn-majah/i03-wife-prostration-husband.html",         "tirmidhi",  "h1159",  "h1162"),
    ("arguments/muslim/m06-three-options-non-muslims.html",           "muslim",    "h1731",  "h1743"),
    ("arguments/muslim/m16-hell-emptied-of-believers.html",           "bukhari",   "h7510",  None),
    ("arguments/muslim/m19-allah-two-forms.html",                     "bukhari",   "h7437",  None),
    ("arguments/quran/q15-zayd-zaynab-marriage.html",                 "bukhari",   "h7420",  None),
    ("arguments/tirmidhi/t06-angels-houses-images.html",              "bukhari",   "h5950",  "h5942"),
    ("arguments/tirmidhi/t12-mahdi-eschatology.html",                 "abu-dawud", "h4282",  "h4283"),
    ("arguments/tirmidhi/t16-jihad-supreme-deed.html",                "tirmidhi",  "h2003",  "h2017"),
    ("arguments/tirmidhi/t19-predestination-effort-futile.html",      "tirmidhi",  "h2209",  "h2205"),
    ("arguments/tirmidhi/t19-predestination-effort-futile.html",      "bukhari",   "h3208",  "h3194"),
]

for file_rel, source, cited, correct in cases:
    idx = hadith_index(source)
    cited_text  = idx.get(cited,   "(NOT IN READER)")
    correct_text = idx.get(correct, "(NOT IN READER)") if correct else "(no suggestion)"

    print("-"*90)
    print(f"FILE  : {file_rel}")
    print(f"CITED : {source}#{cited}")
    print(f"  AT CITED : {safe(cited_text)}")
    if correct:
        print(f"SUGGESTED: {source}#{correct}")
        print(f"  AT CORR  : {safe(correct_text)}")
    else:
        print(f"SUGGESTED: (none — ID not found in reader at all)")
    print()
