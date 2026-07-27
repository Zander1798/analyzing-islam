#!/usr/bin/env python3
"""Build Analyzing Islam Vol I — The Quran complete mock-up HTML."""

import re, json, math, html as html_mod
from pathlib import Path

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG   = BASE / "site/assets/data/catalog-entries.json"
QURAN_SRC = BASE / "site/catalog/quran.html"
BOOK_FILE = BASE / "book-design/vol1-quran/Analyzing Islam Vol I — The Quran.html"

# ── Chapter definitions ───────────────────────────────────────────────────

CHAPTERS = {
    1:  ("Abrogation",
         "The doctrine of <em>naskh</em> (abrogation) holds that later Quranic verses can supersede earlier ones "
         "while both remain in the written text. The Quran references this principle explicitly at Q 2:106 and "
         "Q 16:101. This chapter examines the theological and logical problems that arise when a supposedly perfect, "
         "eternal divine text requires internal revision — and the implications for claims of divine omniscience and consistency."),
    2:  ("Scripture Integrity",
         "The Quran presents itself as a perfectly preserved, uniquely clear, and self-authenticating revelation. "
         "This chapter examines the passages and historical facts that challenge those claims: the burning of variant "
         "codices under Uthman, the acknowledgement of verses no one knows the interpretation of, the Islamic Dilemma "
         "between Quranic endorsement of the Bible and the doctrine of <em>tahrif</em>, and internal claims that "
         "undermine the text’s own standard of clarity and permanence."),
    3:  ("Contradictions",
         "A text claimed to be the direct word of an omniscient God is expected to be internally consistent. "
         "This chapter catalogues passages in the Quran that contradict other Quranic passages — in arithmetic, "
         "cosmology, prophetic history, and law — and examines the apologetic strategies employed to reconcile them."),
    4:  ("Logical Inconsistency",
         "Beyond factual contradiction, several Quranic passages generate problems of logical form: "
         "self-refuting claims, arguments that assume what they are meant to prove, divine attributes that "
         "cannot coherently coexist, and instructions whose application requires information the text withholds. "
         "This chapter collects passages where the problem is not factual but structural."),
    5:  ("Allah's Character",
         "Islamic theology attributes to Allah a set of perfections — omniscience, omnipotence, justice, mercy. "
         "A number of Quranic passages sit in tension with one or more of those attributes: a God who seals "
         "disbelievers’ hearts and then punishes them for disbelief, who engineers deception, who creates "
         "beings destined for Hell. This chapter examines passages where the Quranic portrait of God raises "
         "philosophical difficulties that standard defences do not resolve."),
    6:  ("Cosmology",
         "A number of Quranic passages describe the physical universe in ways that reflect pre-scientific "
         "cosmological assumptions rather than observed reality — including a sun that sets in a muddy spring, "
         "a seven-layered sky, sperm produced between the backbone and ribs, and the creation of the heavens and "
         "earth in six days. This chapter examines these passages against the backdrop of what was believed in "
         "7th-century Arabia and what is known today."),
    7:  ("Pre-Islamic Borrowings",
         "Several Quranic narratives have direct parallels in Jewish midrashic literature, Christian apocryphal "
         "gospels, Zoroastrian texts, and pre-Islamic Arabian legend — including stories, characters, and "
         "details not found in canonical Jewish or Christian scripture. This chapter examines passages where the "
         "source material predates Islam and asks what the presence of that material implies for claims of direct divine revelation."),
    8:  ("Prophetic Character",
         "The Quran presents Muhammad as the exemplary moral model (<em>uswa hasana</em>). Several passages, "
         "however, describe a prophet who required divine reassurance, who benefited personally from his own "
         "revelations, who was rebuked by Allah for specific decisions, and whose conduct in particular episodes "
         "raises ethical questions the text itself registers without resolving. This chapter examines those passages."),
    9:  ("Prophetic Privileges",
         "A cluster of Quranic verses grants Muhammad exemptions and permissions explicitly denied to ordinary "
         "believers — additional wives beyond the limit of four, marriage to his adopted son’s divorcee, "
         "a personal cut of war spoils, permission for women to offer themselves to him without a dowry. "
         "This chapter examines the theological and ethical problems created when divine revelation is used to "
         "resolve a prophet’s personal domestic circumstances."),
    10: ("Jesus / Christology",
         "The Quran contains a substantial Christology — an account of Jesus that agrees with some Christian "
         "claims, categorically denies others, and adds details found in no earlier canonical source. This chapter "
         "examines passages where the Quranic portrait of Jesus contradicts the historical record, borrows from "
         "Christian apocrypha, or creates internal contradictions within the Quran’s own Christological account."),
    11: ("Women & Sexual Issues",
         "The Quran legislates extensively on the status of women, marriage, sexual access, and related matters. "
         "Several passages establish legal and social hierarchies that contemporary ethics regards as discriminatory, "
         "permit practices modern law criminalises, or create internal inconsistencies that Islamic jurisprudence "
         "has never fully resolved. This chapter examines those passages and the apologetic responses they have generated."),
    12: ("Child Marriage",
         "Q 65:4 sets out divorce procedures for wives who have not yet menstruated — an explicit Quranic provision "
         "for marriage to pre-pubescent girls. This chapter examines the verse, its classical tafsir, the apologetic "
         "strategies used to contextualise it, and why those strategies do not remove the ethical problem the text creates."),
    13: ("LGBTQ / Gender",
         "The Quran’s account of Lot’s people and related passages have been read by the classical tradition "
         "as a divine condemnation of same-sex relations. This chapter examines those passages, the related verse "
         "on gender non-conformity, and the ethical problems they raise for claims that Islam is compatible with "
         "modern conceptions of human dignity."),
    14: ("Slavery & Captives",
         "The Quran regulates slavery rather than prohibiting it — specifying procedures for manumission, "
         "permitting sexual access to female captives, and treating enslaved people as a recognised legal category. "
         "This chapter examines the relevant passages, their classical interpretations, and the apologetic argument "
         "that Quranic regulation represents progressive reform."),
    15: ("Warfare & Jihad",
         "Several Quranic verses command violence against non-Muslims in terms that admit no obvious limiting "
         "context — commanding believers to kill, fight, or subjugate until conversion or submission is "
         "obtained. This chapter examines passages where the plain reading authorises offensive warfare, the "
         "theological function of those commands within Islamic jurisprudence, and why the most common apologetic "
         "responses do not resolve the plain-text problem."),
    16: ("Apostasy & Blasphemy",
         "The Quran does not state an explicit death penalty for apostasy, but several passages are read by "
         "classical jurists as endorsing it, and Q 4:89 is the key proof-text for that ruling. This chapter "
         "examines the Quranic basis for apostasy law, the related passages on blaspheming the Prophet, and the "
         "apologetic claim that the Quran mandates no earthly punishment for leaving Islam."),
    17: ("Governance",
         "A number of passages establish that sovereignty belongs to Allah alone and that legislation is his "
         "exclusive prerogative — the canonical proof-texts for Islamic theocratic governance. Others mandate "
         "fixed punishments for specific crimes that a human legislature cannot reduce. This chapter examines the "
         "political theology of the Quran and the challenges it poses for democratic and pluralist governance."),
    18: ("Disbelievers & Moral Problems",
         "The Quran characterises non-Muslims in terms ranging from misguided to irredeemably corrupt, "
         "the worst of creatures, and objects of divine curse. Several passages mandate social and legal "
         "discrimination against them. This chapter collects passages where the Quranic treatment of "
         "non-Muslims raises ethical problems — either in the characterisation itself or in the "
         "practical consequences that characterisation has historically generated."),
    19: ("Antisemitism",
         "The Quran contains direct derogatory characterisations of Jews as a group: divine transformation "
         "into apes and pigs, fabricated theological claims attributed to them, and placement at the top of a "
         "ranking of hostility toward believers. This chapter examines those passages and the apologetic "
         "argument that they are context-specific rather than general statements about Jewish people."),
    20: ("Paradise",
         "The Quran’s descriptions of paradise are detailed and physical: gardens of flowing rivers, "
         "the eternal virgin houris, seventy-two companions, rivers of wine and honey. This chapter examines "
         "passages where those descriptions raise moral problems — a paradise designed for male pleasure, "
         "a Hell engineered for maximum suffering, and the incoherence of promising wine in paradise after "
         "condemning it on earth."),
    21: ("Strange",
         "A number of Quranic passages describe supernatural events, historical claims, or cosmological "
         "assertions that resist straightforward naturalisation — stars as missiles thrown at eavesdropping "
         "jinn, a village left dead for a century with unspoiled food, ants that converse with Solomon, "
         "mountains that pass like clouds. This chapter collects those passages and examines why the "
         "standard apologetic readings do not resolve the problems they create."),
    22: ("Magic & Ritual",
         "The Quran legislates extensively on ritual purity and acknowledges a world populated by jinn, "
         "sorcerers, and supernatural entities. Several passages describe magic as real and dangerous, "
         "attribute miraculous powers to prophets, and create ritual requirements whose scriptural basis "
         "is internally contradictory. This chapter examines passages in each of those categories."),
    23: ("Animals",
         "Several Quranic passages about animals create scientific, moral, or theological problems: "
         "bees that receive divine inspiration, animals that form communities like humans, Solomon commanding "
         "the ants, and the killing of a specific bird species justified by religious reward. "
         "This chapter examines those passages and the apologetic arguments surrounding them."),
}

# ── Chapter assignment ────────────────────────────────────────────────────

# Priority order: first matching tag wins → that chapter
TAG_PRIORITY = [
    ("antisemitism", 19), ("childmarriage", 12), ("apostasy", 16),
    ("privileges", 9),    ("jesus", 10),          ("abrogation", 1),
    ("warfare", 15),      ("governance", 17),     ("preislamic", 7),
    ("scripture", 2),     ("allah", 5),           ("cosmology", 6),
    ("science", 6),       ("magic", 22),          ("slavery", 14),
    ("women", 11),        ("sexual", 11),         ("hudud", 17),
    ("prophet", 8),       ("animals", 23),        ("ritual", 22),
    ("contradiction", 3), ("logic", 4),           ("paradise", 20),
    ("hell", 20),         ("disbelievers", 18),   ("morality", 18),
    ("strange", 21),      ("incest", 13),         ("gross-vile", 13),
]

ID_OVERRIDES = {
    # Seven Sleepers → Pre-Islamic (jesus tag would win otherwise)
    "the-seven-sleepers-of-ephesus-a-christian-legend-as-quranic-13829e66": 7,
    # Female slaves sexual access → Women (slavery tag would win otherwise)
    "sexual-access-to-married-female-slaves-right-hand-possesses-25cd8f4b": 11,
    # Wudu/tayammum → Magic & Ritual (preislamic would win otherwise)
    "quran-wudu-tayammum-touching-women": 22,
    # Blind man rebuke → Prophetic Character (scripture would win otherwise)
    "quran-abasa-frowned-blind-rebuke": 8,
    # Inheritance fractions → Logical Inconsistency (governance would win otherwise)
    "quran-inheritance-fractions-do-not-sum": 4,
    # Gestation arithmetic → Cosmology (governance would win otherwise)
    "quran-46-15-31-14-six-month-gestation-arithmetic": 6,
    # Chain/pus food hell → Paradise (allah would win otherwise)
    "quran-69-32-seventy-cubit-chain-ghislin-food": 20,
    # Paradise garden → Paradise (sexual would win otherwise)
    "paradise-as-physical-pleasure-garden-with-purified-spouses-65756a43": 20,
    # Houris → Paradise (women would win otherwise)
    "the-houris-eternal-virgins-as-paradise-reward-d8c254e9": 20,
    # Quran as cure → Scripture Integrity (science would give Ch.6)
    "quran-quran-as-healing": 2,
    # Islamic Dilemma → Scripture Integrity (jesus would win otherwise)
    "islamic-dilemma": 2,
    # Quran endorses judge by own books → Scripture Integrity
    "the-quran-endorses-jews-and-christians-to-judge-by-their-own-32929162": 2,
    # Tahrif / no-change → Scripture Integrity
    "no-one-can-change-the-words-of-allah-yet-tahrif-is-the-centr-d98f36e4": 2,
}

EXCLUDE_IDS = {
    # Duplicate of quran-s5v38-hand-amputation-theft
    "amputate-the-hand-of-the-thief-regardless-of-circumstance-4104d45b",
    # Quran/hadith cross-ref duplicate of fornication lashes entry
    "one-hundred-lashes-for-fornication-yet-the-hadith-demands-st-f805f912",
}

def assign_chapter(eid, categories):
    if eid in ID_OVERRIDES:
        return ID_OVERRIDES[eid]
    for tag, ch in TAG_PRIORITY:
        if tag in categories:
            return ch
    return 18  # fallback

# ── Parse quran.html for entry content ───────────────────────────────────

def clean_html(s):
    """Remove links but keep em/strong/br; collapse whitespace."""
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
        end = opens[i + 1].start() if i + 1 < len(opens) else len(raw)
        chunk = raw[m.start():end]

        # Blockquote
        bq_m = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', chunk, re.DOTALL)
        quote_html = ''
        if bq_m:
            q = bq_m.group(1)
            q = re.sub(r'<p[^>]*>', '', q)
            q = re.sub(r'</p>', ' ', q)
            q = clean_html(q).strip()
            quote_html = q

        # Section bodies via h4 split
        h4_parts = re.split(r'<h4[^>]*>', chunk)
        sections = {'says': '', 'problem': '', 'response': '', 'fails': ''}

        for part in h4_parts[1:]:
            end_tag = part.find('</h4>')
            if end_tag == -1:
                continue
            header = part[:end_tag].lower().strip()
            body = part[end_tag + 5:]
            # Extract <p> content
            paras = re.findall(r'<p[^>]*>(.*?)</p>', body, re.DOTALL)
            para_html = '\n'.join(
                f'<p>{clean_html(p.strip())}</p>' for p in paras if p.strip()
            )
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

# ── HTML generation helpers ───────────────────────────────────────────────

STRENGTH_LABEL = {'basic': 'Basic', 'moderate': 'Moderate', 'strong': 'Strong'}
STRENGTH_CLASS = {'basic': 'strength-basic', 'moderate': 'strength-moderate', 'strong': 'strength-strong'}

def entry_html(e, content, ch_name):
    eid      = e['id']
    title    = html_mod.escape(e.get('title', ''))
    ref      = html_mod.escape(e.get('ref', ''))
    strength = e.get('strength', '').lower()
    scls     = STRENGTH_CLASS.get(strength, '')
    slbl     = STRENGTH_LABEL.get(strength, strength.title())

    c = content.get(eid, {})
    quote    = c.get('quote', '')
    says     = c.get('says', '<p><em>[content not extracted]</em></p>')
    problem  = c.get('problem', '')
    response = c.get('response', '')
    fails    = c.get('fails', '')

    quote_block = f'<blockquote>{quote}</blockquote>' if quote else ''

    def section(label, body):
        return f'<h4>{label}</h4>\n{body}' if body else ''

    return f"""<div class="entry">
  <div class="entry-title">{title}</div>
  <div class="entry-meta">
    <span class="tag ch-tag">{html_mod.escape(ch_name)}</span>
    <span class="tag {scls}">{slbl}</span>
    <span class="entry-ref">{ref}</span>
  </div>
  {quote_block}
  {section('What the verse says', says)}
  {section('Why this is a problem', problem)}
  {section('The Muslim response', response)}
  {section('Why it fails', fails)}
</div>"""


def chapter_opener_html(ch_num, ch_name, ch_desc, entries):
    PAGE1_MAX = 18   # entries on first page (room for title/desc block)
    CONT_MAX  = 22   # entries per continuation page
    count     = len(entries)
    ch_esc    = html_mod.escape(ch_name)

    def _rows(batch, start_n):
        rows = ''
        for n, e in enumerate(batch, start_n):
            s  = e.get('strength', '').lower()
            sc = {'basic': 'basic', 'moderate': 'moderate', 'strong': 'strong'}.get(s, '')
            rows += (f'<div class="entry-row">'
                     f'<span class="entry-row-num">{n}</span>'
                     f'<span class="entry-row-title">{html_mod.escape(e.get("title",""))}</span>'
                     f'<span class="entry-row-ref">{html_mod.escape(e.get("ref",""))}</span>'
                     f'<span class="etag {sc}">{s.title()}</span>'
                     f'</div>\n')
        return rows

    # ── Page 1: full chapter header + first batch ──────────────────────────
    rows1 = _rows(entries[:PAGE1_MAX], 1)
    html = f"""<div class="page-label">Chapter {ch_num}: {ch_esc}</div>
<div class="page">
  <div class="page-inner">
    <div class="chapter-breadcrumb">The Quran &middot; Chapter {ch_num}</div>
    <div class="chapter-title">{ch_esc}</div>
    <div class="chapter-rule"></div>
    <div class="chapter-desc">{ch_desc}</div>
    <div class="entry-list">
{rows1}    </div>
    <div class="chapter-footer">
      <div class="chapter-footer-rule"></div>
      <div class="chapter-footer-row">
        <div class="chapter-entry-count"><span>{count}</span> entr{"y" if count==1 else "ies"}</div>
        <div class="chapter-source-label">The Quran</div>
      </div>
    </div>
  </div>
</div>
"""

    # ── Continuation pages ─────────────────────────────────────────────────
    rh = (f'<div class="rh-row">'
          f'<span class="running-chapter">The Quran &middot; Chapter {ch_num} &middot; {ch_esc}</span>'
          f'<span class="running-page"></span></div>')

    remaining = entries[PAGE1_MAX:]
    offset    = PAGE1_MAX + 1  # display number of first entry on cont. page
    while remaining:
        batch     = remaining[:CONT_MAX]
        remaining = remaining[CONT_MAX:]
        rows_c    = _rows(batch, offset)
        offset   += len(batch)
        html += f"""<div class="page">
  <div class="page-inner">
    {rh}
    <div class="entry-list cont-list">
{rows_c}    </div>
  </div>
</div>
"""

    return html


JS_PAGINATOR = ""


def _est_h(html):
    """Estimate rendered pixel height of an HTML content fragment."""
    h = 0
    # Entry title: Didot 20px lh 1.25, ~56 chars/line, mb 10px
    m = re.search(r'class="entry-title"[^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        h += max(1, math.ceil(len(text) / 56)) * 25 + 10
    # Entry meta: fixed ~27px
    if 'entry-meta' in html:
        h += 27
    # Blockquote: Didot 13.5px italic lh 1.6, ~84 chars/line, padding+margin 26px
    bq = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', html, re.DOTALL)
    if bq:
        text = re.sub(r'<[^>]+>', '', bq.group(1)).strip()
        h += max(1, math.ceil(len(text) / 84)) * 22 + 26
    # H4 headings: mt 14 + text 13 + mb 6 = 33px each
    h += len(re.findall(r'<h4[^>]*>', html)) * 33
    # Paragraphs: system-ui 13.5px lh 1.75 (~23.6px/line), ~82 chars/line, mb 8px
    for pm in re.finditer(r'<p[^>]*>(.*?)</p>', html, re.DOTALL):
        text = re.sub(r'<[^>]+>', '', pm.group(1)).strip()
        if text:
            h += max(1, math.ceil(len(text) / 82)) * 26 + 8
    return h


def _fine_chunks(inner_html):
    """Split entry inner HTML into paragraph-level chunks for greedy page filling.
    h4 headings are emitted as standalone chunks so they stay on page 1 when
    space permits; individual paragraphs follow as separate chunks."""
    chunks = []
    h4_pos = [m.start() for m in re.finditer(r'<h4>', inner_html)]

    # Header block (title + meta + blockquote)
    header_end = h4_pos[0] if h4_pos else len(inner_html)
    header = inner_html[:header_end]
    if header.strip():
        chunks.append(header)

    for i, pos in enumerate(h4_pos):
        end     = h4_pos[i+1] if i+1 < len(h4_pos) else len(inner_html)
        section = inner_html[pos:end]
        p_list  = list(re.finditer(r'<p[^>]*>', section))

        if len(p_list) == 0:
            # No paragraphs — just the h4 itself
            chunks.append(section)
        else:
            first_p_start = p_list[0].start()
            # h4 alone (text before first <p>)
            h4_chunk = section[:first_p_start]
            if h4_chunk.strip():
                chunks.append(h4_chunk)
            # Each paragraph individually
            for j in range(len(p_list)):
                p_start = p_list[j].start()
                p_end   = p_list[j+1].start() if j+1 < len(p_list) else len(section)
                chunks.append(section[p_start:p_end])

    return chunks


def _sentence_split(para_html):
    """Split a <p>...</p> chunk into (open_tag, [sentence_texts], close_tag).
    Returns None if the chunk is not a plain paragraph or has only one sentence."""
    m = re.match(r'(<p[^>]*>)(.*?)(</p>)', para_html.strip(), re.DOTALL)
    if not m:
        return None
    open_tag, body, close_tag = m.groups()
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z“‘”’"])', body.strip())
    return (open_tag, parts, close_tag) if len(parts) > 1 else None


def chapter_entry_pages(ch_num, ch_name, entries, contents):
    """Each entry gets exactly 2 pages (front + back of a leaf).
    Content is split at paragraph/sentence boundaries so page 1 fills tightly."""
    PAGE_H = 830   # estimated-px budget; 26px/line paragraphs, 24px/line sentences
    ch_esc = html_mod.escape(ch_name)
    rh = (f'<div class="rh-row">'
          f'<span class="running-chapter">The Quran &middot; Chapter {ch_num} &middot; {ch_esc}</span>'
          f'<span class="running-page"></span></div>')

    def make_page(inner_html):
        return (f'<div class="page entry-page">\n'
                f'  <div class="page-inner">\n    {rh}\n{inner_html}\n  </div>\n</div>')

    pages = []
    for e in entries:
        ehtml = entry_html(e, contents, ch_name)
        title = html_mod.escape(e.get('title', ''))

        # Strip outer <div class="entry"> to get bare inner content
        inner = re.sub(r'^<div[^>]*class="entry"[^>]*>\s*', '', ehtml)
        inner = re.sub(r'\s*</div>\s*$', '', inner)

        # Greedy fill: paragraph-level, with sentence-level split at the boundary
        h_used   = 0
        p1_inner = ''
        p2_inner = ''
        on_p2    = False

        for ck in _fine_chunks(inner):
            ck_h = _est_h(ck)
            if not on_p2 and h_used + ck_h <= PAGE_H:
                p1_inner += ck
                h_used   += ck_h
            elif not on_p2:
                # Paragraph doesn't fit whole — try sentence-level split
                split = _sentence_split(ck)
                if split:
                    open_tag, sentences, close_tag = split
                    p1_sents = []
                    p2_sents = []
                    overflow_started = False
                    for s in sentences:
                        plain = re.sub(r'<[^>]+>', '', s)
                        s_h = max(1, math.ceil(len(plain) / 82)) * 26
                        if not overflow_started and h_used + s_h + 8 <= PAGE_H:
                            p1_sents.append(s)
                            h_used += s_h
                        else:
                            overflow_started = True
                            on_p2 = True
                            p2_sents.append(s)
                    if p1_sents:
                        p1_inner += open_tag + ' '.join(p1_sents) + close_tag
                        h_used += 8  # paragraph margin-bottom
                    if p2_sents:
                        p2_inner += open_tag + ' '.join(p2_sents) + close_tag
                else:
                    on_p2     = True
                    p2_inner += ck
            else:
                p2_inner += ck

        # Push orphan h4 (heading with no paragraph on p1) to page 2
        if p2_inner:
            orphan = re.search(r'(<h4[^>]*>[^<]*</h4>\s*)$', p1_inner.rstrip())
            if orphan:
                p2_inner  = orphan.group(1) + p2_inner
                p1_inner  = p1_inner[:orphan.start()]

        # Page 1
        pages.append(make_page(f'<div class="entry">\n{p1_inner}\n</div>'))

        # Page 2 — only if there's overflow content
        if p2_inner:
            pages.append(make_page(f'<div class="entry">\n{p2_inner}\n</div>'))

    return '\n'.join(pages)


# ── Main build ────────────────────────────────────────────────────────────

def build():
    print("Parsing quran.html entry content...")
    contents = parse_entries()
    print(f"  Parsed {len(contents)} entries from HTML")

    print("Loading catalog-entries.json...")
    with open(CATALOG, 'r', encoding='utf-8') as f:
        all_entries = json.load(f)
    quran = [e for e in all_entries if e['source'] == 'quran']
    print(f"  {len(quran)} quran entries in catalog")

    # Assign chapters
    by_chapter = {i: [] for i in range(1, 24)}
    excluded = 0
    for e in quran:
        eid = e['id']
        if eid in EXCLUDE_IDS:
            excluded += 1
            continue
        ch = assign_chapter(eid, e.get('categories', []))
        by_chapter[ch].append(e)

    total = sum(len(v) for v in by_chapter.values())
    print(f"  {total} entries assigned ({excluded} excluded)")
    for ch in range(1, 24):
        n = len(by_chapter[ch])
        if n:
            print(f"    Ch.{ch:2d} {CHAPTERS[ch][0]}: {n}")

    # Generate chapter HTML
    print("\nGenerating chapter HTML...")
    chapters_html = []
    chapters_html.append(
        '\n<!-- ══════════════════════════════════════════════════════════\n'
        '     SECTION 10 — CHAPTERS & ENTRIES\n'
        '══════════════════════════════════════════════════════════ -->\n'
        '<div class="section-divider">Section 10 — The Quran: 20 Chapters</div>\n'
    )
    strength_order = {'basic': 0, 'moderate': 1, 'strong': 2}
    for ch in range(1, 24):
        entries = sorted(by_chapter[ch], key=lambda e: strength_order.get(e.get('strength', ''), 1))
        if not entries:
            continue
        ch_name, ch_desc = CHAPTERS[ch]
        chapters_html.append(f'\n<!-- ── Chapter {ch}: {ch_name} ── -->\n')
        chapters_html.append(chapter_opener_html(ch, ch_name, ch_desc, entries))
        chapters_html.append(chapter_entry_pages(ch, ch_name, entries, contents))

    new_section = '\n'.join(chapters_html)

    # Splice into existing file
    print("Splicing into book file...")
    book = BOOK_FILE.read_text(encoding='utf-8')

    # Find Section 10 and Section 12 comment blocks
    def find_comment_start(text, label):
        idx = text.find(label)
        if idx == -1:
            return -1
        # Walk back to find the opening <!--
        start = text.rfind('<!--', 0, idx)
        return start

    s10 = find_comment_start(book, 'SECTION 10')
    s12 = find_comment_start(book, 'SECTION 12')

    if s10 == -1 or s12 == -1:
        print(f"ERROR: markers not found (sec10={s10}, sec12={s12}). Aborting.")
        return

    front = book[:s10]
    back  = book[s12:]

    output = front + new_section + '\n\n' + back

    BOOK_FILE.write_text(output, encoding='utf-8')
    print(f"Done. Wrote {len(output):,} chars ({len(output.splitlines()):,} lines) to:")
    print(f"  {BOOK_FILE}")


if __name__ == '__main__':
    build()
