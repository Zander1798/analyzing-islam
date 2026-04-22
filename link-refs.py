#!/usr/bin/env python3
"""Wrap Quran / Bukhari / Muslim references inside <span class="ref">...</span>
blocks in site/catalog/*.html with <a href="..."> links that point to the
matching reader anchor.

Reader anchor schemes:
  Quran   read/quran.html   #s{surah}v{verse}                    (per-verse)
  Bukhari read/bukhari.html #v{volume}b{book}n{number}           (per-hadith)
  Muslim  read/muslim.html  #b{book}n{number:04d}                (per-hadith)

Only the primary, canonical reference form is linked. For ranges, the entire
range text is a single link pointing to the first verse / hadith of the range.
Secondary "continuous-number" mentions (e.g., "also 3894, 5133") and bare
inline prose references are NOT handled by this first pass.

Run order:
  1. python link-refs.py           # rewrites site/catalog/*.html
  2. python build-category-pages.py # propagates into site/category/*.html
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
CATALOG_DIR = ROOT / "site" / "catalog"

# Files to process, tagged with the source identity of the catalog.
# This matters for "Book N, #M" (implicit Muslim) inside muslim.html.
CATALOG_FILES = [
    ("quran.html",     "quran"),
    ("bukhari.html",   "bukhari"),
    ("muslim.html",    "muslim"),
    ("abu-dawud.html", "abu-dawud"),
    ("tirmidhi.html",  "tirmidhi"),
    ("nasai.html",     "nasai"),
    ("ibn-majah.html", "ibn-majah"),
]

# Matches an already-linked token so we don't double-link:
ALREADY_LINKED_RE = re.compile(r'<a\s[^>]*>[^<]*</a>', re.I)

# Range dash class used inside captures:
DASH = r"[-–—]"  # hyphen, en-dash, em-dash

# Full-span ref pattern — we rewrite contents of each <span class="ref">...</span>.
REF_SPAN_RE = re.compile(
    r'(<span\s+class="ref">)(.*?)(</span>)',
    re.DOTALL,
)

# --- Patterns for substrings inside a ref span ---
# Order matters: more specific first.

# 1) Quran N:M or Quran N:M–P  (always named "Quran")
QURAN_RE = re.compile(
    rf'(?P<full>Quran\s+(?P<surah>\d+):(?P<verse>\d+)(?:{DASH}\d+)?)'
)

# 1b) Bare "N:M" (optionally with range) — only used inside a span that already
#     mentioned "Quran". Constrained to valid surah numbers (1–114) and verses
#     (1–286) to avoid matching unrelated things like "Book 18, #150–153" which
#     is already covered by the Bukhari pattern.
BARE_VERSE_RE = re.compile(
    rf'(?<![\w#:-])(?P<full>(?P<surah>\d{{1,3}}):(?P<verse>\d{{1,3}})(?:{DASH}\d{{1,3}})?)(?![\w:#-])'
)

# 2) Bukhari Vol X, Book Y, #Z[–Z2]  (with explicit "Bukhari" prefix)
BUKHARI_FULL_RE = re.compile(
    rf'(?P<full>Bukhari\s+Vol\s+(?P<vol>\d+),\s+Book\s+(?P<book>\d+),\s+#(?P<num>\d+)(?:{DASH}\d+)?)'
)

# 3) Standalone "Vol X, Book Y, #Z[–Z2]" (no Bukhari prefix; this format is
#    distinctly Bukhari/Muhsin Khan — Muslim uses Book+Number, never Volume.)
BUKHARI_VOL_ONLY_RE = re.compile(
    rf'(?<![A-Za-z])(?P<full>Vol\s+(?P<vol>\d+),\s+Book\s+(?P<book>\d+),\s+#(?P<num>\d+)(?:{DASH}\d+)?)'
)

# 4) Muslim Book N, #M[–M2]  (with explicit "Muslim" prefix)
MUSLIM_FULL_RE = re.compile(
    rf'(?P<full>Muslim\s+Book\s+(?P<book>\d+),\s+#(?P<num>\d+)(?:{DASH}\d+)?)'
)

# 5) "Book N, #M[–M2]" inside the Muslim catalog only (Muslim implicit)
MUSLIM_IMPLICIT_RE = re.compile(
    rf'(?<![A-Za-z])(?P<full>Book\s+(?P<book>\d+),\s+#(?P<num>\d+)(?:{DASH}\d+)?)'
)


def link_quran(m: re.Match) -> str:
    full = m.group("full")
    surah = m.group("surah")
    verse = m.group("verse")
    href = f'../read/quran.html#s{surah}v{verse}'
    return f'<a href="{href}">{full}</a>'


def link_bukhari(m: re.Match) -> str:
    full = m.group("full")
    vol = m.group("vol")
    book = m.group("book")
    num = m.group("num")
    href = f'../read/bukhari.html#v{vol}b{book}n{num}'
    return f'<a href="{href}">{full}</a>'


def link_muslim(m: re.Match) -> str:
    full = m.group("full")
    book = int(m.group("book"))  # strip leading zeros (catalog sometimes has "Book 004")
    num = int(m.group("num"))
    href = f'../read/muslim.html#b{book}n{num:04d}'
    return f'<a href="{href}">{full}</a>'


# Tokens in the inner text that are already part of an <a ...>...</a> must be
# protected so we don't re-link them. We do this by temporarily blanking them
# during matching, then restoring.
class Protector:
    def __init__(self, s: str):
        self.orig = s
        self.slots = []
        # Replace each <a ...>...</a> with a placeholder of the same length of nothing-ish
        # but regex-safe. Simpler: just mark positions and skip matches whose span
        # overlaps any protected span. We'll instead do sequential non-overlapping
        # substitution using re.sub with a callback that checks overlap.
        self.protected = []
        for m in ALREADY_LINKED_RE.finditer(s):
            self.protected.append((m.start(), m.end()))

    def overlaps(self, start: int, end: int) -> bool:
        for ps, pe in self.protected:
            if start < pe and end > ps:
                return True
        return False


def apply_with_protection(text: str, pattern: re.Pattern, repl_fn) -> tuple[str, int]:
    """Run pattern.sub(repl_fn, text) but skip any match that overlaps an
    already-present <a>...</a>. Returns (new_text, count_of_substitutions).
    Since protected spans are by byte offset in the ORIGINAL text, we walk
    matches in original text and rebuild the output piecewise.
    """
    p = Protector(text)
    out = []
    last = 0
    count = 0
    for m in pattern.finditer(text):
        if p.overlaps(m.start(), m.end()):
            continue
        out.append(text[last:m.start()])
        out.append(repl_fn(m))
        last = m.end()
        count += 1
    out.append(text[last:])
    return "".join(out), count


def rewrite_ref_inner(inner: str, source_tag: str) -> tuple[str, dict]:
    """Apply all linking patterns to the inner text of a <span class="ref">.
    Returns (new_inner, counts_dict).
    """
    counts = {"quran": 0, "bukhari": 0, "muslim": 0}
    original_inner = inner

    # 1) Quran N:M anywhere (explicit "Quran" prefix).
    inner, n = apply_with_protection(inner, QURAN_RE, link_quran)
    counts["quran"] += n

    # 2) Bukhari Vol X, Book Y, #Z (explicit).
    inner, n = apply_with_protection(inner, BUKHARI_FULL_RE, link_bukhari)
    counts["bukhari"] += n

    # 3) Standalone Vol X, Book Y, #Z (no Bukhari prefix).
    inner, n = apply_with_protection(inner, BUKHARI_VOL_ONLY_RE, link_bukhari)
    counts["bukhari"] += n

    # 4) Muslim Book N, #M (explicit).
    inner, n = apply_with_protection(inner, MUSLIM_FULL_RE, link_muslim)
    counts["muslim"] += n

    # 5) Only inside the muslim catalog: treat "Book N, #M" as implicit Muslim.
    if source_tag == "muslim":
        inner, n = apply_with_protection(inner, MUSLIM_IMPLICIT_RE, link_muslim)
        counts["muslim"] += n

    # 6) Bare "N:M" inside a span that already mentioned Quran — these are
    #    implicit Quran references (e.g. "Quran 2:62 vs 3:85" → 3:85 is Quran).
    #    Only applied when original text contained "Quran". Also skip if the
    #    surah number would be > 114 or verse > 286.
    if "Quran" in original_inner:
        def link_bare_verse(m: re.Match) -> str:
            surah = int(m.group("surah"))
            verse = int(m.group("verse"))
            if surah < 1 or surah > 114 or verse < 1 or verse > 286:
                return m.group(0)  # out of Quran bounds, leave alone
            href = f'../read/quran.html#s{surah}v{verse}'
            return f'<a href="{href}">{m.group("full")}</a>'

        inner, n = apply_with_protection(inner, BARE_VERSE_RE, link_bare_verse)
        counts["quran"] += n

    return inner, counts


def process_file(path: Path, source_tag: str) -> dict:
    text = path.read_text(encoding="utf-8")
    totals = {"quran": 0, "bukhari": 0, "muslim": 0, "spans": 0}

    def span_repl(m: re.Match) -> str:
        open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
        new_inner, counts = rewrite_ref_inner(inner, source_tag)
        for k, v in counts.items():
            totals[k] += v
        totals["spans"] += 1
        return f'{open_tag}{new_inner}{close_tag}'

    new_text = REF_SPAN_RE.sub(span_repl, text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return totals


def main():
    grand = {"quran": 0, "bukhari": 0, "muslim": 0, "spans": 0}
    for fname, tag in CATALOG_FILES:
        path = CATALOG_DIR / fname
        if not path.exists():
            print(f"  {fname}: missing, skipping")
            continue
        t = process_file(path, tag)
        for k, v in t.items():
            grand[k] += v
        print(f"  {fname}: spans={t['spans']}  "
              f"quran={t['quran']}  bukhari={t['bukhari']}  muslim={t['muslim']}")

    print()
    print(f"Totals: spans={grand['spans']}  "
          f"quran={grand['quran']}  bukhari={grand['bukhari']}  muslim={grand['muslim']}")
    print()
    print("Next: run  python build-category-pages.py  to propagate to category pages.")


if __name__ == "__main__":
    main()
