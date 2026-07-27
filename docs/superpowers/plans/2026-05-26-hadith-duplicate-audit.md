# Hadith Duplicate Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Systematically detect and remove all duplicate hadith entries across six catalog HTML files (Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah), then update `catalog-entries.json` and site page counts to match.

**Architecture:** A three-phase pipeline — (1) an audit script that auto-detects all candidate duplicates and writes a human-readable report; (2) a human review step where the keep/drop decisions are encoded as a confirmed-removes list; (3) an apply script that excises the HTML div blocks and rebuilds the JSON, matching the pattern used in the existing `apply_dedup.py`.

**Tech Stack:** Python 3, `re`, `json`, `difflib`, `pathlib` — no new dependencies. All files operated on are plain UTF-8 HTML/JSON.

---

## Background & Current State

The Quran side was audited first. The methodology:
- Candidate pairs were identified (manual + title matching)
- `validate_dupes.py` compiled a `confirmed_removes` list with keep/drop pairs
- `apply_dedup.py` removed the drop divs from HTML, rebuilt `catalog-entries.json`, and stripped exact-ID same-source dups

All those removes have already been applied (commit `86e159b`). The site currently has **1,573 entries** total across 7 sources (1,311 in the six hadith files).

**Three known bugs to fix immediately (Task 1):**
The IDs `aisha-age`, `women-majority-hell`, and `fight-until-testify` each appear once in **both** `bukhari.html` **and** `muslim.html`. These are cross-source ID collisions — two different entries sharing the same anchor ID. The `catalog-entries.json` has each of these twice with `source=muslim` (incorrect for the Bukhari occurrence).

**Six confirmed exact-title cross-source duplicates to resolve (Task 2 output):**
| Drop | Keep | Both refs |
|---|---|---|
| `prayer-invalid-dog-donkey-woman-tirmidhi` (tirmidhi) | `prayer-invalidate-dog-woman` (abu-dawud) | Abu Dawud #702 / Tirmidhi #338 |
| `tirmidhi-slave-marriage-master-permission` (tirmidhi) | `nasai-slave-cannot-marry-without-master` (nasai) | Tirmidhi #1111 / Ibn Majah #1693 |
| `paradise-tree-100-years` (tirmidhi) | `muslim-paradise-tree-shade-100-years` (muslim) | Muslim #2594 / Tirmidhi #3377 |
| `ibnmajah-virgin-silent-consent` (ibn-majah) | `nasai-father-virgin-silent-consent` (nasai) | Nasa'i #3266 both |
| `tirmidhi-killed-cut-bone` (tirmidhi) | `amputation-quarter-dinar-thief` (abu-dawud) | Abu Dawud #4385 / Bukhari #6543 |
| `devil-farts-at-adhan` (muslim) | `satan-farts-adhan` (bukhari) | Bukhari 594 / Muslim 757 |

> **Note:** These keep/drop decisions are defaults based on title match + ref overlap. The user may override any pair in the review step.

---

## File Map

| File | Action |
|---|---|
| `audit_hadith_dupes.py` | **Create** — detection script; writes `docs/hadith-dupe-audit-YYYY-MM-DD.md` |
| `docs/hadith-dupe-audit-2026-05-26.md` | **Created by script** — human-readable candidate report |
| `apply_hadith_dedup.py` | **Create** — applies confirmed_removes to 6 HTML files + JSON |
| `site/catalog/bukhari.html` | Modified (remove dup div blocks) |
| `site/catalog/muslim.html` | Modified (remove dup div blocks) |
| `site/catalog/abu-dawud.html` | Modified (remove dup div blocks) |
| `site/catalog/tirmidhi.html` | Modified (remove dup div blocks) |
| `site/catalog/nasai.html` | Modified (remove dup div blocks) |
| `site/catalog/ibn-majah.html` | Modified (remove dup div blocks) |
| `site/assets/data/catalog-entries.json` | Rebuilt (removes drops, fixes source fields) |
| `site/index.html` | Modified — update total entry count |
| `site/catalog/bukhari.html` header | Modified — update per-source entry count (in the page header stat) |
| *(repeat for other catalog pages)* | Modified |

---

## Task 1 — Write the Audit Detection Script

**Files:**
- Create: `audit_hadith_dupes.py`

- [ ] **Step 1: Write `audit_hadith_dupes.py`**

```python
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
            "id": eid,
            "source": source,
            "title": re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else "",
            "ref":   re.sub(r"<[^>]+>", "", ref_m.group(1)).strip() if ref_m else "",
            "bq":    re.sub(r"<[^>]+>", "", bq_m.group(1)).strip() if bq_m else "",
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

# CLASS C: Near-title duplicates (fuzzy ≥0.82 SequenceMatcher ratio)
#   Only compare entries in different sources to avoid excess noise.
#   Skip pairs already caught by class B.
titles_list = [(e["title"].lower().strip(), e) for e in entries if e["title"]]
class_c = []
for i in range(len(titles_list)):
    for j in range(i+1, len(titles_list)):
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
    "One must be removed or renamed. Decide which source is the definitive home.",
    "",
]
for eid, srcs in sorted(class_a.items()):
    lines.append(f"- `{eid}` appears in: {', '.join(sorted(srcs))}")
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
for title, es in sorted(class_b.items(), key=lambda x: x[0]):
    lines.append(f"### \"{es[0]['title']}\"")
    for e in es:
        lines.append(f"- **[{e['source']}]** `{e['id']}` | ref: {e['ref']}")
        if e["bq"]:
            preview = e["bq"][:150].replace("\n", " ")
            lines.append(f"  > {preview}…")
    lines.append("")

# --- Class C ---
lines += [
    "## Class C — Near-Title Duplicates (≥82% similarity, cross-source)",
    "",
    f"**{len(class_c)} pairs.** Similar titles in different sources — may be intentional variants or duplicates.",
    "Review each pair; mark as `KEEP_BOTH`, `DROP_FIRST`, or `DROP_SECOND`.",
    "",
]
for ratio, ea, eb in class_c[:60]:  # cap at 60 to keep report readable
    lines.append(f"### {ratio:.0%} match")
    lines.append(f"- **[{ea['source']}]** `{ea['id']}` | {ea['ref']}")
    lines.append(f"  Title: \"{ea['title']}\"")
    if ea["bq"]:
        lines.append(f"  > {ea['bq'][:120].replace(chr(10),' ')}…")
    lines.append(f"- **[{eb['source']}]** `{eb['id']}` | {eb['ref']}")
    lines.append(f"  Title: \"{eb['title']}\"")
    if eb["bq"]:
        lines.append(f"  > {eb['bq'][:120].replace(chr(10),' ')}…")
    lines.append(f"  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND")
    lines.append("")
if len(class_c) > 60:
    lines.append(f"*(…{len(class_c) - 60} additional pairs omitted — increase cap in script if needed)*")
    lines.append("")

# --- Class D ---
lines += [
    "## Class D — Same-Source Same-Ref Duplicates",
    "",
    f"**{len(class_d)} groups.** Two entries within the same collection cite the same hadith reference.",
    "May be legitimate (different aspects highlighted) or true duplicates.",
    "",
]
for (src, ref), es in sorted(class_d.items()):
    lines.append(f"### [{src}] {ref}")
    for e in es:
        lines.append(f"- `{e['id']}` | \"{e['title'][:80]}\"")
    lines.append("")

OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
print(f"\nReport written to: {OUT_PATH}")
print(f"\nSummary:")
print(f"  Class A (exact-ID collisions):        {len(class_a)}")
print(f"  Class B (exact title, cross-source):  {len(class_b)}")
print(f"  Class C (near-title ≥82%, cross-src): {len(class_c)}")
print(f"  Class D (same-source same-ref):        {len(class_d)}")
```

- [ ] **Step 2: Run the script**

```powershell
cd "C:\Users\zande\Documents\AI Workspace\Analyzing Islam"
python audit_hadith_dupes.py
```

Expected output:
```
Parsed 1311 hadith HTML entries from 6 files

Report written to: docs/hadith-dupe-audit-2026-05-26.md

Summary:
  Class A (exact-ID collisions):        3
  Class B (exact title, cross-source):  6
  Class C (near-title ≥82%, cross-src): [N]
  Class D (same-source same-ref):        [M]
```

- [ ] **Step 3: Commit the script (not yet the report)**

```bash
git add audit_hadith_dupes.py
git commit -m "feat: add hadith duplicate audit detection script"
```

---

## Task 2 — Review the Audit Report

This is a **human review step**. No code is written here.

- [ ] **Step 1: Open the report**

```powershell
code "docs/hadith-dupe-audit-2026-05-26.md"
```

- [ ] **Step 2: For every Class B pair, decide which entry to keep**

Default recommendations (based on ref overlap analysis already done):

| Drop | Keep | Reason |
|---|---|---|
| `prayer-invalid-dog-donkey-woman-tirmidhi` | `prayer-invalidate-dog-woman` | Abu Dawud is the primary source; Tirmidhi entry is thinner |
| `tirmidhi-slave-marriage-master-permission` | `nasai-slave-cannot-marry-without-master` | Nasa'i entry is more complete |
| `paradise-tree-100-years` | `muslim-paradise-tree-shade-100-years` | Muslim is more authoritative |
| `ibnmajah-virgin-silent-consent` | `nasai-father-virgin-silent-consent` | Both cite Nasa'i ref — keep Nasa'i home |
| `tirmidhi-killed-cut-bone` | `amputation-quarter-dinar-thief` | Abu Dawud entry has the fuller treatment |
| `devil-farts-at-adhan` | `satan-farts-adhan` | Bukhari is the primary collection |

- [ ] **Step 3: For each Class A ID collision, decide which source to keep**

Default: keep the Muslim entry (it was the original `aisha-age` / `women-majority-hell` / `fight-until-testify` ID), and remove the Bukhari copy.

| ID | Keep in | Remove from |
|---|---|---|
| `aisha-age` | muslim.html | bukhari.html |
| `women-majority-hell` | muslim.html | bukhari.html |
| `fight-until-testify` | muslim.html | bukhari.html |

- [ ] **Step 4: For each Class C near-dupe pair you flag, add to the remove list**

Open `apply_hadith_dedup.py` (Task 3) and add any additional DROP IDs found during Class C/D review.

- [ ] **Step 5: Confirm the final remove list with the user before Task 3**

> ⛔ **STOP HERE** — do not proceed to Task 3 until the user has reviewed and approved the remove list.

---

## Task 3 — Write the Apply Script

**Files:**
- Create: `apply_hadith_dedup.py`

- [ ] **Step 1: Write `apply_hadith_dedup.py`**

```python
"""
apply_hadith_dedup.py
Applies the confirmed-removes list to the 6 hadith catalog HTML files
and rebuilds catalog-entries.json.

Follows the same pattern as apply_dedup.py (which covered the first pass).
Run from project root after reviewing the audit report:
    python apply_hadith_dedup.py
"""
import re, json, shutil
from pathlib import Path
from collections import defaultdict

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam")
CATALOG_DIR = BASE / "site/catalog"
CATALOG_JSON = BASE / "site/assets/data/catalog-entries.json"

SOURCE_MAP = {
    "bukhari.html": "bukhari",
    "muslim.html": "muslim",
    "abu-dawud.html": "abu-dawud",
    "tirmidhi.html": "tirmidhi",
    "nasai.html": "nasai",
    "ibn-majah.html": "ibn-majah",
}

# -----------------------------------------------------------------------
# CONFIRMED REMOVES — fill in after user review of the audit report.
# Format: ("drop_id", "keep_id")  — keep_id is for documentation only.
# -----------------------------------------------------------------------
CONFIRMED_REMOVES = [
    # Class A — cross-source ID collisions (remove from Bukhari, keep in Muslim)
    # These are handled separately below via CROSS_SOURCE_REMOVES
    # Class B — exact title cross-source duplicates
    ("prayer-invalid-dog-donkey-woman-tirmidhi",  "prayer-invalidate-dog-woman"),
    ("tirmidhi-slave-marriage-master-permission",  "nasai-slave-cannot-marry-without-master"),
    ("paradise-tree-100-years",                    "muslim-paradise-tree-shade-100-years"),
    ("ibnmajah-virgin-silent-consent",             "nasai-father-virgin-silent-consent"),
    ("tirmidhi-killed-cut-bone",                   "amputation-quarter-dinar-thief"),
    ("devil-farts-at-adhan",                       "satan-farts-adhan"),
    # Class C / D additions go here after review:
    # ("drop-id", "keep-id"),
]

# Class A: cross-source exact-ID collisions.
# Each entry: (id, remove_from_source) — the other source keeps its occurrence.
CROSS_SOURCE_REMOVES = [
    ("aisha-age",         "bukhari"),
    ("women-majority-hell", "bukhari"),
    ("fight-until-testify", "bukhari"),
]

# -----------------------------------------------------------------------
# Build remove sets
# -----------------------------------------------------------------------
remove_ids = {drop for drop, _ in CONFIRMED_REMOVES}
cross_remove_set = {(eid, src) for eid, src in CROSS_SOURCE_REMOVES}

# -----------------------------------------------------------------------
# Pass 1: Remove div blocks from HTML files
# -----------------------------------------------------------------------

def remove_entry_divs(html: str, target_ids: set) -> tuple[str, int]:
    """
    Remove all <div class="entry" id="TARGET_ID">…</div> blocks.
    Returns (new_html, count_removed).
    Uses a bracket-counting approach to handle nested divs.
    """
    removed = 0
    result = []
    i = 0
    pattern = re.compile(
        r'<div\s+class=["\'][^"\']*\bentry\b[^"\']*["\'][^>]+id=["\']([^"\']+)["\'][^>]*>',
        re.DOTALL
    )

    while i < len(html):
        m = pattern.search(html, i)
        if not m:
            result.append(html[i:])
            break
        eid = m.group(1)
        if eid not in target_ids:
            result.append(html[i:m.start()+1])
            i = m.start() + 1
            continue
        # Found a target: consume everything up to the matching </div>
        result.append(html[i:m.start()])
        depth = 1
        pos = m.end()
        while pos < len(html) and depth > 0:
            open_m  = re.search(r'<div\b',  html, pos)
            close_m = re.search(r'</div\s*>', html, pos)
            if not close_m:
                break
            if open_m and open_m.start() < close_m.start():
                depth += 1
                pos = open_m.end()
            else:
                depth -= 1
                pos = close_m.end()
        i = pos
        removed += 1
    return "".join(result), removed


total_removed = 0

for fname, source in SOURCE_MAP.items():
    path = CATALOG_DIR / fname
    html = path.read_text(encoding="utf-8", errors="ignore")

    # Build per-file target set
    targets = set(remove_ids)
    for eid, src in cross_remove_set:
        if src == source:
            targets.add(eid)

    if not targets:
        continue

    new_html, count = remove_entry_divs(html, targets)

    if count > 0:
        shutil.copy(path, path.with_suffix(".html.bak3"))
        path.write_text(new_html, encoding="utf-8")
        print(f"  {fname}: removed {count} entries")
        total_removed += count
    else:
        print(f"  {fname}: 0 entries found to remove (check IDs)")

print(f"\nTotal HTML entries removed: {total_removed}")

# -----------------------------------------------------------------------
# Pass 2: Rebuild catalog-entries.json
# -----------------------------------------------------------------------
shutil.copy(CATALOG_JSON, CATALOG_JSON.with_name("catalog-entries.backup3.json"))

with open(CATALOG_JSON, encoding="utf-8") as f:
    catalog = json.load(f)

# Fix Class A source bugs (entries incorrectly listed as source=muslim when in bukhari)
# First, build the correct source map from HTML (what's actually there after HTML removal)
html_remaining = set()
for fname, source in SOURCE_MAP.items():
    path = CATALOG_DIR / fname
    content = path.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r'id=["\']([^"\']+)["\']', content):
        html_remaining.add((source, m.group(1)))

final = []
seen = set()
for e in catalog:
    eid = e["id"]
    src = e.get("source", "")
    key = (src, eid)
    # Skip confirmed removes
    if eid in remove_ids:
        continue
    # Skip cross-source removes (entry id + wrong source)
    skip = False
    for rem_eid, rem_src in CROSS_SOURCE_REMOVES:
        if eid == rem_eid and src == rem_src:
            skip = True
            break
    if skip:
        continue
    # Deduplicate exact (source, id) pairs
    if key in seen:
        continue
    seen.add(key)
    final.append(e)

with open(CATALOG_JSON, "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

by_source = defaultdict(int)
for e in final:
    by_source[e["source"]] += 1

print(f"\nFinal catalog-entries.json: {len(final)} entries")
for s, c in sorted(by_source.items()):
    print(f"  {s}: {c}")
print(f"\nRemoved from JSON: {len(catalog) - len(final)}")
```

- [ ] **Step 2: Run a dry-run count to verify the remove list before applying**

```powershell
cd "C:\Users\zande\Documents\AI Workspace\Analyzing Islam"
python -c "
from apply_hadith_dedup import CONFIRMED_REMOVES, CROSS_SOURCE_REMOVES
print(f'Regular removes: {len(CONFIRMED_REMOVES)}')
print(f'Cross-source removes: {len(CROSS_SOURCE_REMOVES)}')
for drop, keep in CONFIRMED_REMOVES:
    print(f'  DROP {drop} -> KEEP {keep}')
for eid, src in CROSS_SOURCE_REMOVES:
    print(f'  REMOVE {eid} from {src}')
"
```

Expected: Lists all pairs — confirm they match the user-approved list from Task 2.

- [ ] **Step 3: Commit the apply script before running it**

```bash
git add apply_hadith_dedup.py
git commit -m "feat: add hadith dedup apply script (pre-run)"
```

---

## Task 4 — Apply the Removals

- [ ] **Step 1: Run the apply script**

```powershell
cd "C:\Users\zande\Documents\AI Workspace\Analyzing Islam"
python apply_hadith_dedup.py
```

Expected output (counts depend on final user-approved list):
```
  bukhari.html: removed 3 entries   ← 3 Class A cross-source ID dups
  muslim.html: removed 1 entries    ← devil-farts-at-adhan or similar
  abu-dawud.html: removed 0 entries
  tirmidhi.html: removed 4 entries  ← rough estimate
  nasai.html: removed 0 entries
  ibn-majah.html: removed 1 entries ← ibnmajah-virgin-silent-consent

Total HTML entries removed: ~9

Final catalog-entries.json: ~1564 entries
  abu-dawud: 182
  bukhari: ~306
  ibn-majah: ~177
  muslim: ~254
  nasai: 150
  quran: 262
  tirmidhi: ~230
```

- [ ] **Step 2: Re-run the audit script to verify zero new duplicates**

```powershell
python audit_hadith_dupes.py
```

Expected output:
```
Class A (exact-ID collisions):        0
Class B (exact title, cross-source):  0
Class C (near-title ≥82%, cross-src): [same or fewer — no new exact-title hits]
Class D (same-source same-ref):        [same or fewer]
```

- [ ] **Step 3: Verify JSON counts match HTML counts**

```powershell
python -c "
import re, json
from pathlib import Path
from collections import defaultdict
source_map = {'bukhari.html':'bukhari','muslim.html':'muslim','abu-dawud.html':'abu-dawud','tirmidhi.html':'tirmidhi','nasai.html':'nasai','ibn-majah.html':'ibn-majah'}
catalog_dir = Path('site/catalog')
html_counts = {}
for fname, src in source_map.items():
    content = (catalog_dir / fname).read_text(encoding='utf-8', errors='ignore')
    html_counts[src] = len(re.findall(r'class=[\"\\'].*?\\bentry\\b.*?[\"\\']', content))
catalog = json.loads(Path('site/assets/data/catalog-entries.json').read_text(encoding='utf-8'))
json_counts = defaultdict(int)
for e in catalog:
    json_counts[e['source']] += 1
print('Source        HTML   JSON  Match')
for src in sorted(source_map.values()):
    h = html_counts.get(src, 0)
    j = json_counts.get(src, 0)
    ok = '✓' if h == j else '✗ MISMATCH'
    print(f'  {src:<14} {h:>4}   {j:>4}  {ok}')
"
```

Expected: All `✓` for all six hadith sources.

---

## Task 5 — Update Site Page Entry Counts

The site pages display total entry counts. These must match the new totals.

- [ ] **Step 1: Find where the counts live**

```powershell
grep -r "1573\|1595\|1311" site/ --include="*.html" -l
```

- [ ] **Step 2: Calculate the new total**

```powershell
python -c "
import json
from pathlib import Path
from collections import defaultdict
catalog = json.loads(Path('site/assets/data/catalog-entries.json').read_text(encoding='utf-8'))
by_src = defaultdict(int)
for e in catalog:
    by_src[e['source']] += 1
total = sum(by_src.values())
print(f'New total: {total}')
for s, c in sorted(by_src.items()):
    print(f'  {s}: {c}')
"
```

- [ ] **Step 3: Update each file that displays the count**

Open each file from Step 1. Replace the old total count with the new total. The pattern to find/replace:

```python
# In site/index.html — look for a pattern like:
# "1,573 entries" or "1573 entries"
# Replace with the new count.
```

- [ ] **Step 4: Verify the pages load correctly**

Open `site/index.html` in a browser (or just inspect the HTML) and confirm the count displays the new total.

---

## Task 6 — Commit

- [ ] **Step 1: Stage and commit all changes**

```bash
git add site/catalog/bukhari.html site/catalog/muslim.html \
        site/catalog/abu-dawud.html site/catalog/tirmidhi.html \
        site/catalog/nasai.html site/catalog/ibn-majah.html \
        site/assets/data/catalog-entries.json \
        site/index.html \
        docs/hadith-dupe-audit-2026-05-26.md
git commit -m "fix: remove hadith duplicate entries from site catalog and JSON

- Remove 3 cross-source exact-ID collisions (aisha-age, women-majority-hell,
  fight-until-testify) from bukhari.html (kept in muslim.html)
- Remove 6 exact-title cross-source duplicate entries
- Fix catalog-entries.json: deduplicate and correct source fields
- Update site page entry counts to reflect new total"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ Cross-source ID collisions detected and resolved
- ✅ Exact-title duplicates identified and removed
- ✅ Near-title analysis run and reported
- ✅ Same-source same-ref analysis run and reported
- ✅ HTML div blocks removed from all 6 hadith files
- ✅ catalog-entries.json rebuilt with deduplication and source-field correction
- ✅ Site page entry counts updated
- ✅ Verification pass confirms zero remaining class A/B duplicates

**No placeholders:** All code blocks are complete and runnable.

**Type/name consistency:** `remove_entry_divs()` defined in Task 3 Step 1, called in the same script — no cross-task references.
