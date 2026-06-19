#!/usr/bin/env python3
"""Apply re-classified strength levels (Basic/Moderate/Strong) to the SITE.

Reads a results file mapping entry id (slug) -> level, then updates:
  - data-strength="..." on each entry div  (catalog/*.html + category/*.html)
  - the <span class="tag strength-X">Level</span> badge inside that entry
  - the `strength` field in assets/data/catalog-entries.json

Book data is intentionally left untouched (the books are synced from the site
later, in a separate pass). stats.html numbers + the about/faq copy are handled
separately. Run with --check to preview the new distribution without writing.
"""
import io, json, re, glob, sys, collections
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS = ROOT / ".git/sdd/reclassify/_results.json"   # { id: "Basic"|"Moderate"|"Strong" }
LC = {"Basic": "basic", "Moderate": "moderate", "Strong": "strong"}


def load_map():
    raw = json.loads(RESULTS.read_text(encoding="utf-8"))
    # accept {classifications:[{id,level}]} or flat {id:level}
    if isinstance(raw, dict) and "classifications" in raw:
        return {c["id"]: c["level"] for c in raw["classifications"]}
    if isinstance(raw, list):
        return {c["id"]: c["level"] for c in raw}
    return raw


ENTRY = re.compile(r'(<div class="entry" id="([^"]+)"[^>]*data-strength=")([a-z]+)(")')
BADGE = re.compile(r'(<span class="tag strength-)[a-z]+(">)[A-Za-z]+(</span>)')


def apply(mp, check=False):
    changed = collections.Counter()
    missing = 0
    for f in glob.glob(str(ROOT / "site/catalog/*.html")) + glob.glob(str(ROOT / "site/category/*.html")):
        t = io.open(f, encoding="utf-8").read()
        parts = re.split(r'(?=<div class="entry" id=)', t)
        for i, p in enumerate(parts):
            m = re.match(r'<div class="entry" id="([^"]+)"', p)
            if not m:
                continue
            eid = m.group(1)
            lvl = mp.get(eid)
            if not lvl:
                continue
            lc = LC[lvl]
            p2 = ENTRY.sub(lambda mm: mm.group(1) + lc + mm.group(4), p, count=1)
            p2 = BADGE.sub(lambda mm: mm.group(1) + lc + mm.group(2) + lvl + mm.group(3), p2, count=1)
            if p2 != p:
                parts[i] = p2
                changed[lvl] += 1
        if not check:
            io.open(f, "w", encoding="utf-8").write("".join(parts))
    # index json
    idx = ROOT / "site/assets/data/catalog-entries.json"
    d = json.loads(idx.read_text(encoding="utf-8"))
    rows = d if isinstance(d, list) else d.get("entries", [])
    jchanged = 0
    for e in rows:
        lvl = mp.get(e.get("id"))
        if lvl and e.get("strength") != LC[lvl]:
            e["strength"] = LC[lvl]; jchanged += 1
    if not check:
        idx.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    # new distribution from the map itself
    dist = collections.Counter(mp.values())
    print(("CHECK " if check else "") + f"new distribution: {dict(dist)} (total {sum(dist.values())})")
    print(f"HTML entry-badges updated: {dict(changed)} | json strength fields updated: {jchanged}")


if __name__ == "__main__":
    mp = load_map()
    apply(mp, check="--check" in sys.argv)
