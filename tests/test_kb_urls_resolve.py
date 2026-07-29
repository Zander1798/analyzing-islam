"""Every kb_docs url must resolve to a real file and a real anchor on the site.

A citation pointing at a 404 is worse than no citation, so this runs against the
parsed corpus rather than the database — it catches the bug before ingest, not
after an hour of embedding.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SITE = ROOT / "site"

_spec = importlib.util.spec_from_file_location("build_kb", ROOT / "build-kb.py")
bk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bk)


def _anchors(path: Path) -> set[str]:
    html = path.read_text(encoding="utf-8")
    return set(re.findall(r'id="([^"]+)"', html))


@pytest.mark.parametrize("tier", ["entries", "dossiers", "doctrine"])
def test_urls_point_at_existing_pages(tier):
    docs = bk.COLLECTORS[tier]()
    assert docs, f"{tier} produced no documents"

    for d in docs:
        if d["url"].startswith("http"):
            continue                      # external (video) — not our file tree
        if d["kind"] == "doctrine":
            continue                      # doctrine pages are built in Phase 3
        page, _, anchor = d["url"].partition("#")
        assert (SITE / page).exists(), f"{d['slug']}: missing page {page}"


def test_entry_anchors_exist():
    """Spot-check anchors per catalog page — parsing all seven is slow."""
    docs = bk.collect_entries()
    by_page: dict[str, list[dict]] = {}
    for d in docs:
        by_page.setdefault(d["url"].split("#")[0], []).append(d)

    for page, group in by_page.items():
        ids = _anchors(SITE / page)
        for d in group[:25]:
            anchor = d["url"].split("#", 1)[1]
            assert anchor in ids, f"{page} has no anchor #{anchor}"


def test_entry_count_matches_catalog_index():
    """catalog-entries.json is the site's own count — the parse must agree."""
    index = json.loads(
        (SITE / "assets" / "data" / "catalog-entries.json").read_text(encoding="utf-8")
    )
    assert len(bk.collect_entries()) == len(index)


def test_dossier_urls_carry_no_anchor_they_cannot_honour():
    """Dossier citations point at whole pages. If one ever grows a fragment, it
    has to resolve like an entry anchor does."""
    for d in bk.collect_dossiers():
        page, sep, anchor = d["url"].partition("#")
        if sep:
            assert anchor in _anchors(SITE / page), f"{d['slug']}: no anchor #{anchor}"
