#!/usr/bin/env python3
"""Split existing combined 'Muslim response (and why it fails)' sections into
two separate <h4> sections: 'The Muslim response' and 'Why it fails'.

The split heuristic: find the first 'But' / 'However' / 'Yet' pivot in the
first paragraph and break there. If no pivot, treat first paragraph as the
response and remaining paragraphs as the refutation. If only one paragraph
and no pivot, keep as 'The Muslim response' and leave a dangling 'Why it
fails' placeholder (rare; flagged in output for manual review).
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CATALOG_DIR = Path(__file__).parent / "site" / "catalog"

# Match: <h4>The Muslim response (and why it fails)</h4>\n    <p>...</p>[...more <p>...</p>]
# followed by </section> or next <h4>.
SECTION_RE = re.compile(
    r"<h4>The Muslim response \(and why it fails\)</h4>\s*\n"
    r"((?:\s*<p>.*?</p>\s*\n?)+)",
    re.DOTALL,
)

PARA_RE = re.compile(r"<p>(.*?)</p>", re.DOTALL)

PIVOTS = [" But ", " However, ", " However ", " Yet "]

def try_split_para(para):
    for p in PIVOTS:
        idx = para.find(p)
        if idx > 0:
            return para[:idx].rstrip(), p.strip() + " " + para[idx + len(p):].lstrip()
    return None, None

def process_section(match):
    block = match.group(1)
    paras = [m.strip() for m in PARA_RE.findall(block)]
    if not paras:
        return match.group(0)

    # Strategy 1: pivot-split inside first paragraph
    resp, ref = try_split_para(paras[0])
    if resp and ref:
        response_paras = [resp]
        refutation_paras = [ref] + paras[1:]
    elif len(paras) >= 2:
        # Strategy 2: first paragraph = response, rest = refutation
        response_paras = [paras[0]]
        refutation_paras = paras[1:]
    else:
        # Strategy 3 (fallback): only one paragraph and no pivot.
        # Put everything under 'The Muslim response' and create a minimal
        # Why-it-fails placeholder so the two h4s both exist.
        # Flag for manual review.
        print(f"  [FLAG] single-para no-pivot: {paras[0][:80]}...")
        response_paras = [paras[0]]
        refutation_paras = None

    out_lines = ["<h4>The Muslim response</h4>"]
    for p in response_paras:
        out_lines.append(f"    <p>{p}</p>")
    out_lines.append("    <h4>Why it fails</h4>")
    if refutation_paras is None:
        out_lines.append("    <p><em>(Needs expansion.)</em></p>")
    else:
        for p in refutation_paras:
            out_lines.append(f"    <p>{p}</p>")
    # Preserve original indentation context by prefixing with the same leading
    # whitespace the h4 had (we don't have it here, so just rely on 4-space
    # indent of inner content).
    return "    " + "\n    ".join(out_lines) + "\n"

total_split = 0
for f in sorted(CATALOG_DIR.glob("*.html")):
    text = f.read_text(encoding="utf-8")
    new_text, n = SECTION_RE.subn(process_section, text)
    if n:
        f.write_text(new_text, encoding="utf-8")
        print(f"{f.name}: split {n} combined section(s) into two h4s")
        total_split += n

print(f"\nTotal split: {total_split}")
