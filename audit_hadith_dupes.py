"""
audit_hadith_dupes.py
Detects candidate duplicate entries in the six hadith catalog HTML files.
Outputs a markdown report to docs/hadith-dupe-audit-YYYY-MM-DD.md

Run from project root:
    python audit_hadith_dupes.py
"""
import re, json, difflib
from pathlib import Path
from collections import defaultdict
from datetime import date

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG_DIR = BASE / "site/catalog"
CATALOG_JSON = BASE / "site/assets/data/catalog-entries.json"
OUT_PATH = BASE / f"docs/hadith-dupe-audit-{date.today()}.md"

SOURCE_MAP = {
    "bukhari.html": "bukhari",
    "muslim.html": "muslim",
    "abu-dawud.html": "abu-dawud",
    "tirmidhi.html": "tirmidhi",
    "nasai.html": "nasai",
    "ibn-majah.html": "ibn-majah",
}

# ---------------------------------------------------------------------------
# 1. Parse all hadith entries from HTML (id, source, title, ref, bq_text)
# ---------------------------------------------------------------------------
entries = []  # list of dicts

for fname, source in SOURCE_MAP.items():
    content = (CATALOG_DIR / fname).read_text(encoding="utf-8", errors="ignore")
    opens = list(re.finditer(
        r'<div\s+class=["\'][^"\']*\bentry\b[^"\']*["\'][^>]+id=["\']([^"\']+)["\']',
        content
    ))
    for i, m in enumerate(opens):
        eid = m.group(1)
        end = opens[i+1].start() if i+1 < len(opens) else len(content)
        chunk = content[m.start():end]
        title_m = re.search(r'class=["\'][^"\']*entry-title[^"\']*["\'][^>]*>(.*?)</span>', chunk, re.DOTALL)
        ref_m   = re.search(r'class=["\'][^"\']*\bref\b[^"\']*["\'][^>]*>.*?<a[^>]*>(.*?)</a>', chunk, re.DOTALL)
        bq_m    = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', chunk, re.DOTALL)
        entries.append({
            "id":     eid,
            "source": source,
            "title":  re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else "",
            "ref":    re.sub(r"<[^>]+>", "", ref_m.group(1)).strip() if ref_m else "",
            "bq":     re.sub(r"<[^>]+>", "", bq_m.group(1)).strip() if bq_m else "",
        })

print(f"Parsed {len(entries)} hadith HTML entries from {len(SOURCE_MAP)} files")

# ---------------------------------------------------------------------------
# 2. Detection — four candidate classes
# ---------------------------------------------------------------------------

# CLASS A: Cross-source exact-ID duplicates (same id in >1 source file)
id_to_sources = defaultdict(list)
for e in entries:
    id_to_sources[e["id"]].append(e["source"])
class_a = {eid: srcs for eid, srcs in id_to_sources.items() if len(srcs) > 1}

# CLASS B: Exact-title duplicates (cross-source, normalized)
title_map = defaultdict(list)
for e in entries:
    norm = e["title"].lower().strip()
    if norm:
        title_map[norm].append(e)
class_b = {t: es for t, es in title_map.items() if len(es) > 1}

# CLASS C: Near-title duplicates (fuzzy >= 0.82 SequenceMatcher ratio)
#   Only compare entries in different sources to avoid excess noise.
#   Skip pairs already caught by class B.
titles_list = [(e["title"].lower().strip(), e) for e in entries if e["title"]]
class_c = []
for i in range(len(titles_list)):
    for j in range(i + 1, len(titles_list)):
        ta, ea = titles_list[i]
        tb, eb = titles_list[j]
        if ea["source"] == eb["source"]:
            continue
        if ta == tb:
            continue  # already in class B
        ratio = difflib.SequenceMatcher(None, ta, tb).ratio()
        if ratio >= 0.82:
            class_c.append((ratio, ea, eb))
class_c.sort(key=lambda x: -x[0])

# CLASS D: Same-source same-ref duplicates (same hadith cited by two entries)
ref_src_map = defaultdict(list)
for e in entries:
    r = e["ref"].strip()
    if r:
        ref_src_map[(e["source"], r)].append(e)
class_d = {k: v for k, v in ref_src_map.items() if len(v) > 1}

# ---------------------------------------------------------------------------
# 3. Write the report
# ---------------------------------------------------------------------------
lines = [
    f"# Hadith Duplicate Audit — {date.today()}",
    "",
    f"Total hadith entries scanned: **{len(entries)}** across {len(SOURCE_MAP)} sources",
    "",
    "---",
    "",
]

# --- Class A ---
lines += [
    "## Class A — Cross-Source Exact-ID Collisions",
    "",
    f"**{len(class_a)} found.** These are hard bugs — two different entry `<div>` blocks share the same anchor ID.",
    "One must be removed from one of the files. Decide which source is the definitive home.",
    "",
]
if class_a:
    for eid, srcs in sorted(class_a.items()):
        lines.append(f"- `{eid}` appears in: {', '.join(sorted(srcs))}")
else:
    lines.append("*(none found)*")
lines.append("")

# --- Class B ---
lines += [
    "## Class B — Exact Title Duplicates (Cross-Source)",
    "",
    f"**{len(class_b)} groups.** Same title in different collections.",
    "Common cause: the hadith appears in multiple authoritative compilations.",
    "Recommended action: keep the entry with more analytical content; drop the thinner one.",
    "",
]
if class_b:
    for title, es in sorted(class_b.items(), key=lambda x: x[0]):
        lines.append(f"### \"{es[0]['title']}\"")
        for e in es:
            lines.append(f"- **[{e['source']}]** `{e['id']}` | ref: {e['ref']}")
            if e["bq"]:
                preview = e["bq"][:150].replace("\n", " ")
                lines.append(f"  > {preview}…")
        lines.append("")
else:
    lines.append("*(none found)*")
    lines.append("")

# --- Class C ---
lines += [
    "## Class C — Near-Title Duplicates (≥82% similarity, cross-source)",
    "",
    f"**{len(class_c)} pairs found.** Similar titles in different sources — may be intentional variants or duplicates.",
    "Review each pair; mark as `KEEP_BOTH`, `DROP_FIRST`, or `DROP_SECOND`.",
    "",
]
if class_c:
    cap = 80
    for ratio, ea, eb in class_c[:cap]:
        lines.append(f"### {ratio:.0%} match")
        lines.append(f"- **[{ea['source']}]** `{ea['id']}` | {ea['ref']}")
        lines.append(f"  Title: \"{ea['title']}\"")
        if ea["bq"]:
            lines.append(f"  > {ea['bq'][:150].replace(chr(10), ' ')}…")
        lines.append(f"- **[{eb['source']}]** `{eb['id']}` | {eb['ref']}")
        lines.append(f"  Title: \"{eb['title']}\"")
        if eb["bq"]:
            lines.append(f"  > {eb['bq'][:150].replace(chr(10), ' ')}…")
        lines.append(f"  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND")
        lines.append("")
    if len(class_c) > cap:
        lines.append(f"*(…{len(class_c) - cap} additional pairs omitted — lower threshold in script to see more)*")
        lines.append("")
else:
    lines.append("*(none found)*")
    lines.append("")

# --- Class D ---
lines += [
    "## Class D — Same-Source Same-Ref Duplicates",
    "",
    f"**{len(class_d)} groups.** Two entries within the same collection cite the same hadith reference number.",
    "May be legitimate (different aspects highlighted) or true duplicates.",
    "",
]
if class_d:
    for (src, ref), es in sorted(class_d.items()):
        lines.append(f"### [{src}] {ref}")
        for e in es:
            lines.append(f"- `{e['id']}` | \"{e['title'][:90]}\"")
            if e["bq"]:
                lines.append(f"  > {e['bq'][:150].replace(chr(10), ' ')}…")
        lines.append("")
else:
    lines.append("*(none found)*")
    lines.append("")

OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
print(f"\nReport written to: {OUT_PATH}")
print(f"\nSummary:")
print(f"  Class A (exact-ID collisions):        {len(class_a)}")
print(f"  Class B (exact title, cross-source):  {len(class_b)}")
print(f"  Class C (near-title >=82%, cross-src): {len(class_c)}")
print(f"  Class D (same-source same-ref):        {len(class_d)}")
