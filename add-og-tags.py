#!/usr/bin/env python3
"""Inject Open Graph + Twitter Card meta tags into the site's top-level
HTML pages so WhatsApp / Twitter / Facebook / LinkedIn / Slack / Discord
render a proper preview card (editorial dark-theme header we generated
in site/assets/og-image.png) instead of a naked text snippet.

Idempotent — skips files that already have `og:image` tags."""
import re
from pathlib import Path

ROOT = Path(__file__).parent / "site"
SITE_BASE = "https://analyzingislam.com"

# Top-level landing pages (people rarely share reader / catalog sub-
# pages directly, and those already have page-specific descriptions).
TARGET_PAGES = [
    "index.html", "about.html", "faq.html", "catalog.html",
    "compare.html", "read.html", "stats.html", "build.html",
    "read-external.html", "read-islamic.html",
    "saved.html", "shared.html",
]

# Per-page override: page_filename → (og_title, og_description, url_path).
# If a page isn't in here we fall back to a sensible default built from
# the page's existing <title> + <meta name="description">.
OVERRIDES = {
    "index.html": (
        "Analyzing Islam",
        "A systematic analysis of textual, moral, historical, and logical problems in the Quran and the canonical Sunni hadith collections. 1,500 curated entries across 30 categories.",
        "/",
    ),
    "build.html": (
        "Build — Analyzing Islam",
        "Compose your own arguments inside a side-by-side workspace. Quote every Quran verse, every hadith, every catalog entry — drag it into a rich-text editor, style it, save and share.",
        "/build.html",
    ),
    "compare.html": (
        "Compare — Analyzing Islam",
        "Read any two sources side-by-side — Quran, hadith, Tanakh, New Testament, Mishnah, Josephus, Ibn Kathir, and more. Independent search per pane.",
        "/compare.html",
    ),
    "catalog.html": (
        "Catalog — Analyzing Islam",
        "Filterable catalog of 1,500 entries across 30 categories — abrogation, scripture integrity, prophetic character, cosmology, hudud, warfare, child marriage, slavery, apostasy, antisemitism, and more.",
        "/catalog.html",
    ),
    "read.html": (
        "Read — Analyzing Islam",
        "Read the Quran, the six canonical Sunni hadith collections, the Tanakh, the New Testament, the Mishnah, the Talmud, Ibn Kathir, Josephus, and more.",
        "/read.html",
    ),
    "stats.html": (
        "Stats — Analyzing Islam",
        "A statistical deep-dive into what the 1,500-entry catalog reveals about the moral structure of the Quran and hadith, category by category.",
        "/stats.html",
    ),
    "about.html": (
        "About — Analyzing Islam",
        "How the catalog is built, what sources are cited, and the method behind the 1,500-entry systematic review.",
        "/about.html",
    ),
    "faq.html": (
        "FAQ — Analyzing Islam",
        "Frequently asked questions about the project — methodology, sources, responses to common objections.",
        "/faq.html",
    ),
}

TITLE_RE = re.compile(r"<title>([^<]+)</title>", re.IGNORECASE)
DESC_RE  = re.compile(
    r'<meta\s+name="description"\s+content="([^"]+)"\s*/?>',
    re.IGNORECASE,
)
# Canonical anchor: insert OG tags right after the <meta name="description">
# tag. Every page we target has one.
DESC_INSERT_RE = re.compile(
    r'(<meta\s+name="description"\s+content="[^"]*"\s*/?>)',
    re.IGNORECASE,
)

IMAGE_URL   = SITE_BASE + "/assets/og-image.png"
SQUARE_URL  = SITE_BASE + "/assets/og-image-square.png"


def escape_attr(s):
    return (
        s.replace("&", "&amp;")
         .replace('"', "&quot;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def build_tags(title, description, url):
    t = escape_attr(title)
    d = escape_attr(description)
    u = escape_attr(url)
    return (
        "\n"
        "<!-- Open Graph (link preview on WhatsApp, Facebook, LinkedIn, Slack, Discord, etc.) -->\n"
        f'<meta property="og:type" content="website">\n'
        f'<meta property="og:site_name" content="Analyzing Islam">\n'
        f'<meta property="og:title" content="{t}">\n'
        f'<meta property="og:description" content="{d}">\n'
        f'<meta property="og:url" content="{u}">\n'
        f'<meta property="og:image" content="{IMAGE_URL}">\n'
        f'<meta property="og:image:width" content="1200">\n'
        f'<meta property="og:image:height" content="630">\n'
        f'<meta property="og:image:alt" content="Analyzing Islam — 1,500 entries across 30 categories">\n'
        "<!-- Twitter / X card -->\n"
        f'<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{t}">\n'
        f'<meta name="twitter:description" content="{d}">\n'
        f'<meta name="twitter:image" content="{IMAGE_URL}">'
    )


def extract_fallback(text, filename):
    title_m = TITLE_RE.search(text)
    desc_m  = DESC_RE.search(text)
    title = title_m.group(1).strip() if title_m else "Analyzing Islam"
    desc  = desc_m.group(1).strip() if desc_m else "A systematic analysis of the Quran and the canonical Sunni hadith collections."
    return title, desc, "/" + filename


changed = 0
skipped = 0
missing_desc = 0

for name in TARGET_PAGES:
    path = ROOT / name
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    if "og:image" in text:
        skipped += 1
        continue
    if not DESC_INSERT_RE.search(text):
        missing_desc += 1
        continue

    if name in OVERRIDES:
        title, desc, urlpath = OVERRIDES[name]
        url = SITE_BASE + urlpath
    else:
        title, desc, urlpath = extract_fallback(text, name)
        url = SITE_BASE + urlpath

    tags = build_tags(title, desc, url)
    # Insert right after the existing description meta tag.
    new_text = DESC_INSERT_RE.sub(lambda m: m.group(1) + tags, text, count=1)
    path.write_text(new_text, encoding="utf-8")
    changed += 1
    print(f"  {name}")

print(f"\nUpdated: {changed} · Skipped (already had og:image): {skipped} · Missing description tag: {missing_desc}")
