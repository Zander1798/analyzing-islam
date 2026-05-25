#!/usr/bin/env python3
"""
Analyzing Islam Vol I — HTML Book Generator
Produces: book-design/vol1-quran/book.html
Run: python build-book-html.py
"""
import re, json, html as html_mod
from pathlib import Path

BASE    = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG = BASE / "site/assets/data/catalog-entries.json"
QURAN   = BASE / "site/catalog/quran.html"
OUT_DIR = BASE / "book-design/vol1-quran"
OUT     = OUT_DIR / "book.html"

# ── Exclusions (same as build-book-docx.py) ───────────────────────────────────
EXCLUDE_IDS = {
    "amputate-the-hand-of-the-thief-regardless-of-circumstance-4104d45b",
    "one-hundred-lashes-for-fornication-yet-the-hadith-demands-st-f805f912",
    "jews-transformed-into-apes-a205d9d7",
    "the-sun-runs-to-a-fixed-resting-place-5f69c2e2",
    "quran-fire-punishment-to-skin-replace",
    "polytheists-are-unclean-and-forbidden-from-the-sacred-mosque-793234d0",
    "fabricated-quote-jews-say-ezra-is-the-son-of-allah-df9200f3",
    "quran-menstruating-retreat",
    "quran-cow-that-killed",
    "quran-iblis-command-prostrate",
    "jinn-listen-to-the-quran-in-a-tree-and-convert-63828ff4",
    "creation-in-six-days-or-eight-a-day-count-contradiction-201b57cd",
    "quran-predestination-but-punishment",
    "quran-allah-best-plotters-jesus",
    "quran-pharaoh-wall-building",
    "quran-do-not-befriend-kafir",
    "quran-right-hand-sex-captive-wife",
    "quran-children-spoils-war",
    "quran-number-of-sleepers",
    "quran-how-long-sleepers-slept",
    "quran-muhammad-mutah-private-wife",
    "quran-prophet-captives-war-booty",
}

# ── Chapter definitions ───────────────────────────────────────────────────────
CHAPTERS = {
    1:  ("Abrogation",
         "The doctrine of naskh (abrogation) holds that later Quranic verses can supersede earlier ones "
         "while both remain in the written text. The Quran references this principle explicitly at Q 2:106 and "
         "Q 16:101. This chapter examines the theological and logical problems that arise when a supposedly "
         "perfect, eternal divine text requires internal revision."),
    2:  ("Scripture Integrity",
         "The Quran presents itself as a perfectly preserved, uniquely clear, and self-authenticating revelation. "
         "This chapter examines the passages and historical facts that challenge those claims."),
    3:  ("Contradictions",
         "A text claimed to be the direct word of an omniscient God is expected to be internally consistent. "
         "This chapter catalogues passages in the Quran that contradict other Quranic passages."),
    4:  ("Logical Inconsistency",
         "Several Quranic passages generate problems of logical form: self-refuting claims, arguments that assume "
         "what they are meant to prove, and divine attributes that cannot coherently coexist."),
    5:  ("Allah's Character",
         "Islamic theology attributes to Allah a set of perfections — omniscience, omnipotence, justice, mercy. "
         "A number of Quranic passages sit in tension with one or more of those attributes."),
    6:  ("Cosmology",
         "A number of Quranic passages describe the physical universe in ways that reflect pre-scientific "
         "cosmological assumptions rather than observed reality."),
    7:  ("Pre-Islamic Borrowings",
         "Several Quranic narratives have direct parallels in Jewish midrashic literature, Christian apocryphal "
         "gospels, Zoroastrian texts, and pre-Islamic Arabian legend."),
    8:  ("Prophetic Character",
         "The Quran presents Muhammad as the exemplary moral model. Several passages, however, describe a prophet "
         "who required divine reassurance and whose conduct raises ethical questions the text itself registers."),
    9:  ("Prophetic Privileges",
         "A cluster of Quranic verses grants Muhammad exemptions and permissions explicitly denied to ordinary "
         "believers — additional wives, marriage to his adopted son's divorcee, a personal cut of war spoils."),
    10: ("Jesus / Christology",
         "The Quran contains a substantial Christology — an account of Jesus that agrees with some Christian "
         "claims, categorically denies others, and adds details found in no earlier canonical source."),
    11: ("Women & Sexual Issues",
         "The Quran legislates extensively on the status of women, marriage, sexual access, and related matters. "
         "Several passages establish legal hierarchies that contemporary ethics regards as discriminatory."),
    12: ("Child Marriage",
         "Q 65:4 sets out divorce procedures for wives who have not yet menstruated — an explicit "
         "Quranic provision for marriage to pre-pubescent girls."),
    13: ("LGBTQ / Gender",
         "The Quran's account of Lot's people and related passages have been read by the classical tradition "
         "as a divine condemnation of same-sex relations."),
    14: ("Slavery & Captives",
         "The Quran regulates slavery rather than prohibiting it — specifying procedures for manumission "
         "and permitting sexual access to female captives."),
    15: ("Warfare & Jihad",
         "Several Quranic verses command violence against non-Muslims in terms that admit no obvious limiting "
         "context — commanding believers to kill, fight, or subjugate."),
    16: ("Apostasy & Blasphemy",
         "The Quran does not state an explicit death penalty for apostasy, but several passages are read by "
         "classical jurists as endorsing it."),
    17: ("Governance",
         "A number of passages establish that sovereignty belongs to Allah alone and that legislation is his "
         "exclusive prerogative — the canonical proof-texts for Islamic theocratic governance."),
    18: ("Disbelievers & Moral Problems",
         "The Quran characterises non-Muslims in terms ranging from misguided to irredeemably corrupt, "
         "the worst of creatures, and objects of divine curse."),
    19: ("Antisemitism",
         "The Quran contains direct derogatory characterisations of Jews as a group: divine transformation into "
         "apes and pigs, fabricated theological claims attributed to them."),
    20: ("Paradise",
         "The Quran's descriptions of paradise are detailed and physical: gardens of flowing rivers, eternal "
         "virgin houris, rivers of wine and honey. Several descriptions raise moral problems."),
    21: ("Strange",
         "A number of Quranic passages describe supernatural events and historical claims that resist "
         "straightforward naturalisation — stars as missiles thrown at eavesdropping jinn."),
    22: ("Magic & Ritual",
         "The Quran legislates extensively on ritual purity and acknowledges a world populated by jinn, "
         "sorcerers, and supernatural entities."),
    23: ("Animals",
         "Several Quranic passages about animals create scientific, moral, or theological problems: bees "
         "that receive divine inspiration, animals that form communities like humans."),
}

# ── Chapter assignment ────────────────────────────────────────────────────────
TAG_PRIORITY = [
    ("antisemitism", 19), ("childmarriage", 12), ("apostasy", 16),
    ("privileges",    9), ("jesus",         10), ("abrogation",   1),
    ("warfare",      15), ("governance",    17), ("preislamic",   7),
    ("scripture",     2), ("allah",          5), ("cosmology",    6),
    ("science",       6), ("magic",         22), ("slavery",     14),
    ("women",        11), ("sexual",        11), ("hudud",       17),
    ("prophet",       8), ("animals",       23), ("ritual",      22),
    ("contradiction", 3), ("logic",          4), ("paradise",    20),
    ("hell",         20), ("disbelievers",  18), ("morality",    18),
    ("strange",      21), ("incest",        13), ("gross-vile",  13),
    ("lgbtq",        13),
]

ID_OVERRIDES = {
    "the-seven-sleepers-of-ephesus-a-christian-legend-as-quranic-13829e66": 7,
    "sexual-access-to-married-female-slaves-right-hand-possesses-25cd8f4b": 11,
    "quran-wudu-tayammum-touching-women": 22,
    "quran-abasa-frowned-blind-rebuke": 8,
    "quran-inheritance-fractions-do-not-sum": 4,
    "quran-46-15-31-14-six-month-gestation-arithmetic": 6,
    "quran-69-32-seventy-cubit-chain-ghislin-food": 20,
    "paradise-as-physical-pleasure-garden-with-purified-spouses-65756a43": 20,
    "the-houris-eternal-virgins-as-paradise-reward-d8c254e9": 20,
    "quran-quran-as-healing": 2,
    "islamic-dilemma": 2,
    "the-quran-endorses-jews-and-christians-to-judge-by-their-own-32929162": 2,
    "no-one-can-change-the-words-of-allah-yet-tahrif-is-the-centr-d98f36e4": 2,
    "prophet-should-not-take-captives-until-he-inflicts-a-massacr-75d23fb1": 14,
    "quran-38-31-33-solomon-hamstrings-the-horses": 23,
}

STRENGTH_ORDER = {"basic": 0, "moderate": 1, "strong": 2}
STRENGTH_LABEL = {"basic": "BASIC", "moderate": "MODERATE", "strong": "STRONG"}
STRENGTH_CSS   = {"basic": "tag-basic", "moderate": "tag-moderate", "strong": "tag-strong"}


def strip_tags(s: str) -> str:
    """Strip HTML tags and decode common entities."""
    s = re.sub(r'<[^>]+>', '', s)
    for ent, ch in [
        ('&amp;','&'),('&lt;','<'),('&gt;','>'),('&nbsp;',' '),
        ('&#8212;','—'),('&#8211;','–'),('&#8216;',"'"),('&#8217;',"'"),
        ('&#8220;','"'),('&#8221;','"'),('&mdash;','—'),('&ndash;','–'),
        ('&rsquo;',"'"),('&lsquo;',"'"),('&ldquo;','"'),('&rdquo;','"'),
        ('&hellip;','…'),
    ]:
        s = s.replace(ent, ch)
    return re.sub(r'[ \t]+', ' ', s).strip()


def esc(s: str) -> str:
    """HTML-escape a plain-text string for insertion into HTML."""
    return html_mod.escape(str(s))


def assign_chapter(eid: str, categories: list) -> int:
    if eid in ID_OVERRIDES:
        return ID_OVERRIDES[eid]
    for tag, ch in TAG_PRIORITY:
        if tag in categories:
            return ch
    return 18


def get_entries() -> list:
    """Return 262 active Quran entries from catalog-entries.json."""
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    return [e for e in catalog
            if e.get('source') == 'quran' and e['id'] not in EXCLUDE_IDS]


def parse_entries() -> dict:
    """Parse body text from quran.html. Returns dict[id -> {quote,says,problem,response,fails}]."""
    raw = QURAN.read_text(encoding='utf-8', errors='ignore')
    pat = r'<div[^>]+class="[^"]*\bentry\b[^"]*"[^>]+id="([^"]+)"[^>]*>'
    opens = list(re.finditer(pat, raw))
    result = {}
    for i, m in enumerate(opens):
        eid = m.group(1)
        end = opens[i+1].start() if i+1 < len(opens) else len(raw)
        chunk = raw[m.start():end]
        bq_m = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', chunk, re.DOTALL)
        quote = ''
        if bq_m:
            q = re.sub(r'<p[^>]*>', '', bq_m.group(1))
            q = re.sub(r'</p>', ' ', q)
            quote = strip_tags(q).strip()
        h4_parts = re.split(r'<h4[^>]*>', chunk)
        sections = {'quote': quote, 'says': '', 'problem': '', 'response': '', 'fails': ''}
        for part in h4_parts[1:]:
            end_tag = part.find('</h4>')
            if end_tag == -1:
                continue
            header = part[:end_tag].lower().strip()
            body = part[end_tag+5:]
            paras = re.findall(r'<p[^>]*>(.*?)</p>', body, re.DOTALL)
            text = '\n\n'.join(strip_tags(p) for p in paras if p.strip())
            if 'what the verse' in header:
                sections['says'] = text
            elif 'why this is a problem' in header:
                sections['problem'] = text
            elif 'muslim response' in header:
                sections['response'] = text
            elif 'why it fails' in header:
                sections['fails'] = text
        result[eid] = sections
    return result


def build_chapters(entries: list) -> dict:
    """Assign entries to chapters and sort basic→moderate→strong within each."""
    chapters = {n: [] for n in CHAPTERS}
    for e in entries:
        ch = assign_chapter(e['id'], e.get('categories', []))
        chapters[ch].append(e)
    for ch in chapters:
        chapters[ch].sort(key=lambda e: STRENGTH_ORDER.get(e.get('strength', ''), 0))
    return chapters


if __name__ == '__main__':
    pass  # main() added in Task 8
