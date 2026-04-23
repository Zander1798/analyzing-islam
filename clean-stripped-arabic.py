"""Mechanical cleanup of "stripped-Arabic" artefacts across reader HTML.

When Arabic quotations were removed from the Ibn Kathīr / hadith pages
their wrapping punctuation (angle-quotes «», parens (), square brackets
[], curlies {}, RLM/LRM invisible marks, runs of colons) was left
behind, producing noise like:

    the Prophet said, «        » (It is Umm Al-Qur'an, …)
    «           :           :           »

This script:
  1. Splits the raw HTML on tag boundaries so it only edits text spans.
  2. On each text span: strips invisible marks, iteratively collapses
     bracket pairs whose interior has no alphanumeric character,
     removes bare colon runs, and tidies leftover whitespace.
  3. After text cleanup, regex-removes block elements (`<p>`, `<h2>`,
     `<blockquote>`) that ended up with no textual content.

Raw-string level work means the rest of the HTML (attributes, quote
styles, whitespace) is untouched — diffs are minimal and reviewable.

Run mode:
    python clean-stripped-arabic.py            # dry-run summary
    python clean-stripped-arabic.py --write    # apply to disk
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

# ---------------- Files to clean -----------------------------------------

TARGETS: list[Path] = []
TARGETS += sorted(SITE.glob("read-external/ibn-kathir-*.html"))
TARGETS += [
    SITE / "read/bukhari.html",
    SITE / "read/muslim.html",
    SITE / "read/abu-dawud.html",
    SITE / "read/tirmidhi.html",
    SITE / "read/nasai.html",
    SITE / "read/ibn-majah.html",
]

# ---------------- Text-level cleanup -------------------------------------

# Invisible directional marks that let stripped-Arabic brackets survive
# a naive grep.
INVISIBLE_MARKS = re.compile(r"[‎‏‪-‮⁦-⁩﻿]")

# An "alphanumeric" for our purposes includes digits, Latin letters,
# diacritic Latin, and the three non-Latin blocks we explicitly DON'T
# want to strip (Arabic, Hebrew, Greek — legitimate content).
ALNUM_CLASS_INNER = "A-Za-z0-9À-ɏ؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿֐-׿יִ-ﭏͰ-Ͽἀ-῿"

# Empty bracket pairs: open/close of the same family with no alnum inside.
EMPTY_BRACKET_RES = [
    re.compile(rf"«[^«»{ALNUM_CLASS_INNER}]*»"),
    re.compile(rf"\([^(){ALNUM_CLASS_INNER}]*\)"),
    re.compile(rf"\[[^\[\]{ALNUM_CLASS_INNER}]*\]"),
    re.compile(rf"\{{[^{{}}{ALNUM_CLASS_INNER}]*\}}"),
]

# Runs of bare colons with no word on either side.
COLON_RUN_RE = re.compile(r"(?<!\w)[ \t]*:(?:[ \t]*:)+[ \t]*(?!\w)")


def clean_text_span(t: str) -> tuple[str, int]:
    """Clean one text span (content between two HTML tags). Returns
    (new, removal_count)."""
    if not t.strip():
        return t, 0

    original = t
    removed = 0

    if INVISIBLE_MARKS.search(t):
        t = INVISIBLE_MARKS.sub("", t)

    # Iteratively eat empty bracket pairs until stable (handles nested
    # cases like « (  ) »).
    while True:
        changed = False
        for rx in EMPTY_BRACKET_RES:
            matches = rx.findall(t)
            if matches:
                t = rx.sub("", t)
                removed += len(matches)
                changed = True
        if not changed:
            break

    # Bare colon runs.
    if COLON_RUN_RE.search(t):
        t = COLON_RUN_RE.sub(" ", t)
        removed += 1

    # Tidy leftover whitespace / orphan punctuation the removals leave
    # behind. Keep line-break whitespace as-is so the diff stays small.
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r" ([,;.!?:])", r"\1", t)
    t = re.sub(r",\s*\.", ".", t)

    if t == original:
        return original, 0
    return t, removed


# ---------------- Tag-aware HTML splitting -------------------------------

# Split on tags but keep the tags as separate tokens, so we can edit only
# text. Good enough for our well-formed generated HTML.
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")

# Matches empty block elements (no children, only whitespace content).
EMPTY_BLOCK_RE = re.compile(
    r"<(p|h[1-6]|blockquote)(?:\s[^>]*)?>\s*</\1>", re.IGNORECASE
)


def clean_html(html: str) -> tuple[str, int, int]:
    """Return (new_html, text_removals, empty_block_removals)."""
    parts = TAG_SPLIT_RE.split(html)
    total = 0
    # Track whether we're inside a script / style where text must not
    # be touched.
    skip_depth = 0
    for i, piece in enumerate(parts):
        if piece.startswith("<"):
            # A tag — check if it opens/closes a script / style.
            lower = piece.lower()
            if lower.startswith("<script") or lower.startswith("<style"):
                skip_depth += 1
            elif lower.startswith("</script") or lower.startswith("</style"):
                skip_depth = max(0, skip_depth - 1)
            continue
        if skip_depth:
            continue
        cleaned, n = clean_text_span(piece)
        if n:
            parts[i] = cleaned
            total += n

    new_html = "".join(parts)

    # Cross-tag pass: in Ibn Kathīr some stripped quotations straddle a
    # paragraph break ("said, «</p><p>   -    :   »" → orphan « and »
    # sitting in neighbouring blocks). Match any « … » where the span
    # contains only whitespace / punctuation / HTML tags (entire tags as
    # single units) — if the visible text has no alphanumerics, it's a
    # dead quotation and we drop the whole range.
    # Tag width limit keeps us from swallowing legitimate long quotes.
    CROSS_TAG_EMPTY = re.compile(
        r"«(?:\s|<[^>]{0,80}>|[,.;:\-~=_‏‎]){0,80}»",
    )
    while True:
        before = new_html
        new_html, n = CROSS_TAG_EMPTY.subn("", new_html)
        total += n
        if new_html == before:
            break

    # Strip block elements that now have no content.
    empty_removed = 0
    while True:
        before = new_html
        new_html, n = EMPTY_BLOCK_RE.subn("", new_html)
        empty_removed += n
        if new_html == before:
            break

    return new_html, total, empty_removed


# ---------------- Driver -------------------------------------------------

def process(path: Path, write: bool) -> tuple[int, int, list[tuple[str, str]]]:
    html = path.read_text(encoding="utf-8")
    new_html, text_n, block_n = clean_html(html)
    if new_html == html:
        return 0, 0, []

    # Collect a few before/after text-span samples for human review.
    samples: list[tuple[str, str]] = []
    before_parts = TAG_SPLIT_RE.split(html)
    after_parts  = TAG_SPLIT_RE.split(new_html)
    # After structural empty-block deletion these lists can diverge in
    # length; do a quick zip up to the shorter one.
    for b, a in zip(before_parts, after_parts):
        if b.startswith("<") or b == a:
            continue
        if not b.strip() or b.strip() == a.strip():
            continue
        samples.append((b.strip()[:120], a.strip()[:120]))
        if len(samples) >= 3:
            break

    if write:
        path.write_text(new_html, encoding="utf-8")
    return text_n, block_n, samples


def main() -> None:
    write = "--write" in sys.argv[1:]
    total_text = 0
    total_blocks = 0
    by_file: dict[str, int] = {}
    sample_bag: list[tuple[str, str, str]] = []

    for path in TARGETS:
        if not path.exists():
            continue
        text_n, block_n, samples = process(path, write=write)
        if text_n or block_n:
            try:
                rel = str(path.relative_to(ROOT))
            except ValueError:
                rel = str(path)
            by_file[rel] = text_n
            total_text += text_n
            total_blocks += block_n
            for before, after in samples:
                if len(sample_bag) < 30:
                    sample_bag.append((path.name, before, after))

    mode = "APPLIED" if write else "DRY-RUN"
    print(f"\n=== {mode} ===")
    for f, n in sorted(by_file.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {n:6d}  {f}")
    print(f"  ------")
    print(f"  {total_text:6d} text removals, {total_blocks} empty-block drops, across {len(by_file)} file(s)")

    print("\n=== First 30 sample diffs ===")
    for fname, before, after in sample_bag:
        print(f"\n  {fname}")
        print(f"    BEFORE: {before!r}")
        print(f"    AFTER : {after!r}")


if __name__ == "__main__":
    main()
