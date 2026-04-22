#!/usr/bin/env python3
"""Convert extracted Sahih Muslim PDF text into a styled HTML reader page.

Reads: muslim-re.txt
Writes: site/read/muslim.html
"""
import re
import sys
import html as html_lib
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HADITH_RE = re.compile(r"^Book\s+(\d+),\s*Number\s+(\d+[a-z]?):\s*$")
CHAPTER_RE = re.compile(r"^Chapter\s+\d+\s*:.*$")
PAGE_HEADER_RE = re.compile(
    r"^\s*SAHIH\s+MUSLIM\b.*$|^\s*\d+\s*/\s*\d+\s*$|^\s*-\s*\d+\s*/\s*\d+\s*$"
)

# Book titles — book number → title. Source: extracted from PDF TOC.
BOOK_TITLES = {
    1: "The Book of Faith (Kitab Al-Iman)",
    2: "The Book of Purification (Kitab Al-Taharah)",
    3: "The Book of Menstruation (Kitab Al-Haid)",
    4: "The Book of Prayers (Kitab Al-Salat)",
    5: "The Book of Zakat (Kitab Al-Zakat)",
    6: "The Book of Fasting (Kitab Al-Sawm)",
    7: "The Book of Pilgrimage (Kitab Al-Hajj)",
    8: "The Book of Marriage (Kitab Al-Nikah)",
    9: "The Book of Divorce (Kitab Al-Talaq)",
    10: "The Book of Transactions (Kitab Al-Buyu)",
    11: "The Book Pertaining to the Rules of Inheritance (Kitab Al-Faraid)",
    12: "The Book of Gifts (Kitab Al-Hibat)",
    13: "The Book of Bequests (Kitab Al-Wasiyya)",
    14: "The Book of Vows (Kitab Al-Nadhr)",
    15: "The Book of Oaths (Kitab Al-Aiman)",
    16: "The Book Pertaining to the Oath (Kitab Al-Qasama)",
    17: "The Book Pertaining to Punishments Prescribed by Islam (Kitab Al-Hudud)",
    18: "The Book Pertaining to Judicial Decisions (Kitab Al-Aqdiyya)",
    19: "The Book of Jihad and Expedition (Kitab Al-Jihad wa'l-Siyar)",
    20: "The Book on Government (Kitab Al-Imara)",
    21: "The Book of Games and Animals that May be Slaughtered (Kitab al-Said)",
    22: "The Book of Sacrifices (Kitab Al-Adahi)",
    23: "The Book of Drinks (Kitab Al-Ashriba)",
    24: "The Book Pertaining to Clothes and Decoration (Kitab Al-Libas)",
    25: "The Book on General Behaviour (Kitab Al-Adab)",
    26: "The Book on Salutations and Greetings (Kitab As-Salam)",
    27: "The Book Concerning the Use of Correct Words (Kitab Al-Alfaz)",
    28: "The Book of Poetry (Kitab Al-Sh'ir)",
    29: "The Book of Vision (Kitab Al-Ruya)",
    30: "The Book Pertaining to the Excellent Qualities of the Prophet (Kitab Al-Fada'il)",
    31: "The Book Pertaining to the Merits of the Companions (Kitab Fada'il Al-Sahabah)",
    32: "The Book of Virtue, Good Manners and Joining of Ties of Relationship (Kitab Al-Birr)",
    33: "The Book of Destiny (Kitab-ul-Qadr)",
    34: "The Book of Knowledge (Kitab Al-'Ilm)",
    35: "The Book Pertaining to the Remembrance of Allah (Kitab Al-Dhikr)",
    36: "The Book of Heart-Melting Traditions (Kitab Al-Riqaq)",
    37: "The Book Pertaining to Repentance (Kitab Al-Tauba)",
    38: "Pertaining to the Characteristics of the Hypocrites (Kitab Sifat Al-Munafiqin)",
    39: "The Book Giving Description of the Day of Judgement, Paradise and Hell (Kitab Sifat Al-Qiyama)",
    40: "The Book Pertaining to Paradise (Kitab Al-Jannah)",
    41: "The Book Pertaining to the Turmoil and Portents of the Last Hour (Kitab Al-Fitan)",
    42: "The Book Pertaining to Piety and Softening of Hearts (Kitab Al-Zuhd)",
    43: "The Book of Commentary (Kitab Al-Tafsir)",
}


def parse(raw: str):
    lines = raw.splitlines()

    # Find content start: first real hadith header "Book 001, Number 0001:".
    start = 0
    for i, ln in enumerate(lines):
        if HADITH_RE.match(ln.strip()):
            start = i
            break

    lines = lines[start:]

    # Group hadiths by book number.
    books_map = {}  # book_num -> list of hadiths
    current_hadith = None

    def flush_hadith():
        nonlocal current_hadith
        if current_hadith is None:
            return
        if current_hadith["_buffer"]:
            current_hadith["paragraphs"].append(" ".join(current_hadith["_buffer"]).strip())
            current_hadith["_buffer"] = []
        if current_hadith["paragraphs"]:
            books_map.setdefault(current_hadith["book"], []).append(current_hadith)
        current_hadith = None

    for ln in lines:
        if PAGE_HEADER_RE.match(ln):
            continue
        stripped = ln.strip()
        m = HADITH_RE.match(stripped)
        if m:
            flush_hadith()
            current_hadith = {
                "book": int(m.group(1)),
                "number": m.group(2),
                "paragraphs": [],
                "_buffer": [],
            }
            continue

        if CHAPTER_RE.match(stripped):
            continue

        if current_hadith is None:
            continue

        if not stripped:
            if current_hadith["_buffer"]:
                current_hadith["paragraphs"].append(" ".join(current_hadith["_buffer"]).strip())
                current_hadith["_buffer"] = []
            continue

        current_hadith["_buffer"].append(stripped)

    flush_hadith()

    # Assemble books in numeric order using known titles.
    books = []
    for bnum in sorted(books_map.keys()):
        title = BOOK_TITLES.get(bnum, f"Book {bnum}")
        books.append({"number": bnum, "title": title, "hadiths": books_map[bnum]})
    return books


def build_html(books):
    total_hadiths = sum(len(b["hadiths"]) for b in books)
    print(f"Parsed {len(books)} books, {total_hadiths} hadiths.")

    toc_items = []
    book_sections = []
    for b in books:
        bnum = b["number"]
        btitle = b["title"]
        hcount = len(b["hadiths"])
        toc_items.append(
            f'<li><a href="#book-{bnum}">'
            f'<span class="toc-num">{bnum}</span>'
            f' <span class="toc-name">{html_lib.escape(btitle)}</span>'
            f'</a></li>'
        )

        hadith_html = []
        for h in b["hadiths"]:
            paragraphs_html = "\n        ".join(
                f'<p>{html_lib.escape(p)}</p>' for p in h["paragraphs"] if p.strip()
            )
            hadith_html.append(
                f'    <article class="hadith" id="b{h["book"]}n{h["number"]}">\n'
                f'      <header class="hadith-header">\n'
                f'        <span class="hadith-ref">Book {h["book"]} · Number {h["number"]}</span>\n'
                f'      </header>\n'
                f'      <div class="hadith-body">\n'
                f'        {paragraphs_html}\n'
                f'      </div>\n'
                f'    </article>'
            )

        book_sections.append(
            f'<section class="hadith-book" id="book-{bnum}">\n'
            f'  <header class="hadith-book-header">\n'
            f'    <div class="hadith-book-number">Book {bnum}</div>\n'
            f'    <h2>{html_lib.escape(btitle)}</h2>\n'
            f'    <div class="hadith-book-subtitle">{hcount} hadith{"s" if hcount != 1 else ""}</div>\n'
            f'  </header>\n'
            f'  <div class="hadith-book-body">\n'
            + "\n".join(hadith_html)
            + "\n  </div>\n"
            f'</section>'
        )

    return TEMPLATE.format(
        toc="\n".join(toc_items),
        body="\n\n".join(book_sections),
        total=f"{total_hadiths:,}",
        books_count=len(books),
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read the complete Sahih Muslim — {total} hadiths across {books_count} books. Translation by Abd-al-Hamid Siddiqui.">
<title>Read Sahih Muslim — Islam Analyzed</title>
<link rel="stylesheet" href="../assets/css/style.css">
<link rel="stylesheet" href="../assets/css/reader.css">
</head>
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Islam Analyzed</a>
    <div class="site-nav-links">
      <a href="../index.html">Home</a>
      <a href="../catalog.html">Catalog</a>
      <a href="../read.html" class="active">Read</a>
      <a href="../about.html">About</a>
    </div>
  </div>
</nav>

<div class="reader-layout">

  <aside class="reader-toc">
    <div class="reader-toc-header">Books</div>
    <ol>
{toc}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">Sahih Muslim · English translation by Abd-al-Hamid Siddiqui</div>
      <h1>Ṣaḥīḥ Muslim</h1>
      <p class="reader-intro">The complete collection — {total} hadiths across {books_count} books, compiled by Muslim ibn al-Ḥajjāj (d. 875 CE). The second of the two <em>Ṣaḥīḥayn</em>, together with al-Bukhārī regarded as the most authoritative hadith books in Sunnī Islam.</p>
      <div class="reader-cta">
        <a href="../read.html" class="btn">← All sources</a>
        <a href="../assets/sources/muslim.pdf" class="btn" download>Download PDF</a>
      </div>
    </header>

{body}

    <footer class="reader-footer">
      <p>Source: Sahih Muslim, English translation by Abd-al-Hamid Siddiqui. Quoted here under fair use / fair dealing for the purposes of criticism, review, and commentary.</p>
    </footer>

  </main>

</div>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def main():
    src = Path(__file__).parent / "muslim-re.txt"
    if not src.exists():
        raise SystemExit(f"Source {src} not found.")
    raw = src.read_text(encoding="utf-8")
    books = parse(raw)
    html_out = build_html(books)
    out_path = Path(__file__).parent / "site" / "read" / "muslim.html"
    out_path.write_text(html_out, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
