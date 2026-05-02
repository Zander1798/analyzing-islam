"""
Apply the precise anchor corrections to catalog HTML files.
For each correction:
  1. Verify the NEW anchor exists in the reader
  2. Verify the NEW anchor's text contains at least 2 content words from BQ
  3. Apply: change OLD href -> NEW href in the entry's span.ref
  4. Update the display link text

Skips corrections with overly generic phrases (< 30 chars and starts with generic words).
"""

import os, re, html as html_mod

SITE    = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT     = os.path.join(SITE, "catalog")
CORR    = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/precise_corrections.txt"
REPORT  = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/apply_report.txt"

STOP = set("""the a an of in to is was were are be been being have has had do does did
will would could should may might shall for from with by at on or and but not this
that these those his her its their our your i he she we they it as if so no nor yet
when where who what which while then than after before since though although because
even only also just more most very well such both other another each all any few many
much some into out up down over under about between through during among against along
without within upon whom whose him them us me my your its his her its their our
hadith book narrated said allah messenger prophet peace upon him reported told asked""".split())

GENERIC_STARTS = [
    "the messenger of allah",
    "he ordered that a",
    "the prophet did not",
    "if there was not",
    "the prophet, and he",
    "to have intercourse with",
    "a man said:",
    "to be saved from",
]

def is_suspect(phrase):
    p = phrase.lower().strip()
    if len(phrase) < 25:
        return True
    for g in GENERIC_STARTS:
        if p.startswith(g):
            return True
    return False

# Source display names
SOURCE_NAME = {
    "bukhari":   "Bukhari",
    "muslim":    "Muslim",
    "abu-dawud": "Abu Dawud",
    "tirmidhi":  "Tirmidhi",
    "ibn-majah": "Ibn Majah",
    "nasai":     "Nasa'i",
}

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

def verify_anchor(source, anchor, bq_text):
    """Check anchor exists and shares content words with BQ."""
    c = get_reader(source)
    m = re.search(rf'id="{re.escape(anchor)}"', c, re.IGNORECASE)
    if not m:
        return False, "anchor not found"
    # Get text after anchor (up to 2000 chars)
    nxt = re.search(r'id="h\d+', c[m.start()+10:])
    end = m.start() + 10 + (nxt.start() if nxt else 2000)
    raw = re.sub(r"<[^>]+>", " ", c[m.start():end])
    anchor_text = html_mod.unescape(re.sub(r"\s+", " ", raw)).lower()
    anchor_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", anchor_text) if w not in STOP)
    bq_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", bq_text.lower()) if w not in STOP)
    overlap = len(bq_words & anchor_words)
    return overlap >= 2, f"overlap={overlap}"

# ── parse corrections file ────────────────────────────────────────────────────
corrections = []
section = None
with open(CORR, encoding="utf-8") as f:
    current = {}
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
            if current.get("entry"):
                corrections.append(current)
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
    if current.get("entry"):
        corrections.append(current)

print(f"Loaded {len(corrections)} corrections to apply")

# ── apply corrections ─────────────────────────────────────────────────────────
applied = []
skipped = []
failed = []

for corr in corrections:
    fname = corr.get("file", "")
    entry_id = corr.get("entry", "")
    old_src = corr.get("old_source", "")
    old_anc = corr.get("old_anchor", "")
    new_src = corr.get("new_source", "")
    new_anc = corr.get("new_anchor", "")
    phrase  = corr.get("phrase", "")
    bq      = corr.get("bq", "")

    if not all([fname, entry_id, old_src, old_anc, new_src, new_anc]):
        failed.append((entry_id, "missing fields"))
        continue

    # Skip generic phrases
    if is_suspect(phrase):
        skipped.append((entry_id, f"generic phrase: '{phrase}'"))
        continue

    # Verify new anchor
    ok, msg = verify_anchor(new_src, new_anc, bq)
    if not ok:
        skipped.append((entry_id, f"verification failed: {msg}"))
        continue

    # Load catalog file
    cat_path = os.path.join(CAT, fname)
    if not os.path.exists(cat_path):
        failed.append((entry_id, f"catalog file not found: {fname}"))
        continue

    with open(cat_path, encoding="utf-8") as f:
        html = f.read()

    # Find the entry
    entry_m = re.search(
        rf'<div\s+class="entry"[^>]*id="{re.escape(entry_id)}"[^>]*>(.*?)(?=<div\s+class="entry"|\Z)',
        html, re.DOTALL | re.IGNORECASE
    )
    if not entry_m:
        failed.append((entry_id, "entry div not found in HTML"))
        continue

    # Build the old href pattern (relative path from catalog)
    old_href = f"../read/{old_src}.html#{old_anc}"
    new_href = f"../read/{new_src}.html#{new_anc}"
    new_display = f"{SOURCE_NAME.get(new_src, new_src.title())} #{new_anc[1:]}"  # strip leading 'h'

    # Find the span.ref within this entry and replace the specific link
    entry_start = entry_m.start()
    entry_end   = entry_m.end()
    entry_html  = html[entry_start:entry_end]

    # Replace the old href with new href and update display text
    # Pattern: href="..../old_src.html#old_anc">...text...</a>
    old_href_escaped = re.escape(old_href)
    link_re = re.compile(
        rf'href="{old_href_escaped}"[^>]*>(.*?)</a>',
        re.IGNORECASE
    )

    def repl(m):
        return f'href="{new_href}">{new_display}</a>'

    new_entry_html, count = link_re.subn(repl, entry_html)

    if count == 0:
        failed.append((entry_id, f"link not found: {old_href}"))
        continue

    new_html = html[:entry_start] + new_entry_html + html[entry_end:]

    with open(cat_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    applied.append((entry_id, f"{corr['old']} -> {corr['new']}"))
    # Reload for next correction (since file changed)
    html = new_html


print(f"\nApplied: {len(applied)}")
print(f"Skipped (generic/unverified): {len(skipped)}")
print(f"Failed: {len(failed)}")

with open(REPORT, "w", encoding="utf-8") as f:
    f.write(f"APPLY REPORT\n{'='*60}\n\n")
    f.write(f"=== APPLIED ({len(applied)}) ===\n")
    for e, msg in applied:
        f.write(f"  {e}: {msg}\n")
    f.write(f"\n=== SKIPPED ({len(skipped)}) ===\n")
    for e, msg in skipped:
        f.write(f"  {e}: {msg}\n")
    f.write(f"\n=== FAILED ({len(failed)}) ===\n")
    for e, msg in failed:
        f.write(f"  {e}: {msg}\n")

print(f"\nReport written to apply_report.txt")
