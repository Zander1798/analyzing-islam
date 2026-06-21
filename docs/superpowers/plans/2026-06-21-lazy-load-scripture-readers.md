# Lazy-load Scripture Readers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the monolithic multi-MB scripture readers (`site/read/quran.html`, `site/read/{6 hadith collections}.html`) into small per-surah / per-book standalone pages so clicking any citation lands on the verse near-instantly, while keeping all ~31,812 existing `read/{reader}.html#{anchor}` links working.

**Architecture:** A post-build Python tool (`split_readers.py`) string-splices each already-built, fully-decorated monolithic reader into (a) one small standalone page per surah/book under `read/{slug}/{id}.html`, and (b) a tiny shell at the original `read/{slug}.html` path that redirects `#anchor` links to the owning sub-page (or shows a table-of-contents landing when there's no anchor). The chrome (head, nav, scripts, highlights wiring) is copied verbatim from the monolith with relative URLs deepened one level; per-block text/anchors are extracted with BeautifulSoup to build a search-index JSON and (for hadith) an anchor→book map inlined into the shell. `reader-search.js` and `verse-parser.js` get the new slugs/paths registered so search and casual-reference jumps keep working.

**Tech Stack:** Python 3 + BeautifulSoup4 (`bs4`, already used in this repo) for per-block parsing; plain string operations for chrome splicing; vanilla JS (no framework) for the shell redirector and the existing reader scripts; static hosting on GitHub Pages.

## Global Constraints

- Do **not** change any inbound citation link. The public URL contract `read/{slug}.html#{anchor}` (e.g. `read/quran.html#s23v13`, `read/bukhari.html#h299`) must keep resolving to the cited verse/hadith.
- Verse anchors are `s{surah}v{verse}` on `<li>`; hadith anchors are `h{number}` on `<article>`; hadith numbers are globally unique within a collection.
- Quran surah for an anchor is derivable (`s23v13` → surah `23`); hadith book for an anchor is **not** derivable and must come from a generated map.
- Favicon/manifest links use absolute `/assets/...` (leave untouched). Every other in-chrome relative URL starts with `../` and must become `../../` on sub-pages (which sit one directory deeper).
- Sub-page filenames use the block id number: Quran `read/quran/{surah}.html`; hadith `read/{slug}/{bookId}.html` where `bookId` is the number in `id="book-{bookId}"` (book ids start at 0).
- Search index files must NOT clobber existing `assets/compare-index/*.json`: the Quran main reader uses `assets/compare-index/quran-reader.json` (the existing `quran.json` belongs to the interlinear reader). Hadith use `assets/compare-index/{slug}.json`.
- Reader slug strings MUST match what `site/assets/js/verse-parser.js` `detectReaderSlug()` returns for each reader URL — confirm them, do not assume.
- Deploy = push `site/**` to `main`; GitHub Pages auto-builds. SQL/data files are unaffected.

---

### Task 1: Splitter engine — extract chrome + blocks, emit Quran surah pages

Build the core of `split_readers.py`: load a built reader, split it into the shared chrome and the per-surah blocks, deepen relative URLs and rewrite the TOC for sub-pages, and write one standalone page per surah. Test on `read/quran.html`.

**Files:**
- Create: `split_readers.py`
- Create: `tests/test_split_readers.py`
- Output (generated, git-ignored during dev): `site/read/quran/{1..114}.html`

**Interfaces:**
- Produces:
  - `READERS: list[dict]` — config; each entry has keys `slug, src, outdir, block_open_re (1 capture = block id), toc_href_re (1 capture = block id), toc_link_for(block_id)->str, anchor_re (matches every verse/hadith anchor id in a block)`.
  - `load_reader(cfg) -> tuple[str, str, list[tuple[str,str]], str]` returning `(head_prefix, toc_and_chrome_unused, blocks, tail)` — see implementation; canonical return is `(prefix, blocks, tail)` where `prefix` is everything up to the first block (incl. `<main>` + hero), `blocks` is a list of `(block_id, block_html)`, `tail` is `</main>`…end.
  - `deepen_urls(chrome: str) -> str` — turns `="../X"` into `="../../X"`.
  - `rewrite_toc(prefix: str, cfg, active_id: str) -> str` — turns the TOC's in-page anchors into sub-page links and marks the active one.
  - `pager_html(cfg, ids: list[str], idx: int) -> str` — prev/next nav.
  - `emit_subpages(cfg)` — writes every sub-page.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_split_readers.py
import subprocess, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

def _run_quran():
    # Regenerate just the quran sub-pages before asserting.
    subprocess.run([sys.executable, str(ROOT / "split_readers.py"), "--only", "quran", "--subpages"],
                   cwd=ROOT, check=True)

def test_quran_subpage_exists_and_has_anchor():
    _run_quran()
    p = SITE / "read" / "quran" / "23.html"
    assert p.exists(), "surah 23 page missing"
    html = p.read_text(encoding="utf-8")
    assert 'id="s23v13"' in html, "verse anchor missing on its surah page"
    assert 'id="surah-23"' in html, "surah wrapper missing"

def test_quran_subpage_has_full_chrome_with_deepened_urls():
    p = SITE / "read" / "quran" / "23.html"
    html = p.read_text(encoding="utf-8")
    # CSS/JS deepened one level…
    assert 'href="../../assets/css/style.css"' in html
    assert 'src="../../assets/js/reader-search.js"' in html
    # …favicons stay absolute…
    assert 'href="/assets/icons/favicon-32.png"' in html
    # …nav deepened…
    assert 'href="../../catalog.html"' in html

def test_quran_subpage_toc_links_to_siblings_and_marks_active():
    html = (SITE / "read" / "quran" / "23.html").read_text(encoding="utf-8")
    assert 'href="2.html"' in html          # a sibling TOC link
    assert 'href="#surah-2"' not in html    # no in-page TOC anchors remain
    assert re.search(r'class="[^"]*toc-active[^"]*"[^>]*href="23.html"'
                     r'|href="23.html"[^>]*class="[^"]*toc-active', html), "active TOC item not marked"

def test_quran_subpage_has_prev_next():
    html = (SITE / "read" / "quran" / "23.html").read_text(encoding="utf-8")
    assert 'href="22.html"' in html and 'href="24.html"' in html

def test_quran_first_and_last_pages_pager_bounds():
    first = (SITE / "read" / "quran" / "1.html").read_text(encoding="utf-8")
    last  = (SITE / "read" / "quran" / "114.html").read_text(encoding="utf-8")
    assert 'reader-pager-prev' not in first or 'is-disabled' in first
    assert 'reader-pager-next' not in last  or 'is-disabled' in last

def test_no_verse_lost():
    # every s{n}v{m} anchor in the monolith appears on exactly one sub-page
    mono = (SITE / "read" / "quran.html").read_text(encoding="utf-8")
    mono_ids = set(re.findall(r'id="(s\d+v\d+)"', mono))
    seen = set()
    for n in range(1, 115):
        p = SITE / "read" / "quran" / f"{n}.html"
        seen |= set(re.findall(r'id="(s\d+v\d+)"', p.read_text(encoding="utf-8")))
    assert mono_ids == seen, f"lost/extra anchors: {mono_ids ^ seen}"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_split_readers.py -x -q`
Expected: FAIL — `split_readers.py` does not exist yet (collection/`subprocess` error).

- [ ] **Step 3: Write the splitter engine**

```python
# split_readers.py
"""Split monolithic, already-built scripture readers into per-chapter standalone
pages plus a shell/landing page at the original URL. Run AFTER the normal reader
build + decorators, since it copies the finished chrome verbatim.

Usage:
  python split_readers.py --all                  # everything
  python split_readers.py --only quran --subpages # one reader, sub-pages only
"""
import argparse, html as ihtml, json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup

SITE = Path(__file__).resolve().parent / "site"

READERS = [
    {
        "slug": "quran",
        "title": "The Qurʾān",
        "src": "read/quran.html",
        "outdir": "read/quran",
        "block_open_re": r'<article class="surah" id="surah-(\d+)">',
        "toc_href_re": r'href="#surah-(\d+)"',
        "anchor_re": r'id="(s\d+v\d+)"',
        # anchor -> owning block id (surah number), derivable for quran:
        "anchor_to_block": lambda a: re.match(r"s(\d+)v\d+", a).group(1),
        "ref_for_anchor": lambda a: "{}:{}".format(*re.match(r"s(\d+)v(\d+)", a).groups()),
        "needs_manifest": False,
    },
]

# ---- chrome / block splitting -------------------------------------------------

def load_reader(cfg):
    src = (SITE / cfg["src"]).read_text(encoding="utf-8")
    opens = list(re.finditer(cfg["block_open_re"], src))
    if not opens:
        raise SystemExit(f"no blocks found in {cfg['src']}")
    first = opens[0].start()
    main_close = src.index("</main>", opens[-1].end())
    prefix = src[:first]                 # head, nav, TOC, <main>, hero
    tail = src[main_close:]              # </main> … scripts … </html>
    blocks = []
    for i, m in enumerate(opens):
        end = opens[i + 1].start() if i + 1 < len(opens) else main_close
        blocks.append((m.group(1), src[m.start():end]))
    return prefix, blocks, tail

def deepen_urls(chrome):
    # sub-pages live one directory deeper than the monolith; every relative
    # ref starts with ../ (absolute /assets and https:// are left alone).
    return re.sub(r'(\b(?:href|src)=")\.\./', r'\1../../', chrome)

def split_prefix_chrome_and_toc(prefix, cfg):
    """Return (chrome_before_toc, toc_inner, chrome_after_toc) so we can rewrite
    just the TOC per page. The TOC is the <ol> inside <aside class="reader-toc">."""
    a = prefix.index('<aside class="reader-toc"')
    ol_start = prefix.index("<ol", a)
    ol_end = prefix.index("</ol>", ol_start) + len("</ol>")
    return prefix[:ol_start], prefix[ol_start:ol_end], prefix[ol_end:]

def rewrite_toc(toc_inner, cfg, active_id):
    def repl(m):
        bid = m.group(1)
        cls = ' class="toc-active"' if bid == active_id else ""
        return f'href="{bid}.html"{cls}'
    return re.sub(cfg["toc_href_re"], repl, toc_inner)

def pager_html(cfg, ids, idx):
    prev_id = ids[idx - 1] if idx > 0 else None
    next_id = ids[idx + 1] if idx + 1 < len(ids) else None
    prev = (f'<a class="reader-pager-prev" href="{prev_id}.html">← Previous</a>'
            if prev_id else '<span class="reader-pager-prev is-disabled">← Previous</span>')
    nxt = (f'<a class="reader-pager-next" href="{next_id}.html">Next →</a>'
           if next_id else '<span class="reader-pager-next is-disabled">Next →</span>')
    return f'<nav class="reader-pager">{prev}{nxt}</nav>'

# ---- emit ---------------------------------------------------------------------

def emit_subpages(cfg):
    prefix, blocks, tail = load_reader(cfg)
    ids = [bid for bid, _ in blocks]
    pre_toc, toc_inner, post_toc = split_prefix_chrome_and_toc(prefix, cfg)
    outdir = SITE / cfg["outdir"]
    outdir.mkdir(parents=True, exist_ok=True)
    deep_tail = deepen_urls(tail)
    for idx, (bid, block) in enumerate(blocks):
        toc = rewrite_toc(toc_inner, cfg, bid)
        chrome_prefix = deepen_urls(pre_toc + toc + post_toc)
        pager = pager_html(cfg, ids, idx)
        page = chrome_prefix + pager + block + pager + deep_tail
        (outdir / f"{bid}.html").write_text(page, encoding="utf-8")
    return ids, blocks

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--subpages", action="store_true")
    args = ap.parse_args()
    todo = READERS if (args.all or not args.only) else [c for c in READERS if c["slug"] == args.only]
    for cfg in todo:
        if args.subpages or args.all:
            ids, _ = emit_subpages(cfg)
            print(f"[{cfg['slug']}] wrote {len(ids)} sub-pages")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_split_readers.py -x -q`
Expected: PASS (6 tests). If `test_quran_subpage_toc_links_to_siblings_and_marks_active` fails on the active-class regex, confirm the TOC `<a>` is emitted as `href="23.html" class="toc-active"` and adjust the assertion's two accepted orderings only — not the code.

- [ ] **Step 5: Commit**

```bash
git add split_readers.py tests/test_split_readers.py
git commit -m "feat(readers): split engine + Quran per-surah pages"
```

---

### Task 2: Quran shell + landing page at the original URL

Replace `site/read/quran.html` with a small shell: an inline `<head>` script that, when a verse anchor is present, `location.replace`s to the owning surah sub-page; when absent, the page renders a surah table-of-contents landing. Reuses the monolith's chrome.

**Files:**
- Modify: `split_readers.py` (add `emit_shell(cfg)` + wire into `main`)
- Modify: `tests/test_split_readers.py` (add shell tests)
- Output: overwrites `site/read/quran.html`

**Interfaces:**
- Consumes: `load_reader`, `deepen_urls`, `split_prefix_chrome_and_toc` from Task 1.
- Produces: `emit_shell(cfg) -> None`; `redirect_script(cfg) -> str`; `landing_body(cfg, blocks) -> str`.

- [ ] **Step 1: Write the failing test**

```python
def test_quran_shell_redirects_and_lands():
    import subprocess, sys
    subprocess.run([sys.executable, str(ROOT / "split_readers.py"), "--only", "quran", "--shell"],
                   cwd=ROOT, check=True)
    html = (SITE / "read" / "quran.html").read_text(encoding="utf-8")
    # redirect logic present and runs before body (in <head>)
    head = html[:html.index("</head>")]
    assert "location.replace" in head
    assert "s(\\d+)v\\d+" in head or "s(\\\\d+)v" in head or 'match(/s(\\d+)v' in head
    # landing TOC lists surahs as sub-page links
    assert 'href="2.html"' in html
    # still no monolithic verse content
    assert 'id="s2v1"' not in html
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_split_readers.py::test_quran_shell_redirects_and_lands -x -q`
Expected: FAIL — `--shell` not implemented; `location.replace` absent.

- [ ] **Step 3: Implement the shell emitter**

```python
def redirect_script(cfg):
    # Quran: surah is derivable from the anchor, no map needed.
    return (
        "<script>(function(){"
        "var h=location.hash.slice(1);"
        "if(!h)return;"
        "var m=h.match(/^s(\\d+)v\\d+/);"
        "if(m){location.replace(m[1]+'.html#'+h);}"
        "})();</script>"
    )

def landing_body(cfg, blocks):
    items = []
    soup_names = {}
    for bid, block in blocks:
        # pull the surah/book display name from its header if present
        msoup = BeautifulSoup(block, "html.parser")
        name_el = msoup.select_one(".surah-header, .hadith-book-header, h2, .toc-name")
        name = name_el.get_text(" ", strip=True) if name_el else bid
        items.append(f'<li><a href="{bid}.html"><span class="toc-num">{bid}</span> '
                     f'<span class="toc-name">{ihtml.escape(name)}</span></a></li>')
    return ('<div class="reader-landing"><h2>Contents</h2><ol class="reader-landing-list">'
            + "".join(items) + "</ol></div>")

def emit_shell(cfg):
    prefix, blocks, tail = load_reader(cfg)
    pre_toc, toc_inner, post_toc = split_prefix_chrome_and_toc(prefix, cfg)
    # landing keeps the monolith's own depth (read/quran.html), so DON'T deepen.
    # TOC anchors -> sub-page links (no active item on the landing).
    toc = re.sub(cfg["toc_href_re"], lambda m: f'href="{m.group(1)}.html"', toc_inner)
    chrome_prefix = pre_toc + toc + post_toc
    # inject the redirect script just before </head>
    chrome_prefix = chrome_prefix.replace("</head>", redirect_script(cfg) + "</head>", 1)
    body = landing_body(cfg, blocks)
    page = chrome_prefix + body + tail
    (SITE / cfg["src"]).write_text(page, encoding="utf-8")
    print(f"[{cfg['slug']}] wrote shell {cfg['src']}")
```

Add to `main()` arg parsing and dispatch:

```python
    ap.add_argument("--shell", action="store_true")
    ...
    for cfg in todo:
        if args.subpages or args.all:
            ids, _ = emit_subpages(cfg)
            print(f"[{cfg['slug']}] wrote {len(ids)} sub-pages")
        if args.shell or args.all:
            emit_shell(cfg)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_split_readers.py -x -q`
Expected: PASS. Note: `emit_shell` overwrites the monolith, so run sub-page tests and shell tests in the same session is fine because sub-page tests regenerate sub-pages from the (now shell) `read/quran.html`? **No** — sub-pages must be generated from the monolith. See Step 5.

- [ ] **Step 5: Guard against reading an already-shelled monolith**

Because `emit_shell` overwrites `read/quran.html`, `emit_subpages` must run from a pristine monolith. Add a one-time backup so re-runs are safe:

```python
def source_html_path(cfg):
    """Use a pristine .orig backup of the monolith as the split source so the
    splitter is idempotent even after the shell has overwritten read/{slug}.html."""
    live = SITE / cfg["src"]
    orig = live.with_suffix(".orig.html")
    if not orig.exists():
        orig.write_text(live.read_text(encoding="utf-8"), encoding="utf-8")
    return orig

# in load_reader, replace the first line:
#   src = (SITE / cfg["src"]).read_text(encoding="utf-8")
# with:
#   src = source_html_path(cfg).read_text(encoding="utf-8")
```

Add `.orig.html` to `.gitignore` (these are large, regenerable backups):

```bash
echo "site/read/*.orig.html" >> .gitignore
```

Re-run: `python -m pytest tests/test_split_readers.py -x -q`
Expected: PASS (all tests), and re-running the whole suite twice still passes (idempotent).

- [ ] **Step 6: Commit**

```bash
git add split_readers.py tests/test_split_readers.py .gitignore
git commit -m "feat(readers): Quran shell redirect + landing, idempotent source backup"
```

---

### Task 3: Search index for the Quran reader + JS slug wiring

Generate `assets/compare-index/quran-reader.json` from the split blocks, and register the `quran` slug (and the new sub-page paths) in `reader-search.js` / `verse-parser.js` so search and casual-ref jumps work on the landing and sub-pages.

**Files:**
- Modify: `split_readers.py` (add `emit_index(cfg)`)
- Modify: `site/assets/js/reader-search.js` (add to `INDEXED_SOURCES` + landing detection)
- Modify: `site/assets/js/verse-parser.js` (`detectReaderSlug` recognises `read/quran/{n}.html`)
- Modify: `tests/test_split_readers.py`
- Output: `site/assets/compare-index/quran-reader.json`

**Interfaces:**
- Consumes: `load_reader`, `READERS[*].anchor_re`, `anchor_to_block`, `ref_for_anchor`.
- Produces: index JSON shape `{ "entries": [ { "ref": str, "text": str, "href": "{blockId}.html#{anchor}" }, ... ] }`.

- [ ] **Step 0: Confirm the exact slug strings**

Run: `grep -nE "detectReaderSlug|return \"(quran|bukhari|muslim|nasai|tirmidhi|abudawud|abu-dawud|ibnmajah|ibn-majah)\"" site/assets/js/verse-parser.js`
Record the precise slug each reader URL resolves to (e.g. is it `abudawud` or `abu-dawud`?). Use those strings as the `slug` in `READERS`, the `INDEXED_SOURCES` keys, and the index filenames in later tasks. If `detectReaderSlug` keys on the filename `quran.html`, it already returns `quran` for `read/quran/23.html` only if it inspects the path segment — verify and, if not, extend it in Step 3b.

- [ ] **Step 1: Write the failing test**

```python
def test_quran_search_index_built():
    import subprocess, sys, json
    subprocess.run([sys.executable, str(ROOT / "split_readers.py"), "--only", "quran", "--index"],
                   cwd=ROOT, check=True)
    idx = json.loads((SITE / "assets" / "compare-index" / "quran-reader.json").read_text(encoding="utf-8"))
    entries = idx["entries"]
    by_href = {e["href"]: e for e in entries}
    assert "23.html#s23v13" in by_href
    e = by_href["23.html#s23v13"]
    assert e["ref"] == "23:13"
    assert len(e["text"]) > 0
    # one entry per verse, none lost
    mono = (SITE / "read" / "quran.orig.html").read_text(encoding="utf-8")
    import re as _re
    assert len(entries) == len(set(_re.findall(r'id="(s\d+v\d+)"', mono)))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_split_readers.py::test_quran_search_index_built -x -q`
Expected: FAIL — `--index` not implemented.

- [ ] **Step 3a: Implement `emit_index`**

First add the anchor-pattern helper (also reused by the hadith map in Task 5):

```python
def _anchor_pattern(cfg):
    # cfg["anchor_re"] is like r'id="(s\d+v\d+)"' -> inner group is the id shape
    return re.compile("^" + re.search(r"\((.*)\)", cfg["anchor_re"]).group(1) + "$")

def _index_path(cfg):
    # Quran main reader avoids clobbering the interlinear's quran.json.
    name = "quran-reader.json" if cfg["slug"] == "quran" else f"{cfg['slug']}.json"
    return SITE / "assets" / "compare-index" / name
```

Then the emitter:

```python
def emit_index(cfg):
    _, blocks, _ = load_reader(cfg)
    anchor_id_re = _anchor_pattern(cfg)
    entries = []
    for bid, block in blocks:
        soup = BeautifulSoup(block, "html.parser")
        for el in soup.find_all(id=anchor_id_re):
            anchor = el["id"]
            text = re.sub(r"\s+", " ", el.get_text(" ", strip=True))[:600]
            entries.append({
                "ref": cfg["ref_for_anchor"](anchor),
                "text": text,
                "href": f"{bid}.html#{anchor}",
            })
    out = _index_path(cfg)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    print(f"[{cfg['slug']}] wrote index {out.name} ({len(entries)} entries)")
```

Wire `--index` into `main()`:

```python
    ap.add_argument("--index", action="store_true")
    ...
        if args.index or args.all:
            emit_index(cfg)
```

- [ ] **Step 3b: Register the slug in `reader-search.js`**

In `site/assets/js/reader-search.js`, add to `INDEXED_SOURCES` (after the `talmud` entry):

```javascript
    "quran": {
      indexPath: "assets/compare-index/quran-reader.json",
      contentBase: "read/quran/",
    },
```

Extend `isIndexLandingPage(slug)` so the Quran reader landing routes through the index — add before the final `return false;`:

```javascript
    if (slug === "quran") return /\/read\/quran\.html$/.test(path);
```

(Reasoning: on `read/quran.html` with no anchor the page is the TOC landing — no verse anchors in the DOM — so search must use the index. On a sub-page like `read/quran/23.html`, `onIndexPage` is false, so the parser first tries the in-page anchors, then falls through to the index for cross-surah queries — both work because the slug is now in `INDEXED_SOURCES`.)

- [ ] **Step 3c: Make `detectReaderSlug` recognise sub-page paths**

Only if Step 0 showed `detectReaderSlug` does NOT already return `quran` for `read/quran/23.html`: in `site/assets/js/verse-parser.js`, in `detectReaderSlug`, add a path-segment check so `/read/quran/<n>.html` → `quran` (mirror the existing `read-external/quran/surah-NNN.html` → `quran-interlinear` rule, but pointing at the main slug). Exact edit depends on the function's current shape recorded in Step 0; keep it a single added branch.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_split_readers.py -x -q`
Expected: PASS. Then JS sanity: `node --check site/assets/js/reader-search.js && node --check site/assets/js/verse-parser.js`
Expected: no output / exit 0.

- [ ] **Step 5: Commit**

```bash
git add split_readers.py tests/test_split_readers.py site/assets/js/reader-search.js site/assets/js/verse-parser.js
git commit -m "feat(readers): Quran search index + slug routing for split pages"
```

---

### Task 4: Manual browser verification of the Quran reader

Prove the whole Quran flow works in a real browser before generalising to the 16 MB hadith files.

**Files:** none (verification only). Uses a local static server.

- [ ] **Step 1: Generate the full Quran reader**

Run: `python split_readers.py --only quran --all`
Expected: `wrote 114 sub-pages`, `wrote shell read/quran.html`, `wrote index quran-reader.json`.

- [ ] **Step 2: Serve the site locally**

Run: `python -m http.server 8765 --directory site`
Then open these URLs in a browser (use the `run`/`verify` skill or a manual browser):

- [ ] **Step 3: Verify each behaviour**

1. `http://localhost:8765/read/quran.html#s23v13` → redirects to `…/read/quran/23.html#s23v13` and the page is scrolled to verse 23:13 (highlighted by snap). Should feel instant.
2. `http://localhost:8765/read/quran.html#s114v1` (last surah) and `#s2v255` (deep verse) → both land correctly.
3. `http://localhost:8765/read/quran.html` (no hash) → shows the surah Contents landing; clicking a surah opens its page.
4. On `read/quran/23.html`, the search box: type `2:255` → jumps/navigates to surah 2:255; type a keyword present elsewhere → shows index results that navigate to the right surah page.
5. Prev/next: from surah 23, Next → 24, Previous → 22; surah 1 has Previous disabled, surah 114 has Next disabled.
6. TOC sidebar shows surah 23 marked active and links open sibling pages.
7. (Highlights) Sign in, select text in a verse, reload the sub-page → the highlight restores.
8. Check the browser console for errors (especially 404s on assets — confirms URL deepening is correct).

- [ ] **Step 4: Record results**

If any check fails, fix the relevant Task 1–3 code and re-run. Do not proceed to hadith until all 8 checks pass. No commit (verification only) unless a fix was made.

---

### Task 5: Generalise the splitter to the six hadith readers (+ anchor map)

Add the hadith readers to `READERS`. Hadith books are not derivable from the anchor, so the shell must carry an inline `anchor → bookId` map and the build emits a manifest for reference.

**Files:**
- Modify: `split_readers.py` (extend `READERS`; manifest + map-aware shell)
- Modify: `tests/test_split_readers.py`
- Output: `site/read/{slug}/{bookId}.html`, shells, `assets/compare-index/{slug}.json`, `site/read/{slug}/anchors.json`

**Interfaces:**
- Produces: per-collection `anchor_map: dict[str,str]` (`"h299"` → `"3"`); `emit_manifest(cfg)`; map-aware `redirect_script(cfg)`.

- [ ] **Step 1: Confirm hadith slugs + book id range**

Run: `grep -noE 'id="book-[0-9]+"' site/read/bukhari.html | head -3; grep -noE 'id="book-[0-9]+"' site/read/bukhari.html | tail -1`
Record min/max book id (ids start at 0). Use the slug strings confirmed in Task 3 Step 0.

- [ ] **Step 2: Write the failing test**

```python
def test_bukhari_subpage_and_map():
    import subprocess, sys, json, re
    subprocess.run([sys.executable, str(ROOT / "split_readers.py"), "--only", "bukhari", "--all"],
                   cwd=ROOT, check=True)
    # the page that owns #h299
    amap = json.loads((SITE / "read" / "bukhari" / "anchors.json").read_text(encoding="utf-8"))
    assert "h299" in amap
    book = amap["h299"]
    page = SITE / "read" / "bukhari" / f"{book}.html"
    assert page.exists()
    assert 'id="h299"' in page.read_text(encoding="utf-8")
    # shell carries the inline map + redirect
    shell = (SITE / "read" / "bukhari.html").read_text(encoding="utf-8")
    head = shell[:shell.index("</head>")]
    assert "location.replace" in head
    assert '"h299"' in head and f'"{book}"' in head  # inline map present
    # index built under the hadith slug name (not -reader)
    idx = json.loads((SITE / "assets" / "compare-index" / "bukhari.json").read_text(encoding="utf-8"))
    assert any(e["href"] == f"{book}.html#h299" for e in idx["entries"])

def test_bukhari_no_hadith_lost():
    import re
    mono = (SITE / "read" / "bukhari.orig.html").read_text(encoding="utf-8")
    mono_ids = set(re.findall(r'id="(h\d+)"', mono))
    amap = __import__("json").loads((SITE / "read" / "bukhari" / "anchors.json").read_text(encoding="utf-8"))
    assert set(amap.keys()) == mono_ids
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python -m pytest tests/test_split_readers.py::test_bukhari_subpage_and_map -x -q`
Expected: FAIL — bukhari not in `READERS`; no manifest/map.

- [ ] **Step 4: Extend `READERS` with the six hadith collections**

```python
# Append to READERS. Use the slug strings confirmed earlier; this example
# assumes detectReaderSlug returns "bukhari","muslim","nasai","tirmidhi",
# "abudawud","ibnmajah". Adjust if Step 0/1 showed different strings.
_HADITH_NAMES = {
    "bukhari": "Ṣaḥīḥ al-Bukhārī", "muslim": "Ṣaḥīḥ Muslim",
    "nasai": "Sunan an-Nasāʾī", "tirmidhi": "Jāmiʿ at-Tirmidhī",
    "abudawud": "Sunan Abī Dāwūd", "ibnmajah": "Sunan Ibn Mājah",
}
for _slug, _name in _HADITH_NAMES.items():
    READERS.append({
        "slug": _slug,
        "title": _name,
        "src": f"read/{_slug}.html",
        "outdir": f"read/{_slug}",
        "block_open_re": r'<section class="hadith-book" id="book-(\d+)">',
        "toc_href_re": r'href="#book-(\d+)"',
        "anchor_re": r'id="(h\d+)"',
        "anchor_to_block": None,            # not derivable -> use the built map
        "ref_for_anchor": (lambda nm: (lambda a: f"{nm} {a[1:]}"))(_name),
        "needs_manifest": True,
    })
```

- [ ] **Step 5: Build the anchor map and make the shell map-aware**

```python
def build_anchor_map(cfg):
    _, blocks, _ = load_reader_blocks_only(cfg)  # see helper below
    amap = {}
    pat = _anchor_pattern(cfg)
    for bid, block in blocks:
        for aid in re.findall(r'id="(' + pat.pattern.strip("^$") + r')"', block):
            amap[aid] = bid
    return amap

def load_reader_blocks_only(cfg):
    return load_reader(cfg)  # alias for readability

def emit_manifest(cfg):
    if not cfg["needs_manifest"]:
        return None
    amap = build_anchor_map(cfg)
    out = SITE / cfg["outdir"] / "anchors.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(amap, ensure_ascii=False), encoding="utf-8")
    print(f"[{cfg['slug']}] wrote manifest anchors.json ({len(amap)} anchors)")
    return amap
```

Update `redirect_script` to inline the map for map-based readers:

```python
def redirect_script(cfg, amap=None):
    if cfg["needs_manifest"]:
        m = json.dumps(amap, ensure_ascii=False)
        return (
            "<script>(function(){"
            "var M=" + m + ";"
            "var h=location.hash.slice(1);"
            "if(!h)return;"
            "var b=M[h];"
            "if(b!==undefined){location.replace(b+'.html#'+h);}"
            "})();</script>"
        )
    return (
        "<script>(function(){"
        "var h=location.hash.slice(1);"
        "if(!h)return;"
        "var m=h.match(/^s(\\d+)v\\d+/);"
        "if(m){location.replace(m[1]+'.html#'+h);}"
        "})();</script>"
    )
```

Thread the map through `emit_shell`:

```python
def emit_shell(cfg):
    prefix, blocks, tail = load_reader(cfg)
    pre_toc, toc_inner, post_toc = split_prefix_chrome_and_toc(prefix, cfg)
    toc = re.sub(cfg["toc_href_re"], lambda m: f'href="{m.group(1)}.html"', toc_inner)
    chrome_prefix = pre_toc + toc + post_toc
    amap = emit_manifest(cfg) if cfg["needs_manifest"] else None
    chrome_prefix = chrome_prefix.replace("</head>", redirect_script(cfg, amap) + "</head>", 1)
    body = landing_body(cfg, blocks)
    (SITE / cfg["src"]).write_text(chrome_prefix + body + tail, encoding="utf-8")
    print(f"[{cfg['slug']}] wrote shell {cfg['src']}")
```

`emit_index`/`_index_path` already names hadith files `{slug}.json` and the Quran file `quran-reader.json`. No change needed there.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest tests/test_split_readers.py -x -q`
Expected: PASS, including `test_bukhari_subpage_and_map` and `test_bukhari_no_hadith_lost`.

Performance note: `read/bukhari.html` is 16 MB; `load_reader` is pure string ops (fast). Per-block BeautifulSoup parsing in `emit_index` runs on small book blocks, so memory stays bounded. If `emit_index` is slow, that's acceptable for a build step.

- [ ] **Step 7: Commit**

```bash
git add split_readers.py tests/test_split_readers.py
git commit -m "feat(readers): split six hadith collections with inline anchor map + manifest"
```

---

### Task 6: Register hadith slugs in search + verify one hadith reader in the browser

**Files:**
- Modify: `site/assets/js/reader-search.js`
- (maybe) Modify: `site/assets/js/verse-parser.js`

- [ ] **Step 1: Add the six hadith slugs to `INDEXED_SOURCES`**

In `reader-search.js`, add (using the confirmed slug strings):

```javascript
    "bukhari":  { indexPath: "assets/compare-index/bukhari.json",  contentBase: "read/bukhari/" },
    "muslim":   { indexPath: "assets/compare-index/muslim.json",   contentBase: "read/muslim/" },
    "nasai":    { indexPath: "assets/compare-index/nasai.json",    contentBase: "read/nasai/" },
    "tirmidhi": { indexPath: "assets/compare-index/tirmidhi.json", contentBase: "read/tirmidhi/" },
    "abudawud": { indexPath: "assets/compare-index/abudawud.json", contentBase: "read/abudawud/" },
    "ibnmajah": { indexPath: "assets/compare-index/ibnmajah.json", contentBase: "read/ibnmajah/" },
```

Extend `isIndexLandingPage` with one branch per collection landing:

```javascript
    if (["bukhari","muslim","nasai","tirmidhi","abudawud","ibnmajah"].indexOf(slug) >= 0)
      return new RegExp("/read/" + slug + "\\.html$").test(path);
```

- [ ] **Step 2: Confirm sub-page slug detection**

If Task 3 Step 3c was needed for Quran, apply the analogous `detectReaderSlug` branch so `read/bukhari/3.html` resolves to `bukhari` (path-segment based, covering all hadith slugs at once).

- [ ] **Step 3: JS sanity + browser check**

Run: `node --check site/assets/js/reader-search.js && node --check site/assets/js/verse-parser.js`
Then with the local server running, verify in a browser:
1. `…/read/bukhari.html#h299` → redirects to the owning book page, scrolled to hadith 299.
2. `…/read/bukhari.html#h7000` (a high number) and `#h1` (if present) → land correctly.
3. `…/read/bukhari.html` (no hash) → book Contents landing.
4. Search `2749` and `Bukhari 2749` → navigates to the right book page#h2749.
5. Prev/next + TOC active state.
6. Console clean (no asset 404s).

- [ ] **Step 4: Commit**

```bash
git add site/assets/js/reader-search.js site/assets/js/verse-parser.js
git commit -m "feat(readers): register hadith collections in reader search index"
```

---

### Task 7: Orchestration, full regeneration, and pipeline wiring

Make one command rebuild every split reader, and document where it sits relative to the existing reader builders.

**Files:**
- Modify: `split_readers.py` (ensure `--all` covers all 7 readers and all phases)
- Create: `build-split-readers.sh` (or a `Makefile` target) — thin orchestrator
- Modify: `README.md` or the reader build docs — note the new post-build step

- [ ] **Step 1: Full regen**

Run: `python split_readers.py --all`
Expected: for all 7 readers — sub-pages, shells, indexes, and (hadith) manifests written, with printed counts. No exceptions.

- [ ] **Step 2: Invariant sweep across all readers**

Add a final test that loops all readers and asserts no anchors are lost:

```python
def test_all_readers_no_anchor_lost():
    import re, json, subprocess, sys
    subprocess.run([sys.executable, str(ROOT / "split_readers.py"), "--all"], cwd=ROOT, check=True)
    cases = [
        ("quran", r'id="(s\d+v\d+)"', None),
        ("bukhari", r'id="(h\d+)"', "bukhari/anchors.json"),
        ("muslim",  r'id="(h\d+)"', "muslim/anchors.json"),
        ("nasai",   r'id="(h\d+)"', "nasai/anchors.json"),
        ("tirmidhi",r'id="(h\d+)"', "tirmidhi/anchors.json"),
        ("abudawud",r'id="(h\d+)"', "abudawud/anchors.json"),
        ("ibnmajah",r'id="(h\d+)"', "ibnmajah/anchors.json"),
    ]
    for slug, idre, manifest in cases:
        mono = (SITE / "read" / f"{slug}.orig.html").read_text(encoding="utf-8")
        mono_ids = set(re.findall(idre, mono))
        if manifest:
            amap = json.loads((SITE / "read" / manifest).read_text(encoding="utf-8"))
            seen = set(amap.keys())
        else:
            seen = set()
            for n in range(1, 115):
                p = SITE / "read" / "quran" / f"{n}.html"
                if p.exists():
                    seen |= set(re.findall(idre, p.read_text(encoding="utf-8")))
        assert mono_ids == seen, f"{slug}: lost/extra {len(mono_ids ^ seen)} anchors"
```

Run: `python -m pytest tests/test_split_readers.py -q`
Expected: PASS (all tests).

- [ ] **Step 3: Orchestrator script**

```bash
# build-split-readers.sh
#!/usr/bin/env bash
set -euo pipefail
# Run AFTER build-quran-reader.py / build-hadith-readers.py and the post-build
# decorators have produced the monolithic read/*.html files.
python split_readers.py --all
echo "Split readers regenerated. Sub-pages, shells, indexes, manifests updated."
```

Run: `chmod +x build-split-readers.sh && ./build-split-readers.sh`
Expected: same successful output as Step 1.

- [ ] **Step 4: Document the pipeline order**

Append to the reader build docs (or `README.md`) the order: `build-quran-reader.py` / `build-hadith-readers.py` → post-build decorators → **`./build-split-readers.sh`**. Note that `read/*.orig.html` are pristine backups (git-ignored) and the committed `read/*.html` are now shells.

- [ ] **Step 5: Commit**

```bash
git add split_readers.py build-split-readers.sh tests/test_split_readers.py README.md
git commit -m "feat(readers): one-command split-reader regeneration + pipeline docs"
```

---

### Task 8: Final verification against real inbound links, then deploy

Prove that real citations from the catalog/dossiers resolve, then ship.

**Files:** none (verification + git add of generated `site/read/**`).

- [ ] **Step 1: Sample real inbound links and verify each resolves**

```bash
# Pull 20 real reader links actually used on the site and print them.
grep -rhoE 'read/(quran|bukhari|muslim|nasai|tirmidhi|abudawud|ibnmajah)\.html#[a-z0-9]+' site --include=*.html | sort -u | shuf | head -20
```

With the local server running, open ~10 of these (mix of Quran + several hadith collections, including deep/late anchors) and confirm each redirects to the right sub-page and scrolls to the cited verse/hadith. The earlier slug-string assumptions are validated here — if a hadith link 404s on its sub-page, the slug/book mapping is wrong; fix `READERS` and re-run `python split_readers.py --all`.

- [ ] **Step 2: Confirm file-size win**

```bash
ls -lh site/read/*.html                 # shells should be small now
ls -lh site/read/quran/23.html site/read/bukhari/$(python -c "import json;print(json.load(open('site/read/bukhari/anchors.json'))['h299'])").html
```
Expected: shells are KB-to-low-MB (hadith shells carry the inline map), individual sub-pages tens-to-hundreds of KB.

- [ ] **Step 3: Stage the generated tree**

```bash
git add site/read/ site/assets/compare-index/
git status --short | head        # sanity: many new sub-pages, modified shells, new indexes
```

- [ ] **Step 4: Commit and deploy**

```bash
git commit -m "feat(readers): ship split scripture readers (instant citation navigation)"
git push origin main
```

- [ ] **Step 5: Verify the live deploy**

```bash
gh run watch "$(gh run list --workflow=pages.yml --limit 1 --json databaseId -q '.[0].databaseId')" --exit-status
```
Then hard-refresh `https://analyzingislam.com/read/quran.html#s23v13` and one hadith link on the live site (desktop + phone) and confirm instant landing. Note: mobile caches aggressively — hard-refresh or use a private tab.

---

## Notes for the implementer

- **Idempotency depends on the `.orig.html` backups.** The very first run on a pristine checkout captures the monoliths as `read/*.orig.html`; every later run splits from those. If you ever re-run the upstream reader builders, they overwrite `read/*.html` with fresh monoliths — delete the matching `.orig.html` so the next split re-captures them.
- **Do not hand-edit sub-pages**; they are generated. All fixes go in `split_readers.py` then re-run.
- **Slug strings are the main risk.** Task 3 Step 0 and Task 5 Step 1 exist specifically to pin them down before they propagate into filenames, `INDEXED_SOURCES` keys, and index names. Treat a hadith sub-page 404 as a slug/id mismatch, not a logic bug.
- **Highlights** need no code change: each anchor is present in its sub-page's DOM at load, which is exactly what `highlights.js` requires.
