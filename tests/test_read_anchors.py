# tests/test_read_anchors.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "read_anchors", Path(__file__).parent.parent / "read_anchors.py")
ra = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ra)


def test_quran_has_known_anchor():
    anchors = ra.read_anchor_set("quran")
    assert "s2v25" in anchors


def test_bukhari_has_known_anchor():
    anchors = ra.read_anchor_set("bukhari")
    assert "h224" in anchors          # "urinated standing at a dump"
    assert "h7277" in anchors         # last idInBook


def test_missing_page_returns_empty():
    assert ra.read_anchor_set("does-not-exist") == set()
