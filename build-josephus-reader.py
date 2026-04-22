#!/usr/bin/env python3
"""Build site/read-external/josephus.html from the Project Gutenberg
Whiston edition of Flavius Josephus (Antiquities PG #2848, Wars PG #2850).

Both files are PD (Whiston 1737). Each file starts with a TOC and then
the full text. We skip the TOC, identify BOOK and CHAPTER headers, and
split the prose inside each chapter on leading "N." section numbers.
"""
import html
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
ANT_PATH = ROOT / ".tmp" / "josephus-antiquities.txt"
WARS_PATH = ROOT / ".tmp" / "josephus-wars.txt"
OUT_PATH = ROOT / "site" / "read-external" / "josephus.html"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def roman_of(n: int) -> str:
    vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
            (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
            (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = []
    for v, s in vals:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def roman_to_int(s: str) -> int:
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, c in enumerate(s):
        v = vals[c]
        if i + 1 < len(s) and vals[s[i + 1]] > v:
            total -= v
        else:
            total += v
    return total


BOOK_RE = re.compile(r"^BOOK\s+([IVXLCM]+)\.\s*(.*)$")
CHAPTER_RE = re.compile(r"^CHAPTER\s+(\d+)\.\s*(.*)$")
SECTION_RE = re.compile(r"^(\d+)\.\s+")


def parse_josephus_text(raw: str, work_slug: str):
    """Parse a Josephus plain-text file and return:
       [(book_num, book_title, [(chap_num, chap_title, [(sec_num, text), ...]), ...]), ...]"""
    # Trim PG boilerplate
    m0 = re.search(r"\*\*\*\s*START OF THE PROJECT GUTENBERG EBOOK[^\n]*\*\*\*", raw)
    m1 = re.search(r"\*\*\*\s*END OF THE PROJECT GUTENBERG EBOOK[^\n]*\*\*\*", raw)
    if m0:
        raw = raw[m0.end():]
    if m1:
        raw = raw[:m1.start()]

    lines = raw.splitlines()

    # Skip the TOC. We assume real content starts at the SECOND BOOK I. line
    # (first is in the TOC), since every BOOK header is duplicated. Same for
    # PREFACE — skip until we see the second occurrence.
    book_i_line = -1
    count = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("BOOK I."):
            count += 1
            if count == 2:
                book_i_line = i
                break
    if book_i_line == -1:
        sys.exit(f"Couldn't find the start of Book I for {work_slug}")
    # Actually Wars of the Jews also has "BOOK I." — same pattern applies.
    lines = lines[book_i_line:]

    # Collect books
    books = []
    current_book = None
    current_chapter = None

    def finalise_chapter():
        nonlocal current_chapter
        if current_chapter is None:
            return
        # Flush last section
        if current_chapter.get("_buf"):
            sec_num = current_chapter["_sec"]
            text = " ".join(current_chapter["_buf"]).strip()
            text = re.sub(r"\s+", " ", text)
            if text:
                if sec_num is None:
                    current_chapter["sections"].append((None, text))
                else:
                    current_chapter["sections"].append((sec_num, text))
            current_chapter["_buf"] = []
            current_chapter["_sec"] = None
        current_book["chapters"].append(
            (current_chapter["num"], current_chapter["title"], current_chapter["sections"])
        )
        current_chapter = None

    def finalise_book():
        nonlocal current_book
        if current_book is None:
            return
        finalise_chapter()
        books.append((current_book["num"], current_book["title"], current_book["chapters"]))
        current_book = None

    # We need to handle the awkward fact that BOOK headers can span two lines
    # ("BOOK I. Containing The Interval...") and CHAPTER titles too. We
    # collapse consecutive non-blank header lines into one.
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue

        bm = BOOK_RE.match(line)
        if bm:
            # Collect trailing continuation lines (no blank in between).
            title = bm.group(2).strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() and not BOOK_RE.match(lines[j]) and not CHAPTER_RE.match(lines[j]) and not SECTION_RE.match(lines[j].lstrip()):
                title = (title + " " + lines[j].strip()).strip()
                j += 1
            finalise_book()
            current_book = {
                "num": roman_to_int(bm.group(1)),
                "title": title,
                "chapters": [],
            }
            i = j
            continue

        cm = CHAPTER_RE.match(line)
        if cm:
            title = cm.group(2).strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() and not BOOK_RE.match(lines[j]) and not CHAPTER_RE.match(lines[j]) and not SECTION_RE.match(lines[j].lstrip()):
                title = (title + " " + lines[j].strip()).strip()
                j += 1
            finalise_chapter()
            if current_book is None:
                # "PREFACE" chapters appear before any BOOK header in some editions;
                # create a synthetic book 0 for them. Shouldn't happen post-trim.
                current_book = {"num": 0, "title": "Preface", "chapters": []}
            current_chapter = {
                "num": int(cm.group(1)),
                "title": title,
                "sections": [],
                "_buf": [],
                "_sec": None,
            }
            i = j
            continue

        sm = SECTION_RE.match(line.lstrip())
        if sm and current_chapter is not None:
            # Flush previous section
            if current_chapter.get("_buf"):
                sec_num = current_chapter["_sec"]
                text = " ".join(current_chapter["_buf"]).strip()
                text = re.sub(r"\s+", " ", text)
                if text:
                    if sec_num is None:
                        current_chapter["sections"].append((None, text))
                    else:
                        current_chapter["sections"].append((sec_num, text))
            current_chapter["_buf"] = [line.lstrip()[len(sm.group(0)):].strip()]
            current_chapter["_sec"] = int(sm.group(1))
            i += 1
            continue

        # Accumulate into current section buffer
        if current_chapter is not None:
            current_chapter["_buf"].append(line.strip())

        i += 1

    finalise_book()

    # Books II-XX in Antiquities start with a per-book mini-TOC: a "BOOK N."
    # header followed by CHAPTER listings with little/no section content,
    # then "BOOK N." repeats for the real content. If a book number appears
    # more than once, keep the copy with the most sections.
    from collections import OrderedDict
    best = OrderedDict()
    for bnum, btitle, chapters in books:
        total_sec = sum(len(s) for _, _, s in chapters)
        if bnum not in best or total_sec > sum(len(s) for _, _, s in best[bnum][1]):
            best[bnum] = (btitle, chapters)
    return [(bnum, btitle, chapters) for bnum, (btitle, chapters) in best.items()]


def render_toc(works):
    rows = []
    for slug, display_name, books in works:
        rows.append(
            f'<li class="toc-section"><span class="toc-section-label">{esc(display_name)}</span></li>'
        )
        for bnum, btitle, _chapters in books:
            rows.append(
                f'<li><a href="#{slug}-b{bnum}"><span class="toc-num">{roman_of(bnum)}</span> '
                f'<span class="toc-name">Book {bnum}</span></a></li>'
            )
    return "\n".join(rows)


def render_work(slug, display_name, intro, books):
    blocks = []
    blocks.append(
        f'  <header class="reader-section-heading">\n'
        f'    <div class="reader-section-eyebrow">{esc(display_name)}</div>\n'
        f'    <h2>{esc(display_name)}</h2>\n'
        f'    <p>{esc(intro)}</p>\n'
        f'  </header>\n'
    )
    for bnum, btitle, chapters in books:
        blocks.append(
            f'  <article class="surah" id="{slug}-b{bnum}">\n'
            f'    <header class="surah-header">\n'
            f'      <div class="surah-num">{roman_of(bnum)}</div>\n'
            f'      <h2 class="surah-title">Book {bnum}</h2>\n'
            f'      <p class="surah-subtitle">{esc(btitle)}</p>\n'
            f'    </header>\n'
        )
        for cnum, ctitle, sections in chapters:
            blocks.append(
                f'    <section class="chapter" id="{slug}-b{bnum}-c{cnum}">\n'
                f'      <h3 class="chapter-title"><span class="chapter-num">Chapter {cnum}</span> <span class="chapter-head">{esc(ctitle)}</span></h3>\n'
                f'      <ol class="verses">\n'
            )
            for snum, stext in sections:
                if snum is None:
                    blocks.append(
                        f'        <li class="verse-unnumbered"><span class="verse-text">{esc(stext)}</span></li>\n'
                    )
                else:
                    blocks.append(
                        f'        <li id="{slug}-b{bnum}-c{cnum}-s{snum}" value="{snum}">'
                        f'<span class="verse-number">{snum}</span>'
                        f'<span class="verse-text">{esc(stext)}</span></li>\n'
                    )
            blocks.append('      </ol>\n    </section>\n')
        blocks.append('  </article>\n')
    return "".join(blocks)


def main():
    if not ANT_PATH.exists() or not WARS_PATH.exists():
        sys.exit(
            f"Missing sources — download first:\n"
            f'  curl -sL "https://www.gutenberg.org/cache/epub/2848/pg2848.txt" -o {ANT_PATH}\n'
            f'  curl -sL "https://www.gutenberg.org/cache/epub/2850/pg2850.txt" -o {WARS_PATH}\n'
        )

    ant_raw = ANT_PATH.read_text(encoding="utf-8")
    wars_raw = WARS_PATH.read_text(encoding="utf-8")

    ant_books = parse_josephus_text(ant_raw, "ant")
    wars_books = parse_josephus_text(wars_raw, "wars")

    # Summaries
    total_ant_sec = sum(len(secs) for _, _, chaps in ant_books for _, _, secs in chaps)
    total_wars_sec = sum(len(secs) for _, _, chaps in wars_books for _, _, secs in chaps)
    total_ant_chap = sum(len(chaps) for _, _, chaps in ant_books)
    total_wars_chap = sum(len(chaps) for _, _, chaps in wars_books)

    works = [
        ("ant", "Antiquities of the Jews", ant_books),
        ("wars", "The Wars of the Jews", wars_books),
    ]
    toc_html = render_toc(works)

    ant_intro = ("Josephus's twenty-book universal history of the Jews from the creation "
                 "through the outbreak of the revolt against Rome (AD 66). Includes the "
                 "disputed Testimonium Flavianum on Jesus (Book XVIII, Chapter 3) and the "
                 "reference to James the brother of Jesus (Book XX, Chapter 9) — first-century "
                 "external testimony relevant to Q 4:157.")
    wars_intro = ("Josephus's eyewitness account of the Jewish revolt against Rome and the "
                  "destruction of the Second Temple in AD 70. Seven books covering the causes "
                  "of the war, the siege of Jerusalem, and the fall of Masada.")

    body = render_work("ant", "Antiquities of the Jews", ant_intro, ant_books)
    body += render_work("wars", "The Wars of the Jews", wars_intro, wars_books)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read the complete works of Flavius Josephus — Antiquities of the Jews (20 books) and The Wars of the Jews (7 books) — in William Whiston's 1737 English translation. Public domain.">
<title>Flavius Josephus — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<link rel="stylesheet" href="../assets/css/reader.css">
<style>
  .reader-toc li.toc-section {{
    list-style: none;
    margin-left: -12px;
    margin-top: 18px;
    margin-bottom: 6px;
  }}
  .reader-toc li.toc-section .toc-section-label {{
    font-family: var(--sans);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    color: var(--text-dim);
    font-weight: 600;
    display: block;
    padding-top: 10px;
    border-top: 1px solid var(--border);
  }}
  .reader-section-heading {{
    margin: 72px 0 24px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }}
  .reader-section-heading .reader-section-eyebrow {{
    font-family: var(--sans);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.28em;
    color: var(--text-dim);
    font-weight: 600;
    margin-bottom: 10px;
  }}
  .reader-section-heading h2 {{
    font-family: var(--serif);
    font-size: clamp(32px, 4.5vw, 56px);
    line-height: 1.05;
    margin: 0 0 10px;
    letter-spacing: -0.02em;
  }}
  .reader-section-heading p {{
    color: var(--text-muted);
    margin: 0;
    max-width: 70ch;
  }}
  .surah-subtitle {{
    font-family: var(--sans);
    font-size: 13px;
    color: var(--text-muted);
    margin: 6px 0 0;
    max-width: 70ch;
    font-style: italic;
  }}
  .chapter {{
    margin: 48px 0;
    padding-top: 12px;
  }}
  .chapter-title {{
    font-family: var(--serif);
    font-size: clamp(20px, 2.2vw, 28px);
    line-height: 1.25;
    margin: 0 0 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }}
  .chapter-num {{
    display: block;
    font-family: var(--sans);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    font-weight: 600;
    margin-bottom: 4px;
  }}
  .chapter-head {{
    display: block;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.015em;
  }}
  .verse-unnumbered .verse-text {{
    color: var(--text-muted);
    font-style: italic;
  }}
</style>
</head>
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Analyzing Islam</a>
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
{toc_html}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">William Whiston · 1737 English translation · Public domain</div>
      <h1>Flavius Josephus</h1>
      <p class="reader-intro">First-century Jewish historian. His <em>Antiquities of the Jews</em> ({total_ant_chap} chapters across 20 books) and <em>The Wars of the Jews</em> ({total_wars_chap} chapters across 7 books) are the single most important contemporary source on Second Temple Judaism and the Roman destruction of Jerusalem in AD 70 — and independent external testimony relevant to Q 4:157's denial of the crucifixion.</p>
      <div class="reader-cta">
        <a href="../read-external.html" class="btn">← External sources</a>
        <a href="https://www.gutenberg.org/ebooks/2848" class="btn" target="_blank" rel="noopener">Antiquities · Gutenberg</a>
        <a href="https://www.gutenberg.org/ebooks/2850" class="btn" target="_blank" rel="noopener">Wars · Gutenberg</a>
      </div>
    </header>

{body}
  </main>

</div>

<footer class="site-footer">
  Whiston's 1737 English translation of Josephus. Public domain. Sourced from Project Gutenberg eBooks #2848 and #2850. Anchors: #ant-b{{book}}-c{{chap}}-s{{section}} and #wars-b{{book}}-c{{chap}}-s{{section}}.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT_PATH}:")
    print(f"  Antiquities: {len(ant_books)} books, {total_ant_chap} chapters, {total_ant_sec} sections")
    print(f"  Wars:        {len(wars_books)} books, {total_wars_chap} chapters, {total_wars_sec} sections")


if __name__ == "__main__":
    main()
