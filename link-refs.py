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

# 6–9) The four Sunan collections sourced from hadith-json (idInBook anchors).
#     All of them use the same form: <SourceName> [#]<num>. The `#` is optional
#     because body text sometimes drops it ("Tirmidhi 2562" vs. "Tirmidhi #2562").
#     Ranges (e.g. "#1042-#1046") are linked by the FIRST number only.

# Source-name alternations — tolerant of common variants.
_ABU_DAWUD_NAME  = r'(?:Sunan\s+Ab[iu]\s+D[aā]wud|Ab[uū]\s+D[aā]wud)'
_TIRMIDHI_NAME   = r'(?:Jami[\'’`]?\s+at-Tirmidh[iī]|(?:at-)?Tirmidh[iī])'
_NASAI_NAME      = r'(?:Sunan\s+(?:an-|al-)?Nasa[\'’`]?[iI]|(?:an-|al-)?Nasa[\'’`]?[iI])'
_IBN_MAJAH_NAME  = r'(?:Sunan\s+Ibn\s+M[aā]jah|Ibn\s+M[aā]jah)'

ABU_DAWUD_RE = re.compile(
    rf'(?P<full>{_ABU_DAWUD_NAME}\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?)'
)
TIRMIDHI_RE = re.compile(
    rf'(?P<full>{_TIRMIDHI_NAME}\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?)'
)
NASAI_RE = re.compile(
    rf'(?P<full>{_NASAI_NAME}\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?)'
)
IBN_MAJAH_RE = re.compile(
    rf'(?P<full>{_IBN_MAJAH_NAME}\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?)'
)


def _anchor(href: str, text: str, cls: str = "") -> str:
    cls_attr = f' class="{cls}"' if cls else ""
    return f'<a{cls_attr} href="{href}">{text}</a>'


def make_link_quran(cls: str = ""):
    def fn(m: re.Match) -> str:
        surah = m.group("surah")
        verse = m.group("verse")
        return _anchor(f'../read/quran.html#s{surah}v{verse}', m.group("full"), cls)
    return fn


def make_link_bukhari(cls: str = ""):
    def fn(m: re.Match) -> str:
        vol = m.group("vol")
        book = m.group("book")
        num = m.group("num")
        return _anchor(f'../read/bukhari.html#v{vol}b{book}n{num}', m.group("full"), cls)
    return fn


def make_link_muslim(cls: str = ""):
    def fn(m: re.Match) -> str:
        book = int(m.group("book"))  # strip leading zeros (catalog sometimes has "Book 004")
        num = int(m.group("num"))
        return _anchor(f'../read/muslim.html#b{book}n{num:04d}', m.group("full"), cls)
    return fn


def _make_single_num_linker(slug: str):
    """Factory for sources whose anchor is `#h{idInBook}` (Abu Dawud, Tirmidhi,
    Nasai, Ibn Majah)."""
    def factory(cls: str = ""):
        def fn(m: re.Match) -> str:
            num = m.group("num")
            return _anchor(f'../read/{slug}.html#h{num}', m.group("full"), cls)
        return fn
    return factory


make_link_abu_dawud = _make_single_num_linker("abu-dawud")
make_link_tirmidhi  = _make_single_num_linker("tirmidhi")
make_link_nasai     = _make_single_num_linker("nasai")
make_link_ibn_majah = _make_single_num_linker("ibn-majah")


# Default header-ref linkers (no class — matches existing behavior).
link_quran = make_link_quran()
link_bukhari = make_link_bukhari()
link_muslim = make_link_muslim()
link_abu_dawud = make_link_abu_dawud()
link_tirmidhi = make_link_tirmidhi()
link_nasai = make_link_nasai()
link_ibn_majah = make_link_ibn_majah()

# In-body citation linkers (styled via .cite-link CSS).
link_quran_body = make_link_quran("cite-link")
link_bukhari_body = make_link_bukhari("cite-link")
link_muslim_body = make_link_muslim("cite-link")
link_abu_dawud_body = make_link_abu_dawud("cite-link")
link_tirmidhi_body = make_link_tirmidhi("cite-link")
link_nasai_body = make_link_nasai("cite-link")
link_ibn_majah_body = make_link_ibn_majah("cite-link")


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


def rewrite_inner(inner: str, source_tag: str, linkers: dict) -> tuple[str, dict]:
    """Apply all linking patterns to an inner HTML fragment.

    `linkers` supplies the callbacks used for each match — lets the caller pick
    header-ref style (unclassed <a>) vs in-body style (<a class="cite-link">).
    Expected keys: quran, bukhari, muslim, abu_dawud, tirmidhi, nasai, ibn_majah.

    Returns (new_inner, counts_dict).
    """
    counts = {"quran": 0, "bukhari": 0, "muslim": 0,
              "abu_dawud": 0, "tirmidhi": 0, "nasai": 0, "ibn_majah": 0}
    original_inner = inner
    q_link = linkers["quran"]
    b_link = linkers["bukhari"]
    m_link = linkers["muslim"]
    ad_link = linkers["abu_dawud"]
    t_link = linkers["tirmidhi"]
    na_link = linkers["nasai"]
    im_link = linkers["ibn_majah"]

    # 1) Quran N:M anywhere (explicit "Quran" prefix).
    inner, n = apply_with_protection(inner, QURAN_RE, q_link)
    counts["quran"] += n

    # 2) Bukhari Vol X, Book Y, #Z (explicit).
    inner, n = apply_with_protection(inner, BUKHARI_FULL_RE, b_link)
    counts["bukhari"] += n

    # 3) Standalone Vol X, Book Y, #Z (no Bukhari prefix).
    inner, n = apply_with_protection(inner, BUKHARI_VOL_ONLY_RE, b_link)
    counts["bukhari"] += n

    # 4) Muslim Book N, #M (explicit).
    inner, n = apply_with_protection(inner, MUSLIM_FULL_RE, m_link)
    counts["muslim"] += n

    # 5) Only inside the muslim catalog: treat "Book N, #M" as implicit Muslim.
    if source_tag == "muslim":
        inner, n = apply_with_protection(inner, MUSLIM_IMPLICIT_RE, m_link)
        counts["muslim"] += n

    # 6-9) The four single-number Sunan collections (idInBook anchors).
    inner, n = apply_with_protection(inner, ABU_DAWUD_RE, ad_link)
    counts["abu_dawud"] += n
    inner, n = apply_with_protection(inner, TIRMIDHI_RE, t_link)
    counts["tirmidhi"] += n
    inner, n = apply_with_protection(inner, NASAI_RE, na_link)
    counts["nasai"] += n
    inner, n = apply_with_protection(inner, IBN_MAJAH_RE, im_link)
    counts["ibn_majah"] += n

    # 6) Bare "N:M" inside a fragment that already mentioned Quran — these are
    #    implicit Quran references (e.g. "Quran 2:62 vs 3:85" → 3:85 is Quran).
    #    Only applied when original text contained "Quran". Also skip if the
    #    surah number would be > 114 or verse > 286.
    if "Quran" in original_inner:
        # Derive class from the caller's quran linker so body-mode bare refs
        # also get the cite-link underline.
        probe = q_link(re.match(QURAN_RE, "Quran 1:1"))
        cls = ' class="cite-link"' if 'class="cite-link"' in probe else ''

        def link_bare_verse(m: re.Match) -> str:
            surah = int(m.group("surah"))
            verse = int(m.group("verse"))
            if surah < 1 or surah > 114 or verse < 1 or verse > 286:
                return m.group(0)  # out of Quran bounds, leave alone
            href = f'../read/quran.html#s{surah}v{verse}'
            return f'<a{cls} href="{href}">{m.group("full")}</a>'

        inner, n = apply_with_protection(inner, BARE_VERSE_RE, link_bare_verse)
        counts["quran"] += n

    return inner, counts


HEADER_LINKERS = {
    "quran": link_quran, "bukhari": link_bukhari, "muslim": link_muslim,
    "abu_dawud": link_abu_dawud, "tirmidhi": link_tirmidhi,
    "nasai": link_nasai, "ibn_majah": link_ibn_majah,
}
BODY_LINKERS = {
    "quran": link_quran_body, "bukhari": link_bukhari_body, "muslim": link_muslim_body,
    "abu_dawud": link_abu_dawud_body, "tirmidhi": link_tirmidhi_body,
    "nasai": link_nasai_body, "ibn_majah": link_ibn_majah_body,
}


# Entry-body region: only plain <section> (no attributes). The hero panel on
# each catalog page is `<section class="hero" ...>` and is thus excluded.
SECTION_RE = re.compile(r'(<section>)(.*?)(</section>)', re.DOTALL)


_SOURCE_KEYS = ["quran", "bukhari", "muslim", "abu_dawud", "tirmidhi", "nasai", "ibn_majah"]


def process_file(path: Path, source_tag: str) -> dict:
    original = path.read_text(encoding="utf-8")
    totals = {"ref_spans": 0, "body_sections": 0}
    for k in _SOURCE_KEYS:
        totals[f"ref_{k}"] = 0
        totals[f"body_{k}"] = 0

    # Pass 1: header <span class="ref">...</span> (unclassed <a>, existing style).
    def span_repl(m: re.Match) -> str:
        open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
        new_inner, counts = rewrite_inner(inner, source_tag, HEADER_LINKERS)
        for k in _SOURCE_KEYS:
            totals[f"ref_{k}"] += counts[k]
        totals["ref_spans"] += 1
        return f'{open_tag}{new_inner}{close_tag}'

    text = REF_SPAN_RE.sub(span_repl, original)

    # Pass 2: entry body <section>...</section> (<a class="cite-link"> style).
    def section_repl(m: re.Match) -> str:
        open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
        new_inner, counts = rewrite_inner(inner, source_tag, BODY_LINKERS)
        for k in _SOURCE_KEYS:
            totals[f"body_{k}"] += counts[k]
        totals["body_sections"] += 1
        return f'{open_tag}{new_inner}{close_tag}'

    new_text = SECTION_RE.sub(section_repl, text)
    if new_text != original:
        path.write_text(new_text, encoding="utf-8")
    return totals


def _run_pass() -> int:
    """Run a single pass over all catalog files. Returns total links added."""
    added = 0
    for fname, tag in CATALOG_FILES:
        path = CATALOG_DIR / fname
        if not path.exists():
            continue
        t = process_file(path, tag)
        for k in _SOURCE_KEYS:
            added += t[f"ref_{k}"] + t[f"body_{k}"]
    return added


def main():
    # BARE_VERSE_RE triggers when "Quran" appears in a section's text. A newly
    # linked citation like `<a>Quran 5:67</a>` inserts that string into the
    # section, which can activate bare-verse linking on a later pass for
    # nearby shorthand like "Q 19:29". So we loop until stable.
    MAX_PASSES = 6
    grand_added = 0
    for i in range(1, MAX_PASSES + 1):
        grand = {"ref_spans": 0, "body_sections": 0}
        for k in _SOURCE_KEYS:
            grand[f"ref_{k}"] = 0
            grand[f"body_{k}"] = 0
        pass_added = 0
        for fname, tag in CATALOG_FILES:
            path = CATALOG_DIR / fname
            if not path.exists():
                if i == 1:
                    print(f"  {fname}: missing, skipping")
                continue
            t = process_file(path, tag)
            for k, v in t.items():
                grand[k] += v
            ref_total = sum(t[f"ref_{k}"] for k in _SOURCE_KEYS)
            body_total = sum(t[f"body_{k}"] for k in _SOURCE_KEYS)
            pass_added += ref_total + body_total
            if i == 1:
                print(f"  {fname}: header-refs={ref_total} (spans={t['ref_spans']})  "
                      f"body-cites={body_total} (sections={t['body_sections']})")
        if i == 1:
            print()
            hdr_parts = "  ".join(f"{k}={grand[f'ref_{k}']}" for k in _SOURCE_KEYS)
            body_parts = "  ".join(f"{k}={grand[f'body_{k}']}" for k in _SOURCE_KEYS)
            print(f"Header refs:  spans={grand['ref_spans']}  {hdr_parts}")
            print(f"Body cites:   sections={grand['body_sections']}  {body_parts}")
        grand_added += pass_added
        if pass_added == 0:
            if i > 1:
                print(f"Converged after {i} passes (+{grand_added - (grand_added if i==1 else 0)} extras in passes 2..{i-1}).")
            break
        elif i > 1:
            print(f"Pass {i}: +{pass_added} additional links (bare-verse cascade).")
    else:
        print(f"Warning: did not converge in {MAX_PASSES} passes.")
    print()
    print("Next: run  python build-category-pages.py  to propagate to category pages.")


if __name__ == "__main__":
    main()
