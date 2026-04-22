#!/usr/bin/env python3
"""Build volume-picker and per-volume PDF reader pages for the multi-volume
Darussalam editions (Nasa'i 1-6, Ibn Majah 1-5).

Writes:
  site/read/<slug>.html            (volume picker)
  site/read/<slug>-v{N}.html       (per-volume PDF reader with fullscreen)
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
READ_DIR = ROOT / "site" / "read"

SOURCES = [
    {
        "slug": "nasai",
        "folder": "nasai-vols",
        "title": "Sunan an-Nasāʾī",
        "description_html": (
            "Compiled by al-Nasāʾī (d. 915 CE). Known for strict standards in the "
            "selection of narrators. About 5,760 hadiths across six volumes, Darussalam "
            "English+Arabic edition."
        ),
        "volumes": [
            (1, "Hadiths 1–876"),
            (2, "Hadiths 877–1818"),
            (3, "Hadiths 1819–3086"),
            (4, "Hadiths 3087–3970"),
            (5, "Hadiths 3971–4987"),
            (6, "Hadiths 4988–5761"),
        ],
    },
    {
        "slug": "ibn-majah",
        "folder": "ibn-majah-vols",
        "title": "Sunan Ibn Mājah",
        "description_html": (
            "Compiled by Ibn Mājah (d. 887 CE). The last-added of the six canonical "
            "collections; contains some hadiths not found in the others. About 4,340 "
            "hadiths across five volumes, Darussalam English+Arabic edition."
        ),
        "volumes": [
            (1, "Hadiths 1–802"),
            (2, "Hadiths 803–1782"),
            (3, "Hadiths 1783–2718"),
            (4, "Hadiths 2719–3656"),
            (5, "Hadiths 3657–4341"),
        ],
    },
]


PICKER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read {title} — pick a volume.">
<title>Read {title} — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<style>
  /* Inherit the editorial index-list look from read.html */
  .vol-index {{
    border-top: 1px solid var(--border);
    margin: 48px 0 64px;
  }}
  .vol-row {{
    display: grid;
    grid-template-columns: 72px 1fr auto;
    align-items: center;
    gap: 32px;
    padding: 28px 4px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    text-decoration: none;
    transition: padding-left 0.3s, color 0.2s;
  }}
  .vol-row:hover {{
    padding-left: 24px;
    text-decoration: none;
  }}
  .vol-row:hover .vol-arrow {{
    opacity: 1;
    transform: translateX(4px);
  }}
  .vol-num {{
    font-family: ui-monospace, "SF Mono", Consolas, monospace;
    font-size: 12px;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    font-weight: 600;
    padding-top: 10px;
    align-self: start;
  }}
  .vol-title {{
    font-family: var(--serif);
    font-size: clamp(28px, 3.4vw, 44px);
    line-height: 1;
    letter-spacing: -0.02em;
    font-weight: 700;
    color: var(--text);
    display: block;
  }}
  .vol-meta {{
    display: block;
    font-family: var(--sans);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--text-dim);
    font-weight: 600;
    margin-top: 10px;
  }}
  .vol-arrow {{
    font-family: var(--serif);
    font-size: 24px;
    color: var(--text-muted);
    opacity: 0.4;
    transition: opacity 0.25s, transform 0.25s;
    line-height: 1;
  }}
  @media (max-width: 640px) {{
    .vol-row {{ grid-template-columns: 48px 1fr auto; gap: 16px; padding: 22px 4px; }}
    .vol-title {{ font-size: clamp(22px, 8vw, 32px); }}
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

  <section class="hero" style="padding: 40px 0 12px; text-align:left;">
    <h1 style="font-size:clamp(44px, 6vw, 72px); margin-bottom:16px;">{title}</h1>
    <p class="hero-tagline" style="margin-left:0; max-width:640px;">{description_html}</p>
    <div class="hero-cta" style="margin-top:20px;">
      <a href="../read.html" class="btn">← All sources</a>
    </div>
  </section>

  <div class="vol-index">
{rows}
  </div>

</main>

<footer class="site-footer">
  Read the text, then read the catalog. Every entry references a specific passage — verify before citing.
</footer>

<script src="../assets/js/pdf-mobile.js" defer></script>
<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


VOL_ROW_TEMPLATE = """    <a href="{slug}-v{num}.html" class="vol-row">
      <span class="vol-num">{num_pad}</span>
      <span>
        <span class="vol-title">Volume {num}</span>
        <span class="vol-meta">{meta}</span>
      </span>
      <span class="vol-arrow" aria-hidden="true">→</span>
    </a>"""


VOL_READER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read {title} — Volume {num} ({meta}).">
<title>{title} Vol. {num} — Analyzing Islam</title>
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

<div class="pdf-reader-layout">

  <div class="pdf-reader-header">
    <div>
      <div class="pdf-reader-meta">{title} · Volume {num} · Darussalam English+Arabic edition</div>
      <h1>{title} — Vol. {num}</h1>
      <p>{meta}. Scanned PDF; use the Fullscreen button for a full-screen reading view, or download the PDF.</p>
    </div>
    <div class="pdf-reader-actions">
      <a href="{slug}.html" class="btn">← All volumes</a>
      <button type="button" class="btn" id="fullscreen-btn">⛶ Fullscreen</button>
      <a href="../assets/sources/{folder}/v{num}.pdf" class="btn" download>Download PDF</a>
    </div>
  </div>

  <iframe class="pdf-reader-frame" id="pdf-frame" src="../assets/sources/{folder}/v{num}.pdf" title="{title} Volume {num}"></iframe>

</div>

<script>
  document.getElementById('fullscreen-btn').addEventListener('click', function () {{
    var el = document.getElementById('pdf-frame');
    if (el.requestFullscreen) el.requestFullscreen();
    else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    else if (el.msRequestFullscreen) el.msRequestFullscreen();
  }});
</script>

<footer class="site-footer">
  Built from the Darussalam English edition of {title}, Volume {num}. Every entry references a specific hadith — verify before citing.
</footer>

<script src="../assets/js/pdf-mobile.js" defer></script>
<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def build(src):
    slug = src["slug"]
    # Picker page
    rows = "\n".join(
        VOL_ROW_TEMPLATE.format(slug=slug, num=num, num_pad=f"{num:02d}", meta=meta)
        for num, meta in src["volumes"]
    )
    picker_html = PICKER_TEMPLATE.format(
        title=src["title"],
        description_html=src["description_html"],
        rows=rows,
    )
    picker_path = READ_DIR / f"{slug}.html"
    picker_path.write_text(picker_html, encoding="utf-8")
    print(f"  wrote picker: {picker_path}")

    # Per-volume reader pages
    for num, meta in src["volumes"]:
        reader_html = VOL_READER_TEMPLATE.format(
            slug=slug,
            num=num,
            meta=meta,
            title=src["title"],
            folder=src["folder"],
        )
        reader_path = READ_DIR / f"{slug}-v{num}.html"
        reader_path.write_text(reader_html, encoding="utf-8")
        print(f"  wrote reader: {reader_path}")


def main():
    for src in SOURCES:
        print(f"\n{src['title']}:")
        build(src)


if __name__ == "__main__":
    main()
