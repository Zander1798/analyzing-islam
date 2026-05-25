# tests/test_book_html.py
import importlib.util, sys
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
    """No more than 3 chapters are empty."""
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    empty = [n for n, ch in chapters.items() if len(ch) == 0]
    assert len(empty) <= 3, f"Too many empty chapters: {empty}"

def test_parse_entries_has_body():
    """At least 200 entries have body text parsed from quran.html."""
    sections = mod.parse_entries()
    has_says = sum(1 for s in sections.values() if s.get('says', '').strip())
    assert has_says >= 200, f"Only {has_says} entries have body text"
