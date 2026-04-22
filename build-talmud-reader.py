#!/usr/bin/env python3
"""Build the Babylonian Talmud reader (Rodkinson 1903 edition, PD).

Scrapes sacred-texts.com/jud/t01/ … /jud/t10/ (with a browser User-Agent
and Referer header to get through Cloudflare), caches every chapter
page, then emits:

  site/read-external/talmud.html         — index of the 10 Books
  site/read-external/talmud-{1..10}.html — per-Book readers

Chapter pages on sacred-texts.com follow the pattern t{NN}{CC}.htm.
Content lives between two <hr> tags in the body.

The scrape is polite: a 0.6s delay between fetches, full cache to
.tmp/sources/talmud/ so reruns are instant.
"""
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
CACHE_DIR = ROOT / ".tmp" / "sources" / "talmud"
OUT_DIR = ROOT / "site" / "read-external"

BASE = "https://sacred-texts.com/jud"

BOOKS = [
    (1,  "Tract Sabbath (Vols. I–II)",
         "Laws of the Sabbath — the 39 forbidden labours, kindling, carrying, what may be worn, preparation of food."),
    (2,  "Tracts Erubin, Shekalim, Rosh Hashana",
         "Sabbath boundaries (eruvin), Temple shekel contributions, New Year calendar and the shofar."),
    (3,  "Tract Pesachim (Vol. I)",
         "Passover — removal of leaven, the paschal offering, the seder."),
    (4,  "Tracts Pesachim (Vol. II), Yomah, Hagiga",
         "Passover continued, Yom Kippur Temple service (including the goat for Azazel), pilgrimage offerings."),
    (5,  "Tracts Aboth, Derech Eretz, Betzah, Succah, Moed Katan, Taanith, Megilla",
         "Fathers (Pirkei Avot), worldly conduct, festival labour, booths, minor festivals, fasts, the Megillah."),
    (6,  "Tract Baba Kama (First Gate)",
         "Torts — damages, animals and fire, personal injury."),
    (7,  "Tract Baba Bathra (Last Gate)",
         "Property, partnerships, inheritance, contracts."),
    (8,  "Tract Sanhedrin (Supreme Council)",
         "Courts, capital cases, the false prophet, the Messianic age — contains the foundational ethical passage \"whoever saves a life saves a world\" (Sanhedrin 4:5) which Q 5:32 quotes."),
    (9,  "Tracts Maccoth, Ebel Rabbathi, Shebuoth, Eduyoth, Abuda Zara, Horioth",
         "Lashes, mourning, oaths, testimonies, idolatry (critical for Jewish-Muslim polemic), and erroneous rulings."),
    (10, "History of the Talmud",
         "Rodkinson's own volume on the history, development, and defence of the Talmud."),
]


def fetch(url: str, cache_name: str) -> str:
    cache = CACHE_DIR / cache_name
    if cache.exists():
        return cache.read_text(encoding="utf-8")

    # Referer helps bypass Cloudflare's managed challenge.
    book_slug = re.match(r"(t\d\d)", cache_name)
    referer_tail = f"/{book_slug.group(1)}/" if book_slug else "/"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"{BASE}{referer_tail}",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read().decode("utf-8", errors="replace")

    # Detect Cloudflare challenge
    if "Just a moment..." in data[:500] or "_cf_chl_opt" in data[:2000]:
        raise RuntimeError(f"Cloudflare challenged: {url}")

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(data, encoding="utf-8")
    time.sleep(0.6)
    return data


def parse_book_index(book_num: int):
    """Returns list of (chapter_file, chapter_label, section_label_or_none).
    Section labels come from <H3>Volume I</H3> etc. inside the index."""
    url = f"{BASE}/t{book_num:02d}/"
    html_text = fetch(url, f"t{book_num:02d}-index.html")

    # Extract body between <H5 ALIGN="CENTER">...</H5> block and the final <HR>
    # Actually simpler: walk through all <H3> and <A HREF="..."> in order.

    # Collect interleaved headings + anchors. <H3 ALIGN="CENTER">Volume I</H3>
    # then <A HREF="t0100.htm">Title Page</A><BR>
    out = []
    current_section = None

    # Simplified token stream: find every <H3> or <A HREF>. Books vary
    # in their chapter URL scheme — t0100.htm in Book 1, eru05.htm in
    # Book 2, sanhXX.htm in Book 8, etc. — so we accept any same-folder
    # .htm link that's plausibly a chapter.
    token_re = re.compile(
        r'<H3[^>]*>(?P<h3>[^<]+)</H3>|'
        r'<A\s+HREF="(?P<href>[a-z0-9][a-z0-9_-]{1,15}\.htm)"[^>]*>(?P<label>[^<]+)</A>',
        re.IGNORECASE,
    )
    for m in token_re.finditer(html_text):
        if m.group("h3"):
            current_section = m.group("h3").strip()
        else:
            href = m.group("href")
            label = re.sub(r"\s+", " ", m.group("label")).strip()
            out.append((href, label, current_section))
    return out


# Labels of front/back-matter entries we skip from the body content
# (we'll still list them as a tiny header if desired, but we don't
# render their text inline — keeping the reader focused on Mishnah+Gemara).
SKIP_LABELS = {
    "title page", "explanatory remarks", "dedication",
    "contents", "editor's preface", "preface to the second edition",
    "errata", "appendix", "the prayer at the conclusion of a tract",
    "brief general introduction to the babylonian talmud",
    "introduction to tract sabbath",
    "synopsis of subjects",
    "introduction", "preface",
}


def is_skippable(label: str) -> bool:
    norm = label.strip().lower()
    if norm in SKIP_LABELS:
        return True
    if norm.startswith("synopsis of subjects"):
        return True
    if norm.startswith("synopsis of tract"):
        return True
    if "title page" in norm:
        return True
    if norm.startswith("introduction to"):
        return True
    if norm.startswith("preface to"):
        return True
    if norm.startswith("contents of"):
        return True
    if norm == "contents" or norm.endswith("contents"):
        return True
    if norm == "tract rosh hashana contents":
        return True
    return False


def extract_content(raw_html: str) -> str:
    """Pull the chapter body out of a sacred-texts chapter page.

    Layout:
        <BODY>
         <CENTER>
           <A …>…CD…</A><BR>
           <A …>Sacred Texts</A>…
           <HR>
           <A …>…kindle…</A>
         </CENTER>
         <HR>
         … actual content …
         <HR>
         <nav …>…prev/next…</nav>
        </BODY>

    We take everything between the 2nd and last <HR>, minus <script>
    and a few anchor-only lines.
    """
    # Find the <BODY ...> block
    m = re.search(r"<BODY[^>]*>(.*)</BODY>", raw_html, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    body = m.group(1)

    # Strip scripts
    body = re.sub(r"<script\b[^>]*>.*?</script>", "", body, flags=re.IGNORECASE | re.DOTALL)

    # Split on <HR> (case-insensitive, allow self-closing, attributes)
    parts = re.split(r"<hr\b[^>]*/?>", body, flags=re.IGNORECASE)
    # Content blocks are parts[1..-2] joined, but often there are just 3 parts:
    # [0]=nav, [1]=content, [2]=prev/next
    # Sometimes 4 parts if there's an internal HR. We take parts[1:-1] joined.
    if len(parts) < 3:
        return ""
    content = "<hr>".join(parts[1:-1])

    # Strip nav pieces that leak in
    content = re.sub(
        r'<nav\b[^>]*>.*?</nav>', "", content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return content.strip()


TAG_KEEP = re.compile(
    r"</?(p|h1|h2|h3|h4|h5|h6|em|i|b|strong|ol|ul|li|br)\b[^>]*>",
    re.IGNORECASE,
)


def sanitize(content: str) -> str:
    """Keep only prose formatting tags, strip attributes, drop everything
    else into plain text. Convert deprecated tags to semantic ones."""
    # Uniform case / strip attributes on kept tags; drop all others.
    def clean_tag(tag: str) -> str:
        tag_m = re.match(r"</?([a-zA-Z0-9]+)", tag)
        if not tag_m:
            return ""
        name = tag_m.group(1).lower()
        # H1/H2 downgrade to H3 (avoid fighting with site h1/h2)
        if name in ("h1", "h2"):
            name = "h3"
        close = "/" if tag.startswith("</") else ""
        return f"<{close}{name}>"

    # First pass: keep tags we want, converted; drop others.
    out = []
    i = 0
    for t in re.finditer(r"<[^>]+>", content):
        out.append(content[i:t.start()])
        tag = t.group(0)
        if TAG_KEEP.match(tag):
            out.append(clean_tag(tag))
        # drop everything else
        i = t.end()
    out.append(content[i:])
    sanitized = "".join(out)

    # Collapse whitespace
    sanitized = re.sub(r"&nbsp;", " ", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"[ \t]+", " ", sanitized)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)

    # <br><br> → paragraph break
    sanitized = re.sub(r"(?:<br>\s*){2,}", "\n\n", sanitized, flags=re.IGNORECASE)
    # Single <br> → space
    sanitized = re.sub(r"<br>", " ", sanitized, flags=re.IGNORECASE)

    # Wrap unwrapped paragraphs: split on blank lines, wrap naked text in <p>
    blocks = re.split(r"\n\s*\n", sanitized)
    wrapped = []
    for blk in blocks:
        blk = blk.strip()
        if not blk:
            continue
        # If it already starts with a block tag, leave it.
        if re.match(r"<(p|h3|h4|h5|h6|ol|ul|li)\b", blk, re.IGNORECASE):
            wrapped.append(blk)
        else:
            wrapped.append(f"<p>{blk}</p>")
    joined = "\n\n".join(wrapped)

    # --- Post-processing: strip typesetting artefacts ---
    # Stray double close tags from malformed source
    joined = re.sub(r"</p>\s*</p>", "</p>", joined)
    # Attribution banners sacred-texts stamps onto every chapter.
    joined = re.sub(
        r"<p>\s*<i>\s*(?:Bablyonian|Babylonian)\s+Talmud[^<]*</i>[^<]*sacred-texts\.com[^<]*</p>",
        "", joined, flags=re.IGNORECASE | re.DOTALL,
    )
    # Isolated page-number paragraphs "<p>p. 97</p>"
    joined = re.sub(r"<p>\s*p\.\s*\d+\s*</p>", "", joined, flags=re.IGNORECASE)
    # Duplicate chapter headings that the source embeds inside content
    # (e.g. "<h3>CHAPTER IV.</h3>" — we already print our own).
    joined = re.sub(
        r"<h3>\s*CHAPTER\s+[IVXLCM]+\.?\s*</h3>",
        "", joined, flags=re.IGNORECASE,
    )
    # "Next:" / "Previous:" chapter navigation that sometimes leaks in
    joined = re.sub(r"<p>\s*(?:Next|Previous):[^<]*</p>", "", joined, flags=re.IGNORECASE)
    # Collapse blank paragraphs and multiple newlines
    joined = re.sub(r"<p>\s*</p>", "", joined)
    joined = re.sub(r"\n{3,}", "\n\n", joined)
    return joined.strip()


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# -------------------- main build --------------------

def build():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    book_totals = []   # (book_num, book_title, [chapters])
    grand_chapters = 0

    for book_num, book_title, book_desc in BOOKS:
        print(f"\n=== Book {book_num}: {book_title} ===")
        entries = parse_book_index(book_num)
        print(f"  index: {len(entries)} links")
        chapters = []
        current_section = None
        for href, label, section in entries:
            if section:
                current_section = section
            if is_skippable(label):
                continue
            # Fetch the chapter
            url = f"{BASE}/t{book_num:02d}/{href}"
            try:
                page = fetch(url, f"t{book_num:02d}-{href}")
            except Exception as e:
                print(f"  FAILED {href}: {e}")
                continue
            content = extract_content(page)
            sanitized = sanitize(content)
            if not sanitized.strip():
                continue
            chap_id = href.replace(".htm", "")  # e.g. t0109
            chapters.append({
                "id": chap_id,
                "label": label,
                "section": current_section,
                "content": sanitized,
            })
        book_totals.append((book_num, book_title, book_desc, chapters))
        grand_chapters += len(chapters)
        print(f"  rendered: {len(chapters)} chapters")

    # Write per-book readers
    for book_num, book_title, book_desc, chapters in book_totals:
        write_book_page(book_num, book_title, book_desc, chapters)

    # Write index
    write_index(book_totals, grand_chapters)

    print(f"\nTotal: {grand_chapters} chapters across {len(book_totals)} Books")


def write_book_page(book_num, book_title, book_desc, chapters):
    """One big scrollable reader for this Book."""
    toc_rows = []
    last_section = None
    for c in chapters:
        if c["section"] and c["section"] != last_section:
            toc_rows.append(
                f'<li class="toc-section"><span class="toc-section-label">{esc(c["section"])}</span></li>'
            )
            last_section = c["section"]
        toc_rows.append(
            f'<li><a href="#{esc(c["id"])}">'
            f'<span class="toc-name">{esc(c["label"])}</span></a></li>'
        )

    body_parts = []
    last_section = None
    for c in chapters:
        if c["section"] and c["section"] != last_section:
            body_parts.append(
                f'<header class="reader-section-heading">\n'
                f'  <div class="reader-section-eyebrow">Section</div>\n'
                f'  <h2>{esc(c["section"])}</h2>\n'
                f'</header>\n'
            )
            last_section = c["section"]
        body_parts.append(
            f'<article class="surah" id="{esc(c["id"])}">\n'
            f'  <header class="surah-header">\n'
            f'    <div class="surah-num">{esc(c["id"].upper())}</div>\n'
            f'    <h2 class="surah-title">{esc(c["label"])}</h2>\n'
            f'  </header>\n'
            f'  <div class="prose">\n'
            f'    {c["content"]}\n'
            f'  </div>\n'
            f'</article>\n'
        )

    page = TALMUD_BOOK_TEMPLATE.format(
        book_num=book_num,
        book_title=esc(book_title),
        book_desc=esc(book_desc),
        toc=("\n".join(toc_rows)),
        body=("\n".join(body_parts)),
        chapter_count=len(chapters),
    )
    out = OUT_DIR / f"talmud-{book_num}.html"
    out.write_text(page, encoding="utf-8")
    print(f"  wrote {out}")


def write_index(book_totals, grand_chapters):
    cards = []
    for book_num, book_title, book_desc, chapters in book_totals:
        cards.append(
            f'<a href="talmud-{book_num}.html" class="book-card">\n'
            f'  <div><h3>Book {book_num}</h3>\n'
            f'    <p class="book-sub">{esc(book_title)}</p>\n'
            f'    <p>{esc(book_desc)}</p>\n'
            f'  </div>\n'
            f'  <div class="book-meta">{len(chapters)} chapters · read ›</div>\n'
            f'</a>'
        )
    page = TALMUD_INDEX_TEMPLATE.format(
        grand_chapters=grand_chapters,
        cards="\n".join(cards),
    )
    out = OUT_DIR / "talmud.html"
    out.write_text(page, encoding="utf-8")
    print(f"\nwrote {out}")


# -------------------- templates --------------------

TALMUD_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read the Babylonian Talmud in Michael Rodkinson's 1903 English translation — the complete New Edition, public domain. {grand_chapters} chapters across 10 Books.">
<title>The Talmud — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<style>
  .book-group {{ margin: 48px 0 8px; }}
  .book-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 14px;
    margin-bottom: 32px;
  }}
  .book-card {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 22px;
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text);
    text-decoration: none;
    min-height: 160px;
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
    line-height: 1.15;
    letter-spacing: -0.015em;
    font-weight: 700;
    margin: 0 0 6px;
  }}
  .book-card .book-sub {{
    font-family: var(--sans);
    font-size: 12px;
    color: var(--text-muted);
    font-style: italic;
    margin: 0 0 10px;
  }}
  .book-card p {{
    font-size: 13px;
    color: var(--text-muted);
    margin: 0 0 12px;
    line-height: 1.5;
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
  .license-notice {{
    padding: 16px 20px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    font-size: 13px;
    color: var(--text-muted);
    margin: 24px 0 48px;
    max-width: 72ch;
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

<main>

  <section class="hero" style="padding: 40px 0 8px; text-align:left;">
    <a href="../read-external.html" class="back-link">← External sources</a>
    <h1 style="font-size:clamp(48px, 7vw, 88px); margin-bottom:20px;">The Talmud</h1>
    <p class="hero-tagline" style="margin-left:0; max-width:720px;">The Babylonian Talmud in Michael L. Rodkinson's 1903 <em>New Edition</em> — the standard English translation used in Anglophone scholarship for half a century, now public domain. {grand_chapters} chapters across 10 Books, covering the most-cited tractates of Jewish law and aggada.</p>
  </section>

  <section class="license-notice">
    <strong>On this edition:</strong> Rodkinson's translation is abridged in places and sometimes paraphrased rather than literal; it is the PD predecessor of the Soncino (1935–52) and Davidson (Sefaria, CC-BY-NC) editions. For critical work, cross-check with Soncino or Sefaria. This reader is sourced from sacred-texts.com, which hosts the complete 1903 edition in HTML.
  </section>

  <div class="book-group">
    <div class="book-grid">
{cards}
    </div>
  </div>

  <section style="padding:24px; background:var(--panel); border:1px solid var(--border); margin-top: 32px;">
    <h3 style="margin-top:0;">Citing the Talmud</h3>
    <p>Talmud references are given as <em>Tractate, page, side</em> — e.g. <strong>Sanhedrin 90a</strong> means folio 90, side <em>a</em>. Rodkinson organises the content by chapter within each tractate rather than by folio, so catalog citations give both: folio (for the standard Talmud reference) and Rodkinson's chapter (for finding the passage in this reader).</p>
    <p style="color:var(--text-muted); font-size:13px; margin-bottom:0;">Catalog entries citing Rodkinson link to the specific chapter anchor in one of the Book pages above.</p>
  </section>

</main>

<footer class="site-footer">
  Michael L. Rodkinson's 1903 New Edition of the Babylonian Talmud. Public domain. Sourced from sacred-texts.com. Anchors: #t{{book}}{{chapter}} (e.g. #t0109 for Book 1, chapter 9).
</footer>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="../assets/js/config.js"></script>
<script src="../assets/js/auth.js" defer></script>
<script src="../assets/js/auth-ui.js" defer></script>
<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""

TALMUD_BOOK_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Babylonian Talmud Book {book_num}: {book_title}. Rodkinson 1903 English translation (public domain).">
<title>Talmud Book {book_num} — {book_title} — Analyzing Islam</title>
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
    font-size: clamp(28px, 3.5vw, 44px);
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
  .prose p {{
    font-size: 15px;
    line-height: 1.7;
    margin: 0 0 16px;
    color: var(--text);
  }}
  .prose p:last-child {{ margin-bottom: 0; }}
  .prose h3, .prose h4, .prose h5 {{
    font-family: var(--serif);
    font-size: clamp(17px, 1.7vw, 20px);
    margin: 24px 0 10px;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--border);
  }}
  .surah {{ margin-bottom: 56px; }}
  .surah-num {{
    font-family: var(--sans);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    font-weight: 600;
  }}
  .surah-title {{
    font-family: var(--serif);
    font-size: clamp(24px, 3vw, 34px);
    line-height: 1.2;
    letter-spacing: -0.015em;
    margin: 4px 0 0;
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
    <div class="reader-toc-header">Book {book_num}</div>
    <ol>
{toc}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">Babylonian Talmud · Rodkinson 1903 · Public domain</div>
      <h1>Book {book_num}</h1>
      <p class="reader-intro"><strong>{book_title}.</strong> {book_desc}</p>
      <div class="reader-cta">
        <a href="talmud.html" class="btn">← All Books</a>
        <a href="https://sacred-texts.com/jud/t{book_num:02d}/" class="btn" target="_blank" rel="noopener">Source · sacred-texts.com</a>
      </div>
    </header>

{body}
  </main>

</div>

<footer class="site-footer">
  Babylonian Talmud, Book {book_num}: {book_title}. Rodkinson 1903 New Edition, public domain. {chapter_count} chapters. Sourced from sacred-texts.com.
</footer>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="../assets/js/config.js"></script>
<script src="../assets/js/auth.js" defer></script>
<script src="../assets/js/auth-ui.js" defer></script>
<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
