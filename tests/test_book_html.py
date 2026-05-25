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


# ── Task 3: Front matter ──────────────────────────────────────────────────────

def test_front_matter_returns_six_sections():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    ch_start = {n: n * 15 for n in chapters}
    sections = mod.render_front_matter(chapters, ch_start)
    assert len(sections) == 6, f"Expected 6 front matter sections, got {len(sections)}"

def test_front_matter_toc_contains_all_chapters():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    ch_start = {n: n * 15 for n in chapters}
    sections = mod.render_front_matter(chapters, ch_start)
    toc_html = sections[3]
    for ch_num, (ch_name, _) in mod.CHAPTERS.items():
        if chapters.get(ch_num):  # only non-empty chapters appear in TOC
            # Chapter names are HTML-escaped in the TOC, so check for escaped version
            escaped_name = mod.esc(ch_name)
            assert escaped_name in toc_html, f"TOC missing chapter: {ch_name}"


# ── Task 4: Chapter opener ────────────────────────────────────────────────────

def test_chapter_opener_contains_required_elements():
    entries = mod.get_entries()
    ch1_entries = [e for e in entries
                   if mod.assign_chapter(e['id'], e.get('categories', [])) == 1]
    html = mod.render_chapter_opener(1, ch1_entries, section_idx=7)
    assert 'CHAPTER 1' in html
    assert 'Abrogation' in html
    assert str(len(ch1_entries)) in html
    assert 'id="s7"' in html


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

def test_general_index_contains_chapters():
    entries = mod.get_entries()
    chapters = mod.build_chapters(entries)
    html = mod.render_general_index(chapters, section_idx=300)
    assert 'General Index' in html
    assert 'Abrogation' in html
    assert 'Warfare' in html
    assert 'id="s300"' in html

def test_verse_index_sorted_and_present():
    entries = mod.get_entries()
    html = mod.render_verse_index(entries, section_idx=301)
    assert 'Quran Verse Index' in html
    assert 'Q 2:' in html
    assert 'id="s301"' in html


# ── Task 7: Navigator ─────────────────────────────────────────────────────────

def test_navigator_tick_count_and_chapter_marks():
    all_ids = [f"s{i}" for i in range(292)]
    chapter_ids = {f"s{i}" for i in range(6, 28)}
    html = mod.render_navigator(all_ids, chapter_ids)
    assert 'pn-tick' in html
    tick_count = html.count('class="pn-tick')
    assert tick_count >= 290, f"Expected >=290 ticks, got {tick_count}"
    assert 'chapter-mark' in html
    assert 'IntersectionObserver' in html
