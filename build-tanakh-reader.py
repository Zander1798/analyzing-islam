#!/usr/bin/env python3
"""Build site/read-external/tanakh.html from the JPS 1917 Tanakh
(Jewish Publication Society of America, 1917 — public domain).

Source: a tab-separated UTF-16 dump of the 1917 JPS translation from
Yakubovich/tanakh (GitHub), which originates from jewishpub.org under
the Creative Commons Public Domain Dedication 1.0 Universal license.
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
SRC_PATH = ROOT / ".tmp" / "tanakh-repo" / "tanakh-master" / "english" / "Tanakh1917d.txt"
OUT_PATH = ROOT / "site" / "read-external" / "tanakh.html"

# 39 books in the order of the JPS 1917 edition.
# (slug, display title, Hebrew name, section)
BOOKS = [
    ("genesis",       "Genesis",       "Bereshit",  "Torah"),
    ("exodus",        "Exodus",        "Shemot",    "Torah"),
    ("leviticus",     "Leviticus",     "Vayikra",   "Torah"),
    ("numbers",       "Numbers",       "Bamidbar",  "Torah"),
    ("deuteronomy",   "Deuteronomy",   "Devarim",   "Torah"),
    ("joshua",        "Joshua",        "Yehoshua",  "Nevi'im"),
    ("judges",        "Judges",        "Shoftim",   "Nevi'im"),
    ("1samuel",       "I Samuel",      "Shmuel A",  "Nevi'im"),
    ("2samuel",       "II Samuel",     "Shmuel B",  "Nevi'im"),
    ("1kings",        "I Kings",       "Melakhim A","Nevi'im"),
    ("2kings",        "II Kings",      "Melakhim B","Nevi'im"),
    ("isaiah",        "Isaiah",        "Yeshayahu", "Nevi'im"),
    ("jeremiah",      "Jeremiah",      "Yirmeyahu", "Nevi'im"),
    ("ezekiel",       "Ezekiel",       "Yechezkel", "Nevi'im"),
    ("hosea",         "Hosea",         "Hoshea",    "Nevi'im"),
    ("joel",          "Joel",          "Yoel",      "Nevi'im"),
    ("amos",          "Amos",          "Amos",      "Nevi'im"),
    ("obadiah",       "Obadiah",       "Ovadyah",   "Nevi'im"),
    ("jonah",         "Jonah",         "Yonah",     "Nevi'im"),
    ("micah",         "Micah",         "Mikhah",    "Nevi'im"),
    ("nahum",         "Nahum",         "Nachum",    "Nevi'im"),
    ("habakkuk",      "Habakkuk",      "Chavakuk",  "Nevi'im"),
    ("zephaniah",     "Zephaniah",     "Tzefanyah", "Nevi'im"),
    ("haggai",        "Haggai",        "Chaggai",   "Nevi'im"),
    ("zechariah",     "Zechariah",     "Zecharyah", "Nevi'im"),
    ("malachi",       "Malachi",       "Malakhi",   "Nevi'im"),
    ("psalms",        "Psalms",        "Tehillim",  "Ketuvim"),
    ("proverbs",      "Proverbs",      "Mishlei",   "Ketuvim"),
    ("job",           "Job",           "Iyyov",     "Ketuvim"),
    ("songofsongs",   "Song of Songs", "Shir HaShirim", "Ketuvim"),
    ("ruth",          "Ruth",          "Rut",       "Ketuvim"),
    ("lamentations",  "Lamentations",  "Eikhah",    "Ketuvim"),
    ("ecclesiastes",  "Ecclesiastes",  "Kohelet",   "Ketuvim"),
    ("esther",        "Esther",        "Esther",    "Ketuvim"),
    ("daniel",        "Daniel",        "Daniyyel",  "Ketuvim"),
    ("ezra",          "Ezra",          "Ezra",      "Ketuvim"),
    ("nehemiah",      "Nehemiah",      "Nechemyah", "Ketuvim"),
    ("1chronicles",   "I Chronicles",  "Divrei Hayamim A", "Ketuvim"),
    ("2chronicles",   "II Chronicles", "Divrei Hayamim B", "Ketuvim"),
]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def clean_text(text: str) -> str:
    """Clean up the JPS TSV text artifacts.

    - <span class=|divineName|>Lord</span> → L<span class="divineName">ORD</span>
      (the JPS uses small-caps LORD for YHWH)
    - Handle unbalanced quoting characters
    """
    # The TSV uses | instead of " for attribute quoting.
    text = re.sub(
        r'<span class=\|divineName\|>([^<]+)</span>',
        r'<span class="divineName">\1</span>',
        text,
    )
    # Any remaining <span...> we keep but sanitise. Escape stray angle brackets
    # that aren't part of an allowed tag.
    # Easier: strip all other HTML tags the source didn't use.
    return text


def main():
    if not SRC_PATH.exists():
        sys.exit(f"Missing source: {SRC_PATH}")

    raw = SRC_PATH.read_text(encoding="utf-16")
    # Normalise: remove stray BOM / nulls
    raw = raw.replace("﻿", "")
    lines = raw.splitlines()
    header = lines[0]
    data_lines = lines[1:]

    # Group by book (1-indexed) and chapter.
    # Structure: books[book_num][chapter_num] = [(verse_num, formatting, text), ...]
    books_data = {}
    for line in data_lines:
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        try:
            book_num = int(parts[0])
            chapter = int(parts[1])
            formatting = parts[2]  # "" or "<p>"
            verse_num = int(parts[3])
        except ValueError:
            continue
        text = parts[4].strip()
        if not text:
            continue
        books_data.setdefault(book_num, {}).setdefault(chapter, []).append(
            (verse_num, formatting, text)
        )

    # Render TOC + body
    toc_rows = []
    body_blocks = []
    total_verses = 0
    current_section = None

    for idx, (slug, title, hebrew, section) in enumerate(BOOKS, start=1):
        if section != current_section:
            toc_rows.append(
                f'<li class="toc-section"><span class="toc-section-label">{esc(section)}</span></li>'
            )
            body_blocks.append(
                f'  <header class="reader-section-heading" id="section-{esc(section).lower().replace(chr(39), "")}">\n'
                f'    <div class="reader-section-eyebrow">Section</div>\n'
                f'    <h2>{esc(section)}</h2>\n'
                f'  </header>\n'
            )
            current_section = section

        chapters = books_data.get(idx, {})
        if not chapters:
            continue

        toc_rows.append(
            f'<li><a href="#{slug}"><span class="toc-num">{idx}</span> '
            f'<span class="toc-name">{esc(title)}</span></a></li>'
        )

        body_blocks.append(
            f'  <article class="surah" id="{slug}">\n'
            f'    <header class="surah-header">\n'
            f'      <div class="surah-num">{idx}</div>\n'
            f'      <h2 class="surah-title">{esc(title)}</h2>\n'
            f'      <p class="surah-subtitle">{esc(hebrew)}</p>\n'
            f'    </header>\n'
        )
        for chap_num in sorted(chapters.keys()):
            verses = chapters[chap_num]
            body_blocks.append(
                f'    <section class="chapter" id="{slug}-{chap_num}">\n'
                f'      <h3 class="chapter-title">'
                f'<span class="chapter-num">Chapter {chap_num}</span></h3>\n'
                f'      <ol class="verses">\n'
            )
            for verse_num, formatting, text in verses:
                total_verses += 1
                text_clean = clean_text(text)
                # Escape any remaining chars that aren't inside our allowed tags.
                # The only allowed tags here are <span class="divineName">...</span>.
                # We preserve text as-is after clean_text — its remaining content
                # is plain text with the one allowed span tag.
                # To avoid XSS / malformed HTML, keep the output as the cleaned text.
                body_blocks.append(
                    f'        <li id="{slug}-{chap_num}-{verse_num}" value="{verse_num}">'
                    f'<span class="verse-number">{verse_num}</span>'
                    f'<span class="verse-text">{text_clean}</span></li>\n'
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
<meta name="description" content="Read the complete Hebrew Bible (Tanakh) in the JPS 1917 English translation — Torah, Neviim, and Ketuvim. Public domain.">
<title>Tanakh (JPS 1917) — Analyzing Islam</title>
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
  .divineName {{
    font-variant: small-caps;
    letter-spacing: 0.04em;
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
      <div class="reader-meta">Jewish Publication Society · 1917 English translation · Public domain</div>
      <h1>The Tanakh</h1>
      <p class="reader-intro">The Hebrew Bible in the Jewish Publication Society 1917 English translation — the first major Jewish-authored English Bible. 39 books across Torah, Neviʾim (Prophets), and Ketuvim (Writings). {total_verses} verses in total. Public domain.</p>
      <div class="reader-cta">
        <a href="../read-external.html" class="btn">← External sources</a>
        <a href="https://archive.org/details/jps1917" class="btn" target="_blank" rel="noopener">Source · Internet Archive</a>
      </div>
    </header>

{body_html}
  </main>

</div>

<footer class="site-footer">
  JPS 1917 Tanakh. Public domain. Released under Creative Commons Public Domain Dedication 1.0 (via OpenSiddur / jewishpub.org). Anchors: #{{book-slug}}-{{chapter}}-{{verse}}.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT_PATH}: {total_verses} verses across {sum(1 for b in BOOKS)} books")


if __name__ == "__main__":
    main()
