# Site Rebuild — Plan 1: Foundation (ref→anchor contract + link validator + read-page baseline) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the canonical citation `ref→anchor` module, regenerate the read pages deterministically, and establish a link-resolution gate that proves every catalog/category/quiz citation resolves to a real anchor — the foundation everything else in the site rebuild verifies against.

**Architecture:** A single pure-Python module (`refs.py`) is the one source of truth that turns a book/entry citation string (`"Q 2:25"`, `"Bukhari 240"`, `"Q 27:15–44"`) into a read-page `(slug, anchor)`. Read pages are regenerated from the local `hadith-json` (sunnah.com) and `quran-json` (Saheeh International) datasets via the existing builders. A validator (`validate_links.py`) consumes `refs.py` plus an anchor index of the regenerated read pages and reports any unresolved citation as a hard failure.

**Tech Stack:** Python 3 (stdlib only: `re`, `json`, `pathlib`, `html`), `pytest`. No new third-party dependencies.

## Global Constraints

- **Numbering contract (verbatim):** Qur'an `Q s:v` → anchor `s{s}v{v}` on `read/quran.html`; hadith `<Collection> N` → anchor `h{idInBook=N}` on `read/{slug}.html`.
- **Collection → read-page slug:** Bukhari→`bukhari`, Muslim→`muslim`, Abu Dawud→`abu-dawud`, Tirmidhi→`tirmidhi`, Nasa'i→`nasai`, Ibn Majah→`ibn-majah`.
- **A citation's canonical anchor is its FIRST verse/hadith.** For ranges (`Q 27:15–44`, `Tirmidhi 439-443`) and multi-refs (`Q 2:154,3:169–170`), the primary anchor is the first element/start of range. Both ASCII hyphen `-` and en-dash `–` (U+2013) are range separators.
- **Anchors are integer-keyed for hadith.** Read-page hadith anchors are `h{integer}`; a ref number's anchor uses its leading integer (`Muslim 2020a` → `h2020`). Refs whose anchor does not resolve are reported for manual reconciliation, never silently dropped.
- **Encoding:** all file I/O is UTF-8; scripts begin with `sys.stdout.reconfigure(encoding="utf-8")` guarded by try/except (repo convention).
- **Branch:** all work on `site-rebuild-from-books`. Frequent commits, one per task.
- **Repo convention:** standalone scripts live at repo root with hyphenated or underscore names; tests live in `tests/` and load hyphenated modules via `importlib.util.spec_from_file_location` (see `tests/test_book_html.py`). New foundation module uses an underscore name (`refs.py`) so it is directly importable.

---

### Task 1: Qur'an ref parsing in `refs.py`

**Files:**
- Create: `refs.py`
- Test: `tests/test_refs.py`

**Interfaces:**
- Produces: `parse_quran_ref(ref: str) -> list[tuple[int, int]]` — returns `(surah, verse)` pairs in source order; for a range returns only the start pair. Raises `RefError` on unparseable input.
- Produces: `quran_anchor(surah: int, verse: int) -> str` → `"s{surah}v{verse}"`.
- Produces: `RefError(ValueError)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_refs.py
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "refs", Path(__file__).parent.parent / "refs.py")
refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refs)


def test_quran_anchor_format():
    assert refs.quran_anchor(2, 25) == "s2v25"


def test_parse_quran_single():
    assert refs.parse_quran_ref("Q 2:25") == [(2, 25)]


def test_parse_quran_multi():
    # comma-separated distinct refs, source order preserved
    assert refs.parse_quran_ref("Q 2:154,3:169–170") == [(2, 154), (3, 169)]


def test_parse_quran_range_uses_start():
    # en-dash range -> start verse only
    assert refs.parse_quran_ref("Q 27:15–44") == [(27, 15)]
    # ascii hyphen range
    assert refs.parse_quran_ref("Q 9:5-6") == [(9, 5)]


def test_parse_quran_bad():
    with pytest.raises(refs.RefError):
        refs.parse_quran_ref("Bukhari 224")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_refs.py -v`
Expected: FAIL — `ModuleNotFoundError`/`AttributeError` (refs.py does not exist yet).

- [ ] **Step 3: Write minimal implementation**

```python
# refs.py — canonical citation ref -> read-page anchor mapping.
# Single source of truth binding book/entry citations to the rebuilt read
# pages. Consumed by the catalog generator (to emit links) and the link
# validator (to check them). Stdlib only.
import re

QURAN_SLUG = "quran"


class RefError(ValueError):
    """Raised when a citation string cannot be parsed."""


def quran_anchor(surah: int, verse: int) -> str:
    return f"s{surah}v{verse}"


# One "S:V" or "S:V-V" / "S:V–V" token; capture surah + first verse.
_QV = re.compile(r"\s*(\d+)\s*:\s*(\d+)")


def parse_quran_ref(ref: str) -> list[tuple[int, int]]:
    s = ref.strip()
    if not re.match(r"(?i)^q\b", s):
        raise RefError(f"Not a Qur'an ref: {ref!r}")
    body = re.sub(r"(?i)^q\s*", "", s)
    pairs: list[tuple[int, int]] = []
    for token in body.split(","):
        m = _QV.match(token)
        if not m:
            raise RefError(f"Unparseable Qur'an token {token!r} in {ref!r}")
        pairs.append((int(m.group(1)), int(m.group(2))))
    if not pairs:
        raise RefError(f"No verses in {ref!r}")
    return pairs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_refs.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add refs.py tests/test_refs.py
git commit -m "feat: add Qur'an ref parsing to refs.py"
```

---

### Task 2: Hadith ref parsing + collection slugs in `refs.py`

**Files:**
- Modify: `refs.py`
- Test: `tests/test_refs.py`

**Interfaces:**
- Consumes: `RefError` from Task 1.
- Produces: `COLLECTION_SLUGS: dict[str, str]` — normalized collection name → read-page slug.
- Produces: `parse_hadith_ref(ref: str) -> tuple[str, int]` — returns `(slug, idInBook)` from the leading integer of the number token. Raises `RefError` if the collection is unknown or no number is present.
- Produces: `hadith_anchor(idInBook: int) -> str` → `"h{idInBook}"`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_refs.py

def test_hadith_anchor_format():
    assert refs.hadith_anchor(224) == "h224"


def test_parse_hadith_basic():
    assert refs.parse_hadith_ref("Bukhari 224") == ("bukhari", 224)


def test_parse_hadith_slug_normalization():
    assert refs.parse_hadith_ref("Abu Dawud 1234") == ("abu-dawud", 1234)
    assert refs.parse_hadith_ref("Ibn Majah 90") == ("ibn-majah", 90)
    assert refs.parse_hadith_ref("Nasa'i 5397") == ("nasai", 5397)


def test_parse_hadith_letter_suffix_uses_leading_int():
    assert refs.parse_hadith_ref("Muslim 2020a") == ("muslim", 2020)


def test_parse_hadith_range_uses_start():
    assert refs.parse_hadith_ref("Tirmidhi 439-443") == ("tirmidhi", 439)


def test_parse_hadith_unknown_collection():
    with pytest.raises(refs.RefError):
        refs.parse_hadith_ref("Darimi 5")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_refs.py -v`
Expected: FAIL — `AttributeError: module 'refs' has no attribute 'parse_hadith_ref'`.

- [ ] **Step 3: Write minimal implementation**

```python
# append to refs.py

# Normalized collection name (lowercased, apostrophes/diacritics stripped to
# ASCII) -> read-page slug. Keys cover the spellings used in book verse_refs.
COLLECTION_SLUGS = {
    "bukhari": "bukhari",
    "muslim": "muslim",
    "abu dawud": "abu-dawud",
    "abudawud": "abu-dawud",
    "tirmidhi": "tirmidhi",
    "nasai": "nasai",
    "ibn majah": "ibn-majah",
    "ibnmajah": "ibn-majah",
}


def hadith_anchor(id_in_book: int) -> str:
    return f"h{id_in_book}"


def _normalize_collection(name: str) -> str:
    n = name.strip().lower()
    # Strip apostrophes/diacritic markers that appear in transliterations.
    n = n.replace("'", "").replace("`", "").replace("’", "")
    n = n.replace("ʾ", "").replace("ʿ", "")
    n = re.sub(r"\s+", " ", n)
    return n


def parse_hadith_ref(ref: str) -> tuple[str, int]:
    s = ref.strip()
    m = re.match(r"^(.+?)\s+(\d+)", s)
    if not m:
        raise RefError(f"No collection+number in {ref!r}")
    name = _normalize_collection(m.group(1))
    if name not in COLLECTION_SLUGS:
        raise RefError(f"Unknown collection {m.group(1)!r} in {ref!r}")
    return COLLECTION_SLUGS[name], int(m.group(2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_refs.py -v`
Expected: PASS (11 tests total).

- [ ] **Step 5: Commit**

```bash
git add refs.py tests/test_refs.py
git commit -m "feat: add hadith ref parsing + collection slugs to refs.py"
```

---

### Task 3: Unified `ref_to_links` dispatcher

**Files:**
- Modify: `refs.py`
- Test: `tests/test_refs.py`

**Interfaces:**
- Consumes: `parse_quran_ref`, `quran_anchor`, `parse_hadith_ref`, `hadith_anchor` from Tasks 1–2.
- Produces: `ref_to_links(ref: str) -> list[tuple[str, str]]` — list of `(slug, anchor)` for one citation string, source order; Qur'an multi-refs expand to one link per verse, hadith returns a single link. Raises `RefError` on unparseable input.
- Produces: `primary_anchor(ref: str) -> tuple[str, str]` — the first `(slug, anchor)` (what a heading ref links to).

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_refs.py

def test_ref_to_links_quran_multi():
    assert refs.ref_to_links("Q 2:154,3:169–170") == [
        ("quran", "s2v154"), ("quran", "s3v169")]


def test_ref_to_links_hadith():
    assert refs.ref_to_links("Bukhari 224") == [("bukhari", "h224")]


def test_primary_anchor_quran_range():
    assert refs.primary_anchor("Q 27:15–44") == ("quran", "s27v15")


def test_primary_anchor_hadith():
    assert refs.primary_anchor("Muslim 2020a") == ("muslim", "h2020")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_refs.py -v`
Expected: FAIL — `AttributeError: module 'refs' has no attribute 'ref_to_links'`.

- [ ] **Step 3: Write minimal implementation**

```python
# append to refs.py

def ref_to_links(ref: str) -> list[tuple[str, str]]:
    s = ref.strip()
    if re.match(r"(?i)^q\b", s):
        return [(QURAN_SLUG, quran_anchor(su, ve))
                for su, ve in parse_quran_ref(s)]
    slug, n = parse_hadith_ref(s)
    return [(slug, hadith_anchor(n))]


def primary_anchor(ref: str) -> tuple[str, str]:
    links = ref_to_links(ref)
    if not links:
        raise RefError(f"No links for {ref!r}")
    return links[0]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_refs.py -v`
Expected: PASS (15 tests total).

- [ ] **Step 5: Commit**

```bash
git add refs.py tests/test_refs.py
git commit -m "feat: add ref_to_links + primary_anchor dispatcher to refs.py"
```

---

### Task 4: Read-page anchor index + regeneration check

**Files:**
- Create: `read_anchors.py`
- Test: `tests/test_read_anchors.py`

**Interfaces:**
- Consumes: read pages at `site/read/{slug}.html`.
- Produces: `read_anchor_set(slug: str, site_dir: Path = SITE) -> set[str]` — the set of element `id="..."` anchors in that read page (cached). Returns empty set if the page is missing.
- Produces: `SITE: Path` — `<repo>/site`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_read_anchors.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "read_anchors", Path(__file__).parent.parent / "read_anchors.py")
ra = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ra)


def test_quran_has_known_anchor():
    anchors = ra.read_anchor_set("quran")
    assert "s2v25" in anchors


def test_bukhari_has_known_anchor():
    anchors = ra.read_anchor_set("bukhari")
    assert "h224" in anchors          # "urinated standing at a dump"
    assert "h7277" in anchors         # last idInBook


def test_missing_page_returns_empty():
    assert ra.read_anchor_set("does-not-exist") == set()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_read_anchors.py -v`
Expected: FAIL — `read_anchors.py` does not exist.

- [ ] **Step 3: Regenerate the read pages, then implement**

First regenerate the read pages from the local datasets so anchors are current and deterministic:

Run: `python build-hadith-readers.py`
Expected output includes: `Wrote bukhari.html: 7277 hadiths ...` for all six collections.

Run: `python build-quran-reader.py`
Expected: writes `site/read/quran.html`.

Then create the module:

```python
# read_anchors.py — index of anchors present in each rebuilt read page.
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SITE = Path(__file__).parent / "site"
_ID_RE = re.compile(r'id="([^"]+)"')
_cache: dict[str, set[str]] = {}


def read_anchor_set(slug: str, site_dir: Path = SITE) -> set[str]:
    key = f"{site_dir}::{slug}"
    if key in _cache:
        return _cache[key]
    path = site_dir / "read" / f"{slug}.html"
    if not path.exists():
        _cache[key] = set()
        return _cache[key]
    html = path.read_text(encoding="utf-8")
    _cache[key] = set(_ID_RE.findall(html))
    return _cache[key]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_read_anchors.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add read_anchors.py tests/test_read_anchors.py site/read/
git commit -m "feat: add read-page anchor index; regenerate read pages from datasets"
```

---

### Task 5: Link-resolution validator (`validate_links.py`)

**Files:**
- Create: `validate_links.py`
- Test: `tests/test_validate_links.py`

**Interfaces:**
- Consumes: `read_anchors.read_anchor_set`.
- Produces: `extract_read_links(html: str) -> list[tuple[str, str]]` — every `href="../read/{slug}.html#{anchor}"` in an HTML string, as `(slug, anchor)`.
- Produces: `unresolved_links(pairs: list[tuple[str,str]], site_dir=SITE) -> list[tuple[str,str]]` — the subset whose anchor is not present in the target read page.
- Produces: `scan_site(site_dir=SITE) -> dict` — `{"checked": int, "unresolved": list[dict]}` over `catalog/*.html`, `category/*.html`, and `assets/data/quiz-levels.json` source links. `main()` prints a report and exits non-zero if any unresolved.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_validate_links.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "validate_links", Path(__file__).parent.parent / "validate_links.py")
vl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vl)


def test_extract_read_links():
    html = ('<a class="cite-link" href="../read/quran.html#s2v25">Q 2:25</a> '
            '<a href="../read/bukhari.html#h224">Bukhari 224</a> '
            '<a href="../about.html">About</a>')
    assert vl.extract_read_links(html) == [
        ("quran", "s2v25"), ("bukhari", "h224")]


def test_unresolved_flags_missing_anchor():
    pairs = [("quran", "s2v25"), ("quran", "s999v999")]
    bad = vl.unresolved_links(pairs)
    assert ("quran", "s999v999") in bad
    assert ("quran", "s2v25") not in bad


def test_scan_site_baseline_zero_unresolved():
    """The current site must have zero unresolved read-links."""
    report = vl.scan_site()
    assert report["unresolved"] == [], (
        f"{len(report['unresolved'])} unresolved links: "
        f"{report['unresolved'][:10]}")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_validate_links.py -v`
Expected: FAIL — `validate_links.py` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
# validate_links.py — gate: every read-page citation must resolve to a real
# anchor in the regenerated read pages. Reuses read_anchors for the index.
import importlib.util
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"

_ra_spec = importlib.util.spec_from_file_location("read_anchors", ROOT / "read_anchors.py")
read_anchors = importlib.util.module_from_spec(_ra_spec)
_ra_spec.loader.exec_module(read_anchors)

_LINK_RE = re.compile(r'href="\.\./read/([a-z0-9-]+)\.html#([^"]+)"')
# quiz source links are stored without the "../" prefix, e.g. "read/quran.html#s1v2"
_QUIZ_RE = re.compile(r'(?:\.\./)?read/([a-z0-9-]+)\.html#([^"#]+)')


def extract_read_links(html: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _LINK_RE.finditer(html)]


def unresolved_links(pairs, site_dir: Path = SITE) -> list[tuple[str, str]]:
    bad = []
    for slug, anchor in pairs:
        if anchor not in read_anchors.read_anchor_set(slug, site_dir):
            bad.append((slug, anchor))
    return bad


def _quiz_source_pairs(site_dir: Path) -> list[tuple[str, str]]:
    qp = site_dir / "assets" / "data" / "quiz-levels.json"
    if not qp.exists():
        return []
    data = json.loads(qp.read_text(encoding="utf-8"))
    pairs = []
    for level in data.get("levels", []):
        for q in level.get("questions", []):
            src = q.get("source", "")
            m = _QUIZ_RE.search(src)
            if m:
                pairs.append((m.group(1), m.group(2)))
    return pairs


def scan_site(site_dir: Path = SITE) -> dict:
    targets = sorted((site_dir / "catalog").glob("*.html")) + \
              sorted((site_dir / "category").glob("*.html"))
    checked = 0
    unresolved: list[dict] = []
    for path in targets:
        html = path.read_text(encoding="utf-8")
        pairs = extract_read_links(html)
        checked += len(pairs)
        for slug, anchor in unresolved_links(pairs, site_dir):
            unresolved.append({"file": path.name, "slug": slug, "anchor": anchor})
    quiz_pairs = _quiz_source_pairs(site_dir)
    checked += len(quiz_pairs)
    for slug, anchor in unresolved_links(quiz_pairs, site_dir):
        unresolved.append({"file": "quiz-levels.json", "slug": slug, "anchor": anchor})
    return {"checked": checked, "unresolved": unresolved}


def main() -> None:
    report = scan_site()
    print(f"Checked {report['checked']} read-page links.")
    if report["unresolved"]:
        print(f"UNRESOLVED: {len(report['unresolved'])}")
        for u in report["unresolved"][:50]:
            print(f"  {u['file']}: {u['slug']}#{u['anchor']}")
        sys.exit(1)
    print("All read-page links resolve. ✓")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_validate_links.py -v`
Expected: PASS (3 tests). If `test_scan_site_baseline_zero_unresolved` fails, the current site already has broken citations — record the list in the commit message and raise with the user before proceeding (it is a pre-existing condition, not a regression from this plan).

- [ ] **Step 5: Commit**

```bash
git add validate_links.py tests/test_validate_links.py
git commit -m "feat: add read-link resolution validator + baseline gate"
```

---

### Task 6: Cross-check `refs.py` against real read anchors (integration gate)

**Files:**
- Test: `tests/test_refs_integration.py`

**Interfaces:**
- Consumes: `refs.ref_to_links`, `read_anchors.read_anchor_set`.

This task has no production code — it is the integration gate proving the contract module agrees with the regenerated read pages on real citations, so later plans can rely on `refs.py` for the supported ref forms, but MUST catch `RefError` and normalize the unsupported forms listed in the Reconciliation notes.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_refs_integration.py
import importlib.util
from pathlib import Path

def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent.parent / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

refs = _load("refs")
ra = _load("read_anchors")

# (ref string, expected first (slug, anchor)) — sampled from book verse_refs.
SAMPLES = [
    ("Q 2:25", ("quran", "s2v25")),
    ("Q 27:15–44", ("quran", "s27v15")),
    ("Bukhari 224", ("bukhari", "h224")),
    ("Bukhari 3185", ("bukhari", "h3185")),
    ("Nasa'i 5397", ("nasai", "h5397")),
]


def test_sampled_refs_resolve_to_existing_anchors():
    for ref, expected in SAMPLES:
        slug, anchor = refs.primary_anchor(ref)
        assert (slug, anchor) == expected, f"{ref} -> {(slug, anchor)}"
        assert anchor in ra.read_anchor_set(slug), \
            f"{ref}: anchor {slug}#{anchor} missing from read page"
```

- [ ] **Step 2: Run test to verify it fails (or passes outright)**

Run: `python -m pytest tests/test_refs_integration.py -v`
Expected: FAIL only if a sampled anchor is missing. If it passes immediately, that is acceptable — the test exists as a permanent regression gate. (If `Nasa'i 5397` fails, the collection's book-ref numbering may not equal `idInBook`; record it as a reconciliation item for Plan 2 and adjust the sample.)

- [ ] **Step 3: (only if failing) reconcile**

If a sample fails because the book ref number ≠ `idInBook`, document the collection and the discrepancy in `docs/superpowers/plans/2026-06-18-site-rebuild-plan1-foundation.md` under a new "Reconciliation notes" heading, and replace the failing sample with a verified one so the gate is green and the issue is tracked for Plan 2.

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest tests/test_refs.py tests/test_read_anchors.py tests/test_validate_links.py tests/test_refs_integration.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_refs_integration.py
git commit -m "test: integration gate binding refs.py to regenerated read anchors"
```

---

## Self-Review

**Spec coverage (Plan 1 portion of the spec):**
- Numbering contract (`Q s:v`→`#s{s}v{v}`, `<Collection> N`→`#h{idInBook}`) → Tasks 1–3 (`refs.py`) + Task 6 (integration gate). ✓
- Read pages rebuilt from `hadith-json` + `quran-json` → Task 4 (regeneration + anchor index). ✓
- Link alignment hard gate (entries + category + quiz `source` links resolve) → Task 5 (`validate_links.py`, baseline gate). ✓
- Qur'an already SI / hadith already idInBook → confirmed; Task 4 regenerates deterministically rather than migrating. ✓
- Out of scope for Plan 1 (handled in later plans): entry regeneration to mirror 1,524, PDF removal + "Go to site" cards, site-wide counts. Not covered here by design.

**Placeholder scan:** No TBD/TODO. Every code step shows complete code; every run step shows the command and expected result. The only conditional steps (Task 5 Step 4, Task 6 Steps 2–3) define exactly what to do in each branch. ✓

**Type consistency:** `ref_to_links`/`primary_anchor` return `(slug, anchor)` tuples used identically by `read_anchor_set(slug)` and `unresolved_links(pairs)`. `read_anchor_set(slug, site_dir=SITE)` signature matches both call sites (`validate_links`, tests). Anchor strings (`s2v25`, `h224`) are consistent across `quran_anchor`/`hadith_anchor`, the validator regexes, and the integration samples. ✓

## Reconciliation notes

Surfaced by the Plan 1 final review (tested against all 1,874 book refs in `../Analyzing Islam Books/data/*_v2.json`). These are book-data realities for Plan 2 to resolve, not Plan 1 regressions:

1. **Semicolon multi-refs (9 entries) — silent truncation.** e.g. `"Bukhari 1040; Bukhari 3199"`, `"Ibn Majah 2554; Muslim 1695a"`, `"Q 19:71–72; contrast Q 21:101–102"`. `ref_to_links` splits only on `,`, so the second citation is dropped. Some carry prose ("contrast", "see also"), so a naive `;` split is insufficient — Plan 2 must normalize these (split + strip annotations) before emitting links. Violates the "never silently dropped" constraint if left unhandled.
2. **RefError refs (109 entries).** Many are correctly non-resolvable (not in the Six Books: Musnad Ahmad, Mishkat al-Masabih, "untraceable in canonical collections"). Plan 2's catalog generator MUST wrap `primary_anchor`/`ref_to_links` in try/except `RefError` and render these as plain text (no link), never crash.
3. **Rejected-but-resolvable forms.** Colon-style hadith refs (`"abudawud:2311"`, ~6) and no-space Qur'an refs (`"Q4:92"`). Plan 2 should normalize these to the canonical `"<Collection> N"` / `"Q s:v"` forms (or extend the parser) so they resolve.
4. **Flip the baseline gate to strict.** Once Plan 2 regenerates catalog + category pages and drives `validate_links` to 0 unresolved, change the `xfail` in `tests/test_validate_links.py` to a hard assertion (remove the marker) so the gate can never silently regress.
