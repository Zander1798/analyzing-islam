import json
from pathlib import Path

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
catalog = json.loads((BASE / "site/assets/data/catalog-entries.json").read_text(encoding="utf-8"))
cat = {e["id"]: e for e in catalog}

NEAR_DUPES = [
    # Group A: Terror / warfare — 3 entries, overlapping refs
    ("A", "quran-s8v60-terrorize-enemies",
           "cast-terror-into-the-hearts-strike-upon-the-necks-caf4bc42",
           "Both about preparing/casting terror into enemies hearts — different verses (8:60 vs 8:12)"),

    ("A", "quran-s8v60-terrorize-enemies",
           "we-will-cast-terror-into-the-hearts-of-those-who-disbelieve-ec0fdd8b",
           "Both about terror against disbelievers — 8:60 vs 3:151 (also refs 8:12, 8:60)"),

    # Group B: Right hand possesses / sexual captives — 3 entries, heavily overlapping
    ("B", "quran-right-hand-sex-captive-wife",
           "sexual-access-to-married-female-slaves-right-hand-possesses-25cd8f4b",
           "Both: sexual access to captive women ('right hand possesses') — Q 23:5-6 vs Q 4:24"),

    ("B", "quran-children-spoils-war",
           "sexual-access-to-married-female-slaves-right-hand-possesses-25cd8f4b",
           "Both: war captives as legal sexual partners — Q 4:24 appears in both"),

    # Group C: Seven Sleepers — 3 entries on the same Quran passage (18:9-26)
    ("C", "quran-number-of-sleepers",
           "the-seven-sleepers-of-ephesus-a-christian-legend-as-quranic-13829e66",
           "Number-of-sleepers question (Q 18:22) vs full Seven Sleepers legend (Q 18:9-26)"),

    ("C", "quran-how-long-sleepers-slept",
           "the-seven-sleepers-of-ephesus-a-christian-legend-as-quranic-13829e66",
           "Duration problem (Q 18:25-26) vs full Seven Sleepers legend (Q 18:9-26)"),

    # Group D: Dhul-Qarnayn / Gog & Magog — same passage, different angles
    ("D", "quran-gog-magog-wall-yajuj",
           "dhul-qarnayn-alexander-the-great-as-a-muslim-monotheist-36e9015b",
           "Iron wall + Gog/Magog (Q 18:92-97) vs Dhul-Qarnayn identity (Q 18:83-98)"),

    # Group E: Inheritance — same passage, different specific problems
    ("E", "quran-inheritance-fractions-do-not-sum",
           "male-inheritance-is-double-female-inheritance-db0a739d",
           "Fractions don't add to 1 (Q 4:11-12) vs male gets double share (Q 4:11)"),

    # Group F: Prophet's marriage privileges — aggregate entry vs individual sub-entries
    ("F", "muhammad-s-special-marriage-privileges-above-other-believers-e6d39c00",
           "quran-muhammad-mutah-private-wife",
           "Aggregate privileges entry (Q 33:50-52) vs specific: woman who offers herself"),

    ("F", "muhammad-s-special-marriage-privileges-above-other-believers-e6d39c00",
           "quran-prophet-captives-war-booty",
           "Aggregate privileges entry (Q 33:50-52) vs specific: any woman/captive he wants"),
]

print()
for grp, a, b, note in NEAR_DUPES:
    ea = cat.get(a, {})
    eb = cat.get(b, {})
    print(f"Group {grp}:")
    print(f"  Entry 1: {ea.get('title','[not found]')}")
    print(f"           ref: {ea.get('ref','?')}  |  strength: {ea.get('strength','?')}")
    print(f"  Entry 2: {eb.get('title','[not found]')}")
    print(f"           ref: {eb.get('ref','?')}  |  strength: {eb.get('strength','?')}")
    print(f"  Issue:   {note}")
    print()
