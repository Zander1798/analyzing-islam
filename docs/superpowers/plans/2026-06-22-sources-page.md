# Sources Page (secondary-scholarship bibliography) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `site/sources.html` — a grouped bibliography of every secondary scholarly/apologetic/polemical work cited inside the 1,524 catalog entries + 140 dossiers — and link it from a new "Sources" section on the About page, with completeness enforced so nothing is silently missed.

**Architecture:** Deterministic Python (`build_sources.py`) does the testable parts: gather all entry/dossier prose into a corpus, run a regex "candidate net" over it, audit for un-captured name/title-shaped tokens, and render the page from a curated `sources.json`. The non-deterministic part — turning prose mentions into a clean, classified, de-duplicated bibliography — is a controller-orchestrated mining stage (parallel extraction agents grounded in the text) gated by the coverage + audit checks.

**Tech Stack:** Python 3 + BeautifulSoup4 (parsing/rendering), Python `re` (candidate net), pytest (unit tests), parallel subagents for extraction, static HTML on GitHub Pages.

## Global Constraints

- **Scope:** ONLY secondary works cited *inside* entry/dossier prose (scholarship, apologetics, polemics, academic, comparative). NOT the readable scripture sources (Quran translation, the six hadith collections, the external comparative readers) — those stay on the About page and must not be listed here.
- **Grouping (exactly these four `group` keys → titles):** `classical-islamic` → "Classical Islamic scholarship"; `academic` → "Academic & historical scholarship"; `apologetics` → "Apologetics & polemics"; `comparative` → "Other / comparative". Alphabetical within each group.
- **Per source:** display `name` + one-line `descriptor` only. No counts, no per-source link-backs on the page.
- **Completeness is build-blocking:** 100% of corpus blocks must be processed (coverage ledger asserted equal to the full block set); every pattern-net candidate must resolve to a source OR an explicit non-source; the completeness audit must end with `sources-unresolved.json` empty. A miss must surface as a build failure, never a silent drop.
- **Grounding:** every `sources.json` source must trace to ≥1 `entry_id` whose corpus text actually contains one of its `name`/`aliases`. Nothing invented.
- **Corpus:** catalog prose from the 7 `site/catalog/{slug}.html` files (dedupe by entry `id`; ignore `site/category/*` duplicates); dossier prose from `arguments-data/{slug}.json` fields `context`, `premises`, `conclusion`, `muslim_responses[].response/.counter` (NOT `verse_text`). `slug ∈ {quran,bukhari,muslim,abu-dawud,tirmidhi,nasai,ibn-majah}`.
- **Data source of truth:** `site/assets/data/sources.json` (curated, editable). The page is regenerated from it.
- **Deploy:** push `site/**` to `main` (GitHub Pages). Scratch JSON (`sources-corpus.json`, `sources-candidates.json`, `sources-raw.json`, `sources-unresolved.json`) is git-ignored, not shipped.

---

### Task 1: Corpus gathering (`build_sources.py gather`)

Parse every catalog entry + dossier argument into one corpus file with a block-id ledger.

**Files:**
- Create: `build_sources.py`
- Create: `tests/test_build_sources.py`
- Modify: `.gitignore` (ignore scratch JSON)
- Output (scratch): `sources-corpus.json`

**Interfaces:**
- Produces: `gather() -> dict` writing `sources-corpus.json` shaped
  `{"blocks": [{"block_id": str, "origin": str, "text": str}], "block_ids": [str sorted]}`.
  Catalog `block_id` = the entry `id`; dossier `block_id` = `"dossier:{slug}:{arg_id}"`.
  `CATALOG_SOURCES = ["quran","bukhari","muslim","abu-dawud","tirmidhi","nasai","ibn-majah"]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_build_sources.py
import subprocess, sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def _run(*args):
    subprocess.run([sys.executable, str(ROOT / "build_sources.py"), *args], cwd=ROOT, check=True)

def _corpus():
    return json.loads((ROOT / "sources-corpus.json").read_text(encoding="utf-8"))

def test_gather_covers_catalog_and_dossiers():
    _run("gather")
    c = _corpus()
    blocks = c["blocks"]
    ids = [b["block_id"] for b in blocks]
    assert len(ids) == len(set(ids)), "duplicate block ids"
    cat = [b for b in blocks if b["origin"].startswith("catalog:")]
    dos = [b for b in blocks if b["origin"].startswith("dossier:")]
    assert len(cat) >= 1500, f"expected ~1524 catalog entries, got {len(cat)}"
    assert len(dos) >= 138, f"expected ~140 dossiers, got {len(dos)}"
    assert all(b["text"].strip() for b in blocks), "a block has empty text"
    # ledger matches blocks exactly
    assert c["block_ids"] == sorted(ids)
    # a known scholarly mention is present in the gathered prose (grounding sanity)
    joined = " ".join(b["text"] for b in cat)
    assert "Rustomji" in joined or "Ibn Kathir" in joined
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_build_sources.py::test_gather_covers_catalog_and_dossiers -q`
Expected: FAIL — `build_sources.py` missing.

- [ ] **Step 3: Implement `gather` + the CLI**

```python
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_build_sources.py::test_gather_covers_catalog_and_dossiers -q`
Expected: PASS.

- [ ] **Step 5: Ignore scratch files + commit**

```bash
printf '\nsources-corpus.json\nsources-candidates.json\nsources-raw.json\nsources-unresolved.json\nsources-processed.json\n' >> .gitignore
git add build_sources.py tests/test_build_sources.py .gitignore
git commit -m "feat(sources): gather catalog + dossier prose into a corpus with block ledger"
```

---

### Task 2: Pattern candidate net (`build_sources.py candidates`)

A deterministic, recall-oriented regex pass that surfaces a superset of scholarly-source candidate strings per block (the backbone of the completeness guarantee).

**Files:**
- Modify: `build_sources.py` (add `find_candidates`, `candidates`, `SEED_VOCAB`, `STOPWORDS`, `CAND_PATTERNS`; wire `candidates` into `main`)
- Modify: `tests/test_build_sources.py`
- Output (scratch): `sources-candidates.json`

**Interfaces:**
- Produces: `find_candidates(text: str) -> list[str]` (sorted unique candidate strings); `candidates() -> dict` writing `sources-candidates.json` = `{"per_block": {block_id: [str]}, "all": [str sorted]}`. `find_candidates` is reused by the audit (Task 3).

- [ ] **Step 1: Write the failing test**

```python
def test_find_candidates_recall():
    _run("gather")  # ensure corpus exists for the file-level command
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_sources", ROOT / "build_sources.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    t = ("Nerina Rustomji, in The Garden and the Fire: Heaven and Hell in Islamic Culture "
         "(Columbia University Press, 2009), and al-Nawawi, and Tafsir Ibn Kathir, and "
         "Ibn Hajar's Fath al-Bari, and Kecia Ali (2006) all discuss this. Allah and Mecca do not.")
    cands = mod.find_candidates(t)
    flat = " || ".join(cands)
    for needed in ["al-Nawawi", "Ibn Hajar", "Kecia Ali", "Ibn Kathir", "Rustomji"]:
        assert any(needed in c for c in cands), f"candidate net missed {needed}: {flat}"
    # stopwords are not emitted as standalone candidates
    assert "Allah" not in cands and "Mecca" not in cands

def test_candidates_command_writes_per_block():
    _run("gather"); _run("candidates")
    data = json.loads((ROOT / "sources-candidates.json").read_text(encoding="utf-8"))
    assert data["all"], "no candidates found across corpus"
    assert any("Ibn Kathir" in c for c in data["all"])
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_build_sources.py -k candidates -q`
Expected: FAIL — `find_candidates`/`candidates` not defined.

- [ ] **Step 3: Implement the candidate net**

```python
# --- add to build_sources.py ---
CANDIDATES = ROOT / "sources-candidates.json"

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
    re.compile(r"\b(?:Tafsir|Sahih|Sunan|Musnad|Jami['ʿ’]?|Muwatta|Sira|Mishkat|Fath al-)[A-Za-z'’ʿ \-]{2,40}"),
    # Islamic name forms: al-/Ibn/Abu/Bin + Name (+ optional second name)
    re.compile(r"\b(?:al-|Ibn |Abu |Bin |ibn )[A-Z][\w'’ʿ\-]+(?:\s+[A-Z][\w'’ʿ\-]+)?"),
    # Author, in Title ... (Publisher?, Year)
    re.compile(r"[A-Z][\w'’.\-]+(?:\s+[A-Z][\w'’.\-]+){0,3},?\s+(?:in\s+)?['‘\"]?[A-Z][^()]{3,90}?\((?:[^)]*?\d{4})\)"),
    # Title Case multi-word + (Year)
    re.compile(r"[A-Z][A-Za-z'’.\-]+(?:\s+[A-Za-z'’.\-]+){1,8}\s\(\d{4}\)"),
]

def find_candidates(text):
    cands = set()
    for pat in _CAND_PATTERNS:
        for m in pat.finditer(text or ""):
            s = m.group(0).strip(" ,.;:’'\"")
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
```

Wire into `main`: add `elif args.cmd == "candidates": candidates()`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_build_sources.py -k candidates -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build_sources.py tests/test_build_sources.py
git commit -m "feat(sources): regex candidate net (recall superset) over the corpus"
```

---

### Task 3: Completeness audit (`build_sources.py audit`)

Re-scan the full corpus for any candidate not covered by a known source alias or the explicit non-source list, and write them to `sources-unresolved.json` — the gate that makes a miss build-blocking.

**Files:**
- Modify: `build_sources.py` (add `_norm`, `audit`; wire into `main`)
- Create: `non-sources.json` (starts as `[]`)
- Modify: `tests/test_build_sources.py`
- Output (scratch): `sources-unresolved.json`

**Interfaces:**
- Consumes: `site/assets/data/sources.json` (may not exist yet → treat as no sources), `non-sources.json`, `sources-corpus.json`, `find_candidates`.
- Produces: `audit() -> list` writing `sources-unresolved.json` = `[{"candidate": str, "blocks": [block_id ≤5], "count": int}]` sorted by count desc.

- [ ] **Step 1: Write the failing test**

```python
def test_audit_flags_uncovered_and_clears_when_covered():
    _run("gather")
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_sources", ROOT / "build_sources.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    data_dir = ROOT / "site" / "assets" / "data"; data_dir.mkdir(parents=True, exist_ok=True)
    src = data_dir / "sources.json"; ns = ROOT / "non-sources.json"
    backup = src.read_text(encoding="utf-8") if src.exists() else None
    nbackup = ns.read_text(encoding="utf-8") if ns.exists() else None
    try:
        # empty sources + empty non-sources → corpus has many uncovered candidates
        src.write_text(json.dumps({"groups": [], "sources": []}), encoding="utf-8")
        ns.write_text("[]", encoding="utf-8")
        unresolved = mod.audit()
        assert len(unresolved) > 0, "audit should flag uncovered candidates"
        # cover everything it flagged via aliases → unresolved must be empty
        aliases = [u["candidate"] for u in unresolved]
        src.write_text(json.dumps({"groups": [],
            "sources": [{"name": "X", "descriptor": "d", "group": "academic", "aliases": aliases, "entry_ids": []}]}),
            encoding="utf-8")
        assert mod.audit() == [], "audit should be empty once all candidates are covered"
    finally:
        if backup is not None: src.write_text(backup, encoding="utf-8")
        elif src.exists(): src.unlink()
        if nbackup is not None: ns.write_text(nbackup, encoding="utf-8")
        elif ns.exists(): ns.unlink()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_build_sources.py -k audit -q`
Expected: FAIL — `audit` not defined.

- [ ] **Step 3: Implement the audit**

```python
# --- add to build_sources.py ---
UNRESOLVED = ROOT / "sources-unresolved.json"
NON_SOURCES = ROOT / "non-sources.json"
SOURCES_JSON = DATA / "sources.json"

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
```

Wire into `main`: `elif args.cmd == "audit": audit()`. Create `non-sources.json` containing `[]`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_build_sources.py -k audit -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build_sources.py tests/test_build_sources.py non-sources.json
git commit -m "feat(sources): completeness audit (uncovered candidates -> sources-unresolved.json)"
```

---

### Task 4: Render the page (`build_sources.py render`)

Render `site/sources.html` from `sources.json`, grouped + alphabetical, in the site's dark style.

**Files:**
- Modify: `build_sources.py` (add `render`, `GROUP_ORDER`, `GROUP_TITLES`; wire into `main`)
- Modify: `tests/test_build_sources.py`
- Output: `site/sources.html`

**Interfaces:**
- Consumes: `site/assets/data/sources.json` = `{"groups":[{key,title}], "sources":[{name,descriptor,group,aliases,entry_ids}]}`.
- Produces: `render()` writing `site/sources.html`. `GROUP_ORDER = ["classical-islamic","academic","apologetics","comparative"]`.

- [ ] **Step 1: Write the failing test**

```python
def test_render_groups_and_escapes():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_sources", ROOT / "build_sources.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    data_dir = ROOT / "site" / "assets" / "data"; data_dir.mkdir(parents=True, exist_ok=True)
    src = data_dir / "sources.json"
    backup = src.read_text(encoding="utf-8") if src.exists() else None
    try:
        src.write_text(json.dumps({"groups": [
            {"key": "classical-islamic", "title": "Classical Islamic scholarship"},
            {"key": "academic", "title": "Academic & historical scholarship"},
            {"key": "apologetics", "title": "Apologetics & polemics"},
            {"key": "comparative", "title": "Other / comparative"}],
            "sources": [
              {"name": "Zebra Work <b>", "descriptor": "d1", "group": "academic", "aliases": [], "entry_ids": ["x"]},
              {"name": "Apple Work", "descriptor": "d2", "group": "academic", "aliases": [], "entry_ids": ["y"]},
              {"name": "Tafsir Ibn Kathir", "descriptor": "classical", "group": "classical-islamic", "aliases": [], "entry_ids": ["z"]}]}),
            encoding="utf-8")
        mod.render()
        html = (ROOT / "site" / "sources.html").read_text(encoding="utf-8")
        assert "Classical Islamic scholarship" in html and "Academic &amp; historical scholarship" in html
        assert "Tafsir Ibn Kathir" in html and "Apple Work" in html
        assert "&lt;b&gt;" in html and "Zebra Work <b>" not in html  # escaped
        assert html.index("Apple Work") < html.index("Zebra Work"), "not alphabetical within group"
        assert 'href="assets/css/style.css"' in html  # site chrome present
    finally:
        if backup is not None: src.write_text(backup, encoding="utf-8")
        elif src.exists(): src.unlink()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_build_sources.py -k render -q`
Expected: FAIL.

- [ ] **Step 3: Implement render**

Build the chrome by copying the `<head>` + `<nav class="site-nav">…</nav>` from `site/about.html` (so favicons/nav/scripts match) into module-level `_CHROME_HEAD`/`_CHROME_TAIL` constants in `build_sources.py`. Set the `<title>` to "Sources — Analyzing Islam", add an inline `<style>` block for `.src-group/.src-list/.src-name/.src-desc`, and the standard script block in the tail. Then:

```python
# --- add to build_sources.py ---
GROUP_ORDER = ["classical-islamic", "academic", "apologetics", "comparative"]

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
            '<span class="src-desc">' + ihtml.escape(s["descriptor"]) + '</span></li>'
            for s in items)
        body.append('<section class="src-group"><h2>' + ihtml.escape(titles.get(key, key)) +
                    '</h2><ul class="src-list">' + rows + '</ul></section>')
    body.append("</main>")
    (SITE / "sources.html").write_text(_CHROME_HEAD + "".join(body) + _CHROME_TAIL, encoding="utf-8")
    print(f"rendered site/sources.html ({sum(len(v) for v in by_group.values())} sources)")
```

Provide `_CHROME_HEAD` (doctype→ just after `<body>`+nav, including `<link rel="stylesheet" href="assets/css/style.css">`, the inline `<style>` below, and `<title>Sources — Analyzing Islam</title>`) and `_CHROME_TAIL` (footer + the standard deferred script block copied from about.html, including `track.js`). Inline style:

```css
.src-wrap{max-width:820px;margin:0 auto;padding:24px 16px 64px}
.src-intro{color:var(--muted,#888);margin:0 0 28px}
.src-group{margin-bottom:32px}
.src-group h2{font-size:16px;border-bottom:1px solid rgba(255,255,255,.15);padding-bottom:6px}
.src-list{list-style:none;padding:0;margin:0}
.src-list li{padding:8px 0;border-bottom:1px solid rgba(255,255,255,.06)}
.src-name{display:block;font-weight:600}
.src-desc{display:block;color:var(--muted,#9a9a9a);font-size:13px}
```

Wire into `main`: `elif args.cmd == "render": render()`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_build_sources.py -k render -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add build_sources.py tests/test_build_sources.py
git commit -m "feat(sources): render grouped sources.html from sources.json"
```

---

### Task 5: About-page "Sources" section

Add a "Sources" section under "Who this is for" linking to the new page in a new tab.

**Files:**
- Modify: `site/about.html`
- Modify: `tests/test_build_sources.py`

- [ ] **Step 1: Write the failing test**

```python
def test_about_has_sources_section():
    html = (ROOT / "site" / "about.html").read_text(encoding="utf-8")
    assert "Who this is for" in html
    i = html.index("Who this is for")
    rest = html[i:]
    assert "<h2>Sources</h2>" in rest, "Sources heading missing after Who-this-is-for"
    assert 'href="sources.html"' in rest and 'target="_blank"' in rest
    assert rest.index("<h2>Sources</h2>") < rest.index("</body>")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_build_sources.py -k about -q`
Expected: FAIL.

- [ ] **Step 3: Add the section to `about.html`**

Immediately AFTER the "Who this is for" `<ul>…</ul>` (the three audience bullets ending at `about.html` line ~171) and BEFORE the `<div style="margin-top:48px;…">` "Ready to start?" block, insert:

```html
  <h2>Sources</h2>
  <p>Beyond the primary scripture sources above, the entries draw on a wide body of secondary scholarship — classical tafsirs and hadith commentaries, fiqh manuals, academic histories, and apologetics and polemics from every side. The full list of works referenced across the catalog and dossiers is compiled here:</p>
  <p><a href="sources.html" target="_blank" rel="noopener" class="btn btn-primary">Browse all sources ↗</a></p>
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_build_sources.py -k about -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add site/about.html tests/test_build_sources.py
git commit -m "feat(sources): link a Sources section from the About page"
```

---

### Task 6: Mine the corpus into a complete `sources.json` (controller-orchestrated)

This is the extraction + curation stage. It is NOT a single-implementer code task — the **controller** runs it directly with parallel agents, gated by the deterministic tooling from Tasks 1–3. Produces `site/assets/data/sources.json` and the populated `non-sources.json`.

**Files:**
- Create/populate: `site/assets/data/sources.json`
- Populate: `non-sources.json`

- [ ] **Step 1: Generate the inputs**

Run: `python build_sources.py gather && python build_sources.py candidates`
Expected: `sources-corpus.json` (~1,664 blocks) and `sources-candidates.json` written.

- [ ] **Step 2: Parallel extraction (fan out over the corpus, 100% coverage)**

Split `sources-corpus.json` blocks into batches of ~40. For EACH batch, dispatch an extraction agent with this contract (the batch's blocks + their `sources-candidates.json` entries pasted in as a file path the agent reads):

> "You are extracting cited secondary sources from catalog/dossier prose. For each block you are given its text and a list of regex-detected candidate strings. Emit a JSON array of records `{block_id, raw_mention, normalized_name, group, descriptor}` for every secondary scholarly/apologetic/polemical work NAMED IN THE TEXT — tafsirs, hadith commentaries, fiqh manuals, sira, academic books/authors, named apologists/polemicists, comparative (biblical/Jewish) works. `group` ∈ {classical-islamic, academic, apologetics, comparative}. `descriptor` = one neutral factual line (≤12 words). RULES: (1) only works literally present in the text — never invent; (2) you MUST account for every candidate string handed to you: either map it to a source record OR list it in a `non_sources` array with a one-word reason (e.g. place, person-not-a-source, scripture, generic) — do not silently drop a candidate; (3) exclude the readable scripture sources themselves (Quran/Saheeh International, the six hadith collections, the comparative readers)."

Each extraction agent MUST report the full list of `block_id`s it was given (even blocks where it found zero sources), so coverage can be proven independently of whether a block yielded any source. Collect all agent outputs into `sources-raw.json` (flat list of source records), the union of all reported processed ids into `sources-processed.json` (a flat JSON array of `block_id`), and the union of all `non_sources` into `non-sources.json`.

- [ ] **Step 3: Coverage gate**

Assert every corpus block was processed (a block with no sources still counts only if it appears in the processed ledger):
```bash
python - <<'PY'
import json
from pathlib import Path
R = Path(".")
corpus = {b["block_id"] for b in json.loads((R/"sources-corpus.json").read_text(encoding="utf-8"))["blocks"]}
processed = set(json.loads((R/"sources-processed.json").read_text(encoding="utf-8")))
missing = corpus - processed
print("MISSING BLOCKS:", len(missing), sorted(missing)[:20])
assert not missing, "every corpus block must be processed"
print("coverage OK")
PY
```
If any block is missing, dispatch extraction for exactly those blocks, append to the ledger, and repeat until 0 missing.

- [ ] **Step 4: Curate + normalize into `sources.json`**

Dispatch a curation agent (or do it directly) over `sources-raw.json`: merge records that refer to the same work into one canonical `{name, descriptor, group, aliases[], entry_ids[]}` (collect every `raw_mention`/`normalized_name` variant into `aliases`, and every `block_id` into `entry_ids`); pick the clearest `name` and one neutral `descriptor`; resolve group conflicts; drop anything that is actually a scripture source or a non-source. Write `site/assets/data/sources.json` with the four `groups` (keys/titles per Global Constraints) and the merged `sources`. Ensure `aliases` are broad enough that the audit's substring match will recognise every raw phrasing.

- [ ] **Step 5: Completeness audit loop (the "nothing slipped" gate)**

```bash
python build_sources.py audit
```
Read `sources-unresolved.json`. For EVERY entry: either (a) it's a real source missed in curation → add it (or an alias) to `sources.json`; or (b) it's not a source → add it to `non-sources.json`. Re-run `python build_sources.py audit`. Repeat until `sources-unresolved.json` is `[]`. Do not proceed while it is non-empty.

- [ ] **Step 6: Grounding gate**

```bash
python - <<'PY'
import json, re
from pathlib import Path
R=Path("."); SITE=R/"site"
corpus={b["block_id"]: b["text"] for b in json.loads((R/"sources-corpus.json").read_text(encoding="utf-8"))["blocks"]}
src=json.loads((SITE/"assets/data/sources.json").read_text(encoding="utf-8"))["sources"]
bad=[]
for s in src:
    names=[s["name"]]+s.get("aliases",[])
    ok=any(any(n.lower() in corpus.get(eid,"").lower() for n in names) for eid in s.get("entry_ids",[]))
    if not ok: bad.append(s["name"])
print("UNGROUNDED:", bad[:20]); assert not bad, "every source must appear in one of its entry_ids"
print("grounding OK")
PY
```
Fix any ungrounded source (correct its `entry_ids`/`aliases`) until this passes.

- [ ] **Step 7: Render + commit**

```bash
python build_sources.py render
git add site/assets/data/sources.json non-sources.json site/sources.html
git commit -m "feat(sources): mined + curated sources.json and rendered sources.html"
```

---

### Task 7: Full pipeline verification + deploy

**Files:** none (verification + deploy).

- [ ] **Step 1: Unit tests + gates green**

```bash
python -m pytest tests/test_build_sources.py -q
python build_sources.py gather && python build_sources.py candidates && python build_sources.py audit
test "$(python -c "import json;print(len(json.load(open('sources-unresolved.json'))))")" = "0" && echo "AUDIT CLEAN"
```
Expected: all unit tests pass; audit reports 0 unresolved.

- [ ] **Step 2: Spot-check the page locally**

Run `python -m http.server 8765 --directory site`, open `http://localhost:8765/sources.html` and `http://localhost:8765/about.html`. Confirm: four groups in order, alphabetical within, descriptors read well, the About "Sources" button opens `sources.html` in a new tab. Skim for any obviously-missing major source (Ibn Kathir, al-Tabari, al-Nawawi, Ibn Hajar, Kecia Ali, Goldziher) — each must be present.

- [ ] **Step 3: Deploy**

```bash
git push origin main
gh run watch "$(gh run list --workflow=pages.yml --limit 1 --json databaseId -q '.[0].databaseId')" --exit-status
```

- [ ] **Step 4: Live confirm**

`curl -s -o /dev/null -w "%{http_code}\n" https://analyzingislam.com/sources.html` → 200; hard-refresh About and confirm the Sources section + link.

---

## Notes for the implementer

- **Completeness is the headline requirement.** Tasks 1–3 build the gates; Task 6 must drive `sources-unresolved.json` to empty and pass the coverage + grounding gates before anything ships. A non-empty unresolved file = not done.
- **The candidate net over-captures on purpose** (place names, generic Title-Case). That's fine — each false positive is recorded once in `non-sources.json` and stays resolved on re-runs.
- **Don't hand Task 6 to a single implementer subagent** — it's a controller-run fan-out. Tasks 1–5 and 7 are normal implementer tasks.
- **`descriptor` accuracy:** keep neutral and factual; if unsure what a work is, flag it in curation rather than guessing.
