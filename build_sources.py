# build_sources.py
import argparse, json, re, html as ihtml
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DATA = SITE / "assets" / "data"
CATALOG_SOURCES = ["quran", "bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah"]
CORPUS = ROOT / "sources-corpus.json"

def gather():
    blocks, seen = [], set()
    for slug in CATALOG_SOURCES:
        soup = BeautifulSoup((SITE / "catalog" / f"{slug}.html").read_text(encoding="utf-8"), "html.parser")
        for e in soup.select(".entry[id]"):
            bid = e.get("id")
            if bid in seen:
                continue
            seen.add(bid)
            # prose only: <p>/<li> text; skip the <blockquote> verse quote.
            parts = [t.get_text(" ", strip=True) for t in e.select("p, li")]
            blocks.append({"block_id": bid, "origin": f"catalog:{slug}",
                           "text": re.sub(r"\s+", " ", " ".join(p for p in parts if p))})
    for slug in CATALOG_SOURCES:
        for arg in json.loads((ROOT / "arguments-data" / f"{slug}.json").read_text(encoding="utf-8")):
            chunks = [arg.get("context", "")]
            pr = arg.get("premises", "")
            chunks.append(" ".join(pr) if isinstance(pr, list) else pr)
            chunks.append(arg.get("conclusion", ""))
            for mr in arg.get("muslim_responses", []):
                chunks += [mr.get("response", ""), mr.get("counter", "")]
            blocks.append({"block_id": f"dossier:{slug}:{arg['id']}", "origin": f"dossier:{slug}",
                           "text": re.sub(r"\s+", " ", " ".join(c for c in chunks if c))})
    out = {"blocks": blocks, "block_ids": sorted(b["block_id"] for b in blocks)}
    CORPUS.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    ncat = sum(1 for b in blocks if b["origin"].startswith("catalog:"))
    print(f"gathered {len(blocks)} blocks ({ncat} catalog + {len(blocks) - ncat} dossier)")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gather", "candidates", "audit", "render"])
    args = ap.parse_args()
    if args.cmd == "gather":
        gather()

if __name__ == "__main__":
    main()
