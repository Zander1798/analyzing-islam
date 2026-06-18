#!/usr/bin/env python3
"""Make every remaining scripture reference in catalog + category entries
clickable: tight/spaced Qur'an refs (Q5:60), multi-verse header continuations
(Q2:65, 5:60, 7:166), Bible refs (Genesis 1:26-27), and plain hadith refs —
all validate-before-link (only linked if the target anchor actually exists).

Operates on entry <section> bodies (skipping blockquotes + existing <a>) and
the header <span class="ref"> regions. Idempotent.
"""
import io
import re
import glob
import collections
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"

# ---- anchor sets (only link if the target exists) ----------------------------
def anchors(path):
    p = SITE / path
    if not p.exists():
        return set()
    return set(re.findall(r'id="([^"]+)"', p.read_text(encoding="utf-8", errors="ignore")))

QURAN = anchors("read/quran.html")
HAD = {s: anchors(f"read/{s}.html") for s in
       ["bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah"]}
TANAKH = anchors("read-external/tanakh.html")
NT = anchors("read-external/new-testament.html")

OT_BOOKS = {b: b.lower().replace(" ", "") for b in [
    "Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
    "1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra",
    "Nehemiah","Esther","Job","Psalms","Psalm","Proverbs","Ecclesiastes","Isaiah",
    "Jeremiah","Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos","Obadiah",
    "Jonah","Micah","Nahum","Habakkuk","Zephaniah","Haggai","Zechariah","Malachi"]}
OT_BOOKS["Song of Songs"] = "songofsongs"; OT_BOOKS["Psalm"] = "psalms"
NT_BOOKS = {b: b.lower().replace(" ", "") for b in [
    "Matthew","Mark","Luke","John","Acts","Romans","1 Corinthians","2 Corinthians",
    "Galatians","Ephesians","Philippians","Colossians","1 Thessalonians","2 Thessalonians",
    "1 Timothy","2 Timothy","Titus","Philemon","Hebrews","James","1 Peter","2 Peter",
    "1 John","2 John","3 John","Jude","Revelation"]}
HAD_NAMES = sorted(["Bukhari","Muslim","Abu Dawud","Tirmidhi","Nasa'i","Nasa’i","Nasai","Ibn Majah"], key=len, reverse=True)
HAD_SLUG = {"bukhari":"bukhari","muslim":"muslim","abudawud":"abu-dawud","abu dawud":"abu-dawud",
            "tirmidhi":"tirmidhi","nasai":"nasai","ibnmajah":"ibn-majah","ibn majah":"ibn-majah"}

_Q = re.compile(r"\bQ\s?(\d+):(\d+)((?:[–-]\d+)?)")
_BARE = re.compile(r"(?<![\w:/#-])(\d+):(\d+)((?:[–-]\d+)?)")   # for header multi-verse continuations
_BIB = re.compile(r"\b(" + "|".join(re.escape(b) for b in sorted(list(OT_BOOKS)+list(NT_BOOKS), key=len, reverse=True)) + r")\s(\d+):(\d+)((?:[–-]\d+)?)")
_HAD = re.compile(r"\b(" + "|".join(re.escape(n) for n in HAD_NAMES) + r")\s(\d+)([a-z]?)")

cnt = collections.Counter()

def q_link(m):
    s, v, rng = m.group(1), m.group(2), m.group(3)
    if f"s{s}v{v}" in QURAN:
        cnt["quran"] += 1
        return f'<a class="cite-link" href="../read/quran.html#s{s}v{v}">Q{s}:{v}{rng}</a>'
    return m.group(0)

def bare_link(m):   # header continuation "5:60" -> Q5:60 link
    s, v, rng = m.group(1), m.group(2), m.group(3)
    if f"s{s}v{v}" in QURAN:
        cnt["quran-multiverse"] += 1
        return f'<a class="cite-link" href="../read/quran.html#s{s}v{v}">Q{s}:{v}{rng}</a>'
    return m.group(0)

def bib_link(m):
    book, ch, v, rng = m.group(1), m.group(2), m.group(3), m.group(4)
    if book in OT_BOOKS:
        slug, anc, fn = OT_BOOKS[book], f"{OT_BOOKS[book]}-{ch}-{v}", "tanakh"
        ok = anc in TANAKH
    else:
        slug, anc, fn = NT_BOOKS[book], f"{NT_BOOKS[book]}-{ch}-{v}", "new-testament"
        ok = anc in NT
    if ok:
        cnt["bible"] += 1
        return f'<a class="cite-link" href="../read-external/{fn}.html#{anc}">{m.group(0)}</a>'
    return m.group(0)

def had_link(m):
    name, num, suf = m.group(1), m.group(2), m.group(3)
    slug = HAD_SLUG.get(re.sub(r"[’'`]", "", name.lower()))
    # Muslim's reader numbering != its citation numbering; linking a plain
    # Muslim ref by number would point to the WRONG hadith. Leave Muslim plain
    # here (its header citations are already correctly re-pointed by quote-match).
    if slug == "muslim":
        return m.group(0)
    if slug and f"h{num}" in HAD.get(slug, set()):
        cnt["hadith"] += 1
        return f'<a class="cite-link" href="../read/{slug}.html#h{num}{suf}">{m.group(0)}</a>'
    return m.group(0)

SKIP = re.compile(r'(<blockquote[^>]*>.*?</blockquote>|<a\b[^>]*>.*?</a>|<h[1-6][^>]*>.*?</h[1-6]>)', re.S | re.I)

def link_text(s, header=False):
    s = _Q.sub(q_link, s)
    s = _BIB.sub(bib_link, s)
    s = _HAD.sub(had_link, s)
    if header:
        s = _BARE.sub(bare_link, s)
    return s

def process_segments(html, header=False):
    parts = SKIP.split(html)
    return "".join(p if i % 2 else link_text(p, header) for i, p in enumerate(parts))

def process_page(path):
    t = io.open(path, encoding="utf-8").read()
    # entry bodies (<section> ... </section>)
    t = re.sub(r"<section>(.*?)</section>", lambda m: "<section>" + process_segments(m.group(1)) + "</section>", t, flags=re.S)
    # headers (<span class="ref"> ... </span>)
    t = re.sub(r'(<span class="ref">)(.*?)(</span>)', lambda m: m.group(1) + process_segments(m.group(2), header=True) + m.group(3), t, flags=re.S)
    io.open(path, "w", encoding="utf-8").write(t)

if __name__ == "__main__":
    for f in glob.glob(str(SITE / "catalog/*.html")) + glob.glob(str(SITE / "category/*.html")):
        process_page(f)
    print("links added:", dict(cnt))
