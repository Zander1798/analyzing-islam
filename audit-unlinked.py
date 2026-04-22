#!/usr/bin/env python3
"""Find plain-text citations that are NOT inside an <a> tag — candidates
for upgrading to cite-links."""
import re
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"

# Only scan catalog + category (canonical text) — the category pages
# are regenerated from the catalog, so duplicates are expected.
TARGETS = list((SITE / "catalog").glob("*.html"))


def inside_anchor(text: str, pos: int) -> bool:
    """Return True if `pos` falls inside an <a ...>…</a> span."""
    # Find the last <a or </a before pos; if <a is later, we're inside.
    before = text[:pos]
    last_open = before.rfind("<a ")
    last_close = before.rfind("</a>")
    if last_open == -1:
        return False
    if last_close == -1:
        return True
    return last_open > last_close


# ------- patterns that should be hyperlinks -------

PATTERNS = [
    # Qurʾān refs: "Q 4:34", "Quran 4:34", "Qur'an 2:256", "Q. 2:256"
    ("Quran", re.compile(
        r"\b(?:Q|Qur[ʾ'']?an|Quran)\.?\s+(\d{1,3}):(\d{1,3})(?:[-–](\d{1,3}))?\b"
    )),
    # Surah/chapter style: "Surah 2:256", "chap. vi.", "Sura 2 verse 256"
    ("Surah", re.compile(
        r"\b(?:Surah|Sura|Sūra(?:h)?)\s+(\d{1,3}):(\d{1,3})\b"
    )),
    # Bukhari/sunnah-style: "Bukhari 2:24:285" or "Sahih al-Bukhari 4.54.521"
    ("Bukhari", re.compile(
        r"\b(?:Sahih\s+al-)?Bukh[aā]r[īi][,\s]+(\d+)[:.](\d+)[:.](\d+)\b"
    )),
    # "Sahih Muslim 8:3310" etc.
    ("Muslim", re.compile(
        r"\b(?:Sahih\s+)?Muslim[,\s]+(?:Book\s+)?(\d+)[:.](\d+)(?:[:.](\d+))?\b"
    )),
    # Abu Dawud nnn
    ("AbuDawud", re.compile(
        r"\bAbu\s+D[aā]w[uū]d[,\s]+(\d{1,5})\b"
    )),
    # Talmud tractate refs: "Sanhedrin 90a", "Bava Batra 74a"
    ("Talmud", re.compile(
        r"\b(Sanhedrin|Bava\s+(?:Batra|Kamma|Metzia)|Baba\s+(?:Bathra|Kama|Metzia)|Berakhot|Pesachim|Yoma|Sukkah|Megillah|Megilla|Erubin|Shabbat|Avodah\s+Zarah|Abuda\s+Zara|Rosh\s+Hashana|Shekalim|Hagiga|Betzah|Moed\s+Katan|Taanith|Taanit)\s+(\d{1,3}[ab]?|\d{1,3}:\d{1,3})\b"
    )),
    # Mishnah explicit: "Mishnah Sanhedrin 4:5"
    ("Mishnah", re.compile(
        r"\bMishnah\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+:\d+)\b"
    )),
]


def audit():
    found: dict[str, list[tuple[Path, str, int]]] = {k: [] for k, _ in PATTERNS}

    for src in TARGETS:
        text = src.read_text(encoding="utf-8", errors="replace")
        for kind, pat in PATTERNS:
            for m in pat.finditer(text):
                if inside_anchor(text, m.start()):
                    continue
                # Skip if the whole match text is contained within nearby
                # short snippet that's clearly a heading or ID value
                ctx_start = max(0, m.start() - 20)
                ctx = text[ctx_start:m.start()]
                if ctx.rstrip().endswith(('id="', 'name="', 'href="')):
                    continue
                found[kind].append((src, m.group(0), m.start()))

    print("========== UNLINKED CITATION AUDIT ==========\n")
    for kind, hits in found.items():
        print(f"--- {kind}: {len(hits)} unlinked occurrences ---")
        counter = Counter(h[1].strip() for h in hits)
        for ref, count in counter.most_common(8):
            print(f"  {count:4d} × {ref!r}")
        # Sample one occurrence per file
        seen_files = set()
        for src, ref, pos in hits:
            if src in seen_files:
                continue
            seen_files.add(src)
            # Get enclosing sentence snippet
            start = max(0, pos - 60)
            end = min(len(open(src, encoding='utf-8', errors='replace').read()), pos + 80)
            snippet = src.read_text(encoding='utf-8', errors='replace')[start:end].replace("\n", " ")
            print(f"    {src.name} @ {pos}: …{snippet}…")
        print()


if __name__ == "__main__":
    audit()
