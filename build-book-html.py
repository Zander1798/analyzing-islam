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
    """Assign entries to chapters and sort basic→moderate→strong within each."""
    chapters = {n: [] for n in CHAPTERS}
    for e in entries:
        ch = assign_chapter(e['id'], e.get('categories', []))
        chapters[ch].append(e)
    for ch in chapters:
        chapters[ch].sort(key=lambda e: STRENGTH_ORDER.get(e.get('strength', ''), 0))
    return chapters


def render_styles() -> str:
    """Return the full CSS for the book as a <style> block string."""
    return """
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Montserrat:wght@400;600&family=EB+Garamond:ital,wght@0,400;1,400&display=swap');

:root {
  --bg:         #0d0d0d;
  --surface:    #111111;
  --border:     #1e1e1e;
  --quote-bar:  #2a2a2a;
  --text-body:  #cccccc;
  --text-dim:   #888888;
  --text-faint: #555555;
  --text-ghost: #333333;
  --gold:       #c8963c;
  --white:      #ffffff;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  background: var(--bg);
  color: var(--text-body);
  font-family: 'Libre Baskerville', Georgia, serif;
  margin: 0;
  padding: 0 52px 0 0;
}

/* ── Page sections ── */
.page {
  width: 176mm;
  min-height: 250mm;
  margin: 0 auto;
  padding: 20mm 18mm 22mm 18mm;
  box-sizing: border-box;
  break-before: page;
  position: relative;
  display: flex;
  flex-direction: column;
}

/* ── Front matter ── */
.fm-page { background: var(--bg); }
.fm-halftitle {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 28px; font-weight: 700; color: var(--white);
  text-align: center; margin-top: auto;
}
.fm-vol {
  font-family: 'Montserrat', sans-serif;
  font-size: 10px; font-weight: 400; color: var(--text-dim);
  text-align: center; letter-spacing: 3px; text-transform: uppercase;
  margin-top: 14px;
}
.fm-subtitle {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; color: var(--text-faint);
  text-align: center; letter-spacing: 2px; text-transform: uppercase;
  margin-top: 8px; margin-bottom: auto;
}
.fm-rule { border: none; border-top: 1px solid var(--border); margin: 24px 0; }
.fm-author {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 14px; color: var(--text-dim); text-align: center;
}
.fm-publisher {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; color: var(--text-ghost);
  text-align: center; letter-spacing: 2px; text-transform: uppercase;
  margin-top: 8px;
}
.fm-copyright {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 9px; color: var(--text-dim); line-height: 1.8;
}
.fm-h1 {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 18px; font-weight: 700; color: var(--white); margin-bottom: 20px;
}
.fm-sh {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase;
  margin-top: 16px; margin-bottom: 8px;
}
.fm-p {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 9.5px; color: var(--text-body); line-height: 1.7; margin-bottom: 10px;
}
.fm-term { font-weight: 700; color: var(--white); }
.fm-pagenum {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-ghost);
  text-align: center; margin-top: auto;
  padding-top: 12px; border-top: 1px solid var(--border);
}

/* TOC */
.toc-entry {
  display: flex; align-items: baseline;
  gap: 4px; margin-bottom: 9px;
}
.toc-num {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-faint); min-width: 28px;
}
.toc-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 10px; color: var(--text-body); flex: 1;
}
.toc-dots {
  flex: 1;
  border-bottom: 1px dotted var(--border);
  margin: 0 6px; min-width: 20px;
}
.toc-page {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-faint);
}

/* ── Chapter opener ── */
.chapter-opener { background: var(--surface); }
.ch-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 3px; text-transform: uppercase; margin-bottom: 12px;
}
.ch-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 26px; font-weight: 700; color: var(--white);
  line-height: 1.2; margin-bottom: 16px;
}
.ch-rule { border: none; border-top: 1px solid var(--gold); width: 40%; margin-bottom: 12px; }
.ch-count {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-faint); letter-spacing: 1px; margin-bottom: 20px;
}
.ch-intro {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 9px; font-style: italic; color: var(--text-dim);
  line-height: 1.75; margin-bottom: 24px;
}
.ch-entries-list { columns: 2; column-gap: 20px; margin-top: auto; }
.ch-entry-item {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; color: #444; line-height: 1.9;
  break-inside: avoid; overflow: hidden;
  white-space: nowrap; text-overflow: ellipsis;
}
.ch-entry-num { color: var(--text-ghost); margin-right: 4px; }

/* ── Entry ── */
.entry { background: var(--bg); }
.entry-breadcrumb {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px;
}
.entry-title {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 15px; font-weight: 700; color: var(--white);
  line-height: 1.35; margin-bottom: 10px;
}
.entry-tags {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: var(--gold);
  letter-spacing: 1px; margin-bottom: 12px;
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
}
.tag-badge {
  background: #1a1a2e; color: #7986cb;
  padding: 2px 6px; border-radius: 2px;
  font-size: 7px; font-weight: 600;
  letter-spacing: 0.5px; text-transform: uppercase;
}
.tag-strong   { background: #1a3a1a; color: #4caf50; }
.tag-moderate { background: #2a2a0a; color: #cddc39; }
.tag-basic    { background: #1e1e1e; color: #888888; }
.tag-ref      { color: var(--gold); font-weight: 600; }
.entry-quote {
  font-family: 'EB Garamond', Georgia, serif;
  font-size: 11px; font-style: italic; color: #bbbbbb;
  border-left: 2px solid var(--quote-bar);
  padding-left: 12px; margin: 0 0 14px 0; line-height: 1.65;
}
.section-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; font-weight: 600; color: var(--text-faint);
  letter-spacing: 2px; text-transform: uppercase;
  margin-top: 12px; margin-bottom: 5px;
}
.section-body {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 9.5px; color: var(--text-body);
  line-height: 1.7; margin-bottom: 6px;
}
.entry-pagenum {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; color: var(--text-ghost);
  text-align: center; margin-top: auto;
  padding-top: 12px; border-top: 1px solid var(--border);
}

/* ── Back matter ── */
.back-matter { background: var(--bg); }
.bm-h1 {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 18px; font-weight: 700; color: var(--white); margin-bottom: 20px;
}
.idx-columns { columns: 2; column-gap: 20px; }
.idx-cat-header {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; font-weight: 600; color: var(--gold);
  letter-spacing: 1px; text-transform: uppercase;
  margin-top: 14px; margin-bottom: 4px; break-after: avoid;
}
.idx-entry {
  font-family: 'Libre Baskerville', Georgia, serif;
  font-size: 8.5px; color: var(--text-body);
  line-height: 1.6; padding-left: 10px;
  display: flex; justify-content: space-between;
}
.idx-entry-title { flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.idx-entry-page {
  font-family: 'Montserrat', sans-serif;
  font-size: 7.5px; color: var(--text-ghost);
  margin-left: 8px; white-space: nowrap;
}

/* ── Navigator ── */
#page-nav {
  position: fixed; right: 0; top: 0;
  width: 36px; height: 100vh;
  display: flex; flex-direction: column; align-items: center;
  padding: 8px 0;
  background: #0a0a0a; border-left: 1px solid #1a1a1a; z-index: 100;
}
#pn-counter {
  font-family: 'Montserrat', sans-serif;
  font-size: 6px; color: #555;
  margin-bottom: 6px; letter-spacing: 0.5px;
  text-align: center; line-height: 1.6; white-space: pre;
}
#pn-track {
  flex: 1; width: 10px;
  background: #161616; border-radius: 5px;
  border: 1px solid #222; position: relative;
  overflow: hidden; cursor: pointer;
}
.pn-tick {
  position: absolute; left: 0; right: 0;
  height: 1px; background: #2a2a2a;
  cursor: pointer; transition: background 0.15s;
}
.pn-tick:hover { background: #555; }
.pn-tick.chapter-mark { background: #3d3d3d; height: 2px; }
.pn-tick.active { background: #c8963c; }
#pn-thumb {
  position: absolute; left: 0; right: 0; height: 20px;
  background: rgba(200,150,60,0.12);
  border: 1px solid rgba(200,150,60,0.4);
  border-radius: 3px; pointer-events: none;
  transition: top 0.1s; top: 0;
}

/* ── Print ── */
@media print {
  #page-nav { display: none !important; }
  body { padding: 0; }
}
@page { size: 176mm 250mm; margin: 0; }
"""


if __name__ == '__main__':
    pass  # main() added in Task 8
