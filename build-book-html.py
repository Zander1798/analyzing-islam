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
    """HTML-escape a plain-text string for insertion into HTML text nodes.

    Uses quote=False so apostrophes are not converted to &#x27; — apostrophes
    are safe in HTML text content and only require escaping inside attribute values.
    """
    return html_mod.escape(str(s), quote=False)


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


def render_front_matter(chapters: dict, ch_start_pages: dict) -> list:
    """Return list of 6 HTML strings: half-title, title, copyright, TOC, foreword, abbreviations."""

    # ── i: Half-title ──
    s_halftitle = '''
<section class="page fm-page" id="fm-halftitle" data-page="i">
  <div class="fm-halftitle">Analyzing Islam</div>
  <div class="fm-vol">Volume I</div>
  <div class="fm-subtitle">The Quran</div>
  <div class="fm-pagenum">i</div>
</section>'''

    # ── ii: Title page ──
    s_title = '''
<section class="page fm-page" id="fm-title" data-page="ii">
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:0;">
    <div class="fm-halftitle" style="margin-top:0;">Analyzing Islam</div>
    <div class="fm-vol" style="margin-top:12px;">Volume I &mdash; The Quran</div>
    <div class="fm-subtitle" style="margin-top:8px;">A Critical Reference Guide</div>
    <hr class="fm-rule" style="margin:32px 0;">
    <div class="fm-author">G.J. van Vuuren</div>
    <hr class="fm-rule" style="margin:32px 0;">
    <div class="fm-publisher">analyzingislam.com</div>
  </div>
  <div class="fm-pagenum">ii</div>
</section>'''

    # ── iii: Copyright ──
    s_copyright = '''
<section class="page fm-page" id="fm-copyright" data-page="iii">
  <div style="margin-top:auto;">
    <p class="fm-copyright">Copyright &copy; 2026 G.J. van Vuuren</p>
    <p class="fm-copyright" style="margin-top:12px;">
      All rights reserved. No part of this publication may be reproduced, distributed,
      or transmitted in any form or by any means without the prior written permission
      of the publisher.
    </p>
    <p class="fm-copyright" style="margin-top:12px;">
      Published by AnalyzingIslam.com<br>
      analyzingislam.com
    </p>
    <p class="fm-copyright" style="margin-top:12px;">First edition, 2026</p>
    <p class="fm-copyright" style="margin-top:12px;">
      All Quranic quotations are from the Saheeh International English translation.
    </p>
    <p class="fm-copyright" style="margin-top:12px;">
      Volume I of a projected multi-volume series examining primary Islamic source texts.
    </p>
  </div>
  <div class="fm-pagenum">iii</div>
</section>'''

    # ── iv: TOC ──
    toc_rows = ''
    for ch_num in sorted(chapters.keys()):
        if not chapters[ch_num]:
            continue
        ch_name, _ = CHAPTERS[ch_num]
        pg = ch_start_pages.get(ch_num, '&mdash;')  # may contain HTML entities (e.g. &mdash;) — do NOT esc()
        toc_rows += f'''
    <div class="toc-entry">
      <span class="toc-num">{ch_num}</span>
      <span class="toc-title">{esc(ch_name)}</span>
      <span class="toc-dots"></span>
      <span class="toc-page">{pg}</span>
    </div>'''

    s_toc = f'''
<section class="page fm-page" id="fm-toc" data-page="iv">
  <h2 class="fm-h1">Contents</h2>
  {toc_rows}
  <div class="fm-pagenum">iv</div>
</section>'''

    # ── v–vii: Foreword ──
    s_foreword = '''
<section class="page fm-page" id="fm-foreword" data-page="v">
  <h2 class="fm-h1">Foreword</h2>
  <p class="fm-p">
    This volume is a reference guide, not a polemic. Its purpose is to catalogue, clearly and
    without embellishment, the passages of the Quran that present difficulties &mdash; theological,
    logical, scientific, historical, or ethical &mdash; for the claim that the text is the literal,
    perfect, and eternal word of an omniscient God.
  </p>
  <p class="fm-p">
    Each entry follows the same structure: what the verse or passage says, why it constitutes
    a problem, the standard Muslim apologetic response, and why that response does or does not
    resolve the difficulty. Entries are rated by strength: <em>Basic</em> (a stock reply exists
    and is widely rehearsed), <em>Moderate</em> (answering requires conceding something), or
    <em>Strong</em> (every standard response generates a new problem or requires abandoning the
    plain meaning of the text).
  </p>
  <p class="fm-p">
    The Quran is quoted throughout from the Saheeh International English translation &mdash; chosen
    because it is the translation most widely recommended by contemporary Islamic scholars and
    apologists as accurate and faithful to the Arabic. Where a specific word or phrase is
    disputed, the Arabic and multiple translations are noted in the entry.
  </p>
  <p class="fm-p">
    This is Volume I of a projected series. Subsequent volumes will address the hadith
    collections (Sahih Bukhari, Sahih Muslim, and the four Sunan), the Sira (prophetic
    biography), and classical Islamic jurisprudence. Each volume follows the same format and
    rating system, permitting cross-volume comparison.
  </p>
  <p class="fm-p">
    The twenty-three chapters of this volume correspond to the major category groupings used
    on the AnalyzingIslam.com catalog. Not every entry belongs neatly in one category; where
    a passage raises problems of multiple types, it is placed in the chapter corresponding to
    its primary difficulty, with cross-references noted where relevant.
  </p>
  <p class="fm-p">
    A note on tone: the entries describe problems as problems. They do not impute bad faith
    to Muslim believers, assume that Islam as a religion is reducible to its difficult texts,
    or suggest that individual Muslims are responsible for what their scripture contains.
    The object of scrutiny throughout is the text and its implications &mdash; not its adherents.
  </p>
  <div class="fm-pagenum">v</div>
</section>'''

    # ── viii–ix: Abbreviations ──
    s_abbr = '''
<section class="page fm-page" id="fm-abbr" data-page="viii">
  <h2 class="fm-h1">Abbreviations &amp; Reference Guide</h2>

  <div class="fm-sh">CITATION FORMAT</div>
  <p class="fm-p">
    <span class="fm-term">Q 4:34</span>
    &nbsp; Quran, Surah 4 (An-Nisa), Verse 34. All Quranic citations follow this
    surah:verse format. Where a range of verses is relevant, it appears as Q 9:5&ndash;6.
    All quotations are from the Saheeh International English translation.
  </p>

  <div class="fm-sh">STRENGTH RATINGS</div>
  <p class="fm-p">
    <span class="fm-term">Basic</span>
    &nbsp; Apologists have a stock reply. The problem is real but the standard response
    is widely known and rehearsed.
  </p>
  <p class="fm-p">
    <span class="fm-term">Moderate</span>
    &nbsp; Answering requires conceding something &mdash; softening a claim or reinterpreting the text.
  </p>
  <p class="fm-p">
    <span class="fm-term">Strong</span>
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
  <p class="fm-p"><span class="fm-term">Asbab al-Nuzul</span> &nbsp; The &ldquo;occasions of revelation&rdquo; &mdash; historical circumstances that triggered specific verses</p>

  <div class="fm-sh">ARABIC &amp; ISLAMIC TERMINOLOGY</div>
  <p class="fm-p"><span class="fm-term">Fiqh</span> &nbsp; Islamic jurisprudence &mdash; the body of legal rulings derived from Quran and hadith</p>
  <p class="fm-p"><span class="fm-term">Dhimmi</span> &nbsp; A non-Muslim subject living under Islamic rule</p>
  <p class="fm-p"><span class="fm-term">Hudud</span> &nbsp; Fixed Quranic punishments &mdash; amputation, stoning, lashing</p>
  <p class="fm-p"><span class="fm-term">Jizya</span> &nbsp; A tax levied on non-Muslims under Islamic governance (Q 9:29)</p>
  <p class="fm-p"><span class="fm-term">Tahrif</span> &nbsp; The Islamic claim that Jews and Christians corrupted their scriptures</p>
  <p class="fm-p"><span class="fm-term">Makr</span> &nbsp; Plotting or scheming; used of Allah in Q 3:54 and 8:30</p>
  <p class="fm-p"><span class="fm-term">Ma malakat aymanukum</span> &nbsp; &ldquo;What your right hands possess&rdquo; &mdash; the Quranic phrase for enslaved people and captives</p>

  <div class="fm-pagenum">viii</div>
</section>'''

    return [s_halftitle, s_title, s_copyright, s_toc, s_foreword, s_abbr]


def render_chapter_opener(ch_num: int, entries: list, section_idx: int) -> str:
    """Render one chapter opener page."""
    ch_name, ch_intro = CHAPTERS[ch_num]
    count_label = f"{len(entries)} {'entry' if len(entries) == 1 else 'entries'}"

    entry_items = ''
    for i, e in enumerate(entries, 1):
        title = e['title']
        if len(title) > 68:
            title = title[:68] + '…'
        entry_items += (
            f'<div class="ch-entry-item">'
            f'<span class="ch-entry-num">{i}.</span>{esc(title)}'
            f'</div>\n'
        )

    return f'''
<section class="page chapter-opener" id="s{section_idx}" data-page="{section_idx}" data-chapter="{ch_num}">
  <div class="ch-label">CHAPTER {ch_num}</div>
  <h1 class="ch-title">{esc(ch_name)}</h1>
  <hr class="ch-rule">
  <div class="ch-count">{count_label}</div>
  <p class="ch-intro">{esc(ch_intro)}</p>
  <div class="ch-entries-list">
    {entry_items}
  </div>
  <div class="entry-pagenum">{section_idx}</div>
</section>'''


def render_entry(meta: dict, sections_data: dict, ch_num: int, section_idx: int) -> str:
    """Render one entry page."""
    eid      = meta['id']
    title    = meta['title']
    ref      = meta['ref']
    strength = meta.get('strength', 'basic')
    cats     = meta.get('categories', [])
    sec      = sections_data.get(eid, {})

    ch_name, _ = CHAPTERS.get(ch_num, (str(ch_num), ''))
    breadcrumb = f'THE QURAN  ·  CHAPTER {ch_num}  ·  {ch_name.upper()}'

    # Tags row
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

    # Quote block
    quote = sec.get('quote', '').strip()
    quote_html = ''
    if quote:
        quote_html = f'<blockquote class="entry-quote">&ldquo;{esc(quote)}&rdquo;</blockquote>'

    # Content sections
    content_html = ''
    for label, key in [
        ('WHAT THE VERSE SAYS',   'says'),
        ('WHY THIS IS A PROBLEM', 'problem'),
        ('THE MUSLIM RESPONSE',   'response'),
        ('WHY IT FAILS',          'fails'),
    ]:
        text = sec.get(key, '').strip()
        if not text:
            continue
        paras = ''.join(
            f'<p class="section-body">{esc(p.strip())}</p>'
            for p in text.split('\n\n') if p.strip()
        )
        content_html += f'<div class="section-label">{label}</div>{paras}\n'

    return f'''
<section class="page entry" id="s{section_idx}" data-page="{section_idx}" data-chapter="{ch_num}">
  <div class="entry-breadcrumb">{esc(breadcrumb)}</div>
  <h2 class="entry-title">{esc(title)}</h2>
  <div class="entry-tags">{tags_html}</div>
  {quote_html}
  {content_html}
  <div class="entry-pagenum">{section_idx}</div>
</section>'''


def render_general_index(chapters: dict, section_idx: int) -> str:
    """Render the General Index back matter page."""
    rows = ''
    for ch_num in sorted(chapters.keys()):
        ch_entries = chapters[ch_num]
        if not ch_entries:
            continue
        ch_name, _ = CHAPTERS[ch_num]
        rows += f'<div class="idx-cat-header">Chapter {ch_num} — {esc(ch_name)}</div>\n'
        for e in ch_entries:
            title = e['title']
            if len(title) > 70:
                title = title[:70] + '…'
            rows += (
                f'<div class="idx-entry">'
                f'<span class="idx-entry-title">{esc(title)}</span>'
                f'<span class="idx-entry-page">{esc(e["ref"])}</span>'
                f'</div>\n'
            )

    return f'''
<section class="page back-matter" id="s{section_idx}" data-page="{section_idx}">
  <h2 class="bm-h1">General Index</h2>
  <div class="idx-columns">
    {rows}
  </div>
  <div class="entry-pagenum">{section_idx}</div>
</section>'''


def render_verse_index(entries: list, section_idx: int) -> str:
    """Render the Quran Verse Index back matter page, sorted by surah then ayah."""
    def sort_key(e: dict) -> tuple:
        m = re.search(r'(?:Q|Quran)\s*(\d+):(\d+)', e['ref'])
        if m:
            return (int(m.group(1)), int(m.group(2)))
        return (9999, 0)

    sorted_entries = sorted(entries, key=sort_key)

    rows = ''
    for e in sorted_entries:
        title = e['title']
        if len(title) > 70:
            title = title[:70] + '…'
        rows += (
            f'<div class="idx-entry">'
            f'<span class="idx-entry-page" style="min-width:60px;margin-left:0;margin-right:8px;">'
            f'{esc(e["ref"])}</span>'
            f'<span class="idx-entry-title">{esc(title)}</span>'
            f'</div>\n'
        )

    return f'''
<section class="page back-matter" id="s{section_idx}" data-page="{section_idx}">
  <h2 class="bm-h1">Quran Verse Index</h2>
  <div class="idx-columns">
    {rows}
  </div>
  <div class="entry-pagenum">{section_idx}</div>
</section>'''


def render_navigator(all_section_ids: list, chapter_section_ids: set) -> str:
    """
    Render the fixed right-side page navigator and inline JS.

    all_section_ids     : ordered list of every section id
    chapter_section_ids : set of ids that are chapter openers (get brighter tick)
    """
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
    if (e.target === track) {{  /* pn-thumb has pointer-events:none so never fires here */
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
    # Front matter: 6 fixed sections (indices 0-5)
    FM_IDS = ['fm-halftitle', 'fm-title', 'fm-copyright',
              'fm-toc', 'fm-foreword', 'fm-abbr']
    FM_COUNT = len(FM_IDS)

    all_section_ids     = list(FM_IDS)
    chapter_section_ids = set()
    ch_start_pages      = {}   # ch_num -> section_idx (used in TOC)
    ch_sections         = []   # (kind, ch_num, data, section_idx)

    body_idx = FM_COUNT
    for ch_num in sorted(chapters.keys()):
        ch_entries = chapters[ch_num]
        if not ch_entries:
            continue

        # Chapter opener
        ch_start_pages[ch_num] = body_idx
        section_id = f's{body_idx}'
        all_section_ids.append(section_id)
        chapter_section_ids.add(section_id)
        ch_sections.append(('opener', ch_num, ch_entries, body_idx))
        body_idx += 1

        # Entries
        for e in ch_entries:
            section_id = f's{body_idx}'
            all_section_ids.append(section_id)
            ch_sections.append(('entry', ch_num, e, body_idx))
            body_idx += 1

    # Back matter: 2 sections
    genidx_idx  = body_idx; all_section_ids.append(f's{body_idx}'); body_idx += 1
    versidx_idx = body_idx; all_section_ids.append(f's{body_idx}'); body_idx += 1

    total_sections = len(all_section_ids)
    print(f"  {total_sections} total sections")

    # ── Render all parts ──────────────────────────────────────────────────────
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
    genidx_html  = render_general_index(chapters, genidx_idx)
    versidx_html = render_verse_index(entries, versidx_idx)

    print("Rendering navigator…")
    nav_html = render_navigator(all_section_ids, chapter_section_ids)

    # ── Assemble full HTML ────────────────────────────────────────────────────
    print("Assembling book.html…")
    html = f"""<!DOCTYPE html>
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

{nav_html}

</body>
</html>"""

    OUT.write_text(html, encoding='utf-8')
    size_mb = OUT.stat().st_size / 1_048_576
    print(f"Done -> {OUT}  ({size_mb:.1f} MB, {total_sections} sections)")


if __name__ == '__main__':
    main()
