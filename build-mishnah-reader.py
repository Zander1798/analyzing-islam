#!/usr/bin/env python3
"""Build site/read-external/mishnah.html from the Sefaria v3 API, fetching
Joshua Kulp's "Mishnah Yomit" English translation (CC-BY).

This hits Sefaria's API once per tractate (63 requests). A small delay
between calls is polite. Results are cached under .tmp/mishnah/<tractate>.json
so reruns are instant.
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
CACHE_DIR = ROOT / ".tmp" / "mishnah"
OUT_PATH = ROOT / "site" / "read-external" / "mishnah.html"

SEDARIM = [
    ("Zera'im", "Seeds", [
        "Berakhot", "Peah", "Demai", "Kilayim", "Sheviit",
        "Terumot", "Maasrot", "Maaser Sheni", "Challah",
        "Orlah", "Bikkurim",
    ]),
    ("Mo'ed", "Appointed Seasons", [
        "Shabbat", "Eruvin", "Pesachim", "Shekalim", "Yoma",
        "Sukkah", "Beitzah", "Rosh Hashanah", "Taanit",
        "Megillah", "Moed Katan", "Chagigah",
    ]),
    ("Nashim", "Women", [
        "Yevamot", "Ketubot", "Nedarim", "Nazir", "Sotah",
        "Gittin", "Kiddushin",
    ]),
    ("Nezikin", "Damages", [
        "Bava Kamma", "Bava Metzia", "Bava Batra",
        "Sanhedrin", "Makkot", "Shevuot", "Eduyot",
        "Avodah Zarah", "Avot", "Horayot",
    ]),
    ("Kodashim", "Holy Things", [
        "Zevachim", "Menachot", "Chullin", "Bekhorot",
        "Arakhin", "Temurah", "Keritot", "Meilah",
        "Tamid", "Middot", "Kinnim",
    ]),
    ("Tahorot", "Purities", [
        "Kelim", "Oholot", "Negaim", "Parah", "Tahorot",
        "Mikvaot", "Niddah", "Makhshirin", "Zavim",
        "Tevul Yom", "Yadayim", "Oktzin",
    ]),
]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def sefaria_slug(name: str) -> str:
    # Sefaria expects "Mishnah_Bava_Kamma" etc.
    return "Mishnah_" + name.replace(" ", "_")


def fetch_tractate(name: str):
    cache = CACHE_DIR / f"{name.replace(' ', '_')}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    slug = sefaria_slug(name)
    # Sefaria v3: pull Kulp English specifically
    url = (
        f"https://www.sefaria.org/api/v3/texts/{urllib.parse.quote(slug)}"
        f"?version=english|Mishnah_Yomit_by_Dr._Joshua_Kulp"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def clean_mishnah_text(text: str) -> str:
    """Allow-list the HTML tags the Sefaria text uses (<b>, <i>, <br>).
    Everything else: escape."""
    # First, replace <br> with a space (we render as one paragraph).
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text).strip()
    # Escape everything, then re-unescape the allowed tags.
    esc_text = html.escape(text, quote=False)
    esc_text = re.sub(
        r"&lt;(/?)(i|b|em|strong)&gt;",
        r"<\1\2>",
        esc_text,
        flags=re.IGNORECASE,
    )
    return esc_text


def extract_chapters(api_response, tractate_name):
    """Sefaria v3 returns versions[0].text which is a 2D array:
    [chapter_index][mishnah_index]. Returns list of [(chap, mishnah, text), ...]."""
    versions = api_response.get("versions", [])
    if not versions:
        return []
    text = versions[0].get("text", [])
    out = []
    for c_idx, chapter in enumerate(text, start=1):
        for m_idx, mishnah_text in enumerate(chapter, start=1):
            if not mishnah_text:
                continue
            if isinstance(mishnah_text, list):
                mishnah_text = " ".join(t for t in mishnah_text if t)
            if isinstance(mishnah_text, str) and mishnah_text.strip():
                out.append((c_idx, m_idx, mishnah_text))
    return out


def main():
    toc_rows = []
    body_blocks = []
    total_mishnayot = 0
    total_tractates = 0
    failed = []

    for seder_idx, (seder, seder_en, tractates) in enumerate(SEDARIM, start=1):
        toc_rows.append(
            f'<li class="toc-section"><span class="toc-section-label">Seder {esc(seder)} · {esc(seder_en)}</span></li>'
        )
        body_blocks.append(
            f'  <header class="reader-section-heading">\n'
            f'    <div class="reader-section-eyebrow">Seder {esc(seder)}</div>\n'
            f'    <h2>{esc(seder_en)}</h2>\n'
            f'  </header>\n'
        )
        for tractate_name in tractates:
            try:
                data = fetch_tractate(tractate_name)
                chapters = extract_chapters(data, tractate_name)
            except Exception as e:
                print(f"  FAILED {tractate_name}: {e}", file=sys.stderr)
                failed.append(tractate_name)
                continue
            if not chapters:
                print(f"  EMPTY {tractate_name}", file=sys.stderr)
                failed.append(tractate_name)
                continue

            total_tractates += 1
            slug = tractate_name.lower().replace(" ", "-")
            toc_rows.append(
                f'<li><a href="#{slug}"><span class="toc-num">·</span> '
                f'<span class="toc-name">{esc(tractate_name)}</span></a></li>'
            )
            # Group by chapter
            grouped = {}
            for c, m, text in chapters:
                grouped.setdefault(c, []).append((m, text))

            body_blocks.append(
                f'  <article class="surah" id="{slug}">\n'
                f'    <header class="surah-header">\n'
                f'      <div class="surah-num">{tractate_name[:3].upper()}</div>\n'
                f'      <h2 class="surah-title">{esc(tractate_name)}</h2>\n'
                f'      <p class="surah-subtitle">Seder {esc(seder)} · {len(grouped)} chapters</p>\n'
                f'    </header>\n'
            )
            for chap_num in sorted(grouped.keys()):
                body_blocks.append(
                    f'    <section class="chapter" id="{slug}-{chap_num}">\n'
                    f'      <h3 class="chapter-title">'
                    f'<span class="chapter-num">Chapter {chap_num}</span></h3>\n'
                    f'      <ol class="verses">\n'
                )
                for m_num, text in grouped[chap_num]:
                    total_mishnayot += 1
                    cleaned = clean_mishnah_text(text)
                    body_blocks.append(
                        f'        <li id="{slug}-{chap_num}-{m_num}" value="{m_num}">'
                        f'<span class="verse-number">{m_num}</span>'
                        f'<span class="verse-text">{cleaned}</span></li>\n'
                    )
                body_blocks.append('      </ol>\n    </section>\n')
            body_blocks.append('  </article>\n')

            time.sleep(0.2)  # polite delay between Sefaria hits

    toc_html = "\n".join(toc_rows)
    body_html = "".join(body_blocks)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read the complete Mishnah in Dr. Joshua Kulp's English translation — all 63 tractates across the six Sedarim. CC-BY via Sefaria.">
<title>The Mishnah — Analyzing Islam</title>
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
    <div class="reader-toc-header">Tractates</div>
    <ol>
{toc_html}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">Dr. Joshua Kulp · Mishnah Yomit · CC-BY via Sefaria</div>
      <h1>The Mishnah</h1>
      <p class="reader-intro">The foundational Jewish legal text, redacted ca. 200 CE. {total_mishnayot} mishnayot across {total_tractates} tractates grouped into the six Sedarim (Orders). English translation by Dr. Joshua Kulp, served by Sefaria under a Creative Commons Attribution license. Cited across the catalog for parallels and source material behind Quranic legal and narrative passages (notably Mishnah Sanhedrin 4:5 and Q 5:32).</p>
      <div class="reader-cta">
        <a href="../read-external.html" class="btn">← External sources</a>
        <a href="https://www.sefaria.org/texts/Mishnah" class="btn" target="_blank" rel="noopener">Sefaria</a>
      </div>
    </header>

{body_html}
  </main>

</div>

<footer class="site-footer">
  Mishnah Yomit by Dr. Joshua Kulp. CC-BY, via Sefaria. Anchors: #{{tractate-slug}}-{{chapter}}-{{mishnah}} (e.g. #sanhedrin-4-5).
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT_PATH}: {total_mishnayot} mishnayot across {total_tractates} tractates")
    if failed:
        print(f"Failed/empty: {failed}")


if __name__ == "__main__":
    main()
