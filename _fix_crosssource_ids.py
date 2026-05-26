"""
_fix_crosssource_ids.py
Fixes the 3 cross-source ID collisions left over from the original dedup pass.
These IDs exist in both bukhari.html AND muslim.html with the same anchor id,
and appear twice in catalog-entries.json both as source=muslim.

Fix:
  - Remove the 3 entry divs from bukhari.html (keep them in muslim.html)
  - Deduplicate the JSON entries (keep one of each, source=muslim)
"""
import re, json, shutil
from pathlib import Path

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG_DIR = BASE / "site/catalog"
CATALOG_JSON = BASE / "site/assets/data/catalog-entries.json"

# These IDs live correctly in muslim.html; remove from bukhari.html
REMOVE_FROM_BUKHARI = {"aisha-age", "women-majority-hell", "fight-until-testify"}

ENTRY_OPEN = re.compile(
    r'<div\s+class=["\'][^"\']*\bentry\b[^"\']*["\'][^>]+id=["\']([^"\']+)["\'][^>]*>',
    re.DOTALL,
)
DIV_OPEN  = re.compile(r'<div\b',  re.IGNORECASE)
DIV_CLOSE = re.compile(r'</div\s*>', re.IGNORECASE)


def remove_entry_divs(html, target_ids):
    removed = 0
    out = []
    pos = 0
    while pos < len(html):
        m = ENTRY_OPEN.search(html, pos)
        if not m:
            out.append(html[pos:])
            break
        eid = m.group(1)
        if eid not in target_ids:
            out.append(html[pos:m.start() + 1])
            pos = m.start() + 1
            continue
        out.append(html[pos:m.start()])
        depth, scan = 1, m.end()
        while scan < len(html) and depth > 0:
            o = DIV_OPEN.search(html, scan)
            c = DIV_CLOSE.search(html, scan)
            if not c:
                scan = len(html)
                break
            if o and o.start() < c.start():
                depth += 1
                scan = o.end()
            else:
                depth -= 1
                scan = c.end()
        pos = scan
        removed += 1
    return "".join(out), removed


# --- Fix bukhari.html ---
buk_path = CATALOG_DIR / "bukhari.html"
buk_html = buk_path.read_text(encoding="utf-8", errors="ignore")
new_buk, count = remove_entry_divs(buk_html, REMOVE_FROM_BUKHARI)
print(f"bukhari.html: removed {count} cross-source ID entries")
if count > 0:
    shutil.copy(buk_path, CATALOG_DIR / "bukhari.html.bak4")
    buk_path.write_text(new_buk, encoding="utf-8")

# --- Fix catalog-entries.json — deduplicate the 3 IDs ---
with open(CATALOG_JSON, encoding="utf-8") as f:
    catalog = json.load(f)

seen = set()
final = []
for e in catalog:
    eid = e["id"]
    if eid in REMOVE_FROM_BUKHARI:
        if eid in seen:
            continue  # skip duplicate
        seen.add(eid)
    final.append(e)

removed_from_json = len(catalog) - len(final)
print(f"catalog-entries.json: removed {removed_from_json} duplicate entries")

shutil.copy(CATALOG_JSON, CATALOG_JSON.with_name("catalog-entries.backup4.json"))
with open(CATALOG_JSON, "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

print(f"Final JSON count: {len(final)}")
