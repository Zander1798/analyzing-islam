#!/usr/bin/env python3
"""Build site/read-external/book-of-enoch.html from the Project Gutenberg
plain-text edition of R.H. Charles's 1 Enoch (PG #77935, London 1917).

Source: .tmp/enoch-gutenberg.txt (downloaded via curl).

Chapter starts are lines beginning with a Roman numeral followed by a
period, e.g. "VI. 1. And it came to pass...". A handful of chapter
numbers appear twice — once as a section title in italics, once at the
actual content start; we keep the latest occurrence as the content
start. Verses are numbered inline within the chapter text.
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
SRC_PATH = ROOT / ".tmp" / "enoch-gutenberg.txt"
OUT_PATH = ROOT / "site" / "read-external" / "book-of-enoch.html"


SECTIONS = [
    (1,  "The Book of the Watchers",
     "Parable of Enoch, the Fall of the Angels, and Enoch's dream visions and journeys · Chapters I–XXXVI"),
    (37, "The Parables (Similitudes) of Enoch",
     "The three parables on the coming judgement and the Son of Man · Chapters XXXVII–LXXI"),
    (72, "The Book of the Heavenly Luminaries",
     "Astronomical and calendrical material · Chapters LXXII–LXXXII"),
    (83, "The Book of Dream-Visions",
     "Enoch's dream-visions, including the Animal Apocalypse · Chapters LXXXIII–XC"),
    (91, "The Epistle of Enoch",
     "The Apocalypse of Weeks and concluding admonitions · Chapters XCI–CVIII"),
]


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


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# --- load plain text ---
if not SRC_PATH.exists():
    sys.exit(
        f"Missing source: {SRC_PATH}\n"
        f"Download first:\n"
        f'  curl -sL -A "Mozilla/5.0" https://www.gutenberg.org/cache/epub/77935/pg77935.txt -o {SRC_PATH}'
    )
text = SRC_PATH.read_text(encoding="utf-8")

# Trim the Gutenberg boilerplate.
start_m = re.search(r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK[^\n]*\*\*\*", text)
end_m = re.search(r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK[^\n]*\*\*\*", text)
if not start_m or not end_m:
    sys.exit("Couldn't locate Project Gutenberg start/end markers.")
body = text[start_m.end():end_m.start()]

# Drop the front matter up to the start of Chapter I's content marker.
# Chapter I in this edition begins with "I. 1. The words of the blessing of Enoch"
first_chap_m = re.search(r"^I\.\s+1\.\s+The words of the blessing of Enoch",
                         body, re.MULTILINE)
if not first_chap_m:
    sys.exit("Couldn't find the start of Chapter I.")
body = body[first_chap_m.start():]


# --- locate chapter markers ---
# Each chapter starts at column 0 with a Roman numeral + period + space.
# Allow an optional leading "[" — a few chapters are bracket-wrapped in the
# edition to indicate a textual insertion (e.g. "[LIX. 1. In those days...").
CHAPTER_RE = re.compile(r"^[ \t]*\[?([IVXLCM]+)\.\s+(.+)$", re.MULTILINE)
raw_markers = []
for m in CHAPTER_RE.finditer(body):
    roman = m.group(1)
    rest = m.group(2).rstrip()
    try:
        n = roman_to_int(roman)
    except Exception:
        continue
    if not (1 <= n <= 108):
        continue
    raw_markers.append((n, m.start(), rest))


def looks_like_title_line(rest: str) -> bool:
    """A section title line consists mostly of italics markers and has no
    verse-number "1. ..." pattern. We treat those as headings, not content."""
    if re.search(r"\d+\.\s", rest):
        return False
    if re.fullmatch(r"_[^_]+_\.?", rest.strip()):
        return True
    return False


# Keep ALL markers grouped per chapter. Prefer the last content-bearing
# marker; fall back to the last title marker when a chapter only has a
# title line (the content follows after, without the chapter number
# prefix — chapter XXXVIII is like this).
from collections import defaultdict
grouped = defaultdict(list)
for n, pos, rest in raw_markers:
    grouped[n].append((pos, rest))

best = {}
for n, occs in grouped.items():
    content = [o for o in occs if not looks_like_title_line(o[1])]
    if content:
        best[n] = content[-1]
    else:
        best[n] = occs[-1]

missing = [n for n in range(1, 109) if n not in best]
if missing:
    print(f"WARNING: missing chapters {missing}")

# Build ordered chapter list with (n, start, end) positions.
ordered = sorted(best.items(), key=lambda kv: kv[1][0])
chapters_parsed = []
for i, (n, (pos, _rest)) in enumerate(ordered):
    nxt = ordered[i + 1][1][0] if i + 1 < len(ordered) else len(body)
    chunk = body[pos:nxt]
    # Strip the leading ROMAN. marker from the chunk.
    chunk = re.sub(r"^[IVXLCM]+\.\s+", "", chunk, count=1)
    # Collapse internal newlines and whitespace into single spaces.
    chunk = re.sub(r"\s+", " ", chunk).strip()
    chapters_parsed.append((n, chunk))

# Re-order by chapter number just in case.
chapters_parsed.sort(key=lambda kv: kv[0])


# --- split each chapter into verses ---
VERSE_SPLIT_RE = re.compile(r"(?<=\s)(\d{1,3})\.\s+")


def parse_verses(chunk: str):
    # Normalise brackets/symbols used in Charles's edition. We KEEP them —
    # they convey textual-critical information — but make sure they don't
    # confuse the verse-splitter.
    text = " " + chunk  # leading space so VERSE_SPLIT_RE catches verse 1
    markers = list(VERSE_SPLIT_RE.finditer(text))
    if not markers:
        return [(None, chunk)]
    verses = []
    # Any text before verse 1 becomes an unnumbered lead-in.
    if markers[0].start() > 1:
        lead = text[:markers[0].start()].strip()
        if lead:
            verses.append((None, lead))
    for j, m in enumerate(markers):
        vnum = int(m.group(1))
        vstart = m.end()
        vend = markers[j + 1].start() if j + 1 < len(markers) else len(text)
        vtext = text[vstart:vend].strip()
        if vtext:
            verses.append((vnum, vtext))
    return verses


# --- render TOC ---
toc_rows = []
section_iter = iter(SECTIONS)
current_section = next(section_iter, None)
for n, _chunk in chapters_parsed:
    if current_section and n == current_section[0]:
        toc_rows.append(
            f'<li class="toc-section"><span class="toc-section-label">{esc(current_section[1])}</span></li>'
        )
        current_section = next(section_iter, None)
    toc_rows.append(
        f'<li><a href="#enoch-{n}"><span class="toc-num">{roman_of(n)}</span> '
        f'<span class="toc-name">Chapter {n}</span></a></li>'
    )
toc_html = "\n".join(toc_rows)


# --- render chapters ---
article_blocks = []
total_verses = 0
section_iter = iter(SECTIONS)
current_section = next(section_iter, None)

for n, chunk in chapters_parsed:
    verses = parse_verses(chunk)

    section_html = ""
    if current_section and n == current_section[0]:
        label, desc = current_section[1], current_section[2]
        section_html = (
            f'  <header class="reader-section-heading">\n'
            f'    <div class="reader-section-eyebrow">Section</div>\n'
            f'    <h2>{esc(label)}</h2>\n'
            f'    <p>{esc(desc)}</p>\n'
            f'  </header>\n'
        )
        current_section = next(section_iter, None)

    verse_items = []
    for vnum, vtext in verses:
        if vnum is None:
            verse_items.append(
                f'      <li class="verse-unnumbered"><span class="verse-text">{esc(vtext)}</span></li>'
            )
        else:
            total_verses += 1
            verse_items.append(
                f'      <li id="enoch-{n}-{vnum}" value="{vnum}"><span class="verse-number">{vnum}</span><span class="verse-text">{esc(vtext)}</span></li>'
            )
    verse_html = "\n".join(verse_items)

    article_blocks.append(
        f'{section_html}'
        f'  <article class="surah" id="enoch-{n}">\n'
        f'    <header class="surah-header">\n'
        f'      <div class="surah-num">{roman_of(n)}</div>\n'
        f'      <h2 class="surah-title">Chapter {n}</h2>\n'
        f'    </header>\n'
        f'    <ol class="verses">\n'
        f'{verse_html}\n'
        f'    </ol>\n'
        f'  </article>\n'
    )


total_chapters = len(chapters_parsed)
page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read the full Book of Enoch (1 Enoch) in R.H. Charles's 1917 English translation. All 108 chapters, verse by verse. Public domain.">
<title>The Book of Enoch — Analyzing Islam</title>
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
    font-size: clamp(32px, 4vw, 48px);
    line-height: 1.05;
    margin: 0 0 10px;
    letter-spacing: -0.02em;
  }}
  .reader-section-heading p {{
    color: var(--text-muted);
    margin: 0;
    max-width: 60ch;
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
    <div class="reader-toc-header">Chapters</div>
    <ol>
{toc_html}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">R. H. Charles · 1917 English translation · Public domain</div>
      <h1>The Book of Enoch</h1>
      <p class="reader-intro">1 Enoch — the Ethiopic Apocalypse of Enoch, in the classic English translation by R. H. Charles (Oxford, 1917). {total_chapters} chapters covering the fall of the Watchers, Enoch's heavenly journeys, the parables of the Son of Man, the astronomical secrets, and the Apocalypse of Weeks. Cited across the catalog for parallels with Islamic angelology (Hārūt and Mārūt, the jinn, the Watchers) and eschatology.</p>
      <div class="reader-cta">
        <a href="../read-external.html" class="btn">← External sources</a>
        <a href="https://www.gutenberg.org/ebooks/77935" class="btn" target="_blank" rel="noopener">Source · Project Gutenberg</a>
      </div>
    </header>

{chr(10).join(article_blocks)}
  </main>

</div>

<footer class="site-footer">
  R. H. Charles's 1917 English translation of 1 Enoch. Public domain. Sourced from Project Gutenberg eBook #77935. Every verse anchored as #enoch-{{chapter}}-{{verse}} for stable linking.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(page, encoding="utf-8")
print(f"Wrote {OUT_PATH}: {total_chapters} chapters, {total_verses} verses")
