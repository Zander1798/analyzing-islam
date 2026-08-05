#!/usr/bin/env python3
"""Repair the two verses where interlinear morphology is attached to the wrong word.

build-quran-interlinear.js joins two independent sources by position: the Arabic,
transliteration and English gloss come from one file (per word), while root, lemma,
part of speech and morphology come from a QAC-derived file keyed by
`surah:verse:wordIndex`. Where the two sources divide a word differently, that
positional join silently shifts every remaining token in the verse.

Two verses are affected corpus-wide:

  8:6   بَعْدَ / مَا is two words in one source and بعدما in the other. Tokens w5
        through w12 each carry the FOLLOWING word's morphology, so وَهُمْ
        ("while they") is labelled root نظر "to look", and يَنْظُرُونَ is left
        with no morphology at all. The concordance inherits the same shift, so
        root links jump to and highlight the wrong word.

  37:130 إِلْ / يَاسِينَ is split in one source and إلياسين in the other. The
        merged entry lands on w3, leaving w4 with nothing.

The generator is NOT the place to fix this by re-running: it refetches its sources
live and a re-run would also discard patch-quran-highlights.js. This script edits
the generated pages and the concordance in place, and is idempotent -- it verifies
the defective shape before touching anything and reports "already correct" once the
fix is applied.

Usage:
    python fix-interlinear-morphology.py            # apply
    python fix-interlinear-morphology.py --check    # verify only, exit 1 if unfixed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QURAN_DIR = ROOT / "site" / "read-external" / "quran"
CONCORDANCE = QURAN_DIR / "data" / "concordance.json"

ATTRS = ("root", "lem", "pos", "feats")


def token_re(surah: int, verse: int, word: int) -> re.Pattern:
    return re.compile(
        r'(<span class="w"[^>]*id="s%dv%dw%d"[^>]*>)' % (surah, verse, word)
    )


def read_attrs(tag: str) -> dict:
    return {a: (re.search(r'data-%s="([^"]*)"' % a, tag).group(1)
                if re.search(r'data-%s="([^"]*)"' % a, tag) else None)
            for a in ATTRS}


def write_attrs(tag: str, values: dict) -> str:
    out = tag
    for a in ATTRS:
        new = values.get(a)
        pat = re.compile(r'(data-%s=")([^"]*)(")' % a)
        if pat.search(out):
            if new is None:
                # Attribute exists but the target has none: blank it rather than
                # removing it, so the shape of the markup stays uniform.
                out = pat.sub(lambda m: m.group(1) + "" + m.group(3), out)
            else:
                out = pat.sub(lambda m: m.group(1) + new + m.group(3), out)
        elif new:
            out = out[:-1] + ' data-%s="%s">' % (a, new)
    return out


def tokens_of(html: str, surah: int, verse: int, count: int):
    found = {}
    for w in range(1, count + 1):
        m = token_re(surah, verse, w).search(html)
        if not m:
            sys.exit("error: token s%dv%dw%d not found" % (surah, verse, w))
        found[w] = (m.span(1), m.group(1))
    return found


def fix_8_6(html: str, check: bool):
    """Shift w6..w12 back by one; clear w5, which has no entry of its own."""
    toks = tokens_of(html, 8, 6, 12)
    current = {w: read_attrs(tag) for w, (_, tag) in toks.items()}

    # Already correct? The signature of the defect is وَهُمْ (w11) carrying نظر.
    if current[11].get("root") != "نظر":
        return html, False

    if check:
        return html, True

    target = {5: {a: None for a in ATTRS}}
    for w in range(6, 13):
        target[w] = current[w - 1]

    # Rewrite back-to-front so earlier spans stay valid.
    for w in sorted(target, reverse=True):
        (start, end), tag = toks[w]
        html = html[:start] + write_attrs(tag, target[w]) + html[end:]
    return html, True


def fix_37_130(html: str, check: bool):
    """إِلْياسِين is one proper noun split across two display words: give the
    second half the same lemma as the first rather than leaving it bare."""
    toks = tokens_of(html, 37, 130, 4)
    current = {w: read_attrs(tag) for w, (_, tag) in toks.items()}

    if current[4].get("lem"):
        return html, False
    if check:
        return html, True

    (start, end), tag = toks[4]
    html = html[:start] + write_attrs(tag, current[3]) + html[end:]
    return html, True


def fix_concordance(check: bool) -> bool:
    """The concordance stores [surah, verse, wordIndex] triples built from the
    same shifted join, so its 8:6 anchors point one word early."""
    data = json.loads(CONCORDANCE.read_text(encoding="utf-8"))
    shifts = {"بين": 5, "سوق": 7, "موت": 9, "نظر": 11}
    changed = False
    for root, wrong in shifts.items():
        for entry in data.get(root, []):
            if len(entry) == 3 and entry[0] == 8 and entry[1] == 6 and entry[2] == wrong:
                changed = True
                if not check:
                    entry[2] = wrong + 1
    if changed and not check:
        CONCORDANCE.write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report whether the defect is present; exit 1 if it is")
    args = ap.parse_args()

    pending = []
    for surah, fixer in ((8, fix_8_6), (37, fix_37_130)):
        path = QURAN_DIR / ("surah-%03d.html" % surah)
        if not path.is_file():
            sys.exit("error: %s not found" % path)
        html = path.read_text(encoding="utf-8")
        new_html, needed = fixer(html, args.check)
        if needed:
            pending.append("surah-%03d.html" % surah)
            if not args.check:
                path.write_text(new_html, encoding="utf-8")

    if fix_concordance(args.check):
        pending.append("concordance.json")

    if args.check:
        if pending:
            print("FAIL interlinear morphology shift still present in: "
                  + ", ".join(pending))
            return 1
        print("OK  interlinear morphology for 8:6 and 37:130 is correct")
        return 0

    if pending:
        print("fixed: " + ", ".join(pending))
    else:
        print("already correct -- nothing to do")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
