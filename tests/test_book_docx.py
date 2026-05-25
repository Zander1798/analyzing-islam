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
    # Some Quran categories may genuinely have no entries
    assert len(empty) <= 3, f"Too many empty chapters: {empty}"


def test_entries_sorted_by_strength():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    for ch_num, ch_entries in chapters.items():
        strengths = [mod.STRENGTH_ORDER.get(e.get('strength',''), 0) for e in ch_entries]
        assert strengths == sorted(strengths), \
            f"Chapter {ch_num} entries not sorted by strength: {strengths[:5]}"


def test_output_exists_and_reasonable_size():
    """Output .docx must exist and be at least 200 KB (262 entries of content)."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, 'build-book-docx.py'],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent)
    )
    assert result.returncode == 0, f"Build failed:\n{result.stderr}\n{result.stdout}"
    out = Path(__file__).parent.parent / 'book-design/vol1-quran/Analyzing Islam Vol I — Word Prototype.docx'
    assert out.exists(), "Output .docx file not found"
    assert out.stat().st_size > 200_000, f"File too small: {out.stat().st_size} bytes"
