#!/usr/bin/env python3
"""Link plain-text 'Q N:M' / 'Quran N:M' / 'Qur'an N:M' references
throughout catalog + category HTML that aren't already inside an <a>.

Skipped contexts:
  - already inside an <a> tag
  - inside <span class="entry-title">…</span>  (entry headings)
  - inside id="…" / href="…" / name="…" attribute values
  - verse ranges preserve their full "N:M-P" / "N:M-P:Q" form
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"
TARGETS = list((SITE / "catalog").glob("*.html")) + \
          list((SITE / "category").glob("*.html"))


# We match:
#   Q 4:34 | Q. 4:34 | Quran 4:34 | Qur'an 4:34 | Qur`an 4:34
# Optional range: 4:34-35   (we link to :34 only)
# Negative lookbehind: not preceded by # (e.g. "href=...#s4v34" — though
# those aren't plain "Q" anyway; attributes are handled separately).
REF_RE = re.compile(
    r"\b(?P<prefix>Q|Qur[ʾ'`]?an|Quran)(?P<dot>\.?)\s+(?P<ch>\d{1,3}):(?P<v>\d{1,3})(?P<range>[-–]\d{1,3}(?::\d{1,3})?)?\b"
)


def in_attr_value(text: str, pos: int) -> bool:
    """True if pos is inside a "…" attribute value."""
    # Find the last <...> tag open/close on this line
    # Simpler heuristic: count unescaped double-quotes between the last
    # '<' and our position. If odd, we're inside an attribute.
    last_lt = text.rfind("<", 0, pos)
    last_gt = text.rfind(">", 0, pos)
    if last_lt == -1 or last_gt > last_lt:
        return False  # not inside a tag
    chunk = text[last_lt:pos]
    return chunk.count('"') % 2 == 1


def in_anchor(text: str, pos: int) -> bool:
    before = text[:pos]
    last_open = before.rfind("<a ")
    last_close = before.rfind("</a>")
    if last_open == -1:
        return False
    return last_close == -1 or last_open > last_close


def in_entry_title(text: str, pos: int) -> bool:
    # span class="entry-title" opens and closes in ~one line. Check
    # that our pos is within the nearest <span class="entry-title"…>
    # and before its </span>.
    open_re = re.compile(r'<span\s+class="entry-title"[^>]*>', re.IGNORECASE)
    opens = [m.end() for m in open_re.finditer(text, 0, pos)]
    if not opens:
        return False
    last_open = opens[-1]
    # find the matching </span> after last_open
    close = text.find("</span>", last_open)
    if close == -1:
        return False
    return last_open <= pos < close


def link_refs(text: str) -> tuple[str, int]:
    """Return (new_text, count_linked)."""
    out = []
    last = 0
    count = 0
    for m in REF_RE.finditer(text):
        if in_anchor(text, m.start()):
            continue
        if in_attr_value(text, m.start()):
            continue
        if in_entry_title(text, m.start()):
            continue

        ch = m.group("ch")
        v = m.group("v")
        prefix = m.group("prefix")
        dot = m.group("dot")
        rng = m.group("range") or ""
        label = f"{prefix}{dot} {ch}:{v}{rng}"
        href = f"../read/quran.html#s{ch}v{v}"
        out.append(text[last:m.start()])
        out.append(f'<a class="cite-link" href="{href}">{label}</a>')
        last = m.end()
        count += 1
    out.append(text[last:])
    return "".join(out), count


def main():
    total = 0
    touched = 0
    for path in TARGETS:
        before = path.read_text(encoding="utf-8", errors="replace")
        after, n = link_refs(before)
        if n:
            path.write_text(after, encoding="utf-8")
            touched += 1
            total += n
            print(f"  {path.relative_to(ROOT)}: +{n} links")
    print(f"\nDone: {total} new Q-links across {touched} file(s).")


if __name__ == "__main__":
    main()
