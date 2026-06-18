# tests/test_build_catalog_pages.py
import importlib.util
from pathlib import Path

def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent.parent / fname)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

bcp = _load("build_catalog_pages", "build-catalog-pages.py")

EXPECTED = {"quran":275,"bukhari":315,"muslim":264,"abu-dawud":181,
            "tirmidhi":226,"nasai":113,"ibn-majah":150}

def test_book_counts():
    data = bcp.load_book_entries()
    got = {k: len(v) for k, v in data.items()}
    assert got == EXPECTED, got
    assert sum(got.values()) == 1524

def test_replace_entries_container_preserves_chrome():
    page = ('<head><title>x</title></head><nav>NAV</nav>'
            '<div id="entries-container">OLD<div class="empty" id="empty-state" '
            'style="display:none;">No entries match current filters.</div></div>'
            '<footer>F</footer>')
    out = bcp.replace_entries_container(page, '<div class="entry">NEW</div>')
    assert "<nav>NAV</nav>" in out and "<footer>F</footer>" in out
    assert "OLD" not in out
    assert '<div class="entry">NEW</div>' in out
    assert 'id="empty-state"' in out
