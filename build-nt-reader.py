#!/usr/bin/env python3
"""Build site/read-external/new-testament.html from the World English
Bible (WEB) JSON at TehShrike/world-english-bible on GitHub.

The WEB is a modern public-domain English translation. All 27 books
of the New Testament are rendered here with per-verse anchors.
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
JSON_DIR = ROOT / ".tmp" / "web-bible" / "world-english-bible-master" / "json"
OUT_PATH = ROOT / "site" / "read-external" / "new-testament.html"

# 27 NT books in canonical order with (file-slug, display title, subtitle, section).
NT_BOOKS = [
    ("matthew",        "Matthew",        "Gospel",           "Gospels"),
    ("mark",           "Mark",           "Gospel",           "Gospels"),
    ("luke",           "Luke",           "Gospel",           "Gospels"),
    ("john",           "John",           "Gospel",           "Gospels"),
    ("acts",           "Acts",           "Acts of the Apostles", "Acts"),
    ("romans",         "Romans",         "Epistle",          "Pauline Epistles"),
    ("1corinthians",   "1 Corinthians",  "Epistle",          "Pauline Epistles"),
    ("2corinthians",   "2 Corinthians",  "Epistle",          "Pauline Epistles"),
    ("galatians",      "Galatians",      "Epistle",          "Pauline Epistles"),
    ("ephesians",      "Ephesians",      "Epistle",          "Pauline Epistles"),
    ("philippians",    "Philippians",    "Epistle",          "Pauline Epistles"),
    ("colossians",     "Colossians",     "Epistle",          "Pauline Epistles"),
    ("1thessalonians", "1 Thessalonians","Epistle",          "Pauline Epistles"),
    ("2thessalonians", "2 Thessalonians","Epistle",          "Pauline Epistles"),
    ("1timothy",       "1 Timothy",      "Pastoral epistle", "Pauline Epistles"),
    ("2timothy",       "2 Timothy",      "Pastoral epistle", "Pauline Epistles"),
    ("titus",          "Titus",          "Pastoral epistle", "Pauline Epistles"),
    ("philemon",       "Philemon",       "Epistle",          "Pauline Epistles"),
    ("hebrews",        "Hebrews",        "Epistle",          "Hebrews"),
    ("james",          "James",          "General epistle",  "General Epistles"),
    ("1peter",         "1 Peter",        "General epistle",  "General Epistles"),
    ("2peter",         "2 Peter",        "General epistle",  "General Epistles"),
    ("1john",          "1 John",         "General epistle",  "General Epistles"),
    ("2john",          "2 John",         "General epistle",  "General Epistles"),
    ("3john",          "3 John",         "General epistle",  "General Epistles"),
    ("jude",           "Jude",           "General epistle",  "General Epistles"),
    ("revelation",     "Revelation",     "Apocalypse",       "Revelation"),
]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def load_book(slug: str):
    """Load a WEB JSON book and return [(chap, verse, text), ...]."""
    p = JSON_DIR / f"{slug}.json"
    if not p.exists():
        sys.exit(f"Missing JSON: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    verses = {}  # (chap, verse) -> accumulated text
    for item in data:
        t = item.get("type")
        if t not in ("paragraph text", "line text"):
            continue
        chap = item.get("chapterNumber")
        verse = item.get("verseNumber")
        val = item.get("value", "")
        if chap is None or verse is None:
            continue
        verses.setdefault((chap, verse), []).append(val)
    out = []
    for (chap, verse), pieces in sorted(verses.items()):
        text = " ".join(pieces)
        text = " ".join(text.split())  # normalise whitespace
        out.append((chap, verse, text))
    return out


def main():
    if not JSON_DIR.exists():
        sys.exit(f"Missing WEB JSON dir: {JSON_DIR}")

    toc_rows = []
    body_blocks = []
    total_verses = 0
    current_section = None

    for idx, (slug, title, subtitle, section) in enumerate(NT_BOOKS, start=1):
        verses = load_book(slug)

        # Group verses by chapter
        chapters = {}
        for chap, verse, text in verses:
            chapters.setdefault(chap, []).append((verse, text))

        if section != current_section:
            toc_rows.append(
                f'<li class="toc-section"><span class="toc-section-label">{esc(section)}</span></li>'
            )
            body_blocks.append(
                f'  <header class="reader-section-heading">\n'
                f'    <div class="reader-section-eyebrow">Section</div>\n'
                f'    <h2>{esc(section)}</h2>\n'
                f'  </header>\n'
            )
            current_section = section

        toc_rows.append(
            f'<li><a href="#{slug}"><span class="toc-num">{idx}</span> '
            f'<span class="toc-name">{esc(title)}</span></a></li>'
        )

        body_blocks.append(
            f'  <article class="surah" id="{slug}">\n'
            f'    <header class="surah-header">\n'
            f'      <div class="surah-num">{idx}</div>\n'
            f'      <h2 class="surah-title">{esc(title)}</h2>\n'
            f'      <p class="surah-subtitle">{esc(subtitle)}</p>\n'
            f'    </header>\n'
        )
        for chap_num in sorted(chapters.keys()):
            body_blocks.append(
                f'    <section class="chapter" id="{slug}-{chap_num}">\n'
                f'      <h3 class="chapter-title">'
                f'<span class="chapter-num">Chapter {chap_num}</span></h3>\n'
                f'      <ol class="verses">\n'
            )
            for verse, text in chapters[chap_num]:
                total_verses += 1
                body_blocks.append(
                    f'        <li id="{slug}-{chap_num}-{verse}" value="{verse}">'
                    f'<span class="verse-number">{verse}</span>'
                    f'<span class="verse-text">{esc(text)}</span></li>\n'
                )
            body_blocks.append('      </ol>\n    </section>\n')
        body_blocks.append('  </article>\n')

    toc_html = "\n".join(toc_rows)
    body_html = "".join(body_blocks)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read the complete New Testament in the World English Bible (WEB) translation — all 27 books, verse by verse. Public domain.">
<title>The New Testament — Analyzing Islam</title>
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
  .reader-section-heading h2 {{
    font-family: var(--serif);
    font-size: clamp(32px, 4.5vw, 56px);
    letter-spacing: -0.02em;
    margin: 0;
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
  .surah-subtitle {{
    font-family: var(--sans);
    font-size: 13px;
    color: var(--text-muted);
    margin: 6px 0 0;
    font-style: italic;
  }}
  .chapter {{
    margin: 40px 0;
  }}
  .chapter-title {{
    font-family: var(--serif);
    font-size: clamp(20px, 2.2vw, 28px);
    line-height: 1.25;
    margin: 0 0 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }}
  .chapter-num {{
    font-family: var(--sans);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    font-weight: 600;
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
      <div class="reader-meta">World English Bible · Public domain modern translation</div>
      <h1>The New Testament</h1>
      <p class="reader-intro">All 27 books of the New Testament in the World English Bible (WEB) — a modern, plain-English translation based on the 1901 American Standard Version and released into the public domain. {total_verses} verses across Gospels, Acts, Pauline and General Epistles, and Revelation.</p>
      <div class="reader-cta">
        <a href="../read-external.html" class="btn">← External sources</a>
        <a href="https://github.com/TehShrike/world-english-bible" class="btn" target="_blank" rel="noopener">Source · GitHub</a>
        <a href="https://ebible.org/web/" class="btn" target="_blank" rel="noopener">WEB · ebible.org</a>
      </div>
    </header>

{body_html}
  </main>

</div>

<footer class="site-footer">
  World English Bible. Public domain. Sourced from TehShrike/world-english-bible. Anchors: #{{book-slug}}-{{chapter}}-{{verse}}.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT_PATH}: {total_verses} verses across {len(NT_BOOKS)} books")


if __name__ == "__main__":
    main()
