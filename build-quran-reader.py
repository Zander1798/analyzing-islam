#!/usr/bin/env python3
"""Build site/read/quran.html from clean JSON source.

Source: quran-json/chapters/{1..114}.json from npm package quran-json@3.1.2,
which bundles the Saheeh International English translation (tanzil.net origin)
alongside Arabic text and transliteration.

The previous builder parsed a PDF and carried its artifacts. This one emits
the same HTML shape (verse anchors #s{surah}v{verse}, .verses list, .surah
article) — so every existing inbound link from catalog entries still resolves.

Polished transliterated surah names are kept from the old builder's SURAH_META
table, since the JSON's "transliteration" field is plain ASCII.
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
CHAPTERS_DIR = ROOT / "quran-json" / "chapters"
OUT_PATH = ROOT / "site" / "read" / "quran.html"

# (number, transliterated_name, english_meaning) — verse counts come from JSON.
SURAH_META = [
    (1, "al-Fātiḥah", "The Opening"),
    (2, "al-Baqarah", "The Cow"),
    (3, "Āli ʿImrān", "The Family of ʿImrān"),
    (4, "an-Nisāʾ", "The Women"),
    (5, "al-Māʾidah", "The Table Spread"),
    (6, "al-Anʿām", "The Cattle"),
    (7, "al-Aʿrāf", "The Heights"),
    (8, "al-Anfāl", "The Spoils of War"),
    (9, "at-Tawbah", "The Repentance"),
    (10, "Yūnus", "Jonah"),
    (11, "Hūd", "Hud"),
    (12, "Yūsuf", "Joseph"),
    (13, "ar-Raʿd", "The Thunder"),
    (14, "Ibrāhīm", "Abraham"),
    (15, "al-Ḥijr", "The Rocky Tract"),
    (16, "an-Naḥl", "The Bee"),
    (17, "al-Isrāʾ", "The Night Journey"),
    (18, "al-Kahf", "The Cave"),
    (19, "Maryam", "Mary"),
    (20, "Ṭā Hā", "Ta Ha"),
    (21, "al-Anbiyāʾ", "The Prophets"),
    (22, "al-Ḥajj", "The Pilgrimage"),
    (23, "al-Muʾminūn", "The Believers"),
    (24, "an-Nūr", "The Light"),
    (25, "al-Furqān", "The Criterion"),
    (26, "ash-Shuʿarāʾ", "The Poets"),
    (27, "an-Naml", "The Ants"),
    (28, "al-Qaṣaṣ", "The Stories"),
    (29, "al-ʿAnkabūt", "The Spider"),
    (30, "ar-Rūm", "The Romans"),
    (31, "Luqmān", "Luqman"),
    (32, "as-Sajdah", "The Prostration"),
    (33, "al-Aḥzāb", "The Combined Forces"),
    (34, "Sabaʾ", "Sheba"),
    (35, "Fāṭir", "The Originator"),
    (36, "Yā Seen", "Ya Seen"),
    (37, "aṣ-Ṣāffāt", "Those Lined Up"),
    (38, "Ṣād", "Sad"),
    (39, "az-Zumar", "The Groups"),
    (40, "Ghāfir", "The Forgiver"),
    (41, "Fuṣṣilat", "Explained in Detail"),
    (42, "ash-Shūrā", "The Consultation"),
    (43, "az-Zukhruf", "The Gold Adornments"),
    (44, "ad-Dukhān", "The Smoke"),
    (45, "al-Jāthiyah", "The Kneeling"),
    (46, "al-Aḥqāf", "The Curved Sand-Dunes"),
    (47, "Muḥammad", "Muhammad"),
    (48, "al-Fatḥ", "The Victory"),
    (49, "al-Ḥujurāt", "The Inner Apartments"),
    (50, "Qāf", "Qaf"),
    (51, "adh-Dhāriyāt", "The Winds That Scatter"),
    (52, "aṭ-Ṭūr", "The Mount"),
    (53, "an-Najm", "The Star"),
    (54, "al-Qamar", "The Moon"),
    (55, "ar-Raḥmān", "The Most Merciful"),
    (56, "al-Wāqiʿah", "The Inevitable"),
    (57, "al-Ḥadīd", "Iron"),
    (58, "al-Mujādilah", "The Disputer"),
    (59, "al-Ḥashr", "The Gathering"),
    (60, "al-Mumtaḥanah", "The Woman Examined"),
    (61, "aṣ-Ṣaff", "The Row"),
    (62, "al-Jumuʿah", "Friday"),
    (63, "al-Munāfiqūn", "The Hypocrites"),
    (64, "at-Taghābun", "Mutual Disillusion"),
    (65, "aṭ-Ṭalāq", "Divorce"),
    (66, "at-Taḥreem", "The Prohibition"),
    (67, "al-Mulk", "The Sovereignty"),
    (68, "al-Qalam", "The Pen"),
    (69, "al-Ḥāqqah", "The Reality"),
    (70, "al-Maʿārij", "The Ways of Ascent"),
    (71, "Nūḥ", "Noah"),
    (72, "al-Jinn", "The Jinn"),
    (73, "al-Muzzammil", "The Enwrapped"),
    (74, "al-Muddaththir", "The Cloaked"),
    (75, "al-Qiyāmah", "The Resurrection"),
    (76, "al-Insān", "Man"),
    (77, "al-Mursalāt", "Those Sent Forth"),
    (78, "an-Nabaʾ", "The Tidings"),
    (79, "an-Nāziʿāt", "Those Who Pull Out"),
    (80, "ʿAbasa", "He Frowned"),
    (81, "at-Takweer", "The Folding Up"),
    (82, "al-Infiṭār", "The Cleaving"),
    (83, "al-Muṭaffifeen", "The Defrauders"),
    (84, "al-Inshiqāq", "The Splitting Open"),
    (85, "al-Burūj", "The Mansions of the Stars"),
    (86, "aṭ-Ṭāriq", "The Night-Comer"),
    (87, "al-Aʿlā", "The Most High"),
    (88, "al-Ghāshiyah", "The Overwhelming"),
    (89, "al-Fajr", "The Dawn"),
    (90, "al-Balad", "The City"),
    (91, "ash-Shams", "The Sun"),
    (92, "al-Layl", "The Night"),
    (93, "aḍ-Ḍuḥā", "The Morning Hours"),
    (94, "ash-Sharḥ", "The Opening Forth"),
    (95, "at-Teen", "The Fig"),
    (96, "al-ʿAlaq", "The Clot"),
    (97, "al-Qadr", "The Decree"),
    (98, "al-Bayyinah", "The Clear Evidence"),
    (99, "az-Zalzalah", "The Earthquake"),
    (100, "al-ʿĀdiyāt", "The Runners"),
    (101, "al-Qāriʿah", "The Striking Hour"),
    (102, "at-Takāthur", "The Piling Up"),
    (103, "al-ʿAṣr", "The Time"),
    (104, "al-Humazah", "The Slanderer"),
    (105, "al-Feel", "The Elephant"),
    (106, "Quraysh", "Quraysh"),
    (107, "al-Māʿūn", "Small Kindnesses"),
    (108, "al-Kawthar", "Abundance"),
    (109, "al-Kāfirūn", "The Disbelievers"),
    (110, "an-Naṣr", "The Help"),
    (111, "al-Masad", "The Palm Fibre"),
    (112, "al-Ikhlāṣ", "The Sincerity"),
    (113, "al-Falaq", "The Daybreak"),
    (114, "an-Nās", "Mankind"),
]


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def load_chapter(n: int) -> dict:
    return json.loads((CHAPTERS_DIR / f"{n}.json").read_text(encoding="utf-8"))


def render_surah(n: int, translit: str, meaning: str, chapter: dict) -> str:
    verses = chapter["verses"]
    verse_count = chapter.get("total_verses", len(verses))
    # Every sūrah has Bismillāh before it, except sūrah 1 (which starts with it
    # as verse 1) and sūrah 9 (which begins without the Basmala).
    show_bismillah = n not in (1, 9)

    parts = [
        f'<article class="surah" id="surah-{n}">',
        '  <header class="surah-header">',
        f'    <div class="surah-number">Sūrah {n}</div>',
        f'    <h2>{esc(translit)}</h2>',
        f'    <div class="surah-subtitle">{esc(meaning)} · {verse_count} verses</div>',
    ]
    if show_bismillah:
        parts.append('    <div class="surah-bismillah">Bismillāhir-Raḥmānir-Raḥeem</div>')
    parts.append('  </header>')
    parts.append('  <ol class="verses">')
    for v in verses:
        vid = v["id"]
        text = (v.get("translation") or "").strip()
        arabic = (v.get("text") or "").strip()
        # Replace "Allah" with "Allāh" to match the polished transliteration
        # style used everywhere else on the site.
        text = text.replace("Allah", "Allāh").replace("Muhammad", "Muḥammad")
        parts.append(
            f'      <li id="s{n}v{vid}" value="{vid}">'
            f'<span class="verse-number">{vid}</span>'
            f'<span class="verse-text">{esc(text)}</span>'
            f'<span class="verse-arabic" lang="ar" dir="rtl">{esc(arabic)}</span>'
            f'</li>'
        )
    parts.append('  </ol>')
    parts.append('</article>')
    return "\n".join(parts)


def render_toc() -> str:
    rows = []
    for n, translit, _meaning in SURAH_META:
        rows.append(
            f'<li><a href="#surah-{n}"><span class="toc-num">{n}</span> '
            f'<span class="toc-name">{esc(translit)}</span></a></li>'
        )
    return "\n".join(rows)


def main() -> None:
    if not CHAPTERS_DIR.exists():
        sys.exit(f"Missing source dir: {CHAPTERS_DIR}")

    toc_html = render_toc()
    surah_blocks = []
    total_verses = 0
    for n, translit, meaning in SURAH_META:
        chapter = load_chapter(n)
        total_verses += chapter.get("total_verses", len(chapter["verses"]))
        surah_blocks.append(render_surah(n, translit, meaning, chapter))

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read the complete Quran in the Saheeh International English translation. All 114 surahs, verse by verse.">
<title>Read the Quran — Analyzing Islam</title>
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

<div class="reader-layout">

  <aside class="reader-toc">
    <div class="reader-toc-header">Sūrahs</div>
    <ol>
{toc_html}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">Saheeh International · English translation</div>
      <h1>The Qurʾān</h1>
      <p class="reader-intro">The complete text, all 114 sūrahs, {total_verses} verses. English by Saheeh International (Umm Muhammad), the Saudi-sanctioned mainstream Sunni edition. Arabic preserved alongside.</p>
      <div class="reader-cta">
        <a href="../read.html" class="btn">← All sources</a>
        <a href="../assets/sources/quran.pdf" class="btn" download>Download PDF</a>
        <a href="quran-qarai.html" class="btn">Phrase By Phrase English Translation</a>
      </div>
    </header>

{chr(10).join(surah_blocks)}
  </main>

</div>

<footer class="site-footer">
  Saheeh International English translation sourced from the quran-json package (tanzil.net origin). Every verse anchored as #s{{surah}}v{{verse}} for stable linking.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT_PATH}: {len(SURAH_META)} surahs, {total_verses} verses")


if __name__ == "__main__":
    main()
