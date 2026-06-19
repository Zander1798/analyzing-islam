#!/usr/bin/env python3
"""Scripture-accuracy check for the dossiers: compare each quoted verse/hadith
in a dossier's "The text" box to the readable source it links to, and flag
quotes whose wording diverges from the source (potential misquote).

Quran quotes are checked against site/read/quran.html (Saheeh International);
hadith quotes against the fawazahmed0 reader data keyed by anchor number.
Low word-overlap = review candidate (quotes are often excerpts, so this finds
gross mismatches, not minor trims). Read-only; reports, does not edit.
"""
import io, re, json, glob, html
from pathlib import Path

ROOT = Path(__file__).parent


def words(s):
    return set(re.findall(r"[a-z]{4,}", (s or "").lower()))


# Quran anchor -> verse text
QV = {}
qh = (ROOT / "site/read/quran.html").read_text(encoding="utf-8")
for m in re.finditer(r'id="(s\d+v\d+)"[^>]*>.*?verse-text">(.*?)</span>', qh, re.S):
    QV[m.group(1)] = re.sub(r"<[^>]+>", "", m.group(2))

# Hadith anchor -> text (fawazahmed0)
HV = {}
for slug, stem in [("bukhari", "bukhari"), ("muslim", "muslim"), ("abu-dawud", "abudawud"),
                   ("tirmidhi", "tirmidhi"), ("nasai", "nasai"), ("ibn-majah", "ibnmajah")]:
    d = json.loads((ROOT / f"hadith-sunnah/eng-{stem}.json").read_text(encoding="utf-8"))
    HV[slug] = {str(x["hadithnumber"]): (x.get("text") or "") for x in d["hadiths"]}

VERSEBOX = re.compile(r'<div class="arg-verse-box">(.*?)</div>', re.S)
# a cite-link followed by the quoted text up to the next cite-link or end
SEG = re.compile(r'<a class="cite-link" href="\.\./\.\./read/([a-z-]+)\.html#([a-z0-9]+)">[^<]+</a>\s*[—\-:]?\s*(.*?)(?=<a class="cite-link"|$)', re.S)


def reader_text(slug, anchor):
    if slug == "quran":
        return QV.get(anchor, "")
    return HV.get(slug, {}).get(anchor.lstrip("h"), "")


ANCHOR = re.compile(r'href="\.\./\.\./read/([a-z-]+)\.html#([a-z0-9]+)"')


def main():
    flagged = []
    checked = 0
    for f in sorted(glob.glob(str(ROOT / "site/arguments/*/*.html"))):
        box = VERSEBOX.search(io.open(f, encoding="utf-8").read())
        if not box:
            continue
        # every source text cited anywhere in the box (quote may match any of them)
        srcs = [reader_text(s, a) for s, a in ANCHOR.findall(box.group(1))]
        srcwords = set().union(*[words(s) for s in srcs]) if srcs else set()
        if not srcwords:
            continue
        for _m in SEG.finditer(box.group(1)):
            raw = html.unescape(re.sub(r"<[^>]+>", "", _m.group(3))).strip()
            if re.match(r"(?i)(parallel|also|with |see |cf\.|similar)", raw):
                continue
            q = words(raw)
            if len(q) < 12:
                continue
            checked += 1
            ov = len(q & srcwords) / len(q)   # best match against ANY cited source in the box
            if ov < 0.35:
                rel = f.split("arguments")[1].replace("\\", "/").lstrip("/")
                flagged.append((round(ov, 2), rel))
    print(f"checked {checked} dossier scripture quotes")
    print(f"flagged (quote matches NONE of its box's cited sources — review): {len(flagged)}")
    for ov, rel in sorted(flagged)[:40]:
        print(f"  ov={ov}  {rel}")


if __name__ == "__main__":
    main()
