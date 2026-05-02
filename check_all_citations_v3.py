"""
Comprehensive citation verifier v3.

Covers:
  - All hadith citations across catalog (site/catalog/) AND dossiers (site/arguments/)
  - All Quran citations across catalog AND dossiers
  - Hadith: ±50 search window (was ±15), thin-context threshold 5 words (was 8)
  - Quran: href/display cross-check (definite errors only, zero false-positive)

Quran check:
  Each <a href="...quran.html#sXvY">DISPLAY</a> is checked two ways:
  1. Does the anchor sXvY exist in the quran reader?
  2. Does the display text encode the same surah:verse as the href?
     (e.g. href=#s4v34 but display says "4:33" → definite error)

Hadith check:
  5-gram match of surrounding context against cited hadith text.
  Flags only when cited ID fails AND a nearby ID (±50) does match.
"""

import os, re, html as html_mod
from pathlib import Path

SITE     = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT_DIR  = os.path.join(SITE, "catalog")
ARG_DIR  = os.path.join(SITE, "arguments")
READ_DIR = os.path.join(SITE, "read")

HADITH_WINDOW = 50   # search ±50 IDs for nearby match
MIN_WORDS     = 5    # skip citations with fewer content words in context

# ── reader helpers ────────────────────────────────────────────────────────────

_reader_cache: dict = {}

def reader_html(source: str) -> str:
    if source not in _reader_cache:
        p = os.path.join(READ_DIR, f"{source}.html")
        _reader_cache[source] = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    return _reader_cache[source]

_hadith_index: dict = {}

def hadith_index(source: str) -> dict:
    if source in _hadith_index:
        return _hadith_index[source]
    content = reader_html(source)
    idx: dict = {}
    pat = re.compile(r'id="(h\d+)"', re.IGNORECASE)
    positions = [(m.group(1), m.start()) for m in pat.finditer(content)]
    for i, (hid, start) in enumerate(positions):
        end = positions[i+1][1] if i+1 < len(positions) else len(content)
        block = content[start:end]
        text = re.sub(r"<[^>]+>", " ", block)
        text = html_mod.unescape(re.sub(r"\s+", " ", text).strip())
        idx[hid] = text
    _hadith_index[source] = idx
    return idx

_quran_index: dict = None

def quran_index() -> dict:
    global _quran_index
    if _quran_index is not None:
        return _quran_index
    content = reader_html("quran")
    idx = {}
    pat = re.compile(r'id="s(\d+)v(\d+)"', re.IGNORECASE)
    positions = [(int(m.group(1)), int(m.group(2)), m.start()) for m in pat.finditer(content)]
    for i, (surah, verse, start) in enumerate(positions):
        end = positions[i+1][2] if i+1 < len(positions) else len(content)
        block = content[start:end]
        text = re.sub(r"<[^>]+>", " ", block)
        text = html_mod.unescape(re.sub(r"\s+", " ", text).strip())
        idx[(surah, verse)] = text
    _quran_index = idx
    return idx

def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return html_mod.unescape(re.sub(r"\s+", " ", s).strip())

# ── n-gram helpers ────────────────────────────────────────────────────────────

BOILERPLATE = {
    "narrated by", "the messenger of allah", "allah's messenger", "messenger of allah",
    "the prophet said", "it was narrated", "allah be pleased with", "peace be upon him",
    "said the prophet", "the apostle of allah", "i asked the messenger",
    "he said that", "allah the exalted", "the prophet peace", "upon him said",
    "narrated that the", "it is narrated", "the prophet of", "said i heard",
    "i heard the", "told me that",
}

def content_ngrams(text: str, n: int = 5):
    words = text.split()
    for i in range(len(words) - n + 1):
        gram = " ".join(words[i:i+n]).lower()
        if not any(bp in gram for bp in BOILERPLATE):
            yield gram

def context_matches(context: str, target_text: str, n: int = 5) -> bool:
    t_lower = target_text.lower()
    for gram in content_ngrams(context, n):
        if gram in t_lower:
            return True
    return False

STOPS = {"the","a","an","of","in","to","for","and","or","is","are","was",
         "were","that","this","it","as","at","by","from","with","on","be",
         "its","their","also","not","but","had","have","has","which","who",
         "he","she","they","we","i","his","her","our","more","than","when",
         "so","if","about","will","would","could","should","no","such","may"}

def content_word_count(text: str) -> int:
    words = re.findall(r"[a-z']+", text.lower())
    return sum(1 for w in words if w not in STOPS and len(w) > 2)

# ── context extraction ────────────────────────────────────────────────────────

_P_START  = re.compile(r'<p\b',        re.IGNORECASE)
_LI_START = re.compile(r'<li\b',       re.IGNORECASE)
_BQ_START = re.compile(r'<blockquote\b', re.IGNORECASE)
_P_END    = re.compile(r'</p>',        re.IGNORECASE)
_LI_END   = re.compile(r'</li>',       re.IGNORECASE)
_BQ_END   = re.compile(r'</blockquote>', re.IGNORECASE)

def get_block_context(raw: str, cite_start: int, cite_end: int) -> str:
    look_back = max(0, cite_start - 2000)
    pre = raw[look_back:cite_start]
    best_start = look_back
    best_tag_pos = -1
    for pat in (_P_START, _LI_START, _BQ_START):
        for m in pat.finditer(pre):
            if m.start() > best_tag_pos:
                best_tag_pos = m.start()
                best_start = look_back + m.start()
    look_fwd = min(len(raw), cite_end + 3000)
    post = raw[cite_end:look_fwd]
    best_end = look_fwd
    for pat in (_P_END, _LI_END, _BQ_END):
        m = pat.search(post)
        if m:
            candidate = cite_end + m.end()
            if candidate < best_end:
                best_end = candidate
    return strip_html(raw[best_start:best_end])

_BQ_FULL = re.compile(r'<blockquote\b[^>]*>(.*?)</blockquote>', re.DOTALL | re.IGNORECASE)
ENTRY_RE  = re.compile(r'<div\s+class="entry[^"]*"', re.IGNORECASE)

def get_entry_blockquote(raw: str, entry_start: int) -> str:
    next_entry = re.search(r'<div class="entry[^"]*"', raw[entry_start+10:])
    entry_end = entry_start + 10 + (next_entry.start() if next_entry else len(raw))
    block = raw[entry_start:entry_end]
    m = _BQ_FULL.search(block)
    return strip_html(m.group(1)) if m else ""

def get_full_entry_text(raw: str, entry_start: int) -> str:
    next_entry = re.search(r'<div class="entry[^"]*"', raw[entry_start+10:])
    entry_end = entry_start + 10 + (next_entry.start() if next_entry else len(raw))
    return strip_html(raw[entry_start:entry_end])

def find_entry_start(entry_starts, pos):
    best = 0
    for s in entry_starts:
        if s <= pos:
            best = s
    return best

# ── citation regexes ──────────────────────────────────────────────────────────

# Matches both hNNNN (hadith) and sXvY (quran) anchors.
# Group 1: source name, Group 2: anchor id, Group 3: display text

PRIMARY_RE = re.compile(
    r'<span\s+class="ref"[^>]*>.*?<a\s+href="[^"]*read/([^/"]+)\.html#(h\d+|s\d+v\d+)"[^>]*>([^<]*)</a>',
    re.IGNORECASE | re.DOTALL,
)

BODY_RE = re.compile(
    r'<a[^>]+class="cite-link"[^>]+href="[^"]*read/([^/"]+)\.html#(h\d+|s\d+v\d+)"[^>]*>([^<]*)</a>',
    re.IGNORECASE,
)

# For catalog primary-ref: also catch links not inside </span> immediately
# (span may contain multiple links separated by semicolons)
SPAN_LINK_RE = re.compile(
    r'<span\s+class="ref"[^>]*>(.*?)</span>',
    re.IGNORECASE | re.DOTALL,
)
LINK_IN_SPAN_RE = re.compile(
    r'<a\s+href="[^"]*read/([^/"]+)\.html#(h\d+|s\d+v\d+)"[^>]*>([^<]*)</a>',
    re.IGNORECASE,
)

# ── Quran display parser ──────────────────────────────────────────────────────

_QREF_RE = re.compile(r'(\d{1,3}):(\d{1,3})')

def parse_quran_display(display: str):
    """Extract (surah, verse) from display text. Returns (None, None) if unrecognised."""
    m = _QREF_RE.search(display)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

# ── error lists ───────────────────────────────────────────────────────────────

hadith_errors = []
quran_errors  = []
checked_hadith = 0
checked_quran  = 0
skipped_thin   = 0

# ── check functions ───────────────────────────────────────────────────────────

def check_hadith(source, cited_id, context, label, fpath):
    global checked_hadith, skipped_thin
    if content_word_count(context) < MIN_WORDS:
        skipped_thin += 1
        return
    checked_hadith += 1
    idx = hadith_index(source)
    if cited_id not in idx:
        hadith_errors.append({
            "file": fpath, "cited": f"{source}#{cited_id}",
            "issue": "ID not in reader", "context": context[:120],
            "label": label, "correct_id": None,
        })
        return
    cited_text = idx[cited_id]
    if context_matches(context, cited_text):
        return
    num = int(cited_id[1:])
    found_ids = []
    for delta in range(-HADITH_WINDOW, HADITH_WINDOW + 1):
        if delta == 0:
            continue
        candidate = f"h{num + delta}"
        if candidate in idx and context_matches(context, idx[candidate]):
            found_ids.append(candidate)
    if found_ids:
        hadith_errors.append({
            "file": fpath, "cited": f"{source}#{cited_id}",
            "issue": "wrong ID", "context": context[:120],
            "label": label, "correct_id": found_ids[0],
            "all_matches": found_ids,
            "cited_snippet": cited_text[:120],
        })

def check_quran(surah, verse, display, label, fpath):
    global checked_quran
    checked_quran += 1
    qi = quran_index()

    # 1. Does the anchor exist?
    if (surah, verse) not in qi:
        quran_errors.append({
            "file": fpath, "cited": f"s{surah}v{verse}",
            "issue": "anchor not found in quran reader",
            "display": display, "label": label,
        })
        return

    # 2. Href/display cross-check (only when display contains a surah:verse pattern)
    d_surah, d_verse = parse_quran_display(display)
    if d_surah is not None:
        if d_surah != surah or d_verse != verse:
            quran_errors.append({
                "file": fpath, "cited": f"s{surah}v{verse}",
                "issue": (f"href says {surah}:{verse} but display '{display}' says {d_surah}:{d_verse}"),
                "display": display, "label": label,
            })

def scan_file(fpath, is_catalog):
    raw = open(fpath, encoding="utf-8").read()
    entry_starts = [m.start() for m in ENTRY_RE.finditer(raw)] if is_catalog else []

    def get_context_for(cite_start, cite_end, label):
        if is_catalog and label == "primary-ref":
            es = find_entry_start(entry_starts, cite_start)
            ctx = get_entry_blockquote(raw, es)
            if content_word_count(ctx) < MIN_WORDS:
                ctx = get_full_entry_text(raw, es)
            return ctx
        return get_block_context(raw, cite_start, cite_end)

    def dispatch(source, anchor_id, display, label, cite_start, cite_end):
        if source == "quran":
            m = re.match(r's(\d+)v(\d+)$', anchor_id, re.IGNORECASE)
            if m:
                check_quran(int(m.group(1)), int(m.group(2)), display.strip(), label, fpath)
        else:
            if anchor_id.startswith("h"):
                ctx = get_context_for(cite_start, cite_end, label)
                check_hadith(source, anchor_id, ctx, label, fpath)

    # Primary refs (catalog): iterate links inside each <span class="ref">
    if is_catalog:
        for span_m in SPAN_LINK_RE.finditer(raw):
            for lnk_m in LINK_IN_SPAN_RE.finditer(span_m.group(1)):
                dispatch(lnk_m.group(1), lnk_m.group(2), lnk_m.group(3),
                         "primary-ref",
                         span_m.start() + lnk_m.start(),
                         span_m.start() + lnk_m.end())

    # Body cite-links
    for m in BODY_RE.finditer(raw):
        dispatch(m.group(1), m.group(2), m.group(3), "body-cite", m.start(), m.end())

# ── scan all files ────────────────────────────────────────────────────────────

print("Scanning catalog files...")
for fname in sorted(os.listdir(CAT_DIR)):
    if fname.endswith(".html"):
        scan_file(os.path.join(CAT_DIR, fname), is_catalog=True)

print("Scanning dossier files...")
for root, dirs, files in os.walk(ARG_DIR):
    for fname in sorted(files):
        if fname.endswith(".html"):
            scan_file(os.path.join(root, fname), is_catalog=False)

# ── report ────────────────────────────────────────────────────────────────────

print(f"\nChecked {checked_hadith} hadith citations | {checked_quran} Quran citations | {skipped_thin} skipped (thin context)")

print(f"\n{'='*70}")
print(f"HADITH ERRORS: {len(hadith_errors)}")
print(f"{'='*70}")
for e in sorted(hadith_errors, key=lambda x: (x["file"], x["cited"])):
    rel = os.path.relpath(e["file"], SITE)
    all_m = e.get("all_matches", [])
    print(f"  FILE : {rel}")
    print(f"  CITED: {e['cited']}  ({e['label']})  ->  CORRECT: {e.get('correct_id','???')}",
          f"  (also: {all_m[1:6]})" if len(all_m) > 1 else "")
    ctx = e["context"].encode("ascii", "replace").decode("ascii")
    print(f"  CTX  : {ctx[:110]}")
    if "cited_snippet" in e:
        snip = e["cited_snippet"].encode("ascii", "replace").decode("ascii")
        print(f"  AT ID: {snip[:110]}")
    print()

print(f"\n{'='*70}")
print(f"QURAN ERRORS: {len(quran_errors)}")
print(f"{'='*70}")
for e in sorted(quran_errors, key=lambda x: (x["file"], x["cited"])):
    rel = os.path.relpath(e["file"], SITE)
    print(f"  FILE : {rel}")
    print(f"  CITED: {e['cited']}  ({e['label']})  DISPLAY: '{e.get('display','')}'")
    print(f"  ISSUE: {e['issue']}")
    print()
