"""
For each zero-overlap entry in the flags file, search the reader HTML files
to find the correct anchor ID for the blockquote text.
Outputs a mapping: (file, entry, old_cite) -> new_cite
"""

import os, re, html as html_mod

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
FLAGS = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/zero_overlap_flags.txt"
OUT   = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/anchor_corrections.txt"

STOP = set("""the a an of in to is was were are be been being have has had do does did
will would could should may might shall for from with by at on or and but not this
that these those his her its their our your i he she we they it as if so no nor yet
when where who what which while then than after before since though although because
even only also just more most very well such both other another each all any few many
much some into out up down over under about between through during among against along
without within upon whom whose him them us me my your its his her its their our
hadith book narrated said allah messenger ﷺ peace prophet upon him sallallahu alayhi
wasallam reported told asked replied answered chapter volume""".split())

# ── load all reader HTML files ───────────────────────────────────────────────
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

# build index: source -> list of (anchor_id, start_pos, text_words_set)
_anchor_indexes = {}

def build_index(source):
    if source in _anchor_indexes:
        return _anchor_indexes[source]
    c = get_reader(source)
    positions = [(m.group(1), m.start()) for m in re.finditer(r'id="(h\d+)"', c, re.IGNORECASE)]
    idx = []
    for i, (aid, start) in enumerate(positions):
        end = positions[i+1][1] if i+1 < len(positions) else min(len(c), start + 1500)
        block = re.sub(r"<[^>]+>", " ", c[start:end])
        text = html_mod.unescape(re.sub(r"\s+", " ", block)).lower()
        words = set(w for w in re.findall(r"\b[a-z]{3,}\b", text) if w not in STOP)
        snippet = text[:300]
        idx.append((aid, words, snippet))
    _anchor_indexes[source] = idx
    return idx

READER_SOURCES = ["bukhari", "muslim", "abu-dawud", "tirmidhi", "ibn-majah", "nasai"]

def content_words(text):
    return [w for w in re.findall(r"\b[a-z]{3,}\b", text.lower()) if w not in STOP]

def find_best_anchor(bq_text, primary_source, original_anchor):
    """Search all reader files and return (best_source, best_anchor, score, snippet)"""
    bq_words = content_words(bq_text)
    if len(bq_words) < 3:
        return None

    # Use a sliding window approach: check how many consecutive BQ words appear in each anchor
    bq_set = set(bq_words[:20])  # first 20 content words

    best_score = 0
    best_source = None
    best_anchor = None
    best_snippet = ""

    # Search primary source first, then others
    sources_to_search = [primary_source] + [s for s in READER_SOURCES if s != primary_source]

    for source in sources_to_search:
        idx = build_index(source)
        for (aid, words, snippet) in idx:
            score = len(bq_set & words)
            if score > best_score:
                best_score = score
                best_source = source
                best_anchor = aid
                best_snippet = snippet
            if best_score >= 8 and source == primary_source:
                break  # good enough match in primary source

    if best_score < 3:
        return None
    return (best_source, best_anchor, best_score, best_snippet)


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

    result = find_best_anchor(bq, source, anchor)

    if result:
        new_source, new_anchor, score, snippet = result
        old_cite = f"{source}#{anchor}"
        new_cite = f"{new_source}#{new_anchor}"
        same = old_cite == new_cite
        corrections.append({
            "file": entry["file"],
            "entry": entry["entry"],
            "old": old_cite,
            "new": new_cite,
            "score": score,
            "bq": bq[:120],
            "snippet": snippet[:150],
            "changed": not same,
        })
    else:
        no_match.append(entry)

print(f"\nFound {sum(1 for c in corrections if c['changed'])} corrections needed")
print(f"No match: {len(no_match)}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"ANCHOR CORRECTIONS — {sum(1 for c in corrections if c['changed'])} changes needed\n")
    f.write("="*80 + "\n\n")

    f.write("=== CHANGES NEEDED ===\n\n")
    for c in corrections:
        if c["changed"]:
            f.write(f"FILE : {c['file']}\n")
            f.write(f"ENTRY: {c['entry']}\n")
            f.write(f"OLD  : {c['old']}\n")
            f.write(f"NEW  : {c['new']}  (score={c['score']})\n")
            f.write(f"BQ   : {c['bq']}\n")
            f.write(f"SNIP : {c['snippet']}\n")
            f.write("\n")

    f.write("\n=== NO CHANGE NEEDED (already correct) ===\n\n")
    for c in corrections:
        if not c["changed"]:
            f.write(f"ENTRY: {c['entry']}  {c['old']}  score={c['score']}\n")

    f.write("\n=== NO MATCH FOUND ===\n\n")
    for e in no_match:
        f.write(f"FILE : {e['file']}\n")
        f.write(f"ENTRY: {e['entry']}\n")
        f.write(f"CITED: {e.get('cited','?')}\n")
        f.write(f"BQ   : {e.get('bq','')[:120]}\n\n")

print(f"\nWrote corrections to anchor_corrections.txt")
