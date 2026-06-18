# tests/test_validate_links.py
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "validate_links", Path(__file__).parent.parent / "validate_links.py")
vl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vl)


def test_extract_read_links():
    html = ('<a class="cite-link" href="../read/quran.html#s2v25">Q 2:25</a> '
            '<a href="../read/bukhari.html#h224">Bukhari 224</a> '
            '<a href="../about.html">About</a>')
    assert vl.extract_read_links(html) == [
        ("quran", "s2v25"), ("bukhari", "h224")]


def test_unresolved_flags_missing_anchor():
    pairs = [("quran", "s2v25"), ("quran", "s999v999")]
    bad = vl.unresolved_links(pairs)
    assert ("quran", "s999v999") in bad
    assert ("quran", "s2v25") not in bad


@pytest.mark.xfail(reason="31 pre-existing broken citations (30 stale ibn-majah anchors in category pages, 1 muslim#h0334 zero-pad); Plan 2 regenerates catalog+category pages and drives this to 0. Run `python validate_links.py` for the current list.", strict=False)
def test_scan_site_baseline_zero_unresolved():
    """The current site must have zero unresolved read-links."""
    report = vl.scan_site()
    assert report["unresolved"] == [], (
        f"{len(report['unresolved'])} unresolved links: "
        f"{report['unresolved'][:10]}")
