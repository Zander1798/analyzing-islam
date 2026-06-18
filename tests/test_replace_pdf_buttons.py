import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("rpb", Path(__file__).parent.parent / "replace_pdf_buttons.py")
rpb = importlib.util.module_from_spec(spec); spec.loader.exec_module(rpb)

def test_swap_hadith():
    html = '<div class="reader-cta"><a href="../read-islamic.html" class="btn">x</a><a href="../assets/sources/bukhari.pdf" class="btn" download>Download PDF</a></div>'
    out, n = rpb.swap_button(html, "bukhari")
    assert n == 1
    assert "assets/sources/bukhari.pdf" not in out
    assert 'href="https://sunnah.com/bukhari"' in out
    assert "View on sunnah.com" in out
    assert 'target="_blank"' in out and 'rel="noopener"' in out

def test_swap_quran_uses_quran_com():
    html = '<a href="../assets/sources/quran.pdf" class="btn" download>Download PDF</a>'
    out, n = rpb.swap_button(html, "quran")
    assert n == 1 and "https://quran.com" in out and "sunnah.com" not in out

def test_idempotent():
    html = '<a href="https://sunnah.com/bukhari" class="btn" target="_blank" rel="noopener">View on sunnah.com ↗</a>'
    out, n = rpb.swap_button(html, "bukhari")
    assert n == 0 and out == html
