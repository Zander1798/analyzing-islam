import re
from pathlib import Path

SITE = Path(__file__).parent.parent / "site"

def test_volume_pages_gone():
    assert not list(SITE.glob("read/nasai-v*.html"))
    assert not list(SITE.glob("read/ibn-majah-v*.html"))

def test_no_references_to_volume_pages():
    pat = re.compile(r'(nasai|ibn-majah)-v[1-6]\.html')
    hits = [p.name for p in SITE.rglob("*.html") if pat.search(p.read_text(encoding="utf-8", errors="ignore"))]
    assert hits == [], f"Still referenced by: {hits}"
