# Site Rebuild — Plan 4: Site-wide Counts & Stats Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Update every hardcoded catalog figure across the site to the new authoritative values — total **1,524** entries, **31** categories, the new per-source and per-category counts, strength distribution, and word frequencies — all derived from the regenerated catalog.

**Architecture:** `analyze-catalog-stats.py` already computes the figures from `site/catalog/*.html` and writes `.tmp/catalog-stats.json`. First fix its category taxonomy to the new 31-category set, then drive all updates from its output: a headline-count sweep across the non-stats pages, and a numbers update on `stats.html`.

**Tech Stack:** Python 3 (stdlib only), `pytest`.

## Global Constraints

- **Authoritative new figures (from `analyze-catalog-stats.py` on the regenerated catalog):**
  - Total entries: **1,524**. Per source: quran 275, bukhari 315, muslim 264, abu-dawud 181, tirmidhi 226, nasai 113, ibn-majah 150.
  - Strength distribution: basic 368, moderate 683, strong 473 → **76%** Moderate-or-above, **~31%** ("three in ten") Strong. (These two prose claims remain accurate — keep them.)
  - Categories: **31** (the book taxonomy). Top by count: Strange / Obscure 560, Women 335, Prophetic Character 322, Logical Inconsistency 220, Treatment of Disbelievers 178, Contradictions 100, Moral Problems 88, Eschatology 82, Governance 78, Warfare & Jihad 57, Jesus / Christology 54, Allah's Character 50. (Full set in `.tmp/catalog-stats.json` after the run.)
- **Category taxonomy = the 31 book categories** (same display→slug map as Plan 2). Notably: **Cosmology is removed** (renamed to Science; the `category/cosmology.html` redirect to science.html stays), **Science and Animals are added** relative to the stats script's old list. `Treatment of Disbelievers` is the display name; slug `disbelievers`.
- **Old strings to replace** (catalog-count contexts only — NOT scripture text in `read-external/`): `1,541`/`1541` → `1,524`; `30 categories` → `31 categories`; `1,541-entry` → `1,524-entry`; per-source meta counts on catalog pages (e.g. quran "262 ... entries" → "275").
- **Do not touch** `read-external/**` (Bible/Talmud numbers are scripture, not catalog counts) or the per-hadith counts inside read pages.
- **Chrome/prose preservation:** change only the figures (and the one distribution paragraph whose specific rankings changed). Don't restructure pages.
- **Branch:** `site-rebuild-from-books`. One commit per task. Stdlib only; UTF-8 guarded.

---

### Task 1: Fix stats taxonomy + regenerate stats JSON

**Files:**
- Modify: `analyze-catalog-stats.py` (the `CATEGORIES` list)
- Test: `tests/test_catalog_stats.py`

**Interfaces:** the script writes `.tmp/catalog-stats.json`. Confirm/locate its output structure (keys for total, per-category counts+strength, keyword frequencies) by reading the script; the test asserts on the JSON.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_catalog_stats.py
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).parent.parent

def test_stats_total_and_taxonomy():
    subprocess.run([sys.executable, "analyze-catalog-stats.py"], cwd=ROOT, check=True,
                   capture_output=True)
    data = json.loads((ROOT / ".tmp/catalog-stats.json").read_text(encoding="utf-8"))
    # total
    assert data["total"] == 1524
    # 31 categories, including the renamed/added ones and excluding cosmology
    cats = {c["name"] for c in data["categories"]}
    assert "Science" in cats and "Animals" in cats
    assert "Cosmology" not in cats
    assert len(data["categories"]) == 31
    # a couple of known counts
    by = {c["name"]: c["count"] for c in data["categories"]}
    assert by["Strange / Obscure"] == 560
    assert by["Women"] == 335
    assert by["Child Marriage"] == 14
```

(If the JSON's keys differ from `total`/`categories`/`name`/`count`, adjust the test to the script's actual schema — read the script first and match its real output keys.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_catalog_stats.py -v`
Expected: FAIL — old taxonomy yields wrong category set (no Science/Animals; has Cosmology) or a key mismatch.

- [ ] **Step 3: Fix the taxonomy**

In `analyze-catalog-stats.py`, update the `CATEGORIES` list to the 31 book categories: remove `("cosmology", "Cosmology")`; add `("science", "Science")` and `("animals", "Animals")`; ensure `("disbelievers", "Treatment of Disbelievers")` (display name) is present. The full 31 (slug, display) pairs are the inverse of the Plan 2 `CATEGORY_SLUGS` map. Keep the rest of the script unchanged. If the JSON schema needs a `total`/`categories` shape for the test, align the test to the script's existing output keys rather than changing the script's structure.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_catalog_stats.py -v`
Expected: PASS. Then inspect `.tmp/catalog-stats.json` and record the per-category counts + strong-tier rates and the top keyword frequencies — Task 3 needs them.

- [ ] **Step 5: Commit**

```bash
git add analyze-catalog-stats.py tests/test_catalog_stats.py
git commit -m "feat: update stats taxonomy to 31 categories; regenerate stats JSON"
```

---

### Task 2: Headline-count sweep across non-stats pages

**Files:**
- Create: `update_site_counts.py`
- Modify (via script): `site/index.html`, `site/about.html`, `site/faq.html`, and the OG/meta blocks on `site/{build,compare,faq,goat,play,index,about,stats,catalog}.html`; per-source meta on `site/catalog/{stem}.html`.
- Test: `tests/test_site_counts.py`

**Interfaces:**
- Produces: `update_text(html: str, replacements: list[tuple[str,str]]) -> tuple[str,int]` — applies literal string replacements, returns `(new, n)`.
- `main()` applies: global catalog-count replacements (`1,541`→`1,524`, `1541`→`1524`, `30 categories`→`31 categories`, `1,541-entry`→`1,524-entry`, `1,541 curated`→`1,524 curated`, `1,541 rated`/`1,541 tagged`/`1,541 entries`→`1,524 …`) to the listed non-`read-external` pages; and per-source meta-description counts on each `catalog/{stem}.html` (old→new: quran 262→275, bukhari 301→315, muslim 250→264, abu-dawud 178→181, tirmidhi 230→226, nasai 146→113, ibn-majah 174→150).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_site_counts.py
import re
from pathlib import Path
SITE = Path(__file__).parent.parent / "site"

CATALOG_COUNT_PAGES = ["index.html","about.html","faq.html","stats.html","goat.html",
                       "build.html","compare.html","play.html","catalog.html"]

def test_no_stale_total_in_catalog_pages():
    bad = []
    for name in CATALOG_COUNT_PAGES:
        t = (SITE / name).read_text(encoding="utf-8")
        if "1,541" in t or "1541" in t or "30 categories" in t:
            bad.append(name)
    assert bad == [], f"stale counts remain in {bad}"

def test_index_hero_number():
    t = (SITE / "index.html").read_text(encoding="utf-8")
    assert re.search(r'<span class="number">\s*1,524\s*</span>', t)

def test_quran_meta_updated():
    t = (SITE / "catalog/quran.html").read_text(encoding="utf-8")
    assert "275" in t and "262 critical-analysis" not in t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_site_counts.py -v`
Expected: FAIL — stale `1,541`/`30 categories` still present.

- [ ] **Step 3: Write the sweep script**

```python
# update_site_counts.py — replace hardcoded catalog figures with the new
# authoritative values across non-stats site pages (and stats.html headline).
import sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).parent
SITE = ROOT / "site"

GLOBAL = [
    ("1,541", "1,524"), ("1541", "1524"),
    ("30 categories", "31 categories"),
]
# pages that carry catalog-count copy / OG tags (NOT read-external)
PAGES = ["index.html","about.html","faq.html","goat.html","build.html",
         "compare.html","play.html","catalog.html","stats.html",
         "read.html","read-islamic.html","read-external.html","saved.html","shared.html"]
# per-source meta description counts on catalog pages
PER_SOURCE = {  # stem: (old, new)
    "quran": ("262","275"), "bukhari": ("301","315"), "muslim": ("250","264"),
    "abu-dawud": ("178","181"), "tirmidhi": ("230","226"),
    "nasai": ("146","113"), "ibn-majah": ("174","150"),
}

def update_text(html: str, replacements):
    n = 0
    for old, new in replacements:
        c = html.count(old)
        if c:
            html = html.replace(old, new); n += c
    return html, n

def main():
    for name in PAGES:
        p = SITE / name
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        out, n = update_text(html, GLOBAL)
        if n:
            p.write_text(out, encoding="utf-8")
        print(f"  {name}: {n} replacements")
    for stem,(old,new) in PER_SOURCE.items():
        p = SITE / "catalog" / f"{stem}.html"
        html = p.read_text(encoding="utf-8")
        # only the meta-description count phrase, e.g. "262 critical-analysis entries"
        out = html.replace(f"{old} critical-analysis", f"{new} critical-analysis")
        if out != html:
            p.write_text(out, encoding="utf-8")
            print(f"  catalog/{stem}.html meta: {old}->{new}")

if __name__ == "__main__":
    main()
```

NOTE: the per-source meta phrasing differs per source (quran says "critical-analysis entries on the Quran"; hadith pages say "… entries on Sahih al-Bukhari", etc.). The implementer MUST read each catalog page's `<meta name="description">` and replace the specific count token in context (don't blindly replace a bare number that may appear elsewhere). Adjust `PER_SOURCE` replacement phrasing per page after reading them.

- [ ] **Step 4: Run script + test**

Run: `python update_site_counts.py`
Run: `python -m pytest tests/test_site_counts.py -v` → PASS.
Manually confirm `git diff --stat` shows only the intended pages changed and the diffs are count-only.

- [ ] **Step 5: Commit**

```bash
git add update_site_counts.py tests/test_site_counts.py site/
git commit -m "feat: update headline catalog counts (1,524 / 31 categories) site-wide"
```

---

### Task 3: Update stats.html computed figures

**Files:**
- Modify: `site/stats.html`
- Test: `tests/test_stats_page.py`

**Interfaces:** none; a content update driven by `.tmp/catalog-stats.json` (Task 1).

Update every remaining catalog figure on `stats.html` to match the JSON:
- The headline metric `<div class="n">1,541</div>` → `1,524` (Task 2's global sweep already turns `1,541`→`1,524` here, so verify rather than redo).
- Each per-category section's `<div class="cat-meta">N entries · X% Strong-tier · …</div>` — set `N` and `X%` from the JSON (count and `round(100*strong/count)`). Add a Science section's figures; remove/--repoint the Cosmology section (its entries are now under Science). Keep section ordering as the page presents it (by Strong-rate) unless a count moved a category; minimally, correct the numbers in place.
- The word-frequency block (around the "Word-frequency across all 1,524 entry bodies" lede) → the new top keywords/counts from the JSON `keyword` frequencies (women 2114, slave 1237, kill 1228, death 946, wives 439, captive 399, jihad 347, stoning 306, …).
- The distribution paragraph (currently "cluster around four nodes: Prophetic Character (408), Women (376), Contradictions (301), Treatment of Disbelievers (211)") → rewrite with the new top nodes: **Strange / Obscure (560), Women (335), Prophetic Character (322), Logical Inconsistency (220)**, and adjust the surrounding sentence so the claim matches the new ranking.
- Keep the strength-distribution lede ("76% … Moderate or above", "three in ten … Strong") — still accurate (1156/1524 = 76%, 473/1524 = 31%).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stats_page.py
import json, re
from pathlib import Path
ROOT = Path(__file__).parent.parent
def test_stats_total_and_no_stale():
    t = (ROOT / "site/stats.html").read_text(encoding="utf-8")
    assert "1,524" in t
    assert "1,541" not in t and "1541" not in t
    # the metric block shows the new total
    assert re.search(r'<div class="n">\s*1,524\s*</div>', t)
def test_stats_distribution_nodes_updated():
    t = (ROOT / "site/stats.html").read_text(encoding="utf-8")
    # old top-node numbers must be gone; new top node present
    assert "Prophetic Character (408)" not in t
    assert "560" in t  # Strange / Obscure new count appears in the distribution prose
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_stats_page.py -v`
Expected: FAIL — distribution prose still has old nodes (and possibly stale total if Task 2 didn't cover a spot).

- [ ] **Step 3: Apply the updates**

Read `.tmp/catalog-stats.json` for exact per-category counts + strong rates and keyword frequencies. Then edit `site/stats.html`: correct each `cat-meta` count and Strong-tier %, the word-frequency entries, and rewrite the distribution paragraph with the new nodes (Strange / Obscure 560, Women 335, Prophetic Character 322, Logical Inconsistency 220). Verify the strength-distribution lede math (keep 76% / three-in-ten).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_stats_page.py -v` → PASS.
Run the full count tests: `python -m pytest tests/test_site_counts.py tests/test_stats_page.py tests/test_catalog_stats.py -v` → PASS.

- [ ] **Step 5: Commit**

```bash
git add site/stats.html tests/test_stats_page.py
git commit -m "feat: update stats.html figures to new catalog (1,524 / 31 categories)"
```

---

## Self-Review

**Spec coverage (Plan 4 portion):**
- Total + per-source + per-category counts updated → Tasks 1–3. ✓
- Category count 30→31 (cosmology→science, +animals) → Task 1 taxonomy + Task 2 sweep. ✓
- Home/about/faq/meta/OG headline figures → Task 2. ✓
- stats.html computed figures + distribution prose → Task 3. ✓
- Strength %/word-freq from authoritative script output → Tasks 1,3. ✓
- read-external scripture untouched → constrained out in Task 2. ✓

**Placeholder scan:** numeric targets are either fixed (1,524; 31; per-source counts) or sourced from the deterministic `catalog-stats.json` with the exact locations named. The per-source meta phrasing caveat is an explicit read-then-edit instruction.

**Type consistency:** `update_text(html, replacements) -> (html, n)` used consistently; per-source counts match Plan 2's verified counts.

## Notes for the user
- `stats.html` is analytical prose; Task 3 updates the figures and the one ranking-dependent paragraph, but if you want the surrounding analysis re-argued against the new distribution, that's an editorial pass beyond this sync.
