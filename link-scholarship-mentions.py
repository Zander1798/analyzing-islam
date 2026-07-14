#!/usr/bin/env python3
"""Link UNLINKED mentions of known scholarship in entry/dossier prose.

Many book/article titles are cited with a src-link in one place but mentioned
again (or in other entries) as plain text. This finds those unlinked mentions of
titles we already link elsewhere and wraps them in the same src-link.

Title -> URL is learned from existing <a class="src-link"><em>Title</em></a>
anchors. Only distinctive titles are used (>=3 words, or a curated short list);
generic words are excluded. Matches inside an existing <a>...</a> are skipped, so
it is idempotent and never double-links.

    python link-scholarship-mentions.py            # dry run
    python link-scholarship-mentions.py --apply     # rewrite in place
"""
from __future__ import annotations
import os, re, sys, html
from collections import defaultdict, Counter
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
APPLY = "--apply" in sys.argv

ANCHOR = re.compile(r'<a\b[^>]*>.*?</a>', re.S)
SRCLINK = re.compile(r'<a class="src-link" href="([^"]+)"[^>]*>(.*?)</a>', re.S)
EM = re.compile(r'<em>(.*?)</em>', re.S)
TAG = re.compile(r'<[^>]+>')

# short (1-2 word) titles that are distinctive, unambiguous BOOK names (safe to link)
SHORT_OK = {"Hagarism","Milestones","Misquoting Muhammad","Understanding Jihad",
            "Quranic Studies","Kitab al-Maghazi"}
# never link these as titles (too generic / scripture / a place / apostrophe traps)
GENERIC = {"islam","muhammad","history","the quran","quran","koran","the koran","bible",
           "hadith","the bible","allah","god","paradise","hawwa","the qur","islamic law",
           "the history","islamic medicine","dabiq","infidel","heretic","orientalism",
           "answering islam","the dhimmi","fath al-bari","the life of muhammad",
           "judaism and islam","the evil eye","islam and human rights"}
# journals/periodicals: a mention refers to a specific article, not one fixed URL -> never auto-link
def is_journal(t):
    tl = t.lower()
    if any(k in tl for k in ("journal","bulletin","studies in","welt des","muslim world",
                             "studia","centaurus","remmm","der islam","numen","arabica",
                             "quarterly","review of","annual","proceedings")):
        return True
    return False
JOURNALS = set()

def clean_title(raw):
    t = html.unescape(TAG.sub("", raw)).strip().strip("'\"“”‘’ ")
    return t

def build_index():
    raw2url = defaultdict(Counter)     # raw-html title (as it appears in HTML) -> url counter
    for p in SITE.rglob("*.html"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for href, inner in SRCLINK.findall(txt):
            titles = list(EM.findall(inner))                       # <em>Title</em>
            # 'Title' quoted, capital-initial; allow internal &#x27; (Qur'an), close at a boundary
            titles += re.findall(r"&#x27;([A-Z][^<]{2,90}?)&#x27;(?=[\s(),.;:]|$)", inner)
            titles += re.findall(r"'([A-Z][^'<]{2,90}?)'(?=[\s(),.;:]|$)", inner)
            if not titles:
                continue
            raw0 = titles[0].strip()                 # keep raw (entities) for matching
            # index the full title AND its pre-colon core (prose often drops the subtitle)
            variants = [raw0]
            if ":" in raw0:
                variants.append(raw0.split(":")[0].strip())
            for raw in variants:
                t = clean_title(raw)
                wc = len(t.split())
                if wc < 3 and t not in SHORT_OK:
                    continue
                if t.lower() in GENERIC or is_journal(t):
                    continue
                if len(t) < 6 and t not in SHORT_OK:
                    continue
                raw2url[raw][href] += 1
    # consolidate to best url; drop titles with tags inside (safer to skip)
    idx = {}
    for raw, c in raw2url.items():
        if "<" in raw:                                # nested markup -> skip
            continue
        idx[raw] = c.most_common(1)[0][0]
    # drop titles that are MID-WORD truncations of a longer indexed title
    # (e.g. "...the Qur" cut before "&#x27;an") — these would break "Qur'an".
    keys = sorted(idx, key=len)
    drop = set()
    for i, t in enumerate(keys):
        for t2 in keys[i + 1:]:
            if t2.startswith(t) and len(t2) > len(t):
                nxt = t2[len(t)]
                if nxt.isalpha() or nxt in "&'’":     # continues the same word -> truncation
                    drop.add(t)
                    break
    for t in drop:
        idx.pop(t, None)
    return idx

PARA = re.compile(r'</p>|</div>|<div\b|<p\b', re.I)
def para_id(cuts, pos):
    # which block a position falls in (crude paragraph/section index)
    lo, hi = 0, len(cuts)
    while lo < hi:
        mid = (lo + hi) // 2
        if cuts[mid] <= pos: lo = mid + 1
        else: hi = mid
    return lo

def compile_patterns(idx):
    # longest titles first so subtitles win over bare titles; precompiled once
    return [(raw, idx[raw], re.compile(r"(?<![A-Za-z0-9])" + re.escape(raw) + r"(?![A-Za-z0-9'’])"))
            for raw in sorted(idx, key=lambda s: -len(s))]

EXCLUDE_ZONES = re.compile(
    r'<head\b.*?</head>|<script\b.*?</script>|<style\b.*?</style>|'
    r'<title\b.*?</title>|<h[1-6]\b.*?</h[1-6]>|<[^>]+>', re.S | re.I)

def process(txt, patterns):
    # never link inside existing anchors, head, scripts, headings, or tag markup itself
    forbidden = [(m.start(), m.end()) for m in ANCHOR.finditer(txt)]
    forbidden += [(m.start(), m.end()) for m in EXCLUDE_ZONES.finditer(txt)]
    cuts = [m.start() for m in PARA.finditer(txt)]
    chosen = []                                        # (a, b, url)
    taken_para = set()                                 # (title, para_id) already linked
    def overlaps(a, b):
        for s, e in forbidden:
            if a < e and b > s: return True
        for s, e, _ in chosen:
            if a < e and b > s: return True
        return False
    made = []
    for raw, url, pat in patterns:                     # longest first (precompiled)
        if raw not in txt:                             # fast substring pre-filter
            continue
        for m in pat.finditer(txt):
            a, b = m.start(), m.end()
            pid = para_id(cuts, a)
            if (raw, pid) in taken_para:               # 1 per title per block
                continue
            if overlaps(a, b):
                continue
            chosen.append((a, b, url))
            taken_para.add((raw, pid))
            made.append((clean_title(raw), url))
    if not chosen:
        return txt, made
    for a, b, url in sorted(chosen, key=lambda c: -c[0]):   # apply right-to-left
        txt = f'{txt[:a]}<a class="src-link" href="{url}" target="_blank" rel="noopener">{txt[a:b]}</a>{txt[b:]}'
    return txt, made

def main():
    idx = build_index()
    patterns = compile_patterns(idx)
    print(f"linkable distinct titles: {len(idx)}", flush=True)
    total = 0; files = 0; samples = Counter()
    for p in SITE.rglob("*.html"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if '<p>' not in txt and 'arg-context' not in txt:
            continue
        new, made = process(txt, patterns)
        if made:
            total += len(made); files += 1
            for t, u in made: samples[t] += 1
            if APPLY:
                p.write_text(new, encoding="utf-8")
    print(f"unlinked mentions linked: {total} across {files} files" + ("" if APPLY else "  (DRY RUN)"))
    print("\ntop titles newly linked:")
    for t, n in samples.most_common(40):
        print(f"  {n:>4}  {t}")

if __name__ == "__main__":
    main()
