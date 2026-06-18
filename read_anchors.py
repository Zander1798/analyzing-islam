# read_anchors.py — index of anchors present in each rebuilt read page.
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SITE = Path(__file__).parent / "site"
_ID_RE = re.compile(r'id="([^"]+)"')
_cache: dict[str, set[str]] = {}


def read_anchor_set(slug: str, site_dir: Path = SITE) -> set[str]:
    key = f"{site_dir}::{slug}"
    if key in _cache:
        return _cache[key]
    path = site_dir / "read" / f"{slug}.html"
    if not path.exists():
        _cache[key] = set()
        return _cache[key]
    html = path.read_text(encoding="utf-8")
    _cache[key] = set(_ID_RE.findall(html))
    return _cache[key]
