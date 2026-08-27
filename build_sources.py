# build_sources.py
import argparse, json, re, html as ihtml
from pathlib import Path
from bs4 import BeautifulSoup

GROUP_ORDER = ["classical-islamic", "academic", "apologetics", "comparative"]

_CHROME_HEAD = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Secondary scholarship, apologetics, and polemics referenced across the catalog entries and dossiers.">
<!-- Favicon + app-icon set (browser tab, iOS home-screen, Android manifest) -->
<link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16.png">
<link rel="icon" href="/assets/icons/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/assets/icons/site.webmanifest">
<meta name="theme-color" content="#000000">
<!-- Open Graph (link preview on WhatsApp, Facebook, LinkedIn, Slack, Discord, etc.) -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="Analyzing Islam">
<meta property="og:title" content="Sources — Analyzing Islam">
<meta property="og:description" content="Secondary scholarship, apologetics, and polemics referenced across the catalog entries and dossiers.">
<meta property="og:url" content="https://analyzingislam.com/sources.html">
<meta property="og:image" content="https://analyzingislam.com/assets/og-image-v2.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Analyzing Islam — 1,524 entries across 31 categories">
<!-- Twitter / X card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Sources — Analyzing Islam">
<meta name="twitter:description" content="Secondary scholarship, apologetics, and polemics referenced across the catalog entries and dossiers.">
<meta name="twitter:image" content="https://analyzingislam.com/assets/og-image-v2.jpg">
<title>Sources — Analyzing Islam</title>
<link rel="stylesheet" href="assets/css/style.css">
<style>
.src-wrap{max-width:820px;margin:0 auto;padding:24px 16px 64px}
.src-intro{color:var(--muted,#888);margin:0 0 28px}
.src-group{margin-bottom:32px}
.src-group h2{font-size:16px;border-bottom:1px solid rgba(255,255,255,.15);padding-bottom:6px}
.src-list{list-style:none;padding:0;margin:0}
.src-list li{padding:8px 0;border-bottom:1px solid rgba(255,255,255,.06)}
.src-name{display:block;font-weight:600}
.src-desc{display:block;color:var(--muted,#9a9a9a);font-size:13px}
</style>
</head>
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
      <a href="index.html">Home</a>
      <a href="catalog.html">Catalog</a>
      <a href="arguments.html">Dossiers</a>
      <a href="read.html">Read</a>
      <a href="compare.html">Compare</a>
      <a href="build.html">Build</a>
      <a href="watch.html">Watch</a>
      <a href="stats.html">Stats</a>
      <a href="about.html">About</a>
      <a href="faq.html">FAQ</a>
    </div>
  </div>
</nav>
"""

_CHROME_TAIL = """
<footer class="site-footer">
  Built from the Saheeh International translation. Every entry references a specific verse — verify before citing.
</footer>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2" defer></script>
<script src="assets/js/config.js"></script>
<script src="assets/js/auth.js" defer></script>
<script src="assets/js/auth-ui.js" defer></script>
<script src="assets/js/track.js" defer></script>

<script src="assets/js/goat-skins.js" defer></script>
<script src="assets/js/goat.js" defer></script>
<script src="assets/js/snap-to-hash.js" defer></script>
</body>
</html>
"""

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
    # Dossiers: mine the RENDERED HTML under site/arguments/{slug}/ — the
    # arguments-data/*.json is stale (the dossier scholarship upgrade was written
    # into the HTML, not the JSON). Skip index/landing pages.
    for slug in CATALOG_SOURCES:
        dossier_dir = SITE / "arguments" / slug
        if not dossier_dir.is_dir():
            continue
        for path in sorted(dossier_dir.glob("*.html")):
            stem = path.stem
            if stem in ("index", slug):
                continue
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            main = soup.find("main") or soup
            parts = [t.get_text(" ", strip=True) for t in main.select("p, li")]
            blocks.append({"block_id": f"dossier:{slug}:{stem}", "origin": f"dossier:{slug}",
                           "text": re.sub(r"\s+", " ", " ".join(p for p in parts if p))})
    out = {"blocks": blocks, "block_ids": sorted(b["block_id"] for b in blocks)}
    CORPUS.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    ncat = sum(1 for b in blocks if b["origin"].startswith("catalog:"))
    print(f"gathered {len(blocks)} blocks ({ncat} catalog + {len(blocks) - ncat} dossier)")
    return out

def _norm(s):
    s = (s or "").lower()
    s = re.sub(r"[''']s\b", "", s)   # drop possessive 's (straight or curly)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

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
            if any((len(cov) >= 4 and cov in nc) or nc in cov for cov in covered):
                continue
            if any((len(ns) >= 4 and ns in nc) or nc in ns for ns in nonset):
                continue
            unresolved.setdefault(c, []).append(b["block_id"])
    out = [{"candidate": c, "blocks": ids[:5], "count": len(ids)}
           for c, ids in sorted(unresolved.items(), key=lambda kv: -len(kv[1]))]
    UNRESOLVED.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(out)} unresolved candidates")
    return out

def render():
    data = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    titles = {g["key"]: g["title"] for g in data["groups"]}
    by_group = {}
    for s in data["sources"]:
        by_group.setdefault(s["group"], []).append(s)
    body = ['<main class="src-wrap"><h1>Sources</h1>',
            '<p class="src-intro">Secondary scholarship, apologetics, and polemics referenced '
            'across the catalog entries and dossiers. The primary scripture sources are listed on the '
            '<a href="about.html">About</a> page.</p>']
    for key in GROUP_ORDER:
        items = sorted(by_group.get(key, []), key=lambda s: s["name"].lower())
        if not items:
            continue
        rows = "".join(
            '<li><span class="src-name">' + ihtml.escape(s["name"]) + '</span>'
            '<span class="src-desc">' + ihtml.escape(s.get("descriptor", "")) + '</span></li>'
            for s in items)
        body.append('<section class="src-group"><h2>' + ihtml.escape(titles.get(key, key)) +
                    '</h2><ul class="src-list">' + rows + '</ul></section>')
    body.append("</main>")
    (SITE / "sources.html").write_text(_CHROME_HEAD + "".join(body) + _CHROME_TAIL, encoding="utf-8")
    print(f"rendered site/sources.html ({sum(len(v) for v in by_group.values())} sources)")

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
    elif args.cmd == "render":
        render()

if __name__ == "__main__":
    main()
