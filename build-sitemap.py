#!/usr/bin/env python
"""Generate sitemap.xml and robots.txt for the Analyzing Islam site.

Walks every .html file under site/ and emits a sitemap of the public,
canonical pages. Excludes:
  * redirect shells (meta-refresh / location.replace stubs left by renames
    and the reader split)
  * private / auth / tool / mockup pages that should not be indexed

URLs mirror how the site links internally: relative paths with the .html
extension (GitHub Pages serves them verbatim). index.html maps to the
directory root.

Run from the repo root:  python build-sitemap.py
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent
SITE = REPO / "site"
BASE = "https://analyzingislam.com"

# Top-level pages that must never appear in the sitemap (auth, user-specific,
# admin, in-page tools/editors, mockups, error page, and dynamic templates
# that render nothing without a query param).
DENY = {
    "404.html", "admin.html", "login.html", "signup.html",
    "forgot-password.html", "reset-password.html", "profile.html",
    "saved.html", "shared.html", "build-shared.html", "build-editor.html",
    "design-mockup.html", "watch-mockup.html", "play.html", "compare.html",
    "entry.html",
}
# Subset of DENY worth calling out explicitly in robots.txt.
ROBOTS_DISALLOW = [
    "/admin.html", "/login.html", "/signup.html", "/profile.html",
    "/saved.html", "/forgot-password.html", "/reset-password.html",
    "/build-editor.html", "/build-shared.html", "/shared.html",
]

SHELL_RE = re.compile(r'http-equiv=["\']?refresh|location\.replace', re.I)


def is_redirect_shell(path: Path) -> bool:
    # Scan the whole file: the reader hubs place their location.replace
    # dispatcher well past the first screenful. Only genuine shells contain
    # these markers, so full-file scanning yields no false positives.
    text = path.read_text(encoding="utf-8", errors="ignore")
    return bool(SHELL_RE.search(text))


def url_for(rel: str) -> str:
    rel = rel.replace("\\", "/")
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return f"{BASE}/{rel[:-len('index.html')]}"
    return f"{BASE}/{rel}"


def main():
    urls = []
    for path in sorted(SITE.rglob("*.html")):
        rel = path.relative_to(SITE).as_posix()
        if rel in DENY:
            continue
        if is_redirect_shell(path):
            continue
        urls.append(url_for(rel))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append(f"  <url><loc>{u}</loc></url>")
    lines.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    robots = ["User-agent: *", "Allow: /"]
    robots += [f"Disallow: {p}" for p in ROBOTS_DISALLOW]
    robots += ["", f"Sitemap: {BASE}/sitemap.xml", ""]
    (SITE / "robots.txt").write_text("\n".join(robots), encoding="utf-8")

    print(f"sitemap.xml: {len(urls)} urls")
    print("robots.txt: written")


if __name__ == "__main__":
    main()
