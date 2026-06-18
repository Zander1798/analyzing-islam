"""Tests for analyze-catalog-stats.py taxonomy and counts.

The script outputs .tmp/catalog-stats.json with keys:
  total_entries (int)
  categories (dict: slug -> {name, count, strength, sources, examples})
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _run_and_load():
    subprocess.run(
        [sys.executable, "analyze-catalog-stats.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return json.loads(
        (ROOT / ".tmp" / "catalog-stats.json").read_text(encoding="utf-8")
    )


def test_stats_total_and_taxonomy():
    data = _run_and_load()

    # Total entries
    assert data["total_entries"] == 1524, (
        f"expected 1524, got {data['total_entries']}"
    )

    cats = data["categories"]
    names = {v["name"] for v in cats.values()}

    # New categories present
    assert "Science" in names, f"Science missing from categories: {names}"
    assert "Animals" in names, f"Animals missing from categories: {names}"

    # Old cosmology category removed
    assert "Cosmology" not in names, (
        f"Cosmology should be absent but is present in categories"
    )

    # Exactly 31 categories
    assert len(cats) == 31, f"expected 31 categories, got {len(cats)}: {list(cats.keys())}"

    # Known counts (from book-authoritative catalog)
    by_name = {v["name"]: v["count"] for v in cats.values()}
    assert by_name["Strange / Obscure"] == 560, (
        f"Strange / Obscure: expected 560, got {by_name.get('Strange / Obscure')}"
    )
    assert by_name["Women"] == 335, (
        f"Women: expected 335, got {by_name.get('Women')}"
    )
    assert by_name["Child Marriage"] == 14, (
        f"Child Marriage: expected 14, got {by_name.get('Child Marriage')}"
    )
