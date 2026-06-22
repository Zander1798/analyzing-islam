# build_sources.py
import argparse, json, re, html as ihtml
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DATA = SITE / "assets" / "data"
CATALOG_SOURCES = ["quran", "bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah"]
CORPUS = ROOT / "sources-corpus.json"
CANDIDATES = ROOT / "sources-candidates.json"
UNRESOLVED = ROOT / "sources-unresolved.json"
NON_SOURCES = ROOT / "non-sources.json"
SOURCES_JSON = DATA / "sources.json"

# Known recurring scholars/works — guarantees the long tail is caught regardless of LLM.
SEED_VOCAB = [
    "Ibn Kathir", "al-Tabari", "al-Qurtubi", "Ibn Hajar", "al-Nawawi", "Fath al-Bari",
    "Reliance of the Traveller", "Ibn Ishaq", "al-Ghazali", "Ibn Taymiyya", "al-Suyuti",
    "Ibn Sa'd", "al-Waqidi", "al-Baladhuri", "al-Baydawi", "Ibn Abbas", "al-Razi",
    "Kecia Ali", "Fatima Mernissi", "Leila Ahmed", "Ignaz Goldziher", "Goldziher",
    "Patricia Crone", "Joseph Schacht", "Montgomery Watt", "Nerina Rustomji",
    "Jonathan Brown", "Wael Hallaq", "John Wansbrough", "Theodor Noldeke", "Noldeke",
]
# Capitalized phrases that are never bibliographic sources.
STOPWORDS = {
    "The Quran", "The Hadith", "The Prophet", "The Bible", "The Torah", "The Gospel",
    "Allah", "Muhammad", "Mecca", "Medina", "Saudi Arabia", "Sunni", "Shia", "Islam",
    "Muslim", "Muslims", "God", "Jesus", "Mary", "Moses", "Abraham", "Aisha", "Ali",
    "Day of Judgment", "Day of Resurrection", "Mount Uhud", "Banu Qurayza", "Saheeh International",
}

_CAND_PATTERNS = [
    # work-type prefixes: Tafsir/Sahih/Sunan/Musnad/Jami'/Muwatta/Sira/Mishkat/Fath al-...
    re.compile(r"\b(?:Tafsir|Sahih|Sunan|Musnad|Jami['ʿ']?|Muwatta|Sira|Mishkat|Fath al-)[A-Za-z''ʿ \-]{2,40}"),
    # Islamic name forms: al-/Ibn/Abu/Bin + Name (+ optional second name)
    re.compile(r"\b(?:al-|Ibn |Abu |Bin |ibn )[A-Z][\w''ʿ\-]+(?:\s+[A-Z][\w''ʿ\-]+)?"),
    # Author, in Title ... (Publisher?, Year)
    re.compile(r"[A-Z][\w''.\-]+(?:\s+[A-Z][\w''.\-]+){0,3},?\s+(?:in\s+)?[''\"]?[A-Z][^()]{3,90}?\((?:[^)]*?\d{4})\)"),
    # Title Case multi-word + (Year)
    re.compile(r"[A-Z][A-Za-z''.\-]+(?:\s+[A-Za-z''.\-]+){1,8}\s\(\d{4}\)"),
]

def find_candidates(text):
    cands = set()
    for pat in _CAND_PATTERNS:
        for m in pat.finditer(text or ""):
            s = m.group(0).strip(" ,.;:''\"")
            if len(s) >= 3:
                cands.add(s)
    for name in SEED_VOCAB:
        if re.search(r"\b" + re.escape(name) + r"\b", text or ""):
            cands.add(name)
    return sorted(c for c in cands if c not in STOPWORDS)

def candidates():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    per_block, allc = {}, set()
    for b in corpus["blocks"]:
        cs = find_candidates(b["text"])
        if cs:
            per_block[b["block_id"]] = cs
            allc.update(cs)
    out = {"per_block": per_block, "all": sorted(allc)}
    CANDIDATES.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"{len(allc)} unique candidates across {len(per_block)} blocks")
    return out

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

def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def audit():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))["sources"] if SOURCES_JSON.exists() else []
    nonsrc = json.loads(NON_SOURCES.read_text(encoding="utf-8")) if NON_SOURCES.exists() else []
    covered = set()
    for s in sources:
        for a in [s["name"]] + s.get("aliases", []):
            n = _norm(a)
            if n:
                covered.add(n)
    nonset = {_norm(x) for x in nonsrc if _norm(x)}
    unresolved = {}
    for b in corpus["blocks"]:
        for c in find_candidates(b["text"]):
            nc = _norm(c)
            if not nc:
                continue
            if any(cov in nc or nc in cov for cov in covered):
                continue
            if any(ns in nc or nc in ns for ns in nonset):
                continue
            unresolved.setdefault(c, []).append(b["block_id"])
    out = [{"candidate": c, "blocks": ids[:5], "count": len(ids)}
           for c, ids in sorted(unresolved.items(), key=lambda kv: -len(kv[1]))]
    UNRESOLVED.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(out)} unresolved candidates")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gather", "candidates", "audit", "render"])
    args = ap.parse_args()
    if args.cmd == "gather":
        gather()
    elif args.cmd == "candidates":
        candidates()
    elif args.cmd == "audit":
        audit()

if __name__ == "__main__":
    main()
