"""Insert <script src=".../assets/js/track.js" defer></script> immediately after
the auth-ui.js tag on every page that has it and lacks track.js. Idempotent.
Mirrors sync-auth-scripts.py. Run as the LAST decorator (after split_readers.py)."""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
# Matches auth-ui.js tag regardless of attribute order (handles defer="" before src=)
# captures the relative prefix used by the auth-ui.js tag so track.js matches depth
AUTHUI_RE = re.compile(r'(<script\b[^>]*?\bsrc=")((?:\.\./)*)(assets/js/auth-ui\.js)("[^>]*></script>)', re.I)

def process(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    if "assets/js/track.js" in html:
        return False
    m = AUTHUI_RE.search(html)
    if not m:
        return False
    prefix = m.group(2)
    track = f'\n<script src="{prefix}assets/js/track.js" defer></script>'
    new = html[:m.end()] + track + html[m.end():]
    path.write_text(new, encoding="utf-8")
    return True

def main():
    changed = 0
    for p in SITE.rglob("*.html"):
        if process(p):
            changed += 1
    print(f"track.js injected into {changed} pages")

if __name__ == "__main__":
    main()
