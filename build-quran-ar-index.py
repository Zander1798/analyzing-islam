#!/usr/bin/env python3
"""Build the Arabic -> verse-reference index used by the Build editor's translator.

The Build editor used to machine-translate highlighted Arabic word by word, which
cannot reproduce a verse translation (see build-editor.js translateSmart). The site
already holds the correct English: every verse in site/read/quran/<n>.html carries a
<span class="verse-text"> (Saheeh International) beside its <span class="verse-arabic">.

This script emits a lookup that turns any highlighted Arabic back into the verse
reference it came from, so the editor can then read the canonical English straight
off the reader page. Only references are stored -- never the English -- so the
reader pages stay the single source of truth for translation wording.

Output: site/assets/data/quran-ar-index.json

    {
      "version": 1,
      "corpus":  "<every verse, normalised, joined>",
      "starts":  [<absolute start offset of each of the 6236 verses>],
      "counts":  [<verses per surah, 114 entries>]
    }

Verses within a surah are joined by a single space so a selection spanning
consecutive verses still matches as one substring; surahs are joined by "\\n" so a
match can never run across a surah boundary.

IMPORTANT: normalise() here and normaliseArabic() in site/assets/js/build-editor.js
must stay byte-for-byte equivalent in behaviour. tests/test_quran_ar_index.py pins
this; if you change one, change both and re-run that test.

Usage:
    python build-quran-ar-index.py            # write the index
    python build-quran-ar-index.py --check    # verify the committed index is current
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
READER_DIR = ROOT / "site" / "read" / "quran"
OUT_PATH = ROOT / "site" / "assets" / "data" / "quran-ar-index.json"

SURAH_COUNT = 114
EXPECTED_VERSES = 6236

# <li id="s15v6" ...><span class="verse-number">6</span>
#   <span class="verse-text">English</span>
#   <span class="verse-arabic" lang="ar" dir="rtl">Arabic</span></li>
VERSE_RE = re.compile(
    r'<li id="s(?P<surah>\d+)v(?P<ayah>\d+)"[^>]*>'
    r".*?"
    r'<span class="verse-arabic"[^>]*>(?P<arabic>.*?)</span>',
    re.S,
)

TAG_RE = re.compile(r"<[^>]+>")

# Marks that carry no consonantal information: harakat, Quranic annotation
# symbols, the superscript alef, tatweel, and zero-width joiners. Stripping them
# lets fully-vocalised mushaf text match the plain text a user might paste.
_STRIP = (
    "ؐ-ؚ"  # Arabic honorific / Quranic annotation signs
    "ً-ٟ"  # harakat, shadda, sukun
    "ٰ"  # superscript (dagger) alef
    "ۖ-ۭ"  # sajda, hizb, small high/low marks
    "ـ"  # tatweel
    "​-‏"  # zero-width space/joiners, LRM/RLM
    "﻿"  # BOM / zero-width no-break space
)
STRIP_RE = re.compile("[" + _STRIP + "]")

# Orthographic variants folded together so Uthmani text and the plainer
# orthography found elsewhere on the web resolve to the same key.
FOLD = {
    "ٱ": "ا",  # alef wasla   -> alef
    "أ": "ا",  # alef hamza above
    "إ": "ا",  # alef hamza below
    "آ": "ا",  # alef madda
    "ى": "ي",  # alef maqsura -> ya
    "ئ": "ي",  # ya hamza     -> ya
    "ؤ": "و",  # waw hamza    -> waw
    "ة": "ه",  # ta marbuta   -> ha
}
FOLD_RE = re.compile("[" + "".join(FOLD) + "]")

# After folding, keep only Arabic consonants (hamza through ya) and spaces.
# Everything else -- Latin letters, digits, Arabic-Indic digits, punctuation,
# verse-end ornaments -- is dropped, so a selection that accidentally includes
# the English line or a verse number still matches on its Arabic alone.
KEEP_RE = re.compile(r"[^ء-ي\s]")
WS_RE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Fold Arabic text to the consonantal skeleton used as the lookup key."""
    s = STRIP_RE.sub("", text or "")
    s = FOLD_RE.sub(lambda m: FOLD[m.group(0)], s)
    s = KEEP_RE.sub(" ", s)
    return WS_RE.sub(" ", s).strip()


def plain_text(html: str) -> str:
    """Strip tags and decode entities from a captured span body."""
    return unescape(TAG_RE.sub("", html)).strip()


def read_surah(path: Path) -> list[tuple[int, int, str]]:
    """Return [(surah, ayah, normalised_arabic)] for one reader chapter page."""
    html = path.read_text(encoding="utf-8")
    out: list[tuple[int, int, str]] = []
    for m in VERSE_RE.finditer(html):
        surah = int(m.group("surah"))
        ayah = int(m.group("ayah"))
        arabic = normalise(plain_text(m.group("arabic")))
        out.append((surah, ayah, arabic))
    return out


def build() -> dict:
    if not READER_DIR.is_dir():
        sys.exit(
            f"error: {READER_DIR} not found. The split Qur'an reader must be built "
            "first -- see CLAUDE.md on the reader builders and .orig.html backups."
        )

    corpus_parts: list[str] = []
    starts: list[int] = []
    counts: list[int] = []
    cursor = 0
    problems: list[str] = []

    for surah in range(1, SURAH_COUNT + 1):
        path = READER_DIR / f"{surah}.html"
        if not path.is_file():
            sys.exit(f"error: missing reader page {path}")

        verses = read_surah(path)
        if not verses:
            sys.exit(f"error: no verses parsed from {path}")

        # The page must hold exactly one contiguous run 1..n for this surah.
        for i, (s, a, _) in enumerate(verses, start=1):
            if s != surah or a != i:
                problems.append(f"{path.name}: expected {surah}:{i}, found {s}:{a}")

        if surah > 1:
            corpus_parts.append("\n")  # surah separator: matches never span surahs
            cursor += 1

        for i, (_, _, arabic) in enumerate(verses):
            if not arabic:
                problems.append(f"{surah}:{i + 1} normalised to an empty string")
            if i:
                corpus_parts.append(" ")  # verse separator inside a surah
                cursor += 1
            starts.append(cursor)
            corpus_parts.append(arabic)
            cursor += len(arabic)

        counts.append(len(verses))

    if problems:
        for p in problems[:20]:
            print("  " + p, file=sys.stderr)
        sys.exit(f"error: {len(problems)} verse-numbering problem(s); index not written")

    total = sum(counts)
    if total != EXPECTED_VERSES:
        sys.exit(f"error: parsed {total} verses, expected {EXPECTED_VERSES}")

    return {
        "version": 1,
        "corpus": "".join(corpus_parts),
        "starts": starts,
        "counts": counts,
    }


def serialise(index: dict) -> str:
    return json.dumps(index, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if the committed index differs from a fresh build",
    )
    args = ap.parse_args()

    index = build()
    blob = serialise(index)

    if args.check:
        if not OUT_PATH.is_file():
            print(f"FAIL {OUT_PATH} does not exist -- run build-quran-ar-index.py")
            return 1
        if OUT_PATH.read_text(encoding="utf-8") != blob:
            print(f"FAIL {OUT_PATH} is stale -- re-run build-quran-ar-index.py")
            return 1
        print(f"OK  {OUT_PATH.name} is current ({sum(index['counts'])} verses)")
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(blob, encoding="utf-8")
    kb = len(blob.encode("utf-8")) / 1024
    print(
        f"wrote {OUT_PATH.relative_to(ROOT)} -- {sum(index['counts'])} verses, "
        f"{len(index['corpus'])} chars, {kb:.0f} KB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
