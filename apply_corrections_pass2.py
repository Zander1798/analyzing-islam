"""
Second pass: apply remaining corrections that were skipped due to generic phrase filter.
Re-searches with a lower threshold but requires higher word-overlap verification (>=4 words).
"""

import os, re, html as html_mod

SITE    = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT     = os.path.join(SITE, "catalog")
FLAGS   = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/zero_overlap_flags.txt"
REPORT2 = r"C:/Users/zande\Documents\AI Workspace\Analyzing Islam\apply_report2.txt"

STOP = set("""the a an of in to is was were are be been being have has had do does did
will would could should may might shall for from with by at on or and but not this
that these those his her its their our your i he she we they it as if so no nor yet
when where who what which while then than after before since though although because
even only also just more most very well such both other another each all any few many
much some into out up down over under about between through during among against along
without within upon whom whose him them us me my your its his her its their our
hadith book narrated said allah messenger prophet peace upon him reported told asked""".split())

SOURCE_NAME = {
    "bukhari": "Bukhari", "muslim": "Muslim", "abu-dawud": "Abu Dawud",
    "tirmidhi": "Tirmidhi", "ibn-majah": "Ibn Majah", "nasai": "Nasa'i",
}

# ── reader cache ─────────────────────────────────────────────────────────────
_reader_cache = {}
_plain_cache = {}

def get_reader(source):
    if source not in _reader_cache:
        p = os.path.join(SITE, "read", f"{source}.html")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                _reader_cache[source] = f.read()
        else:
            _reader_cache[source] = ""
    return _reader_cache[source]

def get_plain(source):
    if source not in _plain_cache:
        c = get_reader(source)
        c2 = re.sub(r'<[^>]*\sid="(h\d+)"[^>]*>', r' «\1» ', c, flags=re.IGNORECASE)
        c2 = re.sub(r'<[^>]+>', ' ', c2)
        c2 = html_mod.unescape(c2)
        c2 = re.sub(r'\s+', ' ', c2)
        _plain_cache[source] = c2
    return _plain_cache[source]

READER_SOURCES = ["bukhari", "muslim", "abu-dawud", "tirmidhi", "ibn-majah", "nasai"]

def find_anchor_for_phrase(plain, phrase):
    idx = plain.lower().find(phrase.lower())
    if idx == -1:
        return None
    chunk = plain[max(0, idx-4000):idx+200]
    markers = list(re.finditer(r'«(h\d+)»', chunk))
    if not markers:
        return None
    return markers[-1].group(1)

def extract_phrases(bq, min_len=15):
    text = re.sub(r'\[.*?\]', '', bq)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[""""]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()
    phrases = []
    for start in range(0, min(len(words)-3, 25), 2):
        for length in [6, 5, 4, 3]:
            if start + length <= len(words):
                phrase = ' '.join(words[start:start+length])
                if len(phrase) >= min_len:
                    phrases.append(phrase)
    return phrases[:20]

def verify_anchor(source, anchor, bq_text, min_overlap=3):
    c = get_reader(source)
    m = re.search(rf'id="{re.escape(anchor)}"', c, re.IGNORECASE)
    if not m:
        return False
    nxt = re.search(r'id="h\d+', c[m.start()+10:])
    end = m.start() + 10 + (nxt.start() if nxt else 2000)
    raw = re.sub(r"<[^>]+>", " ", c[m.start():end])
    anchor_text = html_mod.unescape(re.sub(r"\s+", " ", raw)).lower()
    anchor_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", anchor_text) if w not in STOP)
    bq_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", bq_text.lower()) if w not in STOP)
    return len(bq_words & anchor_words) >= min_overlap

def search_readers(bq, primary_source):
    phrases = extract_phrases(bq, min_len=15)
    sources = [primary_source] + [s for s in READER_SOURCES if s != primary_source]
    for source in sources:
        plain = get_plain(source)
        for phrase in phrases:
            anchor = find_anchor_for_phrase(plain, phrase)
            if anchor and verify_anchor(source, anchor, bq, min_overlap=3):
                return source, anchor, phrase
    return None, None, None

# ── parse flags (only entries that were SKIPPED or still need fixing) ────────
def parse_flags(path):
    entries = []
    current = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("FILE :"):
                if current.get("bq"):
                    entries.append(current)
                current = {"file": line[7:].strip()}
            elif line.startswith("ENTRY:"):
                current["entry"] = line[7:].strip()
            elif line.startswith("CITED:"):
                cited = line[7:].strip()
                if "#" in cited:
                    s, a = cited.split("#", 1)
                    current["source"] = s
                    current["anchor"] = a
            elif line.startswith("BQ   :"):
                current["bq"] = line[7:].strip()
    if current.get("bq"):
        entries.append(current)
    return entries

flags = parse_flags(FLAGS)

# Only process entries that are still wrong (not already fixed by pass 1)
# Load the catalog to check current state
def get_current_anchor(catalog_file, entry_id):
    path = os.path.join(CAT, catalog_file)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        html = f.read()
    m = re.search(
        rf'<div\s+class="entry"[^>]*id="{re.escape(entry_id)}"[^>]*>(.*?)(?=<div\s+class="entry"|\Z)',
        html, re.DOTALL | re.IGNORECASE
    )
    if not m:
        return None
    block = m.group(1)
    span_m = re.search(r'<span\s+class="ref"[^>]*>(.*?)</span>', block, re.IGNORECASE | re.DOTALL)
    if not span_m:
        return None
    links = re.findall(r'href="[^"]*read/([^/"]+)\.html#(h\d+)"', span_m.group(1), re.IGNORECASE)
    return links  # list of (source, anchor) tuples

applied2 = []
skipped2 = []

print(f"Processing {len(flags)} entries for pass 2...")

for i, entry in enumerate(flags):
    fname    = entry.get("file", "")
    entry_id = entry.get("entry", "")
    bq       = entry.get("bq", "")
    old_src  = entry.get("source", "")
    old_anc  = entry.get("anchor", "")
    old_cite = f"{old_src}#{old_anc}"

    if i % 50 == 0:
        print(f"  {i}/{len(flags)}...")

    # Check current state of the catalog
    current_links = get_current_anchor(fname, entry_id)
    if not current_links:
        skipped2.append((entry_id, "entry not found or no ref links"))
        continue

    # Check if old link still exists (not already fixed by pass 1)
    old_still_present = any(f"{s}#{a}" == old_cite for s, a in current_links)
    if not old_still_present:
        # Already fixed by pass 1
        continue

    # Search for correct anchor
    new_src, new_anc, phrase = search_readers(bq, old_src)

    if not new_src:
        skipped2.append((entry_id, "no match found"))
        continue

    new_cite = f"{new_src}#{new_anc}"
    if new_cite == old_cite:
        continue

    # Apply the fix
    cat_path = os.path.join(CAT, fname)
    with open(cat_path, encoding="utf-8") as f:
        html = f.read()

    old_href = f"../read/{old_src}.html#{old_anc}"
    new_href = f"../read/{new_src}.html#{new_anc}"
    new_display = f"{SOURCE_NAME.get(new_src, new_src.title())} #{new_anc[1:]}"

    link_re = re.compile(
        rf'href="{re.escape(old_href)}"[^>]*>(.*?)</a>',
        re.IGNORECASE
    )
    new_html, count = link_re.subn(
        lambda m: f'href="{new_href}">{new_display}</a>',
        html
    )
    if count == 0:
        skipped2.append((entry_id, f"link not found: {old_href}"))
        continue

    with open(cat_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    applied2.append((entry_id, f"{old_cite} -> {new_cite}  phrase={phrase[:40]}"))

print(f"\nPass 2 applied: {len(applied2)}")
print(f"Pass 2 skipped: {len(skipped2)}")

with open(REPORT2, "w", encoding="utf-8") as f:
    f.write(f"PASS 2 REPORT\n{'='*60}\n\n")
    f.write(f"=== APPLIED ({len(applied2)}) ===\n")
    for e, msg in applied2:
        f.write(f"  {e}: {msg}\n")
    f.write(f"\n=== SKIPPED ({len(skipped2)}) ===\n")
    for e, msg in skipped2:
        f.write(f"  {e}: {msg}\n")

print(f"Report written to apply_report2.txt")
