# report_entry_sync.py — book<->site reconciliation report (reporting only).
import json, re, sys
from collections import Counter
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).parent
IDX = ROOT / "site/assets/data/catalog-entries.json"
PRE = Path(ROOT / ".git/sdd/pre-sync-index.json")

def _key(e):
    return (e["source"], re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", e["title"])).strip().lower())

def build_report() -> dict:
    cur = json.loads(IDX.read_text(encoding="utf-8"))
    rep = {"total": len(cur), "by_source": dict(Counter(e["source"] for e in cur))}
    if PRE.exists():
        pre = json.loads(PRE.read_text(encoding="utf-8"))
        curk = {_key(e) for e in cur}; prek = {_key(e) for e in pre}
        rep["book_only"] = sorted(curk - prek)
        rep["site_only"] = sorted(prek - curk)
    return rep

def main():
    r = build_report()
    print(f"Total: {r['total']}  by_source: {r['by_source']}")
    print(f"book_only (new): {len(r.get('book_only', []))}")
    print(f"site_only (dropped): {len(r.get('site_only', []))}")
    for k in r.get("site_only", [])[:40]:
        print("  DROPPED:", k)

if __name__ == "__main__":
    main()
