# tests/test_link_hadith_to_sunnah.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("lh", Path(__file__).parent.parent / "link_hadith_to_sunnah.py")
lh = importlib.util.module_from_spec(spec); spec.loader.exec_module(lh)

def test_adds_link():
    html = '<span class="hadith-ref">Hadith 224 · Book 4</span>'
    out, n = lh.add_links(html, "bukhari")
    assert n == 1
    assert 'href="https://sunnah.com/bukhari:224"' in out
    assert 'target="_blank"' in out and 'rel="noopener"' in out
    assert "Hadith 224 · Book 4" in out  # label text preserved
    # The external-link cue must NOT be inline text — it would shift saved
    # highlight offsets inside the article. It is rendered via CSS instead.
    assert "↗" not in out
    assert "Hadith 224 · Book 4</a>" in out  # label ends exactly at the close tag

def test_idempotent_skips_existing_anchor():
    html = '<span class="hadith-ref"><a href="https://sunnah.com/bukhari:224">Hadith 224 · Book 4</a></span>'
    out, n = lh.add_links(html, "bukhari")
    assert n == 0 and out == html

def test_anchor_id_untouched():
    html = '<article class="hadith" id="h224"><header><span class="hadith-ref">Hadith 224 · Book 4</span></header></article>'
    out, n = lh.add_links(html, "bukhari")
    assert 'id="h224"' in out  # article anchor preserved
