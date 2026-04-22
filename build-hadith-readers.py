#!/usr/bin/env python3
"""Build HTML readers for Abu Dawud, Tirmidhi, Nasai, and Ibn Majah from the
AhmedBaset/hadith-json dataset (scraped from sunnah.com).

Source JSON schema (per collection file in hadith-json/):
  {
    "id": <bookId>,
    "metadata": { ... },
    "chapters": [ {id, bookId, arabic, english}, ... ],
    "hadiths":  [ {id, idInBook, chapterId, bookId, arabic, english:{narrator,text}}, ... ]
  }

`idInBook` is the canonical continuous hadith number used in scholarly
citations (e.g., "Nasai 5397" -> idInBook=5397). The reader uses per-hadith
anchors of the form #h{idInBook} so inbound links land on the exact hadith.

Output: site/read/{abu-dawud,tirmidhi,nasai,ibn-majah}.html — markup/classes
match the existing Bukhari/Muslim readers so the CSS in reader.css styles
them identically.
"""
import html
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
JSON_DIR = ROOT / "hadith-json"
OUT_DIR = ROOT / "site" / "read"

# Per-source configuration.
# - json_name: filename under hadith-json/
# - slug:      output HTML filename (without .html)
# - pdf:       optional download PDF path (relative to site/read/ the same way
#              the existing readers reference theirs); None to skip
# - title:     h1 (may include diacritics / Arabic transliteration)
# - meta:      small line above h1, e.g. "English translation by ..."
# - intro:     one-paragraph description under the h1
# - ref_prefix: display prefix used in each hadith's little "ref" strip, e.g. "Hadith"
SOURCES = [
    {
        "json_name": "abudawud.json",
        "slug": "abu-dawud",
        "pdf": "../assets/sources/abu-dawud.pdf",
        "title": "Sunan Abī Dāwūd",
        "meta": "Sunan Abi Dawud · English translation from sunnah.com",
        "intro": "Compiled by Abū Dāwūd al-Sijistānī (d. 889 CE). Focused on reports with legal implications — about 5,270 hadiths. One of the six canonical Sunni collections.",
        "ref_prefix": "Hadith",
    },
    {
        "json_name": "tirmidhi.json",
        "slug": "tirmidhi",
        "pdf": "../assets/sources/tirmidhi.pdf",
        "title": "Jāmiʿ at-Tirmidhī",
        "meta": "Jami` at-Tirmidhi · English translation from sunnah.com",
        "intro": "Compiled by Abū ʿĪsā al-Tirmidhī (d. 892 CE). About 4,050 hadiths, organized topically with grading notes — hasan, sahih, gharib — for most narrations.",
        "ref_prefix": "Hadith",
    },
    {
        "json_name": "nasai.json",
        "slug": "nasai",
        "pdf": None,  # split vol PDFs only; skip single-PDF download
        "title": "Sunan an-Nasāʾī",
        "meta": "Sunan an-Nasa'i · English translation from sunnah.com",
        "intro": "Compiled by Aḥmad ibn Shuʿayb al-Nasāʾī (d. 915 CE). Known for strict isnād standards — about 5,760 hadiths. One of the six canonical Sunni collections.",
        "ref_prefix": "Hadith",
    },
    {
        "json_name": "ibnmajah.json",
        "slug": "ibn-majah",
        "pdf": None,
        "title": "Sunan Ibn Mājah",
        "meta": "Sunan Ibn Majah · English translation from sunnah.com",
        "intro": "Compiled by Muḥammad ibn Yazīd ibn Mājah (d. 887 CE). About 4,340 hadiths. The last-admitted of the six canonical Sunni collections.",
        "ref_prefix": "Hadith",
    },
]


def esc(s: str) -> str:
    """HTML-escape, keeping characters safe for attribute and text contexts."""
    return html.escape(s, quote=True) if s else ""


def render_hadith(h: dict, ref_prefix: str) -> str:
    """Render a single hadith article block."""
    hid = h["idInBook"]
    chapter_id = h["chapterId"]
    eng = h.get("english") or {}
    narrator = (eng.get("narrator") or "").strip()
    text = (eng.get("text") or "").strip()
    arabic = (h.get("arabic") or "").strip()

    parts = [
        f'    <article class="hadith" id="h{hid}">',
        '      <header class="hadith-header">',
        f'        <span class="hadith-ref">{esc(ref_prefix)} {hid} · Book {chapter_id}</span>',
        '      </header>',
        '      <div class="hadith-body">',
    ]
    if narrator:
        parts.append(f'        <div class="hadith-narrator">{esc(narrator)}</div>')
    # Split text into paragraphs on blank lines; otherwise one paragraph.
    if text:
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        if not blocks:
            blocks = [text]
        for b in blocks:
            # Preserve internal single-line breaks as spaces (source rarely has them).
            b_clean = " ".join(b.split())
            parts.append(f'        <p>{esc(b_clean)}</p>')
    if arabic:
        parts.append(f'        <p class="hadith-arabic" lang="ar" dir="rtl">{esc(arabic)}</p>')
    parts += ["      </div>", "    </article>"]
    return "\n".join(parts)


def render_book(chapter: dict, hadiths: list, ref_prefix: str) -> str:
    """Render a full book section with its hadiths."""
    cid = chapter["id"]
    title = (chapter.get("english") or "").strip() or f"Book {cid}"
    n = len(hadiths)
    lines = [
        f'<section class="hadith-book" id="book-{cid}">',
        '  <header class="hadith-book-header">',
        f'    <div class="hadith-book-number">Book {cid}</div>',
        f'    <h2>{esc(title)}</h2>',
        f'    <div class="hadith-book-subtitle">{n} hadith{"s" if n != 1 else ""}</div>',
        '  </header>',
        '  <div class="hadith-book-body">',
    ]
    for h in hadiths:
        lines.append(render_hadith(h, ref_prefix))
    lines += ["  </div>", "</section>", ""]
    return "\n".join(lines)


def render_toc_items(chapters_with_counts: list) -> str:
    """Sidebar <li> entries for each book."""
    out = []
    for ch, count in chapters_with_counts:
        out.append(
            f'<li><a href="#book-{ch["id"]}">'
            f'<span class="toc-num">{ch["id"]}</span> '
            f'<span class="toc-name">{esc((ch.get("english") or "").strip() or "Book")}</span>'
            f'</a></li>'
        )
    return "\n".join(out)


def render_page(src: dict, total_hadiths: int, total_books: int,
                toc_items_html: str, books_html: str) -> str:
    pdf_btn = (
        f'\n        <a href="{esc(src["pdf"])}" class="btn" download>Download PDF</a>'
        if src["pdf"] else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read {esc(src["title"])} in English — {total_hadiths} hadiths across {total_books} books, sourced from sunnah.com.">
<title>Read {esc(src["title"])} — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<link rel="stylesheet" href="../assets/css/reader.css">
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
{toc_items_html}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">{esc(src["meta"])}</div>
      <h1>{esc(src["title"])}</h1>
      <p class="reader-intro">{esc(src["intro"])}</p>
      <div class="reader-cta">
        <a href="../read.html" class="btn">← All sources</a>{pdf_btn}
      </div>
    </header>

{books_html}
  </main>

</div>

<footer class="site-footer">
  English text from sunnah.com via AhmedBaset/hadith-json v1.2.0. Every entry references a specific hadith by its canonical number — verify before citing.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def build_one(src: dict) -> None:
    json_path = JSON_DIR / src["json_name"]
    data = json.loads(json_path.read_text(encoding="utf-8"))
    chapters = data["chapters"]
    hadiths = data["hadiths"]

    # Nasai's upstream has one chapter with id=null ("The Book of Agriculture")
    # and 83 hadiths that reference it as chapterId=null. Assign a synthetic
    # id that sorts after the rest so the book appears at the end.
    max_id = max((c["id"] for c in chapters if c.get("id") is not None), default=0)
    synthetic_id = max_id + 1
    for c in chapters:
        if c.get("id") is None:
            c["id"] = synthetic_id
    for h in hadiths:
        if h.get("chapterId") is None:
            h["chapterId"] = synthetic_id

    # Group hadiths by chapterId, preserving source order (which is idInBook order).
    by_chapter: dict[int, list] = {}
    for h in hadiths:
        by_chapter.setdefault(h["chapterId"], []).append(h)

    # Order chapters by id.
    chapters_sorted = sorted(chapters, key=lambda c: c["id"])

    # Build TOC (all chapters, even empty ones — they should all have hadiths).
    toc_rows = [(c, len(by_chapter.get(c["id"], []))) for c in chapters_sorted]
    toc_items_html = render_toc_items(toc_rows)

    # Render each book section.
    book_blocks = []
    total_hadiths = 0
    for c in chapters_sorted:
        hs = by_chapter.get(c["id"], [])
        if not hs:
            # Skip books with no hadiths (defensive — shouldn't happen).
            continue
        # Sort within chapter by idInBook so the ordering matches citations.
        hs.sort(key=lambda x: x["idInBook"])
        book_blocks.append(render_book(c, hs, src["ref_prefix"]))
        total_hadiths += len(hs)

    html_out = render_page(
        src=src,
        total_hadiths=total_hadiths,
        total_books=len(chapters_sorted),
        toc_items_html=toc_items_html,
        books_html="\n".join(book_blocks),
    )

    out_path = OUT_DIR / f"{src['slug']}.html"
    out_path.write_text(html_out, encoding="utf-8")
    print(f"  Wrote {out_path.name}: {total_hadiths} hadiths in {len(chapters_sorted)} books")


def main() -> None:
    if not JSON_DIR.exists():
        sys.exit(f"Missing source dir: {JSON_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src in SOURCES:
        build_one(src)
    print(f"\nDone. Wrote {len(SOURCES)} reader pages under {OUT_DIR}.")


if __name__ == "__main__":
    main()
