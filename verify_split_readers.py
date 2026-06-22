"""Structural verification for ALL split readers (no browser needed).
Checks the things that silently break: deepened asset paths, redirect mapping
(Quran derived; hadith via the shell's inline map), anchor presence, and
search-index href integrity. Run after `python split_readers.py --all`.
"""
import json, re, sys, random
from pathlib import Path

SITE = Path(__file__).resolve().parent / "site"
fail = []
def check(cond, msg):
    if not cond:
        fail.append(msg)

ASSET_RE = re.compile(r'(?:href|src)="([^"]+)"')
ASSET_EXT = (".css", ".js", ".png", ".ico", ".webmanifest", ".svg", ".json")

def check_assets(page):
    html = page.read_text(encoding="utf-8")
    for url in ASSET_RE.findall(html):
        if url.startswith(("http://", "https://", "//", "#", "data:", "mailto:")):
            continue
        leaf = url.split("#")[0].split("?")[0]
        if not leaf.endswith(ASSET_EXT):
            continue
        if url.startswith("/"):
            target = SITE / leaf.lstrip("/")
        else:
            target = (page.parent / leaf).resolve()
        check(target.exists(), f"{page.relative_to(SITE)}: asset 404 -> {url}")

# Readers: (slug, anchor_id_regex, derives_surah_from_anchor)
READERS = [
    ("quran", r"s\d+v\d+", True),
    ("bukhari", r"h\d+", False),
    ("muslim", r"h\d+", False),
    ("nasai", r"h\d+", False),
    ("tirmidhi", r"h\d+", False),
    ("abu-dawud", r"h\d+", False),
    ("ibn-majah", r"h\d+", False),
]

def index_name(slug):
    return "quran-reader.json" if slug == "quran" else f"{slug}.json"

READ = SITE / "read"  # the shell's own directory; browser resolves shell links here

random.seed(0)
for slug, idre, derive in READERS:
    base = SITE / "read" / slug
    shell_path = SITE / "read" / f"{slug}.html"
    shell = shell_path.read_text(encoding="utf-8")
    head = shell[:shell.index("</head>")]
    check("location.replace" in head, f"{slug}: shell head missing location.replace")

    # Extract the directory prefix the shell's redirect actually emits
    # (var D="..."). The redirect/landing/TOC links resolve against the SHELL's
    # URL (read/{slug}.html), so they must carry this prefix or they 404.
    dm = re.search(r'var D=("[^"]*"|\'[^\']*\');', head)
    check(dm is not None, f"{slug}: shell redirect missing dir-prefix var D")
    D = json.loads(dm.group(1).replace("'", '"')) if dm else ""
    check(D == f"{slug}/", f"{slug}: redirect dir-prefix is {D!r}, expected {slug+'/'!r}")

    # Build anchor -> emitted-redirect-target (exactly what the shell JS produces)
    if derive:
        def emit_target(a, _D=D):
            m = re.match(r"s(\d+)v\d+", a)
            return f"{_D}{m.group(1)}.html" if m else None
        amap_anchors = []
        for n in (1, 2, 23, 100, 114):
            amap_anchors += re.findall(r'id="(s%dv\d+)"' % n,
                                       (base / f"{n}.html").read_text(encoding="utf-8"))[:3]
    else:
        m = re.search(r"var M=(\{.*?\});", head)
        check(m is not None, f"{slug}: shell inline anchor map not found")
        amap = json.loads(m.group(1)) if m else {}
        manifest = json.loads((base / "anchors.json").read_text(encoding="utf-8"))
        check(amap == manifest, f"{slug}: inline map != anchors.json manifest")
        def emit_target(a, _amap=amap, _D=D):
            return f"{_D}{_amap[a]}.html" if a in _amap else None
        amap_anchors = random.sample(list(amap.keys()), min(20, len(amap)))

    # Resolve each emitted redirect target RELATIVE TO THE SHELL'S DIR (read/),
    # exactly as the browser does — this is what catches a missing {slug}/ prefix.
    for aid in amap_anchors:
        target = emit_target(aid)
        check(target is not None, f"{slug}: no redirect target for {aid}")
        resolved = (READ / (target or "MISSING")).resolve()
        check(resolved.exists(), f"{slug}: redirect '{target}' from read/{slug}.html -> 404 ({resolved}) for {aid}")
        if resolved.exists():
            check(f'id="{aid}"' in resolved.read_text(encoding="utf-8"),
                  f"{slug}: anchor {aid} not on redirect target {target}")

    # Every relative .html link IN THE SHELL (landing + sidebar TOC + nav)
    # must resolve against read/ (the shell's own dir), as the browser does.
    for href in re.findall(r'href="([^"]+)"', shell):
        if href.startswith(("http://", "https://", "//", "#", "mailto:")):
            continue
        path = href.split("#")[0].split("?")[0]
        if not path.endswith(".html"):
            continue
        resolved = (READ / path).resolve()
        check(resolved.exists(), f"{slug}: shell link '{href}' -> 404 ({resolved})")

    # asset paths on a few sub-pages
    subpages = sorted(base.glob("*.html"))
    for p in subpages[:1] + subpages[len(subpages)//2:len(subpages)//2+1] + subpages[-1:]:
        check_assets(p)

    # index href integrity (sample)
    idx = json.loads((SITE/"assets"/"compare-index"/index_name(slug)).read_text(encoding="utf-8"))
    entries = idx["entries"]
    check(len(entries) > 0, f"{slug}: empty index")
    for e in random.sample(entries, min(30, len(entries))):
        pg, _, anchor = e["href"].partition("#")
        sub = base / pg
        check(sub.exists(), f"{slug}: index href page missing {e['href']}")
        if sub.exists():
            check(f'id="{anchor}"' in sub.read_text(encoding="utf-8"),
                  f"{slug}: index href anchor missing {e['href']}")
        check(re.fullmatch(idre, anchor) is not None, f"{slug}: bad anchor in href {e['href']}")

if fail:
    print(f"FAIL ({len(fail)} problems):")
    for f in fail[:50]:
        print("  -", f)
    sys.exit(1)
print("OK: all 7 readers — asset paths resolve, redirects (derived + inline map) map to live anchors, manifests match, index hrefs valid.")
