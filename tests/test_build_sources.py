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
