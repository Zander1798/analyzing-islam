# validate_links.py — gate: every read-page citation must resolve to a real
# anchor in the regenerated read pages. Reuses read_anchors for the index.
import importlib.util
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"

_ra_spec = importlib.util.spec_from_file_location("read_anchors", ROOT / "read_anchors.py")
read_anchors = importlib.util.module_from_spec(_ra_spec)
_ra_spec.loader.exec_module(read_anchors)

_LINK_RE = re.compile(r'href="\.\./read/([a-z0-9-]+)\.html#([^"]+)"')
# quiz source links are stored without the "../" prefix, e.g. "read/quran.html#s1v2"
_QUIZ_RE = re.compile(r'(?:\.\./)?read/([a-z0-9-]+)\.html#([^"#]+)')


def extract_read_links(html: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _LINK_RE.finditer(html)]


def unresolved_links(pairs, site_dir: Path = SITE) -> list[tuple[str, str]]:
    bad = []
    for slug, anchor in pairs:
        if anchor not in read_anchors.read_anchor_set(slug, site_dir):
            bad.append((slug, anchor))
    return bad


def _quiz_source_pairs(site_dir: Path) -> list[tuple[str, str]]:
    qp = site_dir / "assets" / "data" / "quiz-levels.json"
    if not qp.exists():
        return []
    data = json.loads(qp.read_text(encoding="utf-8"))
    pairs = []
    for level in data.get("levels", []):
        for q in level.get("questions", []):
            src = q.get("source", "")
            m = _QUIZ_RE.search(src)
            if m:
                pairs.append((m.group(1), m.group(2)))
    return pairs


def scan_site(site_dir: Path = SITE) -> dict:
    targets = sorted((site_dir / "catalog").glob("*.html")) + \
              sorted((site_dir / "category").glob("*.html"))
    checked = 0
    unresolved: list[dict] = []
    for path in targets:
        html = path.read_text(encoding="utf-8")
        pairs = extract_read_links(html)
        checked += len(pairs)
        for slug, anchor in unresolved_links(pairs, site_dir):
            unresolved.append({"file": path.name, "slug": slug, "anchor": anchor})
    quiz_pairs = _quiz_source_pairs(site_dir)
    checked += len(quiz_pairs)
    for slug, anchor in unresolved_links(quiz_pairs, site_dir):
        unresolved.append({"file": "quiz-levels.json", "slug": slug, "anchor": anchor})
    return {"checked": checked, "unresolved": unresolved}


def main() -> None:
    report = scan_site()
    print(f"Checked {report['checked']} read-page links.")
    if report["unresolved"]:
        print(f"UNRESOLVED: {len(report['unresolved'])}")
        for u in report["unresolved"][:50]:
            print(f"  {u['file']}: {u['slug']}#{u['anchor']}")
        sys.exit(1)
    print("All read-page links resolve. ✓")


if __name__ == "__main__":
    main()
