# build-catalog-pages.py — regenerate catalog/*.html entries from book _v2 data,
# preserving each page's existing chrome (only #entries-container is replaced).
import importlib.util, json, re, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"
BOOK_DATA = ROOT.parent / "Analyzing Islam Books" / "data"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


cr = _load("catalog_render", ROOT / "catalog_render.py")
read_anchors = _load("read_anchors", ROOT / "read_anchors.py")

EMPTY_STATE = ('<div class="empty" id="empty-state" style="display:none;">'
               'No entries match current filters.</div>')

# (catalog source stem) -> (book file, optional source-field filter)
SOURCES = [
    ("quran",     "quran_entries_v2.json",   None),
    ("bukhari",   "hadith_entries_v2.json",  "Bukhari"),
    ("muslim",    "hadith_entries_v2.json",  "Muslim"),
    ("abu-dawud", "abudawud_entries_v2.json", None),
    ("tirmidhi",  "tirmidhi_entries_v2.json", None),
    ("nasai",     "nasai_entries_v2.json",    None),
    ("ibn-majah", "ibnmajah_entries_v2.json", None),
]

# Regex to match entries-container opening through empty-state div and container close.
# Handles both real pages (</div>\n\n</main>) and minimal test pages (</div><footer>).
# Group 1: <div id="entries-container">
# Group 2: old entries content (to be replaced)
# Group 3: the empty-state div (preserved)
# Group 4: whitespace + </div> closing the container (preserved)
_CONTAINER_RE = re.compile(
    r'(<div id="entries-container">)'
    r'(.*?)'
    r'(<div class="empty" id="empty-state"[^>]*>[^<]*</div>)'
    r'(\s*</div>)',
    re.DOTALL
)


def load_book_entries() -> dict:
    out = {}
    for stem, fname, filt in SOURCES:
        data = json.loads((BOOK_DATA / fname).read_text(encoding="utf-8"))
        entries = data["entries"]
        if filt:
            entries = [e for e in entries if e.get("source") == filt]
        out[stem] = entries
    return out


def replace_entries_container(page_html: str, entries_html: str) -> str:
    """Replace the inner entries of <div id="entries-container"> with entries_html.

    Preserves the empty-state div and the container's closing </div>.
    Raises ValueError if the container markers are not found.
    """
    m = _CONTAINER_RE.search(page_html)
    if not m:
        raise ValueError("entries-container with empty-state not found in page HTML")
    new_inner = "\n\n" + entries_html + "\n\n" + EMPTY_STATE + "\n  "
    replacement = m.group(1) + new_inner + m.group(4)
    return page_html[:m.start()] + replacement + page_html[m.end():]


def build_one(stem: str, entries: list) -> int:
    anchor_sets = {s: read_anchors.read_anchor_set(s)
                   for s in ["quran", "bukhari", "muslim", "abu-dawud",
                              "tirmidhi", "nasai", "ibn-majah"]}
    blocks = [cr.render_entry(e, stem, anchor_sets) for e in entries]
    page_path = SITE / "catalog" / f"{stem}.html"
    page = page_path.read_text(encoding="utf-8")
    page = replace_entries_container(page, "\n\n".join(blocks))
    page_path.write_text(page, encoding="utf-8")
    return len(blocks)


def main() -> None:
    data = load_book_entries()
    total = 0
    for stem, _, _ in SOURCES:
        n = build_one(stem, data[stem])
        total += n
        print(f"  {stem:12s}: {n} entries")
    print(f"Total: {total}")


if __name__ == "__main__":
    main()
