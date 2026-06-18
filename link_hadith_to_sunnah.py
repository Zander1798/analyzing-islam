# link_hadith_to_sunnah.py — make each hadith-ref label a link to that hadith
# on sunnah.com (per-hadith "Go to site"). Does not touch article id anchors.
import importlib.util, re, sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).parent
SITE = ROOT / "site"
_sl_spec = importlib.util.spec_from_file_location("sunnah_links", ROOT / "sunnah_links.py")
sl = importlib.util.module_from_spec(_sl_spec); _sl_spec.loader.exec_module(sl)

STEMS = ["bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah"]
# Capture the leading hadith number N from the ref label.
# Only matches spans that do NOT already contain an <a> tag (idempotent).
_REF = re.compile(r'<span class="hadith-ref">(Hadith (\d+) · Book \d+)</span>')

def add_links(html: str, stem: str) -> tuple:
    def repl(m):
        label, num = m.group(1), int(m.group(2))
        url = sl.hadith_url(stem, num)
        # NOTE: the "↗" external-link cue is rendered via CSS (.hadith-ref a::after
        # in reader.css), NOT as inline text. Adding literal text here would sit
        # inside the <article id="h{n}"> and shift saved-highlight character
        # offsets (highlights.js measures offsets within the anchor element).
        return (f'<span class="hadith-ref"><a href="{url}" target="_blank" '
                f'rel="noopener">{label}</a></span>')
    return _REF.subn(repl, html)

def main() -> None:
    for stem in STEMS:
        p = SITE / "read" / f"{stem}.html"
        html = p.read_text(encoding="utf-8")
        out, n = add_links(html, stem)
        if n:
            p.write_text(out, encoding="utf-8")
        print(f"  {stem}: {n} hadith links added")

if __name__ == "__main__":
    main()
