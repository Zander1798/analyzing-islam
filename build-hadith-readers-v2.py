#!/usr/bin/env python3
"""Rebuild the 6 hadith reader pages as COMPLETE, browsable collections
anchored by sunnah.com REFERENCE number (= the citation number the book uses).

Source: fawazahmed0/hadith-api complete editions (downloaded to hadith-sunnah/).
Its `hadithnumber` equals sunnah.com's reference number — verified
(eng-bukhari 1927 == kiss-while-fasting, the book's "Bukhari 1927"). So
anchoring each hadith at id="h{hadithnumber}" makes citation links land on the
exact, full, matching hadith.

Chrome-preserving: we keep each existing read/{slug}.html page's <head>, nav,
hero, scripts (highlights, search, snap-to-hash, auth, the sunnah.com button)
and replace ONLY the TOC list and the hadith-book sections. (Regenerating from a
template would strip those features — the Plan 1 lesson.)
"""
import html as html_lib
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
DATA = ROOT / "hadith-sunnah"
READ = ROOT / "site" / "read"

# (read-page slug, fawazahmed0 edition stem, sunnah.com slug for per-hadith link)
COLLECTIONS = [
    ("bukhari", "bukhari", "bukhari"),
    ("muslim", "muslim", "muslim"),
    ("abu-dawud", "abudawud", "abudawud"),
    ("tirmidhi", "tirmidhi", "tirmidhi"),
    ("nasai", "nasai", "nasai"),
    ("ibn-majah", "ibnmajah", "ibnmajah"),
]

_NARR = re.compile(r"^((?:It was narrated|Narrated|It is narrated|Narrated that)[^:]{0,80}:)\s*")


def esc(s):
    return html_lib.escape(s or "", quote=True)


def render_hadith(num, book, eng_text, arabic, grade, sunnah_slug):
    # Separate a leading "Narrated X:" into the narrator line.
    narrator = ""
    body = (eng_text or "").strip()
    m = _NARR.match(body)
    if m:
        narrator = m.group(1).strip().rstrip(":")
        body = body[m.end():].strip()
    url = f"https://sunnah.com/{sunnah_slug}:{num}"
    parts = [
        f'    <article class="hadith" id="h{num}">',
        '      <header class="hadith-header">',
        f'        <span class="hadith-ref"><a href="{url}" target="_blank" rel="noopener">Hadith {num} · Book {book}</a></span>',
    ]
    if grade:
        parts.append(f'        <span class="hadith-grade">{esc(grade)}</span>')
    parts.append('      </header>')
    parts.append('      <div class="hadith-body">')
    if narrator:
        parts.append(f'        <div class="hadith-narrator">{esc(narrator)}</div>')
    if body:
        parts.append(f'        <p>{esc(body)}</p>')
    if arabic:
        parts.append(f'        <p class="hadith-arabic" lang="ar" dir="rtl">{esc(arabic)}</p>')
    parts += ["      </div>", "    </article>"]
    return "\n".join(parts)


def build_content(eng, ara, sunnah_slug):
    sections = eng["metadata"]["sections"]  # {book_no(str): name}
    amap = {h["hadithnumber"]: (h.get("text") or "") for h in ara["hadiths"]}
    by_book = {}
    for h in eng["hadiths"]:
        bk = (h.get("reference") or {}).get("book")
        if bk is None:
            continue
        by_book.setdefault(bk, []).append(h)
    toc, books = [], []
    for bk in sorted(by_book):
        name = sections.get(str(bk)) or f"Book {bk}"
        if not name.strip():
            name = f"Book {bk}"
        hs = sorted(by_book[bk], key=lambda x: x["hadithnumber"])
        toc.append(
            f'<li><a href="#book-{bk}"><span class="toc-num">{bk}</span> '
            f'<span class="toc-name">{esc(name)}</span></a></li>')
        block = [
            f'<section class="hadith-book" id="book-{bk}">',
            '  <header class="hadith-book-header">',
            f'    <div class="hadith-book-number">Book {bk}</div>',
            f'    <h2>{esc(name)}</h2>',
            f'    <div class="hadith-book-subtitle">{len(hs)} hadith{"s" if len(hs)!=1 else ""}</div>',
            '  </header>',
            '  <div class="hadith-book-body">',
        ]
        for h in hs:
            num = h["hadithnumber"]
            grade = ""
            gs = h.get("grades") or []
            if gs:
                grade = gs[0].get("grade") or ""
            block.append(render_hadith(num, bk, h.get("text"), amap.get(num), grade, sunnah_slug))
        block += ["  </div>", "</section>", ""]
        books.append("\n".join(block))
    return "\n".join(toc), "\n\n".join(books), len(eng["hadiths"]), len(by_book)


# TOC list region (inside <aside class="reader-toc"> … <ol>HERE</ol> … </aside>)
_TOC_RE = re.compile(r'(<aside class="reader-toc">.*?<ol>)(.*?)(</ol>\s*</aside>)', re.S)
# Book-sections region: from the first hadith-book section to </main>.
_BOOKS_RE = re.compile(r'(</header>\s*)(<section class="hadith-book".*?</section>\s*)(</main>)', re.S)


def build_one(slug, stem, sunnah_slug):
    eng = json.loads((DATA / f"eng-{stem}.json").read_text(encoding="utf-8"))
    ara = json.loads((DATA / f"ara-{stem}.json").read_text(encoding="utf-8"))
    toc_html, books_html, n_had, n_books = build_content(eng, ara, sunnah_slug)
    page = (READ / f"{slug}.html").read_text(encoding="utf-8")
    if not _TOC_RE.search(page) or not _BOOKS_RE.search(page):
        raise SystemExit(f"  {slug}: chrome markers not found — aborting")
    page = _TOC_RE.sub(lambda m: m.group(1) + "\n" + toc_html + "\n    " + m.group(3), page, count=1)
    page = _BOOKS_RE.sub(lambda m: m.group(1) + "\n" + books_html + "\n  " + m.group(3), page, count=1)
    (READ / f"{slug}.html").write_text(page, encoding="utf-8")
    print(f"  {slug}: {n_had} hadiths, {n_books} books")


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for slug, stem, sunnah_slug in COLLECTIONS:
        if only and slug != only:
            continue
        build_one(slug, stem, sunnah_slug)
    print("done.")


if __name__ == "__main__":
    main()
