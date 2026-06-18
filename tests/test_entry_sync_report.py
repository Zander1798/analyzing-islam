# tests/test_entry_sync_report.py
import importlib.util, json
from pathlib import Path

def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent.parent / fname)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_index_has_1524_after_rebuild():
    idx = json.loads((Path(__file__).parent.parent / "site/assets/data/catalog-entries.json").read_text(encoding="utf-8"))
    assert len(idx) == 1524, len(idx)
    from collections import Counter
    by = Counter(e["source"] for e in idx)
    assert by["quran"] == 275 and by["bukhari"] == 315 and by["muslim"] == 264
    assert by["abu-dawud"] == 181 and by["tirmidhi"] == 226
    assert by["nasai"] == 113 and by["ibn-majah"] == 150
