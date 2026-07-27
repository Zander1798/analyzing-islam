#!/usr/bin/env python3
"""Build Analyzing Islam Vol I — complete HTML mock-up from screenshots spec."""

import re, json, math, html as html_mod
from pathlib import Path

BASE      = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG   = BASE / "site/assets/data/catalog-entries.json"
QURAN_SRC = BASE / "site/catalog/quran.html"
OUT       = BASE / "book-design/vol1-quran/Analyzing Islam Vol I — Complete.html"

# ── Chapter definitions ──────────────────────────────────────────────────────

CHAPTERS = {
    1:  ("Abrogation",
         "The doctrine of <em>naskh</em> (abrogation) holds that later Quranic verses can supersede earlier ones "
         "while both remain in the written text. The Quran references this principle explicitly at Q 2:106 and "
         "Q 16:101. This chapter examines the theological and logical problems that arise when a supposedly "
         "perfect, eternal divine text requires internal revision — and the implications for claims of "
         "divine omniscience and consistency."),
    2:  ("Scripture Integrity",
         "The Quran presents itself as a perfectly preserved, uniquely clear, and self-authenticating revelation. "
         "This chapter examines the passages and historical facts that challenge those claims: the burning of variant "
         "codices under Uthman, the acknowledgement of verses no one knows the interpretation of, the Islamic Dilemma "
         "between Quranic endorsement of the Bible and the doctrine of <em>tahrif</em>, and internal claims that "
         "undermine the text’s own standard of clarity and permanence."),
    3:  ("Contradictions",
         "A text claimed to be the direct word of an omniscient God is expected to be internally consistent. "
         "This chapter catalogues passages in the Quran that contradict other Quranic passages — in "
         "arithmetic, cosmology, prophetic history, and law — and examines the apologetic strategies "
         "employed to reconcile them."),
    4:  ("Logical Inconsistency",
         "Beyond factual contradiction, several Quranic passages generate problems of logical form: self-refuting "
         "claims, arguments that assume what they are meant to prove, divine attributes that cannot coherently "
         "coexist, and instructions whose application requires information the text withholds. This chapter "
         "collects passages where the problem is not factual but structural."),
    5:  ("Allah’s Character",
         "Islamic theology attributes to Allah a set of perfections — omniscience, omnipotence, justice, "
         "mercy. A number of Quranic passages sit in tension with one or more of those attributes: a God who seals "
         "disbelievers’ hearts and then punishes them for disbelief, who engineers deception, who creates "
         "beings destined for Hell. This chapter examines passages where the Quranic portrait of God raises "
         "philosophical difficulties that standard defences do not resolve."),
    6:  ("Cosmology",
         "A number of Quranic passages describe the physical universe in ways that reflect pre-scientific "
         "cosmological assumptions rather than observed reality — including a sun that sets in a muddy "
         "spring, a seven-layered sky, sperm produced between the backbone and ribs, and the creation of the "
         "heavens and earth in six days. This chapter examines these passages against the backdrop of what was "
         "believed in 7th-century Arabia and what is known today."),
    7:  ("Pre-Islamic Borrowings",
         "Several Quranic narratives have direct parallels in Jewish midrashic literature, Christian apocryphal "
         "gospels, Zoroastrian texts, and pre-Islamic Arabian legend — including stories, characters, "
         "and details not found in canonical Jewish or Christian scripture. This chapter examines passages where "
         "the source material predates Islam and asks what the presence of that material implies for claims of "
         "direct divine revelation."),
    8:  ("Prophetic Character",
         "The Quran presents Muhammad as the exemplary moral model (<em>uswa hasana</em>). Several passages, "
         "however, describe a prophet who required divine reassurance, who benefited personally from his own "
         "revelations, who was rebuked by Allah for specific decisions, and whose conduct in particular episodes "
         "raises ethical questions the text itself registers without resolving. This chapter examines those passages."),
    9:  ("Prophetic Privileges",
         "A cluster of Quranic verses grants Muhammad exemptions and permissions explicitly denied to ordinary "
         "believers — additional wives beyond the limit of four, marriage to his adopted son’s "
         "divorcee, a personal cut of war spoils, permission for women to offer themselves to him without a dowry. "
         "This chapter examines the theological and ethical problems created when divine revelation is used to "
         "resolve a prophet’s personal domestic circumstances."),
    10: ("Jesus / Christology",
         "The Quran contains a substantial Christology — an account of Jesus that agrees with some "
         "Christian claims, categorically denies others, and adds details found in no earlier canonical source. "
         "This chapter examines passages where the Quranic portrait of Jesus contradicts the historical record, "
         "borrows from Christian apocrypha, or creates internal contradictions within the Quran’s own "
         "Christological account."),
    11: ("Women & Sexual Issues",
         "The Quran legislates extensively on the status of women, marriage, sexual access, and related matters. "
         "Several passages establish legal and social hierarchies that contemporary ethics regards as "
         "discriminatory, permit practices modern law criminalises, or create internal inconsistencies that "
         "Islamic jurisprudence has never fully resolved. This chapter examines those passages and the apologetic "
         "responses they have generated."),
    12: ("Child Marriage",
         "Q 65:4 sets out divorce procedures for wives who have not yet menstruated — an explicit "
         "Quranic provision for marriage to pre-pubescent girls. This chapter examines the verse, its classical "
         "tafsir, the apologetic strategies used to contextualise it, and why those strategies do not remove the "
         "ethical problem the text creates."),
    13: ("LGBTQ / Gender",
         "The Quran’s account of Lot’s people and related passages have been read by the classical "
         "tradition as a divine condemnation of same-sex relations. This chapter examines those passages, the "
         "related verse on gender non-conformity, and the ethical problems they raise for claims that Islam is "
         "compatible with modern conceptions of human dignity."),
    14: ("Slavery & Captives",
         "The Quran regulates slavery rather than prohibiting it — specifying procedures for "
         "manumission, permitting sexual access to female captives, and treating enslaved people as a recognised "
         "legal category. This chapter examines the relevant passages, their classical interpretations, and the "
         "apologetic argument that Quranic regulation represents progressive reform."),
    15: ("Warfare & Jihad",
         "Several Quranic verses command violence against non-Muslims in terms that admit no obvious limiting "
         "context — commanding believers to kill, fight, or subjugate until conversion or submission "
         "is obtained. This chapter examines passages where the plain reading authorises offensive warfare, the "
         "theological function of those commands within Islamic jurisprudence, and why the most common apologetic "
         "responses do not resolve the plain-text problem."),
    16: ("Apostasy & Blasphemy",
         "The Quran does not state an explicit death penalty for apostasy, but several passages are read by "
         "classical jurists as endorsing it, and Q 4:89 is the key proof-text for that ruling. This chapter "
         "examines the Quranic basis for apostasy law, the related passages on blaspheming the Prophet, and the "
         "apologetic claim that the Quran mandates no earthly punishment for leaving Islam."),
    17: ("Governance",
         "A number of passages establish that sovereignty belongs to Allah alone and that legislation is his "
         "exclusive prerogative — the canonical proof-texts for Islamic theocratic governance. Others "
         "mandate fixed punishments for specific crimes that a human legislature cannot reduce. This chapter "
         "examines the political theology of the Quran and the challenges it poses for democratic and pluralist "
         "governance."),
    18: ("Disbelievers & Moral Problems",
         "The Quran characterises non-Muslims in terms ranging from misguided to irredeemably corrupt, the worst "
         "of creatures, and objects of divine curse. Several passages mandate social and legal discrimination "
         "against them. This chapter collects passages where the Quranic treatment of non-Muslims raises ethical "
         "problems — either in the characterisation itself or in the practical consequences that "
         "characterisation has historically generated."),
    19: ("Antisemitism",
         "The Quran contains direct derogatory characterisations of Jews as a group: divine transformation into "
         "apes and pigs, fabricated theological claims attributed to them, and placement at the top of a ranking "
         "of hostility toward believers. This chapter examines those passages and the apologetic argument that "
         "they are context-specific rather than general statements about Jewish people."),
    20: ("Paradise",
         "The Quran’s descriptions of paradise are detailed and physical: gardens of flowing rivers, the "
         "eternal virgin houris, seventy-two companions, rivers of wine and honey. This chapter examines "
         "passages where those descriptions raise moral problems — a paradise designed for male "
         "pleasure, a Hell engineered for maximum suffering, and the incoherence of promising wine in paradise "
         "after condemning it on earth."),
    21: ("Strange",
         "A number of Quranic passages describe supernatural events, historical claims, or cosmological "
         "assertions that resist straightforward naturalisation — stars as missiles thrown at "
         "eavesdropping jinn, a village left dead for a century with unspoiled food, ants that converse with "
         "Solomon, mountains that pass like clouds. This chapter collects those passages and examines why the "
         "standard apologetic readings do not resolve the problems they create."),
    22: ("Magic & Ritual",
         "The Quran legislates extensively on ritual purity and acknowledges a world populated by jinn, "
         "sorcerers, and supernatural entities. Several passages describe magic as real and dangerous, attribute "
         "miraculous powers to prophets, and create ritual requirements whose scriptural basis is internally "
         "contradictory. This chapter examines passages in each of those categories."),
    23: ("Animals",
         "Several Quranic passages about animals create scientific, moral, or theological problems: bees that "
         "receive divine inspiration, animals that form communities like humans, Solomon commanding the ants, "
         "and the killing of a specific bird species justified by religious reward. This chapter examines those "
         "passages and the apologetic arguments surrounding them."),
}

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
}

EXCLUDE_IDS = {
    "amputate-the-hand-of-the-thief-regardless-of-circumstance-4104d45b",
    "one-hundred-lashes-for-fornication-yet-the-hadith-demands-st-f805f912",
}

STRENGTH_ORDER = {'basic': 0, 'moderate': 1, 'strong': 2}

def assign_chapter(eid, categories):
    if eid in ID_OVERRIDES:
        return ID_OVERRIDES[eid]
    for tag, ch in TAG_PRIORITY:
        if tag in categories:
            return ch
    return 18

# ── Entry parsing ────────────────────────────────────────────────────────────

def clean_html(s):
    s = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', s, flags=re.DOTALL)
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()

def parse_entries():
    raw = QURAN_SRC.read_text(encoding='utf-8', errors='ignore')
    pat = r'<div[^>]+class="[^"]*\bentry\b[^"]*"[^>]+id="([^"]+)"[^>]*>'
    opens = list(re.finditer(pat, raw))
    result = {}
    for i, m in enumerate(opens):
        eid = m.group(1)
        end = opens[i+1].start() if i+1 < len(opens) else len(raw)
        chunk = raw[m.start():end]
        bq_m = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', chunk, re.DOTALL)
        quote_html = ''
        if bq_m:
            q = bq_m.group(1)
            q = re.sub(r'<p[^>]*>', '', q)
            q = re.sub(r'</p>', ' ', q)
            quote_html = clean_html(q).strip()
        h4_parts = re.split(r'<h4[^>]*>', chunk)
        sections = {'says': '', 'problem': '', 'response': '', 'fails': ''}
        for part in h4_parts[1:]:
            end_tag = part.find('</h4>')
            if end_tag == -1:
                continue
            header = part[:end_tag].lower().strip()
            body = part[end_tag+5:]
            paras = re.findall(r'<p[^>]*>(.*?)</p>', body, re.DOTALL)
            para_html = '\n'.join(f'<p>{clean_html(p.strip())}</p>' for p in paras if p.strip())
            if 'what the verse' in header:
                sections['says'] = para_html
            elif 'why this is a problem' in header:
                sections['problem'] = para_html
            elif 'muslim response' in header:
                sections['response'] = para_html
            elif 'why it fails' in header:
                sections['fails'] = para_html
        result[eid] = {'quote': quote_html, **sections}
    return result

# ── Height estimator ─────────────────────────────────────────────────────────

def _est_h(html_frag):
    h = 0
    m = re.search(r'class="entry-title"[^>]*>(.*?)</div>', html_frag, re.DOTALL)
    if m:
        text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        h += max(1, math.ceil(len(text) / 54)) * 26 + 10
    if 'entry-meta' in html_frag:
        h += 30
    bq = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', html_frag, re.DOTALL)
    if bq:
        text = re.sub(r'<[^>]+>', '', bq.group(1)).strip()
        h += max(1, math.ceil(len(text) / 82)) * 22 + 28
    h += len(re.findall(r'<h4[^>]*>', html_frag)) * 34
    for pm in re.finditer(r'<p[^>]*>(.*?)</p>', html_frag, re.DOTALL):
        text = re.sub(r'<[^>]+>', '', pm.group(1)).strip()
        if text:
            h += max(1, math.ceil(len(text) / 80)) * 26 + 8
    return h

def _fine_chunks(inner_html):
    chunks = []
    h4_pos = [m.start() for m in re.finditer(r'<h4>', inner_html)]
    header_end = h4_pos[0] if h4_pos else len(inner_html)
    header = inner_html[:header_end]
    if header.strip():
        chunks.append(header)
    for i, pos in enumerate(h4_pos):
        end = h4_pos[i+1] if i+1 < len(h4_pos) else len(inner_html)
        section = inner_html[pos:end]
        p_list = list(re.finditer(r'<p[^>]*>', section))
        if len(p_list) == 0:
            chunks.append(section)
        else:
            first_p = p_list[0].start()
            h4_chunk = section[:first_p]
            if h4_chunk.strip():
                chunks.append(h4_chunk)
            for j in range(len(p_list)):
                p_start = p_list[j].start()
                p_end = p_list[j+1].start() if j+1 < len(p_list) else len(section)
                chunks.append(section[p_start:p_end])
    return chunks

def _sentence_split(para_html):
    m = re.match(r'(<p[^>]*>)(.*?)(</p>)', para_html.strip(), re.DOTALL)
    if not m:
        return None
    open_tag, body, close_tag = m.groups()
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z“‘"])', body.strip())
    return (open_tag, parts, close_tag) if len(parts) > 1 else None

# ── CSS ──────────────────────────────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #141414;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 56px 24px 100px;
  gap: 52px;
  font-family: system-ui, -apple-system, sans-serif;
}

/* ── Shell labels ── */
.sec-label {
  width: 665px;
  border-top: 1px solid #2a2a2a;
  padding-top: 13px;
  font-size: 10px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #444;
  margin-bottom: -36px;
}
.pg-label {
  width: 665px;
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #3a3a3a;
  margin-bottom: -36px;
}

/* ── Page shell ── */
.page {
  width: 665px;
  height: 945px;
  background: #000;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px #222, 0 24px 80px rgba(0,0,0,0.9);
}
.page-inner {
  position: absolute;
  top: 76px; bottom: 76px;
  left: 68px; right: 53px;
  overflow: hidden;
}

/* ── FRONT COVER ── */
.fc-series-bar {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 42px;
  border-bottom: 1px solid #111;
  display: flex;
  align-items: center;
  justify-content: center;
}
.fc-series-text {
  font-size: 7.5px;
  letter-spacing: 0.34em;
  text-transform: uppercase;
  color: #272727;
}
.fc-rings {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  overflow: hidden;
}
.fc-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}
.fc-r1 { width: 880px; height: 880px; border-color: rgba(255,255,255,0.018); }
.fc-r2 { width: 660px; height: 660px; border-color: rgba(255,255,255,0.026); }
.fc-r3 { width: 460px; height: 460px; border-color: rgba(255,255,255,0.035); }
.fc-r4 { width: 280px; height: 280px; border-color: rgba(255,255,255,0.048); }
.fc-r5 { width: 120px; height: 120px; border-color: rgba(255,255,255,0.07); }
.fc-title-upper {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 420px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 12px;
}
.fc-word-analyzing {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 90px;
  font-weight: bold;
  color: #f5f5f5;
  letter-spacing: -0.02em;
  line-height: 1;
}
.fc-divider {
  position: absolute;
  top: 418px; left: 0; right: 0;
  height: 1px;
  background: #111;
}
.fc-title-lower {
  position: absolute;
  top: 419px; left: 0; right: 0;
  padding-top: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.fc-word-islam {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 90px;
  font-weight: bold;
  color: #f5f5f5;
  letter-spacing: -0.02em;
  line-height: 1;
  margin-bottom: 10px;
}
.fc-gold-rule {
  width: 48px;
  height: 1px;
  background: #c8912a;
  margin-bottom: 16px;
}
.fc-volume {
  font-size: 8.5px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: #4a4a4a;
  margin-bottom: 8px;
}
.fc-source {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 17px;
  font-style: italic;
  color: #6a6a6a;
  margin-bottom: 8px;
}
.fc-descriptor {
  font-size: 7.5px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #2e2e2e;
}
.fc-author-block {
  position: absolute;
  bottom: 90px;
  left: 0; right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.fc-author-rule {
  width: 40px;
  height: 1px;
  background: #1e1e1e;
  margin-bottom: 14px;
}
.fc-author {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 20px;
  color: #f5f5f5;
  letter-spacing: 0.03em;
}
.fc-footer {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 46px;
  border-top: 1px solid #111;
  display: flex;
  align-items: center;
  justify-content: center;
}
.fc-footer-text {
  font-size: 7.5px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: #252525;
}

/* ── BACK COVER ── */
.bc-inner {
  position: absolute;
  top: 68px; bottom: 72px;
  left: 64px; right: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.bc-title {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 30px;
  font-weight: bold;
  color: #f5f5f5;
  letter-spacing: -0.01em;
  text-align: center;
  margin-bottom: 6px;
}
.bc-red-rule { width: 100%; height: 1px; background: #e53935; margin-bottom: 5px; }
.bc-subtitle {
  font-size: 7.5px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #4a4a4a;
  text-align: center;
  margin-bottom: 24px;
}
.bc-top-rule { width: 100%; height: 1px; background: #161616; margin-bottom: 24px; }
.bc-blurb {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 13px;
  font-style: italic;
  line-height: 1.85;
  color: #b8b8b8;
  text-align: center;
  max-width: 480px;
  margin-bottom: 24px;
}
.bc-features { width: 100%; margin-bottom: 22px; }
.bc-feat {
  font-size: 9.5px;
  line-height: 1.9;
  color: #666;
  padding-left: 16px;
  position: relative;
}
.bc-feat::before {
  content: '\00b7';
  position: absolute;
  left: 0;
  color: #c8912a;
  font-size: 16px;
  line-height: 1.3;
}
.bc-mid-rule { width: 100%; height: 1px; background: #161616; margin-bottom: 18px; }
.bc-about-label {
  font-size: 7.5px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: #4a4a4a;
  text-align: center;
  margin-bottom: 10px;
}
.bc-bio {
  font-size: 10px;
  line-height: 1.85;
  color: #666;
  text-align: center;
  max-width: 440px;
}
.bc-bottom {
  position: absolute;
  bottom: 0; left: 64px; right: 64px;
}
.bc-bottom-rule { width: 100%; height: 1px; background: #161616; margin-bottom: 14px; }
.bc-bottom-row { display: flex; justify-content: space-between; align-items: flex-end; }
.bc-barcode {
  width: 110px; height: 60px;
  background: repeating-linear-gradient(
    90deg,
    #fff 0,#fff 1px,#000 1px,#000 3px,#fff 3px,#fff 4px,
    #000 4px,#000 7px,#fff 7px,#fff 9px,#000 9px,#000 11px,
    #fff 11px,#fff 13px,#000 13px,#000 16px,#fff 16px,#fff 17px,
    #000 17px,#000 20px,#fff 20px,#fff 22px,#000 22px,#000 24px,
    #fff 24px,#fff 27px,#000 27px,#000 29px,#fff 29px,#fff 31px,
    #000 31px,#000 35px,#fff 35px,#fff 36px,#000 36px,#000 39px,
    #fff 39px,#fff 41px,#000 41px,#000 43px,#fff 43px,#fff 46px,
    #000 46px,#000 48px,#fff 48px,#fff 50px,#000 50px,#000 53px,
    #fff 53px,#fff 55px,#000 55px,#000 58px,#fff 58px,#fff 61px,
    #000 61px,#000 63px,#fff 63px,#fff 66px,#000 66px,#000 69px,
    #fff 69px,#fff 71px,#000 71px,#000 74px,#fff 74px,#fff 76px,
    #000 76px,#000 79px,#fff 79px,#fff 82px,#000 82px,#000 84px,
    #fff 84px,#fff 87px,#000 87px,#000 89px,#fff 89px,#fff 91px,
    #000 91px,#000 94px,#fff 94px,#fff 97px,#000 97px,#000 100px,
    #fff 100px,#fff 102px,#000 102px,#000 105px,#fff 105px,#fff 108px,
    #000 108px,#000 110px
  );
}
.bc-isbn {
  font-size: 8px;
  color: #444;
  letter-spacing: 0.06em;
  margin-top: 5px;
}
.bc-price { font-size: 11px; color: #444; letter-spacing: 0.06em; }
.bc-pub { font-size: 7.5px; letter-spacing: 0.26em; text-transform: uppercase; color: #252525; margin-top: 5px; }

/* ── HALF TITLE ── */
.ht-block { margin-top: 190px; }
.ht-volume {
  font-size: 10px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: #c8912a;
  margin-bottom: 12px;
}
.ht-title {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 44px;
  font-weight: bold;
  color: #f5f5f5;
  line-height: 1.0;
  letter-spacing: -0.015em;
  margin-bottom: 16px;
}
.ht-source {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 14px;
  font-style: italic;
  color: #c8912a;
}

/* ── TITLE PAGE ── */
.tp-block { margin-top: 150px; }
.tp-main {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 54px;
  font-weight: bold;
  color: #f5f5f5;
  line-height: 1.0;
  letter-spacing: -0.02em;
  margin-bottom: 22px;
}
.tp-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 20px; }
.tp-volume {
  font-size: 10px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: #888;
  margin-bottom: 16px;
}
.tp-source {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 28px;
  font-weight: bold;
  color: #f5f5f5;
  letter-spacing: -0.01em;
  margin-bottom: 12px;
}
.tp-descriptor {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 15px;
  font-style: italic;
  color: #5a5a5a;
}
.tp-colophon {
  position: absolute;
  bottom: 0; left: 0; right: 0;
}
.tp-col-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 14px; }
.tp-col-text {
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #5a5a5a;
  line-height: 1.9;
}

/* ── COPYRIGHT ── */
.cr-block {
  position: absolute;
  bottom: 0; left: 0; right: 0;
}
.cr-title {
  font-size: 11.5px;
  color: #f5f5f5;
  line-height: 1.7;
  margin-bottom: 4px;
}
.cr-subtitle {
  font-size: 11.5px;
  color: #f5f5f5;
  line-height: 1.7;
  margin-bottom: 24px;
}
.cr-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 18px; }
.cr-notice {
  font-size: 10px;
  color: #888;
  line-height: 1.9;
  margin-bottom: 14px;
}
.cr-notice em { font-style: italic; color: #aaa; }
.cr-isbn {
  font-size: 10px;
  color: #4a4a4a;
  letter-spacing: 0.04em;
  margin-top: 18px;
}
.cr-pgnum {
  position: absolute;
  bottom: 0; right: 0;
  font-size: 10.5px;
  color: #4a4a4a;
  letter-spacing: 0.06em;
}

/* ── TABLE OF CONTENTS ── */
.toc-head {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 38px;
  font-weight: bold;
  color: #f5f5f5;
  letter-spacing: -0.01em;
  margin-bottom: 26px;
}
.toc-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 20px; }
.toc-row { display: flex; align-items: baseline; margin-bottom: 9px; }
.toc-row-label {
  font-size: 11.5px;
  color: #c8912a;
  white-space: nowrap;
}
.toc-dots {
  flex: 1;
  border-bottom: 1px dotted #282828;
  margin: 0 8px 3px;
  min-width: 12px;
}
.toc-pg {
  font-size: 11.5px;
  color: #5a5a5a;
  white-space: nowrap;
  font-style: italic;
}
.toc-sec {
  font-size: 9px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: #4a4a4a;
  margin: 20px 0 10px;
}
.toc-ch { display: flex; align-items: baseline; margin-bottom: 7px; }
.toc-ch-num {
  font-size: 10px;
  color: #c8912a;
  min-width: 26px;
}
.toc-ch-name {
  font-size: 11.5px;
  color: #c8912a;
  white-space: nowrap;
}
.toc-ch-dots {
  flex: 1;
  border-bottom: 1px dotted #282828;
  margin: 0 8px 3px;
  min-width: 12px;
}
.toc-ch-pg {
  font-size: 11.5px;
  color: #5a5a5a;
  white-space: nowrap;
  font-style: italic;
}
.toc-back { margin-top: 20px; }
.toc-pgnum {
  position: absolute;
  bottom: 0; left: 50%; transform: translateX(-50%);
  font-size: 10.5px;
  color: #4a4a4a;
}

/* ── FOREWORD / BODY PAGES ── */
.fw-head {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 38px;
  font-weight: bold;
  color: #f5f5f5;
  letter-spacing: -0.01em;
  margin-bottom: 30px;
}
.body-rh {
  font-size: 9px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #404040;
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 1px solid #1a1a1a;
}
.fw-sh {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #f5f5f5;
  margin-top: 26px;
  margin-bottom: 10px;
}
.fw-p {
  font-size: 11.5px;
  line-height: 1.85;
  color: #c8912a;
  margin-bottom: 12px;
}
.fw-p em { font-style: italic; color: #d4a044; }
.fw-p strong { font-weight: 600; color: #d4a044; }
.fw-table { width: 100%; border-collapse: collapse; margin: 10px 0 14px; }
.fw-table td {
  font-size: 11px;
  line-height: 1.75;
  color: #b8b8b8;
  padding: 6px 0;
  vertical-align: top;
  border-bottom: 1px solid #151515;
}
.fw-table td:first-child {
  font-weight: 700;
  color: #f5f5f5;
  width: 82px;
  padding-right: 14px;
  white-space: nowrap;
}
.anatomy-block {
  border-left: 1px solid #242424;
  padding-left: 14px;
  margin: 8px 0 12px;
}
.anatomy-row { display: flex; margin-bottom: 6px; }
.anatomy-label {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #888;
  width: 90px;
  flex-shrink: 0;
}
.anatomy-desc { font-size: 11px; color: #b0b0b0; line-height: 1.6; }
.fw-pgnum {
  position: absolute;
  bottom: 0; left: 50%; transform: translateX(-50%);
  font-size: 10.5px;
  color: #4a4a4a;
}

/* ── ABBREVIATIONS ── */
.abbrev-head {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 36px;
  font-weight: bold;
  color: #f5f5f5;
  line-height: 1.05;
  letter-spacing: -0.01em;
  margin-bottom: 6px;
}
.abbrev-subhead {
  font-size: 9.5px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #888;
  margin-bottom: 24px;
}
.abbrev-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 18px; }
.abbrev-sec {
  font-size: 9px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #4a4a4a;
  margin-bottom: 8px;
  margin-top: 18px;
}
.abbrev-table { width: 100%; border-collapse: collapse; }
.abbrev-table td {
  font-size: 11.5px;
  line-height: 1.65;
  padding: 5px 0;
  vertical-align: top;
  border-bottom: 1px solid #0e0e0e;
  color: #c8912a;
}
.abbrev-table td.term {
  font-weight: 700;
  color: #f5f5f5;
  width: 150px;
  padding-right: 16px;
  white-space: nowrap;
}
.abbrev-table td.term em { font-style: italic; font-weight: 400; color: #888; }
.abbrev-pgnum {
  position: absolute;
  bottom: 0; left: 50%; transform: translateX(-50%);
  font-size: 10.5px;
  color: #4a4a4a;
}

/* ── PART OPENER ── */
.po-numeral {
  position: absolute;
  top: 30px; right: -8px;
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 200px;
  font-weight: bold;
  color: #090909;
  line-height: 1;
  letter-spacing: -0.05em;
  user-select: none;
}
.po-block {
  position: absolute;
  top: 48%; left: 0; right: 0;
  transform: translateY(-50%);
}
.po-vol {
  font-size: 9.5px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: #c8912a;
  margin-bottom: 14px;
}
.po-title {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 50px;
  font-weight: bold;
  color: #f5f5f5;
  line-height: 1.0;
  letter-spacing: -0.02em;
  margin-bottom: 22px;
}
.po-rule { width: 40px; height: 1px; background: #c8912a; margin-bottom: 20px; }
.po-desc {
  font-size: 11px;
  line-height: 1.85;
  color: #c8912a;
  max-width: 400px;
}
.po-footer {
  position: absolute;
  bottom: 0; left: 0; right: 0;
}
.po-footer-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 13px; }
.po-footer-row { display: flex; justify-content: space-between; align-items: baseline; }
.po-count {
  font-size: 9.5px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #4a4a4a;
}
.po-count span { color: #888; font-weight: 600; }
.po-pgnum {
  font-size: 10.5px;
  color: #4a4a4a;
}

/* ── SOURCE INTRODUCTION ── */
.si-eyebrow {
  font-size: 9px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: #4a4a4a;
  margin-bottom: 10px;
}
.si-title {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 40px;
  font-weight: bold;
  color: #f5f5f5;
  letter-spacing: -0.015em;
  margin-bottom: 20px;
}
.si-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 22px; }
.si-p {
  font-size: 11.5px;
  line-height: 1.85;
  color: #c8912a;
  margin-bottom: 12px;
}
.si-p em { font-style: italic; color: #d4a044; }
.si-p strong { font-weight: 700; color: #d4a044; }
.si-facts {
  position: absolute;
  bottom: 0; left: 0; right: 0;
}
.si-facts-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 14px; }
.si-facts-row { display: flex; gap: 0; }
.si-fact { flex: 1; padding-right: 14px; }
.si-fact:last-child { padding-right: 0; }
.si-fact-val {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 20px;
  font-weight: bold;
  color: #f5f5f5;
  line-height: 1;
  margin-bottom: 4px;
}
.si-fact-lbl {
  font-size: 8.5px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #4a4a4a;
}
.si-pgnum {
  position: absolute;
  bottom: 0; left: 50%; transform: translateX(-50%);
  font-size: 10.5px;
  color: #4a4a4a;
}

/* ── CHAPTER OPENER ── */
.ch-breadcrumb {
  font-size: 9px;
  letter-spacing: 0.26em;
  text-transform: uppercase;
  color: #4a4a4a;
  margin-bottom: 12px;
}
.ch-title {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 46px;
  font-weight: bold;
  color: #f5f5f5;
  line-height: 1.0;
  letter-spacing: -0.015em;
  margin-bottom: 0;
}
.ch-rule { width: 100%; height: 1px; background: #c8912a; margin: 18px 0 18px; opacity: 0.5; }
.ch-desc {
  font-size: 13px;
  line-height: 1.85;
  color: #c8912a;
  max-width: 460px;
  margin-bottom: 0;
}
.ch-desc em { font-style: italic; color: #d4a044; }
.entry-list { margin-top: 22px; }
.entry-row { display: flex; align-items: baseline; margin-bottom: 10px; gap: 8px; }
.er-num { font-size: 9px; color: #333; min-width: 18px; flex-shrink: 0; }
.er-title { font-size: 11.5px; color: #b8b8b8; flex: 1; line-height: 1.4; }
.er-ref { font-size: 10px; color: #4a4a4a; white-space: nowrap; flex-shrink: 0; }
.etag {
  font-size: 8px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 1px 6px;
  border: 1px solid;
  white-space: nowrap;
  flex-shrink: 0;
}
.etag.basic    { color: #4caf50; border-color: #4caf50; }
.etag.moderate { color: #e07b00; border-color: #e07b00; }
.etag.strong   { color: #fff; border-color: #e53935; background: #e53935; }
.ch-footer {
  position: absolute;
  bottom: 0; left: 0; right: 0;
}
.ch-footer-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 13px; }
.ch-footer-row { display: flex; justify-content: space-between; align-items: baseline; }
.ch-entry-count {
  font-size: 9.5px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #4a4a4a;
}
.ch-entry-count span { color: #888; font-weight: 600; }
.ch-source-lbl {
  font-size: 9.5px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #2a2a2a;
}
.ch-pgnum {
  font-size: 10.5px;
  color: #4a4a4a;
}

/* ── ENTRY PAGES ── */
.rh-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 14px;
  padding-bottom: 11px;
  border-bottom: 1px solid #1a1a1a;
}
.running-chapter {
  font-size: 9px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #4a4a4a;
}
.entry-page { height: 945px; overflow: hidden; }
.entry { }
.entry-title {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 20px;
  font-weight: bold;
  color: #f5f5f5;
  line-height: 1.25;
  letter-spacing: -0.01em;
  margin-bottom: 10px;
}
.entry-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 14px;
}
.tag {
  font-size: 9px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  border: 1px solid;
  padding: 2px 7px;
  white-space: nowrap;
}
.ch-tag { color: #5a5a5a; border-color: #2a2a2a; }
.strength-basic    { color: #4caf50; border-color: #4caf50; }
.strength-moderate { color: #e07b00; border-color: #e07b00; }
.strength-strong   { color: #fff; border-color: #e53935; background: #e53935; }
.entry-ref {
  font-size: 10px;
  letter-spacing: 0.08em;
  color: #c8912a;
  margin-left: auto;
}
.entry blockquote {
  border-left: 2px solid #7aa2f7;
  margin: 0 0 14px 0;
  padding: 8px 16px;
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-style: italic;
  font-size: 13px;
  color: #888;
  line-height: 1.7;
}
.entry h4 {
  font-size: 9.5px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #c8912a;
  font-weight: 700;
  margin: 14px 0 6px;
  font-family: system-ui, sans-serif;
}
.entry p {
  font-size: 13px;
  line-height: 1.8;
  color: #c8912a;
  margin-bottom: 8px;
  font-family: system-ui, sans-serif;
}
.entry p:last-child { margin-bottom: 0; }
.entry p em { font-style: italic; color: #d4a044; }
.entry p strong { font-weight: 600; color: #d4a044; }
.ep-pgnum {
  position: absolute;
  bottom: 6px;
  left: 0; right: 0;
  text-align: center;
  font-size: 10.5px;
  color: #4a4a4a;
}

/* ── GENERAL INDEX ── */
.idx-head {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 38px;
  font-weight: bold;
  color: #f5f5f5;
  letter-spacing: -0.01em;
  margin-bottom: 20px;
}
.idx-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 18px; }
.gi-letter {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 15px;
  font-weight: bold;
  color: #f5f5f5;
  margin-top: 14px;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid #1a1a1a;
  line-height: 1;
}
.gi-letter:first-child { margin-top: 0; }
.gi-cat-row { display: flex; align-items: baseline; margin: 3px 0 5px; }
.gi-cat-label { font-size: 12px; font-weight: 600; color: #d0d0d0; }
.gi-cat-pg { font-size: 11px; color: #4a4a4a; margin-left: 8px; font-style: italic; }
.gi-sub-row { display: flex; align-items: flex-end; margin-bottom: 4px; padding-left: 14px; }
.gi-sub-label { font-size: 11px; line-height: 1.55; color: #c8912a; flex: 1; word-break: break-word; }
.gi-ldots { flex-shrink: 0; width: 24px; border-bottom: 1px dotted #222; margin: 0 4px 3px; }
.gi-pg { font-size: 11px; color: #4a4a4a; white-space: nowrap; font-style: italic; flex-shrink: 0; }
.gi-pgnum {
  position: absolute;
  bottom: 0; left: 50%; transform: translateX(-50%);
  font-size: 10.5px;
  color: #4a4a4a;
}

/* ── QURAN VERSE INDEX ── */
.vi-head {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 38px;
  font-weight: bold;
  color: #f5f5f5;
  letter-spacing: -0.01em;
  margin-bottom: 8px;
}
.vi-sub {
  font-size: 9px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #4a4a4a;
  margin-bottom: 16px;
}
.vi-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 16px; }
.vi-columns { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0 18px; }
.surah-head { margin: 10px 0 4px; padding-bottom: 3px; border-bottom: 1px solid #1a1a1a; }
.surah-head:first-child { margin-top: 0; }
.surah-num {
  font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif;
  font-size: 11px;
  font-weight: bold;
  color: #f5f5f5;
  line-height: 1.2;
}
.surah-name {
  font-size: 8.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #4a4a4a;
}
.vx { display: flex; align-items: baseline; margin-bottom: 2px; }
.vx-ref { font-size: 10px; color: #c8912a; white-space: nowrap; max-width: 100px; overflow: hidden; text-overflow: ellipsis; }
.vx-dots { flex: 1; border-bottom: 1px dotted #1e1e1e; margin: 0 4px 2px; min-width: 4px; }
.vx-pg { font-size: 10px; color: #4a4a4a; white-space: nowrap; }
.vi-pgnum {
  position: absolute;
  bottom: 0; left: 50%; transform: translateX(-50%);
  font-size: 10.5px;
  color: #4a4a4a;
}
"""

# ── HTML generators ──────────────────────────────────────────────────────────

def page_label(text):
    return f'<div class="pg-label">{html_mod.escape(text)}</div>\n'

def sec_label(text):
    return f'<div class="sec-label">{html_mod.escape(text)}</div>\n'

def pgnum_roman(n):
    vals = [(1000,'m'),(900,'cm'),(500,'d'),(400,'cd'),(100,'c'),(90,'xc'),
            (50,'l'),(40,'xl'),(10,'x'),(9,'ix'),(5,'v'),(4,'iv'),(1,'i')]
    result = ''
    for v, s in vals:
        while n >= v:
            result += s
            n -= v
    return result

def front_cover():
    return """\
<div class="page">
  <div class="fc-rings">
    <div class="fc-ring fc-r1"></div>
    <div class="fc-ring fc-r2"></div>
    <div class="fc-ring fc-r3"></div>
    <div class="fc-ring fc-r4"></div>
    <div class="fc-ring fc-r5"></div>
  </div>
  <div class="fc-series-bar">
    <span class="fc-series-text">Analyzing Islam &middot; Volume I &middot; The Quran</span>
  </div>
  <div class="fc-title-upper">
    <span class="fc-word-analyzing">Analyzing</span>
  </div>
  <div class="fc-divider"></div>
  <div class="fc-title-lower">
    <span class="fc-word-islam">Islam</span>
    <div class="fc-gold-rule"></div>
    <div class="fc-volume">Volume I</div>
    <div class="fc-source">The Quran</div>
    <div style="margin-top:6px;"><span class="fc-descriptor">A Critical Reference Guide</span></div>
  </div>
  <div class="fc-author-block">
    <div class="fc-author-rule"></div>
    <div class="fc-author">G.J. van Vuuren</div>
  </div>
  <div class="fc-footer">
    <span class="fc-footer-text">AnalyzingIslam.com</span>
  </div>
</div>
"""

def back_cover():
    return """\
<div class="page">
  <div class="bc-inner">
    <div class="bc-title">Analyzing Islam</div>
    <div class="bc-red-rule"></div>
    <div class="bc-subtitle">Volume I &middot; The Quran &middot; A Critical Reference Guide</div>
    <div class="bc-top-rule"></div>
    <div class="bc-blurb">A structured reference guide to the Quran &mdash; Islam&rsquo;s central divine text, comprising 114 surahs and 6,236 verses. Each of the 282 entries presents a specific verse exactly as it appears in the authoritative Saheeh International translation, examines its context and significance, surveys the standard Muslim apologetic response, and explains precisely where that response falls short.</div>
    <div class="bc-features">
      <div class="bc-feat">282 entries organized across 20 chapters</div>
      <div class="bc-feat">All quotations from the Saheeh International English translation</div>
      <div class="bc-feat">Strength ratings &mdash; Basic, Moderate, Strong &mdash; for every argument</div>
      <div class="bc-feat">Cross-referenced General Index and Quran Verse Index</div>
      <div class="bc-feat">Designed for researchers, apologists, and informed general readers</div>
    </div>
    <div class="bc-mid-rule"></div>
    <div class="bc-about-label">About AnalyzingIslam.com</div>
    <div class="bc-bio">AnalyzingIslam.com is an independent reference platform dedicated to the close examination of Islamic primary texts. Drawing on classical Arabic sources, academic scholarship, and direct textual analysis, it presents the most significant challenges to Islamic truth claims in a structured, accessible format.</div>
  </div>
  <div class="bc-bottom">
    <div class="bc-bottom-rule"></div>
    <div class="bc-bottom-row">
      <div>
        <div class="bc-barcode"></div>
        <div class="bc-isbn">ISBN 978-0-000-00000-0</div>
      </div>
      <div style="text-align:right;">
        <div class="bc-price">$xx.xx / &pound;xx.xx</div>
        <div class="bc-pub">AnalyzingIslam.com</div>
      </div>
    </div>
  </div>
</div>
"""

def half_title(pgnum):
    return f"""\
<div class="page">
  <div class="page-inner">
    <div class="ht-block">
      <div class="ht-volume">Volume I</div>
      <div class="ht-title">Analyzing<br>Islam</div>
      <div class="ht-source">The Quran</div>
    </div>
    <div class="fw-pgnum">{pgnum_roman(pgnum)}</div>
  </div>
</div>
"""

def title_page(pgnum):
    return f"""\
<div class="page">
  <div class="page-inner">
    <div class="tp-block">
      <div class="tp-main">Analyzing<br>Islam</div>
      <div class="tp-rule"></div>
      <div class="tp-volume">Volume I</div>
      <div class="tp-source">The Quran</div>
      <div class="tp-descriptor">A Critical Reference Guide</div>
    </div>
    <div class="tp-colophon">
      <div class="tp-col-rule"></div>
      <div class="tp-col-text">AnalyzingIslam.com<br>First Edition, 2026</div>
    </div>
    <div class="fw-pgnum">{pgnum_roman(pgnum)}</div>
  </div>
</div>
"""

def copyright_page(pgnum):
    return f"""\
<div class="page">
  <div class="page-inner">
    <div class="cr-block">
      <div class="cr-title">Analyzing Islam &mdash; Volume I: The Quran</div>
      <div class="cr-subtitle">A Critical Reference Guide</div>
      <div class="cr-rule"></div>
      <div class="cr-notice">&copy; 2026 Analyzing Islam. All rights reserved.<br>analyzingislam.com</div>
      <div class="cr-notice">First edition, 2026.<br><br>
        All Quranic verses are quoted from the <em>Saheeh International</em> English translation. This volume covers the Quran exclusively. Hadith collections &mdash; Sahih al-Bukhari, Sahih Muslim, and the four Sunan &mdash; are examined in subsequent volumes of this series.<br><br>
        No part of this publication may be reproduced or transmitted in any form without prior written permission from the publisher, except for brief quotations in reviews or scholarly work with full attribution.<br><br>
        Every entry references a specific verse &mdash; verify before citing.
      </div>
      <div class="cr-isbn">ISBN &mdash;</div>
    </div>
    <div class="cr-pgnum">{pgnum_roman(pgnum)}</div>
  </div>
</div>
"""

def toc_page(by_chapter, pgnum):
    # Chapter start pages (approximate, matching screenshots)
    ch_pages = {
        1:1, 2:20, 3:41, 4:72, 5:97, 6:118, 7:192,
        8:229, 9:266, 10:279, 11:312, 12:415,
        13:416, 14:430,
        15:418, 16:447, 17:450, 18:461, 19:511,
        20:518, 21:525, 22:555, 23:570
    }
    rows = ''
    for ch in range(1, 24):
        if not by_chapter.get(ch):
            continue
        ch_name, _ = CHAPTERS[ch]
        pg = ch_pages.get(ch, '—')
        rows += f'''<div class="toc-ch">
  <span class="toc-ch-num">{ch}</span>
  <span class="toc-ch-name">{html_mod.escape(ch_name)}</span>
  <span class="toc-ch-dots"></span>
  <span class="toc-ch-pg">{pg}</span>
</div>\n'''
    return f"""\
<div class="page">
  <div class="page-inner">
    <div class="toc-head">Contents</div>
    <div class="toc-rule"></div>
    <div class="toc-row">
      <span class="toc-row-label">Foreword</span>
      <span class="toc-dots"></span>
      <span class="toc-pg">v</span>
    </div>
    <div class="toc-row">
      <span class="toc-row-label">Abbreviations &amp; Reference Guide</span>
      <span class="toc-dots"></span>
      <span class="toc-pg">viii</span>
    </div>
    <div class="toc-sec">The Quran &middot; 282 entries across 20 chapters</div>
    {rows}
    <div class="toc-back" style="margin-top:16px;">
      <div class="toc-sec">Back Matter</div>
      <div class="toc-row"><span class="toc-row-label">General Index</span><span class="toc-dots"></span><span class="toc-pg">590</span></div>
      <div class="toc-row"><span class="toc-row-label">Quran Verse Index</span><span class="toc-dots"></span><span class="toc-pg">602</span></div>
    </div>
    <div class="toc-pgnum">{pgnum_roman(pgnum)}</div>
  </div>
</div>
"""

def foreword_pages(start_pgnum):
    p1 = f"""\
<div class="page">
  <div class="page-inner">
    <div class="fw-head">Foreword</div>
    <div class="fw-sh">What this is</div>
    <p class="fw-p">This book is a reference catalog of passages from the Quran that present philosophical, historical, moral, or logical difficulties. Every entry cites a specific verse, explains what it says in plain language, and builds the case for why it presents a problem. Where relevant, entries also present the standard Muslim apologetic response and push back on it.</p>
    <p class="fw-p">Volume I covers one source: the Quran &mdash; the text that Islam itself holds to be the direct, unaltered word of Allah, superior to all other Islamic sources in authority. No fringe interpretations. No hostile translations. The case is built entirely from Islam&rsquo;s own most authoritative scripture as rendered in its most widely endorsed English edition.</p>
    <div class="fw-sh">How entries are organized</div>
    <p class="fw-p">Entries are grouped into 23 thematic chapters &mdash; Abrogation, Contradictions, Warfare &amp; Jihad, Women &amp; Sexual Issues, and so on. Each chapter collects every entry that belongs to that theme. If the Quran yields no entries in a given category, that chapter is omitted entirely.</p>
    <p class="fw-p">When an entry touches more than one theme, it appears under the category that best captures its primary problem. It does not appear twice. Subsequent volumes examine the hadith collections &mdash; Sahih al-Bukhari, Sahih Muslim, and the four canonical Sunan.</p>
    <div class="fw-sh">How to read an entry</div>
    <p class="fw-p">Each entry contains four elements:</p>
    <div class="anatomy-block">
      <div class="anatomy-row"><span class="anatomy-label">Reference</span><span class="anatomy-desc">The Quran citation &mdash; surah and verse number.</span></div>
      <div class="anatomy-row"><span class="anatomy-label">Rating</span><span class="anatomy-desc">The apologetic difficulty level: Basic, Moderate, or Strong.</span></div>
      <div class="anatomy-row"><span class="anatomy-label">Passage</span><span class="anatomy-desc">The verse quoted in full from the Saheeh International translation.</span></div>
      <div class="anatomy-row"><span class="anatomy-label">Commentary</span><span class="anatomy-desc">An explanation of the problem &mdash; what it says, why it matters, and where the standard apologetic falls short.</span></div>
    </div>
    <div class="fw-pgnum">{pgnum_roman(start_pgnum)}</div>
  </div>
</div>
"""
    p2 = f"""\
<div class="page">
  <div class="page-inner">
    <div class="body-rh">Foreword</div>
    <div class="fw-sh">Strength ratings</div>
    <p class="fw-p">Every entry is rated according to how difficult the problem is to answer from within the Islamic apologetic tradition:</p>
    <table class="fw-table">
      <tr><td>Basic</td><td>Apologists have a stock reply. The problem is real but the standard response is widely known and rehearsed.</td></tr>
      <tr><td>Moderate</td><td>Answering requires conceding something &mdash; softening a claim, reinterpreting a text, or acknowledging that the tradition is not unanimous.</td></tr>
      <tr><td>Strong</td><td>The apologetic moves themselves generate new problems. Every standard response either contradicts another Islamic claim or requires abandoning the plain meaning of the text.</td></tr>
    </table>
    <p class="fw-p">Ratings reflect apologetic difficulty &mdash; not moral severity. A passage can be morally disturbing and still rated Basic if the apologetic reply is well-established and coherent.</p>
    <div class="fw-sh">Sources and translations</div>
    <p class="fw-p">All Quranic verses in this volume are quoted from the <em>Saheeh International</em> English translation &mdash; the Saudi-sanctioned mainstream Sunni edition, widely used in mosques and Islamic universities across the English-speaking world. It is the edition most commonly recommended by contemporary Sunni scholars when asked to name an accurate English Quran.</p>
    <p class="fw-p">Choosing the most mainstream, most-recommended translation removes the easy dismissal of &ldquo;hostile translation.&rdquo; The problems documented in this volume are not artifacts of a tendentious rendering &mdash; they appear in the text that Islam&rsquo;s own authorities have endorsed and distributed worldwide.</p>
    <div class="fw-pgnum">{pgnum_roman(start_pgnum+1)}</div>
  </div>
</div>
"""
    p3 = f"""\
<div class="page">
  <div class="page-inner">
    <div class="body-rh">Foreword</div>
    <div class="fw-sh">A note on tone</div>
    <p class="fw-p">This catalog does not argue. It presents. The entries speak through the texts themselves &mdash; the reader is left to draw their own conclusions. No passage is fabricated, paraphrased to distort, or stripped of context that would change its meaning. Where context matters, it is provided.</p>
    <p class="fw-p">The commentary aims to be precise rather than polemical. Where Islamic scholars disagree among themselves, that disagreement is noted. Where a passage has a defensible reading, that reading is acknowledged before the problem with it is explained. The goal is not to mock but to examine &mdash; carefully, specifically, and without concession.</p>
    <p class="fw-p">Readers who find a specific entry inaccurate, mistranslated, or missing essential context are encouraged to raise the objection at <em>analyzingislam.com</em>, where every entry in this volume is also published online and open for scrutiny.</p>
    <div class="fw-sh">How to use this book</div>
    <p class="fw-p">Read it in order or jump directly to a category. Each entry stands on its own. The 20 thematic chapters are self-contained &mdash; no prior entry is assumed when reading any later entry.</p>
    <p class="fw-p">Use the Quran Verse Index at the back to locate entries by surah and verse number. Use the General Index to find entries touching a specific topic, person, or concept across all 20 chapters. Every entry references a specific verse. Verify before citing.</p>
    <div class="fw-pgnum">{pgnum_roman(start_pgnum+2)}</div>
  </div>
</div>
"""
    return p1 + p2 + p3

def abbreviations_pages(start_pgnum):
    p1 = f"""\
<div class="page">
  <div class="page-inner">
    <div class="abbrev-head">Abbreviations<br>&amp; Reference Guide</div>
    <div class="abbrev-subhead">Citations, Terminology, and Rating System &mdash; Volume I: The Quran</div>
    <div class="abbrev-rule"></div>
    <div class="abbrev-sec">Citation Format</div>
    <table class="abbrev-table">
      <tr><td class="term">Q 4:34</td><td>Quran, Surah 4 (An-Nisa), Verse 34. All Quranic citations follow this surah:verse format. Where a range of verses is relevant, it appears as Q 9:5&ndash;6. All quotations are from the <em>Saheeh International</em> English translation.</td></tr>
    </table>
    <div class="abbrev-sec">Strength Ratings</div>
    <table class="abbrev-table">
      <tr><td class="term">Basic</td><td>Apologists have a stock reply. The problem is real but the standard response is widely known and rehearsed.</td></tr>
      <tr><td class="term">Moderate</td><td>Answering requires conceding something &mdash; softening a claim or reinterpreting the text.</td></tr>
      <tr><td class="term">Strong</td><td>Apologetic moves generate new problems. Every standard response requires abandoning the plain meaning of the text or contradicts another Islamic claim.</td></tr>
    </table>
    <div class="abbrev-sec">Quranic Terminology</div>
    <table class="abbrev-table">
      <tr><td class="term">Ayah <em>(pl. Ayat)</em></td><td>A verse of the Quran; literally &ldquo;a sign&rdquo;</td></tr>
      <tr><td class="term">Surah</td><td>A chapter of the Quran; there are 114 in total</td></tr>
      <tr><td class="term">Meccan</td><td>Revealed while Muhammad was in Mecca (c. 610&ndash;622 CE) &mdash; generally monotheism and eschatology</td></tr>
      <tr><td class="term">Medinan</td><td>Revealed while Muhammad was in Medina (c. 622&ndash;632 CE) &mdash; generally law, governance, and warfare</td></tr>
      <tr><td class="term">Naskh</td><td>Abrogation &mdash; the doctrine that later Quranic verses can cancel earlier ones</td></tr>
      <tr><td class="term">Tafsir</td><td>Quranic exegesis or commentary; the classical tradition of explaining individual verses</td></tr>
      <tr><td class="term">Asbab al-Nuzul</td><td>The &ldquo;occasions of revelation&rdquo; &mdash; historical circumstances that triggered specific verses</td></tr>
    </table>
    <div class="abbrev-pgnum">{pgnum_roman(start_pgnum)}</div>
  </div>
</div>
"""
    p2 = f"""\
<div class="page">
  <div class="page-inner">
    <div class="body-rh">Abbreviations &amp; Reference Guide</div>
    <div class="abbrev-sec">Arabic &amp; Islamic Terminology</div>
    <table class="abbrev-table">
      <tr><td class="term">Fiqh</td><td>Islamic jurisprudence &mdash; the body of legal rulings derived from the Quran and hadith</td></tr>
      <tr><td class="term">Ulema</td><td>Islamic scholars and jurists collectively</td></tr>
      <tr><td class="term">Dhimmi</td><td>A non-Muslim subject living under Islamic rule, subject to the jizya tax and legal restrictions</td></tr>
      <tr><td class="term">Hudud</td><td>Fixed Quranic punishments &mdash; amputation, stoning, lashing &mdash; that cannot be reduced by a judge</td></tr>
      <tr><td class="term">Jizya</td><td>A tax levied on non-Muslims living under Islamic governance in lieu of military service (Q 9:29)</td></tr>
      <tr><td class="term">Jinn</td><td>Supernatural beings made of smokeless fire; mentioned throughout the Quran</td></tr>
      <tr><td class="term">Tahrif</td><td>The Islamic claim that Jews and Christians corrupted their scriptures</td></tr>
      <tr><td class="term">Fitnah</td><td>Trial, strife, or persecution; used in key warfare verses (Q 2:193, 8:39)</td></tr>
      <tr><td class="term">Ma malakat aymanukum</td><td>&ldquo;What your right hands possess&rdquo; &mdash; the Quranic phrase for enslaved people and captive women</td></tr>
      <tr><td class="term">Dahaha</td><td>Verb in Q 79:30 translated &ldquo;spread out&rdquo; or &ldquo;egg-shaped&rdquo; &mdash; key in cosmology debates</td></tr>
      <tr><td class="term">Makr</td><td>Plotting or scheming; used of Allah in Q 3:54 and 8:30</td></tr>
      <tr><td class="term">Ijaz al-Quran</td><td>The doctrine of the Quran&rsquo;s inimitability &mdash; the claim that its literary style is miraculous</td></tr>
      <tr><td class="term">r.a.</td><td><em>Radi Allahu anhu / anha</em> &mdash; &ldquo;May Allah be pleased with him / her&rdquo;</td></tr>
      <tr><td class="term">s.a.w.</td><td><em>Sallallahu alayhi wa sallam</em> &mdash; &ldquo;Peace and blessings be upon him&rdquo;</td></tr>
    </table>
    <div class="abbrev-pgnum">{pgnum_roman(start_pgnum+1)}</div>
  </div>
</div>
"""
    return p1 + p2

def part_opener(total_entries, total_chapters, pgnum):
    return f"""\
<div class="page">
  <div class="page-inner">
    <div class="po-numeral">I</div>
    <div class="po-block">
      <div class="po-vol">Volume I</div>
      <div class="po-title">The Quran</div>
      <div class="po-rule"></div>
      <div class="po-desc">Comprising 114 surahs and 6,236 verses, the Quran is Islam&rsquo;s central divine text &mdash; believed by Muslims to be the literal word of Allah as revealed to Muhammad between approximately 610 and 632 CE. The surahs were revealed in Mecca and Medina, collected under Abu Bakr and standardised under Uthman ibn Affan around 650 CE. All verses are quoted from the Saheeh International English translation.</div>
    </div>
    <div class="po-footer">
      <div class="po-footer-rule"></div>
      <div class="po-footer-row">
        <div class="po-count"><span>{total_entries}</span> entries across <span>{total_chapters}</span> chapters</div>
        <div class="po-pgnum">{pgnum_roman(pgnum)}</div>
      </div>
    </div>
  </div>
</div>
"""

def source_intro(pgnum):
    return f"""\
<div class="page">
  <div class="page-inner">
    <div class="si-eyebrow">Primary Source</div>
    <div class="si-title">The Quran</div>
    <div class="si-rule"></div>
    <p class="si-p">The Quran is the central religious text of Islam, believed by Muslims to be the direct word of Allah as revealed to the Prophet Muhammad through the angel Jibril (Gabriel) over approximately twenty-three years &mdash; from 610 CE until Muhammad&rsquo;s death in 632 CE. It comprises 114 chapters (<em>surahs</em>) containing 6,236 verses (<em>ayahs</em>), arranged roughly in descending order of length rather than chronological order of revelation.</p>
    <p class="si-p">During Muhammad&rsquo;s lifetime, verses were memorised by companions and recorded on various materials. Following the Battle of Yamama in 632 CE, in which many memorisers were killed, Caliph Abu Bakr commissioned a written compilation. The standardised text known today was established under the third Caliph Uthman ibn Affan around 650 CE; variant readings were officially destroyed.</p>
    <p class="si-p">Surahs revealed in Mecca &mdash; primarily the earlier, shorter chapters &mdash; tend to focus on monotheism, eschatology, and moral instruction. Those revealed in Medina &mdash; longer, later chapters &mdash; deal extensively with law, governance, warfare, and relations with non-Muslims. The <strong>doctrine of abrogation</strong> (<em>naskh</em>) holds that later verses may supersede earlier ones, a principle with significant ethical implications examined throughout this volume.</p>
    <p class="si-p">All Quranic verses in this volume are quoted from the <em>Saheeh International</em> English translation, the edition most widely recommended by contemporary Sunni scholars for accuracy to the Arabic.</p>
    <div class="si-facts">
      <div class="si-facts-rule"></div>
      <div class="si-facts-row">
        <div class="si-fact"><div class="si-fact-val">114</div><div class="si-fact-lbl">Surahs</div></div>
        <div class="si-fact"><div class="si-fact-val">6,236</div><div class="si-fact-lbl">Verses</div></div>
        <div class="si-fact"><div class="si-fact-val">610&ndash;632 CE</div><div class="si-fact-lbl">Revelation Period</div></div>
        <div class="si-fact"><div class="si-fact-val">c.&nbsp;650 CE</div><div class="si-fact-lbl">Uthman&rsquo;s Compilation</div></div>
      </div>
    </div>
  </div>
</div>
"""

# ── Entry page generation ────────────────────────────────────────────────────

STRENGTH_LABEL = {'basic': 'Basic', 'moderate': 'Moderate', 'strong': 'Strong'}
STRENGTH_CLASS = {'basic': 'strength-basic', 'moderate': 'strength-moderate', 'strong': 'strength-strong'}
ETAG_CLASS     = {'basic': 'basic', 'moderate': 'moderate', 'strong': 'strong'}

def entry_inner_html(e, content, ch_name):
    eid      = e['id']
    title    = html_mod.escape(e.get('title', ''))
    ref      = html_mod.escape(e.get('ref', ''))
    strength = e.get('strength', '').lower()
    scls     = STRENGTH_CLASS.get(strength, '')
    slbl     = STRENGTH_LABEL.get(strength, strength.title())

    c        = content.get(eid, {})
    quote    = c.get('quote', '')
    says     = c.get('says', '<p><em>[content not extracted]</em></p>')
    problem  = c.get('problem', '')
    response = c.get('response', '')
    fails    = c.get('fails', '')

    quote_block = f'<blockquote>{quote}</blockquote>' if quote else ''

    def section(label, body):
        return f'<h4>{label}</h4>\n{body}' if body else ''

    ch_esc = html_mod.escape(ch_name)
    return f"""\
<div class="entry-title">{title}</div>
<div class="entry-meta">
  <span class="tag ch-tag">{ch_esc}</span>
  <span class="tag {scls}">{slbl}</span>
  <span class="entry-ref">{ref}</span>
</div>
{quote_block}
{section('What the verse says', says)}
{section('Why this is a problem', problem)}
{section('The Muslim response', response)}
{section('Why it fails', fails)}"""

def chapter_opener_html(ch_num, ch_name, ch_desc, entries, start_page):
    PAGE1_MAX = 18
    CONT_MAX  = 22
    count     = len(entries)
    ch_esc    = html_mod.escape(ch_name)
    current_page = [start_page]

    def _rows(batch, start_n):
        rows = ''
        for n, e in enumerate(batch, start_n):
            s  = e.get('strength', '').lower()
            ec = ETAG_CLASS.get(s, '')
            rows += (f'<div class="entry-row">'
                     f'<span class="er-num">{n}</span>'
                     f'<span class="er-title">{html_mod.escape(e.get("title",""))}</span>'
                     f'<span class="er-ref">{html_mod.escape(e.get("ref",""))}</span>'
                     f'<span class="etag {ec}">{s.title()}</span>'
                     f'</div>\n')
        return rows

    rows1 = _rows(entries[:PAGE1_MAX], 1)
    pg = current_page[0]
    current_page[0] += 1
    html_out = f"""\
<div class="page">
  <div class="page-inner">
    <div class="ch-breadcrumb">The Quran &middot; Chapter {ch_num}</div>
    <div class="ch-title">{ch_esc}</div>
    <div class="ch-rule"></div>
    <div class="ch-desc">{ch_desc}</div>
    <div class="entry-list">
{rows1}    </div>
    <div class="ch-footer">
      <div class="ch-footer-rule"></div>
      <div class="ch-footer-row">
        <div class="ch-entry-count"><span>{count}</span> entr{"y" if count==1 else "ies"}</div>
        <div class="ch-pgnum">{pg}</div>
        <div class="ch-source-lbl">The Quran</div>
      </div>
    </div>
  </div>
</div>
"""
    rh = (f'<div class="rh-row">'
          f'<span class="running-chapter">The Quran &middot; Chapter {ch_num} &middot; {ch_esc}</span>'
          f'</div>')

    remaining = entries[PAGE1_MAX:]
    offset    = PAGE1_MAX + 1
    while remaining:
        batch     = remaining[:CONT_MAX]
        remaining = remaining[CONT_MAX:]
        rows_c    = _rows(batch, offset)
        offset   += len(batch)
        pg = current_page[0]
        current_page[0] += 1
        html_out += f"""\
<div class="page">
  <div class="page-inner">
    {rh}
    <div class="entry-list" style="margin-top:0;">
{rows_c}    </div>
  </div>
</div>
"""
    return html_out, current_page[0]

def chapter_entry_pages(ch_num, ch_name, entries, contents, start_page):
    PAGE_H = 820
    ch_esc = html_mod.escape(ch_name)
    rh = (f'<div class="rh-row">'
          f'<span class="running-chapter">The Quran &middot; Chapter {ch_num} &middot; {ch_esc}</span>'
          f'</div>')

    def make_page(inner_html, pgnum):
        return (f'<div class="page entry-page">\n'
                f'  <div class="page-inner">\n    {rh}\n'
                f'<div class="entry">{inner_html}</div>\n'
                f'  </div>\n'
                f'  <div class="ep-pgnum">{pgnum}</div>\n'
                f'</div>\n')

    pages = []
    current_page = start_page
    for e in entries:
        inner = entry_inner_html(e, contents, ch_name)
        chunks = _fine_chunks(inner)
        h_used = 0
        p1_inner = ''
        p2_inner = ''
        on_p2 = False
        for ck in chunks:
            ck_h = _est_h(ck)
            if not on_p2 and h_used + ck_h <= PAGE_H:
                p1_inner += ck
                h_used += ck_h
            elif not on_p2:
                split = _sentence_split(ck)
                if split:
                    open_tag, sentences, close_tag = split
                    p1_sents, p2_sents = [], []
                    overflow = False
                    for s in sentences:
                        plain = re.sub(r'<[^>]+>', '', s)
                        s_h = max(1, math.ceil(len(plain) / 80)) * 26
                        if not overflow and h_used + s_h + 8 <= PAGE_H:
                            p1_sents.append(s)
                            h_used += s_h
                        else:
                            overflow = True
                            on_p2 = True
                            p2_sents.append(s)
                    if p1_sents:
                        p1_inner += open_tag + ' '.join(p1_sents) + close_tag
                        h_used += 8
                    if p2_sents:
                        p2_inner += open_tag + ' '.join(p2_sents) + close_tag
                else:
                    on_p2 = True
                    p2_inner += ck
            else:
                p2_inner += ck

        if p2_inner:
            orphan = re.search(r'(<h4[^>]*>[^<]*</h4>\s*)$', p1_inner.rstrip())
            if orphan:
                p2_inner = orphan.group(1) + p2_inner
                p1_inner = p1_inner[:orphan.start()]

        pages.append(make_page(p1_inner, current_page))
        current_page += 1
        if p2_inner:
            pages.append(make_page(p2_inner, current_page))
            current_page += 1

    return ''.join(pages), current_page

# ── Index generators ─────────────────────────────────────────────────────────

def general_index_html(by_chapter, entry_pages_map):
    from collections import defaultdict
    # Group chapters alphabetically by first letter of chapter name
    ch_alpha = {}
    for ch_num, entries in by_chapter.items():
        if not entries:
            continue
        ch_name = CHAPTERS[ch_num][0]
        letter = ch_name[0].upper()
        if letter not in ch_alpha:
            ch_alpha[letter] = []
        ch_alpha[letter].append((ch_num, ch_name, entries))

    pages_html = []
    current_letter_html = ''
    page_count = 590

    letter_data = {}
    for ch_num, entries in sorted(by_chapter.items()):
        if not entries:
            continue
        ch_name = CHAPTERS[ch_num][0]
        letter = ch_name[0].upper()
        if letter not in letter_data:
            letter_data[letter] = []
        ch_start = entry_pages_map.get(ch_num, '—')
        sub_items = []
        for e in entries:
            eid = e['id']
            ep = entry_pages_map.get(eid, '—')
            sub_items.append((html_mod.escape(e.get('title', '')), ep))
        letter_data[letter].append((ch_name, ch_start, sub_items))

    # Build 4-page index (simplified - 3 letters per page approx)
    all_letters = sorted(letter_data.keys())
    # Split into pages of roughly equal content
    idx_html = '<div class="gi-list">'
    for letter in all_letters:
        idx_html += f'<div class="gi-letter">{letter}</div>\n'
        for ch_name, ch_start, sub_items in letter_data[letter]:
            idx_html += f'<div class="gi-cat-row"><span class="gi-cat-label">{html_mod.escape(ch_name)}</span><span class="gi-cat-pg">.......... {ch_start}</span></div>\n'
            for title, ep in sub_items:
                idx_html += f'<div class="gi-sub-row"><span class="gi-sub-label">{title}</span><span class="gi-ldots"></span><span class="gi-pg">{ep}</span></div>\n'
    idx_html += '</div>'

    # Wrap in a single tall scrollable page for the mock (indices are represented as one page)
    result = ''
    result += f"""\
<div class="page" style="height:auto;min-height:945px;">
  <div class="page-inner" style="position:relative;overflow:visible;padding-bottom:40px;">
    <div class="idx-head">General Index</div>
    <div class="idx-rule"></div>
    {idx_html}
    <div class="gi-pgnum">{page_count}</div>
  </div>
</div>
"""
    return result

def quran_verse_index_html(all_entries_sorted, entry_pages_map):
    # Group by surah number extracted from ref
    from collections import defaultdict

    SURAH_NAMES = {
        1:'Al-Fatihah', 2:'Al-Baqarah', 3:'Ali \'Imran', 4:'An-Nisa',
        5:'Al-Ma\'idah', 6:'Al-An\'am', 7:'Al-A\'raf', 8:'Al-Anfal',
        9:'At-Tawbah', 10:'Yunus', 11:'Hud', 12:'Yusuf',
        13:'Ar-Ra\'d', 14:'Ibrahim', 15:'Al-Hijr', 16:'An-Nahl',
        17:'Al-Isra', 18:'Al-Kahf', 19:'Maryam', 20:'Ta-Ha',
        21:'Al-Anbiya', 22:'Al-Hajj', 23:'Al-Mu\'minun', 24:'An-Nur',
        25:'Al-Furqan', 26:'Ash-Shu\'ara', 27:'An-Naml', 28:'Al-Qasas',
        29:'Al-\'Ankabut', 30:'Ar-Rum', 31:'Luqman', 32:'As-Sajdah',
        33:'Al-Ahzab', 34:'Saba', 35:'Fatir', 36:'Ya-Sin',
        37:'As-Saffat', 38:'Sad', 39:'Az-Zumar', 40:'Ghafir',
        41:'Fussilat', 42:'Ash-Shura', 43:'Az-Zukhruf', 44:'Ad-Dukhan',
        45:'Al-Jathiyah', 46:'Al-Ahqaf', 47:'Muhammad', 48:'Al-Fath',
        49:'Al-Hujurat', 50:'Qaf', 51:'Adh-Dhariyat', 52:'At-Tur',
        53:'An-Najm', 54:'Al-Qamar', 55:'Ar-Rahman', 56:'Al-Waqi\'ah',
        57:'Al-Hadid', 58:'Al-Mujadila', 59:'Al-Hashr', 60:'Al-Mumtahanah',
        61:'As-Saf', 62:'Al-Jumu\'ah', 63:'Al-Munafiqun', 64:'At-Taghabun',
        65:'At-Talaq', 66:'At-Tahrim', 67:'Al-Mulk', 68:'Al-Qalam',
        69:'Al-Haqqah', 70:'Al-Ma\'arij', 71:'Nuh', 72:'Al-Jinn',
        73:'Al-Muzzammil', 74:'Al-Muddaththir', 75:'Al-Qiyamah', 76:'Al-Insan',
        77:'Al-Mursalat', 78:'An-Naba', 79:'An-Nazi\'at', 80:'\'Abasa',
        81:'At-Takwir', 82:'Al-Infitar', 83:'Al-Mutaffifin', 84:'Al-Inshiqaq',
        85:'Al-Buruj', 86:'At-Tariq', 87:'Al-A\'la', 88:'Al-Ghashiyah',
        89:'Al-Fajr', 90:'Al-Balad', 91:'Ash-Shams', 92:'Al-Layl',
        93:'Ad-Duha', 94:'Ash-Sharh', 95:'At-Tin', 96:'Al-\'Alaq',
        97:'Al-Qadr', 98:'Al-Bayyinah', 99:'Az-Zalzalah', 100:'Al-\'Adiyat',
        101:'Al-Qari\'ah', 102:'At-Takathur', 103:'Al-\'Asr', 104:'Al-Humazah',
        105:'Al-Fil', 106:'Quraysh', 107:'Al-Ma\'un', 108:'Al-Kawthar',
        109:'Al-Kafirun', 110:'An-Nasr', 111:'Al-Masad', 112:'Al-Ikhlas',
        113:'Al-Falaq', 114:'An-Nas',
    }

    by_surah = defaultdict(list)
    for e in all_entries_sorted:
        ref = e.get('ref', '')
        m = re.search(r'(\d+)[:.](\d)', ref)
        if m:
            s = int(m.group(1))
            by_surah[s].append((html_mod.escape(ref), entry_pages_map.get(e['id'], '—')))

    col_html = ''
    for s_num in sorted(by_surah.keys()):
        sname = SURAH_NAMES.get(s_num, '')
        col_html += f'<div class="surah-head"><div class="surah-num">Surah {s_num}</div><div class="surah-name">{html_mod.escape(sname)}</div></div>\n'
        for ref, pg in by_surah[s_num]:
            col_html += f'<div class="vx"><span class="vx-ref">{ref}</span><span class="vx-dots"></span><span class="vx-pg">{pg}</span></div>\n'

    return f"""\
<div class="page" style="height:auto;min-height:945px;">
  <div class="page-inner" style="position:relative;overflow:visible;padding-bottom:40px;">
    <div class="vi-head">Quran Verse Index</div>
    <div class="vi-sub">Volume I &middot; The Quran &middot; All 282 entries</div>
    <div class="vi-rule"></div>
    <div class="vi-columns">
      {col_html}
    </div>
    <div class="vi-pgnum">602</div>
  </div>
</div>
"""

# ── Main build ───────────────────────────────────────────────────────────────

def build():
    print("Parsing quran.html entry content...")
    contents = parse_entries()
    print(f"  Parsed {len(contents)} entries")

    print("Loading catalog-entries.json...")
    with open(CATALOG, 'r', encoding='utf-8') as f:
        all_entries = json.load(f)
    quran = [e for e in all_entries if e.get('source') == 'quran']
    print(f"  {len(quran)} quran entries")

    by_chapter = {i: [] for i in range(1, 24)}
    excluded = 0
    for e in quran:
        eid = e['id']
        if eid in EXCLUDE_IDS:
            excluded += 1
            continue
        ch = assign_chapter(eid, e.get('categories', []))
        by_chapter[ch].append(e)

    for ch in range(1, 24):
        by_chapter[ch].sort(key=lambda e: STRENGTH_ORDER.get(e.get('strength', '').lower(), 1))

    total = sum(len(v) for v in by_chapter.values())
    active_chapters = sum(1 for v in by_chapter.values() if v)
    print(f"  {total} entries assigned ({excluded} excluded), {active_chapters} chapters")
    for ch in range(1, 24):
        n = len(by_chapter[ch])
        if n:
            print(f"    Ch.{ch:2d} {CHAPTERS[ch][0]}: {n}")

    # Build HTML
    print("\nGenerating HTML...")
    parts = []

    # Document head
    parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Analyzing Islam — Volume I: The Quran</title>
<style>{CSS}</style>
</head>
<body>
""")

    # ── SECTION 1: COVERS ──
    parts.append(sec_label("Section 1 — Covers"))
    parts.append(page_label("Front Cover"))
    parts.append(front_cover())
    parts.append(page_label("Back Cover"))
    parts.append(back_cover())

    # ── SECTION 2: HALF-TITLE ──
    parts.append(sec_label("Section 2 — Half-Title"))
    parts.append(half_title(1))

    # ── SECTION 3: TITLE PAGE ──
    parts.append(sec_label("Section 3 — Title Page"))
    parts.append(title_page(2))

    # ── SECTION 4: COPYRIGHT ──
    parts.append(sec_label("Section 4 — Copyright"))
    parts.append(copyright_page(3))

    # ── SECTION 5: TABLE OF CONTENTS ──
    parts.append(sec_label("Section 5 — Table of Contents"))
    parts.append(toc_page(by_chapter, 4))

    # ── SECTION 6: FOREWORD ──
    parts.append(sec_label("Section 6 — Foreword"))
    parts.append(page_label("Foreword (1 of 3)"))
    fw = foreword_pages(5)
    # Split foreword into labeled pages
    fw_pages = fw.split('<div class="page">')
    for i, fp in enumerate(fw_pages):
        if not fp.strip():
            continue
        lbl = f"Foreword ({i} of 3)" if i > 0 else "Foreword"
        parts.append('<div class="page">' + fp)

    # ── SECTION 7: ABBREVIATIONS ──
    parts.append(sec_label("Section 7 — Abbreviations & Reference Guide"))
    ab = abbreviations_pages(8)
    ab_pages = ab.split('<div class="page">')
    for i, ap in enumerate(ab_pages):
        if not ap.strip():
            continue
        parts.append(page_label(f"Abbreviations ({i} of 2)"))
        parts.append('<div class="page">' + ap)

    # ── SECTION 8: PART OPENER ──
    parts.append(sec_label("Section 8 — Part Opener: The Quran"))
    parts.append(part_opener(total, active_chapters, 10))

    # ── SECTION 9: SOURCE INTRODUCTION ──
    parts.append(sec_label("Section 9 — Source Introduction: The Quran"))
    parts.append(source_intro(11))

    # ── SECTION 10: CHAPTERS & ENTRIES ──
    parts.append(sec_label("Section 10 — The Quran: Chapters & Entries"))

    entry_pages_map = {}  # eid → page number; ch_num → chapter start page
    current_page = 1

    all_chapter_html = []
    for ch in range(1, 24):
        entries = by_chapter[ch]
        if not entries:
            continue
        ch_name, ch_desc = CHAPTERS[ch]
        entry_pages_map[ch] = current_page

        # Chapter opener
        opener_html, current_page = chapter_opener_html(ch, ch_name, ch_desc, entries, current_page)
        all_chapter_html.append(f'\n<!-- Chapter {ch}: {ch_name} -->\n')
        all_chapter_html.append(page_label(f"Chapter {ch}: {ch_name}"))
        all_chapter_html.append(opener_html)

        # Entry pages
        ep_html, current_page = chapter_entry_pages(ch, ch_name, entries, contents, current_page)
        all_chapter_html.append(ep_html)

        # Track entry page numbers (approximate - first entry of chapter)
        pg = entry_pages_map[ch] + 1  # opener is +1 from chapter start
        for e in entries:
            entry_pages_map[e['id']] = pg
            pg += 2 if contents.get(e['id'], {}).get('fails') else 1

    parts.extend(all_chapter_html)

    # ── SECTION 11: GENERAL INDEX ──
    parts.append(sec_label("Section 11 — General Index"))
    parts.append(page_label("General Index — Page 1"))
    parts.append(general_index_html(by_chapter, entry_pages_map))

    # ── SECTION 12: QURAN VERSE INDEX ──
    parts.append(sec_label("Section 12 — Quran Verse Index"))
    parts.append(page_label("Quran Verse Index — Page 1"))
    all_quran_sorted = []
    for ch in range(1, 24):
        all_quran_sorted.extend(by_chapter[ch])
    parts.append(quran_verse_index_html(all_quran_sorted, entry_pages_map))

    parts.append('</body>\n</html>\n')

    print(f"\nWriting output...")
    output = ''.join(parts)
    OUT.write_text(output, encoding='utf-8')
    size_kb = len(output) // 1024
    print(f"Done. {size_kb} KB written to:\n  {OUT}")

if __name__ == '__main__':
    build()
