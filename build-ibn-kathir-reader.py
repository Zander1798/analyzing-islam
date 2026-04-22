#!/usr/bin/env python3
"""Build the Tafsir Ibn Kathir reader from quran.com's v4 API.

Source:  https://api.quran.com/api/v4/tafsirs/169/by_ayah/{surah}:{ayah}
         (Tafsir ID 169 = Ibn Kathir (Abridged), English, slug en-tafisr-ibn-kathir.)

Output:  site/read-external/ibn-kathir.html           — index of 114 surahs
         site/read-external/ibn-kathir-{1..114}.html  — per-surah tafsir readers

Scraping is fully cacheable/resumable. Each ayah's raw JSON response is
cached to .tmp/sources/ibn-kathir-qc/{surah}-{ayah}.json so reruns skip
everything already fetched. Politeness delay of 0.25s between live
requests; none between cache hits.

Cleanup applied to the HTML body before rendering:
  - Strip all Arabic glyphs (Arabic block U+0600–U+06FF and presentation
    forms U+FB50–U+FEFF) — per user request, English-only output.
  - Strip `<strong style="color: rgb(95, 99, 104);">ﷺ </strong>` and
    similar leftover inline style="color..." attributes from the source.
  - Remove empty <p> tags left behind by Arabic stripping.
  - Linkify any inline (N:M) or (N:M-P) verse reference into a link to
    ../read/quran.html#s{N}v{M}.
"""
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
CACHE_DIR = ROOT / ".tmp" / "sources" / "ibn-kathir-qc"
OUT_DIR = ROOT / "site" / "read-external"

API_BASE = "https://api.quran.com/api/v4/tafsirs/169/by_ayah"
USER_AGENT = (
    "Mozilla/5.0 (Analyzing Islam static-site build; "
    "contact: github.com/Zander1798/islam-analyzed)"
)
FETCH_DELAY = 0.25


# Verse counts per surah (1..114). Matches the standard mushaf used by
# Saheeh International — same source our Qur'an reader is built from.
VERSE_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,
    5, 4, 5, 6,
]
assert len(VERSE_COUNTS) == 114

# Polished transliterated surah names + one-word English meanings, reused
# from build-quran-reader.py so anchors/names stay in sync.
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
    (73, "al-Muzzammil", "The One Enwrapped"),
    (74, "al-Muddaththir", "The One Enveloped"),
    (75, "al-Qiyāmah", "The Resurrection"),
    (76, "al-Insān", "Man"),
    (77, "al-Mursalāt", "Those Sent Forth"),
    (78, "an-Nabaʾ", "The Great News"),
    (79, "an-Nāziʿāt", "Those Who Pull Out"),
    (80, "ʿAbasa", "He Frowned"),
    (81, "at-Takweer", "The Folding Up"),
    (82, "al-Infiṭār", "The Cleaving"),
    (83, "al-Muṭaffifīn", "The Defrauders"),
    (84, "al-Inshiqāq", "The Splitting"),
    (85, "al-Burūj", "The Constellations"),
    (86, "aṭ-Ṭāriq", "The Night-Comer"),
    (87, "al-Aʿlā", "The Most High"),
    (88, "al-Ghāshiyah", "The Overwhelming"),
    (89, "al-Fajr", "The Dawn"),
    (90, "al-Balad", "The City"),
    (91, "ash-Shams", "The Sun"),
    (92, "al-Layl", "The Night"),
    (93, "aḍ-Ḍuḥā", "The Forenoon"),
    (94, "ash-Sharḥ", "The Opening Forth"),
    (95, "at-Teen", "The Fig"),
    (96, "al-ʿAlaq", "The Clot"),
    (97, "al-Qadr", "The Night of Decree"),
    (98, "al-Bayyinah", "The Clear Evidence"),
    (99, "az-Zalzalah", "The Earthquake"),
    (100, "al-ʿĀdiyāt", "The Courser"),
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
    (112, "al-Ikhlāṣ", "Sincerity"),
    (113, "al-Falaq", "The Daybreak"),
    (114, "an-Nās", "Mankind"),
]


# ---------- Scraping ----------

def fetch_ayah(surah: int, ayah: int) -> dict | None:
    """Return the parsed JSON response for one verse's tafsir, or None on 404."""
    cache_path = CACHE_DIR / f"{surah:03d}-{ayah:03d}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    url = f"{API_BASE}/{surah}:{ayah}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    time.sleep(FETCH_DELAY)
    return data


def scrape_all() -> None:
    total_ayahs = sum(VERSE_COUNTS)
    done = 0
    live = 0
    for s_idx, verse_count in enumerate(VERSE_COUNTS, start=1):
        for a in range(1, verse_count + 1):
            existed_before = (CACHE_DIR / f"{s_idx:03d}-{a:03d}.json").exists()
            fetch_ayah(s_idx, a)
            done += 1
            if not existed_before:
                live += 1
            if done % 200 == 0:
                print(f"  progress: {done}/{total_ayahs} ({live} fetched live)", flush=True)
    print(f"Scrape complete: {done}/{total_ayahs} total, {live} fetched this run.")


# ---------- HTML content cleaning ----------

ARABIC_RANGES = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]+")
EMPTY_PARA = re.compile(r"<p[^>]*>\s*</p>")
INLINE_STYLE = re.compile(r'\s*style="[^"]*"')
VERSE_REF = re.compile(r"\((\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?\)")

# Some entries have `<strong style="color:...">ﷺ </strong>` — once Arabic
# is stripped it becomes `<strong></strong>`. Remove empty inline tags.
EMPTY_INLINE = re.compile(r"<(strong|em|b|i|span)[^>]*>\s*</\1>")


def clean_tafsir_html(raw: str) -> str:
    """Take the API's HTML body and return English-only, attribute-stripped HTML."""
    # Drop Arabic glyphs entirely
    s = ARABIC_RANGES.sub("", raw)
    # Strip all inline style attrs (the API sets brand colours in-line)
    s = INLINE_STYLE.sub("", s)
    # Remove tags that are now empty (ﷺ markers, colour-only spans)
    for _ in range(3):
        s_new = EMPTY_INLINE.sub("", s)
        if s_new == s:
            break
        s = s_new
    # Remove empty paragraphs left behind
    s = EMPTY_PARA.sub("", s)
    # Linkify verse refs (N:M) and (N:M-P)
    def _ref(m: re.Match) -> str:
        n, a = int(m.group(1)), int(m.group(2))
        b = int(m.group(3)) if m.group(3) else None
        if not (1 <= n <= 114 and 1 <= a <= 286):
            return m.group(0)
        href = f"../read/quran.html#s{n}v{a}"
        label = f"{n}:{a}-{b}" if b else f"{n}:{a}"
        return f'(<a class="tafsir-ref" href="{href}">{label}</a>)'
    s = VERSE_REF.sub(_ref, s)
    # Collapse excess whitespace between tags for cleaner output
    s = re.sub(r">\s+<", "><", s)
    return s.strip()


def load_cached(surah: int, ayah: int) -> str | None:
    p = CACHE_DIR / f"{surah:03d}-{ayah:03d}.json"
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return (data.get("tafsir") or {}).get("text") or ""


# ---------- HTML rendering ----------

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

READER_STYLE = """
.ibnk-wrap { max-width: 860px; margin: 40px auto 80px; padding: 0 24px; }
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
  font-size: 44px;
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin: 0 0 6px;
}
.ibnk-wrap .ibnk-subtitle {
  font-family: var(--serif);
  font-style: italic;
  color: var(--text-muted);
  font-size: 16px;
  margin-bottom: 8px;
}
.ibnk-wrap .ibnk-count {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--text-dim);
  margin-bottom: 36px;
}

.ibnk-ayah {
  border-top: 1px solid var(--border);
  padding: 28px 0 4px;
  margin: 0;
}
.ibnk-ayah-head {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  color: var(--text-dim);
  margin-bottom: 14px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.ibnk-ayah-head .ibnk-ayah-link {
  font-family: var(--sans);
  color: var(--accent);
  font-weight: 600;
}
.ibnk-ayah-head .ibnk-ayah-link:hover { color: var(--accent-hover); }

.ibnk-ayah .ibnk-body h1,
.ibnk-ayah .ibnk-body h2,
.ibnk-ayah .ibnk-body h3 {
  font-family: var(--serif);
  line-height: 1.2;
  margin: 28px 0 12px;
  color: var(--text);
}
.ibnk-ayah .ibnk-body h1 { font-size: 26px; }
.ibnk-ayah .ibnk-body h2 { font-size: 20px; }
.ibnk-ayah .ibnk-body h3 { font-size: 16px; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-muted); }
.ibnk-ayah .ibnk-body p {
  font-size: 15px;
  line-height: 1.75;
  margin: 0 0 16px;
  color: var(--text);
}
.ibnk-ayah .ibnk-body blockquote {
  margin: 16px 0;
  padding: 14px 20px;
  border-left: 3px solid var(--accent);
  background: var(--panel);
  color: var(--text);
}
.ibnk-ayah .ibnk-body .tafsir-ref {
  color: var(--accent);
  border-bottom: 1px dotted var(--accent);
}
.ibnk-ayah .ibnk-body .tafsir-ref:hover { color: var(--accent-hover); border-bottom-style: solid; }

.ibnk-footnav {
  max-width: 860px;
  margin: 48px auto 0;
  padding: 24px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  border-top: 1px solid var(--border);
}
.ibnk-footnav a {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--text-muted);
}
.ibnk-footnav a:hover { color: var(--text); }
"""

INDEX_STYLE = """
.ibnk-hero { max-width: 860px; margin: 40px auto 20px; padding: 0 24px; }
.ibnk-hero h1 { font-family: var(--serif); font-size: 44px; line-height: 1.1; margin: 0 0 14px; letter-spacing: -0.02em; }
.ibnk-hero .ibnk-meta { font-size: 11px; text-transform: uppercase; letter-spacing: 0.2em; color: var(--text-dim); margin-bottom: 18px; }
.ibnk-hero p { color: var(--text-muted); font-size: 15px; line-height: 1.7; }
.ibnk-grid {
  max-width: 860px;
  margin: 36px auto 120px;
  padding: 0 24px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
}
.ibnk-grid a.ibnk-surah-card {
  display: flex;
  flex-direction: column;
  padding: 18px 16px;
  background: var(--bg);
  color: var(--text);
  text-decoration: none;
  transition: background 0.2s;
}
.ibnk-grid a.ibnk-surah-card:hover { background: var(--panel); text-decoration: none; }
.ibnk-grid .s-num {
  font-family: var(--sans);
  font-size: 10px;
  color: var(--text-dim);
  letter-spacing: 0.22em;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.ibnk-grid .s-name {
  font-family: var(--serif);
  font-size: 18px;
  line-height: 1.15;
  color: var(--text);
  margin-bottom: 2px;
}
.ibnk-grid .s-mean {
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
}
"""


def render_index() -> str:
    cards = []
    for n, translit, meaning in SURAH_META:
        cards.append(
            f'<a class="ibnk-surah-card" href="ibn-kathir-{n}.html">'
            f'<span class="s-num">Surah {n}</span>'
            f'<span class="s-name">{esc(translit)}</span>'
            f'<span class="s-mean">{esc(meaning)}</span>'
            f'</a>'
        )
    grid_html = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Tafsir Ibn Kathir (Abridged) — classical Sunni commentary on the Qur'an, full English edition. Indexed by surah.">
<title>Tafsir Ibn Kathir — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<style>{INDEX_STYLE}</style>
</head>
<body>
{NAV_HTML}

<header class="ibnk-hero">
  <div class="ibnk-meta">Classical Sunni commentary · English · Ibn Kathir (Abridged)</div>
  <h1>Tafsir Ibn Kathir</h1>
  <p>
    Abū al-Fidāʾ Ismāʿīl ibn Kathīr's (d. 774 AH / 1373 CE) verse-by-verse commentary —
    the most widely cited tafsir in mainstream Sunni scholarship. English text sourced
    from <a href="https://quran.com" target="_blank" rel="noopener">quran.com</a>'s
    "Ibn Kathir (Abridged)" resource, which mirrors the Darussalam abridged edition by
    Shaykh Ṣafiur Raḥmān al-Mubārakpūrī. Every inline <em>(N:M)</em> verse reference
    links to the corresponding ayah in <a href="../read/quran.html">the Qurʾān reader</a>.
  </p>
</header>

<section class="ibnk-grid">
{grid_html}
</section>

<footer class="site-footer">
  English text via quran.com API (tafsir resource id 169). Arabic omitted.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def render_surah(n: int, translit: str, meaning: str, ayah_blocks: list[tuple[int, str]]) -> str:
    prev_link = (
        f'<a href="ibn-kathir-{n - 1}.html">← Surah {n - 1}</a>'
        if n > 1 else '<a href="ibn-kathir.html">← All surahs</a>'
    )
    next_link = (
        f'<a href="ibn-kathir-{n + 1}.html">Surah {n + 1} →</a>'
        if n < 114 else '<a href="ibn-kathir.html">All surahs →</a>'
    )

    # Render each ayah as its own section with an anchor.
    parts = []
    for a, body in ayah_blocks:
        parts.append(
            f'<section class="ibnk-ayah" id="a{a}">'
            f'<header class="ibnk-ayah-head">'
            f'<span>Ayah {n}:{a}</span>'
            f'<a class="ibnk-ayah-link" href="../read/quran.html#s{n}v{a}">Read verse ↗</a>'
            f'</header>'
            f'<div class="ibnk-body">{body}</div>'
            f'</section>'
        )
    ayah_html = "\n".join(parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Tafsir Ibn Kathir (Abridged) on Surah {n}, {esc(translit)} ({esc(meaning)}) — full English commentary, verse by verse.">
<title>Tafsir Ibn Kathir · {esc(translit)} (Surah {n}) — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<style>{READER_STYLE}</style>
</head>
<body>
{NAV_HTML}

<article class="ibnk-wrap">
  <div class="ibnk-topbar">
    <a href="ibn-kathir.html">← All surahs</a>
    <span>Tafsir Ibn Kathir</span>
  </div>
  <h1>{esc(translit)}</h1>
  <div class="ibnk-subtitle">{esc(meaning)} · Surah {n}</div>
  <div class="ibnk-count">{len(ayah_blocks)} ayāt</div>

{ayah_html}
</article>

<nav class="ibnk-footnav">
  {prev_link}
  {next_link}
</nav>

<footer class="site-footer">
  English commentary via quran.com API · Arabic omitted.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


# ---------- Main ----------

def build_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "ibn-kathir.html").write_text(render_index(), encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'ibn-kathir.html'}")

    for n, translit, meaning in SURAH_META:
        ayah_blocks = []
        missing = 0
        for a in range(1, VERSE_COUNTS[n - 1] + 1):
            raw = load_cached(n, a)
            if not raw:
                missing += 1
                continue
            cleaned = clean_tafsir_html(raw)
            ayah_blocks.append((a, cleaned))
        path = OUT_DIR / f"ibn-kathir-{n}.html"
        path.write_text(render_surah(n, translit, meaning, ayah_blocks), encoding="utf-8")
        note = f" ({missing} missing)" if missing else ""
        print(f"  Wrote {path.name}: Surah {n} · {len(ayah_blocks)} ayāt{note}")


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-scrape", action="store_true",
                    help="Don't hit the network, only render from cache.")
    args = ap.parse_args()
    if not args.skip_scrape:
        print("Scraping quran.com tafsir (169, Ibn Kathir Abridged)...")
        scrape_all()
    else:
        print("Skipping scrape — rendering from cache only.")
    print("Rendering HTML...")
    build_all()


if __name__ == "__main__":
    main()
