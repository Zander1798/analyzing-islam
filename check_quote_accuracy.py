"""
Semantic quotation checker: for each entry with a <blockquote>, extract the quoted
text and compare it to the actual text at the primary-ref anchor.

Flags entries where the key content words in the blockquote have <25% overlap with
the anchor text (after stop-word removal). This catches cases where the cited source
says something completely different from what the entry claims.

Output: sorted by overlap score (lowest first) so genuine mismatches surface first.
"""

import os, re, html as html_mod
from collections import defaultdict

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
A    = os.path.join(SITE, "arguments")
CAT  = os.path.join(SITE, "catalog")

STOP = set("""the a an of in to is was were are be been being have has had do does did
will would could should may might shall for from with by at on or and but not this
that these those his her its their our your i he she we they it as if so no nor yet
when where who what which while then than after before since though although because
even only also just more most very well such both other another each all any few many
much some into out up down over under about between through during among against along
without within upon whom whose him them us me my your its his her its their our""".split())

QURAN_SRC = "quran"

# ─── reader index ─────────────────────────────────────────────────────────────

_reader_cache = {}

def reader_html(source):
    if source not in _reader_cache:
        p = os.path.join(SITE, "read", f"{source}.html")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                _reader_cache[source] = f.read()
        else:
            _reader_cache[source] = ""
    return _reader_cache[source]


def build_hadith_index(source):
    """Map anchor_id -> set of content words."""
    c = reader_html(source)
    idx = {}
    positions = [(m.group(1), m.start()) for m in re.finditer(r'id="(h\d+)"', c, re.IGNORECASE)]
    for i, (aid, start) in enumerate(positions):
        end = positions[i+1][1] if i+1 < len(positions) else len(c)
        block = re.sub(r"<[^>]+>", " ", c[start:end])
        text = html_mod.unescape(re.sub(r"\s+", " ", block)).lower()
        idx[aid] = set(w for w in re.findall(r"\b[a-z]{3,}\b", text) if w not in STOP)
    return idx


def build_quran_index():
    c = reader_html("quran")
    idx = {}
    positions = [(int(m.group(1)), int(m.group(2)), m.start())
                 for m in re.finditer(r'id="s(\d+)v(\d+)"', c, re.IGNORECASE)]
    for i, (s, v, start) in enumerate(positions):
        end = positions[i+1][2] if i+1 < len(positions) else len(c)
        block = re.sub(r"<[^>]+>", " ", c[start:end])
        text = html_mod.unescape(re.sub(r"\s+", " ", block)).lower()
        idx[(s, v)] = set(w for w in re.findall(r"\b[a-z]{3,}\b", text) if w not in STOP)
    return idx


_hadith_indexes = {}
_quran_index = None

def get_hadith_words(source, anchor):
    if source not in _hadith_indexes:
        _hadith_indexes[source] = build_hadith_index(source)
    return _hadith_indexes[source].get(anchor, set())

def get_quran_words(surah, verse):
    global _quran_index
    if _quran_index is None:
        _quran_index = build_quran_index()
    return _quran_index.get((surah, verse), set())


# ─── HTML parsing helpers ──────────────────────────────────────────────────────

def strip_html(s):
    return html_mod.unescape(re.sub(r"<[^>]+>", " ", s))

def content_words(text):
    return set(w for w in re.findall(r"\b[a-z]{3,}\b", text.lower()) if w not in STOP)

def overlap(a_words, b_words):
    if not a_words:
        return 1.0
    return len(a_words & b_words) / len(a_words)


# ─── entry parser ──────────────────────────────────────────────────────────────

ENTRY_RE   = re.compile(r'<div\s+class="entry"[^>]*id="([^"]+)"[^>]*>(.*?)(?=<div\s+class="entry"|\Z)', re.DOTALL | re.IGNORECASE)
BQ_RE      = re.compile(r'<blockquote>(.*?)</blockquote>', re.DOTALL | re.IGNORECASE)
HREF_RE    = re.compile(r'href="[^"]*read/([^/"]+)\.html#(h\d+|s\d+v\d+)"', re.IGNORECASE)

def parse_entries(html):
    """Yield (entry_id, blockquote_text, [(source, anchor), ...]) tuples."""
    for m in ENTRY_RE.finditer(html):
        entry_id = m.group(1)
        block    = m.group(2)

        # Collect all blockquote text
        bq_text = " ".join(strip_html(bq.group(1)) for bq in BQ_RE.finditer(block))
        if not bq_text.strip():
            continue  # no blockquote → skip

        # Collect all links inside <span class="ref"> (primary refs)
        span_m = re.search(r'<span\s+class="ref"[^>]*>(.*?)</span>', block, re.IGNORECASE | re.DOTALL)
        if not span_m:
            continue
        primary_links = [(s, a) for s, a in HREF_RE.findall(span_m.group(1))]
        if not primary_links:
            continue

        yield entry_id, bq_text, primary_links


# ─── main check ───────────────────────────────────────────────────────────────

THRESHOLD = 0.20   # flag if overlap < 20%
MIN_WORDS = 4      # only check blockquotes with >= 4 content words

flags = []

def check_file(path, rel):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    for entry_id, bq_text, links in parse_entries(html):
        bq_words = content_words(bq_text)
        if len(bq_words) < MIN_WORDS:
            continue
        for source, anchor in links:
            if anchor.startswith("s") and "v" in anchor:
                # Quran
                m = re.match(r"s(\d+)v(\d+)", anchor, re.IGNORECASE)
                if not m:
                    continue
                anchor_words = get_quran_words(int(m.group(1)), int(m.group(2)))
            else:
                anchor_words = get_hadith_words(source, anchor)
            if not anchor_words:
                continue  # anchor not in reader — already flagged by ID checker
            score = overlap(bq_words, anchor_words)
            if score < THRESHOLD:
                flags.append({
                    "file": rel,
                    "entry": entry_id,
                    "source": source,
                    "anchor": anchor,
                    "score": score,
                    "bq": bq_text[:200],
                    "at": " ".join(list(anchor_words)[:20]),
                })


# catalog files
for fname in os.listdir(CAT):
    if fname.endswith(".html"):
        check_file(os.path.join(CAT, fname), f"catalog/{fname}")

# dossier files
for root, dirs, files in os.walk(A):
    for fname in files:
        if fname.endswith(".html"):
            rel = os.path.relpath(os.path.join(root, fname), SITE)
            check_file(os.path.join(root, fname), rel)

# ─── report ───────────────────────────────────────────────────────────────────

flags.sort(key=lambda x: x["score"])

print(f"\n{'='*70}")
print(f"QUOTE ACCURACY FLAGS: {len(flags)} entries below {THRESHOLD*100:.0f}% overlap")
print(f"{'='*70}\n")

for f in flags:
    print(f"FILE : {f['file']}")
    print(f"ENTRY: {f['entry']}")
    print(f"CITED: {f['source']}#{f['anchor']}  overlap={f['score']:.0%}")
    print(f"BQ   : {f['bq'][:180]}")
    print(f"AT   : {f['at'][:160]}")
    print()

print(f"\nTotal: {len(flags)} flags")
