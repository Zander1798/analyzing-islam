"""Build search-index JSON for sources used by the Compare page that live
across many sub-pages (Interlinear Bible, Tafsīr Ibn Kathīr). The Compare
iframe can only hold one page at a time, so the search there previously
only saw the currently-loaded reader. These indexes let compare.js search
across every sub-page at once.

Output format (per source):
{
  "source": "<slug>",
  "title":  "<display title>",
  "base":   "<dir prefix used when building href, e.g. 'read-external/bible/'>",
  "entries": [
    {"ref": "Genesis 1:1", "href": "gen.html#gen-1-1", "text": "..."}
    ...
  ]
}

The ``href`` is relative to ``base`` so compare.js can build the full
iframe URL with a tiny amount of work.
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

# Force UTF-8 stdout so the script can print Arabic / diacritic characters
# on the Windows default cp1252 console without crashing.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
OUT_DIR = SITE / "assets" / "compare-index"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- Interlinear

# Map 3-letter file abbreviations to human names. Matches the abbreviations
# used by the generated bible/ files.
BIBLE_BOOK_NAMES = {
    "gen": "Genesis", "exo": "Exodus", "lev": "Leviticus", "num": "Numbers",
    "deu": "Deuteronomy", "jos": "Joshua", "jdg": "Judges", "rut": "Ruth",
    "1sa": "1 Samuel", "2sa": "2 Samuel", "1ki": "1 Kings", "2ki": "2 Kings",
    "1ch": "1 Chronicles", "2ch": "2 Chronicles", "ezr": "Ezra",
    "neh": "Nehemiah", "est": "Esther", "job": "Job", "psa": "Psalms",
    "pro": "Proverbs", "ecc": "Ecclesiastes", "sng": "Song of Songs",
    "isa": "Isaiah", "jer": "Jeremiah", "lam": "Lamentations",
    "ezk": "Ezekiel", "dan": "Daniel", "hos": "Hosea", "jol": "Joel",
    "amo": "Amos", "oba": "Obadiah", "jon": "Jonah", "mic": "Micah",
    "nam": "Nahum", "hab": "Habakkuk", "zep": "Zephaniah", "hag": "Haggai",
    "zec": "Zechariah", "mal": "Malachi",
    "mat": "Matthew", "mrk": "Mark", "luk": "Luke", "jhn": "John",
    "act": "Acts", "rom": "Romans", "1co": "1 Corinthians",
    "2co": "2 Corinthians", "gal": "Galatians", "eph": "Ephesians",
    "php": "Philippians", "col": "Colossians", "1th": "1 Thessalonians",
    "2th": "2 Thessalonians", "1ti": "1 Timothy", "2ti": "2 Timothy",
    "tit": "Titus", "phm": "Philemon", "heb": "Hebrews", "jas": "James",
    "1pe": "1 Peter", "2pe": "2 Peter", "1jn": "1 John", "2jn": "2 John",
    "3jn": "3 John", "jud": "Jude", "rev": "Revelation",
}


def build_bible_index() -> dict:
    """Scan every bible/<abbr>.html and collect one entry per verse."""

    bible_dir = SITE / "read-external" / "bible"
    entries: list[dict] = []

    for abbr, name in BIBLE_BOOK_NAMES.items():
        path = bible_dir / f"{abbr}.html"
        if not path.exists():
            print(f"  [skip] {path.name} missing", file=sys.stderr)
            continue

        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "lxml")

        verses = soup.select("li.bible-verse")
        for verse in verses:
            vid = verse.get("id") or ""
            # id pattern: "<abbr>-<chapter>-<verse>", e.g. "gen-1-1"
            m = re.match(r"^[a-z0-9]+-(\d+)-(\d+)$", vid)
            if not m:
                continue
            chap, vnum = m.group(1), m.group(2)

            # Prefer the English gloss (readable word-by-word translation)
            # but fall back to the whole text if no gloss spans exist.
            gloss_bits = [
                g.get_text(" ", strip=True)
                for g in verse.select(".w-gloss")
            ]
            gloss = " ".join(b for b in gloss_bits if b).strip()
            if not gloss:
                gloss = verse.get_text(" ", strip=True)

            # Squash whitespace / arrow-like interlinear punctuation.
            text = re.sub(r"\s+", " ", gloss).strip()
            if not text:
                continue

            entries.append({
                "ref":  f"{name} {chap}:{vnum}",
                "href": f"{abbr}.html#{vid}",
                "text": text,
            })

        print(f"  {abbr}.html -> {len(verses)} verses")

    return {
        "source":  "bible-interlinear",
        "title":   "Interlinear Bible (Hebrew · Greek · Strong's)",
        "base":    "read-external/bible/",
        "entries": entries,
    }


# --------------------------------------------------------------- Ibn Kathīr

# Pull Surah metadata from each ibn-kathir-<n>.html; we only need it per
# source file, not per ayah, so scan once.

IBNK_FILE_RE = re.compile(r"ibn-kathir-(\d+)\.html$")


def build_ibn_kathir_index() -> dict:
    ik_dir = SITE / "read-external"
    files = sorted(
        ik_dir.glob("ibn-kathir-*.html"),
        key=lambda p: int(IBNK_FILE_RE.search(p.name).group(1))
        if IBNK_FILE_RE.search(p.name) else 0,
    )

    entries: list[dict] = []
    for path in files:
        m = IBNK_FILE_RE.search(path.name)
        if not m:
            continue
        surah_num = int(m.group(1))

        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "lxml")

        h1 = soup.select_one(".ibnk-wrap h1") or soup.find("h1")
        surah_name = h1.get_text(strip=True) if h1 else f"Surah {surah_num}"

        sections = soup.select("section.ibnk-ayah")
        for sec in sections:
            sid = sec.get("id") or ""
            # id pattern "a<num>" — gives ayah number
            mm = re.match(r"^a(\d+)$", sid)
            ayah_num = mm.group(1) if mm else sid

            # Header has "<span>Ayah 1:1</span><a ...>Read verse ↗</a>".
            # We only want the span text; the "Read verse ↗" link is
            # reader chrome, not a ref.
            head_span = sec.select_one(".ibnk-ayah-head span")
            head_txt = head_span.get_text(" ", strip=True) if head_span else ""
            ref = head_txt if head_txt.lower().startswith("ayah") else (
                f"Ayah {surah_num}:{ayah_num}"
            )
            # Always prefix the surah so refs stay meaningful when the
            # user jumps to results from other surahs.
            ref = f"{surah_name} · {ref}"

            body = sec.select_one(".ibnk-body")
            text = body.get_text(" ", strip=True) if body else sec.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue

            entries.append({
                "ref":  ref,
                "href": f"{path.name}#{sid}",
                "text": text,
            })

        print(f"  {path.name} ({surah_name}) -> {len(sections)} sections")

    return {
        "source":  "ibn-kathir",
        "title":   "Tafsīr Ibn Kathīr",
        "base":    "read-external/",
        "entries": entries,
    }


# ------------------------------------------------------------------ Talmud

# Rodkinson's Talmud ships in 10 books. Each book file bundles one or more
# *tractates* (Sabbath, Sanhedrin, etc.) with chapters numbered in Roman
# numerals. Chapter anchors are opaque IDs like `t0109`.
TALMUD_BOOK_TITLES = {
    1:  "Tract Sabbath",
    2:  "Tracts Erubin, Shekalim, Rosh Hashana",
    3:  "Tract Pesachim (Vol. I)",
    4:  "Tracts Pesachim (Vol. II), Yomah, Hagiga",
    5:  "Tracts Aboth, Derech Eretz, Betzah, Succah, Moed Katan, Taanith, Megilla",
    6:  "Tract Baba Kama",
    7:  "Tract Baba Bathra",
    8:  "Tract Sanhedrin",
    9:  "Tracts Maccoth, Ebel Rabbathi, Shebuoth, Eduyoth, Abuda Zara, Horioth",
    10: "History of the Talmud",
}

TRACT_PREFIX_RE = re.compile(r"^TRACT\s+([A-Z][A-Z0-9' .,()\-&;/:]*?)\.?$", re.IGNORECASE)


def _tract_name_from_h3(h3_text: str) -> str | None:
    """Return the tractate name from an h3 like 'TRACT SANHEDRIN (SUPREME
    COUNCIL).' — keeps only the first capitalised noun so the ref stays
    short ("Sanhedrin" rather than "Sanhedrin (Supreme Council)")."""
    if not h3_text:
        return None
    m = TRACT_PREFIX_RE.match(h3_text.strip())
    if not m:
        return None
    raw = m.group(1).strip()
    # Drop trailing subtitles in parens ("SANHEDRIN (SUPREME COUNCIL)"
    # → "SANHEDRIN"; "DERECH ERETZ--RABBA. (WORLDLY AFFAIRS.)" → "DERECH ERETZ")
    for sep in ["(", "--", " - "]:
        if sep in raw:
            raw = raw.split(sep, 1)[0]
    raw = raw.strip(" ,.").strip()
    # Title-case: SANHEDRIN → Sanhedrin. Preserve multi-word tracts.
    return " ".join(w.capitalize() for w in raw.split())


def build_talmud_index() -> dict:
    root = SITE / "read-external"
    files = sorted(
        root.glob("talmud-*.html"),
        key=lambda p: int(re.search(r"talmud-(\d+)\.html$", p.name).group(1)),
    )

    entries: list[dict] = []
    for path in files:
        m = re.search(r"talmud-(\d+)\.html$", path.name)
        if not m:
            continue
        book_num = int(m.group(1))
        book_title = TALMUD_BOOK_TITLES.get(book_num, f"Book {book_num}")

        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "lxml")

        sections = soup.select("article.surah")
        current_tract: str | None = None

        for sec in sections:
            sid = sec.get("id") or ""
            h2 = sec.select_one("h2.surah-title")
            h2_txt = h2.get_text(" ", strip=True) if h2 else ""

            # Update the current tractate if this section opens a new one.
            for h3 in sec.select(".prose h3"):
                t = _tract_name_from_h3(h3.get_text(" ", strip=True))
                if t:
                    current_tract = t
                    break

            # Skip prefaces / erratas / advertisement shells — they aren't
            # useful search targets and have noisy titles.
            title = h2_txt.strip().rstrip(".")
            if not title:
                continue
            lower_title = title.lower()
            if any(skip in lower_title for skip in (
                "explanatory remarks", "copyright", "advertisement",
                "errata", "a word to the reader",
            )):
                continue

            # Ref: "Sanhedrin · Chapter IV" (falls back to "Book 8 · Chapter IV"
            # when we haven't spotted a TRACT heading yet).
            tract_part = current_tract or f"Book {book_num}"
            ref = f"{tract_part} · {title}"

            body = sec.select_one(".prose") or sec
            text = body.get_text(" ", strip=True) if body else sec.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue

            entries.append({
                "ref":  ref,
                "href": f"{path.name}#{sid}",
                "text": text,
            })

        print(f"  {path.name} ({book_title}) -> {len(sections)} sections")

    return {
        "source":  "talmud",
        "title":   "The Talmud",
        "base":    "read-external/",
        "entries": entries,
    }


# --------------------------------------------------------------------- main

def write_index(name: str, data: dict) -> None:
    out = OUT_DIR / f"{name}.json"
    out.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    size_kb = out.stat().st_size / 1024
    print(f"wrote {out.relative_to(ROOT)}  ({len(data['entries'])} entries, {size_kb:,.0f} KB)")


def main() -> None:
    args = set(sys.argv[1:])
    do_bible  = not args or "bible" in args
    do_ibnk   = not args or "ibn-kathir" in args or "ibnk" in args
    do_talmud = not args or "talmud" in args

    if do_bible:
        print("Building Interlinear Bible search index...")
        write_index("bible", build_bible_index())

    if do_ibnk:
        print("\nBuilding Tafsir Ibn Kathir search index...")
        write_index("ibn-kathir", build_ibn_kathir_index())

    if do_talmud:
        print("\nBuilding Talmud search index...")
        write_index("talmud", build_talmud_index())


if __name__ == "__main__":
    main()
