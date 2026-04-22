#!/usr/bin/env python3
"""Targeted refinement of anchor maps for specific cited-unmapped anchors.

Loads existing anchor-map-*.json, identifies anchors actually cited by the
catalog that are still unmapped, and runs difflib ratio matching to resolve
them. Fast (~1 min) because the pool is small (<100 anchors).

Prints the proposed matches with similarity scores, lets you eyeball them.
Accepts matches with ratio >= 0.7. Writes the updated map in-place.
"""
import html as html_lib
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent

_SYNONYMS = [
    (re.compile(r"\bapostles?\b"), "messenger"),
    (re.compile(r"\bmay peace be upon him\b"), ""),
    (re.compile(r"\bpeace be upon him\b"), ""),
]


def normalize(s: str) -> str:
    s = html_lib.unescape(s or "")
    s = re.sub(r"(\w)-\s+(\w)", r"\1\2", s)  # undo PDF hyphenation
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("(ﷺ)", "").replace("ﷺ", "")
    s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    for pat, repl in _SYNONYMS:
        s = pat.sub(repl, s)
    return " ".join(s.split())


OLD_HADITH_RE = re.compile(
    r'<article class="hadith" id="(?P<id>[^"]+)">.*?'
    r'(?:<div class="hadith-narrator">(?P<narrator>.*?)</div>)?'
    r'\s*(?P<paras>(?:<p>.*?</p>\s*)+)'
    r'</div>\s*</article>',
    re.S,
)
OLD_PARA_RE = re.compile(r"<p>(.*?)</p>", re.S)


def parse_old(path: Path, needed_ids: set[str]) -> dict[str, str]:
    """Return {id: normalized_text} for each needed id."""
    txt = path.read_text(encoding="utf-8")
    out = {}
    for m in OLD_HADITH_RE.finditer(txt):
        hid = m.group("id")
        if hid not in needed_ids:
            continue
        narrator = (m.group("narrator") or "").strip()
        paras = OLD_PARA_RE.findall(m.group("paras"))
        body = " ".join(paras).strip()
        out[hid] = normalize(narrator + " " + body)[:500]
    return out


def load_new(json_path: Path) -> list[tuple[int, str]]:
    """Return [(idInBook, normalized_text), ...] for all hadiths."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    out = []
    for h in data["hadiths"]:
        eng = h.get("english") or {}
        narr = (eng.get("narrator") or "").strip()
        txt = (eng.get("text") or "").strip()
        out.append((h["idInBook"], normalize(narr + " " + txt)[:500]))
    return out


def _word_set(s: str) -> frozenset[str]:
    """Content-word set from a normalized text, dropping short/stopwords."""
    stop = {
        "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at",
        "for", "with", "by", "from", "as", "is", "are", "was", "were", "be",
        "he", "she", "it", "they", "we", "you", "me", "him", "her", "them",
        "his", "their", "that", "this", "then", "so", "not", "has", "have",
        "had", "who", "what", "which", "how", "why", "will", "would", "may",
        "can", "said", "says", "asked", "about",
    }
    return frozenset(w for w in s.split() if len(w) > 2 and w not in stop)


def best_match(old_text: str, new_list: list[tuple[int, str]]) -> tuple[float, int | None]:
    """Two-stage fast matcher:

    1) Shortlist by word-set Jaccard similarity (O(N), cheap)
    2) Rerank top 30 by difflib ratio (accurate, but run on shortlist only)
    """
    old_set = _word_set(old_text)
    if not old_set:
        return 0.0, None

    # Stage 1: score all, keep top 30 by Jaccard.
    scored = []
    for nid, ntxt in new_list:
        ns = _word_set(ntxt)
        if not ns:
            continue
        inter = len(old_set & ns)
        if inter == 0:
            continue
        union = len(old_set | ns)
        jaccard = inter / union
        scored.append((jaccard, nid, ntxt))
    scored.sort(reverse=True)
    shortlist = scored[:30]
    if not shortlist:
        return 0.0, None

    # Stage 2: difflib ratio on shortlist.
    best_ratio = 0.0
    best_id = None
    sm = SequenceMatcher(None, autojunk=False)
    sm.set_seq1(old_text)
    for _, nid, ntxt in shortlist:
        sm.set_seq2(ntxt)
        r = sm.ratio()
        if r > best_ratio:
            best_ratio = r
            best_id = nid
    return best_ratio, best_id


def cited_anchors(pattern: str) -> set[str]:
    import os
    out = set()
    for root in ["site/catalog", "site/category"]:
        for f in os.listdir(root):
            if not f.endswith(".html"):
                continue
            txt = open(f"{root}/{f}", encoding="utf-8").read()
            out.update(re.findall(pattern, txt))
    return out


def refine(label: str, old_path: Path, json_path: Path, map_path: Path,
           href_pattern: str) -> None:
    print(f"\n=== {label} ===")
    data = json.loads(map_path.read_text(encoding="utf-8"))
    map_current = data.get("map", data)
    cited = cited_anchors(href_pattern)
    unmapped = [a for a in cited if a not in map_current]
    if not unmapped:
        print(f"  All {len(cited)} cited anchors already mapped.")
        return
    print(f"  {len(unmapped)} cited anchors still unmapped")

    old_texts = parse_old(old_path, set(unmapped))
    new_list = load_new(json_path)
    print(f"  matching against {len(new_list)} new hadiths...")

    added = {}
    for i, aid in enumerate(unmapped, 1):
        otext = old_texts.get(aid)
        if not otext:
            print(f"  [{i}/{len(unmapped)}] {aid}: missing in old reader (cannot match)")
            continue
        score, match = best_match(otext, new_list)
        marker = "✓" if score >= 0.70 else ("?" if score >= 0.55 else "✗")
        print(f"  [{i}/{len(unmapped)}] {aid}: best={match} (score={score:.2f}) {marker}")
        if score >= 0.60:
            added[aid] = match

    if not added:
        print(f"  nothing accepted (threshold 0.60)")
        return

    map_current.update(added)
    # Write back in the same shape as the original file.
    if "map" in data:
        data["map"] = map_current
    else:
        data = map_current
    map_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  wrote {len(added)} new mappings to {map_path.name}")


def main() -> None:
    import sys as _sys
    only = _sys.argv[1] if len(_sys.argv) > 1 else None
    if only in (None, "bukhari"):
        refine(
            "Bukhari",
            ROOT / "site" / "read" / "bukhari.html.old",
            ROOT / "hadith-json" / "bukhari.json",
            ROOT / "anchor-map-bukhari.json",
            r'href="\.\./read/bukhari\.html#(v\d+b\d+n\d+)"',
        )
    if only in (None, "muslim"):
        refine(
            "Muslim",
            ROOT / "site" / "read" / "muslim.html.old",
            ROOT / "hadith-json" / "muslim.json",
            ROOT / "anchor-map-muslim.json",
            r'href="\.\./read/muslim\.html#(b\d+n\d+)"',
        )


if __name__ == "__main__":
    main()
