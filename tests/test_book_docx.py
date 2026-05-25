import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "build_book_docx",
    Path(__file__).parent.parent / "build-book-docx.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_entry_count():
    entries = mod.get_entries()
    assert len(entries) == 262, f"Expected 262 entries, got {len(entries)}"


def test_no_excluded_ids_in_entries():
    entries = mod.get_entries()
    ids = {e['id'] for e in entries}
    for bad in mod.EXCLUDE_IDS:
        assert bad not in ids, f"Excluded ID found in entries: {bad}"


def test_all_chapters_populated():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    empty = [n for n, ch in chapters.items() if len(ch) == 0]
    assert not empty, f"Empty chapters: {empty}"


def test_entries_sorted_by_strength():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    for ch_num, ch_entries in chapters.items():
        strengths = [mod.STRENGTH_ORDER.get(e.get('strength',''), 0) for e in ch_entries]
        assert strengths == sorted(strengths), \
            f"Chapter {ch_num} entries not sorted by strength: {strengths[:5]}"
