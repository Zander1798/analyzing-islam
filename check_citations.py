"""
Citation verifier for Analyzing Islam dossier files.

For each cite-link in every dossier (arguments/**/*.html) that points to a
reader hadith (#hNNNN), this script:
  1. Extracts the verbatim quoted text attributed to that citation in the dossier.
  2. Looks up the actual hadith text in the reader file at the cited ID.
  3. Checks whether any ~6-word run from the dossier quote appears in the
     reader text at that ID.
  4. If no match, searches IDs in the range [N-5 .. N+5] for the quote.
  5. Reports definite mismatches (cited ID has different content; correct ID found nearby).

Only citations accompanied by a verbatim quote (enclosed in " ") are checked.
Citations that are just cross-references with no accompanying quote are skipped.
"""

import os, re, sys, html

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
ARGS_DIR = os.path.join(SITE, "arguments")
READ_DIR = os.path.join(SITE, "read")

# ── helpers ──────────────────────────────────────────────────────────────────

_reader_cache: dict[str, str] = {}

def reader_html(source: str) -> str:
    if source not in _reader_cache:
        p = os.path.join(READ_DIR, f"{source}.html")
        _reader_cache[source] = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    return _reader_cache[source]

# Build per-source index: hadith_id -> raw HTML block text
_hadith_index: dict[str, dict[str, str]] = {}

def hadith_index(source: str) -> dict[str, str]:
    """Parse reader HTML once and index all hadiths by ID."""
    if source in _hadith_index:
        return _hadith_index[source]

    content = reader_html(source)
    idx: dict[str, str] = {}
    # Each hadith block starts with id="hNNN"; grab everything up to next id="h
    pattern = re.compile(r'id="(h\d+)"', re.IGNORECASE)
    positions = [(m.group(1), m.start()) for m in pattern.finditer(content)]
    for i, (hid, start) in enumerate(positions):
        end = positions[i + 1][1] if i + 1 < len(positions) else len(content)
        block = content[start:end]
        # Strip HTML tags, decode entities
        text = re.sub(r"<[^>]+>", " ", block)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        idx[hid] = text
    _hadith_index[source] = idx
    return idx

def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(re.sub(r"\s+", " ", s).strip())

def ngrams(text: str, n: int = 6):
    """Yield consecutive n-word runs from text."""
    words = text.split()
    for i in range(len(words) - n + 1):
        yield " ".join(words[i:i+n]).lower()

def quote_in_text(quote: str, text: str, n: int = 6) -> bool:
    """True if any n-gram of the quote appears in text (case-insensitive)."""
    tl = text.lower()
    for gram in ngrams(quote, n):
        if gram in tl:
            return True
    return False

# ── main scan ─────────────────────────────────────────────────────────────────

# Pattern to find: cite-link anchor → dash → optional narration intro → quoted text
# We capture: (source, hadith_id, everything after the anchor on that logical "segment")
CITE_RE = re.compile(
    r'<a[^>]+class="cite-link"[^>]+href="[^"]*read/([^/"]+)\.html#(h\d+)"[^>]*>'
    r'[^<]*</a>'               # link text
    r'([^<\n]{0,20}—[^<\n]*)'  # optional "  — intro text" (same line)
    r'(?:[^<]*(?:<[^>]+>[^<]*)*)?' ,  # absorb any inline HTML
    re.DOTALL
)

# Simpler: just find all cite-links then grab the following raw HTML chunk
CITE_SIMPLE = re.compile(
    r'<a[^>]+class="cite-link"[^>]+href="[^"]*read/([^/"]+)\.html#(h\d+)"[^>]*>(?P<link_text>[^<]*)</a>',
)

errors = []   # list of dicts
checked = 0
skipped_no_quote = 0

for root, dirs, files in os.walk(ARGS_DIR):
    # Only process leaf dossier files (not the source-level index pages)
    rel = os.path.relpath(root, ARGS_DIR)
    if rel == ".":
        continue   # skip top-level arguments/ files
    dirs[:] = []   # don't recurse deeper
    for fname in sorted(files):
        if not fname.endswith(".html"):
            continue
        fpath = os.path.join(root, fname)
        raw = open(fpath, encoding="utf-8").read()

        for m in CITE_SIMPLE.finditer(raw):
            source    = m.group(1)    # e.g. "abu-dawud"
            cited_id  = m.group(2)    # e.g. "h2155"
            end_pos   = m.end()

            # Grab up to 800 chars after the anchor to find the quoted text
            context = raw[end_pos : end_pos + 800]
            context_text = strip_html(context)

            # Find first " … " block (verbatim quote)
            qm = re.search(r'["“](.{20,}?)["”]', context_text)
            if not qm:
                skipped_no_quote += 1
                continue

            quote = qm.group(1).strip()
            checked += 1

            idx = hadith_index(source)
            if cited_id not in idx:
                # Cited ID doesn't exist in reader at all
                errors.append({
                    "file": fpath,
                    "cited": f"{source}#{cited_id}",
                    "issue": "ID not found in reader",
                    "quote": quote[:80],
                    "correct_id": None,
                })
                continue

            cited_text = idx[cited_id]
            if quote_in_text(quote, cited_text):
                continue   # ✓ match confirmed

            # No match at cited ID – search ±5
            num = int(cited_id[1:])
            found_ids = []
            for delta in range(-5, 6):
                candidate = f"h{num + delta}"
                if candidate != cited_id and candidate in idx:
                    if quote_in_text(quote, idx[candidate]):
                        found_ids.append(candidate)

            if found_ids:
                errors.append({
                    "file": fpath,
                    "cited": f"{source}#{cited_id}",
                    "issue": "wrong ID",
                    "quote": quote[:80],
                    "correct_id": found_ids[0],
                    "all_matches": found_ids,
                    "cited_text_snippet": cited_text[:120],
                })
            # else: quote not found nearby either – might be paraphrase, skip

print(f"Checked {checked} cited quotes, skipped {skipped_no_quote} citations without quotes.")
print(f"\nFound {len(errors)} definite citation errors:\n")
for e in errors:
    rel_file = os.path.relpath(e["file"], SITE)
    print(f"  FILE : {rel_file}")
    print(f"  CITED: {e['cited']}  ->  CORRECT: {e.get('correct_id', '???')}")
    print(f"  QUOTE: {e['quote']}")
    if "cited_text_snippet" in e:
        snippet = e['cited_text_snippet'].encode('ascii', 'replace').decode('ascii')
        print(f"  AT CITED ID: {snippet}")
    print()
