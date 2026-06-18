# replace_pdf_buttons.py — swap each reader's Download-PDF button for a
# "Go to site" link (sunnah.com for hadith, quran.com for the Qur'an).
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

HADITH_STEMS = ["bukhari", "muslim", "abu-dawud", "tirmidhi"]

def _new_anchor(stem: str) -> str:
    if stem == "quran":
        return ('<a href="https://quran.com" class="btn" target="_blank" '
                'rel="noopener">Read on Quran.com ↗</a>')
    return (f'<a href="{sl.collection_url(stem)}" class="btn" target="_blank" '
            f'rel="noopener">View on sunnah.com ↗</a>')

def swap_button(html: str, stem: str) -> tuple:
    pat = re.compile(r'<a href="\.\./assets/sources/' + re.escape(stem) +
                     r'\.pdf" class="btn" download>Download PDF</a>')
    new_html, n = pat.subn(_new_anchor(stem), html)
    return new_html, n

def main() -> None:
    for stem in HADITH_STEMS + ["quran"]:
        p = SITE / "read" / f"{stem}.html"
        html = p.read_text(encoding="utf-8")
        out, n = swap_button(html, stem)
        if n:
            p.write_text(out, encoding="utf-8")
        print(f"  {stem}: {n} button(s) swapped")

if __name__ == "__main__":
    main()
