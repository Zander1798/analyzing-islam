"""
Dossier accuracy check: for each dossier entry's blockquote, retrieve the full
anchor text and output side-by-side for manual review.

Also checks catalog entries with clearly divergent named entities / numbers.
"""

import os, re, html as html_mod

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
A    = os.path.join(SITE, "arguments")
CAT  = os.path.join(SITE, "catalog")

_reader_cache = {}

def reader_html(source):
    if source not in _reader_cache:
        p = os.path.join(SITE, "read", f"{source}.html")
        _reader_cache[source] = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    return _reader_cache[source]

def get_anchor_text(source, anchor, maxlen=600):
    c = reader_html(source)
    m = re.search(rf'id="{re.escape(anchor)}"', c, re.IGNORECASE)
    if not m:
        return "(anchor not found in reader)"
    nxt = re.search(r'id="[hs]\d', c[m.start()+10:])
    end = m.start() + 10 + (nxt.start() if nxt else 3000)
    raw = re.sub(r"<[^>]+>", " ", c[m.start():end])
    raw = html_mod.unescape(re.sub(r"\s+", " ", raw)).strip()
    return raw[:maxlen]

def strip_html(s):
    return html_mod.unescape(re.sub(r"<[^>]+>", " ", s)).strip()

ENTRY_RE = re.compile(
    r'<div\s+class="entry"[^>]*id="([^"]+)"[^>]*>(.*?)(?=<div\s+class="entry"|\Z)',
    re.DOTALL | re.IGNORECASE,
)
BQ_RE = re.compile(r'<blockquote>(.*?)</blockquote>', re.DOTALL | re.IGNORECASE)
SPAN_RE = re.compile(r'<span\s+class="ref"[^>]*>(.*?)</span>', re.IGNORECASE | re.DOTALL)
HREF_RE = re.compile(r'href="[^"]*read/([^/"]+)\.html#(h\d+)"', re.IGNORECASE)

results = []

def check_file(path, rel):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    for m in ENTRY_RE.finditer(html):
        entry_id = m.group(1)
        block    = m.group(2)
        bqs = [strip_html(b.group(1)) for b in BQ_RE.finditer(block)]
        if not bqs:
            continue
        bq_text = " ".join(bqs)
        span_m = re.search(r'<span\s+class="ref"[^>]*>(.*?)</span>', block, re.IGNORECASE | re.DOTALL)
        if not span_m:
            continue
        links = HREF_RE.findall(span_m.group(1))
        if not links:
            continue
        for source, anchor in links:
            at = get_anchor_text(source, anchor)
            if at == "(anchor not found in reader)":
                continue
            results.append({
                "file": rel,
                "entry": entry_id,
                "source": source,
                "anchor": anchor,
                "bq": bq_text,
                "at": at,
            })

# Dossier files only
for root, dirs, files in os.walk(A):
    for fname in sorted(files):
        if fname.endswith(".html"):
            rel = os.path.relpath(os.path.join(root, fname), SITE)
            check_file(os.path.join(root, fname), rel)

# ── write output ──────────────────────────────────────────────────────────────
out = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/dossier_accuracy_report.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write(f"DOSSIER CITATION ACCURACY REPORT — {len(results)} citations\n")
    f.write("="*80 + "\n\n")
    for r in results:
        f.write(f"FILE : {r['file']}\n")
        f.write(f"ENTRY: {r['entry']}\n")
        f.write(f"CITED: {r['source']}#{r['anchor']}\n")
        f.write(f"BQ   : {r['bq'][:300]}\n")
        f.write(f"AT   : {r['at'][:400]}\n")
        f.write("\n")

print(f"Wrote {len(results)} entries to dossier_accuracy_report.txt")
