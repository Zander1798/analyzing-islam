import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "refs", Path(__file__).parent.parent / "refs.py")
refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refs)


def test_quran_anchor_format():
    assert refs.quran_anchor(2, 25) == "s2v25"


def test_parse_quran_single():
    assert refs.parse_quran_ref("Q 2:25") == [(2, 25)]


def test_parse_quran_multi():
    # comma-separated distinct refs, source order preserved
    assert refs.parse_quran_ref("Q 2:154,3:169–170") == [(2, 154), (3, 169)]


def test_parse_quran_range_uses_start():
    # en-dash range -> start verse only
    assert refs.parse_quran_ref("Q 27:15–44") == [(27, 15)]
    # ascii hyphen range
    assert refs.parse_quran_ref("Q 9:5-6") == [(9, 5)]


def test_parse_quran_bad():
    with pytest.raises(refs.RefError):
        refs.parse_quran_ref("Bukhari 224")
