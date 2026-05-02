"""
Citation verifier v2 — checks ALL 962 citations, not just the 148 that carry
verbatim curly-quoted text.

Strategy: for every cite-link, extract the text of the enclosing block element
(<p>, <li>, or the arg-verse-box <div>).  That block is exactly what the dossier
CLAIMS the cited hadith says.  We then run 5-gram matching against the actual
hadith text at the cited ID.  A mismatch flagged as "definite" only when both:
  a) the cited ID fails to match, AND
  b) a nearby ID (within ±15) does match.

Skip a citation when the block text is too generic (< 10 content words after
filtering boilerplate phrases).
"""

import os, re, html as html_mod

SITE     = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
ARGS_DIR = os.path.join(SITE, "arguments")
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
        text = html_mod.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        idx[hid] = text
    _hadith_index[source] = idx
    return idx

def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return html_mod.unescape(re.sub(r"\s+", " ", s).strip())

# ── n-gram matching ──────────────────────────────────────────────────────────

# Phrases so generic they appear in almost every hadith — exclude them from
# the matching corpus so they don't produce false positives.
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
    """Count words that are not pure stopwords/numbers."""
    stops = {"the","a","an","of","in","to","for","and","or","is","are","was",
             "were","that","this","it","as","at","by","from","with","on","be",
             "its","their","also","not","but","had","have","has","which","who",
             "he","she","they","we","i","his","her","our","more","than","when",
             "so","if","about","will","would","could","should","no","such","may"}
    words = re.findall(r"[a-z']+", text.lower())
    return sum(1 for w in words if w not in stops and len(w) > 2)

# ── block-context extraction ─────────────────────────────────────────────────

# Patterns for finding enclosing block boundaries
_P_START  = re.compile(r'<p\b',  re.IGNORECASE)
_LI_START = re.compile(r'<li\b', re.IGNORECASE)
_DIV_VERSE = re.compile(r'<div\s+class="arg-verse-box"', re.IGNORECASE)

_P_END  = re.compile(r'</p>',  re.IGNORECASE)
_LI_END = re.compile(r'</li>', re.IGNORECASE)
_DIV_END = re.compile(r'</div>', re.IGNORECASE)

def get_block_context(raw: str, cite_start: int, cite_end: int) -> str:
    """
    Return the stripped text of the innermost <p>, <li>, or arg-verse-box
    block that encloses the citation.
    """
    # Scan backwards from cite_start to find the last block-opening tag
    look_back = max(0, cite_start - 2000)
    pre = raw[look_back:cite_start]

    best_start = look_back   # default: use whatever we can
    best_tag_pos = -1

    for pat in (_P_START, _LI_START, _DIV_VERSE):
        for m in pat.finditer(pre):
            if m.start() > best_tag_pos:
                best_tag_pos = m.start()
                best_start = look_back + m.start()

    # Now scan forward from cite_end for the closing tag matching the opener.
    # Use whichever closing tag comes first.
    look_fwd = min(len(raw), cite_end + 3000)
    post = raw[cite_end:look_fwd]

    best_end = look_fwd
    for pat in (_P_END, _LI_END, _DIV_END):
        m = pat.search(post)
        if m:
            candidate = cite_end + m.end()
            if candidate < best_end:
                best_end = candidate

    return strip_html(raw[best_start:best_end])

# ── citation regex ───────────────────────────────────────────────────────────

CITE_RE = re.compile(
    r'<a[^>]+class="cite-link"[^>]+href="[^"]*read/([^/"]+)\.html#(h\d+)"[^>]*>[^<]*</a>',
)

# ── main scan ─────────────────────────────────────────────────────────────────

errors       = []
checked      = 0
skipped_thin = 0

for root, dirs, files in os.walk(ARGS_DIR):
    rel = os.path.relpath(root, ARGS_DIR)
    if rel == ".":
        continue
    dirs[:] = []
    for fname in sorted(files):
        if not fname.endswith(".html"):
            continue
        fpath = os.path.join(root, fname)
        raw   = open(fpath, encoding="utf-8").read()

        for m in CITE_RE.finditer(raw):
            source    = m.group(1)
            cited_id  = m.group(2)

            # Skip Quran citations — no hadith reader to check against
            if source == "quran":
                continue

            context = get_block_context(raw, m.start(), m.end())

            # Skip if the block gives us too little content to be meaningful
            if content_word_count(context) < 10:
                skipped_thin += 1
                continue

            checked += 1
            idx = hadith_index(source)

            if cited_id not in idx:
                errors.append({
                    "file":    fpath,
                    "cited":   f"{source}#{cited_id}",
                    "issue":   "ID not in reader",
                    "context": context[:120],
                    "correct_id": None,
                })
                continue

            cited_text = idx[cited_id]
            if context_matches(context, cited_text):
                continue   # ✓ confirmed

            # Not confirmed at cited ID — search ±15
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
                    "file":    fpath,
                    "cited":   f"{source}#{cited_id}",
                    "issue":   "wrong ID",
                    "context": context[:120],
                    "correct_id": found_ids[0],
                    "all_matches": found_ids,
                    "cited_snippet": cited_text[:120],
                })
            # No alternative found → could be paraphrase; do not report

# ── report ───────────────────────────────────────────────────────────────────

print(f"Checked {checked} citations  |  skipped {skipped_thin} (context too thin)")
print(f"\nDefinite citation errors found: {len(errors)}\n")
for e in sorted(errors, key=lambda x: x["file"]):
    rel_file = os.path.relpath(e["file"], SITE)
    all_m = e.get("all_matches", [])
    print(f"  FILE : {rel_file}")
    print(f"  CITED: {e['cited']}  ->  CORRECT: {e.get('correct_id','???')}",
          f"  (also matches: {all_m[1:]})" if len(all_m) > 1 else "")
    ctx = e['context'].encode('ascii', 'replace').decode('ascii')
    print(f"  CTX  : {ctx[:110]}")
    if "cited_snippet" in e:
        snip = e['cited_snippet'].encode('ascii', 'replace').decode('ascii')
        print(f"  AT ID: {snip[:110]}")
    print()
