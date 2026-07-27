# tests/test_kb_parsers.py
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SITE = ROOT / "site"


def _load():
    spec = importlib.util.spec_from_file_location("kb_parsers", ROOT / "kb_parsers.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kb = _load()


@pytest.fixture(scope="module")
def entries():
    html = (SITE / "catalog" / "abu-dawud.html").read_text(encoding="utf-8")
    return kb.parse_entries(html, "abu-dawud")


def test_parses_many_entries(entries):
    assert len(entries) > 100


def test_entry_has_required_fields(entries):
    e = entries[0]
    assert set(e) == {
        "kind", "slug", "title", "ref", "source", "categories",
        "strength", "url", "body", "embed_text",
    }
    assert e["kind"] == "entry"
    assert e["source"] == "abu-dawud"


def test_entry_title_is_unescaped(entries):
    """Titles carry &quot; in the HTML; the parser must decode it."""
    assert not any("&quot;" in e["title"] for e in entries)


def test_entry_url_points_at_its_anchor(entries):
    e = entries[0]
    assert e["url"] == f"catalog/abu-dawud.html#{e['slug']}"


def test_entry_body_includes_quote_and_argument(entries):
    e = next(e for e in entries if e["slug"].startswith("allah-seals-the-heart"))
    assert "Friday prayer" in e["body"]
    assert "Why this is a problem" in e["body"]


def test_entry_categories_and_strength_parsed(entries):
    e = next(e for e in entries if e["slug"].startswith("allah-seals-the-heart"))
    assert "morality" in e["categories"]
    assert e["strength"] == "basic"


def test_embed_text_is_bounded(entries):
    """gte-small truncates at 512 tokens; keep embed_text well under it."""
    assert all(len(e["embed_text"]) <= 1800 for e in entries)


def test_slugs_unique(entries):
    slugs = [e["slug"] for e in entries]
    assert len(slugs) == len(set(slugs))
