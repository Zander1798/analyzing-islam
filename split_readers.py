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

def source_html_path(cfg):
    """Use a pristine .orig backup of the monolith as the split source so the
    splitter is idempotent even after the shell has overwritten read/{slug}.html."""
    live = SITE / cfg["src"]
    orig = live.with_suffix(".orig.html")
    if not orig.exists():
        orig.write_text(live.read_text(encoding="utf-8"), encoding="utf-8")
    return orig

def load_reader(cfg):
    src = source_html_path(cfg).read_text(encoding="utf-8")
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

# ---- shell / landing ----------------------------------------------------------

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

def _anchor_pattern(cfg):
    # cfg["anchor_re"] is like r'id="(s\d+v\d+)"' -> inner group is the id shape
    return re.compile("^" + re.search(r"\((.*)\)", cfg["anchor_re"]).group(1) + "$")

def _index_path(cfg):
    # Quran main reader avoids clobbering the interlinear's quran.json.
    name = "quran-reader.json" if cfg["slug"] == "quran" else f"{cfg['slug']}.json"
    return SITE / "assets" / "compare-index" / name

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--subpages", action="store_true")
    ap.add_argument("--shell", action="store_true")
    ap.add_argument("--index", action="store_true")
    args = ap.parse_args()
    todo = READERS if (args.all or not args.only) else [c for c in READERS if c["slug"] == args.only]
    for cfg in todo:
        if args.subpages or args.all:
            ids, _ = emit_subpages(cfg)
            print(f"[{cfg['slug']}] wrote {len(ids)} sub-pages")
        if args.shell or args.all:
            emit_shell(cfg)
        if args.index or args.all:
            emit_index(cfg)

if __name__ == "__main__":
    main()
