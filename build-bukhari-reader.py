#!/usr/bin/env python3
"""Convert extracted Sahih al-Bukhari PDF text into a styled HTML reader page.

Reads: bukhari-re.txt (produced by: pdftotext -enc UTF-8 -layout en_Sahih_Al-Bukhari.pdf)
Writes: site/read/bukhari.html
"""
import re
import sys
import html as html_lib
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BOOK_HEADER_RE = re.compile(r"^Book\s+(\d+):\s+(.+?)\s*$")
HADITH_RE = re.compile(r"^Volume\s+(\d+),\s*Book\s+(\d+),\s*Number\s+(\d+[a-z]?):\s*$")
PAGE_HEADER_RE = re.compile(r"^\s*SAHIH\s+BUKHARI\b.*$|^\s*Volume\s+\d+\s+-\s+\d+\s*/\s*\d+\s*$|^\s*-\s*\d+\s*/\s*\d+\s*$")
NARRATOR_RE = re.compile(r"^\s*Narrated\s+(.+?)\s*:?\s*$")


def parse(raw: str):
    lines = raw.splitlines()

    # Find content start — first "Book 1: Revelation" line after TOC.
    # TOC has "Book 1: Revelation ............................7" with dots; real header is plain.
    start = 0
    for i, ln in enumerate(lines):
        m = BOOK_HEADER_RE.match(ln.rstrip())
        if m and "........" not in ln and m.group(1) == "1":
            start = i
            break

    lines = lines[start:]

    books = []
    current_book = None
    current_hadith = None

    for ln in lines:
        # Skip page-header noise.
        if PAGE_HEADER_RE.match(ln):
            continue
        stripped_for_match = ln.rstrip()
        stripped = ln.strip()

        # New book header.
        m = BOOK_HEADER_RE.match(stripped_for_match)
        if m and "........" not in ln:
            if current_hadith:
                current_book["hadiths"].append(current_hadith)
                current_hadith = None
            current_book = {
                "number": int(m.group(1)),
                "title": m.group(2).strip(),
                "hadiths": [],
            }
            books.append(current_book)
            continue

        # New hadith header.
        m = HADITH_RE.match(stripped)
        if m:
            if current_book is None:
                # Shouldn't happen but guard anyway.
                current_book = {"number": 0, "title": "Prelude", "hadiths": []}
                books.append(current_book)
            if current_hadith:
                current_book["hadiths"].append(current_hadith)
            current_hadith = {
                "volume": int(m.group(1)),
                "book": int(m.group(2)),
                "number": m.group(3),
                "narrator": None,
                "paragraphs": [],
                "_buffer": [],
            }
            continue

        if current_hadith is None:
            # Skip stray lines between the start-of-content marker and the first hadith.
            continue

        # Narrator line (inside hadith).
        m = NARRATOR_RE.match(ln)
        if m and current_hadith["narrator"] is None:
            current_hadith["narrator"] = m.group(1).strip()
            continue

        # Empty line → paragraph break.
        if not stripped:
            if current_hadith["_buffer"]:
                current_hadith["paragraphs"].append(" ".join(current_hadith["_buffer"]).strip())
                current_hadith["_buffer"] = []
            continue

        # Regular body line — append to current paragraph buffer.
        current_hadith["_buffer"].append(stripped)

    # Flush trailing hadith.
    if current_hadith and current_book is not None:
        if current_hadith["_buffer"]:
            current_hadith["paragraphs"].append(" ".join(current_hadith["_buffer"]).strip())
        current_book["hadiths"].append(current_hadith)

    # Clean up empty hadiths.
    for b in books:
        b["hadiths"] = [h for h in b["hadiths"] if h.get("paragraphs") or h.get("narrator")]

    # Drop any trailing books that are artefacts (e.g. glossary/appendix).
    # Keep only books that have at least one hadith with paragraphs.
    books = [b for b in books if b["hadiths"]]

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
            narrator_html = (
                f'<div class="hadith-narrator">Narrated {html_lib.escape(h["narrator"])}</div>\n        '
                if h["narrator"]
                else ""
            )
            hadith_html.append(
                f'    <article class="hadith" id="v{h["volume"]}b{h["book"]}n{h["number"]}">\n'
                f'      <header class="hadith-header">\n'
                f'        <span class="hadith-ref">Volume {h["volume"]} · Book {h["book"]} · Number {h["number"]}</span>\n'
                f'      </header>\n'
                f'      <div class="hadith-body">\n'
                f'        {narrator_html}{paragraphs_html}\n'
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
<meta name="description" content="Read the complete Sahih al-Bukhari — all {total} hadiths across {books_count} books. Translation by M. Muhsin Khan.">
<title>Read Sahih al-Bukhari — Islam Analyzed</title>
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
      <a href="../faq.html">FAQ</a>
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
      <div class="reader-meta">Sahih al-Bukhari · English translation by M. Muhsin Khan</div>
      <h1>Ṣaḥīḥ al-Bukhārī</h1>
      <p class="reader-intro">The complete collection — {total} hadiths across {books_count} books, compiled by Muḥammad al-Bukhārī (d. 870 CE). Regarded by most Sunni Muslims as the most authentic hadith collection after the Qurʾān itself.</p>
      <div class="reader-cta">
        <a href="../read.html" class="btn">← All sources</a>
        <a href="../assets/sources/bukhari.pdf" class="btn" download>Download PDF</a>
      </div>
    </header>

{body}

    <footer class="reader-footer">
      <p>Source: Sahih al-Bukhari, English translation by M. Muhsin Khan. Quoted here under fair use / fair dealing for the purposes of criticism, review, and commentary.</p>
    </footer>

  </main>

</div>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def main():
    src = Path(__file__).parent / "bukhari-re.txt"
    if not src.exists():
        raise SystemExit(
            f"Source {src} not found. Run first:\n"
            f"  pdftotext -enc UTF-8 -layout 'en_Sahih_Al-Bukhari.pdf' bukhari-re.txt"
        )
    raw = src.read_text(encoding="utf-8")
    books = parse(raw)
    html_out = build_html(books)
    out_path = Path(__file__).parent / "site" / "read" / "bukhari.html"
    out_path.write_text(html_out, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
