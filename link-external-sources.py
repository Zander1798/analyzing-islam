#!/usr/bin/env python3
"""Link mentions of the 11 indexed external sources inside catalog entries
to their reader pages under site/read-external/.

The strategy:
- For each HTML file in site/category/ and site/catalog/, find occurrences
  of known source-name patterns outside any existing <a>...</a> span and
  outside HTML head/style/script regions.
- Wrap at most N occurrences per source per file (to avoid visual clutter)
  in <a class="cite-link" href="../read-external/<slug>.html">…</a>.
- More-specific patterns are matched first so "Infancy Gospel of Thomas"
  doesn't get half-linked by a later shorter pattern.

Idempotent: if run twice, the second run is a no-op because matches inside
the produced <a class="cite-link">…</a> are skipped by the <a>-segment
splitter.
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
CATEGORY_DIR = ROOT / "site" / "category"
CATALOG_DIR = ROOT / "site" / "catalog"
EXT_BASE = "../read-external"

# Max links per source per file. Keeps the page from getting speckled with
# dotted underlines if the same name is mentioned 30 times.
MAX_PER_SOURCE_PER_FILE = 3

# Order matters: more-specific phrases first. The (?<![A-Za-z]) / (?![A-Za-z])
# boundaries behave like \b but also exclude diacritics on either side.
PATTERNS = [
    # Apocryphal Gospels — phrase match, longest first
    (r"(?<![A-Za-z])Infancy Gospel of Thomas(?![A-Za-z])", "apocryphal-gospels"),
    (r"(?<![A-Za-z])Infancy Gospel of James(?![A-Za-z])", "apocryphal-gospels"),
    (r"(?<![A-Za-z])Protoevangelium of James(?![A-Za-z])", "apocryphal-gospels"),
    (r"(?<![A-Za-z])Protevangelium of James(?![A-Za-z])", "apocryphal-gospels"),
    (r"(?<![A-Za-z])Arabic Infancy Gospel(?![A-Za-z])", "apocryphal-gospels"),
    (r"(?<![A-Za-z])apocryphal gospels?(?![A-Za-z])", "apocryphal-gospels"),

    # Josephus
    (r"(?<![A-Za-z])Antiquities of the Jews(?![A-Za-z])", "josephus"),
    (r"(?<![A-Za-z])(?:The )?Jewish Wars?(?![A-Za-z])", "josephus"),
    (r"(?<![A-Za-z])Flavius Josephus(?![A-Za-z])", "josephus"),
    (r"(?<![A-Za-z])Josephus(?![A-Za-z])", "josephus"),

    # Book of Enoch
    (r"(?<![A-Za-z])Book of Enoch(?![A-Za-z])", "book-of-enoch"),
    (r"(?<![A-Za-z])1 Enoch(?![A-Za-z])", "book-of-enoch"),

    # Tanakh / Hebrew Bible
    (r"(?<![A-Za-z])Hebrew Bible(?![A-Za-z])", "tanakh"),
    (r"(?<![A-Za-z])Tanakh(?![A-Za-z])", "tanakh"),

    # New Testament (and explicit gospel-of references)
    (r"(?<![A-Za-z])New Testament(?![A-Za-z])", "new-testament"),
    (r"(?<![A-Za-z])Gospel of (?:Matthew|Mark|Luke|John|Paul)(?![A-Za-z])", "new-testament"),
    (r"(?<![A-Za-z])canonical [Gg]ospels(?![A-Za-z])", "new-testament"),

    # Mishnah / Talmud
    (r"(?<![A-Za-z])Mishnah Sanhedrin(?![A-Za-z])", "mishnah"),
    (r"(?<![A-Za-z])Mishnah(?![A-Za-z])", "mishnah"),
    (r"(?<![A-Za-z])Babylonian Talmud(?![A-Za-z])", "talmud"),
    (r"(?<![A-Za-z])Talmud(?![A-Za-z])", "talmud"),

    # Baladhuri
    (r"(?<![A-Za-z])Fut[ūu]h al-Buld[āa]n(?![A-Za-z])", "baladhuri"),
    (r"(?<![A-Za-z])al-Bal[āa]dhur[īi](?![A-Za-z])", "baladhuri"),
    (r"(?<![A-Za-z])Bal[āa]dhur[īi](?![A-Za-z])", "baladhuri"),

    # Baydawi
    (r"(?<![A-Za-z])Anw[āa]r al-Tanz[īi]l(?![A-Za-z])", "baydawi"),
    (r"(?<![A-Za-z])al-Bay[ḍd][āa]w[īi](?![A-Za-z])", "baydawi"),
    (r"(?<![A-Za-z])Bay[ḍd][āa]w[īi](?![A-Za-z])", "baydawi"),

    # Ghazali
    (r"(?<![A-Za-z])I[ḥh]y[āa][ʾ']?(?=\s|,|\.|<)", "ghazali"),
    (r"(?<![A-Za-z])al-Ghaz[āa]l[īi](?![A-Za-z])", "ghazali"),
    (r"(?<![A-Za-z])Ghaz[āa]l[īi](?![A-Za-z])", "ghazali"),

    # Goldziher
    (r"(?<![A-Za-z])Muhammedanische Studien(?![A-Za-z])", "goldziher"),
    (r"(?<![A-Za-z])Muslim Studies(?![A-Za-z])", "goldziher"),
    (r"(?<![A-Za-z])Goldziher(?![A-Za-z])", "goldziher"),
]


SEGMENT_SPLIT_RE = re.compile(
    r"(<a\b[^>]*>.*?</a>"
    r"|<head\b[^>]*>.*?</head>"
    r"|<style\b[^>]*>.*?</style>"
    r"|<script\b[^>]*>.*?</script>)",
    re.DOTALL | re.IGNORECASE,
)


def link_in_file(text: str) -> tuple[str, int]:
    """Return (new_text, num_links_added)."""
    # Split on anchor/head/style/script spans.
    parts = SEGMENT_SPLIT_RE.split(text)

    # Track count per target slug across the WHOLE file.
    per_slug_count = {}
    total_added = 0

    # Process only non-matched segments (even indices).
    for i in range(0, len(parts), 2):
        segment = parts[i]
        for pattern_re, slug in PATTERNS:
            if per_slug_count.get(slug, 0) >= MAX_PER_SOURCE_PER_FILE:
                continue
            href = f"{EXT_BASE}/{slug}.html"

            def make_repl(local_slug, local_href):
                def repl(m):
                    nonlocal total_added
                    if per_slug_count.get(local_slug, 0) >= MAX_PER_SOURCE_PER_FILE:
                        return m.group(0)
                    per_slug_count[local_slug] = per_slug_count.get(local_slug, 0) + 1
                    total_added += 1
                    return f'<a class="cite-link" href="{local_href}">{m.group(0)}</a>'
                return repl

            # Only do up to the remaining budget for this source.
            remaining = MAX_PER_SOURCE_PER_FILE - per_slug_count.get(slug, 0)
            segment = re.sub(pattern_re, make_repl(slug, href), segment, count=remaining)
        parts[i] = segment

    return "".join(parts), total_added


def main():
    targets = list(CATEGORY_DIR.glob("*.html")) + list(CATALOG_DIR.glob("*.html"))
    changed = 0
    total_links = 0
    for f in targets:
        original = f.read_text(encoding="utf-8")
        new_text, added = link_in_file(original)
        if new_text != original:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
            total_links += added
            print(f"  {f.relative_to(ROOT)}: +{added} link(s)")
    print(f"\nFiles updated: {changed} / {len(targets)}   links added: {total_links}")


if __name__ == "__main__":
    main()
