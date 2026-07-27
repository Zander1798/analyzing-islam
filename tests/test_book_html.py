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
    for rule in ['@page', '.entry', '.chapter-opener',
                 'Libre Baskerville', 'EB Garamond', 'Montserrat',
                 'break-before: page', '#000000', '#c8963c']:
        assert rule in css, f"CSS missing: {rule}"

def test_render_styles_strength_colors():
    """New strength badge colors: green/orange/red."""
    css = mod.render_styles()
    assert '#4caf50' in css, "BASIC green color missing"
    assert '#e07800' in css, "MODERATE orange color missing"
    assert '#e53935' in css, "STRONG red color missing"


# ── Task 3: Front matter ──────────────────────────────────────────────────────

def test_front_matter_returns_seven_sections():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    ch_start = {n: n * 15 for n in chapters}
    sections = mod.render_front_matter(chapters, ch_start)
    assert len(sections) == 7, f"Expected 7 front matter sections, got {len(sections)}"

def test_front_matter_has_front_cover():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    ch_start = {n: n * 15 for n in chapters}
    sections = mod.render_front_matter(chapters, ch_start)
    cover_html = sections[0]
    assert 'fm-cover' in cover_html
    assert 'front-cover' in cover_html
    assert 'Analyzing' in cover_html

def test_front_matter_toc_contains_all_chapters():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    ch_start = {n: n * 15 for n in chapters}
    sections = mod.render_front_matter(chapters, ch_start)
    toc_html = sections[4]   # index 4 is TOC (was 3 before cover was added)
    for ch_num, (ch_name, _) in mod.CHAPTERS.items():
        if chapters.get(ch_num):
            escaped_name = mod.esc(ch_name)
            assert escaped_name in toc_html, f"TOC missing chapter: {ch_name}"

def test_abbreviations_has_strength_colors():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    ch_start = {n: n * 15 for n in chapters}
    sections = mod.render_front_matter(chapters, ch_start)
    abbr_html = sections[6]   # last section = abbreviations
    assert 'fm-strength-basic' in abbr_html
    assert 'fm-strength-moderate' in abbr_html
    assert 'fm-strength-strong' in abbr_html


# ── Task 4: Chapter opener ────────────────────────────────────────────────────

def test_chapter_opener_contains_required_elements():
    entries = mod.get_entries()
    ch1_entries = [e for e in entries
                   if mod.assign_chapter(e['id'], e.get('categories', [])) == 1]
    html = mod.render_chapter_opener(1, ch1_entries, section_idx=7)
    assert 'Chapter 1' in html
    assert 'Abrogation' in html
    assert str(len(ch1_entries)) in html
    assert 'id="s7"' in html

def test_chapter_opener_single_column_with_badges():
    """Chapter opener must use single-column entry rows with strength badges."""
    entries = mod.get_entries()
    ch1_entries = [e for e in entries
                   if mod.assign_chapter(e['id'], e.get('categories', [])) == 1]
    html = mod.render_chapter_opener(1, ch1_entries, section_idx=7)
    assert 'ch-entry-row' in html, "Single-column row class missing"
    assert 'ch-entry-badge' in html, "Strength badge missing from chapter opener"
    assert 'columns:' not in html, "Two-column layout found — should be single column"

def test_chapter_opener_footer():
    """Chapter opener must have three-part footer: entries count, page, THE QURAN."""
    entries = mod.get_entries()
    ch1_entries = [e for e in entries
                   if mod.assign_chapter(e['id'], e.get('categories', [])) == 1]
    html = mod.render_chapter_opener(1, ch1_entries, section_idx=7)
    assert 'ch-footer' in html
    assert 'The Quran' in html


# ── Task 5: Entry rendering ───────────────────────────────────────────────────

def test_render_entry_contains_required_elements():
    entries = mod.get_entries()
    sections_data = mod.parse_entries()
    entry = entries[0]
    ch_num = mod.assign_chapter(entry['id'], entry.get('categories', []))
    html = mod.render_entry(entry, sections_data, ch_num, section_idx=8)
    assert entry['title'] in html or mod.esc(entry['title']) in html
    assert 'THE QURAN' in html
    assert entry['ref'] in html
    assert 'WHAT THE VERSE SAYS' in html
    assert 'id="s8"' in html

def test_render_entry_strength_badge():
    entries = mod.get_entries()
    sections_data = mod.parse_entries()
    strong_entries = [e for e in entries if e.get('strength') == 'strong']
    assert strong_entries, "No strong entries found"
    e = strong_entries[0]
    html = mod.render_entry(e, sections_data,
                            mod.assign_chapter(e['id'], e.get('categories', [])),
                            section_idx=9)
    assert 'tag-strong' in html
    assert 'STRONG' in html


# ── Task 6: Back matter ───────────────────────────────────────────────────────

def test_general_index_alphabetical():
    """General index must be alphabetical with letter dividers."""
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    html = mod.render_general_index(chapters, section_idx=300)
    assert 'General Index' in html
    assert 'idx-letter' in html, "Letter divider class missing"
    assert 'Abrogation' in html
    assert 'Warfare' in html
    assert 'id="s300"' in html

def test_verse_index_sorted_and_present():
    entries = mod.get_entries()
    html = mod.render_verse_index(entries, section_idx=301)
    assert 'Quran Verse Index' in html
    assert 'id="s301"' in html
    pos_q2 = html.find('Q 2:')
    pos_q9 = html.find('Q 9:')
    assert pos_q2 != -1, "Q 2:x not found in verse index"
    assert pos_q9 != -1, "Q 9:x not found in verse index"
    assert pos_q2 < pos_q9, "Q 2:x should appear before Q 9:x (sort broken)"

def test_verse_index_surah_grouped():
    """Verse index must group entries by surah with surah headers."""
    entries = mod.get_entries()
    html = mod.render_verse_index(entries, section_idx=301)
    assert 'vi-surah-header' in html, "Surah header class missing"
    assert 'Surah 2' in html
    assert 'Surah 9' in html

def test_back_cover_exists():
    """Back cover page must be renderable and contain required elements."""
    html = mod.render_back_cover()
    assert 'back-cover' in html
    assert 'Analyzing Islam' in html
    assert 'bc-red-rule' in html
    assert 'bc-bullet' in html
    assert 'analyzingislam.com' in html.lower()


# ── Task 7: Navigator ─────────────────────────────────────────────────────────

def test_navigator_renders():
    """Navigator renders with correct total count."""
    ids = ['fm-cover', 'fm-halftitle', 'fm-title', 's7', 's8']
    html = mod.render_navigator(ids, {'s7'})
    assert 'page-nav' in html
    assert 'pn-track' in html
    assert '5' in html  # total sections


# ── Task 8: Integration test ──────────────────────────────────────────────────

def test_build_produces_valid_output():
    """Full integration test: build runs, output > 1 MB, contains key content."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, 'build-book-html.py'],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent)
    )
    assert result.returncode == 0, (
        f"Build failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    out = Path(__file__).parent.parent / 'book-design/vol1-quran/book.html'
    assert out.exists(), "book.html was not created"
    size = out.stat().st_size
    assert size > 1_000_000, f"book.html too small: {size} bytes"

    content = out.read_text(encoding='utf-8')
    for ch_name in ['Abrogation', 'Scripture Integrity', 'Contradictions',
                    'Warfare &amp; Jihad', 'Antisemitism', 'Paradise',
                    'Prophetic Privileges']:
        assert ch_name in content, f"Missing chapter: {ch_name}"
    assert 'General Index' in content
    assert 'Quran Verse Index' in content
    assert 'front-cover' in content
    assert 'back-cover' in content
