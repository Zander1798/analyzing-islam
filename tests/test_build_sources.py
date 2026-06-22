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
