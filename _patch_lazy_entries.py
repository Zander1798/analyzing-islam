"""
_patch_lazy_entries.py
Adds lazy-entries.js to pages that list entries WITHOUT app.js
(category pages), and bumps the app.js version query string on
catalog pages so browsers pick up the updated file.

Run from project root:
    python _patch_lazy_entries.py
"""
import re
from pathlib import Path

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\site")

# ── 1. Category pages: add lazy-entries.js ───────────────────────────────────
# These pages have entries-container but no app.js.
# lazy-entries.js must be non-deferred so it runs synchronously and hides
# entries before the browser's initial layout pass.

CATEGORY_DIR = BASE / "category"
LAZY_SCRIPT_TAG = '<script src="../assets/js/lazy-entries.js"></script>'

# The line we insert before (the first deferred/auth script in these pages)
SUPABASE_TAG = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2" defer></script>'

cat_patched = 0
cat_already = 0

for path in sorted(CATEGORY_DIR.glob("*.html")):
    text = path.read_text(encoding="utf-8")

    if "lazy-entries.js" in text:
        cat_already += 1
        continue

    if SUPABASE_TAG not in text:
        print(f"  SKIP (no supabase tag): {path.name}")
        continue

    # Insert lazy-entries.js immediately before the supabase CDN tag
    new_text = text.replace(
        SUPABASE_TAG,
        LAZY_SCRIPT_TAG + "\n" + SUPABASE_TAG,
        1,
    )
    path.write_text(new_text, encoding="utf-8")
    cat_patched += 1

print(f"Category pages: {cat_patched} patched, {cat_already} already done")

# ── 2. Catalog pages: bump app.js version string ────────────────────────────
# Forces browsers to fetch the updated app.js (which now includes lazy loading).

OLD_APP_VER = 'app.js?v=2'
NEW_APP_VER = 'app.js?v=3'

app_bumped = 0
for path in BASE.rglob("*.html"):
    text = path.read_text(encoding="utf-8", errors="ignore")
    if OLD_APP_VER in text:
        new_text = text.replace(OLD_APP_VER, NEW_APP_VER)
        path.write_text(new_text, encoding="utf-8")
        app_bumped += 1

print(f"app.js version bumped: {app_bumped} page(s)")
print("Done.")
