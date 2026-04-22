#!/usr/bin/env python3
"""Build native HTML readers for the four OCR-scanned Darussalam PDFs
(Abu Dawud, Tirmidhi Vol.6, Nasa'i Vol.1, Ibn Majah Vol.1).

These PDFs are scans with mixed Arabic/English and OCR damage. The English
hadith text is extractable, but is interleaved with Arabic-text lines that
came out as gibberish and with post-hadith commentary sections.

Strategy:
  1. Find every "N. [Capitalized name] ..." line where N is sequential.
  2. For each hadith, collect body lines until the grading marker "(Sahih)",
     "(Hasan)", "(Da'if)", etc. appears.
  3. Filter out OCR-garbage lines — keep only lines that contain an English
     word (3+ consecutive ASCII letters) and whose non-letter ratio is low.
  4. Skip "Comments:" sections (publisher's modern commentary, not the hadith).
  5. Group hadiths by book — detect "N. THE BOOK OF ..." markers.

The output is not perfect — proper nouns with diacritics will still have
OCR artefacts, and some hadiths may be shorter than the original due to
aggressive noise filtering. But it produces a native-HTML reader that
matches the site theme.

Usage: python build-ocr-hadith-readers.py
"""
import re
import sys
import html as html_lib
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent

# Patterns
BOOK_HEADER_RE = re.compile(r"^\s*(\d+)\.\s+THE\s+BOOK\s+OF\b(.*)$", re.IGNORECASE)
CHAPTER_RE = re.compile(r"^\s*Chapter\s+\d+", re.IGNORECASE)
HADITH_START_RE = re.compile(r"^\s*(\d+)\.\s+([A-Z].{2,})$")
GRADING_RE = re.compile(
    r"\(\s*(Sahih|Sahi\S?|Saheeh|Hasan\s?\w*|Da['`]?if|Daif|Da['`]?J|Weak|Authentic|Gharib|Sah)[^\n)]{0,30}\)",
    re.IGNORECASE,
)


def normalize_grading(raw: str) -> str:
    """Map OCR-damaged grading labels to canonical forms."""
    s = raw.strip().lower()
    if s.startswith(("sahih", "sahi", "saheeh", "sah")):
        return "Sahih"
    if s.startswith("hasan"):
        return "Hasan"
    if s.startswith(("da'if", "daif", "da'j", "daj", "da`")):
        return "Da'if"
    if s.startswith("weak"):
        return "Weak"
    if s.startswith("authentic"):
        return "Authentic"
    if s.startswith("gharib"):
        return "Gharib"
    return raw.strip()
COMMENTS_RE = re.compile(r"^\s*Comments?\s*:\s*$", re.IGNORECASE)
PAGE_HEADER_RE = re.compile(
    r"^\s*(The\s+Book\s+Of\s+[A-Za-z].*\s+\d+|Contents\s+\d+|\d+\s*/\s*\d+|\s*\d+\s*$)\s*$"
)
ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{3,}")


def has_english_word(s: str) -> bool:
    return bool(ENGLISH_WORD_RE.search(s))


def left_column(s: str) -> str:
    """Trim the right-side OCR garbage column.
    Pages are laid out in two columns (English left, Arabic right). pdftotext
    -layout preserves both with lots of spaces between. We only want the left
    column. Split on runs of 4+ consecutive whitespace and keep the first chunk.
    """
    s = s.strip()
    if not s:
        return ""
    parts = re.split(r"\s{4,}", s)
    # First part is the left column. Strip trailing OCR noise chars.
    left = parts[0].rstrip(" .,:;-—–·'\"")
    return left.strip()


def is_noise(s: str) -> bool:
    """Return True if the line appears to be OCR garbage or Arabic gibberish."""
    stripped = s.strip()
    if not stripped:
        return True
    # Count English-like words (3+ ASCII letters). Lines with 0 such words
    # are almost always OCR gibberish or Arabic transliteration artefacts.
    english_words = ENGLISH_WORD_RE.findall(stripped)
    if len(english_words) < 2:
        return True
    # Ratio check: letters vs. "weird" characters (not letters, digits, spaces,
    # or standard English punctuation).
    allowed_punct = set(".,!?'\"“”‘’:;-—–()[]/#\\&")
    nospace = stripped.replace(" ", "")
    if not nospace:
        return True
    alpha = sum(1 for c in nospace if c.isalpha())
    weird = sum(
        1
        for c in nospace
        if not c.isalnum() and c not in allowed_punct
    )
    if weird / len(nospace) > 0.30:
        return True
    # If fewer than half the chars are letters, it's probably noise.
    if alpha / len(nospace) < 0.50:
        return True
    return False


def parse(text: str, start_hadith: int, book_titles: dict, content_start_re):
    """Parse OCR'd Darussalam hadith text.
    Returns a list of book dicts: {number, title, hadiths: [{number, text}]}.
    content_start_re must be a compiled regex that matches the first line of
    body content (past TOC + preface).
    """
    lines = text.splitlines()

    content_start = 0
    for i, ln in enumerate(lines):
        if content_start_re.search(ln):
            content_start = i
            break

    lines = lines[content_start:]

    books = []
    current_book = None
    current_hadith = None
    max_seen = start_hadith - 1
    post_hadith = False

    def flush_hadith():
        nonlocal current_hadith
        if current_hadith is None:
            return
        if current_hadith["_buffer"]:
            tail = " ".join(current_hadith["_buffer"]).strip()
            if tail:
                current_hadith["paragraphs"].append(tail)
            current_hadith["_buffer"] = []
        paragraphs = [
            re.sub(r"\s+", " ", p).strip()
            for p in current_hadith["paragraphs"]
            if p.strip()
        ]
        paragraphs = [p for p in paragraphs if len(p) > 15 and has_english_word(p)]
        # Post-process: add Arabic honorifics where obvious.
        paragraphs = [inject_arabic_honorifics(p) for p in paragraphs]
        if paragraphs and current_book is not None:
            current_book["hadiths"].append(
                {
                    "number": current_hadith["number"],
                    "grading": current_hadith.get("grading"),
                    "paragraphs": paragraphs,
                }
            )
        current_hadith = None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        m_book = BOOK_HEADER_RE.match(line)
        if m_book:
            flush_hadith()
            post_hadith = False
            bnum = int(m_book.group(1))
            title_from_line = m_book.group(2).strip().title()
            title = book_titles.get(bnum) or title_from_line or f"Book {bnum}"
            current_book = {"number": bnum, "title": title, "hadiths": []}
            books.append(current_book)
            continue

        if CHAPTER_RE.match(stripped):
            flush_hadith()
            post_hadith = False
            continue

        if COMMENTS_RE.match(stripped):
            flush_hadith()
            post_hadith = True
            continue

        m_had = HADITH_START_RE.match(stripped)
        if m_had:
            hnum = int(m_had.group(1))
            if hnum > max_seen and hnum < max_seen + 500:
                flush_hadith()
                post_hadith = False
                if current_book is None:
                    current_book = {
                        "number": 0,
                        "title": list(book_titles.values())[0] if book_titles else "Untitled",
                        "hadiths": [],
                    }
                    books.append(current_book)
                first_chunk = left_column(m_had.group(2))
                inline_grade = GRADING_RE.search(first_chunk)
                if inline_grade:
                    first_chunk = first_chunk[: inline_grade.start()].rstrip(" .,")
                    grade_val = normalize_grading(inline_grade.group(1))
                    post_hadith = True
                else:
                    grade_val = None
                current_hadith = {
                    "number": hnum,
                    "paragraphs": [],
                    "_buffer": [first_chunk] if first_chunk else [],
                    "grading": grade_val,
                }
                max_seen = hnum
                continue
            continue

        if post_hadith:
            continue

        if current_hadith is None:
            continue

        if not stripped:
            continue

        if PAGE_HEADER_RE.match(line):
            continue

        trimmed = left_column(line)
        if not trimmed:
            continue

        m_inline_grade = GRADING_RE.search(trimmed)
        if m_inline_grade:
            body = trimmed[: m_inline_grade.start()].rstrip(" .,")
            if body and not is_noise(body):
                current_hadith["_buffer"].append(body)
            current_hadith["grading"] = normalize_grading(m_inline_grade.group(1))
            post_hadith = True
            continue

        if is_noise(trimmed):
            continue

        if re.match(r"^(The Book Of|Chapters? On)\b", trimmed, re.IGNORECASE):
            continue

        current_hadith["_buffer"].append(trimmed)

    flush_hadith()
    return books


# ==========================================================
# Arabic injection: add ﷺ after Prophet mentions, and similar
# short, standard Islamic Arabic phrases that are unambiguous.
# ==========================================================

PROPHET_PATTERN = re.compile(
    r"\b(the\s+Prophet|the\s+Messenger\s+of\s+Allah|Allah'?s\s+Messenger|Allah'?s\s+Apostle)\b(?!\s*(?:ﷺ|\(peace))",
    re.IGNORECASE,
)


def inject_arabic_honorifics(text: str) -> str:
    """Insert the Arabic honorific ﷺ (ṣallā llāhu ʿalayhi wa-sallam) after
    references to the Prophet Muḥammad. Standard typographic convention in
    Muslim-produced English hadith editions. Applied only where the phrase
    is not already followed by the mark or a '(peace…)' parenthetical.
    """
    return PROPHET_PATTERN.sub(lambda m: f"{m.group(1)} ﷺ", text)


# =====================================================================
# Rendering
# =====================================================================

def render_html(books, meta):
    total = sum(len(b["hadiths"]) for b in books)
    print(f"  parsed: {len(books)} books, {total} hadiths")

    titles_ar = meta.get("book_titles_ar", {})

    toc_items = []
    book_sections = []
    for b in books:
        if not b["hadiths"]:
            continue
        ar_title = titles_ar.get(b["number"], "")
        toc_items.append(
            f'<li><a href="#book-{b["number"]}"><span class="toc-num">{b["number"]}</span>'
            f' <span class="toc-name">{html_lib.escape(b["title"])}</span></a></li>'
        )
        hadiths_html = []
        for h in b["hadiths"]:
            pblocks = "\n        ".join(
                f'<p>{html_lib.escape(p)}</p>' for p in h["paragraphs"]
            )
            grading_html = ""
            if h.get("grading"):
                grading_html = (
                    f'<span class="hadith-grading">({html_lib.escape(h["grading"])})</span>'
                )
            hadiths_html.append(
                f'    <article class="hadith" id="h{h["number"]}">\n'
                f'      <header class="hadith-header">\n'
                f'        <span class="hadith-ref">Hadith {h["number"]}</span>\n'
                f'        {grading_html}\n'
                f'      </header>\n'
                f'      <div class="hadith-body">\n'
                f'        {pblocks}\n'
                f'      </div>\n'
                f'    </article>'
            )
        ar_header = (
            f'<div class="hadith-book-arabic" lang="ar" dir="rtl">{html_lib.escape(ar_title)}</div>\n    '
            if ar_title
            else ""
        )
        book_sections.append(
            f'<section class="hadith-book" id="book-{b["number"]}">\n'
            f'  <header class="hadith-book-header">\n'
            f'    <div class="hadith-book-number">Book {b["number"]}</div>\n'
            f'    <h2>{html_lib.escape(b["title"])}</h2>\n'
            f'    {ar_header}'
            f'<div class="hadith-book-subtitle">{len(b["hadiths"])} hadith{"s" if len(b["hadiths"]) != 1 else ""}</div>\n'
            f'  </header>\n'
            f'  <div class="hadith-book-body">\n'
            + "\n".join(hadiths_html)
            + "\n  </div>\n"
            f'</section>'
        )

    return TEMPLATE.format(
        title=meta["title"],
        subtitle=meta["subtitle"],
        description=meta["description"],
        note=meta["note"],
        pdf=meta["pdf"],
        toc="\n".join(toc_items),
        body="\n\n".join(book_sections),
        total=f"{total:,}",
        books_count=len([b for b in books if b['hadiths']]),
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read {title} — {total} hadiths rendered from the Darussalam English edition.">
<title>Read {title} — Analyzing Islam</title>
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
    <div class="reader-toc-header">Books</div>
    <ol>
{toc}
    </ol>
  </aside>

  <main class="reader-main">

    <header class="reader-hero">
      <div class="reader-meta">{subtitle}</div>
      <h1>{title}</h1>
      <p class="reader-intro">{description}</p>
      <p class="reader-intro" style="font-size:13px;color:var(--text-dim);"><strong>Note on source quality:</strong> {note}</p>
      <div class="reader-cta">
        <a href="../read.html" class="btn">← All sources</a>
        <a href="../assets/sources/{pdf}" class="btn" download>Download PDF</a>
      </div>
    </header>

{body}

    <footer class="reader-footer">
      <p>Source: Darussalam English edition. Quoted here under fair use / fair dealing for the purposes of criticism, review, and commentary.</p>
    </footer>

  </main>

</div>

<script src="../assets/js/pdf-mobile.js" defer></script>
<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


# =====================================================================
# Per-book config
# =====================================================================

ABU_DAWUD_BOOKS = {
    1:  "The Book of Purification",
    2:  "The Book of As-Salat (The Prayer)",
    3:  "The Book of The Prayer (continued)",
    4:  "The Book of Sujud As-Sahw (Prostrations for Forgetfulness)",
    5:  "The Book of Al-Witr",
    6:  "The Book of Zakat",
    7:  "The Book of Lost & Found",
    8:  "The Book of Rituals (Manasik)",
    9:  "The Book of Marriage",
    10: "The Book of Divorce",
    11: "The Book of Fasting",
    12: "The Book of Jihad",
    13: "The Book of Sacrifice",
    14: "The Book of Game",
    15: "The Book of Wills",
    16: "The Book of Shares of Inheritance",
    17: "The Book of Tribute, Spoils and Rulership (Kharaj, Fay' and Imarah)",
    18: "The Book of Funerals",
    19: "The Book of Oaths and Vows",
    20: "The Book of Commercial Transactions (Buyu')",
    21: "The Book of Wages (Ijarah)",
    22: "The Book of the Office of the Judge (Aqdiyah)",
    23: "The Book of Knowledge",
    24: "The Book of Drinks",
    25: "The Book of Foods",
    26: "The Book of Medicine",
    27: "The Book of Divination and Omens",
    28: "The Book of Manumission of Slaves",
    29: "The Book of Dialects and Readings of the Qur'an",
    30: "The Book of Hot Baths",
    31: "The Book of Clothing",
    32: "The Book of Combing the Hair",
    33: "The Book of Signet-Rings",
    34: "The Book of Tribulations and Fierce Battles",
    35: "The Book of the Promised Deliverer (Mahdi)",
    36: "The Book of Battles",
    37: "The Book of Prescribed Punishments (Hudud)",
    38: "The Book of Types of Blood-Wit (Diyat)",
    39: "The Book of Model Behavior of the Prophet (Sunnah)",
    40: "The Book of General Behavior (Adab)",
    41: "The Book of The Reading of the Qur'an (Qira'at)",
}

# Arabic Kitāb names for the books. Only for ones with well-established,
# unambiguous names used across classical and modern editions.
ABU_DAWUD_BOOKS_AR = {
    1:  "كتاب الطهارة",
    2:  "كتاب الصلاة",
    3:  "كتاب الصلاة",
    4:  "كتاب سجود السهو",
    5:  "كتاب الوتر",
    6:  "كتاب الزكاة",
    7:  "كتاب اللقطة",
    8:  "كتاب المناسك",
    9:  "كتاب النكاح",
    10: "كتاب الطلاق",
    11: "كتاب الصوم",
    12: "كتاب الجهاد",
    13: "كتاب الضحايا",
    14: "كتاب الصيد",
    15: "كتاب الوصايا",
    16: "كتاب الفرائض",
    17: "كتاب الخراج والإمارة والفيء",
    18: "كتاب الجنائز",
    19: "كتاب الأيمان والنذور",
    20: "كتاب البيوع",
    21: "كتاب الإجارة",
    22: "كتاب الأقضية",
    23: "كتاب العلم",
    24: "كتاب الأشربة",
    25: "كتاب الأطعمة",
    26: "كتاب الطب",
    27: "كتاب الكهانة والتطير",
    28: "كتاب العتق",
    29: "كتاب الحروف والقراءات",
    30: "كتاب الحمام",
    31: "كتاب اللباس",
    32: "كتاب الترجل",
    33: "كتاب الخاتم",
    34: "كتاب الفتن والملاحم",
    35: "كتاب المهدي",
    36: "كتاب الملاحم",
    37: "كتاب الحدود",
    38: "كتاب الديات",
    39: "كتاب السنة",
    40: "كتاب الأدب",
    41: "كتاب الحروف والقراءات",
}

TIRMIDHI_BOOKS_V6_AR = {
    45: "كتاب الدعوات",
    46: "كتاب المناقب",
    47: "كتاب التفسير",
    48: "كتاب فضائل القرآن",
    49: "كتاب القراءات",
}

NASAI_BOOKS_V1_AR = {
    1: "كتاب الطهارة",
    2: "كتاب المياه",
    3: "كتاب الحيض والاستحاضة",
    4: "كتاب الغسل والتيمم",
}

IBN_MAJAH_BOOKS_V1_AR = {
    0: "المقدمة",
    1: "كتاب الطهارة وسننها",
    2: "كتاب الصلاة",
}

TIRMIDHI_BOOKS_V6 = {
    45: "The Book of Supplications (Da'awat)",
    46: "Chapters on Al-Manaqib (Virtues)",
    47: "Chapters of Tafsir",
    48: "Chapters on the Virtues of the Qur'an",
    49: "Chapters on Recitation",
}

NASAI_BOOKS_V1 = {
    1: "The Book of Purification (Kitab At-Taharah)",
    2: "The Book of Water (Kitab Al-Miyah)",
    3: "The Book of Menstruation and Istihadah",
    4: "The Book of Ghusl and Tayammum",
}

IBN_MAJAH_BOOKS_V1 = {
    0: "Introduction (Muqaddimah)",
    1: "The Book of Purification and Its Sunan",
    2: "The Book of Prayer (Salat) (opening portion)",
}

SOURCES = [
    {
        "txt": "dawud-re.txt",
        "out": "site/read/abu-dawud.html",
        "title": "Sunan Abī Dāwūd",
        "subtitle": "Sunan Abi Dawud · Darussalam English edition",
        "description": "Compiled by Abū Dāwūd al-Sijistānī (d. 889 CE). Focuses primarily on reports with legal implications.",
        "note": "this text was extracted from a scanned PDF via OCR, so some proper-noun diacritics and Arabic phrases are missing or mangled. The English hadith bodies are preserved in full. For perfect fidelity, download the PDF.",
        "pdf": "abu-dawud.pdf",
        "start_hadith": 1,
        "book_titles": ABU_DAWUD_BOOKS,
        "book_titles_ar": ABU_DAWUD_BOOKS_AR,
        # Body book header: "1. THE BOOK OF" with nothing after (TOC has full title on same line).
        "content_start_re": re.compile(r"^\s*1\.\s+THE BOOK OF\s*$", re.IGNORECASE),
    },
    {
        "txt": "tirmidhi-re.txt",
        "out": "site/read/tirmidhi.html",
        "title": "Jāmi al-Tirmidhī — Volume 6",
        "subtitle": "Jami at-Tirmidhi Vol. 6 · Darussalam English edition",
        "description": "Compiled by al-Tirmidhī (d. 892 CE). This copy covers <strong>Volume 6, hadiths 3291–3956</strong> — the final volume of the 6-volume Darussalam edition.",
        "note": "this text was extracted from a scanned PDF via OCR. Only Volume 6 is included. The English hadith bodies are preserved; for perfect fidelity with diacritics and Arabic quotations, download the PDF.",
        "pdf": "tirmidhi.pdf",
        "start_hadith": 3290,
        "book_titles": TIRMIDHI_BOOKS_V6,
        "book_titles_ar": TIRMIDHI_BOOKS_V6_AR,
        # The first body hadith is "3367." (file is volume 6 of 6 — some early numbers missing).
        "content_start_re": re.compile(r"^\s*3367\.\s+[A-Z]"),
    },
    {
        "txt": "nasai-re.txt",
        "out": "site/read/nasai.html",
        "title": "Sunan an-Nasāʾī — Volume 1",
        "subtitle": "Sunan an-Nasa'i Vol. 1 · Darussalam English edition",
        "description": "Compiled by al-Nasāʾī (d. 915 CE). This copy covers <strong>Volume 1, hadiths 1–876</strong> — the opening volume.",
        "note": "this text was extracted from a scanned PDF via OCR. Only Volume 1 is included. The OCR quality on this volume is poor in places — some proper nouns are mangled. The English hadith bodies are mostly preserved; for perfect fidelity, download the PDF.",
        "pdf": "nasai.pdf",
        "start_hadith": 0,
        "book_titles": NASAI_BOOKS_V1,
        "book_titles_ar": NASAI_BOOKS_V1_AR,
        # First body hadith starts "1. It was narrated" (TOC doesn't match this pattern).
        "content_start_re": re.compile(r"^\s*1\.\s+It was narrated", re.IGNORECASE),
    },
    {
        "txt": "ibn-majah-re.txt",
        "out": "site/read/ibn-majah.html",
        "title": "Sunan Ibn Mājah — Volume 1",
        "subtitle": "Sunan Ibn Majah Vol. 1 · Darussalam English edition",
        "description": "Compiled by Ibn Mājah (d. 887 CE). This copy covers <strong>Volume 1, hadiths 1–802</strong> — the opening volume.",
        "note": "this text was extracted from a scanned PDF via OCR. Only Volume 1 is included. The English hadith bodies are mostly preserved; some proper nouns and Arabic phrases are mangled. For perfect fidelity, download the PDF.",
        "pdf": "ibn-majah.pdf",
        "start_hadith": 0,
        "book_titles": IBN_MAJAH_BOOKS_V1,
        "book_titles_ar": IBN_MAJAH_BOOKS_V1_AR,
        # First body hadith "1. It was narrated that Abu" (follows Book Of The Sunnah in body).
        "content_start_re": re.compile(r"^\s*1\.\s+It was narrated that Abu", re.IGNORECASE),
    },
]


def main():
    for src in SOURCES:
        txt_path = ROOT / src["txt"]
        if not txt_path.exists():
            print(f"Skipping {src['title']} — missing {txt_path}")
            continue
        print(f"\n{src['title']}:")
        raw = txt_path.read_text(encoding="utf-8")
        books = parse(
            raw,
            src["start_hadith"],
            src["book_titles"],
            src["content_start_re"],
        )
        html_out = render_html(books, src)
        out_path = ROOT / src["out"]
        out_path.write_text(html_out, encoding="utf-8")
        print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
