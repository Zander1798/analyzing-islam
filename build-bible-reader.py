#!/usr/bin/env python3
"""Generate site/read-external/bible.html (index) and
site/read-external/bible/<slug>.html (per-book readers) from the JSON
produced by build-bible-data.py. Also copies the shared JSON files into
site/read-external/bible/data/ for client-side loading.
"""
import html
import json
import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SRC = ROOT / ".tmp" / "bible-data"
OUT_DIR = ROOT / "site" / "read-external" / "bible"
OUT_DATA = OUT_DIR / "data"
OUT_INDEX = ROOT / "site" / "read-external" / "bible.html"


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def morph_en_to_attr(parts: list[str]) -> str:
    # Join with "|" so JS can split cleanly; escape HTML for attr
    return "|".join(parts)


def render_word(word: dict) -> str:
    s = ",".join(word.get("strongs", []))
    morph = word.get("morph", "")
    morph_en = morph_en_to_attr(word.get("morph_en", []))
    orig = word.get("orig", "")
    trans = word.get("trans", "")
    gloss = word.get("gloss", "")
    return (
        '<span class="w" '
        'data-s="' + esc(s) + '" '
        'data-m="' + esc(morph) + '" '
        'data-me="' + esc(morph_en) + '">'
        '<span class="w-orig">' + esc(orig) + '</span>'
        '<span class="w-trans">' + esc(trans) + '</span>'
        '<span class="w-gloss">' + esc(gloss) + '</span>'
        '</span>'
    )


def render_verse(slug: str, ch: int, vs_data: dict) -> str:
    vs = vs_data["n"]
    words_html = "".join(render_word(w) for w in vs_data["w"])
    return (
        '<li class="bible-verse" id="' + slug + '-' + str(ch) + '-' + str(vs) + '" '
        'data-v="' + str(vs) + '">'
        '<span class="verse-num">' + str(vs) + '</span>'
        '<span class="ilt-words">' + words_html + '</span>'
        '</li>'
    )


def render_chapter(slug: str, ch_data: dict) -> str:
    ch = ch_data["n"]
    verses = "".join(render_verse(slug, ch, v) for v in ch_data["v"])
    return (
        '<article class="bible-chapter" id="' + slug + '-' + str(ch) + '" '
        'data-c="' + str(ch) + '">'
        '<h2>Chapter ' + str(ch) + '</h2>'
        '<ol class="bible-verses">' + verses + '</ol>'
        '</article>'
    )


BOOK_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{name} — interlinear {lang_name} with Strong's numbers, morphology, and in-line English glosses. Click any word for its Strong's entry and concordance.">
<title>{name} — Interlinear Bible — Analyzing Islam</title>
<link rel="stylesheet" href="../../assets/css/style.css">
<link rel="stylesheet" href="../../assets/css/bible-reader.css">
</head>
<body class="bible-lang-{lang}" data-book-slug="{slug}" data-data-base="data/" data-books-base="" data-book-names='{book_names}'>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
      <a href="../../index.html">Home</a>
      <a href="../../catalog.html">Catalog</a>
      <a href="../../read.html" class="active">Read</a>
      <a href="../../about.html">About</a>
      <a href="../../faq.html">FAQ</a>
    </div>
  </div>
</nav>

<div class="bible-layout">

  <aside class="bible-toc">
    <div class="bible-toc-header">Chapters</div>
    <ol>
{toc}
    </ol>
  </aside>

  <main class="bible-main">
    <header class="bible-hero">
      <div class="bible-meta">{lang_name} · Interlinear · Strong's + Morphology</div>
      <h1>{name}</h1>
      <p>{intro}</p>
      <div class="bible-hero-actions">
        <a href="../bible.html" class="btn">← All books</a>
      </div>
    </header>

{body}
  </main>

</div>

<footer class="site-footer">
  Interlinear Bible reader. Hebrew OT and Greek NT word-by-word, with Strong's numbers, parsed morphology, and concordance. Data from STEPBible TAHOT/TAGNT (CC-BY) and the OpenScriptures Strong's dictionaries (CC-BY-SA, public-domain source 1890/1894).
</footer>

<script src="../../assets/js/bible-reader.js" defer></script>
<script src="../../assets/js/goat.js" defer></script>
</body>
</html>
"""


def build_book_page(slug: str, book: dict, all_book_names: dict) -> str:
    lang = book["lang"]
    lang_name = "Hebrew" if lang == "heb" else "Greek"
    name = book["name"]
    total_chapters = len(book["chapters"])
    total_verses = sum(len(c["v"]) for c in book["chapters"])
    total_words = sum(len(v["w"]) for c in book["chapters"] for v in c["v"])
    intro = (
        f"The full book of {name} in {lang_name}, word-by-word, with English glosses underneath "
        f"each original-language token. Click any word to see its Strong's entry, parsed morphology, "
        f"and every other place in the Bible where that Strong's number appears. "
        f"{total_chapters} chapters · {total_verses:,} verses · {total_words:,} original-language words."
    )

    toc_rows = "\n".join(
        f'      <li><a href="#{slug}-{c["n"]}">Chapter {c["n"]}</a></li>'
        for c in book["chapters"]
    )
    body = "\n".join(render_chapter(slug, c) for c in book["chapters"])

    book_names_json = json.dumps(all_book_names, ensure_ascii=False)
    # Escape single-quote to avoid closing data-attr
    book_names_attr = book_names_json.replace("'", "&#39;")

    return BOOK_TEMPLATE.format(
        name=esc(name),
        slug=slug,
        lang=lang,
        lang_name=lang_name,
        intro=esc(intro),
        toc=toc_rows,
        body=body,
        book_names=book_names_attr,
    )


INDEX_CARD = """<a href="bible/{slug}.html" class="book-card">
  <div>
    <h3>{name}</h3>
    <p class="book-sub">{lang_name} · {section_clean}</p>
    <p>{chapters} ch · {verses} v · {words} w</p>
  </div>
  <div class="book-meta">Open interlinear ›</div>
</a>"""

SECTIONS_ORDER = [
    ("OT-Torah", "Torah · Pentateuch"),
    ("OT-History", "OT Historical Books"),
    ("OT-Wisdom", "OT Wisdom & Poetry"),
    ("OT-Major-Prophets", "Major Prophets"),
    ("OT-Minor-Prophets", "Minor Prophets"),
    ("NT-Gospels", "Gospels"),
    ("NT-History", "NT History (Acts)"),
    ("NT-Pauline", "Pauline Epistles"),
    ("NT-General", "General Epistles & Hebrews"),
    ("NT-Apocalypse", "Apocalypse"),
]


def build_index(books_data: dict) -> str:
    total_verses = sum(
        sum(len(c["v"]) for c in b["chapters"]) for b in books_data.values()
    )
    total_words = sum(
        sum(len(v["w"]) for c in b["chapters"] for v in c["v"])
        for b in books_data.values()
    )

    sections_html = []
    for key, label in SECTIONS_ORDER:
        books = [b for b in books_data.values() if b["section"] == key]
        if not books:
            continue
        cards = []
        for b in books:
            chs = len(b["chapters"])
            vs = sum(len(c["v"]) for c in b["chapters"])
            ws = sum(len(v["w"]) for c in b["chapters"] for v in c["v"])
            cards.append(INDEX_CARD.format(
                slug=b["slug"],
                name=esc(b["name"]),
                lang_name="Hebrew" if b["lang"] == "heb" else "Greek",
                section_clean=label,
                chapters=chs, verses=f"{vs:,}", words=f"{ws:,}",
            ))
        sections_html.append(
            f'<div class="book-group">'
            f'<span class="book-group-label">{esc(label)}</span>'
            f'<div class="book-grid">' + "\n".join(cards) + '</div>'
            f'</div>'
        )
    return INDEX_TEMPLATE.format(
        sections="\n".join(sections_html),
        total_books=len(books_data),
        total_verses=f"{total_verses:,}",
        total_words=f"{total_words:,}",
    )


INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Interlinear Bible — full Hebrew OT and Greek NT with Strong's numbers, morphology, and English glosses. Click any word for its lexicon entry and concordance.">
<title>Interlinear Bible — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<style>
  .book-group {{ margin: 48px 0 8px; }}
  .book-group-label {{
    font-family: var(--sans);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.28em;
    color: var(--text-dim);
    font-weight: 600;
    padding: 0 0 12px;
    display: block;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
  }}
  .book-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 14px;
    margin-bottom: 32px;
  }}
  .book-card {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 20px;
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text);
    text-decoration: none;
    min-height: 130px;
    transition: border-color 0.2s, transform 0.2s;
  }}
  .book-card:hover {{
    border-color: var(--accent);
    text-decoration: none;
    transform: translateY(-2px);
  }}
  .book-card h3 {{
    font-family: var(--serif);
    font-size: 22px;
    margin: 0 0 6px;
    letter-spacing: -0.015em;
  }}
  .book-card .book-sub {{
    font-family: var(--sans);
    font-size: 11px;
    color: var(--text-muted);
    font-style: italic;
    margin: 0 0 8px;
  }}
  .book-card p {{
    font-size: 13px;
    color: var(--text-muted);
    margin: 0 0 10px;
  }}
  .book-card .book-meta {{
    font-family: var(--sans);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    font-weight: 600;
    margin-top: auto;
  }}
  .back-link {{
    display: inline-block;
    font-family: var(--sans);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-decoration: none;
    margin-top: 24px;
    margin-bottom: 8px;
  }}
  .back-link:hover {{ color: var(--accent); text-decoration: none; }}
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

<main>

  <section class="hero" style="padding: 40px 0 8px; text-align:left;">
    <a href="../read.html" class="back-link">← Read</a>
    <h1 style="font-size:clamp(48px, 7vw, 88px); margin-bottom:20px;">Interlinear Bible</h1>
    <p class="hero-tagline" style="margin-left:0; max-width:760px;">The full {total_books}-book Protestant canon — Hebrew Old Testament and Greek New Testament — word-by-word, with Strong's numbers, parsed morphology, and a cross-book concordance index. Click any original-language token to open its Strong's entry and every other verse where the same word appears. {total_verses} verses · {total_words} original-language tokens.</p>
  </section>

  <section style="padding:20px; background:var(--panel); border:1px solid var(--border); border-left:3px solid var(--accent); margin-top: 24px; max-width: 72ch;">
    <h3 style="margin-top:0; font-size: 15px;">About this interlinear</h3>
    <p style="color:var(--text-muted); font-size:13px; line-height: 1.6; margin: 0;">Underlying data from <a href="https://github.com/STEPBible/STEPBible-Data" target="_blank" rel="noopener">STEPBible TAHOT/TAGNT</a> (CC-BY) for Hebrew and Greek text, transliteration, word-by-word gloss, Strong's disambiguation, and morphology. Strong's dictionary entries from the <a href="https://github.com/openscriptures/strongs" target="_blank" rel="noopener">OpenScriptures Strong's</a> project (CC-BY-SA, original Strong's 1890/1894 public domain). The word-by-word English glosses are adapted from the Berean Study Bible (permission) via STEPBible and are designed to be literal, not a readable prose translation — they sit under each original word to show its sense in context.</p>
  </section>

{sections}

</main>

<footer class="site-footer">
  Interlinear Bible reader. Hebrew OT and Greek NT word-by-word, with Strong's numbers, parsed morphology, and cross-book concordance.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def main():
    if not SRC.exists():
        sys.exit(f"Missing data dir: {SRC}. Run build-bible-data.py first.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DATA.mkdir(parents=True, exist_ok=True)

    # Copy shared JSON (strongs + concordance) to site data dir
    print("Copying shared JSON to site…")
    for name in ("strongs-hebrew.json", "strongs-greek.json", "concordance.json"):
        src = SRC / name
        if src.exists():
            shutil.copy2(src, OUT_DATA / name)
            print(f"  {name}: {src.stat().st_size / 1024:.0f} KB")

    # Load manifest to iterate books in a stable order.
    manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
    all_book_names = {m["slug"]: m["name"] for m in manifest["books"]}

    # Build each book
    books_data = {}
    for m in manifest["books"]:
        slug = m["slug"]
        book = json.loads((SRC / "books" / f"{slug}.json").read_text(encoding="utf-8"))
        books_data[slug] = book

    print(f"Generating {len(books_data)} per-book HTML files…")
    for slug, book in books_data.items():
        html_text = build_book_page(slug, book, all_book_names)
        out = OUT_DIR / f"{slug}.html"
        out.write_text(html_text, encoding="utf-8")

    # Build index
    print("Generating bible.html index…")
    idx = build_index(books_data)
    OUT_INDEX.write_text(idx, encoding="utf-8")

    # Size summary
    total = sum(
        (OUT_DIR / f"{slug}.html").stat().st_size for slug in books_data
    )
    print(f"\nWrote {len(books_data)} book pages, total {total / 1024 / 1024:.1f} MB")
    print(f"Index: {OUT_INDEX}")


if __name__ == "__main__":
    main()
