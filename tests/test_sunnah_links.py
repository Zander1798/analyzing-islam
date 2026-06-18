import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("sunnah_links", Path(__file__).parent.parent / "sunnah_links.py")
sl = importlib.util.module_from_spec(spec); spec.loader.exec_module(sl)

def test_slugs():
    assert sl.SUNNAH_SLUGS == {"bukhari":"bukhari","muslim":"muslim","abu-dawud":"abudawud",
                               "tirmidhi":"tirmidhi","nasai":"nasai","ibn-majah":"ibnmajah"}

def test_collection_url():
    assert sl.collection_url("abu-dawud") == "https://sunnah.com/abudawud"

def test_hadith_url():
    assert sl.hadith_url("bukhari", 224) == "https://sunnah.com/bukhari:224"
    assert sl.hadith_url("ibn-majah", 90) == "https://sunnah.com/ibnmajah:90"

def test_non_hadith_raises():
    with pytest.raises(KeyError):
        sl.hadith_url("quran", 1)
