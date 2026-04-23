"""Some reader pages (Interlinear Bible sub-pages, Ibn Kathīr per-surah
pages, Talmud volume pages) were generated before the site grew its
auth UI, so they don't load Supabase / auth.js / auth-ui.js — which
means the "Sign in" / "Account" button in the site header never
appears on them. That makes the header inconsistent across pages.

This script finds every page that has a <div class="site-nav-links">
but no reference to auth-ui.js, and inserts the four scripts it needs
(Supabase CDN, config.js, auth.js, auth-ui.js) immediately before the
first other site script (goat.js by convention), preserving the
relative-prefix used by surrounding scripts.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"

SCRIPT_RE = re.compile(
    r'<script\s+src="(?:(\.\./(?:\.\./)*)|())assets/js/([^"]+)"([^>]*)></script>',
    re.IGNORECASE,
)


def auth_script_block(prefix: str) -> str:
    return (
        '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>\n'
        f'<script src="{prefix}assets/js/config.js"></script>\n'
        f'<script src="{prefix}assets/js/auth.js" defer></script>\n'
        f'<script src="{prefix}assets/js/auth-ui.js" defer></script>\n'
    )


def process(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")

    if 'auth-ui.js' in html:
        return False  # already wired up
    if '<div class="site-nav-links">' not in html:
        return False  # no nav on this page

    first = SCRIPT_RE.search(html)
    if not first:
        # No asset scripts yet — fall back to before </body>.
        body_close = html.rfind('</body>')
        if body_close < 0:
            return False
        # Figure out the prefix from a stylesheet instead.
        css = re.search(r'<link[^>]*href="((?:\.\./)*)assets/css/', html)
        prefix = css.group(1) if css else ''
        block = auth_script_block(prefix) + '\n'
        new_html = html[:body_close] + block + html[body_close:]
    else:
        prefix = first.group(1) or first.group(2) or ''
        block = auth_script_block(prefix)
        new_html = html[:first.start()] + block + html[first.start():]

    if new_html == html:
        return False
    path.write_text(new_html, encoding="utf-8")
    return True


def main() -> None:
    changed, skipped = 0, 0
    for pattern in (
        "*.html",
        "catalog/*.html",
        "category/*.html",
        "read/*.html",
        "read-external/*.html",
        "read-external/bible/*.html",
    ):
        for path in sorted(SITE.glob(pattern)):
            if process(path):
                changed += 1
            else:
                skipped += 1
    print(f"Injected auth scripts into {changed} file(s); left {skipped} alone.")


if __name__ == "__main__":
    main()
