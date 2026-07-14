#!/usr/bin/env python3
"""Fix src-link anchors that swallowed the tail of the PREVIOUS sentence.

Pattern: <a class="src-link" ...>God. Gabriel Said Reynolds, in ...</a>
The "God. " belongs to the prior sentence and must sit OUTSIDE the link:
         God. <a class="src-link" ...>Gabriel Said Reynolds, in ...</a>

Only the leading sentence-tail is moved out. Author initials ("Jonathan A.C.",
"James R.", "Wael B.") and abbreviations ("St.", "Vol.") are NOT touched.

    python fix-anchor-boundaries.py            # dry run (report only)
    python fix-anchor-boundaries.py --apply    # rewrite in place
"""
from __future__ import annotations
import os, re, sys, html
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
APPLY = "--apply" in sys.argv

ANCHOR = re.compile(r'(<a class="src-link"[^>]*>)(.*?)(</a>)', re.S)
TAG = re.compile(r"<[^>]+>")

# tokens that legitimately precede a "." inside a citation -> NOT a sentence tail
ABBREV = {"st","mt","dr","prof","rev","ed","eds","vol","vols","no","nos","jr","sr",
          "pp","p","ch","trans","ibid","cf","repr","ms","mss","fasc","pt","ser"}
INITIAL = re.compile(r"^[A-Z](\.[A-Z])*\.?$")   # A , A.C , N.J
FORCE_TAIL = {"ce","bce","bc","ad","ah"}        # era markers that end a sentence
ABBREV |= {"c", "circa", "ca"}                  # circa (e.g. "completed c. 1438") is NOT a tail

def leading_tail_len(plain: str):
    """Return the char length of a leading sentence-tail (incl. '. '), or 0."""
    m = re.match(r"^(.*?)\.\s+[A-Z]", plain)
    if not m:
        return 0
    lead = m.group(1).strip()
    if not lead or len(lead.split()) > 12:
        return 0
    last = lead.split()[-1].strip("('\"“”‘’’")
    lw = last.lower().rstrip(".")
    if lw in FORCE_TAIL:
        pass                                    # definitely a tail (e.g. "622 CE.")
    elif INITIAL.match(last):
        return 0                                # author initial -> keep
    elif lw in ABBREV:
        return 0                                # abbreviation -> keep
    elif not re.search(r"[a-z]$", last):
        return 0                                # ends in non-lowercase & not forced -> keep (safe)
    # length in the ORIGINAL plain string up to and including ". "
    return m.end(1) + (m.start() and 0) + (len(plain[m.end(1):]) - len(plain[m.end(1):].lstrip(". ")))

def process(text: str):
    changes = []
    def repl(mm: re.Match) -> str:
        open_t, inner, close_t = mm.groups()
        plain = html.unescape(TAG.sub("", inner))
        # locate first ". " boundary in plain and validate as a tail
        b = re.match(r"^(.*?)\.\s+(?=[A-Z])", plain)
        if not b:
            return mm.group(0)
        lead = b.group(1).strip()
        if not lead or len(lead.split()) > 12:
            return mm.group(0)
        last = lead.split()[-1].strip("('\"“”‘’")
        lw = last.lower().rstrip(".")
        if lw not in FORCE_TAIL:
            if INITIAL.match(last) or lw in ABBREV or not re.search(r"[a-z]$", last):
                return mm.group(0)
        # split RAW inner at its first ". " (the tail has no internal ". ")
        idx = inner.find(". ")
        if idx == -1:
            return mm.group(0)
        tail_raw = inner[:idx + 2]           # junk + ". "
        rest = inner[idx + 2:].lstrip()
        if not rest:
            return mm.group(0)
        changes.append((TAG.sub("", tail_raw).strip(), TAG.sub("", rest)[:50]))
        return f"{tail_raw}{open_t}{rest}{close_t}"
    new = ANCHOR.sub(repl, text)
    return new, changes

def main():
    total = 0; files = 0; samples = []
    for p in SITE.rglob("*.html"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if 'class="src-link"' not in t:
            continue
        new, ch = process(t)
        if ch:
            total += len(ch); files += 1
            samples.extend(ch[:2])
            if APPLY:
                p.write_text(new, encoding="utf-8")
    print(f"anchors fixed: {total} across {files} files" + ("" if APPLY else "  (DRY RUN)"))
    print("\nsample moves (tail moved OUT | remaining link text):")
    seen=set()
    for tail, rest in samples:
        if tail in seen: continue
        seen.add(tail)
        print(f"  {tail!r:<45} | {rest!r}")
        if len(seen) >= 40: break

if __name__ == "__main__":
    main()
