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


def test_hadith_anchor_format():
    assert refs.hadith_anchor(224) == "h224"


def test_parse_hadith_basic():
    assert refs.parse_hadith_ref("Bukhari 224") == ("bukhari", 224)


def test_parse_hadith_slug_normalization():
    assert refs.parse_hadith_ref("Abu Dawud 1234") == ("abu-dawud", 1234)
    assert refs.parse_hadith_ref("Ibn Majah 90") == ("ibn-majah", 90)
    assert refs.parse_hadith_ref("Nasa'i 5397") == ("nasai", 5397)


def test_parse_hadith_letter_suffix_uses_leading_int():
    assert refs.parse_hadith_ref("Muslim 2020a") == ("muslim", 2020)


def test_parse_hadith_range_uses_start():
    assert refs.parse_hadith_ref("Tirmidhi 439-443") == ("tirmidhi", 439)


def test_parse_hadith_unknown_collection():
    with pytest.raises(refs.RefError):
        refs.parse_hadith_ref("Darimi 5")
