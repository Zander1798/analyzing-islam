"""
More precise anchor finder: takes a 5-8 word substring from the BQ and searches
for it literally (case-insensitive) in the reader HTML files.
Only reports a match when the actual text is found near an anchor.
"""

import os, re, html as html_mod

SITE  = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
FLAGS = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/zero_overlap_flags.txt"
OUT   = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/precise_corrections.txt"

# ── reader cache ─────────────────────────────────────────────────────────────
_reader_cache = {}

def get_reader(source):
    if source not in _reader_cache:
        p = os.path.join(SITE, "read", f"{source}.html")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                _reader_cache[source] = f.read()
        else:
            _reader_cache[source] = ""
    return _reader_cache[source]

# Pre-processed plain-text versions of each reader (HTML stripped)
_plain_cache = {}

def get_plain(source):
    if source not in _plain_cache:
        c = get_reader(source)
        # Strip HTML but preserve anchor markers as special tokens
        # Replace <... id="hNNN" ...> with «hNNN» so we can find anchor boundaries
        c2 = re.sub(r'<[^>]*\sid="(h\d+)"[^>]*>', r' «\1» ', c, flags=re.IGNORECASE)
        # Strip remaining tags
        c2 = re.sub(r'<[^>]+>', ' ', c2)
        c2 = html_mod.unescape(c2)
        c2 = re.sub(r'\s+', ' ', c2)
        _plain_cache[source] = c2
    return _plain_cache[source]

READER_SOURCES = ["bukhari", "muslim", "abu-dawud", "tirmidhi", "ibn-majah", "nasai"]

def find_anchor_for_text(plain, search_phrase):
    """Return anchor ID if search_phrase found near a «hNNN» marker."""
    idx = plain.lower().find(search_phrase.lower())
    if idx == -1:
        return None
    # Look backwards for the nearest anchor marker
    chunk = plain[max(0, idx-3000):idx+200]
    markers = list(re.finditer(r'«(h\d+)»', chunk))
    if not markers:
        return None
    # Return the last marker before the found text
    return markers[-1].group(1)

def extract_search_phrases(bq_text, n=4):
    """Extract multiple 4-7 word candidate phrases from the BQ text."""
    # Clean up markup artifacts
    text = re.sub(r'\[.*?\]', '', bq_text)  # remove editorial brackets
    text = re.sub(r'\(.*?\)', '', text)       # remove parentheticals
    text = re.sub(r'[""""]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    words = text.split()
    phrases = []
    # Try windows of 5-7 words at different positions
    for start in range(0, min(len(words)-4, 30), 3):
        for length in [7, 6, 5, 4]:
            if start + length <= len(words):
                phrase = ' '.join(words[start:start+length])
                if len(phrase) > 15:
                    phrases.append(phrase)
    return phrases[:15]  # limit candidates

def search_all_readers(bq_text, primary_source):
    """Search all reader files, return (source, anchor) or None."""
    phrases = extract_search_phrases(bq_text)

    # Search primary source first
    sources = [primary_source] + [s for s in READER_SOURCES if s != primary_source]

    for source in sources:
        plain = get_plain(source)
        for phrase in phrases:
            anchor = find_anchor_for_text(plain, phrase)
            if anchor:
                return (source, anchor, phrase)
    return None


# ── parse flags file ──────────────────────────────────────────────────────────
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
                    src, anc = cited.split("#", 1)
                    current["source"] = src
                    current["anchor"] = anc
                current["cited"] = cited
            elif line.startswith("BQ   :"):
                current["bq"] = line[7:].strip()
            elif line.startswith("AT   :"):
                current["at"] = line[7:].strip()
    if current.get("bq"):
        entries.append(current)
    return entries


flags = parse_flags(FLAGS)
print(f"Loaded {len(flags)} flagged entries")

corrections = []
no_match = []

for i, entry in enumerate(flags):
    if i % 50 == 0:
        print(f"  Processing {i}/{len(flags)}...")

    bq = entry.get("bq", "")
    source = entry.get("source", "bukhari")
    anchor = entry.get("anchor", "")
    old_cite = f"{source}#{anchor}"

    result = search_all_readers(bq, source)

    if result:
        new_source, new_anchor, phrase = result
        new_cite = f"{new_source}#{new_anchor}"
        same = old_cite == new_cite
        corrections.append({
            "file": entry["file"],
            "entry": entry["entry"],
            "old": old_cite,
            "new": new_cite,
            "phrase": phrase,
            "bq": bq[:120],
            "changed": not same,
        })
    else:
        no_match.append({
            "file": entry["file"],
            "entry": entry["entry"],
            "old": old_cite,
            "bq": bq[:120],
        })

changed_count = sum(1 for c in corrections if c["changed"])
print(f"\nFound {changed_count} corrections needed")
print(f"Already correct: {sum(1 for c in corrections if not c['changed'])}")
print(f"No match: {len(no_match)}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"PRECISE ANCHOR CORRECTIONS — {changed_count} changes\n")
    f.write("="*80 + "\n\n")

    f.write("=== CHANGES NEEDED ===\n\n")
    for c in corrections:
        if c["changed"]:
            f.write(f"FILE : {c['file']}\n")
            f.write(f"ENTRY: {c['entry']}\n")
            f.write(f"OLD  : {c['old']}\n")
            f.write(f"NEW  : {c['new']}\n")
            f.write(f"PHRASE: {c['phrase']}\n")
            f.write(f"BQ   : {c['bq']}\n")
            f.write("\n")

    f.write("\n=== ALREADY CORRECT ===\n\n")
    for c in corrections:
        if not c["changed"]:
            f.write(f"ENTRY: {c['entry']}  {c['old']}  phrase={c['phrase']}\n")

    f.write("\n=== NO MATCH FOUND ===\n\n")
    for e in no_match:
        f.write(f"FILE : {e['file']}\n")
        f.write(f"ENTRY: {e['entry']}\n")
        f.write(f"OLD  : {e['old']}\n")
        f.write(f"BQ   : {e['bq']}\n\n")

print(f"\nWrote corrections to precise_corrections.txt")
