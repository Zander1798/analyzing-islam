import re
from pathlib import Path
SITE = Path(__file__).parent.parent / "site"

CATALOG_COUNT_PAGES = ["index.html","about.html","faq.html","stats.html","goat.html",
                       "build.html","compare.html","play.html","catalog.html"]

def test_no_stale_total_in_catalog_pages():
    bad = []
    for name in CATALOG_COUNT_PAGES:
        t = (SITE / name).read_text(encoding="utf-8")
        if "1,541" in t or "1541" in t or "30 categories" in t:
            bad.append(name)
    assert bad == [], f"stale counts remain in {bad}"

def test_index_hero_number():
    t = (SITE / "index.html").read_text(encoding="utf-8")
    assert re.search(r'<span class="number">\s*1,524\s*</span>', t)

def test_quran_meta_updated():
    t = (SITE / "catalog/quran.html").read_text(encoding="utf-8")
    assert "275" in t and "262 critical-analysis" not in t
