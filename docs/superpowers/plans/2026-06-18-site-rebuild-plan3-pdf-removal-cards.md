# Site Rebuild — Plan 3: PDF Removal + sunnah.com "Go to site" links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Remove the PDF-download feature from the site and replace it with "Go to site" links to sunnah.com (per collection and per hadith), so a reader can verify any hadith against its authoritative source — while keeping every existing page's chrome intact.

**Architecture:** A small helper (`sunnah_links.py`) maps a collection to its sunnah.com URL slug and builds per-hadith / per-collection URLs (verified scheme: `https://sunnah.com/{slug}:{idInBook}` and `https://sunnah.com/{slug}`). In-place surgery on the existing read pages: (a) swap each reader's "Download PDF" button for a "View on sunnah.com" button; (b) wrap each hadith's `hadith-ref` label in a per-hadith sunnah.com link; (c) delete the orphaned per-volume PDF pages. The link validator (Plan 1) confirms internal citation links remain at zero; quiz `source` links are already validated there.

**Tech Stack:** Python 3 (stdlib only), `pytest`. Reuses Plan 1 `validate_links.py`.

## Global Constraints

- **sunnah.com slugs (verified scheme):** bukhari→`bukhari`, muslim→`muslim`, abu-dawud→`abudawud`, tirmidhi→`tirmidhi`, nasai→`nasai`, ibn-majah→`ibnmajah`. Per-hadith URL `https://sunnah.com/{slug}:{idInBook}`; collection URL `https://sunnah.com/{slug}`. (`sunnah.com/bukhari:224` and `sunnah.com/nasai:5397` confirmed HTTP 200.)
- **Quran reader exception:** the Qur'an is not a sunnah.com resource. Its "Download PDF" button is replaced with a link to `https://quran.com` (Saheeh International is quran.com's default). Flagged for the user.
- **Chrome preservation:** edit ONLY the targeted markup (the `reader-cta` button; the `hadith-ref` span). Never alter head/nav/scripts/other structure. Verify byte-identical outside the edited spans.
- **Do not break anchors:** per-hadith links go INSIDE the `hadith-ref` span; the `id="h{N}"` anchor lives on the enclosing `<article>` and must be untouched. `read_anchor_set` counts must be unchanged after editing.
- **PDF asset files** (`site/assets/sources/*.pdf`, `*/*.pdf`) are left on disk (removing the UI removes the "function"); they become unreferenced. Noted for the user to purge if desired.
- **External links** open in a new tab: `target="_blank" rel="noopener"`.
- **Reader "Download PDF" markup (current, 5 readers):** `<a href="../assets/sources/{stem}.pdf" class="btn" download>Download PDF</a>` inside `<div class="reader-cta">`. Present in bukhari, muslim, abu-dawud, tirmidhi, quran. (nasai, ibn-majah readers have no PDF button.)
- **Per-hadith label markup (current):** `<span class="hadith-ref">Hadith {N} · Book {B}</span>` (N = idInBook).
- **Orphan volume pages:** `site/read/nasai-v{1..6}.html`, `site/read/ibn-majah-v{1..5}.html` — 11 files, no referrers in `site/` — delete.
- **Branch:** `site-rebuild-from-books`. One commit per task. Stdlib only; UTF-8 guarded.

---

### Task 1: `sunnah_links.py` helper

**Files:**
- Create: `sunnah_links.py`
- Test: `tests/test_sunnah_links.py`

**Interfaces:**
- Produces: `SUNNAH_SLUGS: dict[str,str]` — site read-page slug → sunnah.com slug.
- Produces: `collection_url(site_slug: str) -> str` → `https://sunnah.com/{slug}`.
- Produces: `hadith_url(site_slug: str, id_in_book: int) -> str` → `https://sunnah.com/{slug}:{id_in_book}`.
- Both raise `KeyError` on a non-hadith slug (e.g. `quran`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sunnah_links.py
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("sunnah_links", Path(__file__).parent.parent / "sunnah_links.py")
sl = importlib.util.module_from_spec(spec); spec.loader.exec_module(sl)

def test_slugs():
    assert sl.SUNNAH_SLUGS == {"bukhari":"bukhari","muslim":"muslim","abu-dawud":"abudawud",
                               "tirmidhi":"tirmidhi","nasai":"nasai","ibn-majah":"ibnmajah"}

def test_collection_url():
    assert sl.collection_url("abu-dawud") == "https://sunnah.com/abudawud"

def test_hadith_url():
    assert sl.hadith_url("bukhari", 224) == "https://sunnah.com/bukhari:224"
    assert sl.hadith_url("ibn-majah", 90) == "https://sunnah.com/ibnmajah:90"

def test_non_hadith_raises():
    with pytest.raises(KeyError):
        sl.hadith_url("quran", 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sunnah_links.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# sunnah_links.py — build sunnah.com URLs for "Go to site" links.
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SUNNAH_SLUGS = {
    "bukhari": "bukhari", "muslim": "muslim", "abu-dawud": "abudawud",
    "tirmidhi": "tirmidhi", "nasai": "nasai", "ibn-majah": "ibnmajah",
}

def collection_url(site_slug: str) -> str:
    return f"https://sunnah.com/{SUNNAH_SLUGS[site_slug]}"

def hadith_url(site_slug: str, id_in_book: int) -> str:
    return f"https://sunnah.com/{SUNNAH_SLUGS[site_slug]}:{id_in_book}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sunnah_links.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add sunnah_links.py tests/test_sunnah_links.py
git commit -m "feat: add sunnah.com URL helper (sunnah_links.py)"
```

---

### Task 2: Swap reader "Download PDF" button → "Go to site"

**Files:**
- Create: `replace_pdf_buttons.py`
- Modify (via the script): `site/read/{bukhari,muslim,abu-dawud,tirmidhi,quran}.html`
- Test: `tests/test_replace_pdf_buttons.py`

**Interfaces:**
- Produces: `swap_button(html: str, stem: str) -> tuple[str,int]` — replaces the exact `Download PDF` anchor with a "Go to site" anchor; returns `(new_html, n_replaced)`. For hadith stems the href is `collection_url(stem)` and text `View on sunnah.com ↗`; for `quran` the href is `https://quran.com` and text `Read on Quran.com ↗`. Idempotent (0 replacements if already swapped).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_replace_pdf_buttons.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("rpb", Path(__file__).parent.parent / "replace_pdf_buttons.py")
rpb = importlib.util.module_from_spec(spec); spec.loader.exec_module(rpb)

def test_swap_hadith():
    html = '<div class="reader-cta"><a href="../read-islamic.html" class="btn">x</a><a href="../assets/sources/bukhari.pdf" class="btn" download>Download PDF</a></div>'
    out, n = rpb.swap_button(html, "bukhari")
    assert n == 1
    assert "assets/sources/bukhari.pdf" not in out
    assert 'href="https://sunnah.com/bukhari"' in out
    assert "View on sunnah.com" in out
    assert 'target="_blank"' in out and 'rel="noopener"' in out

def test_swap_quran_uses_quran_com():
    html = '<a href="../assets/sources/quran.pdf" class="btn" download>Download PDF</a>'
    out, n = rpb.swap_button(html, "quran")
    assert n == 1 and "https://quran.com" in out and "sunnah.com" not in out

def test_idempotent():
    html = '<a href="https://sunnah.com/bukhari" class="btn" target="_blank" rel="noopener">View on sunnah.com ↗</a>'
    out, n = rpb.swap_button(html, "bukhari")
    assert n == 0 and out == html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_replace_pdf_buttons.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# replace_pdf_buttons.py — swap each reader's Download-PDF button for a
# "Go to site" link (sunnah.com for hadith, quran.com for the Qur'an).
import importlib.util, re, sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).parent
SITE = ROOT / "site"
_sl_spec = importlib.util.spec_from_file_location("sunnah_links", ROOT / "sunnah_links.py")
sl = importlib.util.module_from_spec(_sl_spec); _sl_spec.loader.exec_module(sl)

HADITH_STEMS = ["bukhari", "muslim", "abu-dawud", "tirmidhi"]

def _new_anchor(stem: str) -> str:
    if stem == "quran":
        return ('<a href="https://quran.com" class="btn" target="_blank" '
                'rel="noopener">Read on Quran.com ↗</a>')
    return (f'<a href="{sl.collection_url(stem)}" class="btn" target="_blank" '
            f'rel="noopener">View on sunnah.com ↗</a>')

def swap_button(html: str, stem: str) -> tuple:
    pat = re.compile(r'<a href="\.\./assets/sources/' + re.escape(stem) +
                     r'\.pdf" class="btn" download>Download PDF</a>')
    new_html, n = pat.subn(_new_anchor(stem), html)
    return new_html, n

def main() -> None:
    for stem in HADITH_STEMS + ["quran"]:
        p = SITE / "read" / f"{stem}.html"
        html = p.read_text(encoding="utf-8")
        out, n = swap_button(html, stem)
        if n:
            p.write_text(out, encoding="utf-8")
        print(f"  {stem}: {n} button(s) swapped")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, then the script; verify**

Run: `python -m pytest tests/test_replace_pdf_buttons.py -v` → PASS (3).
Run: `python replace_pdf_buttons.py` → each of the 5 stems reports `1 button(s) swapped`.
Verify no `Download PDF` remains in those 5 readers: `grep -c "Download PDF" site/read/bukhari.html site/read/muslim.html site/read/abu-dawud.html site/read/tirmidhi.html site/read/quran.html` → all 0.

- [ ] **Step 5: Commit**

```bash
git add replace_pdf_buttons.py tests/test_replace_pdf_buttons.py site/read/bukhari.html site/read/muslim.html site/read/abu-dawud.html site/read/tirmidhi.html site/read/quran.html
git commit -m "feat: swap reader Download-PDF button for Go-to-site link"
```

---

### Task 3: Per-hadith sunnah.com links in the 6 hadith readers

**Files:**
- Create: `link_hadith_to_sunnah.py`
- Modify (via the script): `site/read/{bukhari,muslim,abu-dawud,tirmidhi,nasai,ibn-majah}.html`
- Test: `tests/test_link_hadith_to_sunnah.py`

**Interfaces:**
- Produces: `add_links(html: str, stem: str) -> tuple[str,int]` — wraps each `<span class="hadith-ref">Hadith {N} · Book {B}</span>` so the label links to `hadith_url(stem, N)` in a new tab, with a small ` ↗` marker. Returns `(new_html, n_linked)`. Idempotent (skips spans already containing an `<a>`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_link_hadith_to_sunnah.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("lh", Path(__file__).parent.parent / "link_hadith_to_sunnah.py")
lh = importlib.util.module_from_spec(spec); spec.loader.exec_module(lh)

def test_adds_link():
    html = '<span class="hadith-ref">Hadith 224 · Book 4</span>'
    out, n = lh.add_links(html, "bukhari")
    assert n == 1
    assert 'href="https://sunnah.com/bukhari:224"' in out
    assert 'target="_blank"' in out and 'rel="noopener"' in out
    assert "Hadith 224 · Book 4" in out  # label text preserved

def test_idempotent_skips_existing_anchor():
    html = '<span class="hadith-ref"><a href="https://sunnah.com/bukhari:224">Hadith 224 · Book 4</a></span>'
    out, n = lh.add_links(html, "bukhari")
    assert n == 0 and out == html

def test_anchor_id_untouched():
    html = '<article class="hadith" id="h224"><header><span class="hadith-ref">Hadith 224 · Book 4</span></header></article>'
    out, n = lh.add_links(html, "bukhari")
    assert 'id="h224"' in out  # article anchor preserved
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_link_hadith_to_sunnah.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# link_hadith_to_sunnah.py — make each hadith-ref label a link to that hadith
# on sunnah.com (per-hadith "Go to site"). Does not touch article id anchors.
import importlib.util, re, sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).parent
SITE = ROOT / "site"
_sl_spec = importlib.util.spec_from_file_location("sunnah_links", ROOT / "sunnah_links.py")
sl = importlib.util.module_from_spec(_sl_spec); _sl_spec.loader.exec_module(sl)

STEMS = ["bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah"]
# Capture the leading hadith number N from the ref label.
_REF = re.compile(r'<span class="hadith-ref">(Hadith (\d+) · Book \d+)</span>')

def add_links(html: str, stem: str) -> tuple:
    def repl(m):
        label, num = m.group(1), int(m.group(2))
        url = sl.hadith_url(stem, num)
        return (f'<span class="hadith-ref"><a href="{url}" target="_blank" '
                f'rel="noopener">{label} ↗</a></span>')
    return _REF.subn(repl, html)

def main() -> None:
    for stem in STEMS:
        p = SITE / "read" / f"{stem}.html"
        html = p.read_text(encoding="utf-8")
        out, n = add_links(html, stem)
        if n:
            p.write_text(out, encoding="utf-8")
        print(f"  {stem}: {n} hadith links added")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test, then the script; verify anchors intact**

Run: `python -m pytest tests/test_link_hadith_to_sunnah.py -v` → PASS (3).
Before running, record anchor counts: `python -c "import importlib.util as u; s=u.spec_from_file_location('r','read_anchors.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print({k:len(m.read_anchor_set(k)) for k in ['bukhari','muslim','abu-dawud','tirmidhi','nasai','ibn-majah']})"`
Run: `python link_hadith_to_sunnah.py` → prints per-stem counts (bukhari 7277, etc.).
After running, clear the read_anchors cache and re-check the SAME counts are unchanged (links added no new `id=` anchors) — run the same one-liner in a fresh process; the dict must be identical.
Run `python validate_links.py` → still `0 unresolved` (internal citation links unaffected).

- [ ] **Step 5: Commit**

```bash
git add link_hadith_to_sunnah.py tests/test_link_hadith_to_sunnah.py site/read/bukhari.html site/read/muslim.html site/read/abu-dawud.html site/read/tirmidhi.html site/read/nasai.html site/read/ibn-majah.html
git commit -m "feat: per-hadith sunnah.com Go-to-site links in readers"
```

---

### Task 4: Delete orphaned per-volume PDF pages

**Files:**
- Delete: `site/read/nasai-v{1..6}.html`, `site/read/ibn-majah-v{1..5}.html` (11 files)
- Test: `tests/test_no_orphan_volume_pages.py`

**Interfaces:** none.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_no_orphan_volume_pages.py
import re
from pathlib import Path
SITE = Path(__file__).parent.parent / "site"

def test_volume_pages_gone():
    assert not list(SITE.glob("read/nasai-v*.html"))
    assert not list(SITE.glob("read/ibn-majah-v*.html"))

def test_no_references_to_volume_pages():
    pat = re.compile(r'(nasai|ibn-majah)-v[1-6]\.html')
    hits = [p.name for p in SITE.rglob("*.html") if pat.search(p.read_text(encoding="utf-8", errors="ignore"))]
    assert hits == [], f"Still referenced by: {hits}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_no_orphan_volume_pages.py -v`
Expected: FAIL — files still present.

- [ ] **Step 3: Delete the files**

Run:
```bash
git rm site/read/nasai-v1.html site/read/nasai-v2.html site/read/nasai-v3.html site/read/nasai-v4.html site/read/nasai-v5.html site/read/nasai-v6.html site/read/ibn-majah-v1.html site/read/ibn-majah-v2.html site/read/ibn-majah-v3.html site/read/ibn-majah-v4.html site/read/ibn-majah-v5.html
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_no_orphan_volume_pages.py -v`
Expected: PASS (2 tests — files gone, no references).

- [ ] **Step 5: Commit**

```bash
git commit -m "chore: delete orphaned per-volume PDF reader pages"
```

---

### Task 5: Quiz-link confirmation + full-suite gate

**Files:**
- Test: `tests/test_quiz_links_resolve.py`

**Interfaces:** none new (uses `validate_links`).

The goat quiz `source` links are already covered by `validate_links.scan_site` (Plan 1) and currently resolve (validator at 0). This task adds an explicit, named gate so quiz-link health can't silently regress, and confirms the full suite is green.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_quiz_links_resolve.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("vl", Path(__file__).parent.parent / "validate_links.py")
vl = importlib.util.module_from_spec(spec); spec.loader.exec_module(vl)

def test_quiz_source_links_resolve():
    pairs = vl._quiz_source_pairs(vl.SITE)
    assert len(pairs) > 0, "no quiz source links found"
    assert vl.unresolved_links(pairs) == []
```

- [ ] **Step 2: Run test**

Run: `python -m pytest tests/test_quiz_links_resolve.py -v`
Expected: PASS (quiz links already resolve). If it FAILS, list the unresolved quiz links and reconcile (a quiz `source` anchor that no longer exists in the rebuilt read pages) — fix the quiz `source` value to the correct anchor.

- [ ] **Step 3: Full suite + validator**

Run: `python validate_links.py` → `0 unresolved`.
Run: `python -m pytest tests/ -q` → record result. (Note: `tests/test_book_html.py` / `tests/test_book_docx.py` failures are the known legacy-book-builder issue from Plan 2, tracked separately — not introduced here.)

- [ ] **Step 4: Commit**

```bash
git add tests/test_quiz_links_resolve.py
git commit -m "test: explicit gate that goat-quiz source links resolve"
```

---

## Self-Review

**Spec coverage (Plan 3 portion):**
- Remove PDF-download feature → Task 2 (reader buttons) + Task 4 (orphan volume pages). ✓
- "Go to site" → sunnah.com, "specific page of the respective Hadith" → Task 3 (per-hadith links) + Task 2 (per-collection). ✓
- Quran exception (quran.com) → Task 2, flagged. ✓
- Quiz Quran links resolve to new read HTML → Task 5 (already 0; explicit gate). ✓
- Chrome/anchor preservation → Tasks 2–3 verify steps (no `Download PDF` left; anchor counts unchanged; validator 0). ✓

**Placeholder scan:** complete code for every script and test; verification steps are concrete commands with expected output.

**Type consistency:** `swap_button`/`add_links` both return `(html, n)`. `sunnah_links` slugs reused by both Task 2 and Task 3. Read-page stems consistent (`abu-dawud`, `ibn-majah`).

## Notes for the user
- The Qur'an reader's "Go to site" points to quran.com (sunnah.com has no Qur'an); change if you prefer a different target.
- The `site/assets/sources/*.pdf` files are now unreferenced but left on disk — purge them if you want to reclaim space.
