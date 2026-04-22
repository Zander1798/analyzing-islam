#!/usr/bin/env python3
"""Wrap every "Ibn Kathir" / "Ibn Kathīr" mention in catalog + category
pages with an anchor pointing to the corresponding Tafsir Ibn Kathir
reader page.

Target-picking rule (per mention):

  1. Look inside the enclosing paragraph (<p>...</p>). If it contains a
     quran reader ref like href="../read/quran.html#s{N}v{M}", link the
     Ibn Kathir mention to  ../read-external/ibn-kathir-{N}.html#a{M}.
  2. Otherwise link to  ../read-external/ibn-kathir.html  (the index).

Safe replacement:

  - Skips mentions already inside an <a>...</a> element (processed by
    temporarily replacing existing <a>...</a> with placeholders).
  - Only rewrites the <p> contents, never attributes or <script>/<style>.
  - Case-sensitive: "Ibn Kathir" and "Ibn Kathīr" match; nothing else.

Idempotent — rerunning is a no-op (mentions already wrapped in an <a>
with href pointing to the tafsir are skipped automatically).
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
TARGET_DIRS = [
    ROOT / "site" / "catalog",
    ROOT / "site" / "category",
]

NAME_PATTERN = re.compile(r"\bIbn Kath[īi]r\b")
# Block-level elements where Ibn Kathir mentions live in the entries:
# paragraphs and list items. Non-greedy, crosses newlines.
PARA_RE = re.compile(r"<(?:p|li)\b[^>]*>.*?</(?:p|li)>", re.DOTALL)
# Verse ref inside the paragraph that points to our Qur'an reader
VERSE_REF_RE = re.compile(
    r'href="(?:\.\./)?read/quran\.html#s(\d{1,3})v(\d{1,3})"'
)
# Existing <a>...</a> blocks — protect during replacement.
A_BLOCK_RE = re.compile(r"<a\b[^>]*>.*?</a>", re.DOTALL)


def target_href(surah: int | None, ayah: int | None) -> str:
    if surah is None:
        return "../read-external/ibn-kathir.html"
    return f"../read-external/ibn-kathir-{surah}.html#a{ayah}"


def link_in_paragraph(para: str) -> tuple[str, int]:
    """Return (rewritten paragraph, count of mentions linked)."""
    if not NAME_PATTERN.search(para):
        return para, 0

    # Pick target from first verse ref in this paragraph
    vm = VERSE_REF_RE.search(para)
    if vm:
        surah, ayah = int(vm.group(1)), int(vm.group(2))
    else:
        surah = ayah = None
    href = target_href(surah, ayah)

    # Protect existing <a>...</a> blocks so we don't nest anchors.
    placeholders: list[str] = []

    def stash(m: re.Match) -> str:
        placeholders.append(m.group(0))
        return f"\x00A{len(placeholders) - 1}\x00"

    stashed = A_BLOCK_RE.sub(stash, para)

    count_holder = [0]

    def wrap(m: re.Match) -> str:
        count_holder[0] += 1
        return f'<a class="cite-link" href="{href}">{m.group(0)}</a>'

    rewritten = NAME_PATTERN.sub(wrap, stashed)

    # Restore protected <a> blocks
    def restore(m: re.Match) -> str:
        return placeholders[int(m.group(1))]

    rewritten = re.sub(r"\x00A(\d+)\x00", restore, rewritten)
    return rewritten, count_holder[0]


def process_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    total = 0

    def replace_para(m: re.Match) -> str:
        nonlocal total
        new, n = link_in_paragraph(m.group(0))
        total += n
        return new

    new_text = PARA_RE.sub(replace_para, text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return total


def main() -> None:
    grand = 0
    changed = 0
    for d in TARGET_DIRS:
        for f in sorted(d.glob("*.html")):
            n = process_file(f)
            if n:
                print(f"  {f.relative_to(ROOT)}: linked {n} mention(s)")
                grand += n
                changed += 1
    print(f"\nLinked {grand} mentions across {changed} files.")


if __name__ == "__main__":
    main()
