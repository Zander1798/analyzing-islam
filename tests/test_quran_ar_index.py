# tests/test_quran_ar_index.py
#
# Guards the Arabic -> verse-reference index the Build editor's translator uses.
#
# The critical invariant is that normalise() here and normaliseArabic() in
# site/assets/js/quran-lookup.js behave identically. If they drift, the index is
# keyed one way and queried another, and every translation silently misses.
# The expectations below are duplicated verbatim in tests/test_quran_lookup.mjs
# so a change on either side breaks a test on that side.
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
INDEX = ROOT / "site" / "assets" / "data" / "quran-ar-index.json"
READER = ROOT / "site" / "read" / "quran"

EXPECTED_VERSES = 6236
EXPECTED_SURAHS = 114


def _load():
    spec = importlib.util.spec_from_file_location(
        "build_quran_ar_index", ROOT / "build-quran-ar-index.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


builder = _load()


@pytest.fixture(scope="module")
def index():
    if not INDEX.is_file():
        pytest.fail(f"{INDEX} missing — run: python build-quran-ar-index.py")
    return json.loads(INDEX.read_text(encoding="utf-8"))


def test_index_covers_the_whole_quran(index):
    assert len(index["counts"]) == EXPECTED_SURAHS
    assert sum(index["counts"]) == EXPECTED_VERSES
    assert len(index["starts"]) == EXPECTED_VERSES


def test_normalise_matches_the_javascript_side():
    # Same assertions as tests/test_quran_lookup.mjs.
    assert builder.normalise("ٱلۡكِتَٰبِ") == "الكتب"
    assert builder.normalise("الكتاب") == "الكتاب"
    assert builder.normalise("6 And they say, — ٱلذِّكۡرُ") == "الذكر"
    assert builder.normalise("no arabic here at all") == ""


def test_normalise_folds_uthmani_and_plain_to_one_loose_key():
    loose = lambda s: s.replace("ا", "").replace("ء", "").replace(" ", "")
    assert loose(builder.normalise("ٱلۡكِتَٰبِ")) == loose(builder.normalise("الكتاب"))
    assert loose(builder.normalise("يَـٰٓأَيُّهَا")) == loose(builder.normalise("يا أيها"))


def test_no_verse_normalises_to_an_empty_key(index):
    starts, corpus = index["starts"], index["corpus"]
    for k, start in enumerate(starts):
        end = starts[k + 1] - 1 if k + 1 < len(starts) else len(corpus)
        assert end > start, f"verse #{k + 1} has an empty key"


def test_surah_separator_prevents_cross_surah_matches(index):
    # Verses inside a surah are joined by " "; surahs by "\n". A newline must
    # sit at every surah boundary or a selection could match across two surahs.
    corpus, starts, counts = index["corpus"], index["starts"], index["counts"]
    at = 0
    for n in counts[:-1]:
        at += n
        boundary = starts[at] - 1
        assert corpus[boundary] == "\n", f"missing surah separator before verse #{at + 1}"


def test_committed_index_is_current():
    # A reader rebuild that changed any Arabic would leave this stale, and the
    # translator would fail to resolve exactly the verses that changed.
    if not READER.is_dir():
        pytest.skip("split Qur'an reader not present in this checkout")
    fresh = builder.serialise(builder.build())
    assert INDEX.read_text(encoding="utf-8") == fresh, (
        "quran-ar-index.json is stale — re-run: python build-quran-ar-index.py"
    )
