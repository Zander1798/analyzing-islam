import re, json
from pathlib import Path

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
raw = (BASE / "site/catalog/quran.html").read_text(encoding="utf-8", errors="ignore")
catalog = json.loads((BASE / "site/assets/data/catalog-entries.json").read_text(encoding="utf-8"))
cat = {e["id"]: e for e in catalog}

all_entries = list(re.finditer(r'<div[^>]+class="[^"]*\bentry\b[^"]*"[^>]+id="([^"]+)"', raw))
ids_list = [x.group(1) for x in all_entries]
pos_list = [x.start() for x in all_entries]

def get_text(eid):
    try:
        idx = ids_list.index(eid)
    except ValueError:
        return ""
    end = pos_list[idx+1] if idx+1 < len(pos_list) else len(raw)
    chunk = raw[pos_list[idx]:end]
    return re.sub(r"<[^>]+>", "", chunk).strip()

PAIRS = [
    ("quran-s2v65-apes-pigs-sabbath",           "jews-transformed-into-apes-a205d9d7"),
    ("quran-s36v38-sun-stopping-point",          "the-sun-runs-to-a-fixed-resting-place-5f69c2e2"),
    ("quran-fire-punishment-to-skin-replace",    "skins-roasted-and-replaced-eternal-torture-engineered-for-ma-e7720e62"),
    ("quran-s9v28-polytheists-impure",           "polytheists-are-unclean-and-forbidden-from-the-sacred-mosque-793234d0"),
    ("quran-s9v30-ezra-son-of-allah",            "fabricated-quote-jews-say-ezra-is-the-son-of-allah-df9200f3"),
    ("quran-menstruating-retreat",               "menstruation-as-harm-husbands-must-keep-away-da581acc"),
    ("quran-cow-that-killed",                    "the-cow-that-revives-a-murdered-man-bd38a867"),
    ("quran-iblis-command-prostrate",            "iblis-the-jinn-refuses-to-prostrate-but-the-command-was-give-18df916e"),
    ("quran-jinn-listen-quran",                  "jinn-listen-to-the-quran-in-a-tree-and-convert-63828ff4"),
    ("quran-s41v9-creation-days-arithmetic",     "creation-in-six-days-or-eight-a-day-count-contradiction-201b57cd"),
    ("quran-predestination-but-punishment",      "all-things-we-created-with-predestination-then-punishment-be-526c5d8b"),
    ("quran-allah-best-plotters-jesus",          "allah-is-the-best-of-deceivers-divine-deception-as-a-virtue-87a6b648"),
    ("quran-pharaoh-wall-building",              "haman-pharaoh-s-minister-according-to-the-quran-but-a-persia-1d0165c4"),
    ("quran-do-not-befriend-kafir",              "taqiyya-permission-to-deceive-about-your-faith-63a78a52"),
]

keepers = []
drops = []
print()
for i, (a, b) in enumerate(PAIRS, 1):
    ta, tb = get_text(a), get_text(b)
    if len(ta) >= len(tb):
        keep, drop, kl, dl = a, b, len(ta), len(tb)
    else:
        keep, drop, kl, dl = b, a, len(tb), len(ta)
    kt = cat.get(keep, {}).get("title", keep)
    dt = cat.get(drop, {}).get("title", drop)
    kref = cat.get(keep, {}).get("ref", "")
    dref = cat.get(drop, {}).get("ref", "")
    print(f"{i:>2}. KEEP [{kl:>5} chars] {kref:<15} {kt}")
    print(f"    DROP [{dl:>5} chars] {dref:<15} {dt}")
    print()
    keepers.append(keep)
    drops.append(drop)

print("=" * 60)
print("FINAL KEEPERS:")
for k in keepers:
    print(f"  {k}")
print()
print("FINAL DROPS (add to EXCLUDE_IDS):")
for d in drops:
    print(f'  "{d}",')
