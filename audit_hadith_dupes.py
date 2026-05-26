"""
audit_hadith_dupes.py
Detects candidate INTRA-SOURCE duplicate entries within each hadith catalog HTML file.
Only compares entries within the same source (bukhari vs bukhari, muslim vs muslim, etc.)

Run from project root:
    python audit_hadith_dupes.py

Outputs: docs/hadith-dupe-audit-YYYY-MM-DD.md
"""
import re, json, difflib
from pathlib import Path
from collections import defaultdict
from datetime import date

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG_DIR = BASE / "site/catalog"
OUT_PATH = BASE / f"docs/hadith-dupe-audit-{date.today()}.md"

SOURCE_MAP = {
    "bukhari.html":   "bukhari",
    "muslim.html":    "muslim",
    "abu-dawud.html": "abu-dawud",
    "tirmidhi.html":  "tirmidhi",
    "nasai.html":     "nasai",
    "ibn-majah.html": "ibn-majah",
}

# ---------------------------------------------------------------------------
# 1. Parse all entries per source
# ---------------------------------------------------------------------------
by_source = {}   # source -> list of entry dicts

for fname, source in SOURCE_MAP.items():
    content = (CATALOG_DIR / fname).read_text(encoding="utf-8", errors="ignore")
    opens = list(re.finditer(
        r'<div\s+class=["\'][^"\']*\bentry\b[^"\']*["\'][^>]+id=["\']([^"\']+)["\']',
        content
    ))
    entries = []
    for i, m in enumerate(opens):
        eid = m.group(1)
        end = opens[i+1].start() if i+1 < len(opens) else len(content)
        chunk = content[m.start():end]
        title_m = re.search(r'class=["\'][^"\']*entry-title[^"\']*["\'][^>]*>(.*?)</span>', chunk, re.DOTALL)
        ref_m   = re.search(r'class=["\'][^"\']*\bref\b[^"\']*["\'][^>]*>.*?<a[^>]*>(.*?)</a>', chunk, re.DOTALL)
        bq_m    = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', chunk, re.DOTALL)
        entries.append({
            "id":    eid,
            "title": re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else "",
            "ref":   re.sub(r"<[^>]+>", "", ref_m.group(1)).strip() if ref_m else "",
            "bq":    re.sub(r"<[^>]+>", "", bq_m.group(1)).strip() if bq_m else "",
        })
    by_source[source] = entries
    print(f"  {source}: {len(entries)} entries")

total = sum(len(v) for v in by_source.values())
print(f"Total: {total} entries")

# ---------------------------------------------------------------------------
# 2. Intra-source detection per source
# ---------------------------------------------------------------------------

def normalize(text):
    return re.sub(r"[^\w\s]", "", text.lower().strip())

# Results containers
exact_id_dups   = {}   # source -> list of (id, count)
exact_title_dups = {}  # source -> list of (title, [entries])
near_title_pairs = {}  # source -> list of (ratio, ea, eb)
same_ref_groups  = {}  # source -> list of (ref, [entries])
content_pairs    = {}  # source -> list of (ratio, ea, eb)

for source, entries in by_source.items():
    # --- Exact-ID duplicates within this source ---
    id_counts = defaultdict(int)
    for e in entries:
        id_counts[e["id"]] += 1
    exact_id_dups[source] = [(eid, cnt) for eid, cnt in id_counts.items() if cnt > 1]

    # --- Exact-title duplicates within this source ---
    tmap = defaultdict(list)
    for e in entries:
        t = e["title"].lower().strip()
        if t:
            tmap[t].append(e)
    exact_title_dups[source] = [(t, es) for t, es in tmap.items() if len(es) > 1]

    # --- Near-title pairs (>=82%) within this source ---
    titles = [(e["title"].lower().strip(), e) for e in entries if e["title"]]
    pairs = []
    for i in range(len(titles)):
        for j in range(i+1, len(titles)):
            ta, ea = titles[i]
            tb, eb = titles[j]
            if ta == tb:
                continue  # already in exact_title
            ratio = difflib.SequenceMatcher(None, ta, tb).ratio()
            if ratio >= 0.80:
                pairs.append((ratio, ea, eb))
    pairs.sort(key=lambda x: -x[0])
    near_title_pairs[source] = pairs

    # --- Same-ref groups within this source ---
    rmap = defaultdict(list)
    for e in entries:
        r = e["ref"].strip()
        if r:
            rmap[r].append(e)
    same_ref_groups[source] = [(r, es) for r, es in rmap.items() if len(es) > 1]

    # --- High-content-similarity pairs (blockquote text >=0.75) ---
    bq_entries = [(e["bq"], e) for e in entries if len(e["bq"]) > 40]
    cpairs = []
    for i in range(len(bq_entries)):
        for j in range(i+1, len(bq_entries)):
            ba, ea = bq_entries[i]
            bb, eb = bq_entries[j]
            ratio = difflib.SequenceMatcher(None, ba[:400], bb[:400]).ratio()
            if ratio >= 0.75:
                cpairs.append((ratio, ea, eb))
    cpairs.sort(key=lambda x: -x[0])
    content_pairs[source] = cpairs

# ---------------------------------------------------------------------------
# 3. Write the report
# ---------------------------------------------------------------------------
lines = [
    f"# Hadith Intra-Source Duplicate Audit — {date.today()}",
    "",
    f"**Scope:** Entries compared only within the same source file.",
    f"**Total entries scanned:** {total} across {len(SOURCE_MAP)} sources",
    "",
    "---",
    "",
]

for source in SOURCE_MAP.values():
    entries = by_source[source]
    eid_dups   = exact_id_dups[source]
    etitle_dups= exact_title_dups[source]
    ntpairs    = near_title_pairs[source]
    srgroups   = same_ref_groups[source]
    cpairs     = content_pairs[source]

    total_flags = len(eid_dups) + len(etitle_dups) + len(ntpairs) + len(srgroups) + len(cpairs)
    lines += [
        f"## {source.upper()} ({len(entries)} entries)",
        "",
    ]

    # --- Exact-ID dups ---
    lines.append(f"### {source} — Exact-ID duplicates within this file")
    if eid_dups:
        for eid, cnt in eid_dups:
            lines.append(f"- `{eid}` appears **{cnt}×**")
    else:
        lines.append("*(none)*")
    lines.append("")

    # --- Exact-title dups ---
    lines.append(f"### {source} — Exact-title duplicates")
    if etitle_dups:
        for t, es in sorted(etitle_dups, key=lambda x: x[0]):
            lines.append(f"**\"{es[0]['title']}\"**")
            for e in es:
                lines.append(f"- `{e['id']}` | {e['ref']}")
                if e["bq"]:
                    lines.append(f"  > {e['bq'][:160].replace(chr(10),' ')}…")
            lines.append("")
    else:
        lines.append("*(none)*")
        lines.append("")

    # --- Near-title pairs ---
    lines.append(f"### {source} — Near-title pairs (≥80%)")
    if ntpairs:
        for ratio, ea, eb in ntpairs:
            lines.append(f"**{ratio:.0%}** | `{ea['id']}` vs `{eb['id']}`")
            lines.append(f"- \"{ea['title']}\" | {ea['ref']}")
            if ea["bq"]:
                lines.append(f"  > {ea['bq'][:160].replace(chr(10),' ')}…")
            lines.append(f"- \"{eb['title']}\" | {eb['ref']}")
            if eb["bq"]:
                lines.append(f"  > {eb['bq'][:160].replace(chr(10),' ')}…")
            lines.append(f"  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND")
            lines.append("")
    else:
        lines.append("*(none)*")
        lines.append("")

    # --- Same-ref groups ---
    lines.append(f"### {source} — Same-ref-number pairs")
    if srgroups:
        for ref, es in sorted(srgroups, key=lambda x: x[0]):
            lines.append(f"**Ref: {ref}**")
            for e in es:
                lines.append(f"- `{e['id']}` | \"{e['title'][:80]}\"")
                if e["bq"]:
                    lines.append(f"  > {e['bq'][:160].replace(chr(10),' ')}…")
            lines.append(f"  **Decision:** KEEP_BOTH / DROP one")
            lines.append("")
    else:
        lines.append("*(none)*")
        lines.append("")

    # --- Content similarity pairs ---
    lines.append(f"### {source} — High content-similarity pairs (≥75% blockquote match)")
    if cpairs:
        for ratio, ea, eb in cpairs:
            lines.append(f"**{ratio:.0%} content match** | `{ea['id']}` vs `{eb['id']}`")
            lines.append(f"- \"{ea['title']}\" | {ea['ref']}")
            lines.append(f"  > {ea['bq'][:200].replace(chr(10),' ')}…")
            lines.append(f"- \"{eb['title']}\" | {eb['ref']}")
            lines.append(f"  > {eb['bq'][:200].replace(chr(10),' ')}…")
            lines.append(f"  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND")
            lines.append("")
    else:
        lines.append("*(none)*")
        lines.append("")

    lines.append("---")
    lines.append("")

OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
print(f"\nReport written to: {OUT_PATH}")

# Summary
print("\nSummary by source:")
for source in SOURCE_MAP.values():
    nt = near_title_pairs[source]
    sr = same_ref_groups[source]
    cp = content_pairs[source]
    et = exact_title_dups[source]
    ei = exact_id_dups[source]
    print(f"  {source:<14} exact-ID:{len(ei)}  exact-title:{len(et)}  near-title:{len(nt)}  same-ref:{len(sr)}  content-sim:{len(cp)}")
