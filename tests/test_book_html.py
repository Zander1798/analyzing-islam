# tests/test_book_html.py
import importlib.util
from pathlib import Path

def _load():
    spec = importlib.util.spec_from_file_location(
        "build_book_html",
        Path(__file__).parent.parent / "build-book-html.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

mod = _load()

def test_entry_count():
    """Exactly 262 Quran entries after exclusions."""
    entries = mod.get_entries()
    assert len(entries) == 262, f"Expected 262, got {len(entries)}"

def test_all_chapters_populated():
    """Only chapter 13 (LGBTQ/Gender) is expected to be empty — no others."""
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    empty = [n for n, ch in chapters.items() if len(ch) == 0]
    assert empty == [13], f"Unexpected empty chapters: {empty}"

def test_parse_entries_has_body():
    """At least 200 entries have body text parsed from quran.html."""
    sections = mod.parse_entries()
    has_says = sum(1 for s in sections.values() if s.get('says', '').strip())
    assert has_says >= 200, f"Only {has_says} entries have body text"

def test_render_styles_contains_key_rules():
    css = mod.render_styles()
    for rule in ['@page', '#page-nav', '.entry', '.chapter-opener',
                 'Libre Baskerville', 'EB Garamond', 'Montserrat',
                 'break-before: page', '#0d0d0d', '#c8963c']:
        assert rule in css, f"CSS missing: {rule}"
