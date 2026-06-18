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
