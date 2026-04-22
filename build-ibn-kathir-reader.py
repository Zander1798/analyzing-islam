#!/usr/bin/env python3
"""Build the Tafsir Ibn Kathir reader (Abridged Darussalam edition).

Source:  'Tafsir Ibn Kathir all 10 volumes.pdf' sitting in repo root.
Output:  site/read-external/ibn-kathir.html         (index page)
         site/read-external/ibn-kathir-1.html … -10  (per-volume readers)

The PDF is 5,698 pages and extracts cleanly as English text. Garbled
Arabic presentation forms are stripped; common PDF artifacts
("S atan", "Ibn Kath ir", backtick-for-apostrophe, hyphen line wraps)
are cleaned. Within each volume every paragraph is emitted as a <p>,
and every inline Qurʾān verse reference of the form (N:M) or (N:M-P)
is turned into a link to ../read/quran.html#s{N}v{M}.

Volume boundaries are page-range based (equal splits across 5,698
pages) rather than content-based, because the PDF offers no reliable
volume-break marker after extraction. Fine for a reading experience —
users navigate by TOC, not by page number.
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
PDF_PATH = ROOT / "Tafsir Ibn Kathir all 10 volumes.pdf"
OUT_DIR = ROOT / "site" / "read-external"
CACHE_FILE = ROOT / ".tmp" / "sources" / "ibn-kathir" / "full.txt"


# ---------- PDF extraction ----------

def extract_all_pages() -> list[str]:
    """Return a list of page-text strings (length 5,698 for this PDF)."""
    if CACHE_FILE.exists():
        # Cache format: one page per "\x0c" (form-feed) delimiter.
        raw = CACHE_FILE.read_text(encoding="utf-8")
        return raw.split("\x0c")

    import pypdf
    reader = pypdf.PdfReader(str(PDF_PATH))
    pages = []
    for i, p in enumerate(reader.pages):
        pages.append(p.extract_text() or "")
        if (i + 1) % 500 == 0:
            print(f"  extracted {i+1}/{len(reader.pages)} pages", flush=True)
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text("\x0c".join(pages), encoding="utf-8")
    return pages


# ---------- Text cleaning ----------

# Arabic Unicode blocks we want gone — the extraction produces scrambled
# presentation-form characters that aren't meaningful prose.
ARABIC_RANGES = re.compile(
    r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]+"
)

# The most common PDF-extraction artifact on this file is a lone space
# inside a word, typically before a capital or after an opening letter.
# These fixes are deliberately narrow — global "remove-spaces-between-
# words" would eat real text.
WORD_REPAIRS = [
    # single-capital-stranded-at-start-of-word: "S atan" -> "Satan"
    (re.compile(r"\b([A-Z])\s([a-z]{2,})\b"), r"\1\2"),
    # "Isti` adhah" style — backtick + space inside a word
    (re.compile(r"(\w)`\s(\w)"), r"\1'\2"),
    # "Al-A` raf" — hyphenated capital then backtick-space
    (re.compile(r"(\w)`\s+(\w)"), r"\1'\2"),
    # Lone backtick used as apostrophe
    (re.compile(r"`"), "'"),
    # "Ibn Kath ir" -> "Ibn Kathir" (common 3-letter-split name case)
    (re.compile(r"\bKath\s+ir\b"), "Kathir"),
    # Hyphen line-wrap: "com-\nmentary" -> "commentary"
    (re.compile(r"-\s*\n\s*"), ""),
    # Double spaces -> single
    (re.compile(r"[ \t]{2,}"), " "),
]

# Collapse multiple blank lines, strip trailing spaces per line.
PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")


def clean_text(s: str) -> str:
    s = ARABIC_RANGES.sub("", s)
    for pat, repl in WORD_REPAIRS:
        s = pat.sub(repl, s)
    # Trim spaces on each line
    s = "\n".join(line.rstrip() for line in s.split("\n"))
    return s


# ---------- Verse-reference linkification ----------

# Matches (N:M) and (N:M-P) where 1 <= N <= 114 and M,P reasonable ayah numbers.
VERSE_REF = re.compile(r"\((\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?\)")


def linkify_verses(text_html: str) -> str:
    """Replace (N:M) in the already-escaped HTML with a link to the reader.
    Only replaces sensible surah numbers (1..114) and ayah numbers (1..286)."""
    def repl(m: re.Match) -> str:
        n = int(m.group(1))
        a = int(m.group(2))
        b = int(m.group(3)) if m.group(3) else None
        if not (1 <= n <= 114):
            return m.group(0)
        if not (1 <= a <= 286):
            return m.group(0)
        href = f"../read/quran.html#s{n}v{a}"
        label = f"{n}:{a}-{b}" if b else f"{n}:{a}"
        return f'(<a class="tafsir-ref" href="{href}">{label}</a>)'
    return VERSE_REF.sub(repl, text_html)


# ---------- Paragraph assembly ----------

# Lines under this length that don't end in sentence punctuation are
# joined with the next line (PDF wrap lines).
WRAP_LINE_LIMIT = 78
SENTENCE_END = re.compile(r"[.!?:;,\"']\s*$")


def reflow_paragraphs(text: str) -> list[str]:
    """Turn a slab of cleaned text into a list of paragraph strings."""
    paragraphs = []
    current = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        if current and not SENTENCE_END.search(current[-1]) and len(current[-1]) < WRAP_LINE_LIMIT * 2:
            current.append(line)
        else:
            if current:
                paragraphs.append(" ".join(current).strip())
            current = [line]
    if current:
        paragraphs.append(" ".join(current).strip())
    # Drop paragraphs that are garbage (e.g., page numbers, isolated digits)
    paragraphs = [p for p in paragraphs if len(p) > 4 and not p.isdigit()]
    return paragraphs


# ---------- Volume definitions ----------

# (volume_num, first_page, last_page, surah_range_label)
TOTAL_PAGES = 5698
VOLUME_META = [
    (1,  "Surahs 1–2 (al-Fātiḥah, al-Baqarah)"),
    (2,  "Surahs 3–4 (Āli ʿImrān, an-Nisāʾ)"),
    (3,  "Surahs 5–6 (al-Māʾidah, al-Anʿām)"),
    (4,  "Surahs 7–9 (al-Aʿrāf, al-Anfāl, at-Tawbah)"),
    (5,  "Surahs 10–14 (Yūnus — Ibrāhīm)"),
    (6,  "Surahs 15–21 (al-Ḥijr — al-Anbiyāʾ)"),
    (7,  "Surahs 22–29 (al-Ḥajj — al-ʿAnkabūt)"),
    (8,  "Surahs 30–39 (ar-Rūm — az-Zumar)"),
    (9,  "Surahs 40–51 (Ghāfir — adh-Dhāriyāt)"),
    (10, "Surahs 52–114 (aṭ-Ṭūr — an-Nās)"),
]


def volume_page_ranges() -> list[tuple[int, int]]:
    """Split the 5,698 pages into 10 equal-ish chunks. Vol 1 starts at
    page index 18 so the 17-page 'Biography of Ibn Kathir' frontmatter
    sits on the index page, not inside Vol 1."""
    FRONT_MATTER = 17
    body_pages = TOTAL_PAGES - FRONT_MATTER
    chunk = body_pages // 10
    ranges = []
    start = FRONT_MATTER
    for v in range(10):
        end = start + chunk if v < 9 else TOTAL_PAGES
        ranges.append((start, end))
        start = end
    return ranges


# ---------- HTML shells ----------

def esc(s: str) -> str:
    return html.escape(s, quote=False)


NAV_HTML = """
<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
      <a href="../index.html">Home</a>
      <a href="../catalog.html">Catalog</a>
      <a href="../read.html">Read</a>
      <a href="../about.html">About</a>
      <a href="../faq.html">FAQ</a>
    </div>
  </div>
</nav>
"""


INDEX_STYLE = """
.ibnk-hero { max-width: 820px; margin: 40px auto 20px; padding: 0 24px; }
.ibnk-hero h1 { font-family: var(--serif); font-size: 44px; line-height: 1.1; margin: 0 0 14px; letter-spacing: -0.02em; }
.ibnk-hero .ibnk-meta { font-size: 11px; text-transform: uppercase; letter-spacing: 0.2em; color: var(--text-dim); margin-bottom: 18px; }
.ibnk-hero p { color: var(--text-muted); font-size: 15px; line-height: 1.7; }
.ibnk-volumes { max-width: 820px; margin: 36px auto 120px; padding: 0 24px; border-top: 1px solid var(--border); }
.ibnk-volumes a.ibnk-vol {
  display: flex;
  align-items: baseline;
  gap: 18px;
  padding: 22px 0;
  border-bottom: 1px solid var(--border);
  color: var(--text);
  text-decoration: none;
  transition: background 0.2s;
}
.ibnk-volumes a.ibnk-vol:hover { background: var(--panel); text-decoration: none; }
.ibnk-volumes .vol-num {
  font-family: var(--serif);
  font-size: 28px;
  color: var(--text-dim);
  width: 72px;
  flex-shrink: 0;
}
.ibnk-volumes .vol-title {
  font-family: var(--serif);
  font-size: 20px;
  color: var(--text);
}
.ibnk-volumes .vol-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
  text-transform: none;
  letter-spacing: 0;
}
"""


VOLUME_STYLE = """
.ibnk-wrap { max-width: 820px; margin: 40px auto 120px; padding: 0 24px; }
.ibnk-wrap .ibnk-topbar {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--text-dim);
  margin-bottom: 18px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 12px;
}
.ibnk-wrap .ibnk-topbar a { color: var(--text-muted); }
.ibnk-wrap .ibnk-topbar a:hover { color: var(--text); }
.ibnk-wrap h1 {
  font-family: var(--serif);
  font-size: 40px;
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin: 0 0 6px;
}
.ibnk-wrap .ibnk-subtitle {
  font-family: var(--serif);
  font-style: italic;
  color: var(--text-muted);
  font-size: 16px;
  margin-bottom: 36px;
}
.ibnk-wrap .ibnk-body p {
  color: var(--text);
  font-size: 15px;
  line-height: 1.75;
  margin: 0 0 18px;
}
.ibnk-wrap .tafsir-ref {
  color: var(--accent);
  border-bottom: 1px dotted var(--accent);
  padding-bottom: 0;
}
.ibnk-wrap .tafsir-ref:hover { color: var(--accent-hover); border-bottom-style: solid; }
.ibnk-footnav {
  max-width: 820px;
  margin: 60px auto 0;
  padding: 24px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  border-top: 1px solid var(--border);
}
.ibnk-footnav a { font-size: 12px; text-transform: uppercase; letter-spacing: 0.18em; color: var(--text-muted); }
.ibnk-footnav a:hover { color: var(--text); }
"""


def render_index(volumes: list[tuple[int, str]]) -> str:
    rows = []
    for num, label in volumes:
        rows.append(
            f'<a class="ibnk-vol" href="ibn-kathir-{num}.html">'
            f'<span class="vol-num">{num}</span>'
            f'<span class="vol-title">Volume {num}<br>'
            f'<span class="vol-sub">{esc(label)}</span></span>'
            f'</a>'
        )
    volumes_html = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Tafsir Ibn Kathir — classical Sunni commentary on the Qurʾān, Darussalam abridged English edition. All 10 volumes.">
<title>Tafsir Ibn Kathir — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<style>{INDEX_STYLE}</style>
</head>
<body>
{NAV_HTML}

<header class="ibnk-hero">
  <div class="ibnk-meta">Classical Sunni commentary · English · Darussalam abridged</div>
  <h1>Tafsir Ibn Kathir</h1>
  <p>
    Abū al-Fidāʾ Ismāʿīl ibn Kathīr's (d. 774 AH / 1373 CE) verse-by-verse commentary on
    the Qurʾān — the most widely cited tafsir in mainstream Sunni scholarship. This is
    the 10-volume Darussalam abridged English edition by Shaykh Ṣafiur Raḥmān al-Mubārakpūrī.
    Every inline verse reference of the form <em>(N:M)</em> links to the corresponding
    verse in <a href="../read/quran.html">our Qurʾān reader</a>.
  </p>
</header>

<section class="ibnk-volumes">
{volumes_html}
</section>

<footer class="site-footer">
  Text extracted from the Darussalam edition PDF. Garbled Arabic presentation forms
  have been stripped; the English prose is preserved as-is.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def render_volume(num: int, label: str, body_html: str, prev_vol: int | None, next_vol: int | None) -> str:
    prev_link = (
        f'<a href="ibn-kathir-{prev_vol}.html">← Volume {prev_vol}</a>'
        if prev_vol else '<a href="ibn-kathir.html">← All volumes</a>'
    )
    next_link = (
        f'<a href="ibn-kathir-{next_vol}.html">Volume {next_vol} →</a>'
        if next_vol else '<a href="ibn-kathir.html">All volumes →</a>'
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Tafsir Ibn Kathir, Volume {num} — {esc(label)}. Classical Sunni commentary on the Qurʾān, Darussalam abridged English edition.">
<title>Tafsir Ibn Kathir · Volume {num} — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<style>{VOLUME_STYLE}</style>
</head>
<body>
{NAV_HTML}

<article class="ibnk-wrap">
  <div class="ibnk-topbar">
    <a href="ibn-kathir.html">← All volumes</a>
    <span>Tafsir Ibn Kathir</span>
  </div>
  <h1>Volume {num}</h1>
  <div class="ibnk-subtitle">{esc(label)}</div>
  <div class="ibnk-body">
{body_html}
  </div>
</article>

<nav class="ibnk-footnav">
  {prev_link}
  {next_link}
</nav>

<footer class="site-footer">
  Text extracted from the Darussalam 10-volume abridged edition. Inline <em>(N:M)</em> verse references link to the Qurʾān reader.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


# ---------- Main ----------

def main() -> None:
    if not PDF_PATH.exists():
        sys.exit(f"Missing PDF: {PDF_PATH}")

    print("Extracting PDF text...")
    pages = extract_all_pages()
    print(f"  {len(pages)} pages extracted")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ranges = volume_page_ranges()

    # Render index
    (OUT_DIR / "ibn-kathir.html").write_text(
        render_index(VOLUME_META), encoding="utf-8"
    )
    print(f"Wrote {OUT_DIR / 'ibn-kathir.html'}")

    for i, (num, label) in enumerate(VOLUME_META):
        start, end = ranges[i]
        raw = "\n".join(pages[start:end])
        cleaned = clean_text(raw)
        paragraphs = reflow_paragraphs(cleaned)
        body_bits = []
        for p in paragraphs:
            escaped = esc(p)
            linked = linkify_verses(escaped)
            body_bits.append(f"    <p>{linked}</p>")
        body_html = "\n".join(body_bits)
        prev_vol = num - 1 if num > 1 else None
        next_vol = num + 1 if num < 10 else None
        out = OUT_DIR / f"ibn-kathir-{num}.html"
        out.write_text(
            render_volume(num, label, body_html, prev_vol, next_vol),
            encoding="utf-8"
        )
        print(f"  Wrote {out.name}: pages {start+1}-{end}, {len(paragraphs)} paragraphs")


if __name__ == "__main__":
    main()
