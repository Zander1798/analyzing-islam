"""
_perf_quickwins.py
Applies three performance quick wins across the site:

  1. Add `defer` to the Supabase CDN <script> tag (every page that has it)
  2. Add `defer` to every goat-skins.js <script> tag (any relative path variant)
  3. Add <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
     in <head> on every page that loads the Supabase CDN
  4. Add loading="lazy" to the skin-picker .goat-gif images in goat.html
     (the main big display image is left eager)

Safe because auth.js already has `defer` and retries via setTimeout(init, 50)
when window.supabase isn't present yet.

Run from project root:
    python _perf_quickwins.py
"""
import re
from pathlib import Path

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\site")

# ── Patterns ────────────────────────────────────────────────────────────────

SUPABASE_PLAIN = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>'
SUPABASE_DEFER = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2" defer></script>'

PRECONNECT_TAG = '<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>'

# goat-skins may live at any relative depth; match any path ending in goat-skins.js
GOAT_SKINS_RE = re.compile(
    r'(<script\s+src="[^"]*goat-skins\.js")(></script>)'
)
GOAT_SKINS_DEFER = r'\1 defer\2'

# The charset meta always appears first in <head>; insert preconnect after it
CHARSET_META_RE = re.compile(r'(<meta charset="UTF-8">)')
PRECONNECT_INSERT = r'\1\n<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>'

# ── Walk every HTML file ─────────────────────────────────────────────────────

html_files = list(BASE.rglob("*.html"))

stats = {
    "supabase_deferred": 0,
    "goat_skins_deferred": 0,
    "preconnect_added": 0,
    "goat_lazy_added": 0,
    "files_changed": 0,
}

for path in sorted(html_files):
    original = path.read_text(encoding="utf-8", errors="ignore")
    text = original

    # 1. Defer the Supabase CDN script (only if not already deferred)
    if SUPABASE_PLAIN in text:
        text = text.replace(SUPABASE_PLAIN, SUPABASE_DEFER)
        stats["supabase_deferred"] += 1

        # 3. Add preconnect hint (only to pages that load from this CDN)
        if PRECONNECT_TAG not in text:
            text, n = CHARSET_META_RE.subn(PRECONNECT_INSERT, text, count=1)
            if n:
                stats["preconnect_added"] += 1

    # 2. Defer goat-skins.js (any path variant, only if not already deferred)
    if "goat-skins.js" in text and 'goat-skins.js" defer' not in text:
        new_text, n = GOAT_SKINS_RE.subn(GOAT_SKINS_DEFER, text)
        if n:
            text = new_text
            stats["goat_skins_deferred"] += n

    if text != original:
        path.write_text(text, encoding="utf-8")
        stats["files_changed"] += 1

# ── goat.html — lazy-load skin picker images ─────────────────────────────────
# The main display image (#goat-big-img) is left eager (it's the hero element).
# The 9 picker grid images (.goat-gif) get loading="lazy".

GOAT_HTML = BASE / "goat.html"
goat_original = GOAT_HTML.read_text(encoding="utf-8")
goat_text = goat_original

# Match <img ... class="goat-gif" ...> but NOT the big display img
# The big img has id="goat-big-img"; the picker imgs do not.
PICKER_IMG_RE = re.compile(
    r'(<img\s[^>]*class="goat-gif"[^>]*)(/?>)',
    re.DOTALL,
)

def add_lazy(m):
    tag_body = m.group(1)
    close = m.group(2)
    if 'loading=' in tag_body:
        return m.group(0)  # already has loading attr
    return tag_body + ' loading="lazy"' + close

goat_text, n = PICKER_IMG_RE.subn(add_lazy, goat_text)
stats["goat_lazy_added"] = n

if goat_text != goat_original:
    GOAT_HTML.write_text(goat_text, encoding="utf-8")
    stats["files_changed"] += 1  # might double-count if already changed above

# ── Report ───────────────────────────────────────────────────────────────────

print("Performance quick wins applied")
print(f"  Supabase CDN script deferred:   {stats['supabase_deferred']} pages")
print(f"  goat-skins.js deferred:         {stats['goat_skins_deferred']} pages")
print(f"  <link rel=preconnect> added:    {stats['preconnect_added']} pages")
print(f"  Skin picker images lazy-loaded: {stats['goat_lazy_added']} images")
print(f"  Total HTML files touched:       {stats['files_changed']}")
