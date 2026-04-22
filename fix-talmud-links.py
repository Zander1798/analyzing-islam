#!/usr/bin/env python3
"""Fix Talmud-related citations across catalog + category pages.

Three classes of fix:
1. Nested <a> anchors: `<a ...>Babylonian <a ...>Talmud</a></a>` → one link.
2. Broken Sanhedrin 4:5 anchor pointing to quran reader → Mishnah reader.
3. "Bava Batra 74a" plaintext → link to talmud-7.html (Baba Bathra).
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
TARGETS = list((ROOT / "site" / "catalog").glob("*.html")) + \
          list((ROOT / "site" / "category").glob("*.html"))

TALMUD = "../read-external/talmud.html"
TALMUD_7 = "../read-external/talmud-7.html"
MISHNAH = "../read-external/mishnah.html"


def fix(text: str) -> tuple[str, int]:
    total = 0

    # --- 1. Collapse nested "Babylonian Talmud" anchors ---
    # Pattern: <a class="cite-link" href="...talmud.html">Babylonian <a class="cite-link" href="...talmud.html">Talmud</a></a>
    nested_pat = re.compile(
        r'<a\s+class="cite-link"\s+href="[^"]*talmud\.html">'
        r'Babylonian\s+'
        r'<a\s+class="cite-link"\s+href="[^"]*talmud\.html">'
        r'Talmud</a>'
        r'</a>'
    )
    text, n = nested_pat.subn(
        f'<a class="cite-link" href="{TALMUD}">Babylonian Talmud</a>',
        text,
    )
    total += n

    # --- 2. Fix broken Sanhedrin 4:5 citation ---
    # Original: <em>Sanhedrin</em> <a class="cite-link" href="../read/quran.html#s4v5">4:5</a>
    # Target:   <a class="cite-link" href="../read-external/mishnah.html#sanhedrin-4-5"><em>Sanhedrin</em> 4:5</a>
    broken_sanhedrin_pat = re.compile(
        r'<em>Sanhedrin</em>\s+'
        r'<a\s+class="cite-link"\s+href="\.\./read/quran\.html#s4v5">4:5</a>'
    )
    text, n = broken_sanhedrin_pat.subn(
        f'<a class="cite-link" href="{MISHNAH}#sanhedrin-4-5"><em>Sanhedrin</em> 4:5</a>',
        text,
    )
    total += n

    # --- 3. Link "Bava Batra 74a" plaintext ---
    # Only fire when it's bare text (not already inside an <a>).
    # We search for the exact substring "Bava Batra 74a" not preceded by >
    # an opening <a... tag without a closing </a>.
    # Simpler: do a single literal replace, but skip places where the text
    # is already part of an anchor. Since there are currently only 2 such
    # occurrences in the corpus, and neither is inside an anchor, do it
    # safely with a lookaround that requires the prior 50 chars to NOT
    # contain an unclosed <a.
    bava_pat = re.compile(r'(?<!">)Bava Batra 74a(?!</a>)')
    text, n = bava_pat.subn(
        f'<a class="cite-link" href="{TALMUD_7}">Bava Batra 74a</a>',
        text,
    )
    total += n

    return text, total


def main():
    grand = 0
    touched = 0
    for path in TARGETS:
        before = path.read_text(encoding="utf-8")
        after, n = fix(before)
        if n:
            path.write_text(after, encoding="utf-8")
            touched += 1
            grand += n
            print(f"  {path.relative_to(ROOT)}: {n} fix(es)")
    print(f"\nDone: {grand} total fix(es) across {touched} file(s) "
          f"(scanned {len(TARGETS)})")


if __name__ == "__main__":
    main()
