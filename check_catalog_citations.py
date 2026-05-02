"""
Citation verifier for catalog entry pages (site/catalog/*.html).

Two citation types:
  1. Primary: <span class="ref"><a href="../read/source.html#hNNNN">...</a></span>
     Context: the <blockquote> inside the same <div class="entry">
  2. Body:    <a class="cite-link" href="../read/source.html#hNNNN">...</a>
     Context: enclosing <p> or <li> block

Reports definite mismatches only: cited ID fails 5-gram match AND
a nearby ID (±15) does match.
"""

import os, re, html as html_mod

SITE     = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT_DIR  = os.path.join(SITE, "catalog")
READ_DIR = os.path.join(SITE, "read")

# ── reader helpers ───────────────────────────────────────────────────────────

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

def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return html_mod.unescape(re.sub(r"\s+", " ", s).strip())

# ── n-gram matching ──────────────────────────────────────────────────────────

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

def context_matches(context: str, hadith_text: str, n: int = 5) -> bool:
    ht_lower = hadith_text.lower()
    for gram in content_ngrams(context, n):
        if gram in ht_lower:
            return True
    return False

def content_word_count(text: str) -> int:
    stops = {"the","a","an","of","in","to","for","and","or","is","are","was",
             "were","that","this","it","as","at","by","from","with","on","be",
             "its","their","also","not","but","had","have","has","which","who",
             "he","she","they","we","i","his","her","our","more","than","when",
             "so","if","about","will","would","could","should","no","such","may"}
    words = re.findall(r"[a-z']+", text.lower())
    return sum(1 for w in words if w not in stops and len(w) > 2)

# ── block context for body cite-links ────────────────────────────────────────

_P_START   = re.compile(r'<p\b',  re.IGNORECASE)
_LI_START  = re.compile(r'<li\b', re.IGNORECASE)
_BQ_START  = re.compile(r'<blockquote\b', re.IGNORECASE)
_P_END     = re.compile(r'</p>',  re.IGNORECASE)
_LI_END    = re.compile(r'</li>', re.IGNORECASE)
_BQ_END    = re.compile(r'</blockquote>', re.IGNORECASE)

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

# ── catalog-specific: extract blockquote for a primary ref ───────────────────

_BQ_FULL = re.compile(r'<blockquote\b[^>]*>(.*?)</blockquote>', re.DOTALL | re.IGNORECASE)

def get_entry_blockquote(raw: str, entry_start: int) -> str:
    """Return first blockquote text inside the entry starting at entry_start."""
    # Find next entry boundary
    next_entry = re.search(r'<div class="entry[^"]*"', raw[entry_start+10:])
    entry_end = entry_start + 10 + (next_entry.start() if next_entry else len(raw))
    block = raw[entry_start:entry_end]
    m = _BQ_FULL.search(block)
    if m:
        return strip_html(m.group(1))
    return ""

# ── citation regexes ─────────────────────────────────────────────────────────

# Primary ref link (inside <span class="ref">)
PRIMARY_RE = re.compile(
    r'<span\s+class="ref">\s*<a\s+href="[^"]*read/([^/"]+)\.html#(h\d+)"[^>]*>[^<]*</a>\s*</span>',
    re.IGNORECASE,
)

# Body cite-link
BODY_RE = re.compile(
    r'<a[^>]+class="cite-link"[^>]+href="[^"]*read/([^/"]+)\.html#(h\d+)"[^>]*>[^<]*</a>',
    re.IGNORECASE,
)

# Entry div start
ENTRY_RE = re.compile(r'<div\s+class="entry[^"]*"', re.IGNORECASE)

# ── main scan ─────────────────────────────────────────────────────────────────

errors        = []
checked       = 0
skipped_thin  = 0

for fname in sorted(os.listdir(CAT_DIR)):
    if not fname.endswith(".html"):
        continue
    fpath = os.path.join(CAT_DIR, fname)
    raw   = open(fpath, encoding="utf-8").read()

    # Build entry-start index for primary-ref context lookup
    entry_starts = [m.start() for m in ENTRY_RE.finditer(raw)]

    def find_entry_start(pos):
        """Return the entry_start that most recently precedes pos."""
        best = 0
        for s in entry_starts:
            if s <= pos:
                best = s
        return best

    def check_citation(source, cited_id, context, cite_label):
        global checked, skipped_thin
        if source == "quran":
            return
        if content_word_count(context) < 8:
            skipped_thin += 1
            return
        checked += 1
        idx = hadith_index(source)
        if cited_id not in idx:
            errors.append({
                "file":    fpath,
                "cited":   f"{source}#{cited_id}",
                "issue":   "ID not in reader",
                "context": context[:120],
                "label":   cite_label,
                "correct_id": None,
            })
            return
        cited_text = idx[cited_id]
        if context_matches(context, cited_text):
            return
        num = int(cited_id[1:])
        found_ids = []
        for delta in range(-15, 16):
            if delta == 0:
                continue
            candidate = f"h{num + delta}"
            if candidate in idx and context_matches(context, idx[candidate]):
                found_ids.append(candidate)
        if found_ids:
            errors.append({
                "file":       fpath,
                "cited":      f"{source}#{cited_id}",
                "issue":      "wrong ID",
                "context":    context[:120],
                "label":      cite_label,
                "correct_id": found_ids[0],
                "all_matches": found_ids,
                "cited_snippet": cited_text[:120],
            })

    # Check primary refs
    for m in PRIMARY_RE.finditer(raw):
        source   = m.group(1)
        cited_id = m.group(2)
        entry_s  = find_entry_start(m.start())
        context  = get_entry_blockquote(raw, entry_s)
        check_citation(source, cited_id, context, "primary-ref")

    # Check body cite-links
    for m in BODY_RE.finditer(raw):
        source   = m.group(1)
        cited_id = m.group(2)
        context  = get_block_context(raw, m.start(), m.end())
        check_citation(source, cited_id, context, "body-cite")

# ── report ───────────────────────────────────────────────────────────────────

print(f"Checked {checked} catalog citations  |  skipped {skipped_thin} (thin context)")
print(f"\nDefinite citation errors found: {len(errors)}\n")
for e in sorted(errors, key=lambda x: x["file"]):
    rel_file = os.path.relpath(e["file"], SITE)
    all_m = e.get("all_matches", [])
    print(f"  FILE : {rel_file}")
    print(f"  CITED: {e['cited']}  ({e['label']})  ->  CORRECT: {e.get('correct_id','???')}",
          f"  (also: {all_m[1:]})" if len(all_m) > 1 else "")
    ctx = e["context"].encode("ascii", "replace").decode("ascii")
    print(f"  CTX  : {ctx[:110]}")
    if "cited_snippet" in e:
        snip = e["cited_snippet"].encode("ascii", "replace").decode("ascii")
        print(f"  AT ID: {snip[:110]}")
    print()
