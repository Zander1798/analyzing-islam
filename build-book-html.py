#!/usr/bin/env python3
"""
Analyzing Islam Vol I — HTML Book Generator
Produces: book-design/vol1-quran/book.html
Run: python build-book-html.py
"""
import re, json, html as html_mod
from pathlib import Path

BASE    = Path(__file__).resolve().parent
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

# ── Surah names (for Verse Index grouping) ────────────────────────────────────
SURAH_NAMES = {
    1:"AL-FATIHAH", 2:"AL-BAQARAH", 3:"ALI 'IMRAN", 4:"AN-NISA",
    5:"AL-MA'IDAH", 6:"AL-AN'AM", 7:"AL-A'RAF", 8:"AL-ANFAL",
    9:"AT-TAWBAH", 10:"YUNUS", 11:"HUD", 12:"YUSUF",
    13:"AR-RA'D", 14:"IBRAHIM", 15:"AL-HIJR", 16:"AN-NAHL",
    17:"AL-ISRA", 18:"AL-KAHF", 19:"MARYAM", 20:"TA-HA",
    21:"AL-ANBIYA", 22:"AL-HAJJ", 23:"AL-MU'MINUN", 24:"AN-NUR",
    25:"AL-FURQAN", 26:"ASH-SHU'ARA", 27:"AN-NAML", 28:"AL-QASAS",
    29:"AL-'ANKABUT", 30:"AR-RUM", 31:"LUQMAN", 32:"AS-SAJDAH",
    33:"AL-AHZAB", 34:"SABA", 35:"FATIR", 36:"YA-SIN",
    37:"AS-SAFFAT", 38:"SAD", 39:"AZ-ZUMAR", 40:"GHAFIR",
    41:"FUSSILAT", 42:"ASH-SHURA", 43:"AZ-ZUKHRUF", 44:"AD-DUKHAN",
    45:"AL-JATHIYAH", 46:"AL-AHQAF", 47:"MUHAMMAD", 48:"AL-FATH",
    49:"AL-HUJURAT", 50:"QAF", 51:"ADH-DHARIYAT", 52:"AT-TUR",
    53:"AN-NAJM", 54:"AL-QAMAR", 55:"AR-RAHMAN", 56:"AL-WAQI'AH",
    57:"AL-HADID", 58:"AL-MUJADILA", 59:"AL-HASHR", 60:"AL-MUMTAHANAH",
    61:"AS-SAF", 62:"AL-JUMU'AH", 63:"AL-MUNAFIQUN", 64:"AT-TAGHABUN",
    65:"AT-TALAQ", 66:"AT-TAHRIM", 67:"AL-MULK", 68:"AL-QALAM",
    69:"AL-HAQQAH", 70:"AL-MA'ARIJ", 71:"NUH", 72:"AL-JINN",
    73:"AL-MUZZAMMIL", 74:"AL-MUDDATHTHIR", 75:"AL-QIYAMAH", 76:"AL-INSAN",
    77:"AL-MURSALAT", 78:"AN-NABA", 79:"AN-NAZI'AT", 80:"'ABASA",
    81:"AT-TAKWIR", 82:"AL-INFITAR", 83:"AL-MUTAFFIFIN", 84:"AL-INSHIQAQ",
    85:"AL-BURUJ", 86:"AT-TARIQ", 87:"AL-A'LA", 88:"AL-GHASHIYAH",
    89:"AL-FAJR", 90:"AL-BALAD", 91:"ASH-SHAMS", 92:"AL-LAYL",
    93:"AD-DUHA", 94:"ASH-SHARH", 95:"AT-TIN", 96:"AL-'ALAQ",
    97:"AL-QADR", 98:"AL-BAYYINAH", 99:"AZ-ZALZALAH", 100:"AL-'ADIYAT",
    101:"AL-QARI'AH", 102:"AT-TAKATHUR", 103:"AL-'ASR", 104:"AL-HUMAZAH",
    105:"AL-FIL", 106:"QURAYSH", 107:"AL-MA'UN", 108:"AL-KAWTHAR",
    109:"AL-KAFIRUN", 110:"AN-NASR", 111:"AL-MASAD", 112:"AL-IKHLAS",
    113:"AL-FALAQ", 114:"AN-NAS",
}


def strip_tags(s: str) -> str:
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
    return html_mod.escape(str(s), quote=False)


def assign_chapter(eid: str, categories: list) -> int:
    if eid in ID_OVERRIDES:
        return ID_OVERRIDES[eid]
    for tag, ch in TAG_PRIORITY:
        if tag in categories:
            return ch
    return 18


def get_entries() -> list:
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    return [e for e in catalog
            if e.get('source') == 'quran' and e['id'] not in EXCLUDE_IDS]


def parse_entries() -> dict:
    raw = QURAN.read_text(encoding='utf-8', errors='ignore')
    pat = r'<div[^>]+class="[^"]*\bentry\b[^"]*"[^>]+id="([^"]+)"[^>]*>'
    opens = list(re.finditer(pat, raw))
    result = {}
    for i, m in enumerate(opens):
        eid = m.group(1)
        end = opens[i+1].start() if i+1 < len(opens) else len(raw)
        chunk = raw[m.start():end]
        bq_matches = re.findall(r'<blockquote[^>]*>(.*?)</blockquote>', chunk, re.DOTALL)
        quote = ''
        if bq_matches:
            parts = []
            for bq in bq_matches:
                q = re.sub(r'<p[^>]*>', '', bq)
                q = re.sub(r'</p>', ' ', q)
                parts.append(strip_tags(q).strip())
            quote = ' / '.join(p for p in parts if p)
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
    chapters = {n: [] for n in CHAPTERS}
    for e in entries:
        ch = assign_chapter(e['id'], e.get('categories', []))
        chapters[ch].append(e)
    for ch in chapters:
        chapters[ch].sort(key=lambda e: STRENGTH_ORDER.get(e.get('strength', ''), 0))
    return chapters


def render_styles() -> str:
    return """
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Montserrat:wght@400;600&family=EB+Garamond:ital,wght@0,400;1,400&display=swap');

:root {
  --bg:         #000000;
  --border:     #1e1e1e;
  --quote-bar:  #2a2a2a;
  --text-body:  #cccccc;
  --text-dim:   #888888;
  --text-faint: #555555;
  --text-ghost: #333333;
  --gold:       #c8963c;
  --white:      #ffffff;
  --red-rule:   #c0392b;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; background: #111; }
body {
  background: #111;
  color: var(--text-body);
  font-family: 'Libre Baskerville', Georgia, serif;
  margin: 0;
  padding: 0;
}
@media screen {
  /* No horizontal padding — pages centre with margin:auto at any window width.
     Navigator is position:fixed so it never displaces the page cards. */
  body { padding: 40px 0; }
}

/* ── Page sections (screen) ── */
.page {
  width: 176mm;
  height: 250mm;
  overflow: hidden;
  margin: 0 auto 24px auto;
  padding: 20mm 18mm 22mm 18mm;
  box-sizing: border-box;
  break-before: page;
  position: relative;
  display: flex;
  flex-direction: column;
  background: #000;
  box-shadow: 0 0 0 1px rgba(200,150,60,0.10), 0 8px 32px rgba(0,0,0,0.8);
}

/* ── Front cover ── */
.front-cover {
  padding: 0;
  overflow: hidden;
  justify-content: flex-start;
}
.cover-strip {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; font-weight: 600;
  color: var(--text-faint);
  letter-spacing: 3px; text-transform: uppercase;
  text-align: center;
  padding: 10mm 18mm 0 18mm;
  margin-bottom: 0;
}
.cover-panels {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.cover-rings {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 200mm; height: 200mm;
  pointer-events: none;
}
.cover-ring {
  position: absolute;
  border-radius: 50%;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  border: 1px solid rgba(200,150,60,0.04);
}
.cover-word-top {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 68px; font-weight: 700;
  color: var(--white);
  line-height: 1;
  text-align: center;
  position: relative; z-index: 1;
  padding-bottom: 10mm;
  border-bottom: 1px solid #1a1a1a;
  width: 100%;
}
.cover-word-bottom {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 68px; font-weight: 700;
  color: var(--white);
  line-height: 1;
  text-align: center;
  position: relative; z-index: 1;
  padding-top: 10mm;
  width: 100%;
}
.cover-sub-block {
  text-align: center;
  padding: 8mm 18mm 10mm 18mm;
  width: 100%;
}
.cover-vol-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; font-weight: 600;
  color: var(--text-faint);
  letter-spacing: 3px; text-transform: uppercase;
  margin-bottom: 6px;
}
.cover-sub-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 16px; font-style: italic;
  color: var(--text-dim);
  margin-bottom: 4px;
}
.cover-tagline {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; font-weight: 600;
  color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase;
  margin-bottom: 12px;
}
.cover-rule {
  border: none; border-top: 1px solid #222;
  width: 48%; margin: 10px auto;
}
.cover-author {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 13px; color: var(--text-dim);
}
.cover-url {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; font-weight: 600;
  color: var(--text-ghost);
  letter-spacing: 2px; text-transform: uppercase;
  margin-top: 6px;
}

/* ── Front matter ── */
.fm-page { background: #000; }
.fm-halftitle {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 22px; font-weight: 700; color: var(--white);
}
.fm-vol {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; font-weight: 600; color: var(--gold);
  letter-spacing: 3px; text-transform: uppercase;
  margin-bottom: 8px;
}
.fm-subtitle {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 13px; font-style: italic; color: var(--text-dim);
  margin-top: 6px;
}
.fm-rule { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
.fm-author {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 13px; color: var(--text-dim); text-align: center;
}
.fm-publisher {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-ghost);
  text-align: center; letter-spacing: 2px; text-transform: uppercase;
  margin-top: 6px;
}
.fm-copyright {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 11px; color: var(--text-dim); line-height: 1.8;
}
.fm-h1 {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 20px; font-weight: 700; color: var(--white); margin-bottom: 18px;
}
.fm-sh {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase;
  margin-top: 16px; margin-bottom: 8px;
}
.fm-p {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 11px; color: var(--text-body); line-height: 1.75; margin-bottom: 10px;
}
.fm-term { font-weight: 700; color: var(--white); }
.fm-strength-basic    { font-weight: 700; color: #4caf50; }
.fm-strength-moderate { font-weight: 700; color: #e07800; }
.fm-strength-strong   { font-weight: 700; color: #e53935; }
.fm-pagenum {
  position: absolute;
  bottom: 22mm; left: 18mm; right: 18mm;
  z-index: 2;
  background: var(--bg);
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-ghost);
  text-align: center;
  padding-top: 12px; border-top: 1px solid var(--border);
}

/* TOC */
.toc-section-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase;
  margin: 16px 0 8px 0;
}
.toc-entry {
  display: flex; align-items: baseline;
  gap: 4px; margin-bottom: 7px;
}
.toc-num {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-faint); min-width: 26px; flex-shrink: 0;
}
.toc-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 11px; color: var(--text-body);
}
.toc-dots {
  flex: 1; border-bottom: 1px dotted #333;
  margin: 0 6px; min-width: 20px;
}
.toc-page {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-faint); white-space: nowrap;
}

/* ── Chapter opener ── */
.chapter-opener { background: #000; }
.ch-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 3px; text-transform: uppercase; margin-bottom: 10px;
}
.ch-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 28px; font-weight: 700; color: var(--white);
  line-height: 1.15; margin-bottom: 14px;
}
.ch-rule { border: none; border-top: 1px solid var(--gold); width: 38%; margin-bottom: 10px; }
.ch-intro {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 10px; font-style: italic; color: var(--text-dim);
  line-height: 1.8; margin-bottom: 20px;
}
.ch-entries-list { margin-top: auto; flex: 1; overflow: hidden; min-height: 0; }
.ch-entry-row {
  display: flex; align-items: baseline; gap: 6px;
  margin-bottom: 5px;
}
.ch-entry-num {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: var(--text-ghost);
  min-width: 18px; flex-shrink: 0;
}
.ch-entry-title {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: #777;
  flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
}
.ch-entry-ref {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; color: var(--text-ghost);
  white-space: nowrap; flex-shrink: 0;
}
.ch-entry-badge {
  font-family: 'Montserrat', sans-serif;
  font-size: 6.5px; font-weight: 600;
  padding: 1px 4px; border-radius: 2px;
  letter-spacing: 0.3px; text-transform: uppercase;
  flex-shrink: 0;
}
.ch-badge-basic    { background: #0b1e0b; color: #4caf50; border: 1px solid #1e4e1e; }
.ch-badge-moderate { background: #1e1000; color: #e07800; border: 1px solid #5a3200; }
.ch-badge-strong   { background: #1e0808; color: #e53935; border: 1px solid #5a1818; }
.ch-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 16px; padding-top: 10px; border-top: 1px solid var(--border);
}
.ch-footer-count {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: var(--text-ghost); letter-spacing: 1px; text-transform: uppercase;
}
.ch-footer-page {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-ghost);
}
.ch-footer-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: var(--text-ghost); letter-spacing: 1px; text-transform: uppercase;
}

/* ── Entry ── */
.entry { background: #000; }
.entry-breadcrumb {
  font-family: 'Montserrat', sans-serif;
  font-size: 8.5px; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase;
  border-bottom: 1px solid #1e1e1e;
  padding-bottom: 8px;
  margin-bottom: 12px;
}
.entry-cont-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 11px; font-style: italic; color: var(--text-dim);
  line-height: 1.35; margin-bottom: 12px;
}
.entry-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 17px; font-weight: 700; color: var(--white);
  line-height: 1.35; margin-bottom: 10px;
}
.entry-tags {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; color: var(--gold);
  letter-spacing: 1px; margin-bottom: 12px;
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
}
.tag-badge {
  background: #0e0e22; color: #7986cb;
  padding: 2px 6px; border-radius: 2px;
  font-size: 8px; font-weight: 600;
  letter-spacing: 0.5px; text-transform: uppercase;
  border: 1px solid #1e1e3a;
}
.tag-strong   { background: #1a0808; color: #e53935; border: 1px solid #5a1818; }
.tag-moderate { background: #1a1000; color: #e07800; border: 1px solid #5a3200; }
.tag-basic    { background: #081a08; color: #4caf50; border: 1px solid #1e4e1e; }
.tag-ref      { color: var(--gold); font-weight: 600; }
.entry-quote {
  font-family: 'EB Garamond', Georgia, serif;
  font-size: 13px; font-style: italic; color: #b8b8b8;
  border-left: 2px solid #2a2a2a;
  padding-left: 14px; margin: 0 0 14px 0; line-height: 1.7;
}
.section-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase;
  margin-top: 12px; margin-bottom: 5px;
}
.section-body {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 11px; color: var(--text-body);
  line-height: 1.75; margin-bottom: 8px;
}
/* Content wrapper — clips all body text before the footer zone.
   flex:1 fills remaining height; overflow:hidden is the hard wall. */
.page-body {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
.entry-pagenum {
  /* Normal flex item at the bottom — never moves, never clipped,
     because .page-body above it takes all remaining space. */
  flex-shrink: 0;
  margin-top: 0;
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-ghost);
  text-align: center;
  padding-top: 12px; border-top: 1px solid var(--border);
}

/* ── Back matter ── */
.back-matter { background: #000; }
.bm-h1 {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 20px; font-weight: 700; color: var(--white); margin-bottom: 6px;
}
.bm-rule { border: none; border-top: 1px solid var(--gold); width: 100%; margin-bottom: 16px; }

/* General Index — single column */
.idx-letter {
  font-family: 'Montserrat', sans-serif;
  font-size: 10px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase;
  margin-top: 14px; margin-bottom: 2px;
  padding-bottom: 4px; border-bottom: 1px solid #1a1a1a;
}
.idx-cat-row {
  display: flex; align-items: baseline; gap: 4px;
  margin-top: 8px; margin-bottom: 2px;
}
.idx-cat-name {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 10px; font-weight: 700; color: var(--gold);
}
.idx-cat-dots { flex: 1; border-bottom: 1px dotted #2a2a2a; margin: 0 6px; }
.idx-cat-page {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--gold); white-space: nowrap;
}
.idx-entry {
  display: flex; align-items: baseline; gap: 4px;
  padding-left: 12px; margin-bottom: 3px;
}
.idx-entry-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 9.5px; color: var(--text-body);
}
.idx-dots { flex: 1; border-bottom: 1px dotted #222; margin: 0 6px; }
.idx-entry-page {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: var(--text-ghost); white-space: nowrap;
}

/* Quran Verse Index — two column */
.vi-columns { columns: 2; column-gap: 16px; }
.vi-surah-header {
  font-family: 'Montserrat', sans-serif;
  font-size: 8.5px; font-weight: 600; color: var(--white);
  letter-spacing: 0.5px;
  margin-top: 10px; margin-bottom: 1px;
  break-after: avoid;
}
.vi-surah-name {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; color: var(--text-faint); letter-spacing: 1px;
}
.vi-entry {
  display: flex; align-items: baseline; gap: 4px; margin-bottom: 2px;
  break-inside: avoid;
}
.vi-ref {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--gold); white-space: nowrap; flex-shrink: 0;
  min-width: 48px;
}
.vi-dots { flex: 1; border-bottom: 1px dotted #222; margin: 0 4px; }
.vi-page {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: var(--text-ghost); white-space: nowrap;
}

/* ── Back cover ── */
.back-cover { background: #000; padding: 16mm 18mm 14mm 18mm; }
.bc-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 24px; font-weight: 700; color: var(--white);
  margin-bottom: 8px;
}
.bc-red-rule { border: none; border-top: 2px solid var(--red-rule); margin-bottom: 6px; }
.bc-subtitle {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase; margin-bottom: 14px;
}
.bc-rule { border: none; border-top: 1px solid #1a1a1a; margin: 12px 0; }
.bc-desc {
  font-family: 'EB Garamond', Georgia, serif;
  font-size: 12px; font-style: italic; color: var(--text-dim);
  line-height: 1.75; margin-bottom: 14px; text-align: center;
}
.bc-bullets { margin-bottom: 16px; }
.bc-bullet {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; color: #4fc3f7;
  margin-bottom: 5px; padding-left: 12px; position: relative;
  line-height: 1.5;
}
.bc-bullet::before {
  content: '·'; position: absolute; left: 0;
  color: #4fc3f7;
}
.bc-bullet .bc-basic    { color: #4caf50; font-weight: 600; }
.bc-bullet .bc-moderate { color: #e07800; font-weight: 600; }
.bc-bullet .bc-strong   { color: #e53935; font-weight: 600; }
.bc-about-heading {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px;
}
.bc-about-body {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 9.5px; color: var(--text-dim); line-height: 1.7;
  text-align: center; margin-bottom: 12px;
}
.bc-bottom {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-top: auto; padding-top: 10px; border-top: 1px solid #1a1a1a;
}
.bc-isbn {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: var(--text-ghost);
}
.bc-price {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: var(--text-ghost); text-align: right;
}

/* ── Right-side navigator ── */
#page-nav {
  position: fixed; right: 0; top: 0;
  width: 34px; height: 100vh;
  display: flex; flex-direction: column; align-items: center;
  padding: 8px 0;
  background: #050505;
  border-left: 1px solid #111;
  z-index: 100;
}
#pn-counter {
  font-family: 'Montserrat', sans-serif;
  font-size: 6px; color: #444;
  margin-bottom: 6px; letter-spacing: 0.5px;
  text-align: center; white-space: pre;
}
#pn-track {
  flex: 1; width: 8px;
  background: #0d0d0d;
  border-radius: 4px;
  border: 1px solid #1a1a1a;
  position: relative; overflow: hidden;
}
.pn-tick {
  position: absolute; left: 0; right: 0;
  height: 1px; background: #1e1e1e; cursor: pointer;
}
.pn-tick.chapter-mark { background: #333; height: 2px; }
.pn-tick.active  { background: var(--gold); }
#pn-thumb {
  position: absolute; left: 0; right: 0;
  height: 18px;
  background: rgba(200,150,60,0.12);
  border: 1px solid rgba(200,150,60,0.4);
  border-radius: 3px; pointer-events: none;
}

/* ── Print ── */
@page { size: 176mm 250mm; margin: 0; }
@media print {
  html { background: #000; margin: 0; padding: 0; }
  body { background: #000; padding: 0; margin: 0; width: 176mm; }

  /* Fixed B5 height — flex from screen CSS keeps cover/opener layouts intact.
     margin: 0 auto centres the page in whatever width Chromium allocates. */
  .page {
    box-shadow: none;
    margin: 0 auto;
    padding: 20mm 18mm 22mm 18mm;
    width: 176mm;
    height: 250mm;
    overflow: hidden;
  }

  .front-cover, .back-cover { padding: 0; }
  #page-nav { display: none; }
}
"""


def render_front_matter(chapters: dict, ch_start_pages: dict) -> list:
    """Return 7 HTML strings: front-cover, half-title, title, copyright, TOC, foreword, abbreviations."""

    # ── Front cover ──
    rings_html = ''
    for size in [60, 90, 120, 150, 180]:
        rings_html += f'<div class="cover-ring" style="width:{size}mm;height:{size}mm;"></div>\n'

    s_cover = f'''
<section class="page front-cover" id="fm-cover" data-page="">
  <div class="cover-strip">Analyzing Islam &nbsp;&middot;&nbsp; Volume I &nbsp;&middot;&nbsp; The Quran</div>
  <div class="cover-panels">
    <div class="cover-rings">{rings_html}</div>
    <div class="cover-word-top">Analyzing</div>
    <div class="cover-word-bottom">Islam</div>
  </div>
  <div class="cover-sub-block">
    <div class="cover-vol-label">Volume I</div>
    <div class="cover-sub-title">The Quran</div>
    <div class="cover-tagline">A Critical Reference Guide</div>
    <div class="cover-rule"></div>
    <div class="cover-author">G.J. van Vuuren</div>
    <div class="cover-rule"></div>
    <div class="cover-url">analyzingislam.com</div>
  </div>
</section>'''

    # ── i: Half-title ──
    s_halftitle = '''
<section class="page fm-page" id="fm-halftitle" data-page="i">
  <div style="margin-top:auto;margin-bottom:auto;padding-bottom:30mm;">
    <div class="fm-vol">Volume I</div>
    <div class="fm-halftitle">Analyzing Islam</div>
    <div class="fm-subtitle">The Quran</div>
  </div>
  <div class="fm-pagenum">i</div>
</section>'''

    # ── ii: Title page ──
    s_title = '''
<section class="page fm-page" id="fm-title" data-page="ii">
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:0;text-align:center;">
    <div class="fm-halftitle">Analyzing Islam</div>
    <div class="fm-vol" style="margin-top:10px;">Volume I &mdash; The Quran</div>
    <div class="fm-subtitle" style="font-size:11px;margin-top:4px;color:#666;">A Critical Reference Guide</div>
    <hr class="fm-rule" style="width:50%;margin:28px auto;">
    <div class="fm-author">G.J. van Vuuren</div>
    <hr class="fm-rule" style="width:50%;margin:28px auto;">
    <div class="fm-publisher">analyzingislam.com</div>
  </div>
  <div class="fm-pagenum">ii</div>
</section>'''

    # ── iii: Copyright ──
    s_copyright = '''
<section class="page fm-page" id="fm-copyright" data-page="iii">
  <div style="margin-top:auto;">
    <p class="fm-copyright">Analyzing Islam &mdash; Volume I: The Quran</p>
    <p class="fm-copyright">A Critical Reference Guide</p>
    <p class="fm-copyright" style="margin-top:14px;">&copy; 2026 Analyzing Islam. All rights reserved.<br>analyzingislam.com</p>
    <hr class="fm-rule" style="margin:16px 0;">
    <p class="fm-copyright">First edition, 2026.</p>
    <p class="fm-copyright" style="margin-top:10px;">
      All Quranic verses are quoted from the <em>Saheeh International</em> English
      translation. This volume covers the Quran exclusively. Hadith collections &mdash; Sahih
      al-Bukhari, Sahih Muslim, and the four Sunan &mdash; are examined in subsequent volumes.
    </p>
    <p class="fm-copyright" style="margin-top:10px;">
      No part of this publication may be reproduced or transmitted in any form without prior
      written permission from the publisher, except for brief quotations in reviews or scholarly
      work with full attribution.
    </p>
    <p class="fm-copyright" style="margin-top:10px;">Every entry references a specific verse &mdash; verify before citing.</p>
  </div>
  <div class="fm-pagenum">iii</div>
</section>'''

    # ── iv: TOC ──
    toc_rows = f'''
  <div class="toc-entry" style="margin-bottom:12px;">
    <span class="toc-num"></span>
    <span class="toc-title" style="color:#666;font-size:10px;font-style:italic;">Foreword</span>
    <span class="toc-dots"></span>
    <span class="toc-page" style="color:#555;">v</span>
  </div>
  <div class="toc-entry" style="margin-bottom:18px;">
    <span class="toc-num"></span>
    <span class="toc-title" style="color:#666;font-size:10px;font-style:italic;">Abbreviations &amp; Reference Guide</span>
    <span class="toc-dots"></span>
    <span class="toc-page" style="color:#555;">viii</span>
  </div>
  <div class="toc-section-label">The Quran &nbsp;&mdash;&nbsp; 262 entries across 22 chapters</div>'''

    for ch_num in sorted(chapters.keys()):
        if not chapters[ch_num]:
            continue
        ch_name, _ = CHAPTERS[ch_num]
        pg = ch_start_pages.get(ch_num, '&mdash;')
        toc_rows += f'''
  <div class="toc-entry">
    <span class="toc-num">{ch_num}</span>
    <span class="toc-title">{esc(ch_name)}</span>
    <span class="toc-dots"></span>
    <span class="toc-page">{pg}</span>
  </div>'''

    toc_rows += '''
  <div class="toc-section-label" style="margin-top:14px;">Back Matter</div>
  <div class="toc-entry">
    <span class="toc-num"></span>
    <span class="toc-title" style="color:#666;font-style:italic;">General Index</span>
    <span class="toc-dots"></span>
    <span class="toc-page" style="color:#555;">&mdash;</span>
  </div>
  <div class="toc-entry">
    <span class="toc-num"></span>
    <span class="toc-title" style="color:#666;font-style:italic;">Quran Verse Index</span>
    <span class="toc-dots"></span>
    <span class="toc-page" style="color:#555;">&mdash;</span>
  </div>'''

    s_toc = f'''
<section class="page fm-page" id="fm-toc" data-page="iv">
  <h2 class="fm-h1">Contents</h2>
  <hr class="fm-rule" style="margin-bottom:16px;">
  {toc_rows}
  <div class="fm-pagenum">iv</div>
</section>'''

    # ── v: Foreword ──
    s_foreword = '''
<section class="page fm-page" id="fm-foreword" data-page="v">
  <h2 class="fm-h1">Foreword</h2>

  <div class="fm-sh">WHAT THIS IS</div>
  <p class="fm-p">
    This book is a reference catalog of passages from the Quran that present philosophical,
    historical, moral, or logical difficulties. Every entry cites a specific verse, explains
    what it says in plain language, and builds the case for why it presents a problem. Where
    relevant, entries also present the standard Muslim apologetic response and push back on it.
  </p>
  <p class="fm-p">
    Volume I covers one source: the Quran &mdash; the text that Islam itself holds to be the
    direct, unaltered word of Allah. No fringe interpretations. No hostile translations. The
    case is built entirely from Islam&rsquo;s own most authoritative scripture as rendered in its
    most widely endorsed English edition.
  </p>

  <div class="fm-sh">HOW ENTRIES ARE ORGANISED</div>
  <p class="fm-p">
    Entries are grouped into 22 thematic chapters &mdash; Abrogation, Contradictions, Warfare &amp;
    Jihad, Women &amp; Sexual Issues, and so on. Each chapter collects every entry that belongs to
    that theme. When an entry touches more than one theme, it appears under the category that
    best captures its primary problem.
  </p>

  <div class="fm-sh">HOW TO READ AN ENTRY</div>
  <p class="fm-p">Each entry contains four elements:</p>
  <table style="width:100%;border-collapse:collapse;margin-bottom:10px;">
    <tr>
      <td style="font-family:\'Montserrat\',sans-serif;font-size:8px;font-weight:600;color:#555;letter-spacing:1px;text-transform:uppercase;padding:4px 10px 4px 0;white-space:nowrap;vertical-align:top;">REFERENCE</td>
      <td class="fm-p" style="margin:0;padding:2px 0;">The Quran citation &mdash; surah and verse number.</td>
    </tr>
    <tr>
      <td style="font-family:\'Montserrat\',sans-serif;font-size:8px;font-weight:600;color:#555;letter-spacing:1px;text-transform:uppercase;padding:4px 10px 4px 0;white-space:nowrap;vertical-align:top;">RATING</td>
      <td class="fm-p" style="margin:0;padding:2px 0;">The apologetic difficulty level: Basic, Moderate, or Strong.</td>
    </tr>
    <tr>
      <td style="font-family:\'Montserrat\',sans-serif;font-size:8px;font-weight:600;color:#555;letter-spacing:1px;text-transform:uppercase;padding:4px 10px 4px 0;white-space:nowrap;vertical-align:top;">PASSAGE</td>
      <td class="fm-p" style="margin:0;padding:2px 0;">The verse quoted in full from the Saheeh International translation.</td>
    </tr>
    <tr>
      <td style="font-family:\'Montserrat\',sans-serif;font-size:8px;font-weight:600;color:#555;letter-spacing:1px;text-transform:uppercase;padding:4px 10px 4px 0;white-space:nowrap;vertical-align:top;">COMMENTARY</td>
      <td class="fm-p" style="margin:0;padding:2px 0;">What it says, why it matters, and where the standard apologetic falls short.</td>
    </tr>
  </table>

  <div class="fm-pagenum">v</div>
</section>'''

    # ── viii: Abbreviations ──
    s_abbr = '''
<section class="page fm-page" id="fm-abbr" data-page="viii">
  <h2 class="fm-h1">Abbreviations &amp; Reference Guide</h2>
  <p class="fm-p" style="color:#555;font-size:9px;letter-spacing:1px;text-transform:uppercase;font-family:\'Montserrat\',sans-serif;margin-bottom:14px;">
    Citations, Terminology, and Rating System &mdash; Volume I: The Quran
  </p>

  <div class="fm-sh">CITATION FORMAT</div>
  <p class="fm-p">
    <span class="fm-term">Q 4:34</span>
    &nbsp; Quran, Surah 4 (An-Nisa), Verse 34. All Quranic citations follow this
    surah:verse format. Where a range of verses is relevant, it appears as Q 9:5&ndash;6.
    All quotations are from the Saheeh International English translation.
  </p>

  <div class="fm-sh">STRENGTH RATINGS</div>
  <p class="fm-p">
    <span class="fm-strength-basic">Basic</span>
    &nbsp; Apologists have a stock reply. The problem is real but the standard response
    is widely known and rehearsed.
  </p>
  <p class="fm-p">
    <span class="fm-strength-moderate">Moderate</span>
    &nbsp; Answering requires conceding something &mdash; softening a claim or reinterpreting the text.
  </p>
  <p class="fm-p">
    <span class="fm-strength-strong">Strong</span>
    &nbsp; Apologetic moves generate new problems. Every standard response requires
    abandoning the plain meaning of the text or contradicts another Islamic claim.
  </p>

  <div class="fm-sh">QURANIC TERMINOLOGY</div>
  <p class="fm-p"><span class="fm-term">Ayah (pl. Ayat)</span> &nbsp; A verse of the Quran; literally &ldquo;a sign&rdquo;</p>
  <p class="fm-p"><span class="fm-term">Surah</span> &nbsp; A chapter of the Quran; there are 114 in total</p>
  <p class="fm-p"><span class="fm-term">Meccan</span> &nbsp; Revealed while Muhammad was in Mecca (c. 610&ndash;622 CE)</p>
  <p class="fm-p"><span class="fm-term">Medinan</span> &nbsp; Revealed while Muhammad was in Medina (c. 622&ndash;632 CE)</p>
  <p class="fm-p"><span class="fm-term">Naskh</span> &nbsp; Abrogation &mdash; the doctrine that later verses can cancel earlier ones</p>
  <p class="fm-p"><span class="fm-term">Tafsir</span> &nbsp; Quranic exegesis or commentary</p>
  <p class="fm-p"><span class="fm-term">Asbab al-Nuzul</span> &nbsp; The &ldquo;occasions of revelation&rdquo; &mdash; historical circumstances</p>

  <div class="fm-sh">ARABIC &amp; ISLAMIC TERMINOLOGY</div>
  <p class="fm-p"><span class="fm-term">Fiqh</span> &nbsp; Islamic jurisprudence &mdash; legal rulings derived from Quran and hadith</p>
  <p class="fm-p"><span class="fm-term">Dhimmi</span> &nbsp; A non-Muslim subject living under Islamic rule</p>
  <p class="fm-p"><span class="fm-term">Hudud</span> &nbsp; Fixed Quranic punishments &mdash; amputation, stoning, lashing</p>
  <p class="fm-p"><span class="fm-term">Jizya</span> &nbsp; A tax levied on non-Muslims under Islamic governance (Q 9:29)</p>
  <p class="fm-p"><span class="fm-term">Tahrif</span> &nbsp; The Islamic claim that Jews and Christians corrupted their scriptures</p>
  <p class="fm-p"><span class="fm-term">Ma malakat aymanukum</span> &nbsp; &ldquo;What your right hands possess&rdquo; &mdash; enslaved people and captives</p>

  <div class="fm-pagenum">viii</div>
</section>'''

    return [s_cover, s_halftitle, s_title, s_copyright, s_toc, s_foreword, s_abbr]


def render_chapter_opener(ch_num: int, entries: list, section_idx: int) -> str:
    ch_name, ch_intro = CHAPTERS[ch_num]
    count_label = f"{len(entries)} {'entry' if len(entries) == 1 else 'entries'}"

    entry_rows = ''
    for i, e in enumerate(entries, 1):
        title = e['title']
        if len(title) > 62:
            title = title[:62] + '…'
        strength = e.get('strength', 'basic')
        badge_cls = f'ch-badge-{strength}'
        badge_lbl = STRENGTH_LABEL.get(strength, 'BASIC')
        ref = e.get('ref', '')
        entry_rows += (
            f'<div class="ch-entry-row">'
            f'<span class="ch-entry-num">{i}.</span>'
            f'<span class="ch-entry-title">{esc(title)}</span>'
            f'<span class="ch-entry-ref">{esc(ref)}</span>'
            f'<span class="ch-entry-badge {badge_cls}">{badge_lbl}</span>'
            f'</div>\n'
        )

    return f'''
<section class="page chapter-opener" id="s{section_idx}" data-page="{section_idx}" data-chapter="{ch_num}">
  <div class="ch-label">Chapter {ch_num}</div>
  <h1 class="ch-title">{esc(ch_name)}</h1>
  <hr class="ch-rule">
  <p class="ch-intro">{esc(ch_intro)}</p>
  <div class="ch-entries-list">
    {entry_rows}
  </div>
  <div class="ch-footer">
    <span class="ch-footer-count">{count_label}</span>
    <span class="ch-footer-page">{section_idx}</span>
    <span class="ch-footer-label">The Quran</span>
  </div>
</section>'''


# Base body-text character budget for page 1 of a split entry.
# Page content area: (250-20-22) mm = 208 mm ≈ 787 px at 96 dpi.
# Fixed overhead (breadcrumb, title, tags, 4 labels) ≈ 207 px.
# Footer is now position:absolute so it doesn't reduce the flex budget.
# Average quote (4 lines EB Garamond 11 px lh 1.75) ≈ 77 px.
# Available for body: 787-207-77 = 503 px / 16.5 px/line x 80 char/line ≈ 2440.
# Use 2200 — fills the page without overrunning into the footer zone.
# _split_body subtracts half the quote char-count for long verses automatically.
_BODY_SPLIT_CHARS = 2200

_BODY_SECTIONS = [
    ('WHAT THE VERSE SAYS',   'says'),
    ('WHY THIS IS A PROBLEM', 'problem'),
    ('THE MUSLIM RESPONSE',   'response'),
    ('WHY IT FAILS',          'fails'),
]


def _flatten_body(sec: dict) -> list:
    """Return flat list of ('head', label) | ('para', text) for all body sections."""
    items = []
    for label, key in _BODY_SECTIONS:
        body = sec.get(key, '').strip()
        if not body:
            continue
        items.append(('head', label))
        for p in body.split('\n\n'):
            p = p.strip()
            if p:
                items.append(('para', p))
    return items


def _render_flat(items: list) -> str:
    """Render flat body-item list to HTML."""
    out = ''
    for typ, text in items:
        if typ == 'head':
            out += f'<div class="section-label">{text}</div>\n'
        else:
            out += f'<p class="section-body">{esc(text)}</p>\n'
    return out


def _find_sentence_split(text: str, target: int) -> int:
    """
    Find the best position to split `text` so page 1 gets ~`target` chars.

    Searches backward from ~105 % of target to ~70 % of target for a
    sentence-ending punctuation mark (. ! ?) followed by a space (or end of
    string).  Falls back to the nearest word boundary in the same window.

    Returns the index where page 2 starts (the first char of the continuation),
    or 0 if no good split was found in the window (caller puts whole paragraph
    on page 2 and keeps the threshold budget for earlier paragraphs).
    """
    n = len(text)
    if target >= n:
        return 0  # whole paragraph fits — no split needed here

    lo = max(0, int(target * 0.70))
    hi = min(n, int(target * 1.05))

    # Scan backward from hi for sentence-ending punctuation
    for i in range(hi, lo, -1):
        if text[i - 1] in '.!?' and (i == n or text[i] == ' '):
            # Skip any spaces after the punctuation so page 2 starts cleanly
            j = i
            while j < n and text[j] == ' ':
                j += 1
            return j

    # Fall back: word boundary (space)
    for i in range(min(target, n - 1), lo, -1):
        if text[i] == ' ':
            return i + 1

    return 0  # no suitable split in window


def _split_body(sec: dict) -> tuple:
    """
    Split entry body at SENTENCE boundaries within paragraphs.
    Returns (p1_html, p2_html).  p2_html == '' when all content fits on one page.

    Rules
    -----
    • Greedy: fill page 1 with whole paragraphs until the next one would push
      past the threshold.  Always keep at least the first paragraph on page 1.
    • When a paragraph overflows, try to split it MID-SENTENCE near the
      remaining budget using _find_sentence_split().  Page 1 ends with the
      sentence fragment; page 2 starts with the next sentence.
    • If no sentence split is found, the whole overflowing paragraph goes to
      page 2 and the split happens at the preceding paragraph boundary.
    • Page 1 must NOT end on a bare section header — walk back if needed.
    • Page 2 continues exactly where page 1 stopped; no repeated header.
    """
    flat = _flatten_body(sec)
    if not flat:
        return '', ''

    # Compensate for long quotes: subtract half the quote character count.
    # Reduce threshold for:
    #  • long quotes  (each quote char ≈ ¾ body char of vertical space)
    #  • section headers (label + margins ≈ 100 char-equivalents each)
    quote_chars = len(sec.get('quote', ''))
    n_sections  = sum(1 for _, key in _BODY_SECTIONS if sec.get(key, '').strip())
    threshold   = max(600, _BODY_SPLIT_CHARS
                      - quote_chars * 3 // 4
                      - n_sections * 100)

    total_para = sum(len(t) for typ, t in flat if typ == 'para')
    if total_para <= threshold:
        return _render_flat(flat), ''

    # ── Greedy fill ───────────────────────────────────────────────────────────
    p1_chars  = 0
    got_para  = False
    split_at  = len(flat)   # flat index where page 2 starts
    mid_split = None        # (flat_idx, char_offset) when splitting mid-para

    for i, (typ, text) in enumerate(flat):
        if typ != 'para':
            continue

        if not got_para:
            # Always put the first paragraph on page 1
            p1_chars += len(text)
            got_para = True
            continue

        if p1_chars + len(text) <= threshold:
            p1_chars += len(text)
        else:
            # This paragraph overflows — try a mid-sentence split
            remaining = threshold - p1_chars
            char_off  = _find_sentence_split(text, remaining)
            if char_off > 0:
                mid_split = (i, char_off)
            split_at = i
            break

    # ── Mid-paragraph split ───────────────────────────────────────────────────
    if mid_split is not None:
        flat_idx, char_off = mid_split
        para_text = flat[flat_idx][1]
        p1_para   = para_text[:char_off].rstrip()
        p2_para   = para_text[char_off:].lstrip()

        p1_items = list(flat[:flat_idx])
        if p1_para:
            p1_items.append(('para', p1_para))

        p2_items = []
        if p2_para:
            p2_items.append(('para', p2_para))
        p2_items.extend(flat[flat_idx + 1:])

        if not p2_items:
            return _render_flat(flat), ''
        return _render_flat(p1_items), _render_flat(p2_items)

    # ── Paragraph-boundary split ──────────────────────────────────────────────
    # Page 1 must not end on a header
    while split_at > 0 and flat[split_at - 1][0] == 'head':
        split_at -= 1

    # Failsafe: guarantee at least one paragraph on page 1
    if split_at == 0:
        for i, (typ, _) in enumerate(flat):
            if typ == 'para':
                split_at = i + 1
                break

    p2 = flat[split_at:]
    if not p2:
        return _render_flat(flat), ''
    return _render_flat(flat[:split_at]), _render_flat(p2)


def render_entry(meta: dict, sections_data: dict, ch_num: int, section_idx: int) -> str:
    eid      = meta['id']
    title    = meta['title']
    ref      = meta['ref']
    strength = meta.get('strength', 'basic')
    cats     = meta.get('categories', [])
    sec      = sections_data.get(eid, {})
    ch_name, _ = CHAPTERS.get(ch_num, (str(ch_num), ''))
    breadcrumb = f'THE QURAN  ·  CHAPTER {ch_num}  ·  {ch_name.upper()}'

    cat_badges = ''.join(
        f'<span class="tag-badge">{esc(c.upper().replace("-", " "))}</span> '
        for c in cats[:2]
    )
    strength_cls = STRENGTH_CSS.get(strength, 'tag-basic')
    strength_lbl = STRENGTH_LABEL.get(strength, 'BASIC')
    tags_html = (
        f'{cat_badges}'
        f'<span class="tag-badge {strength_cls}">{strength_lbl}</span> '
        f'<span class="tag-ref">{esc(ref)}</span>'
    )

    quote = sec.get('quote', '').strip()
    quote_html = (
        f'<blockquote class="entry-quote">&ldquo;{esc(quote)}&rdquo;</blockquote>'
        if quote else ''
    )

    # ── Split body at paragraph level ─────────────────────────────────────────
    content_p1, content_p2 = _split_body(sec)

    # ── Page 1 ────────────────────────────────────────────────────────────────
    page1 = f'''
<section class="page entry" id="s{section_idx}" data-page="{section_idx}" data-chapter="{ch_num}">
  <div class="page-body">
    <div class="entry-breadcrumb">{esc(breadcrumb)}</div>
    <h2 class="entry-title">{esc(title)}</h2>
    <div class="entry-tags">{tags_html}</div>
    {quote_html}
    {content_p1}
  </div>
  <div class="entry-pagenum">{section_idx}</div>
</section>'''

    if not content_p2:
        return page1

    # ── Page 2 (continuation — same breadcrumb, no repeated title) ───────────
    page2 = f'''
<section class="page entry entry-continuation" id="s{section_idx}c" data-page="{section_idx}" data-chapter="{ch_num}">
  <div class="page-body">
    <div class="entry-breadcrumb">{esc(breadcrumb)}</div>
    {content_p2}
  </div>
  <div class="entry-pagenum">{section_idx}</div>
</section>'''

    return page1 + page2


def render_general_index(chapters: dict, section_idx: int) -> str:
    """General Index — alphabetical by chapter name with letter dividers, single column."""
    # Build sorted list of (ch_num, ch_name, entries)
    sorted_chs = sorted(
        [(ch_num, CHAPTERS[ch_num][0], chapters[ch_num])
         for ch_num in chapters if chapters[ch_num]],
        key=lambda x: x[1].upper()
    )

    rows = ''
    current_letter = ''
    for ch_num, ch_name, ch_entries in sorted_chs:
        letter = ch_name[0].upper()
        if letter != current_letter:
            current_letter = letter
            rows += f'<div class="idx-letter">{letter}</div>\n'

        rows += (
            f'<div class="idx-cat-row">'
            f'<span class="idx-cat-name">{esc(ch_name)}</span>'
            f'<span class="idx-cat-dots"></span>'
            f'<span class="idx-cat-page">{section_idx - (section_idx - ch_num * 12)}</span>'
            f'</div>\n'
        )
        for e in ch_entries:
            title = e['title']
            if len(title) > 72:
                title = title[:72] + '…'
            rows += (
                f'<div class="idx-entry">'
                f'<span class="idx-entry-title">{esc(title)}</span>'
                f'<span class="idx-dots"></span>'
                f'<span class="idx-entry-page">{esc(e["ref"])}</span>'
                f'</div>\n'
            )

    return f'''
<section class="page back-matter" id="s{section_idx}" data-page="{section_idx}">
  <h2 class="bm-h1">General Index</h2>
  <hr class="bm-rule">
  {rows}
  <div class="entry-pagenum">{section_idx}</div>
</section>'''


def render_verse_index(entries: list, section_idx: int) -> str:
    """Quran Verse Index — two columns, grouped by surah with surah names."""
    def sort_key(e: dict) -> tuple:
        m = re.search(r'(?:Q|Quran)\s*(\d+):(\d+)', e['ref'])
        if m:
            return (int(m.group(1)), int(m.group(2)))
        return (9999, 0)

    sorted_entries = sorted(entries, key=sort_key)

    # Group by surah
    surah_groups: dict = {}
    for e in sorted_entries:
        m = re.search(r'(?:Q|Quran)\s*(\d+):', e['ref'])
        sn = int(m.group(1)) if m else 9999
        surah_groups.setdefault(sn, []).append(e)

    rows = ''
    for sn in sorted(surah_groups.keys()):
        surah_name = SURAH_NAMES.get(sn, '')
        rows += (
            f'<div class="vi-surah-header" style="break-inside:avoid;">'
            f'Surah {sn}'
            f'<br><span class="vi-surah-name">{esc(surah_name)}</span>'
            f'</div>\n'
        )
        for e in surah_groups[sn]:
            ref_short = re.sub(r'^Quran\s+', 'Q ', e['ref'])
            rows += (
                f'<div class="vi-entry">'
                f'<span class="vi-ref">{esc(ref_short)}</span>'
                f'<span class="vi-dots"></span>'
                f'<span class="vi-page">{esc(e["ref"])}</span>'
                f'</div>\n'
            )

    return f'''
<section class="page back-matter" id="s{section_idx}" data-page="{section_idx}">
  <h2 class="bm-h1">Quran Verse Index</h2>
  <p style="font-family:\'Montserrat\',sans-serif;font-size:8px;color:#555;letter-spacing:1px;text-transform:uppercase;margin-bottom:12px;">
    Volume I &nbsp;&middot;&nbsp; The Quran &nbsp;&middot;&nbsp; All 262 Entries
  </p>
  <hr class="bm-rule">
  <div class="vi-columns">
    {rows}
  </div>
  <div class="entry-pagenum">{section_idx}</div>
</section>'''


def render_back_cover() -> str:
    """Back cover page."""
    return '''
<section class="page back-cover" id="fm-backcover" data-page="">
  <h2 class="bc-title">Analyzing Islam</h2>
  <div class="bc-red-rule"></div>
  <div class="bc-subtitle">Volume I &nbsp;&middot;&nbsp; The Quran &nbsp;&middot;&nbsp; A Critical Reference Guide</div>
  <hr class="bc-rule">

  <p class="bc-desc">
    A structured reference guide to the Quran &mdash; Islam&rsquo;s central divine text,
    comprising 114 surahs and 6,236 verses. Each of the 262 entries presents a specific verse
    exactly as it appears in the authoritative Saheeh International translation, examines its
    context and significance, surveys the standard Muslim apologetic response, and explains
    precisely where that response falls short.
  </p>

  <div class="bc-bullets">
    <div class="bc-bullet">262 entries organised across 22 chapters</div>
    <div class="bc-bullet">All quotations from the Saheeh International English translation</div>
    <div class="bc-bullet">Strength ratings &mdash; <span class="bc-basic">Basic</span>, <span class="bc-moderate">Moderate</span>, <span class="bc-strong">Strong</span> &mdash; for every argument</div>
    <div class="bc-bullet">Cross-referenced General Index and Quran Verse Index</div>
    <div class="bc-bullet">Designed for researchers, apologists, and informed general readers</div>
  </div>

  <hr class="bc-rule">

  <div class="bc-about-heading">About AnalyzingIslam.com</div>
  <p class="bc-about-body">
    AnalyzingIslam.com is an independent reference platform dedicated to the close examination
    of Islamic primary texts. Drawing on classical Arabic sources, academic scholarship, and
    direct textual analysis, it presents the most significant challenges to Islamic truth claims
    in a structured, accessible format.
  </p>

  <div class="bc-bottom">
    <div class="bc-isbn">
      <div style="font-size:20px;letter-spacing:2px;color:#333;margin-bottom:4px;">|||||||||||||</div>
      ISBN 978-0-000-00000-0
    </div>
    <div class="bc-price">
      $xx.xx / &pound;xx.xx<br>
      analyzingislam.com
    </div>
  </div>
</section>'''


def render_navigator(all_section_ids: list, chapter_section_ids: set) -> str:
    total = len(all_section_ids)

    ticks_html = ''
    for i, sid in enumerate(all_section_ids):
        pct = (i / (total - 1) * 100) if total > 1 else 0
        extra_cls = ' chapter-mark' if sid in chapter_section_ids else ''
        ticks_html += (
            f'<div class="pn-tick{extra_cls}" '
            f'data-idx="{i}" data-sid="{sid}" '
            f'style="top:{pct:.3f}%"></div>\n'
        )

    js = f"""
(function() {{
  var sections = Array.from(document.querySelectorAll('section.page'));
  var track   = document.getElementById('pn-track');
  var counter = document.getElementById('pn-counter');
  var thumb   = document.getElementById('pn-thumb');
  var total   = {total};

  track.querySelectorAll('.pn-tick').forEach(function(tick) {{
    tick.addEventListener('click', function(e) {{
      e.stopPropagation();
      var sid = tick.dataset.sid;
      var target = document.getElementById(sid);
      if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }});
  }});

  track.addEventListener('click', function(e) {{
    if (e.target === track) {{
      var rect = track.getBoundingClientRect();
      var pct  = (e.clientY - rect.top) / rect.height;
      var idx  = Math.round(pct * (sections.length - 1));
      if (sections[idx]) sections[idx].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}
  }});

  function setActive(idx) {{
    var sec = sections[idx];
    if (!sec) return;
    var pg = sec.dataset.page || (idx + 1);
    counter.textContent = pg + '\\n/ ' + total;
    var pct = total > 1 ? (idx / (total - 1) * 100) : 0;
    thumb.style.top = pct.toFixed(2) + '%';
    var prev = track.querySelector('.pn-tick.active');
    if (prev) prev.classList.remove('active');
    var next = track.querySelector('.pn-tick[data-idx="' + idx + '"]');
    if (next) next.classList.add('active');
  }}

  var io = new IntersectionObserver(function(entries) {{
    entries.forEach(function(entry) {{
      if (entry.isIntersecting) {{
        var idx = sections.indexOf(entry.target);
        if (idx >= 0) setActive(idx);
      }}
    }});
  }}, {{ threshold: 0.15, rootMargin: '-20% 0px -20% 0px' }});

  sections.forEach(function(sec) {{ io.observe(sec); }});
  setActive(0);
}})();
"""

    return f'''
<div id="page-nav">
  <div id="pn-counter">1&#10;/ {total}</div>
  <div id="pn-track">
    {ticks_html}
    <div id="pn-thumb"></div>
  </div>
</div>
<script>
{js}
</script>'''


def main():
    print("Loading entries…")
    entries       = get_entries()
    sections_data = parse_entries()
    chapters      = build_chapters(entries)

    non_empty = sum(1 for v in chapters.values() if v)
    print(f"  {len(entries)} entries across {non_empty} chapters")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Assign section indices ────────────────────────────────────────────────
    FM_IDS = ['fm-cover', 'fm-halftitle', 'fm-title', 'fm-copyright',
              'fm-toc', 'fm-foreword', 'fm-abbr']
    FM_COUNT = len(FM_IDS)

    all_section_ids     = list(FM_IDS)
    chapter_section_ids = set()
    ch_start_pages      = {}
    ch_sections         = []

    body_idx = FM_COUNT
    for ch_num in sorted(chapters.keys()):
        ch_entries = chapters[ch_num]
        if not ch_entries:
            continue

        ch_start_pages[ch_num] = body_idx
        section_id = f's{body_idx}'
        all_section_ids.append(section_id)
        chapter_section_ids.add(section_id)
        ch_sections.append(('opener', ch_num, ch_entries, body_idx))
        body_idx += 1

        for e in ch_entries:
            section_id = f's{body_idx}'
            all_section_ids.append(section_id)
            ch_sections.append(('entry', ch_num, e, body_idx))
            body_idx += 1

    # Back matter: 2 index sections + back cover
    genidx_idx  = body_idx; all_section_ids.append(f's{body_idx}'); body_idx += 1
    versidx_idx = body_idx; all_section_ids.append(f's{body_idx}'); body_idx += 1
    all_section_ids.append('fm-backcover')

    total_sections = len(all_section_ids)
    print(f"  {total_sections} total sections")

    # ── Render ────────────────────────────────────────────────────────────────
    print("Rendering front matter…")
    fm_sections = render_front_matter(chapters, ch_start_pages)

    print("Rendering body sections…")
    body_parts = []
    for item in ch_sections:
        kind = item[0]
        if kind == 'opener':
            _, ch_num, ch_entries, idx = item
            body_parts.append(render_chapter_opener(ch_num, ch_entries, idx))
        else:
            _, ch_num, entry, idx = item
            body_parts.append(render_entry(entry, sections_data, ch_num, idx))

    print("Rendering back matter…")
    genidx_html   = render_general_index(chapters, genidx_idx)
    versidx_html  = render_verse_index(entries, versidx_idx)
    backcover_html = render_back_cover()

    # ── Assemble ──────────────────────────────────────────────────────────────
    print("Assembling book.html…")
    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Analyzing Islam — Volume I: The Quran</title>
  <style>
{render_styles()}
  </style>
</head>
<body>

{''.join(fm_sections)}

{''.join(body_parts)}

{genidx_html}
{versidx_html}
{backcover_html}

{render_navigator(all_section_ids, chapter_section_ids)}
</body>
</html>"""

    OUT.write_text(html_out, encoding='utf-8')
    size_mb = OUT.stat().st_size / 1_048_576
    print(f"Done -> {OUT}  ({size_mb:.1f} MB, {total_sections} sections)")


if __name__ == '__main__':
    main()
