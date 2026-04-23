"""Diagnostic scan across every readable source on the site.

Purpose: find "non-word gibberish" interleaved with English text — leftover
brackets / colons from stripped-out Arabic, Unicode replacement chars,
mojibake, stray long punctuation runs, etc. Excludes legitimate full
non-Latin blocks (real Arabic / Hebrew / Greek text spans).

Emits a per-source summary of pattern counts + sample snippets so we can
decide where to spend the cleanup effort before changing any HTML.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"

# Force UTF-8 stdout on Windows so diacritic source names print cleanly.
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

# Sources to scan (slug → list of HTML paths).
SOURCES: dict[str, list[Path]] = {
    "Qur'an":              [SITE / "read/quran.html"],
    "Bukhari":             [SITE / "read/bukhari.html"],
    "Muslim":              [SITE / "read/muslim.html"],
    "Abu Dawud":           [SITE / "read/abu-dawud.html"],
    "Tirmidhi":            [SITE / "read/tirmidhi.html"],
    "Nasa'i":              [SITE / "read/nasai.html"],
    "Ibn Majah":           [SITE / "read/ibn-majah.html"],
    "Tanakh":              [SITE / "read-external/tanakh.html"],
    "New Testament":       [SITE / "read-external/new-testament.html"],
    "Apocryphal Gospels":  [SITE / "read-external/apocryphal-gospels.html"],
    "Book of Enoch":       [SITE / "read-external/book-of-enoch.html"],
    "Mishnah":             [SITE / "read-external/mishnah.html"],
    "Josephus":            [SITE / "read-external/josephus.html"],
    "Talmud":              sorted(SITE.glob("read-external/talmud-*.html")),
    "Ibn Kathir":          sorted(SITE.glob("read-external/ibn-kathir-*.html")),
    # Bible Interlinear: skip — its "gibberish" is the legitimate
    # transliteration / interlinear glyphs that look weird but are on-purpose.
}

# Patterns to count. Each tuple: (name, regex, description).
#
# The idea: isolate cases where punctuation/separators sit with NO word
# characters around them — strong sign of stripped-out text.
PATTERNS = [
    ("empty-quote-run",
        re.compile(r"[«»]\s*[:,\.\-;\s]{2,}\s*[«»]"),
        "« ... » with only punctuation inside — usually stripped Arabic"),
    ("colon-run",
        re.compile(r"(?<!\w)[ \t]*:(?:[ \t]*:){2,}"),
        ": : : — runs of bare colons"),
    ("bullet-run",
        re.compile(r"[•·.]{5,}"),
        "dot/bullet runs (5+ in a row)"),
    ("replacement-char",
        re.compile(r"�"),
        "U+FFFD replacement character (encoding damage)"),
    ("mojibake-a-tilde",
        re.compile(r"Ã[-¿]"),
        "Ã̂/Ã© style mojibake (UTF-8 decoded as cp1252)"),
    ("paren-run",
        re.compile(r"\(\s*[:,\.\-;\s]{2,}\s*\)"),
        "( ... ) with only punctuation inside"),
    ("bracket-pair-empty",
        re.compile(r"«\s*»|\[\s*\]|\{\s*\}"),
        "«», [], {} with nothing between"),
    ("stripped-diacritics",
        re.compile(r"\b[a-z]{3,}\\[\-\']"),
        "backslash-escaped hyphens/quotes (\\' \\-) mid-word"),
    ("repeated-punct",
        re.compile(r"([-=_~])\1{6,}"),
        "=======, ------- long punctuation bars"),
]

# Regex approximating Unicode Letter class without the unicodedata overhead.
LETTER_RE = re.compile(r"[A-Za-zÀ-ɏ]")

# Run patterns after stripping Arabic/Hebrew/Greek blocks, so "real"
# non-Latin text is not flagged.
ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]+")
HEBREW_RE = re.compile(r"[֐-׿יִ-ﭏ]+")
GREEK_RE  = re.compile(r"[Ͱ-Ͽἀ-῿]+")


def clean_text(t: str) -> str:
    t = ARABIC_RE.sub(" ", t)
    t = HEBREW_RE.sub(" ", t)
    t = GREEK_RE.sub(" ", t)
    return t


def scan_file(path: Path) -> dict[str, list[str]]:
    html = path.read_text(encoding="utf-8", errors="replace")
    # Only look at the reading content — skip the nav / toolbar / toc.
    soup = BeautifulSoup(html, "lxml")
    for sel in (".site-nav", ".reader-toc", ".site-footer", "script", "style"):
        for el in soup.select(sel):
            el.decompose()
    text = clean_text(soup.get_text(" ", strip=True))

    hits: dict[str, list[str]] = defaultdict(list)
    for name, rx, _desc in PATTERNS:
        for m in rx.finditer(text):
            # Capture a short window for display.
            s, e = max(0, m.start() - 40), min(len(text), m.end() + 40)
            snippet = text[s:e].replace("\n", " ")
            hits[name].append(snippet)
    return hits


def main() -> None:
    overall = defaultdict(lambda: defaultdict(int))
    samples = defaultdict(lambda: defaultdict(list))

    for source_name, files in SOURCES.items():
        print(f"\n=== {source_name} ({len(files)} file(s)) ===")
        total_by_pattern: dict[str, int] = defaultdict(int)
        example_by_pattern: dict[str, str] = {}
        for path in files:
            if not path.exists():
                print(f"  [skip] {path.name} missing")
                continue
            hits = scan_file(path)
            for name, snippets in hits.items():
                total_by_pattern[name] += len(snippets)
                if name not in example_by_pattern and snippets:
                    example_by_pattern[name] = snippets[0]
                overall[source_name][name] += len(snippets)
                if len(samples[source_name][name]) < 3:
                    samples[source_name][name].extend(snippets[:3])
        for name, n in sorted(total_by_pattern.items(), key=lambda kv: -kv[1]):
            ex = example_by_pattern.get(name, "")
            print(f"  {n:6d} × {name:20s} | example: {ex[:100]!r}")

    print("\n=== Grand totals by pattern ===")
    grand: dict[str, int] = defaultdict(int)
    for counts in overall.values():
        for k, v in counts.items():
            grand[k] += v
    for name, n in sorted(grand.items(), key=lambda kv: -kv[1]):
        print(f"  {n:6d}  {name}")


if __name__ == "__main__":
    main()
