# tests/test_kb_parsers.py
import importlib.util
import re
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
    """Every entry's url fragment must be an id that actually exists in the raw
    fixture file — found independently of the parser (regex over raw HTML), so
    this doesn't just prove the parser is self-consistent with itself."""
    raw_html = (SITE / "catalog" / "abu-dawud.html").read_text(encoding="utf-8")
    real_ids = set(re.findall(r'<div class="entry" id="([^"]+)"', raw_html))
    assert len(real_ids) > 100  # sanity: the regex actually found entries
    for e in entries:
        assert e["url"] == f"catalog/abu-dawud.html#{e['slug']}"
        fragment = e["url"].split("#", 1)[1]
        assert fragment in real_ids


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


def test_embed_text_contains_title_ref_and_category(entries):
    """embed_text is the field the embedding model actually consumes. A
    regression that collapses _compose_embed_text to `body` alone (dropping
    title/ref/categories from the head) must fail here even though length
    checks alone wouldn't catch it."""
    e = next(e for e in entries if e["slug"].startswith("allah-seals-the-heart"))
    assert e["title"] in e["embed_text"]
    assert e["ref"] and e["ref"] in e["embed_text"]
    assert e["categories"]
    assert any(c in e["embed_text"] for c in e["categories"])


def test_slugs_unique(entries):
    slugs = [e["slug"] for e in entries]
    assert len(slugs) == len(set(slugs))


def test_entry_missing_optional_fields_fall_back_to_none_and_empty():
    """Not every entry div is guaranteed to carry data-category, data-strength
    or a .ref span. Exercise those fallback branches directly with a minimal
    inline fixture (parser stays pure — no file I/O needed for this case)."""
    html = """
    <div class="entry" id="bare-entry-no-optional-fields">
      <div class="entry-header">
        <span class="entry-title">A bare entry with no optional fields</span>
      </div>
      <section>
        <p>Just a body paragraph.</p>
      </section>
    </div>
    """
    docs = kb.parse_entries(html, "abu-dawud")
    assert len(docs) == 1
    e = docs[0]
    assert e["ref"] is None
    assert e["categories"] == []
    assert e["strength"] is None


def test_parse_dossier_returns_one_doc():
    p = SITE / "arguments" / "bukhari" / "b01-aisha-age.html"
    doc = kb.parse_dossier(p.read_text(encoding="utf-8"), "arguments/bukhari/b01-aisha-age.html")
    assert doc is not None
    assert doc["kind"] == "dossier"
    assert doc["slug"] == "bukhari/b01-aisha-age"
    assert doc["url"] == "arguments/bukhari/b01-aisha-age.html"
    assert len(doc["title"]) > 5


def test_dossier_body_includes_responses():
    p = SITE / "arguments" / "bukhari" / "b01-aisha-age.html"
    doc = kb.parse_dossier(p.read_text(encoding="utf-8"), "arguments/bukhari/b01-aisha-age.html")
    assert len(doc["body"]) > 800, "a dossier is thesis-length, not a stub"


def test_parse_dossier_ignores_index_pages():
    """arguments/bukhari.html is a table of contents, not a dossier."""
    p = SITE / "arguments" / "bukhari.html"
    assert kb.parse_dossier(p.read_text(encoding="utf-8"), "arguments/bukhari.html") is None
