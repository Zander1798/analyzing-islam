# Site Rebuild — Plan 2: Entry Sync (mirror the 1,524 book entries) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regenerate the 7 `site/catalog/*.html` pages, the category pages, and `catalog-entries.json` as an exact mirror of the 1,524 campaign-verified book entries, with every citation emitted through the Plan 1 `ref→anchor` contract and the link validator driven to zero.

**Architecture:** A renderer module (`catalog_render.py`) turns one book entry dict into the site's exact entry-block HTML. A driver (`build-catalog-pages.py`) reads the book `_v2` JSON and, for each source, **replaces only the `#entries-container` contents** of the existing catalog page — preserving all page chrome (head, nav, filters, scripts, hero, footer) byte-for-byte. Citations are linked **validate-before-link**: a ref is hyperlinked only if its anchor exists in the read pages (Plan 1 `read_anchors`), else rendered as plain text — so no broken links are ever emitted. Existing derived-page builders (`build-category-pages.py`, `build-catalog-entries-index.py`) then rebuild category pages and the index from the new catalog HTML.

**Tech Stack:** Python 3 (stdlib only), `pytest`. Reuses Plan 1 modules `refs.py`, `read_anchors.py`, `validate_links.py`.

## Global Constraints

- **Source of truth:** `../Analyzing Islam Books/data/*_v2.json` (`{metadata, entries}`). Volume→file: quran `quran_entries_v2.json` (275); bukhari + muslim share `hadith_entries_v2.json` split by `entry["source"]` (315 Bukhari, 264 Muslim); abu-dawud `abudawud_entries_v2.json` (181); tirmidhi `tirmidhi_entries_v2.json` (226); nasai `nasai_entries_v2.json` (113); ibn-majah `ibnmajah_entries_v2.json` (150). **Total 1,524.**
- **Book entry schema:** `id, title, categories[display names], strength(Basic|Moderate|Strong), verse_refs[list], verse_quote, what_it_says, why_problem, muslim_response|null, why_fails|null, source(hadith only)`. Paragraph breaks are `\n\n`.
- **Final catalog = exactly the 1,524 book entries.** All-new content, all-new slugs; nothing old retained.
- **Entry-block markup (verbatim target):**
  ```html
  <div class="entry" id="{slug}" data-category="{space-joined category slugs}" data-strength="{basic|moderate|strong}">
    <div class="entry-header">
      <span class="entry-title">{title}</span>
      <span class="tag">{Category Display Name}</span>           <!-- one per category -->
      <span class="tag strength-{basic|moderate|strong}">{Basic|Moderate|Strong}</span>
      <span class="ref">{ref links or plain text}</span>
    </div>
    <section>
      <blockquote>{verse_quote}</blockquote>
      <h4>{What the verse says|What the verses say|What the hadith says}</h4>
      <p>{paragraph}</p> ...
      <h4>Why this is a problem</h4>
      <p>...</p> ...
      <h4>The Muslim response</h4>     <!-- only if muslim_response present -->
      <p>...</p> ...
      <h4>Why it fails</h4>             <!-- only if why_fails present -->
      <p>...</p> ...
    </section>
  </div>
  ```
- **Heading wording:** quran source → "What the verse says" (single verse_ref) / "What the verses say" (multiple); all hadith sources → "What the hadith says".
- **Category display→slug map (all 31, verbatim):** `Strange / Obscure→strange`, `Women→women`, `Prophetic Character→prophet`, `Logical Inconsistency→logic`, `Treatment of Disbelievers→disbelievers`, `Science→science`, `Contradictions→contradiction`, `Moral Problems→morality`, `Eschatology→eschatology`, `Governance→governance`, `Warfare & Jihad→warfare`, `Jesus / Christology→jesus`, `Allah's Character→allah`, `Hudud→hudud`, `Ritual Absurdities→ritual`, `Abrogation→abrogation`, `Magic & Occult→magic`, `Antisemitism→antisemitism`, `Sexual Issues→sexual`, `Scripture Integrity→scripture`, `Slavery & Captives→slavery`, `Prophetic Privileges→privileges`, `Pre-Islamic Borrowings→preislamic`, `Hell→hell`, `Paradise→paradise`, `Apostasy & Blasphemy→apostasy`, `LGBTQ / Gender→lgbtq`, `Child Marriage→childmarriage`, `Gross / Vile→gross-vile`, `Incest→incest`, `Animals→animals`.
- **Slug scheme (matches `assign-entry-ids.py`):** `slugify(title)[:60].rstrip('-') + '-' + sha256(f"{source}::{title}").hexdigest()[:8]` where `slugify` lowercases, strips HTML/combining marks, maps `[^a-z0-9]+`→`-`, strips leading/trailing `-`. `source` is the catalog stem (`quran`,`bukhari`,...).
- **Validate-before-link:** a citation is wrapped in `<a class="cite-link" href="../read/{slug}.html#{anchor}">…</a>` ONLY if `anchor in read_anchors.read_anchor_set(slug)`. Otherwise emit the display text unlinked. `RefError` → unlinked. This holds for header refs AND inline body refs.
- **Ref normalization (Plan 1 reconciliation conditions):** before parsing, split a ref string on both `,` and `;`; strip leading prose words (e.g. "contrast ", "see also ", "cf. ") from each part; accept colon-form hadith (`abudawud:2311`→`Abu Dawud 2311`) and no-space Qur'an (`Q4:92`→`Q 4:92`).
- **Verbatim transfer:** HTML-escape text but preserve `\n\n` paragraph splits, en-dashes, ﷺ, transliterations, ellipses. Do not paraphrase. Polemical sources stay as written.
- **Chrome preservation:** never rewrite page `<head>`/nav/filters/scripts/hero/footer — only the `#entries-container` body. (The read-page regression in Plan 1 came from template staleness; do not repeat it.)
- **Encoding:** UTF-8; scripts begin with guarded `sys.stdout.reconfigure(encoding="utf-8")`.
- **Branch:** `site-rebuild-from-books`. One commit per task.

---

### Task 1: Category map + render helpers in `catalog_render.py`

**Files:**
- Create: `catalog_render.py`
- Test: `tests/test_catalog_render.py`

**Interfaces:**
- Produces: `CATEGORY_SLUGS: dict[str,str]` (31 entries, verbatim from Global Constraints).
- Produces: `category_slug(name: str) -> str` — raises `KeyError` on unknown name (fail loud; the taxonomy is closed).
- Produces: `slugify(s: str, max_len: int = 60) -> str` and `entry_slug(title: str, source: str) -> str` (matches `assign-entry-ids.py`).
- Produces: `strength_class(strength: str) -> str` (`"Basic"`→`"basic"`).
- Produces: `esc(s: str) -> str` (`html.escape(s, quote=True)`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_catalog_render.py
import importlib.util, hashlib
from pathlib import Path
import pytest

cr = None
def _load():
    global cr
    spec = importlib.util.spec_from_file_location(
        "catalog_render", Path(__file__).parent.parent / "catalog_render.py")
    cr = importlib.util.module_from_spec(spec); spec.loader.exec_module(cr)
_load()


def test_category_map_has_31():
    assert len(cr.CATEGORY_SLUGS) == 31
    assert cr.category_slug("Strange / Obscure") == "strange"
    assert cr.category_slug("Treatment of Disbelievers") == "disbelievers"
    assert cr.category_slug("Gross / Vile") == "gross-vile"


def test_category_slug_unknown_raises():
    with pytest.raises(KeyError):
        cr.category_slug("Nonexistent Category")


def test_strength_class():
    assert cr.strength_class("Basic") == "basic"
    assert cr.strength_class("Strong") == "strong"


def test_slugify_and_entry_slug_match_legacy_scheme():
    title = 'Paradise as physical pleasure garden with "purified spouses"'
    expected_hash = hashlib.sha256(f"quran::{title}".encode("utf-8")).hexdigest()[:8]
    slug = cr.entry_slug(title, "quran")
    assert slug.endswith("-" + expected_hash)
    assert slug.startswith("paradise-as-physical-pleasure-garden")
    assert len(slug.split("-")[-1]) == 8
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_catalog_render.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
# catalog_render.py — render a book entry dict into the site's catalog
# entry-block HTML. Stdlib only. Citation linking is validate-before-link
# (see render_ref_html / link helpers in later tasks).
import hashlib
import html
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CATEGORY_SLUGS = {
    "Strange / Obscure": "strange", "Women": "women",
    "Prophetic Character": "prophet", "Logical Inconsistency": "logic",
    "Treatment of Disbelievers": "disbelievers", "Science": "science",
    "Contradictions": "contradiction", "Moral Problems": "morality",
    "Eschatology": "eschatology", "Governance": "governance",
    "Warfare & Jihad": "warfare", "Jesus / Christology": "jesus",
    "Allah's Character": "allah", "Hudud": "hudud",
    "Ritual Absurdities": "ritual", "Abrogation": "abrogation",
    "Magic & Occult": "magic", "Antisemitism": "antisemitism",
    "Sexual Issues": "sexual", "Scripture Integrity": "scripture",
    "Slavery & Captives": "slavery", "Prophetic Privileges": "privileges",
    "Pre-Islamic Borrowings": "preislamic", "Hell": "hell",
    "Paradise": "paradise", "Apostasy & Blasphemy": "apostasy",
    "LGBTQ / Gender": "lgbtq", "Child Marriage": "childmarriage",
    "Gross / Vile": "gross-vile", "Incest": "incest", "Animals": "animals",
}


def category_slug(name: str) -> str:
    return CATEGORY_SLUGS[name.strip()]


def strength_class(strength: str) -> str:
    return (strength or "").strip().lower()


def esc(s: str) -> str:
    return html.escape(s, quote=True) if s else ""


def slugify(s: str, max_len: int = 60) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[̀-ͯ]", "", s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:max_len].rstrip("-")


def entry_slug(title: str, source: str) -> str:
    h = hashlib.sha256(f"{source}::{title}".encode("utf-8")).hexdigest()[:8]
    return f"{slugify(title)}-{h}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_catalog_render.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add catalog_render.py tests/test_catalog_render.py
git commit -m "feat: add category map + slug/render helpers (catalog_render.py)"
```

---

### Task 2: Ref normalization + validate-before-link citation rendering

**Files:**
- Modify: `catalog_render.py`
- Test: `tests/test_catalog_render.py`

**Interfaces:**
- Consumes: `refs.ref_to_links`, `refs.primary_anchor`, `refs.RefError` (Plan 1); `read_anchors.read_anchor_set` (Plan 1).
- Produces: `normalize_ref_part(part: str) -> str` — strips leading prose words and rewrites colon-form hadith (`abudawud:2311`→`Abu Dawud 2311`) and no-space Qur'an (`Q4:92`→`Q 4:92`) to canonical form; returns `""` if the part has no parseable ref token.
- Produces: `link_one_ref(ref: str, anchor_sets: dict[str,set]) -> str` — returns `<a class="cite-link" href="../read/{slug}.html#{anchor}">{esc(ref)}</a>` if the primary anchor exists in `anchor_sets[slug]`, else `esc(ref)` (plain). `RefError`/unknown → plain.
- Produces: `render_ref_html(verse_refs: list[str], anchor_sets) -> str` — joins each `verse_refs` element (after splitting on `,`/`;` and normalizing) with `, `, each linked-or-plain; this is the `<span class="ref">` inner HTML.
- `anchor_sets` is `{slug: read_anchor_set(slug)}` passed in for testability (no disk hits in unit tests).

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_catalog_render.py

FAKE = {
    "quran": {"s2v25", "s4v92", "s2v228"},
    "bukhari": {"h224"},
    "abu-dawud": {"h2311"},
}

def test_normalize_ref_part():
    assert cr.normalize_ref_part("contrast Q 21:101") == "Q 21:101"
    assert cr.normalize_ref_part("abudawud:2311") == "Abu Dawud 2311"
    assert cr.normalize_ref_part("Q4:92") == "Q 4:92"
    assert cr.normalize_ref_part("see also Bukhari 224") == "Bukhari 224"

def test_link_one_ref_resolves():
    assert cr.link_one_ref("Q 2:25", FAKE) == (
        '<a class="cite-link" href="../read/quran.html#s2v25">Q 2:25</a>')

def test_link_one_ref_unresolved_is_plain():
    # anchor not present -> plain text, no link
    assert cr.link_one_ref("Q 99:99", FAKE) == "Q 99:99"

def test_link_one_ref_referror_is_plain():
    assert cr.link_one_ref("Musnad Ahmad 12345", FAKE) == "Musnad Ahmad 12345"

def test_render_ref_html_multi_and_semicolon():
    out = cr.render_ref_html(["Q 2:154,3:169–170"], FAKE)
    # s2v154 absent in FAKE -> plain; both parts present, comma-joined
    assert "Q 2:154" in out and "3:169" in out
    out2 = cr.render_ref_html(["Bukhari 224; Bukhari 9999"], FAKE)
    assert '#h224' in out2 and "Bukhari 9999" in out2  # second plain (absent)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_catalog_render.py -v`
Expected: FAIL — new functions undefined.

- [ ] **Step 3: Write minimal implementation**

```python
# append to catalog_render.py
import importlib.util as _ilu
from pathlib import Path as _Path

_refs_spec = _ilu.spec_from_file_location("refs", _Path(__file__).parent / "refs.py")
refs = _ilu.module_from_spec(_refs_spec); _refs_spec.loader.exec_module(refs)

# Leading prose words sometimes prefix a ref inside a multi-ref string.
_PROSE = re.compile(r"(?i)^(?:contrast|see also|see|cf\.?|also|and|vs\.?|compare)\s+")
# Colon-form hadith: "abudawud:2311" -> slug + number. Reuse refs.COLLECTION_SLUGS
# values to recognise the left side.
_SLUG_TO_NAME = {
    "bukhari": "Bukhari", "muslim": "Muslim", "abu-dawud": "Abu Dawud",
    "tirmidhi": "Tirmidhi", "nasai": "Nasa'i", "ibn-majah": "Ibn Majah",
}
# accept the compact json keys too (abudawud, ibnmajah)
_COMPACT = {"abudawud": "Abu Dawud", "ibnmajah": "Ibn Majah"}


def normalize_ref_part(part: str) -> str:
    p = part.strip()
    p = _PROSE.sub("", p).strip()
    if not p:
        return ""
    # no-space Qur'an: Q4:92 -> Q 4:92
    m = re.match(r"(?i)^q(\d+:\d+.*)$", p)
    if m:
        return "Q " + m.group(1)
    # colon-form hadith: abudawud:2311 -> Abu Dawud 2311
    m = re.match(r"^([a-z-]+):(\d+[a-z]?)$", p, re.I)
    if m:
        key = m.group(1).lower()
        name = _SLUG_TO_NAME.get(key) or _COMPACT.get(key)
        if name:
            return f"{name} {m.group(2)}"
    return p


def link_one_ref(ref: str, anchor_sets: dict) -> str:
    try:
        slug, anchor = refs.primary_anchor(ref)
    except refs.RefError:
        return esc(ref)
    if anchor in anchor_sets.get(slug, set()):
        return f'<a class="cite-link" href="../read/{slug}.html#{anchor}">{esc(ref)}</a>'
    return esc(ref)


def render_ref_html(verse_refs: list, anchor_sets: dict) -> str:
    out = []
    for raw in verse_refs:
        for part in re.split(r"[;,]", raw):
            norm = normalize_ref_part(part)
            if norm:
                out.append(link_one_ref(norm, anchor_sets))
    return ", ".join(out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_catalog_render.py -v`
Expected: PASS (9 tests total).

- [ ] **Step 5: Commit**

```bash
git add catalog_render.py tests/test_catalog_render.py
git commit -m "feat: validate-before-link ref rendering + ref normalization"
```

---

### Task 3: Inline body cite-linking (validate-before-link) in `catalog_render.py`

**Files:**
- Modify: `catalog_render.py`
- Test: `tests/test_catalog_render.py`

**Interfaces:**
- Produces: `link_inline(text_html: str, anchor_sets: dict) -> str` — given an already-HTML-escaped paragraph, wrap inline Qur'an (`Q S:V`, `Q S:V–V2`) and hadith (`Bukhari N`, `Abu Dawud N`, …) references in `<a class="cite-link">` IF the anchor exists; leave plain otherwise. Never double-links (input has no existing `<a>`). Display text unchanged.

This reuses the proven patterns from `link_inline_refs.py` (collection alternation, longest-first), but routes every candidate through `link_one_ref`'s existence check so no broken inline link is ever produced. Bible (OT/NT) inline linking is OUT OF SCOPE for this task (handled by the existing `link_inline_refs.py` Bible maps in Task 5's pipeline step if desired); this function covers Qur'an + the six hadith collections only.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_catalog_render.py

def test_link_inline_quran_present_and_absent():
    txt = "As in Q 2:25 and also Q 99:99 the text says."
    out = cr.link_inline(txt, FAKE)
    assert '<a class="cite-link" href="../read/quran.html#s2v25">Q 2:25</a>' in out
    assert "Q 99:99" in out and "#s99v99" not in out  # absent -> plain

def test_link_inline_hadith():
    txt = "Reported in Bukhari 224 clearly."
    out = cr.link_inline(txt, FAKE)
    assert '<a class="cite-link" href="../read/bukhari.html#h224">Bukhari 224</a>' in out

def test_link_inline_no_double_link_and_plain_text_preserved():
    txt = "No refs here at all."
    assert cr.link_inline(txt, FAKE) == txt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_catalog_render.py -v`
Expected: FAIL — `link_inline` undefined.

- [ ] **Step 3: Write minimal implementation**

```python
# append to catalog_render.py

_HADITH_NAMES = sorted(
    ["Bukhari", "Muslim", "Abu Dawud", "Tirmidhi", "Nasa'i", "Nasai", "Ibn Majah"],
    key=len, reverse=True)
_HADITH_ALT = "|".join(re.escape(n) for n in _HADITH_NAMES)
_QURAN_INLINE = re.compile(r"Q (\d+):(\d+)(?:[–\-]\d+)?")
_HADITH_INLINE = re.compile(rf"({_HADITH_ALT}) (\d+[a-z]?)")


def link_inline(text_html: str, anchor_sets: dict) -> str:
    def q(m):
        return link_one_ref(m.group(0), anchor_sets)

    def h(m):
        return link_one_ref(m.group(0), anchor_sets)

    text_html = _QURAN_INLINE.sub(q, text_html)
    text_html = _HADITH_INLINE.sub(h, text_html)
    return text_html
```

Note: `link_one_ref` re-escapes its display text; since inline input is already escaped and ref display text (`Q 2:25`, `Bukhari 224`) contains no HTML-special chars, this is idempotent. Verify in the test that output display text is unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_catalog_render.py -v`
Expected: PASS (12 tests total).

- [ ] **Step 5: Commit**

```bash
git add catalog_render.py tests/test_catalog_render.py
git commit -m "feat: validate-before-link inline body citation linking"
```

---

### Task 4: Full entry-block renderer

**Files:**
- Modify: `catalog_render.py`
- Test: `tests/test_catalog_render.py`

**Interfaces:**
- Produces: `render_paragraphs(text: str, anchor_sets: dict) -> str` — split `text` on `\n\n`, esc each block, inline-link it, wrap in `<p>…</p>`, join with `\n      `.
- Produces: `says_heading(source: str, n_refs: int) -> str` — `"What the hadith says"` for hadith sources; for quran `"What the verse says"` if `n_refs<=1` else `"What the verses say"`.
- Produces: `render_entry(entry: dict, source: str, anchor_sets: dict) -> str` — the full `<div class="entry">…</div>` block per the Global Constraints markup. Omits the Muslim-response `<h4>`+paras when `muslim_response` is null/empty; omits the Why-it-fails block when `why_fails` is null/empty.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_catalog_render.py

ENTRY_Q = {
    "id": 1, "title": 'Paradise as physical pleasure garden',
    "categories": ["Strange / Obscure"], "strength": "Basic",
    "verse_refs": ["Q 2:25"], "verse_quote": "\"... gardens [in Paradise] ...\"",
    "what_it_says": "Paradise is physical. See Q 2:25 again.",
    "why_problem": "First para.\n\nSecond para.",
    "muslim_response": None, "why_fails": None,
}
ENTRY_H = {
    "id": 1, "title": "Muhammad urinated standing up at a dump",
    "categories": ["Prophetic Character", "Strange / Obscure"], "strength": "Basic",
    "verse_refs": ["Bukhari 224"], "verse_quote": "\"Once the Prophet ...\"",
    "what_it_says": "Plain.", "why_problem": "Problem.",
    "muslim_response": "They say X.", "why_fails": "It fails.", "source": "Bukhari",
}

def test_render_entry_quran_structure():
    html_out = cr.render_entry(ENTRY_Q, "quran", FAKE)
    assert 'class="entry"' in html_out
    assert 'data-category="strange"' in html_out
    assert 'data-strength="basic"' in html_out
    assert "<h4>What the verse says</h4>" in html_out
    assert "<h4>Why this is a problem</h4>" in html_out
    assert "The Muslim response" not in html_out   # null -> omitted
    assert "Why it fails" not in html_out           # null -> omitted
    # inline link applied in body, anchor exists in FAKE
    assert '../read/quran.html#s2v25">Q 2:25</a>' in html_out
    # two paragraphs in why_problem
    assert html_out.count("<p>") >= 3

def test_render_entry_hadith_structure_and_multicat():
    html_out = cr.render_entry(ENTRY_H, "bukhari", FAKE)
    assert 'data-category="prophet strange"' in html_out
    assert "<h4>What the hadith says</h4>" in html_out
    assert "<h4>The Muslim response</h4>" in html_out
    assert "<h4>Why it fails</h4>" in html_out
    assert '<span class="tag">Prophetic Character</span>' in html_out
    assert '<span class="tag">Strange / Obscure</span>' in html_out
    assert '<span class="tag strength-basic">Basic</span>' in html_out
    assert '../read/bukhari.html#h224">Bukhari 224</a>' in html_out

def test_render_entry_escapes_quote():
    html_out = cr.render_entry(ENTRY_Q, "quran", FAKE)
    assert "<blockquote>" in html_out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_catalog_render.py -v`
Expected: FAIL — `render_entry` undefined.

- [ ] **Step 3: Write minimal implementation**

```python
# append to catalog_render.py

def render_paragraphs(text: str, anchor_sets: dict) -> str:
    blocks = [b.strip() for b in (text or "").split("\n\n") if b.strip()]
    out = []
    for b in blocks:
        out.append("<p>" + link_inline(esc(b), anchor_sets) + "</p>")
    return "\n      ".join(out)


def says_heading(source: str, n_refs: int) -> str:
    if source == "quran":
        return "What the verses say" if n_refs > 1 else "What the verse says"
    return "What the hadith says"


def render_entry(entry: dict, source: str, anchor_sets: dict) -> str:
    title = entry["title"]
    cats = entry.get("categories") or []
    slugs = [category_slug(c) for c in cats]
    strength = entry.get("strength") or ""
    scls = strength_class(strength)
    eid = entry_slug(title, source)
    refs_list = entry.get("verse_refs") or []
    ref_html = render_ref_html(refs_list, anchor_sets)

    parts = [
        f'<div class="entry" id="{eid}" data-category="{esc(" ".join(slugs))}" data-strength="{scls}">',
        '  <div class="entry-header">',
        f'    <span class="entry-title">{esc(title)}</span>',
    ]
    for c in cats:
        parts.append(f'    <span class="tag">{esc(c)}</span>')
    parts.append(f'    <span class="tag strength-{scls}">{esc(strength)}</span>')
    parts.append(f'    <span class="ref">{ref_html}</span>')
    parts.append('  </div>')
    parts.append('  <section>')
    parts.append(f'    <blockquote>{esc(entry.get("verse_quote") or "")}</blockquote>')
    parts.append(f'    <h4>{says_heading(source, len(refs_list))}</h4>')
    parts.append(f'    {render_paragraphs(entry.get("what_it_says"), anchor_sets)}')
    parts.append('    <h4>Why this is a problem</h4>')
    parts.append(f'    {render_paragraphs(entry.get("why_problem"), anchor_sets)}')
    if (entry.get("muslim_response") or "").strip():
        parts.append('    <h4>The Muslim response</h4>')
        parts.append(f'    {render_paragraphs(entry["muslim_response"], anchor_sets)}')
    if (entry.get("why_fails") or "").strip():
        parts.append('    <h4>Why it fails</h4>')
        parts.append(f'    {render_paragraphs(entry["why_fails"], anchor_sets)}')
    parts.append('  </section>')
    parts.append('</div>')
    return "\n".join(parts)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_catalog_render.py -v`
Expected: PASS (15 tests total).

- [ ] **Step 5: Commit**

```bash
git add catalog_render.py tests/test_catalog_render.py
git commit -m "feat: full entry-block renderer (catalog_render.render_entry)"
```

---

### Task 5: Catalog page driver `build-catalog-pages.py` (chrome-preserving surgery)

**Files:**
- Create: `build-catalog-pages.py`
- Test: `tests/test_build_catalog_pages.py`

**Interfaces:**
- Consumes: `catalog_render.render_entry`, `read_anchors.read_anchor_set`.
- Produces: `load_book_entries() -> dict[str, list]` — `{source: [entry, ...]}` for the 7 catalog sources, reading the book `_v2` files (hadith file split by `entry["source"]`). Book repo path: `Path(__file__).parent.parent / "Analyzing Islam Books" / "data"`.
- Produces: `replace_entries_container(page_html: str, entries_html: str) -> str` — replaces the inner content of `<div id="entries-container"> … </div>` with `entries_html` plus the preserved empty-state div, leaving ALL other page bytes unchanged. Raises if the container markers are not found.
- Produces: `EMPTY_STATE = '<div class="empty" id="empty-state" style="display:none;">No entries match current filters.</div>'`
- `main()` writes all 7 pages and prints per-source counts.

**Counts that MUST result (assert in test):** quran 275, bukhari 315, muslim 264, abu-dawud 181, tirmidhi 226, nasai 113, ibn-majah 150; total 1,524.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_build_catalog_pages.py
import importlib.util
from pathlib import Path

def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent.parent / fname)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

bcp = _load("build_catalog_pages", "build-catalog-pages.py")

EXPECTED = {"quran":275,"bukhari":315,"muslim":264,"abu-dawud":181,
            "tirmidhi":226,"nasai":113,"ibn-majah":150}

def test_book_counts():
    data = bcp.load_book_entries()
    got = {k: len(v) for k, v in data.items()}
    assert got == EXPECTED, got
    assert sum(got.values()) == 1524

def test_replace_entries_container_preserves_chrome():
    page = ('<head><title>x</title></head><nav>NAV</nav>'
            '<div id="entries-container">OLD<div class="empty" id="empty-state" '
            'style="display:none;">No entries match current filters.</div></div>'
            '<footer>F</footer>')
    out = bcp.replace_entries_container(page, '<div class="entry">NEW</div>')
    assert "<nav>NAV</nav>" in out and "<footer>F</footer>" in out
    assert "OLD" not in out
    assert '<div class="entry">NEW</div>' in out
    assert 'id="empty-state"' in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_build_catalog_pages.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# build-catalog-pages.py — regenerate catalog/*.html entries from book _v2 data,
# preserving each page's existing chrome (only #entries-container is replaced).
import importlib.util, json, re, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"
BOOK_DATA = ROOT.parent / "Analyzing Islam Books" / "data"

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

cr = _load("catalog_render", ROOT / "catalog_render.py")
read_anchors = _load("read_anchors", ROOT / "read_anchors.py")

EMPTY_STATE = ('<div class="empty" id="empty-state" style="display:none;">'
               'No entries match current filters.</div>')

# (catalog source stem) -> (book file, optional source-field filter)
SOURCES = [
    ("quran", "quran_entries_v2.json", None),
    ("bukhari", "hadith_entries_v2.json", "Bukhari"),
    ("muslim", "hadith_entries_v2.json", "Muslim"),
    ("abu-dawud", "abudawud_entries_v2.json", None),
    ("tirmidhi", "tirmidhi_entries_v2.json", None),
    ("nasai", "nasai_entries_v2.json", None),
    ("ibn-majah", "ibnmajah_entries_v2.json", None),
]


def load_book_entries() -> dict:
    out = {}
    for stem, fname, filt in SOURCES:
        data = json.loads((BOOK_DATA / fname).read_text(encoding="utf-8"))
        entries = data["entries"]
        if filt:
            entries = [e for e in entries if e.get("source") == filt]
        out[stem] = entries
    return out


def replace_entries_container(page_html: str, entries_html: str) -> str:
    m = re.search(r'(<div id="entries-container">)(.*?)(</div>\s*</main>)',
                  page_html, re.DOTALL)
    if not m:
        raise ValueError("entries-container not found")
    new_inner = "\n\n" + entries_html + "\n\n" + EMPTY_STATE + "\n  "
    return page_html[:m.start()] + m.group(1) + new_inner + m.group(3) + page_html[m.end():]


def build_one(stem: str, entries: list) -> int:
    anchor_sets = {s: read_anchors.read_anchor_set(s)
                   for s in ["quran", "bukhari", "muslim", "abu-dawud",
                             "tirmidhi", "nasai", "ibn-majah"]}
    blocks = [cr.render_entry(e, stem, anchor_sets) for e in entries]
    page = (SITE / "catalog" / f"{stem}.html").read_text(encoding="utf-8")
    page = replace_entries_container(page, "\n\n".join(blocks))
    (SITE / "catalog" / f"{stem}.html").write_text(page, encoding="utf-8")
    return len(blocks)


def main() -> None:
    data = load_book_entries()
    total = 0
    for stem, _, _ in SOURCES:
        n = build_one(stem, data[stem])
        total += n
        print(f"  {stem:12s}: {n} entries")
    print(f"Total: {total}")


if __name__ == "__main__":
    main()
```

**NOTE on `replace_entries_container`:** the regex assumes the container is immediately followed by `</div>\s*</main>`. The implementer MUST verify this against the real `site/catalog/quran.html` (the Explore report shows `#entries-container` holds entries + the empty-state div, then closes before `</main>`). If the real close differs, adjust the regex to match the actual structure — confirm by reading the tail of one catalog page before running `main()`.

- [ ] **Step 4: Run test to verify it passes; then run the build**

Run: `python -m pytest tests/test_build_catalog_pages.py -v`
Expected: PASS (2 tests).

Then run the build and verify counts:
Run: `python build-catalog-pages.py`
Expected: prints `quran: 275 … total: 1524`.

- [ ] **Step 5: Commit**

```bash
git add build-catalog-pages.py tests/test_build_catalog_pages.py site/catalog/
git commit -m "feat: regenerate catalog pages from book data (chrome-preserving)"
```

---

### Task 6: Rebuild category pages + index; reporting map

**Files:**
- Create: `report_entry_sync.py`
- Modify (run): existing `build-category-pages.py`, `build-catalog-entries-index.py`
- Test: `tests/test_entry_sync_report.py`

**Interfaces:**
- Produces: `report_entry_sync.build_report() -> dict` — compares the regenerated `catalog-entries.json` (now 1,524) against a snapshot of the pre-sync index, reporting `{total, by_source, book_only, site_only}` using a content key `(source, normalized title)`. Prints human-readable summary; writes `output not required`.
- Category pages and index are regenerated by the existing scripts; this task wires them and verifies counts.

**IMPORTANT chrome check:** before running `build-category-pages.py`, confirm its `PAGE_TEMPLATE` chrome matches the CURRENT category-page chrome (nav links, script tags). If it is stale (as the read-page builder was), do NOT regenerate chrome from it — instead apply the same `replace_entries_container` surgery used in Task 5 to category pages, updating only entries and the `section-title` count. Decide this by diffing one regenerated category page against its git HEAD version; if only entries/counts change, the template is current and the script is safe.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_entry_sync_report.py
import importlib.util, json
from pathlib import Path

def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent.parent / fname)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_index_has_1524_after_rebuild():
    idx = json.loads((Path(__file__).parent.parent / "site/assets/data/catalog-entries.json").read_text(encoding="utf-8"))
    assert len(idx) == 1524, len(idx)
    from collections import Counter
    by = Counter(e["source"] for e in idx)
    assert by["quran"] == 275 and by["bukhari"] == 315 and by["muslim"] == 264
    assert by["abu-dawud"] == 181 and by["tirmidhi"] == 226
    assert by["nasai"] == 113 and by["ibn-majah"] == 150
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_entry_sync_report.py -v`
Expected: FAIL — index still has 1,541 until the rebuild runs.

- [ ] **Step 3: Snapshot, run the rebuild pipeline, write the report tool**

First snapshot the pre-sync index for the report:
Run: `cp site/assets/data/catalog-entries.json .git/sdd/pre-sync-index.json`

Regenerate category pages (after the chrome check above) and the index:
Run: `python build-category-pages.py`
Run: `python build-catalog-entries-index.py`

Create `report_entry_sync.py`:

```python
# report_entry_sync.py — book<->site reconciliation report (reporting only).
import json, re, sys
from collections import Counter
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).parent
IDX = ROOT / "site/assets/data/catalog-entries.json"
PRE = Path(ROOT / ".git/sdd/pre-sync-index.json")

def _key(e):
    return (e["source"], re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", e["title"])).strip().lower())

def build_report() -> dict:
    cur = json.loads(IDX.read_text(encoding="utf-8"))
    rep = {"total": len(cur), "by_source": dict(Counter(e["source"] for e in cur))}
    if PRE.exists():
        pre = json.loads(PRE.read_text(encoding="utf-8"))
        curk = {_key(e) for e in cur}; prek = {_key(e) for e in pre}
        rep["book_only"] = sorted(curk - prek)
        rep["site_only"] = sorted(prek - curk)
    return rep

def main():
    r = build_report()
    print(f"Total: {r['total']}  by_source: {r['by_source']}")
    print(f"book_only (new): {len(r.get('book_only', []))}")
    print(f"site_only (dropped): {len(r.get('site_only', []))}")
    for k in r.get("site_only", [])[:40]:
        print("  DROPPED:", k)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests + report**

Run: `python -m pytest tests/test_entry_sync_report.py -v`
Expected: PASS (index now 1,524).
Run: `python report_entry_sync.py` — record matched/book-only/site-only in the task report for human eyeballing.

- [ ] **Step 5: Commit**

```bash
git add report_entry_sync.py tests/test_entry_sync_report.py site/category/ site/assets/data/catalog-entries.json
git commit -m "feat: rebuild category pages + index to 1,524; add reconciliation report"
```

---

### Task 7: Drive the link validator to zero + flip baseline to strict

**Files:**
- Modify: `tests/test_validate_links.py` (remove the xfail marker)
- Test: existing `tests/test_validate_links.py`

**Interfaces:** none new.

- [ ] **Step 1: Run the validator on the regenerated site**

Run: `python validate_links.py`
Expected: `All read-page links resolve. ✓` (exit 0). If any remain, they are listed — investigate each: it is either a ref-normalization gap (fix in `catalog_render.normalize_ref_part`/`link_inline`, re-run Task 5–6 build) or a genuinely-absent anchor (record in the plan's reconciliation notes). Do not proceed until zero.

- [ ] **Step 2: Remove the xfail marker (test now must hard-pass)**

Edit `tests/test_validate_links.py`: delete the `@pytest.mark.xfail(...)` decorator on `test_scan_site_baseline_zero_unresolved` so it is a hard gate.

- [ ] **Step 3: Run the full suite**

Run: `python -m pytest tests/ -q`
Expected: all pass, no xfail, no failures.

- [ ] **Step 4: Commit**

```bash
git add tests/test_validate_links.py
git commit -m "test: link validator now hard-passes (0 unresolved after entry sync)"
```

---

## Self-Review

**Spec coverage (Plan 2 portion):**
- Mirror 1,524 entries, all-new content/slugs → Tasks 1,4,5 (renderer + driver, counts asserted). ✓
- Citations via Plan 1 contract, validate-before-link → Tasks 2,3 + Task 7 gate. ✓
- Ref normalization (4 Plan-1 conditions) → Task 2 (`normalize_ref_part`, `,`/`;` split) + Task 3. ✓
- Verbatim transfer, escaping, paragraph breaks → Task 4 (`render_paragraphs`, `esc`). ✓
- Category taxonomy (book display → site slug) → Task 1. ✓
- Chrome preservation (no template regression) → Task 5 surgery + Task 6 chrome check. ✓
- Category pages + index rebuilt to 1,524 → Task 6. ✓
- Reporting map (matched/book-only/site-only) → Task 6 (`report_entry_sync`). ✓
- Validator to 0, flip xfail strict → Task 7. ✓

**Placeholder scan:** complete code for all pure functions; Task 5/6 flag the two real-structure checks (container close regex; category template currency) as explicit verify-steps with how to confirm — not vague TODOs.

**Type consistency:** `anchor_sets: dict[str,set]` is threaded identically through `link_one_ref`, `render_ref_html`, `link_inline`, `render_paragraphs`, `render_entry`, and built once in `build-catalog-pages.build_one`. `entry_slug(title, source)` matches `assign-entry-ids.py`. Source stems are consistent (`abu-dawud`, `ibn-majah`).

## Reconciliation notes
_(Populated during execution if any ref cannot be normalized to a resolvable anchor.)_
