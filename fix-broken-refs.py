#!/usr/bin/env python3
"""For each <a href="../read/{src}.html#ANCHOR"> in site/catalog/*.html whose
ANCHOR does not exist in the corresponding reader page, try to infer the
correct anchor by searching the reader for a distinctive phrase from the
entry's blockquote(s). Print suggestions; auto-apply only when exactly one
reader hadith matches.

Flags
  --apply    actually rewrite the catalog files
  --verbose  show all matches and misses with context
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"
CATALOG_DIR = SITE / "catalog"
READ_DIR = SITE / "read"

apply_changes = "--apply" in sys.argv
verbose = "--verbose" in sys.argv

READERS = {
    "bukhari": (READ_DIR / "bukhari.html").read_text(encoding="utf-8"),
    "muslim":  (READ_DIR / "muslim.html").read_text(encoding="utf-8"),
    "quran":   (READ_DIR / "quran.html").read_text(encoding="utf-8"),
}
READER_IDS = {k: set(re.findall(r'id="([^"]+)"', v)) for k, v in READERS.items()}

# Per-reader: list of (id, body_text) so we can search.
def parse_reader(html: str, src: str) -> list[tuple[str, str]]:
    # Each hadith is an <article class="hadith" id="..."> ... </article>
    if src == "quran":
        # Quran verses: <li id="sNvM">
        items = re.findall(r'<li id="(s\d+v\d+)"[^>]*>(.*?)</li>', html, re.DOTALL)
    else:
        items = re.findall(r'<article class="hadith" id="([^"]+)">(.*?)</article>', html, re.DOTALL)
    cleaned = []
    for aid, body in items:
        # Strip HTML tags and entities for searching.
        txt = re.sub(r"<[^>]+>", " ", body)
        txt = re.sub(r"&#x27;", "'", txt)
        txt = re.sub(r"&quot;", '"', txt)
        txt = re.sub(r"&amp;", "&", txt)
        txt = re.sub(r"&#\d+;", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        cleaned.append((aid, txt))
    return cleaned

READER_ITEMS = {src: parse_reader(html, src) for src, html in READERS.items()}
print(f"Parsed: bukhari={len(READER_ITEMS['bukhari'])}  muslim={len(READER_ITEMS['muslim'])}  quran={len(READER_ITEMS['quran'])}")

ENTRY_RE = re.compile(r'<div class="entry"[^>]*>.*?</div>\s*(?=<div class="entry"|<div class="empty"|</div>\s*</main>|$)', re.DOTALL)
LINK_RE = re.compile(r'<a href="\.\./read/(quran|bukhari|muslim)\.html#([^"]+)">([^<]+)</a>')
BLOCKQUOTE_RE = re.compile(r"<blockquote>(.*?)</blockquote>", re.DOTALL)

def clean_text(s: str) -> str:
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&#x27;", "'", s)
    s = re.sub(r"&quot;", '"', s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def distinctive_phrases(blockquote_text: str) -> list[str]:
    """Return candidate search phrases of varying lengths and positions.
    Ordered longest-first so distinctive hits come first."""
    # All double-quote spans, ASCII and typographic.
    raw = []
    for m in re.finditer(r'["""]([^"""]{15,})["""]', blockquote_text):
        raw.append(m.group(1))
    if not raw:
        raw = [blockquote_text]

    phrases = []
    for r in raw:
        r = re.sub(r"\s+", " ", r).strip()
        # Strip trailing parenthetical refs.
        r = re.sub(r"\s*\(\d+[a-z]?\)\s*$", "", r).strip()
        # Full (may be long).
        phrases.append(r)
        # Windows of various sizes across the string.
        for size in (60, 40, 25):
            if len(r) > size:
                step = max(1, size // 2)
                for i in range(0, len(r) - size + 1, step):
                    phrases.append(r[i:i + size])
            else:
                phrases.append(r)

    # Split on punctuation as additional candidates (mid-sentence clauses).
    for r in raw:
        for part in re.split(r"[.;:?!]|—", r):
            part = re.sub(r"\s+", " ", part).strip()
            if 20 <= len(part) <= 80:
                phrases.append(part)

    # De-dup, order longest first.
    seen = set(); out = []
    for p in sorted(set(phrases), key=len, reverse=True):
        key = p.lower()
        if key in seen: continue
        seen.add(key); out.append(p)
    return out[:20]

def find_matches(src: str, phrases: list[str]) -> list[str]:
    """Return list of reader-item IDs whose body contains ANY of the phrases."""
    if not phrases:
        return []
    hits = set()
    for aid, body in READER_ITEMS[src]:
        for p in phrases:
            if p and p.lower() in body.lower():
                hits.add(aid)
                break
    return sorted(hits)

def find_entry_for_link(catalog_text: str, link_match_start: int) -> tuple[int, int, str]:
    """Given the start offset of a link in the catalog, find the enclosing
    <div class="entry">...</div> block. Returns (start, end, block_text)."""
    # Walk backwards to find the nearest <div class="entry"
    before = catalog_text.rfind('<div class="entry"', 0, link_match_start)
    if before == -1:
        return (-1, -1, "")
    # Walk forward counting div depth to find the matching </div>
    depth = 1
    j = catalog_text.find(">", before) + 1
    while depth > 0 and j < len(catalog_text):
        next_open = catalog_text.find("<div", j)
        next_close = catalog_text.find("</div>", j)
        if next_close == -1:
            return (-1, -1, "")
        if next_open != -1 and next_open < next_close:
            depth += 1
            j = next_open + 4
        else:
            depth -= 1
            j = next_close + len("</div>")
    return (before, j, catalog_text[before:j])


# Scan all catalog files.
fixes = []  # list of (fname, old_href, new_href, link_label, entry_title)
ambiguous = []
not_found = []

for path in sorted(CATALOG_DIR.glob("*.html")):
    text = path.read_text(encoding="utf-8")
    # Walk each link; check if anchor exists. If not, look up correct anchor.
    offset = 0
    replacements = []  # (start, end, replacement_text)
    for m in LINK_RE.finditer(text):
        src, anchor, label = m.group(1), m.group(2), m.group(3)
        if anchor in READER_IDS[src]:
            continue
        # Broken — locate containing entry and pull blockquote phrases.
        ent_start, ent_end, block = find_entry_for_link(text, m.start())
        if not block:
            not_found.append((path.name, label, anchor, "no entry block"))
            continue
        title_m = re.search(r'<span class="entry-title">([^<]+)</span>', block)
        entry_title = clean_text(title_m.group(1)) if title_m else "(no title)"
        bqs = BLOCKQUOTE_RE.findall(block)
        # Drop blockquotes that are "parallel" or cross-collection quotes.
        primary_bqs = []
        for bq in bqs:
            txt = clean_text(bq)
            lower = txt.lower()
            if lower.startswith(("parallel:", "parallel ", "muslim:", "muslim ",
                                 "the companion story", "companion story")):
                continue
            primary_bqs.append(txt)
        # Also: if there's at least one primary, skip all others.
        if primary_bqs:
            use_bqs = primary_bqs
        else:
            use_bqs = [clean_text(bq) for bq in bqs]
        all_phrases = []
        for bq in use_bqs:
            all_phrases.extend(distinctive_phrases(bq))
        # de-dup preserving order
        seen = set(); deduped = []
        for p in all_phrases:
            if p not in seen:
                seen.add(p); deduped.append(p)
        hits = find_matches(src, deduped)
        # Heuristic narrowing: prefer hits whose id contains the book cited
        # in the label (e.g., "Book 26" -> hit contains "b26n"). For Bukhari,
        # also prefer hits matching "b{book}".
        def narrow_by_label(cands: list[str]) -> list[str]:
            book_m = re.search(r'Book\s+0*(\d+)', label)
            if not book_m:
                return cands
            want = f'b{book_m.group(1)}n'
            sub = [h for h in cands if want in h]
            return sub if sub else cands

        # Also try narrowing by volume for Bukhari.
        def narrow_by_volume(cands: list[str]) -> list[str]:
            vol_m = re.search(r'Vol\s+(\d+)', label)
            if not vol_m or src != "bukhari":
                return cands
            want = f'v{vol_m.group(1)}b'
            sub = [h for h in cands if h.startswith(want)]
            return sub if sub else cands

        if len(hits) > 1:
            hits = narrow_by_volume(narrow_by_label(hits))

        if len(hits) == 1:
            new_anchor = hits[0]
            new_link = f'<a href="../read/{src}.html#{new_anchor}">{label}</a>'
            replacements.append((m.start(), m.end(), new_link))
            fixes.append((path.name, anchor, new_anchor, label, entry_title, src))
        elif len(hits) > 1:
            ambiguous.append((path.name, label, anchor, entry_title, hits, deduped[:2]))
        else:
            not_found.append((path.name, label, anchor, entry_title))

    # Apply replacements in reverse order so offsets stay valid.
    if replacements and apply_changes:
        new_text = text
        for start, end, repl in sorted(replacements, reverse=True):
            new_text = new_text[:start] + repl + new_text[end:]
        path.write_text(new_text, encoding="utf-8")

print()
print(f"=== Auto-fixable ({len(fixes)}) ===")
for fname, old, new, label, title, src in fixes:
    print(f"  {fname}: \"{label}\"  [{src}]  #{old}  ->  #{new}    ({title})")

print()
print(f"=== Ambiguous — multiple matches ({len(ambiguous)}) ===")
for fname, label, anchor, title, hits, phrases in ambiguous:
    print(f"  {fname}: \"{label}\" -> #{anchor}  ({title})")
    print(f"    candidates: {', '.join(hits[:6])}{' ...' if len(hits) > 6 else ''}")
    if verbose:
        for p in phrases:
            print(f"    phrase: \"{p[:70]}{'...' if len(p) > 70 else ''}\"")

print()
print(f"=== Not found ({len(not_found)}) ===")
for fname, label, anchor, title in not_found:
    print(f"  {fname}: \"{label}\" -> #{anchor}  ({title})")

print()
if apply_changes:
    print(f"APPLIED {len(fixes)} fixes.  Run: python build-category-pages.py  to propagate.")
else:
    print("Dry run.  Re-run with --apply to write changes.")
