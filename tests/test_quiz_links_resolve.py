import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("vl", Path(__file__).parent.parent / "validate_links.py")
vl = importlib.util.module_from_spec(spec); spec.loader.exec_module(vl)

def test_quiz_source_links_resolve():
    pairs = vl._quiz_source_pairs(vl.SITE)
    assert len(pairs) > 0, "no quiz source links found"
    assert vl.unresolved_links(pairs) == []
