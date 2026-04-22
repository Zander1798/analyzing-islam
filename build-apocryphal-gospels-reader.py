#!/usr/bin/env python3
"""Build site/read-external/apocryphal-gospels.html from three public-domain
Roberts–Donaldson translations (Ante-Nicene Fathers Vol 8, 1886):

  - Infancy Gospel of Thomas (First Greek Form)
  - Infancy Gospel of James (Protevangelium)
  - Arabic Infancy Gospel (Gospel of the Infancy of the Saviour)

Source HTML is cached under .tmp/ from earlychristianwritings.com
(Thomas, James) and gnosis.org (Arabic Infancy).
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
OUT_PATH = ROOT / "site" / "read-external" / "apocryphal-gospels.html"

WORKS = [
    {
        "slug": "thomas",
        "src": ROOT / ".tmp" / "infancy-thomas.html",
        "title": "Infancy Gospel of Thomas",
        "subtitle": "First Greek Form · Roberts–Donaldson 1886",
        "source_url": "https://www.earlychristianwritings.com/text/infancythomas-a-roberts.html",
        "intro": (
            "The Infancy Gospel of Thomas. 19 chapters of childhood miracles "
            "including Jesus animating clay birds (chapter 2), cursing a child "
            "who then dies (chapter 4), and humbling his teacher (chapter 6). "
            "The clay-birds miracle is the direct source of Q 3:49 and 5:110."
        ),
    },
    {
        "slug": "james",
        "src": ROOT / ".tmp" / "infancy-james.html",
        "title": "Infancy Gospel of James",
        "subtitle": "Protevangelium · Roberts–Donaldson 1886",
        "source_url": "https://www.earlychristianwritings.com/text/infancyjames-roberts.html",
        "intro": (
            "The Protevangelium of James (mid-2nd century). The earliest "
            "extended account of Mary's birth, upbringing in the temple, and "
            "betrothal — the textual source behind many of the Quran's details "
            "on Mary (Surah 3:35-44) not found in the canonical Gospels."
        ),
    },
    {
        "slug": "arabic",
        "src": ROOT / ".tmp" / "infancy-arabic.html",
        "title": "Arabic Infancy Gospel",
        "subtitle": "Gospel of the Infancy of the Saviour · Roberts–Donaldson, ANF Vol 8, 1886",
        "source_url": "http://gnosis.org/library/infarab.htm",
        "intro": (
            "Arabic Infancy Gospel (compiled by the 6th c., possibly from a "
            "Syriac original). 55 chapters combining material from the "
            "Protevangelium and Infancy Thomas with additional legendary "
            "episodes. Key parallels for the Quran: the cradle-speech "
            "(Q 19:29-33), the clay birds, and the palm-tree in childbirth "
            "(Q 19:23-26)."
        ),
    },
]


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


# --- Extract chapter list from HTML ---
# Strategy: strip all HTML tags, then find every paragraph starting with
# "N. " at line start (or after a paragraph break). Paragraphs are joined
# by HTML <p> / <P> boundaries, so we first split on those, then parse.

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
STYLE_RE = re.compile(r"<style[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HEAD_RE = re.compile(r"<head[^>]*>.*?</head>", re.IGNORECASE | re.DOTALL)
NAV_RE = re.compile(r'<div id="menu"[^>]*>.*?</div>\s*</div>', re.IGNORECASE | re.DOTALL)


def extract_chapters(raw_html: str):
    # Strip non-text parts first.
    raw = HEAD_RE.sub("", raw_html)
    raw = SCRIPT_RE.sub("", raw)
    raw = STYLE_RE.sub("", raw)
    raw = COMMENT_RE.sub("", raw)

    # Split on paragraph boundaries (case-insensitive).
    parts = re.split(r"<[Pp]\b[^>]*>", raw)

    chapters = []
    seen = set()
    for part in parts:
        # Strip remaining tags, unescape entities, normalise whitespace.
        text = TAG_RE.sub(" ", part)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        m = re.match(r"^(\d{1,3})\.\s+(.+)$", text)
        if not m:
            continue
        num = int(m.group(1))
        body = m.group(2).strip()
        # Reject huge "1." false positives from menus.
        if len(body) < 10:
            continue
        # Take the first occurrence per number — skip duplicates (e.g. menu
        # items echoing the same "1.").
        if num in seen:
            continue
        seen.add(num)
        chapters.append((num, body))
    chapters.sort(key=lambda kv: kv[0])
    return chapters


# --- render a single work ---
def render_work(w, chapters):
    toc = [f'<li class="toc-section"><span class="toc-section-label">{esc(w["title"])}</span></li>']
    for n, _ in chapters:
        toc.append(
            f'<li><a href="#{w["slug"]}-{n}"><span class="toc-num">{roman_of(n)}</span> '
            f'<span class="toc-name">Chapter {n}</span></a></li>'
        )
    toc_html = "\n".join(toc)

    articles = [
        f'  <header class="reader-section-heading" id="{w["slug"]}">\n'
        f'    <div class="reader-section-eyebrow">{esc(w["subtitle"])}</div>\n'
        f'    <h2>{esc(w["title"])}</h2>\n'
        f'    <p>{esc(w["intro"])}</p>\n'
        f'    <p class="reader-section-source"><a href="{esc(w["source_url"])}" target="_blank" rel="noopener">Source text</a></p>\n'
        f'  </header>\n'
        f'  <article class="surah">\n'
        f'    <ol class="verses">\n'
    ]
    for n, text in chapters:
        articles.append(
            f'      <li id="{w["slug"]}-{n}" value="{n}">'
            f'<span class="verse-number">{n}</span>'
            f'<span class="verse-text">{esc(text)}</span></li>\n'
        )
    articles.append('    </ol>\n  </article>\n')
    return toc_html, "".join(articles), len(chapters)


def main():
    for w in WORKS:
        if not w["src"].exists():
            sys.exit(f"Missing source: {w['src']}")

    all_toc = []
    all_body = []
    totals = []
    for w in WORKS:
        raw = w["src"].read_text(encoding="utf-8", errors="replace")
        chapters = extract_chapters(raw)
        toc_html, body_html, n = render_work(w, chapters)
        all_toc.append(toc_html)
        all_body.append(body_html)
        totals.append((w["title"], n))

    toc_final = "\n".join(all_toc)
    body_final = "\n".join(all_body)

    grand_total = sum(n for _, n in totals)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read the three apocryphal infancy gospels cited in the catalog — the Infancy Gospel of Thomas, the Protevangelium of James, and the Arabic Infancy Gospel — in Roberts-Donaldson's 1886 English translations. Public domain.">
<title>Apocryphal Infancy Gospels — Analyzing Islam</title>
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
    margin: 0 0 8px;
    max-width: 70ch;
  }}
  .reader-section-source a {{
    font-family: var(--sans);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-decoration: none;
  }}
  .reader-section-source a:hover {{
    color: var(--accent);
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
    <div class="reader-toc-header">Works</div>
    <ol>
{toc_final}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">Ante-Nicene Fathers Vol 8 · Roberts–Donaldson · 1886 · Public domain</div>
      <h1>Apocryphal Infancy Gospels</h1>
      <p class="reader-intro">Three apocryphal infancy gospels cited across the catalog as direct textual sources behind the Quran's Jesus-narratives: the clay birds animated by a word, Jesus speaking from the cradle, the palm tree in childbirth. {grand_total} chapters in the Roberts–Donaldson public-domain translations.</p>
      <div class="reader-cta">
        <a href="../read-external.html" class="btn">← External sources</a>
        <a href="#thomas" class="btn">Infancy Thomas</a>
        <a href="#james" class="btn">Protevangelium James</a>
        <a href="#arabic" class="btn">Arabic Infancy</a>
      </div>
    </header>

{body_final}
  </main>

</div>

<footer class="site-footer">
  Roberts–Donaldson 1886 English translations of the apocryphal infancy gospels. Public domain. Anchors: #thomas-{{N}}, #james-{{N}}, #arabic-{{N}}.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    for title, n in totals:
        print(f"  {title}: {n} chapters")


if __name__ == "__main__":
    main()
