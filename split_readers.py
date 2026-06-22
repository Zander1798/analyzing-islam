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
