"""
Pass 3: Apply the 'skipped' corrections from pass 1 that had valid precise matches
but were rejected by the generic-phrase filter. Use min_overlap=2 verification.
"""

import os, re, html as html_mod

SITE    = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT     = os.path.join(SITE, "catalog")
CORR    = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/precise_corrections.txt"
REPORT3 = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/apply_report3.txt"

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

def verify_anchor(source, anchor, bq_text, min_overlap=2):
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
    overlap = len(bq_words & anchor_words)
    return overlap >= min_overlap

# Parse ALL corrections from precise_corrections.txt (including skipped ones = all in CHANGES NEEDED)
corrections_map = {}  # entry_id -> {old, new_source, new_anchor, phrase, bq, file}
section = None
current = {}
with open(CORR, encoding="utf-8") as f:
    for line in f:
        line = line.rstrip()
        if "=== CHANGES NEEDED ===" in line:
            section = "changes"
        elif "=== ALREADY CORRECT ===" in line:
            section = "correct"
        elif "=== NO MATCH FOUND ===" in line:
            section = "none"
        if section != "changes":
            continue
        if line.startswith("FILE :"):
            if current.get("entry") and current.get("new"):
                # Store with (entry_id, old) as key since entry might have multiple corrections
                key = (current["entry"], current.get("old", ""))
                corrections_map[key] = current.copy()
            current = {"file": line[7:].strip()}
        elif line.startswith("ENTRY:"):
            current["entry"] = line[7:].strip()
        elif line.startswith("OLD  :"):
            old = line[7:].strip()
            if "#" in old:
                s, a = old.split("#", 1)
                current["old_source"] = s
                current["old_anchor"] = a
            current["old"] = old
        elif line.startswith("NEW  :"):
            new = line[7:].strip()
            if "#" in new:
                s, a = new.split("#", 1)
                current["new_source"] = s
                current["new_anchor"] = a
            current["new"] = new
        elif line.startswith("PHRASE:"):
            current["phrase"] = line[8:].strip()
        elif line.startswith("BQ   :"):
            current["bq"] = line[7:].strip()

if current.get("entry") and current.get("new"):
    key = (current["entry"], current.get("old", ""))
    corrections_map[key] = current.copy()

print(f"Loaded {len(corrections_map)} corrections from precise_corrections.txt")

# Now apply the ones that were previously skipped (generic phrase filter)
# We try all corrections with min_overlap=2
applied3 = []
skipped3 = []
not_found = []

for key, corr in corrections_map.items():
    entry_id = corr.get("entry", "")
    fname    = corr.get("file", "")
    old_src  = corr.get("old_source", "")
    old_anc  = corr.get("old_anchor", "")
    new_src  = corr.get("new_source", "")
    new_anc  = corr.get("new_anchor", "")
    bq       = corr.get("bq", "")
    phrase   = corr.get("phrase", "")

    old_href = f"../read/{old_src}.html#{old_anc}"

    # Check if old link still exists in catalog
    cat_path = os.path.join(CAT, fname)
    if not os.path.exists(cat_path):
        skipped3.append((entry_id, f"catalog not found: {fname}"))
        continue

    with open(cat_path, encoding="utf-8") as f:
        html = f.read()

    if old_href not in html:
        # Already fixed
        continue

    # Verify new anchor
    if not verify_anchor(new_src, new_anc, bq, min_overlap=2):
        not_found.append((entry_id, f"low overlap: {new_src}#{new_anc}"))
        continue

    # Apply
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
        skipped3.append((entry_id, f"link pattern not found"))
        continue

    with open(cat_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    applied3.append((entry_id, f"{old_src}#{old_anc} -> {new_src}#{new_anc}  [{phrase[:35]}]"))

print(f"\nPass 3 applied: {len(applied3)}")
print(f"Pass 3 low-overlap: {len(not_found)}")
print(f"Pass 3 skipped: {len(skipped3)}")

with open(REPORT3, "w", encoding="utf-8") as f:
    f.write(f"PASS 3 REPORT\n{'='*60}\n\n")
    f.write(f"=== APPLIED ({len(applied3)}) ===\n")
    for e, msg in applied3:
        f.write(f"  {e}: {msg}\n")
    f.write(f"\n=== LOW OVERLAP ({len(not_found)}) ===\n")
    for e, msg in not_found:
        f.write(f"  {e}: {msg}\n")
    f.write(f"\n=== SKIPPED ({len(skipped3)}) ===\n")
    for e, msg in skipped3:
        f.write(f"  {e}: {msg}\n")

print(f"Report: apply_report3.txt")
