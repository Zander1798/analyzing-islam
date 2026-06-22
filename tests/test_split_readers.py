# tests/test_split_readers.py
import subprocess, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

def _run_quran():
    # Regenerate just the quran sub-pages before asserting.
    subprocess.run([sys.executable, str(ROOT / "split_readers.py"), "--only", "quran", "--subpages"],
                   cwd=ROOT, check=True)

def test_quran_subpage_exists_and_has_anchor():
    _run_quran()
    p = SITE / "read" / "quran" / "23.html"
    assert p.exists(), "surah 23 page missing"
    html = p.read_text(encoding="utf-8")
    assert 'id="s23v13"' in html, "verse anchor missing on its surah page"
    assert 'id="surah-23"' in html, "surah wrapper missing"

def test_quran_subpage_has_full_chrome_with_deepened_urls():
    p = SITE / "read" / "quran" / "23.html"
    html = p.read_text(encoding="utf-8")
    # CSS/JS deepened one level…
    assert 'href="../../assets/css/style.css"' in html
    assert 'src="../../assets/js/reader-search.js"' in html
    # …favicons stay absolute…
    assert 'href="/assets/icons/favicon-32.png"' in html
    # …nav deepened…
    assert 'href="../../catalog.html"' in html

def test_quran_subpage_toc_links_to_siblings_and_marks_active():
    html = (SITE / "read" / "quran" / "23.html").read_text(encoding="utf-8")
    assert 'href="2.html"' in html          # a sibling TOC link
    assert 'href="#surah-2"' not in html    # no in-page TOC anchors remain
    assert re.search(r'class="[^"]*toc-active[^"]*"[^>]*href="23.html"'
                     r'|href="23.html"[^>]*class="[^"]*toc-active', html), "active TOC item not marked"

def test_quran_subpage_has_prev_next():
    html = (SITE / "read" / "quran" / "23.html").read_text(encoding="utf-8")
    assert 'href="22.html"' in html and 'href="24.html"' in html

def test_quran_first_and_last_pages_pager_bounds():
    first = (SITE / "read" / "quran" / "1.html").read_text(encoding="utf-8")
    last  = (SITE / "read" / "quran" / "114.html").read_text(encoding="utf-8")
    assert 'reader-pager-prev' not in first or 'is-disabled' in first
    assert 'reader-pager-next' not in last  or 'is-disabled' in last

def test_no_verse_lost():
    # every s{n}v{m} anchor in the monolith appears on exactly one sub-page
    mono = (SITE / "read" / "quran.html").read_text(encoding="utf-8")
    mono_ids = set(re.findall(r'id="(s\d+v\d+)"', mono))
    seen = set()
    for n in range(1, 115):
        p = SITE / "read" / "quran" / f"{n}.html"
        seen |= set(re.findall(r'id="(s\d+v\d+)"', p.read_text(encoding="utf-8")))
    assert mono_ids == seen, f"lost/extra anchors: {mono_ids ^ seen}"
