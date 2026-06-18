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


FAKE = {
    "quran": {"s2v25", "s4v92", "s2v228"},
    "bukhari": {"h224"},
    "abu-dawud": {"h2311"},
}


def test_normalize_ref_part():
    assert cr.normalize_ref_part("contrast Q 21:101") == "Q 21:101"
    assert cr.normalize_ref_part("abudawud:2311") == "Abu Dawud 2311"
    assert cr.normalize_ref_part("Q4:92") == "Q 4:92"
    assert cr.normalize_ref_part("see also Bukhari 224") == "Bukhari 224"


def test_link_one_ref_resolves():
    assert cr.link_one_ref("Q 2:25", FAKE) == (
        '<a class="cite-link" href="../read/quran.html#s2v25">Q 2:25</a>')


def test_link_one_ref_unresolved_is_plain():
    # anchor not present -> plain text, no link
    assert cr.link_one_ref("Q 99:99", FAKE) == "Q 99:99"


def test_link_one_ref_referror_is_plain():
    assert cr.link_one_ref("Musnad Ahmad 12345", FAKE) == "Musnad Ahmad 12345"


def test_render_ref_html_multi_and_semicolon():
    out = cr.render_ref_html(["Q 2:154,3:169–170"], FAKE)
    # s2v154 absent in FAKE -> plain; both parts present, comma-joined
    assert "Q 2:154" in out and "3:169" in out
    out2 = cr.render_ref_html(["Bukhari 224; Bukhari 9999"], FAKE)
    assert '#h224' in out2 and "Bukhari 9999" in out2  # second plain (absent)


def test_link_inline_quran_present_and_absent():
    txt = "As in Q 2:25 and also Q 99:99 the text says."
    out = cr.link_inline(txt, FAKE)
    assert '<a class="cite-link" href="../read/quran.html#s2v25">Q 2:25</a>' in out
    assert "Q 99:99" in out and "#s99v99" not in out  # absent -> plain


def test_link_inline_hadith():
    txt = "Reported in Bukhari 224 clearly."
    out = cr.link_inline(txt, FAKE)
    assert '<a class="cite-link" href="../read/bukhari.html#h224">Bukhari 224</a>' in out


def test_link_inline_no_double_link_and_plain_text_preserved():
    txt = "No refs here at all."
    assert cr.link_inline(txt, FAKE) == txt


ENTRY_Q = {
    "id": 1, "title": 'Paradise as physical pleasure garden',
    "categories": ["Strange / Obscure"], "strength": "Basic",
    "verse_refs": ["Q 2:25"], "verse_quote": "\"... gardens [in Paradise] ...\"",
    "what_it_says": "Paradise is physical. See Q 2:25 again.",
    "why_problem": "First para.\n\nSecond para.",
    "muslim_response": None, "why_fails": None,
}
ENTRY_H = {
    "id": 1, "title": "Muhammad urinated standing up at a dump",
    "categories": ["Prophetic Character", "Strange / Obscure"], "strength": "Basic",
    "verse_refs": ["Bukhari 224"], "verse_quote": "\"Once the Prophet ...\"",
    "what_it_says": "Plain.", "why_problem": "Problem.",
    "muslim_response": "They say X.", "why_fails": "It fails.", "source": "Bukhari",
}

def test_render_entry_quran_structure():
    html_out = cr.render_entry(ENTRY_Q, "quran", FAKE)
    assert 'class="entry"' in html_out
    assert 'data-category="strange"' in html_out
    assert 'data-strength="basic"' in html_out
    assert "<h4>What the verse says</h4>" in html_out
    assert "<h4>Why this is a problem</h4>" in html_out
    assert "The Muslim response" not in html_out   # null -> omitted
    assert "Why it fails" not in html_out           # null -> omitted
    # inline link applied in body, anchor exists in FAKE; display tightened to Q2:25
    assert '../read/quran.html#s2v25">Q2:25</a>' in html_out
    # two paragraphs in why_problem
    assert html_out.count("<p>") >= 3

def test_render_entry_hadith_structure_and_multicat():
    html_out = cr.render_entry(ENTRY_H, "bukhari", FAKE)
    assert 'data-category="prophet strange"' in html_out
    assert "<h4>What the hadith says</h4>" in html_out
    assert "<h4>The Muslim response</h4>" in html_out
    assert "<h4>Why it fails</h4>" in html_out
    assert '<span class="tag">Prophetic Character</span>' in html_out
    assert '<span class="tag">Strange / Obscure</span>' in html_out
    assert '<span class="tag strength-basic">Basic</span>' in html_out
    assert '../read/bukhari.html#h224">Bukhari 224</a>' in html_out

def test_render_entry_escapes_quote():
    html_out = cr.render_entry(ENTRY_Q, "quran", FAKE)
    assert "<blockquote>" in html_out


# New test: render_ref_html must preserve prose/parentheticals and link each citation token
FAKE2 = {
    "quran":    {"s17v1"},
    "tirmidhi": {"h3147"},
}

def test_render_ref_html_preserves_prose_and_links_each():
    out = cr.render_ref_html(["Q 17:1 (with hadith Tirmidhi 3147)"], FAKE2)
    # Both citations must be independently linked
    assert '../read/quran.html#s17v1">Q 17:1</a>' in out, f"Q 17:1 not linked: {out}"
    assert '../read/tirmidhi.html#h3147">Tirmidhi 3147</a>' in out, f"Tirmidhi 3147 not linked: {out}"
    # Prose must be preserved verbatim
    assert "(with hadith" in out, f"prose parenthetical stripped: {out}"


def test_tighten_qrefs_display_only():
    assert cr.tighten_qrefs("see Q 98:6 and Q 8:55") == "see Q98:6 and Q8:55"
    # href contains no "Q " so it is never touched
    assert cr.tighten_qrefs('<a href="../read/quran.html#s98v6">Q 98:6</a>') == \
        '<a href="../read/quran.html#s98v6">Q98:6</a>'


def test_render_entry_tightens_qref_keeps_link():
    out = cr.render_entry(ENTRY_Q, "quran", FAKE)
    assert "Q 2:25" not in out      # no spaced Q-ref display anywhere
    assert "#s2v25" in out          # link target preserved
    assert "Q2:25" in out           # tight display present
