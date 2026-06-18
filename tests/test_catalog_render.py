import importlib.util, hashlib
from pathlib import Path
import pytest

cr = None
def _load():
    global cr
    spec = importlib.util.spec_from_file_location(
        "catalog_render", Path(__file__).parent.parent / "catalog_render.py")
    cr = importlib.util.module_from_spec(spec); spec.loader.exec_module(cr)
_load()


def test_category_map_has_31():
    assert len(cr.CATEGORY_SLUGS) == 31
    assert cr.category_slug("Strange / Obscure") == "strange"
    assert cr.category_slug("Treatment of Disbelievers") == "disbelievers"
    assert cr.category_slug("Gross / Vile") == "gross-vile"


def test_category_slug_unknown_raises():
    with pytest.raises(KeyError):
        cr.category_slug("Nonexistent Category")


def test_strength_class():
    assert cr.strength_class("Basic") == "basic"
    assert cr.strength_class("Strong") == "strong"


def test_slugify_and_entry_slug_match_legacy_scheme():
    title = 'Paradise as physical pleasure garden with "purified spouses"'
    expected_hash = hashlib.sha256(f"quran::{title}".encode("utf-8")).hexdigest()[:8]
    slug = cr.entry_slug(title, "quran")
    assert slug.endswith("-" + expected_hash)
    assert slug.startswith("paradise-as-physical-pleasure-garden")
    assert len(slug.split("-")[-1]) == 8


FAKE = {
    "quran": {"s2v25", "s4v92", "s2v228"},
    "bukhari": {"h224"},
    "abu-dawud": {"h2311"},
}


def test_normalize_ref_part():
    assert cr.normalize_ref_part("contrast Q 21:101") == "Q 21:101"
    assert cr.normalize_ref_part("abudawud:2311") == "Abu Dawud 2311"
    assert cr.normalize_ref_part("Q4:92") == "Q 4:92"
    assert cr.normalize_ref_part("see also Bukhari 224") == "Bukhari 224"


def test_link_one_ref_resolves():
    assert cr.link_one_ref("Q 2:25", FAKE) == (
        '<a class="cite-link" href="../read/quran.html#s2v25">Q 2:25</a>')


def test_link_one_ref_unresolved_is_plain():
    # anchor not present -> plain text, no link
    assert cr.link_one_ref("Q 99:99", FAKE) == "Q 99:99"


def test_link_one_ref_referror_is_plain():
    assert cr.link_one_ref("Musnad Ahmad 12345", FAKE) == "Musnad Ahmad 12345"


def test_render_ref_html_multi_and_semicolon():
    out = cr.render_ref_html(["Q 2:154,3:169–170"], FAKE)
    # s2v154 absent in FAKE -> plain; both parts present, comma-joined
    assert "Q 2:154" in out and "3:169" in out
    out2 = cr.render_ref_html(["Bukhari 224; Bukhari 9999"], FAKE)
    assert '#h224' in out2 and "Bukhari 9999" in out2  # second plain (absent)
