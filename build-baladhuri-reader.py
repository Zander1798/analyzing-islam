#!/usr/bin/env python3
"""Build site/read-external/baladhuri.html from archive.org's DjVu OCR text
of Philip K. Hitti's 1916 and F. C. Murgotten's 1924 English translation
of al-Baladhuri's Kitab Futuh al-Buldan — published as "The Origins of
the Islamic State" (2 volumes, Columbia University).

Both volumes are public domain (pre-1929 US publications). OCR quality
is decent but requires minor cleanup (hyphenation, running headers,
page numbers, extra whitespace).

Sources:
  - Vol 1: https://archive.org/download/originsofislamic00balarich/originsofislamic00balarich_djvu.txt
  - Vol 2: https://archive.org/download/originsofislamic02albauoft/originsofislamic02albauoft_djvu.txt
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
VOL1_PATH = ROOT / ".tmp" / "baladhuri-vol1.txt"
VOL2_PATH = ROOT / ".tmp" / "baladhuri-vol2.txt"
OUT_PATH = ROOT / "site" / "read-external" / "baladhuri.html"


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


# Running page headers we want to strip from the body text.
PAGE_HEADERS = {
    "THE ORIGINS OF THE ISLAMIC STATE",
    "ORIGINS OF THE ISLAMIC STATE",
    "ARABIC HISTORIOGRAPHY",
}


def normalise_line(line: str) -> str:
    # Collapse multi-space to single.
    return re.sub(r"\s+", " ", line).strip()


def is_page_header(line: str) -> bool:
    n = normalise_line(line).upper()
    return n in PAGE_HEADERS


def is_page_number(line: str) -> bool:
    n = normalise_line(line)
    return bool(re.fullmatch(r"\d{1,4}", n))


CHAPTER_RE = re.compile(r"^\s*CHAPTER\s+([IVXLCM]+)\b(.*)$")
PART_RE = re.compile(r"^\s*PART\s+([IVXLCM]+)\b(.*)$")


def parse_volume(raw: str, vol_num: int):
    """Return list of (part_num_or_None, part_title, chapters)
    where chapters is [(chap_num, chap_title_guess, paragraphs)]."""
    lines = raw.splitlines()

    # Skip to first PART I or CHAPTER I in the body (not in TOC).
    # The OCR has the TOC chapter listings near the top. The body starts
    # at the first "PART I" line that stands alone.
    start = None
    for i, line in enumerate(lines):
        if PART_RE.match(line) and i > 300:
            start = i
            break
        if CHAPTER_RE.match(line) and normalise_line(line).upper().startswith("CHAPTER ") and i > 300:
            # Accept this as a fallback if no PART found.
            if start is None:
                start = i
    if start is None:
        # Fall back to the beginning.
        start = 0

    parts = []  # [(part_num, part_title, chapters)]
    current_part = None
    current_chapter = None
    buf = []

    def flush_paragraph():
        if not buf:
            return None
        para = " ".join(b for b in buf if b).strip()
        # Join hyphenated line-wraps: "remember- ing" -> "remembering"
        para = re.sub(r"(\w)-\s+(\w)", r"\1\2", para)
        para = re.sub(r"\s+", " ", para)
        buf.clear()
        return para if para else None

    def flush_chapter():
        nonlocal current_chapter
        p = flush_paragraph()
        if p and current_chapter is not None:
            current_chapter["paragraphs"].append(p)
        if current_chapter is not None and current_part is not None:
            current_part["chapters"].append(current_chapter)
        current_chapter = None

    def flush_part():
        nonlocal current_part
        flush_chapter()
        if current_part is not None:
            parts.append((current_part["num"], current_part["title"], current_part["chapters"]))
        current_part = None

    i = start
    while i < len(lines):
        line = lines[i]
        stripped = normalise_line(line)

        if not stripped:
            # Blank line = paragraph break
            p = flush_paragraph()
            if p and current_chapter is not None:
                current_chapter["paragraphs"].append(p)
            i += 1
            continue

        if is_page_header(line):
            i += 1
            continue
        if is_page_number(line):
            i += 1
            continue

        pm = PART_RE.match(line)
        if pm:
            num = roman_to_int(pm.group(1))
            # Part title may be on the next non-empty line.
            title = pm.group(2).strip()
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not CHAPTER_RE.match(lines[j]) and not PART_RE.match(lines[j]):
                cand = normalise_line(lines[j])
                if cand and not is_page_header(lines[j]) and not is_page_number(lines[j]) and len(cand) < 60:
                    title = (title + " " + cand).strip()
                    j += 1
            flush_part()
            current_part = {"num": num, "title": title, "chapters": []}
            i = j
            continue

        cm = CHAPTER_RE.match(line)
        if cm:
            num = roman_to_int(cm.group(1))
            title = cm.group(2).strip()
            # If title empty, look forward for it on next non-empty line.
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if not title and j < len(lines):
                cand = normalise_line(lines[j])
                if (cand and not is_page_header(lines[j]) and not is_page_number(lines[j])
                        and not PART_RE.match(lines[j]) and not CHAPTER_RE.match(lines[j])
                        and len(cand) < 80 and cand.upper() == cand):
                    title = cand
                    j += 1
            flush_chapter()
            if current_part is None:
                # Synthesize part
                current_part = {"num": 0, "title": f"Volume {vol_num}", "chapters": []}
            current_chapter = {"num": num, "title": title, "paragraphs": []}
            i = j
            continue

        # Regular content line — add to paragraph buffer
        if current_chapter is not None:
            buf.append(stripped)
        i += 1

    flush_part()
    return parts


def render_volume(vol_num, parts):
    toc_rows = []
    body_rows = []

    toc_rows.append(
        f'<li class="toc-section"><span class="toc-section-label">Volume {vol_num}</span></li>'
    )
    body_rows.append(
        f'  <header class="reader-section-heading" id="vol-{vol_num}">\n'
        f'    <div class="reader-section-eyebrow">Volume {vol_num}</div>\n'
        f'    <h2>Volume {vol_num}</h2>\n'
        f'  </header>\n'
    )

    for pnum, ptitle, chapters in parts:
        slug_part = f"vol{vol_num}-p{pnum}"
        if pnum > 0:
            toc_rows.append(
                f'<li class="toc-subsection"><a href="#{slug_part}">'
                f'Part {roman_of(pnum)}. {esc(ptitle)}</a></li>'
            )
            body_rows.append(
                f'  <article class="surah" id="{slug_part}">\n'
                f'    <header class="surah-header">\n'
                f'      <div class="surah-num">Part {roman_of(pnum)}</div>\n'
                f'      <h2 class="surah-title">{esc(ptitle) or "Part " + roman_of(pnum)}</h2>\n'
                f'    </header>\n'
            )
        else:
            body_rows.append(f'  <article class="surah">\n')

        for cnum_idx, chap in enumerate(chapters):
            cnum = chap["num"]
            ctitle = chap["title"]
            paras = chap["paragraphs"]
            slug = f"vol{vol_num}-p{pnum}-c{cnum}"
            toc_rows.append(
                f'<li><a href="#{slug}"><span class="toc-num">{roman_of(cnum)}</span> '
                f'<span class="toc-name">{esc(ctitle[:40]) if ctitle else f"Chapter {cnum}"}</span></a></li>'
            )
            body_rows.append(
                f'    <section class="chapter" id="{slug}">\n'
                f'      <h3 class="chapter-title">'
                f'<span class="chapter-num">Chapter {roman_of(cnum)}</span> '
                f'<span class="chapter-head">{esc(ctitle)}</span></h3>\n'
            )
            for j, p in enumerate(paras, 1):
                body_rows.append(
                    f'      <p id="{slug}-p{j}" class="baladhuri-para">'
                    f'<span class="para-num">{j}</span> {esc(p)}</p>\n'
                )
            body_rows.append('    </section>\n')

        body_rows.append('  </article>\n')

    return "\n".join(toc_rows), "".join(body_rows)


def main():
    if not VOL1_PATH.exists() or not VOL2_PATH.exists():
        sys.exit("Missing volume sources under .tmp/")

    v1 = parse_volume(VOL1_PATH.read_text(encoding="utf-8", errors="replace"), 1)
    v2 = parse_volume(VOL2_PATH.read_text(encoding="utf-8", errors="replace"), 2)

    toc1, body1 = render_volume(1, v1)
    toc2, body2 = render_volume(2, v2)

    total_parts = len(v1) + len(v2)
    total_chaps = sum(len(p[2]) for p in v1 + v2)
    total_paras = sum(len(c["paragraphs"]) for p in v1 + v2 for c in p[2])

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read al-Baladhuri's Futuh al-Buldan (The Origins of the Islamic State) in Philip K. Hitti's 1916 and F. C. Murgotten's 1924 English translation. Public domain, sourced from archive.org OCR.">
<title>al-Baladhuri — Analyzing Islam</title>
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
  .reader-toc li.toc-subsection {{
    list-style: none;
    margin-left: -12px;
    margin-top: 6px;
    font-family: var(--sans);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--text-dim);
    font-weight: 600;
  }}
  .reader-toc li.toc-subsection a {{
    color: var(--text-dim);
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
  .chapter {{
    margin: 48px 0;
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
  .baladhuri-para {{
    margin: 0 0 18px;
    line-height: 1.7;
    color: var(--text);
    max-width: 72ch;
  }}
  .baladhuri-para .para-num {{
    font-family: ui-monospace, "SF Mono", Consolas, monospace;
    font-size: 11px;
    color: var(--text-dim);
    margin-right: 10px;
    font-weight: 600;
  }}
  .ocr-notice {{
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

<div class="reader-layout">

  <aside class="reader-toc">
    <div class="reader-toc-header">Contents</div>
    <ol>
{toc1}
{toc2}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">Philip K. Hitti 1916 · F. C. Murgotten 1924 · Public domain</div>
      <h1>al-Balādhurī</h1>
      <p class="reader-intro"><em>Kitāb Futūḥ al-Buldān</em> — "The Book of the Conquests of the Lands." Al-Balādhurī's 9th-century history of the early Arab-Islamic conquests, in the two-volume English translation published by Columbia University as <em>The Origins of the Islamic State</em>: Philip K. Hitti (Vol. I, 1916) and F. C. Murgotten (Vol. II, 1924). Both volumes are public domain.</p>
      <div class="reader-cta">
        <a href="../read-external.html" class="btn">← External sources</a>
        <a href="https://archive.org/details/originsofislamic00balarich" class="btn" target="_blank" rel="noopener">Vol. 1 · archive.org</a>
        <a href="https://archive.org/details/originsofislamic02albauoft" class="btn" target="_blank" rel="noopener">Vol. 2 · archive.org</a>
      </div>
      <div class="ocr-notice">
        Text is the OCR output from the archive.org scans, lightly cleaned up (hyphenation rejoined, running headers removed). Occasional OCR noise is inevitable — cross-check passages against the source PDF before citing.
      </div>
    </header>

{body1}
{body2}
  </main>

</div>

<footer class="site-footer">
  Hitti's 1916 and Murgotten's 1924 translations of al-Balādhurī. Public domain. Sourced from archive.org OCR. Chapter/paragraph anchors: #vol{{N}}-p{{part}}-c{{chap}}-p{{para}}.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"  Parts: {total_parts}, Chapters: {total_chaps}, Paragraphs: {total_paras}")


if __name__ == "__main__":
    main()
