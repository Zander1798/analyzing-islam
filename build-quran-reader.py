#!/usr/bin/env python3
"""Convert extracted Quran PDF text into a styled HTML reader page.

Reads: quran-re.txt (produced by: pdftotext -enc UTF-8 -layout The-Quran-Saheeh-International.pdf)
Writes: site/read/quran.html
"""
import re
import sys
import html as html_lib
from pathlib import Path

# Force UTF-8 on stdout so we can print transliterated names on Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Map broken PDF glyph codes back to proper Unicode transliteration marks.
CHAR_MAP = {
    "Œ": "ā",
    "´": "ū",
    "ú": "ḥ",
    "Õ": "ʾ",
    "¥": "ī",
    "§": "ṣ",
    "Ô": "ʿ",
    "ê": "Ṣ",
    "î": "Ḥ",
    "‹": "ṭ",
    "«": "ḍ",
    "»": "ḍ",
    "­": "",  # soft hyphen
    "$": "Ṭ",  # capital Ṭā in surah titles (e.g. "$ā Seen Meem")
    "¯": "",   # macron artefacts
    "\xa0": " ",  # non-breaking space
}

def fix_chars(s: str) -> str:
    for k, v in CHAR_MAP.items():
        s = s.replace(k, v)
    return s

# (number, transliterated_name, english_meaning, verse_count)
SURAH_META = [
    (1, "al-Fātiḥah", "The Opening", 7),
    (2, "al-Baqarah", "The Cow", 286),
    (3, "Āli ʿImrān", "The Family of ʿImrān", 200),
    (4, "an-Nisāʾ", "The Women", 176),
    (5, "al-Māʾidah", "The Table Spread", 120),
    (6, "al-Anʿām", "The Cattle", 165),
    (7, "al-Aʿrāf", "The Heights", 206),
    (8, "al-Anfāl", "The Spoils of War", 75),
    (9, "at-Tawbah", "The Repentance", 129),
    (10, "Yūnus", "Jonah", 109),
    (11, "Hūd", "Hud", 123),
    (12, "Yūsuf", "Joseph", 111),
    (13, "ar-Raʿd", "The Thunder", 43),
    (14, "Ibrāhīm", "Abraham", 52),
    (15, "al-Ḥijr", "The Rocky Tract", 99),
    (16, "an-Naḥl", "The Bee", 128),
    (17, "al-Isrāʾ", "The Night Journey", 111),
    (18, "al-Kahf", "The Cave", 110),
    (19, "Maryam", "Mary", 98),
    (20, "Ṭā Hā", "Ta Ha", 135),
    (21, "al-Anbiyāʾ", "The Prophets", 112),
    (22, "al-Ḥajj", "The Pilgrimage", 78),
    (23, "al-Muʾminūn", "The Believers", 118),
    (24, "an-Nūr", "The Light", 64),
    (25, "al-Furqān", "The Criterion", 77),
    (26, "ash-Shuʿarāʾ", "The Poets", 227),
    (27, "an-Naml", "The Ants", 93),
    (28, "al-Qaṣaṣ", "The Stories", 88),
    (29, "al-ʿAnkabūt", "The Spider", 69),
    (30, "ar-Rūm", "The Romans", 60),
    (31, "Luqmān", "Luqman", 34),
    (32, "as-Sajdah", "The Prostration", 30),
    (33, "al-Aḥzāb", "The Combined Forces", 73),
    (34, "Sabaʾ", "Sheba", 54),
    (35, "Fāṭir", "The Originator", 45),
    (36, "Yā Seen", "Ya Seen", 83),
    (37, "aṣ-Ṣāffāt", "Those Lined Up", 182),
    (38, "Ṣād", "Sad", 88),
    (39, "az-Zumar", "The Groups", 75),
    (40, "Ghāfir", "The Forgiver", 85),
    (41, "Fuṣṣilat", "Explained in Detail", 54),
    (42, "ash-Shūrā", "The Consultation", 53),
    (43, "az-Zukhruf", "The Gold Adornments", 89),
    (44, "ad-Dukhān", "The Smoke", 59),
    (45, "al-Jāthiyah", "The Kneeling", 37),
    (46, "al-Aḥqāf", "The Curved Sand-Dunes", 35),
    (47, "Muḥammad", "Muhammad", 38),
    (48, "al-Fatḥ", "The Victory", 29),
    (49, "al-Ḥujurāt", "The Inner Apartments", 18),
    (50, "Qāf", "Qaf", 45),
    (51, "adh-Dhāriyāt", "The Winds That Scatter", 60),
    (52, "aṭ-Ṭūr", "The Mount", 49),
    (53, "an-Najm", "The Star", 62),
    (54, "al-Qamar", "The Moon", 55),
    (55, "ar-Raḥmān", "The Most Merciful", 78),
    (56, "al-Wāqiʿah", "The Inevitable", 96),
    (57, "al-Ḥadīd", "Iron", 29),
    (58, "al-Mujādilah", "The Disputer", 22),
    (59, "al-Ḥashr", "The Gathering", 24),
    (60, "al-Mumtaḥanah", "The Woman Examined", 13),
    (61, "aṣ-Ṣaff", "The Row", 14),
    (62, "al-Jumuʿah", "Friday", 11),
    (63, "al-Munāfiqūn", "The Hypocrites", 11),
    (64, "at-Taghābun", "Mutual Disillusion", 18),
    (65, "aṭ-Ṭalāq", "Divorce", 12),
    (66, "at-Taḥreem", "The Prohibition", 12),
    (67, "al-Mulk", "The Sovereignty", 30),
    (68, "al-Qalam", "The Pen", 52),
    (69, "al-Ḥāqqah", "The Reality", 52),
    (70, "al-Maʿārij", "The Ways of Ascent", 44),
    (71, "Nūḥ", "Noah", 28),
    (72, "al-Jinn", "The Jinn", 28),
    (73, "al-Muzzammil", "The Enwrapped", 20),
    (74, "al-Muddaththir", "The Cloaked", 56),
    (75, "al-Qiyāmah", "The Resurrection", 40),
    (76, "al-Insān", "Man", 31),
    (77, "al-Mursalāt", "Those Sent Forth", 50),
    (78, "an-Nabaʾ", "The Tidings", 40),
    (79, "an-Nāziʿāt", "Those Who Pull Out", 46),
    (80, "ʿAbasa", "He Frowned", 42),
    (81, "at-Takweer", "The Folding Up", 29),
    (82, "al-Infiṭār", "The Cleaving", 19),
    (83, "al-Muṭaffifeen", "The Defrauders", 36),
    (84, "al-Inshiqāq", "The Splitting Open", 25),
    (85, "al-Burūj", "The Mansions of the Stars", 22),
    (86, "aṭ-Ṭāriq", "The Night-Comer", 17),
    (87, "al-Aʿlā", "The Most High", 19),
    (88, "al-Ghāshiyah", "The Overwhelming", 26),
    (89, "al-Fajr", "The Dawn", 30),
    (90, "al-Balad", "The City", 20),
    (91, "ash-Shams", "The Sun", 15),
    (92, "al-Layl", "The Night", 21),
    (93, "aḍ-Ḍuḥā", "The Morning Hours", 11),
    (94, "ash-Sharḥ", "The Opening Forth", 8),
    (95, "at-Teen", "The Fig", 8),
    (96, "al-ʿAlaq", "The Clot", 19),
    (97, "al-Qadr", "The Decree", 5),
    (98, "al-Bayyinah", "The Clear Evidence", 8),
    (99, "az-Zalzalah", "The Earthquake", 8),
    (100, "al-ʿĀdiyāt", "The Runners", 11),
    (101, "al-Qāriʿah", "The Striking Hour", 11),
    (102, "at-Takāthur", "The Piling Up", 8),
    (103, "al-ʿAṣr", "The Time", 3),
    (104, "al-Humazah", "The Slanderer", 9),
    (105, "al-Feel", "The Elephant", 5),
    (106, "Quraysh", "Quraysh", 4),
    (107, "al-Māʿūn", "Small Kindnesses", 7),
    (108, "al-Kawthar", "Abundance", 3),
    (109, "al-Kāfirūn", "The Disbelievers", 6),
    (110, "an-Naṣr", "The Help", 3),
    (111, "al-Masad", "The Palm Fibre", 5),
    (112, "al-Ikhlāṣ", "The Sincerity", 4),
    (113, "al-Falaq", "The Daybreak", 5),
    (114, "an-Nās", "Mankind", 6),
]

PAGE_HEADER_RE = re.compile(r"^\s*Sūrah\s+\d+\s+[–-]\s+.*Juzʾ?\s+\d+\s*$")
VERSE_START_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")
FOOTNOTE_MARK_RE = re.compile(r"^\d+[A-Za-zĀĪŪḤāūīḥṣṭʾʿṢḤĀḌḍṬ]")  # "1Al-Fāti..." etc.
PAGE_NUMBER_RE = re.compile(r"^\s*\d+\s*$")
SURAH_1_START_RE = re.compile(r"Sūrah\s+1\s+[–-]\s+al-Fātiḥah")
# Strip inline footnote digits attached to a word (e.g. "Allāh,2" -> "Allāh,").
# Look for digit sequences glued to a preceding letter or punctuation and not followed by ':'.
INLINE_FOOTNOTE_RE = re.compile(
    r"(?<=[A-Za-zĀĪŪḤŌāūīḥṣṭʾʿṢḤĀḌḍṬ,.;:!?\]\)\"'’”–—])(\d{1,4})(?![\d:])"
)

def parse_quran(raw: str):
    """Walk the raw text and collect verses grouped by surah.
    Strategy: find every `N. text` verse-start line in document order.
    A verse whose number is 1 following one that isn't signals a new surah.
    """
    text = fix_chars(raw)
    lines = text.splitlines()

    # Find content start: first "Sūrah 1 – al-Fātiḥah …" page header line
    # (skips intro/foreword sections that contain numbered items like "1. In addition…").
    start = 0
    for i, ln in enumerate(lines):
        if SURAH_1_START_RE.search(ln):
            start = i
            break

    # Content ends at "SUBJECT INDEX".
    end = len(lines)
    for i, ln in enumerate(lines):
        if "SUBJECT INDEX" in ln:
            end = i
            break

    lines = lines[start:end]

    # Locate all verse-start lines.
    verse_starts = []
    for idx, ln in enumerate(lines):
        m = VERSE_START_RE.match(ln)
        if m:
            verse_starts.append((int(m.group(1)), m.group(2).strip(), idx))

    # Walk verse-starts, grouping into surahs.
    # Group rule: verse_number == 1 begins a new surah (unless it's the first overall).
    # Sanity check: if vnum doesn't follow previous+1 (and isn't 1), log and continue.
    surah_groups = []
    current = []
    for v in verse_starts:
        if v[0] == 1 and current:
            surah_groups.append(current)
            current = []
        current.append(v)
    if current:
        surah_groups.append(current)

    # Debug: show first verse of each detected surah + its count.
    print(f"Detected {len(surah_groups)} surah groups:")
    for i, g in enumerate(surah_groups, 1):
        print(f"  Group {i:>3}: {len(g):>3} verses, v1='{g[0][1][:60]}...'")

    # For each verse, collect continuation lines (until next verse-start or stop pattern).
    parsed_surahs = []
    for surah_idx, group in enumerate(surah_groups):
        verses = []
        for g_i, (vnum, vtext_first, lineidx) in enumerate(group):
            # Range of lines following this verse start up to next verse start.
            if g_i + 1 < len(group):
                next_start = group[g_i + 1][2]
            elif surah_idx + 1 < len(surah_groups):
                # End of this surah = start of first verse of next surah.
                next_start = surah_groups[surah_idx + 1][0][2]
            else:
                next_start = len(lines)

            parts = [vtext_first]
            for cl in lines[lineidx + 1 : next_start]:
                cs = cl.strip()
                if not cs:
                    continue
                if PAGE_HEADER_RE.match(cl):
                    continue
                if cs.startswith("Sūrah"):
                    continue
                if cs.startswith("Bismillāh"):
                    continue
                if PAGE_NUMBER_RE.match(cs):
                    continue
                if FOOTNOTE_MARK_RE.match(cs):
                    break  # footnotes — stop collecting
                parts.append(cs)
            body = " ".join(parts).strip()
            # Collapse whitespace and strip inline footnote superscripts.
            body = re.sub(r"\s+", " ", body)
            body = INLINE_FOOTNOTE_RE.sub("", body)
            verses.append((vnum, body))
        parsed_surahs.append(verses)

    return parsed_surahs


def build_html(parsed_surahs):
    # Align parsed surahs with SURAH_META.
    if len(parsed_surahs) != len(SURAH_META):
        print(f"WARN: parsed {len(parsed_surahs)} surahs, expected {len(SURAH_META)}")

    # Verify verse counts.
    ok = True
    for meta, verses in zip(SURAH_META, parsed_surahs):
        num, name, english, expected = meta
        actual = len(verses)
        status = "OK" if actual == expected else f"MISMATCH (expected {expected})"
        if actual != expected:
            ok = False
            print(f"  Surah {num:>3} {name:<20} {english:<30} verses {actual} {status}")

    if ok:
        print("All 114 surahs have the expected verse counts.")

    toc_items = []
    surah_sections = []
    for meta, verses in zip(SURAH_META, parsed_surahs):
        num, name, english, expected = meta
        toc_items.append(
            f'<li><a href="#surah-{num}"><span class="toc-num">{num}</span> <span class="toc-name">{html_lib.escape(name)}</span></a></li>'
        )

        verse_html = []
        for vnum, vtext in verses:
            verse_html.append(
                f'      <li id="s{num}v{vnum}" value="{vnum}">'
                f'<span class="verse-number">{vnum}</span>'
                f'<span class="verse-text">{html_lib.escape(vtext)}</span>'
                f'</li>'
            )

        bismillah_html = ""
        if num != 1 and num != 9:
            bismillah_html = '    <div class="surah-bismillah">Bismillāhir-Raḥmānir-Raḥeem</div>\n'

        surah_sections.append(
            f'<article class="surah" id="surah-{num}">\n'
            f'  <header class="surah-header">\n'
            f'    <div class="surah-number">Sūrah {num}</div>\n'
            f'    <h2>{html_lib.escape(name)}</h2>\n'
            f'    <div class="surah-subtitle">{html_lib.escape(english)} · {len(verses)} verses</div>\n'
            f'{bismillah_html}'
            f'  </header>\n'
            f'  <ol class="verses">\n'
            + "\n".join(verse_html)
            + '\n  </ol>\n'
            f'</article>'
        )

    toc_html = "\n".join(toc_items)
    body_html = "\n\n".join(surah_sections)

    return TEMPLATE.format(toc=toc_html, body=body_html)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read the complete Quran in the Saheeh International English translation. All 114 surahs, verse by verse.">
<title>Read the Quran — Islam Analyzed</title>
<link rel="stylesheet" href="../assets/css/style.css">
<link rel="stylesheet" href="../assets/css/reader.css">
</head>
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Islam Analyzed</a>
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
{toc}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">Saheeh International · English translation</div>
      <h1>The Qurʾān</h1>
      <p class="reader-intro">The complete text, all 114 sūrahs. Every verse as translated and published by Saheeh International — the Saudi-sanctioned mainstream Sunni edition.</p>
      <div class="reader-cta">
        <a href="../read.html" class="btn">← All sources</a>
        <a href="../assets/sources/quran.pdf" class="btn" download>Download PDF</a>
        <a href="quran-qarai.html" class="btn">Phrase By Phrase English Translation</a>
      </div>
    </header>

{body}

    <footer class="reader-footer">
      <p>Source: Saheeh International (1997, 2004 — Abul-Qasim Publishing House / Al-Muntada Al-Islami). Quoted here under fair use / fair dealing for the purposes of criticism, review, and commentary.</p>
    </footer>

  </main>

</div>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def main():
    src = Path(__file__).parent / "quran-re.txt"
    if not src.exists():
        raise SystemExit(
            f"Source {src} not found. Run first:\n"
            f"  pdftotext -enc UTF-8 -layout 'The-Quran-Saheeh-International.pdf' quran-re.txt"
        )
    raw = src.read_text(encoding="utf-8")
    surahs = parse_quran(raw)
    html_out = build_html(surahs)
    out_path = Path(__file__).parent / "site" / "read" / "quran.html"
    out_path.write_text(html_out, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
