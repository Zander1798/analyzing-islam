# update_site_counts.py — replace hardcoded catalog figures with the new
# authoritative values across non-stats site pages (and stats.html headline).
import sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).parent
SITE = ROOT / "site"

# Global literal replacements applied to all PAGES.
# NOTE: some pages (catalog.html, read.html, saved.html, shared.html,
# read-islamic.html) have 1,549 / 1549 (an earlier stale count) rather than
# 1,541 — include those here so every page lands on 1,524.
GLOBAL = [
    ("1,549", "1,524"), ("1549", "1524"),   # earlier stale variant
    ("1,541", "1,524"), ("1541", "1524"),   # primary stale variant
    ("30 categories", "31 categories"),
]

# Pages that carry catalog-count copy / OG tags (NOT read-external).
# read-external.html is intentionally excluded — its numbers are scripture
# counts, not catalog counts.
PAGES = [
    "index.html", "about.html", "faq.html", "goat.html",
    "build.html", "compare.html", "play.html", "catalog.html", "stats.html",
    "read.html", "read-islamic.html", "saved.html", "shared.html",
]

# Per-source meta description count patches on site/catalog/{stem}.html.
# Only quran.html has a count in its <meta name="description">.
# Hadith catalog pages use "This collection is being built" — no count to patch.
# The replacements are scoped to the meta-description phrase so they cannot
# accidentally hit entry-body numbers.
PER_SOURCE = {
    # stem: (old_phrase, new_phrase)
    "quran":     ("262 critical-analysis", "275 critical-analysis"),
    # Hadith pages — no count in meta; these are no-ops but listed for
    # completeness so the script remains the single authoritative record.
    "bukhari":   ("301 critical-analysis", "315 critical-analysis"),
    "muslim":    ("250 critical-analysis", "264 critical-analysis"),
    "abu-dawud": ("178 critical-analysis", "181 critical-analysis"),
    "tirmidhi":  ("230 critical-analysis", "226 critical-analysis"),
    "nasai":     ("146 critical-analysis", "113 critical-analysis"),
    "ibn-majah": ("174 critical-analysis", "150 critical-analysis"),
}


def update_text(html: str, replacements):
    """Apply literal string replacements; return (new_html, total_count)."""
    n = 0
    for old, new in replacements:
        c = html.count(old)
        if c:
            html = html.replace(old, new)
            n += c
    return html, n


def main():
    # --- global count sweep ---
    for name in PAGES:
        p = SITE / name
        if not p.exists():
            print(f"  SKIP {name} (not found)")
            continue
        html = p.read_text(encoding="utf-8")
        out, n = update_text(html, GLOBAL)
        if n:
            p.write_text(out, encoding="utf-8")
        print(f"  {name}: {n} replacement(s)")

    # --- per-source meta description counts ---
    for stem, (old_phrase, new_phrase) in PER_SOURCE.items():
        p = SITE / "catalog" / f"{stem}.html"
        if not p.exists():
            print(f"  SKIP catalog/{stem}.html (not found)")
            continue
        html = p.read_text(encoding="utf-8")
        out = html.replace(old_phrase, new_phrase)
        if out != html:
            p.write_text(out, encoding="utf-8")
            print(f"  catalog/{stem}.html meta: {old_phrase!r} -> {new_phrase!r}")
        else:
            print(f"  catalog/{stem}.html: no match for {old_phrase!r} (skipped)")


if __name__ == "__main__":
    main()
