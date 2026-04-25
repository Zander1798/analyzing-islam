#!/usr/bin/env python3
"""Inject the highlights feature into every reader page.

Adds to each reader HTML in site/read/ and site/read-external/:
  1. <link rel="stylesheet" href="../assets/css/highlights.css"> in <head>.
  2. has-hl-card class on .reader-layout.
  3. <aside class="hl-card"> + mobile toggle button before </div> closing
     .reader-layout (immediately after </main>).
  4. <script src=".../highlights.js?v=1"> + init block before </body>.

The init block declares the source slug + anchor regex per file.

Idempotent: skips files that already contain the highlights css link.

Usage:  python inject-highlights.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
SITE_READ          = ROOT / "site" / "read"
SITE_READ_EXTERNAL = ROOT / "site" / "read-external"

# Per-file (source slug, anchor regex string) configuration.
# Filenames that aren't listed here are skipped.
CONFIG = {
    "quran.html":             ("quran",             r"^s\d+v\d+$"),
    "bukhari.html":           ("bukhari",           r"^h\d+$"),
    "muslim.html":            ("muslim",            r"^h\d+$"),
    "abu-dawud.html":         ("abu-dawud",         r"^h\d+$"),
    "tirmidhi.html":          ("tirmidhi",          r"^h\d+$"),
    "nasai.html":             ("nasai",             r"^h\d+$"),
    "ibn-majah.html":         ("ibn-majah",         r"^h\d+$"),
    # OCR volume readers — same anchor shape.
    "nasai-v1.html":          ("nasai-v1",          r"^h\d+$"),
    "nasai-v2.html":          ("nasai-v2",          r"^h\d+$"),
    "nasai-v3.html":          ("nasai-v3",          r"^h\d+$"),
    "nasai-v4.html":          ("nasai-v4",          r"^h\d+$"),
    "nasai-v5.html":          ("nasai-v5",          r"^h\d+$"),
    "nasai-v6.html":          ("nasai-v6",          r"^h\d+$"),
    "ibn-majah-v1.html":      ("ibn-majah-v1",      r"^h\d+$"),
    "ibn-majah-v2.html":      ("ibn-majah-v2",      r"^h\d+$"),
    "ibn-majah-v3.html":      ("ibn-majah-v3",      r"^h\d+$"),
    "ibn-majah-v4.html":      ("ibn-majah-v4",      r"^h\d+$"),
    "ibn-majah-v5.html":      ("ibn-majah-v5",      r"^h\d+$"),
}

# read-external — per-file slug + anchor regex.
CONFIG_EXT = {
    "tanakh.html":              ("tanakh",              r"^[a-z0-9-]+-\d+-\d+$"),
    "new-testament.html":       ("new-testament",       r"^[a-z0-9-]+-\d+-\d+$"),
    "apocryphal-gospels.html":  ("apocryphal-gospels",  r"^[a-z0-9-]+-\d+(?:-\d+)?$"),
    "book-of-enoch.html":       ("book-of-enoch",       r"^enoch-\d+-\d+$"),
    "mishnah.html":             ("mishnah",             r"^[a-z-]+-\d+(?:-\d+)?$"),
    "talmud.html":              ("talmud",              r"^[a-z0-9-]+$"),
    "talmud-1.html":            ("talmud-1",            r"^[a-z0-9-]+$"),
    "talmud-2.html":            ("talmud-2",            r"^[a-z0-9-]+$"),
    "talmud-3.html":            ("talmud-3",            r"^[a-z0-9-]+$"),
    "talmud-4.html":            ("talmud-4",            r"^[a-z0-9-]+$"),
    "talmud-5.html":            ("talmud-5",            r"^[a-z0-9-]+$"),
    "talmud-6.html":            ("talmud-6",            r"^[a-z0-9-]+$"),
    "talmud-7.html":            ("talmud-7",            r"^[a-z0-9-]+$"),
    "talmud-8.html":            ("talmud-8",            r"^[a-z0-9-]+$"),
    "talmud-9.html":            ("talmud-9",            r"^[a-z0-9-]+$"),
    "talmud-10.html":           ("talmud-10",           r"^[a-z0-9-]+$"),
    "josephus.html":            ("josephus",            r"^[a-z0-9-]+$"),
    "ibn-kathir.html":          ("ibn-kathir",          r"^[a-z0-9-]+$"),
}
# Add the 114 ibn-kathir surah pages (slug = ibn-kathir-N).
for n in range(1, 115):
    CONFIG_EXT[f"ibn-kathir-{n}.html"] = (f"ibn-kathir-{n}", r"^ibnk-\d+-\d+$")

# Add the 67 interlinear bible book pages.
BIBLE_DIR = SITE_READ_EXTERNAL / "bible"
BIBLE_BOOKS = sorted([p.stem for p in BIBLE_DIR.glob("*.html")]) if BIBLE_DIR.exists() else []
# (Bible pages handled separately because they live in a sub-dir.)

CSS_LINK = '<link rel="stylesheet" href="../assets/css/highlights.css">'
CSS_LINK_BIBLE = '<link rel="stylesheet" href="../../assets/css/highlights.css">'

ASIDE_HTML = """  <aside class="hl-card" id="hl-card" aria-label="Highlights">
    <header class="hl-card-head">
      <h3>Highlights</h3>
      <span class="hl-card-count">0</span>
    </header>
    <ol class="hl-card-list" id="hl-card-list"></ol>
    <p class="hl-card-empty">Highlight text in the reader to save it here.</p>
  </aside>
  <button type="button" class="hl-card-toggle" aria-controls="hl-card">★ Highlights</button>
"""

INIT_TPL = """<script src="{prefix}assets/js/highlights.js?v=1" defer></script>
<script defer>
  document.addEventListener("DOMContentLoaded", function () {{
    function tryAttach() {{
      if (!window.AI_HIGHLIGHTS) {{ setTimeout(tryAttach, 30); return; }}
      window.AI_HIGHLIGHTS.attach({{
        source: "{slug}",
        scope: document.querySelector(".reader-main") || document.querySelector(".bible-reader") || document.body,
        anchorRe: /{anchor_re}/,
        cardEl: document.getElementById("hl-card"),
      }});
    }}
    tryAttach();
    var btn = document.querySelector(".hl-card-toggle");
    var card = document.getElementById("hl-card");
    if (btn && card) btn.addEventListener("click", function () {{
      card.classList.toggle("is-open");
    }});
  }});
</script>
"""


def patch(path: Path, slug: str, anchor_re: str, prefix: str = "../") -> bool:
    txt = path.read_text(encoding="utf-8")
    css_link = CSS_LINK_BIBLE if prefix == "../../" else CSS_LINK
    if "highlights.css" in txt:
        return False  # already patched

    # 1. Inject CSS link after reader.css.
    new = re.sub(
        r'(<link rel="stylesheet" href="[^"]*reader\.css">)',
        r'\1\n' + css_link,
        txt, count=1,
    )
    if new == txt:
        # No reader.css — fall back to before </head>.
        new = txt.replace("</head>", css_link + "\n</head>", 1)

    # 2. Add has-hl-card class to .reader-layout.
    new = re.sub(
        r'<div class="reader-layout"',
        '<div class="reader-layout has-hl-card"',
        new, count=1,
    )

    # 3. Inject the aside after the first </main>.
    new = re.sub(
        r'(</main>\s*)\n(\s*</div>)',
        r'\1\n' + ASIDE_HTML + r'\2',
        new, count=1,
    )

    # 4. Inject script tags before </body>.
    init = INIT_TPL.format(prefix=prefix, slug=slug, anchor_re=anchor_re)
    new = new.replace("</body>", init + "</body>", 1)

    if new == txt:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def main():
    changed = 0
    for fname, (slug, anchor_re) in CONFIG.items():
        p = SITE_READ / fname
        if not p.exists():
            continue
        if patch(p, slug, anchor_re, prefix="../"):
            print(f"[ok] read/{fname}")
            changed += 1
    for fname, (slug, anchor_re) in CONFIG_EXT.items():
        p = SITE_READ_EXTERNAL / fname
        if not p.exists():
            continue
        if patch(p, slug, anchor_re, prefix="../"):
            print(f"[ok] read-external/{fname}")
            changed += 1
    # Bible interlinear pages.
    for stem in BIBLE_BOOKS:
        p = BIBLE_DIR / f"{stem}.html"
        slug = f"bible-{stem}"
        anchor_re = rf"^{stem}-\d+-\d+$"
        if patch(p, slug, anchor_re, prefix="../../"):
            print(f"[ok] read-external/bible/{stem}.html")
            changed += 1
    print(f"\nPatched {changed} files.")


if __name__ == "__main__":
    main()
