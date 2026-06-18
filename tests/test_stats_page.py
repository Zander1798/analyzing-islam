import json, re
from pathlib import Path
ROOT = Path(__file__).parent.parent

def test_stats_total_and_no_stale():
    t = (ROOT / "site/stats.html").read_text(encoding="utf-8")
    assert "1,524" in t
    assert "1,541" not in t and "1541" not in t
    # the metric block shows the new total
    assert re.search(r'<div class="n">\s*1,524\s*</div>', t)

def test_stats_distribution_nodes_updated():
    t = (ROOT / "site/stats.html").read_text(encoding="utf-8")
    # old top-node numbers must be gone; new top node present
    assert "Prophetic Character (408)" not in t
    assert "560" in t  # Strange / Obscure new count appears in the distribution prose

def test_stats_category_count_widget():
    t = (ROOT / "site/stats.html").read_text(encoding="utf-8")
    # The topical-categories metric widget shows 31
    assert re.search(r'<div class="n">\s*31\s*</div>', t)

def test_stats_no_stale_category_counts():
    t = (ROOT / "site/stats.html").read_text(encoding="utf-8")
    # old distribution prose nodes gone
    assert "Women (376)" not in t
    assert "Contradictions (301)" not in t
    assert "Treatment of Disbelievers (211)" not in t

def test_stats_keyword_frequencies_updated():
    t = (ROOT / "site/stats.html").read_text(encoding="utf-8")
    # new keyword counts present
    assert "2,114" in t or "2114" in t  # women count
    assert "1,237" in t or "1237" in t  # slave count

def test_index_category_count_widget():
    t = (ROOT / "site/index.html").read_text(encoding="utf-8")
    # the categories stat widget shows 31
    assert re.search(r'<span class="number">\s*31\s*</span>', t)
