# tests/test_build_sources.py
import subprocess, sys, json, importlib.util
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

def test_find_candidates_recall():
    _run("gather")  # ensure corpus exists for the file-level command
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
