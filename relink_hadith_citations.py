#!/usr/bin/env python3
"""Re-point every hadith citation in the catalog + category pages to the
hadith whose TEXT matches the entry's quote — verified by content, not by
trusting a number.

Why: sunnah.com's reference numbering (esp. Sahih Muslim's letter-suffix
"2020a" scheme) does not always equal the rebuilt reader's anchor number.
Rather than trust the number, we match the book's verified quote to the
reader hadith text and link there. This fixes Muslim (whose numbering is a
different system) and the handful of off-by errors in the other collections.

Prereq: hadith readers already rebuilt by build-hadith-readers-v2.py
(anchored by fawazahmed0 hadithnumber) and hadith-sunnah/ editions present.
"""
import json
import io
import re
import glob
import collections
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "hadith-sunnah"
BOOK = ROOT.parent / "Analyzing Islam Books" / "data"

COLLS = [("bukhari", "bukhari"), ("muslim", "muslim"), ("abu-dawud", "abudawud"),
         ("tirmidhi", "tirmidhi"), ("nasai", "nasai"), ("ibn-majah", "ibnmajah")]
SLUG = {"bukhari": "bukhari", "muslim": "muslim", "abudawud": "abu-dawud",
        "abu dawud": "abu-dawud", "tirmidhi": "tirmidhi", "nasai": "nasai",
        "ibnmajah": "ibn-majah", "ibn majah": "ibn-majah"}
BOOK_FILES = [("hadith_entries_v2.json", None), ("abudawud_entries_v2.json", None),
              ("tirmidhi_entries_v2.json", None), ("nasai_entries_v2.json", None),
              ("ibnmajah_entries_v2.json", None)]


def words(s):
    return set(re.findall(r"[a-z]{4,}", (s or "").lower()))


def norm(name):
    n = re.sub(r"[’'`ʾʿ]", "", name.lower())
    return SLUG.get(re.sub(r"\s+", " ", n).strip())


def build_map(min_overlap=0.5):
    """(slug, number-token) -> correct hadithnumber, via quote text match."""
    idx = {}
    for slug, stem in COLLS:
        d = json.loads((DATA / f"eng-{stem}.json").read_text(encoding="utf-8"))
        idx[slug] = [(h["hadithnumber"], words(h.get("text", ""))) for h in d["hadiths"]]
    mapping = {}
    for bf, _ in BOOK_FILES:
        for e in json.loads((BOOK / bf).read_text(encoding="utf-8"))["entries"]:
            vr = e.get("verse_refs") or []
            if not vr:
                continue
            m = re.match(r"\s*([\w' ]+?)\s+(\d+[a-z]?)", vr[0])
            if not m:
                continue
            slug = norm(m.group(1))
            q = words(e.get("verse_quote"))
            if not slug or len(q) < 4:
                continue
            best_n, best_ov = None, 0.0
            for n, hw in idx[slug]:
                if not hw:
                    continue
                ov = len(q & hw) / len(q)
                if ov > best_ov:
                    best_ov, best_n = ov, n
            if best_n is not None and best_ov >= min_overlap:
                mapping[(slug, m.group(2))] = best_n
    return mapping


def relink(mapping):
    link = re.compile(r'<a class="cite-link" href="\.\./read/([a-z-]+)\.html#h([0-9a-z]+)">([^<]+)</a>')
    numtok = re.compile(r"(\d+[a-z]?)\s*$")
    changed = collections.Counter()
    for f in glob.glob(str(ROOT / "site/catalog/*.html")) + glob.glob(str(ROOT / "site/category/*.html")):
        t = io.open(f, encoding="utf-8").read()

        def repl(m):
            slug, cur, disp = m.group(1), m.group(2), m.group(3)
            nm = numtok.search(disp)
            if not nm:
                return m.group(0)
            correct = mapping.get((slug, nm.group(1)))
            if correct is None or str(correct) == cur:
                return m.group(0)
            changed[slug] += 1
            return f'<a class="cite-link" href="../read/{slug}.html#h{correct}">{disp}</a>'

        out = link.sub(repl, t)
        if out != t:
            io.open(f, "w", encoding="utf-8").write(out)
    return changed


if __name__ == "__main__":
    mp = build_map()
    print(f"quote-match map: {len(mp)} confident (slug,number) -> correct anchors")
    print("re-pointed:", dict(relink(mp)))
