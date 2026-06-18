#!/usr/bin/env python3
"""Make the Sahih Muslim reader read by its official sunnah.com reference
numbers (e.g. "Hadith 79a"), consistent with how the catalog cites them, and
re-point every Muslim citation to the hadith that IS that official reference.

Background: the reader is built from fawazahmed0 (anchored by a sequential
hadithnumber), but sunnah.com / the book cite Muslim by the Abdul-Baqi
reference ("79a", "2020c"). We scraped sunnah.com's 57 Muslim book pages to
build (in-book ref) -> official ref, and fawazahmed0 carries the same in-book
ref, giving fawaz_hadithnumber -> official ref (.git/sdd/muslim_fnum2ref.json).

This script:
1. Relabels each reader article's visible heading + sunnah.com link to the
   official reference (keeps the existing id anchor so nothing breaks).
2. Re-points every catalog/category Muslim citation to the reader article
   whose official reference matches the cited number (bare "1048" -> first
   sub-narration "1048a"), via the official->fawaz reverse map.
"""
import json
import io
import re
import glob
import collections
from pathlib import Path

ROOT = Path(__file__).parent
READ = ROOT / "site" / "read" / "muslim.html"

fnum2ref = json.loads((ROOT / ".git/sdd/muslim_fnum2ref.json").read_text())
# Two clean matches recovered from per-ref sunnah.com fetch (in-book gaps):
fnum2ref.setdefault("7354", "2930a")        # Muslim 2930a
# official ref -> fawaz hadithnumber (first wins)
ref2fnum = {}
for fn, ref in fnum2ref.items():
    ref2fnum.setdefault(ref, fn)
SPECIAL = {"2930a": "7354", "2922": "7373"}  # sunnah.com redirect / in-book gap


def resolve(ref):
    """Cited official ref -> correct fawaz hadithnumber (reader anchor)."""
    if ref in SPECIAL:
        return SPECIAL[ref]
    if ref in ref2fnum:
        return ref2fnum[ref]
    if ref + "a" in ref2fnum:          # bare number -> first sub-narration
        return ref2fnum[ref + "a"]
    return None


def relabel_reader():
    h = READ.read_text(encoding="utf-8")
    pat = re.compile(r'(<a href="https://sunnah\.com/muslim:)(\d+)("[^>]*>Hadith )(\2)( · Book \d+</a>)')
    n = [0]

    def repl(m):
        fz = m.group(2)
        off = fnum2ref.get(fz)
        if not off:
            return m.group(0)
        n[0] += 1
        return f'{m.group(1)}{off}{m.group(3)}{off}{m.group(5)}'

    h = pat.sub(repl, h)
    READ.write_text(h, encoding="utf-8")
    return n[0]


def repoint_citations():
    link = re.compile(r'<a class="cite-link" href="\.\./read/muslim\.html#h([0-9a-z]+)">Muslim ([0-9]+[a-z]?)</a>')
    changed = [0]
    unresolved = set()

    def repl(m):
        cur, ref = m.group(1), m.group(2)
        fz = resolve(ref)
        if fz is None:
            unresolved.add(ref)
            return m.group(0)
        if fz != cur:
            changed[0] += 1
        return f'<a class="cite-link" href="../read/muslim.html#h{fz}">Muslim {ref}</a>'

    for f in glob.glob(str(ROOT / "site/catalog/*.html")) + glob.glob(str(ROOT / "site/category/*.html")):
        t = io.open(f, encoding="utf-8").read()
        out = link.sub(repl, t)
        if out != t:
            io.open(f, "w", encoding="utf-8").write(out)
    return changed[0], unresolved


if __name__ == "__main__":
    relabeled = relabel_reader()
    changed, unresolved = repoint_citations()
    print(f"reader articles relabeled to official ref: {relabeled}")
    print(f"citations re-pointed: {changed}")
    print(f"citation refs left unresolved (kept as-is): {sorted(unresolved)}")
