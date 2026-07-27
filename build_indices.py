#!/usr/bin/env python3
"""
Build comprehensive General Index (section 12) and Quran Verse Index (section 13)
for Analyzing Islam Vol I. Extracts real page numbers from the built HTML.
"""
import re, json, html as html_mod
from pathlib import Path
from collections import defaultdict

BOOK_FILE    = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran.html')
CATALOG_FILE = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\site\assets\data\catalog-entries.json')

book_html = BOOK_FILE.read_text(encoding='utf-8', errors='ignore')
catalog   = json.loads(CATALOG_FILE.read_text(encoding='utf-8'))

quran_entries = [e for e in catalog if e.get('source') == 'quran']
print(f'Quran entries in catalog: {len(quran_entries)}')

# ── Locate sections ────────────────────────────────────────────────────────────
sec_pos    = {int(m.group(1)): m.start()
              for m in re.finditer(r'SECTION (\d+)', book_html)}
sec_sorted = sorted(sec_pos)

def section_slice(n):
    start = sec_pos[n]
    later = [k for k in sec_sorted if k > n]
    end   = sec_pos[later[0]] if later else len(book_html)
    return start, end

s10, e10 = section_slice(10)
chunk10  = book_html[s10:e10]

# ── Extract HTML entries (with unescaped text) ─────────────────────────────────
PAGE_PAT  = re.compile(r'<div class="page entry-page">(.*?)</div>\s*</div>', re.DOTALL)
RP_PAT    = re.compile(r'<span class="running-page">(\d+)</span>')
TITLE_PAT = re.compile(r'<div class="entry-title"[^>]*>(.*?)</div>', re.DOTALL)
REF_PAT   = re.compile(r'<span class="entry-ref">(.*?)</span>', re.DOTALL)
CH_PAT    = re.compile(r'Chapter\s+(\d+)')

def strip_tags(s):
    return html_mod.unescape(re.sub(r'<[^>]+>', '', s)).strip()

html_entries = []
for m in PAGE_PAT.finditer(chunk10):
    inner = m.group(1)
    rp    = RP_PAT.search(inner)
    title = TITLE_PAT.search(inner)
    ref_m = REF_PAT.search(inner)
    ch_m  = CH_PAT.search(inner)
    if rp and title:
        html_entries.append({
            'title': strip_tags(title.group(1)),
            'ref':   strip_tags(ref_m.group(1)) if ref_m else '',
            'page':  int(rp.group(1)),
            'ch':    int(ch_m.group(1)) if ch_m else None,
        })

print(f'HTML entries extracted: {len(html_entries)}')

# ── Build lookup maps ─────────────────────────────────────────────────────────
title_to_page = {}
for e in html_entries:
    if e['title'] not in title_to_page:
        title_to_page[e['title']] = e['page']

# Also build ref -> [pages] for verse index
ref_to_all_pages = defaultdict(list)
for e in html_entries:
    if e['ref']:
        ref_to_all_pages[e['ref']].append(e['page'])

# ── Match catalog entries to pages ────────────────────────────────────────────
def get_page(ce):
    t = ce['title']
    # Direct title match
    if t in title_to_page:
        return title_to_page[t]
    # Case-insensitive title
    for ht, pg in title_to_page.items():
        if ht.lower() == t.lower():
            return pg
    # Ref match (first page for that ref)
    r = ce.get('ref', '')
    if r in ref_to_all_pages:
        return min(ref_to_all_pages[r])
    # Normalize ref: "Quran X:Y" -> "Q X:Y"
    r2 = re.sub(r'^Quran\s+', 'Q ', r)
    if r2 in ref_to_all_pages:
        return min(ref_to_all_pages[r2])
    return None

matched_count = 0
unmatched = []
for ce in quran_entries:
    p = get_page(ce)
    if p:
        matched_count += 1
    else:
        unmatched.append(ce)

print(f'Matched entries: {matched_count} / {len(quran_entries)}')
if unmatched:
    print(f'Unmatched ({len(unmatched)}):')
    for ce in unmatched:
        print(f'  {ce["id"]}: {ce["title"][:60]}')

# ── Extract chapter names from HTML ───────────────────────────────────────────
# Chapter openers are <div class="page"> (not entry-page)
# Look for chapter-name divs in those pages
OPENER_PAT  = re.compile(r'<div class="page">\s*<div class="page-inner">(.*?)</div>\s*</div>', re.DOTALL)
CHNAME_PAT  = re.compile(r'<div class="chapter-name"[^>]*>(.*?)</div>', re.DOTALL)
CHNUM_PAT   = re.compile(r'<div class="chapter-breadcrumb"[^>]*>.*?Chapter\s+(\d+)', re.DOTALL)

ch_names = {}
ch_page  = {}
for m in OPENER_PAT.finditer(chunk10):
    inner = m.group(1)
    cn    = CHNAME_PAT.search(inner)
    num   = CHNUM_PAT.search(inner)
    rp    = RP_PAT.search(inner)
    if cn and num:
        ch  = int(num.group(1))
        nm  = strip_tags(cn.group(1))
        ch_names[ch] = nm
        if rp:
            ch_page[ch] = int(rp.group(1))

print(f'Chapter names found: {len(ch_names)}')
for k in sorted(ch_names):
    print(f'  Ch {k}: {ch_names[k]} (p{ch_page.get(k, "?")})')

# ── Category display names ────────────────────────────────────────────────────
CAT_DISPLAY = {
    'abrogation':       'Abrogation (Naskh)',
    'allah':            "Allah's Character",
    'animals':          'Animals',
    'antisemitism':     'Antisemitism',
    'apostasy':         'Apostasy',
    'banu-qurayza':     'Banu Qurayza Massacre',
    'child-marriage':   'Child Marriage',
    'contradictions':   'Contradictions',
    'cosmology':        'Cosmology',
    'dhul-qarnayn':     'Dhul-Qarnayn',
    'eschatology':      'Eschatology',
    'free-will':        'Free Will vs. Predestination',
    'gender':           'Gender & Inequality',
    'inheritance':      'Inheritance',
    'jesus':            'Jesus (Isa)',
    'jinn':             'Jinn',
    'jizya':            'Jizya',
    'lgbtq':            'LGBTQ / Gender',
    'muhammad':         'Muhammad',
    'paradise':         'Paradise',
    'pre-islamic':      'Pre-Islamic Borrowings',
    'slavery':          'Slavery & Captives',
    'warfare':          'Warfare & Jihad',
    'women':            'Women & Sexual Issues',
    'disbelievers':     'Disbelievers',
    'morality':         'Morality',
    'punishment':       'Punishment & Law',
    'science':          'Science & Cosmology',
    'history':          'Historical Claims',
    'violence':         'Violence',
    'theology':         'Theology',
}

def cat_display(slug):
    return CAT_DISPLAY.get(slug, slug.replace('-', ' ').title())

# ── Build General Index: categories -> sorted entries ─────────────────────────
cat_entries = defaultdict(list)  # display_cat -> [(title, page, ref)]
for ce in quran_entries:
    page = get_page(ce)
    if page is None:
        continue
    primary = (ce.get('categories') or ['other'])[0]
    display = cat_display(primary)
    cat_entries[display].append((ce['title'], page, ce.get('ref', '')))

# Sort by page number within each category
for k in cat_entries:
    cat_entries[k].sort(key=lambda x: x[1])

sorted_cats = sorted(cat_entries.keys())
total_items = sum(1 + len(v) for v in cat_entries.values())
print(f'\nGeneral Index: {len(sorted_cats)} categories, {total_items} items')

# ── Build flat item list for General Index ────────────────────────────────────
gi_items = []  # (type, text, page)
current_letter = ''
for cat in sorted_cats:
    first_letter = cat[0].upper()
    if first_letter != current_letter:
        current_letter = first_letter
        gi_items.append(('letter', first_letter, ''))
    first_page = cat_entries[cat][0][1] if cat_entries[cat] else ''
    gi_items.append(('cat', cat, first_page))
    for title, page, ref in cat_entries[cat]:
        gi_items.append(('sub', title, page))

print(f'General Index rows: {len(gi_items)}')

# ── Build Verse Index items ────────────────────────────────────────────────────
SURAH_NAMES = {
    1: 'Al-Fatihah', 2: 'Al-Baqarah', 3: "Ali 'Imran", 4: 'An-Nisa',
    5: "Al-Ma'idah", 6: "Al-An'am", 7: "Al-A'raf", 8: 'Al-Anfal',
    9: 'At-Tawbah', 10: 'Yunus', 11: 'Hud', 12: 'Yusuf',
    13: "Ar-Ra'd", 14: 'Ibrahim', 15: 'Al-Hijr', 16: 'An-Nahl',
    17: 'Al-Isra', 18: 'Al-Kahf', 19: 'Maryam', 20: 'Ta-Ha',
    21: 'Al-Anbiya', 22: 'Al-Hajj', 23: "Al-Mu'minun", 24: 'An-Nur',
    25: 'Al-Furqan', 26: "Ash-Shu'ara", 27: 'An-Naml', 28: 'Al-Qasas',
    29: 'Al-Ankabut', 30: 'Ar-Rum', 31: 'Luqman', 32: 'As-Sajdah',
    33: 'Al-Ahzab', 34: "Saba'", 35: 'Fatir', 36: 'Ya-Sin',
    37: 'As-Saffat', 38: 'Sad', 39: 'Az-Zumar', 40: 'Ghafir',
    41: 'Fussilat', 42: 'Ash-Shura', 43: 'Az-Zukhruf', 44: 'Ad-Dukhan',
    45: 'Al-Jathiyah', 46: 'Al-Ahqaf', 47: 'Muhammad', 48: 'Al-Fath',
    49: 'Al-Hujurat', 50: 'Qaf', 51: 'Adh-Dhariyat', 52: 'At-Tur',
    53: 'An-Najm', 54: 'Al-Qamar', 55: 'Ar-Rahman', 56: "Al-Waqi'ah",
    57: 'Al-Hadid', 58: 'Al-Mujadila', 59: 'Al-Hashr',
    60: 'Al-Mumtahanah', 61: 'As-Saf', 62: "Al-Jumu'ah",
    63: 'Al-Munafiqun', 64: 'At-Taghabun', 65: 'At-Talaq',
    66: 'At-Tahrim', 67: 'Al-Mulk', 68: 'Al-Qalam', 69: "Al-Haqqah",
    70: "Al-Ma'arij", 71: 'Nuh', 72: 'Al-Jinn', 73: 'Al-Muzzammil',
    74: 'Al-Muddaththir', 75: 'Al-Qiyamah', 76: 'Al-Insan',
    77: 'Al-Mursalat', 78: 'An-Naba', 79: "An-Nazi'at",
    80: "'Abasa", 81: 'At-Takwir', 82: 'Al-Infitar',
    83: 'Al-Mutaffifin', 84: 'Al-Inshiqaq', 85: 'Al-Buruj',
    86: 'At-Tariq', 87: 'Al-Ala', 88: 'Al-Ghashiyah', 89: 'Al-Fajr',
    90: 'Al-Balad', 91: 'Ash-Shams', 92: 'Al-Layl', 93: 'Ad-Duha',
    94: 'Ash-Sharh', 95: 'At-Tin', 96: 'Al-Alaq', 97: 'Al-Qadr',
    98: 'Al-Bayyinah', 99: 'Az-Zalzalah', 100: 'Al-Adiyat',
    101: 'Al-Qariah', 102: 'At-Takathur', 103: "Al-'Asr",
    104: 'Al-Humazah', 105: 'Al-Fil', 106: 'Quraysh', 107: 'Al-Maun',
    108: 'Al-Kawthar', 109: 'Al-Kafirun', 110: 'An-Nasr',
    111: 'Al-Masad', 112: 'Al-Ikhlas', 113: 'Al-Falaq', 114: 'An-Nas',
}

def parse_surah(ref):
    m = re.match(r'(?:Q|Quran)\s*(\d+):', ref.strip())
    return int(m.group(1)) if m else 9999

def sort_key_verse(ref):
    m = re.match(r'(?:Q|Quran)\s*(\d+):(\d+)', ref.strip())
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return (9999, 9999)

# Build verse -> pages mapping from catalog entries (preserving all pages per verse)
# For verse index, each unique (ref) gets listed with all pages it appears on
# Sort pages for display
verse_pages = defaultdict(set)  # ref -> set of pages
for ce in quran_entries:
    page = get_page(ce)
    if page and ce.get('ref'):
        verse_pages[ce['ref']].add(page)

# Sort refs by surah/ayah; drop unparseable refs (surah 9999)
sorted_refs = [r for r in sorted(verse_pages.keys(), key=sort_key_verse)
               if parse_surah(r) != 9999]

vi_items = []  # (type, data, page_or_name)
current_surah = None
for ref in sorted_refs:
    pages = sorted(verse_pages[ref])
    surah = parse_surah(ref)
    if surah != current_surah:
        current_surah = surah
        name = SURAH_NAMES.get(surah, f'Surah {surah}')
        vi_items.append(('surah', surah, name))
    display_ref = re.sub(r'^(?:Quran|Q)\s*', '', ref.strip())
    # Truncate long multi-verse refs so they fit the 168px column (≈15 chars @ 10px)
    if len(display_ref) > 15:
        display_ref = display_ref[:14] + '…'
    # Show up to 2 page numbers
    page_str = ', '.join(str(p) for p in pages[:2])
    vi_items.append(('verse', display_ref, page_str))

print(f'Verse Index items: {len(vi_items)} ({len(sorted_refs)} unique refs)')

# ── Pagination helpers ─────────────────────────────────────────────────────────
# Per page: 756px usable (after running-page at bottom 20px -> ~736px content)
# First page of index: subtract heading overhead
GI_HEADING_H   = 80   # index-heading + rule (first page only)
GI_LETTER_H    = 36   # letter divider including margins
GI_CAT_H       = 25   # category row
GI_ENTRY_H     = 27   # sub-entry row (~1.5 lines avg for full-length titles)
GI_COLS        = 1    # single-column layout
GI_COL_H_P1    = 773 - GI_HEADING_H   # ~693px
GI_COL_H_CONT  = 773

VI_HEADING_H   = 90   # index-heading + subtitle + rule
VI_SURAH_H     = 36
VI_VERSE_H     = 18
VI_COLS        = 3
VI_COL_H_P1    = 736 - VI_HEADING_H   # ~646px
VI_COL_H_CONT  = 736

def item_h(item, mode='gi'):
    if mode == 'gi':
        if item[0] == 'letter': return GI_LETTER_H
        if item[0] == 'cat':    return GI_CAT_H
        return GI_ENTRY_H
    else:
        if item[0] == 'surah': return VI_SURAH_H
        return VI_VERSE_H

def paginate(items, col_h_first, col_h_cont, cols_per_page, mode='gi'):
    pages = []  # list of pages, each page = list of cols (each col = list of items)
    cols  = []
    col_items   = []
    col_h_used  = 0
    is_first_pg = True

    def flush_col():
        nonlocal col_items, col_h_used
        cols.append(col_items[:])
        col_items = []
        col_h_used = 0

    def flush_page():
        nonlocal cols, is_first_pg
        while len(cols) < cols_per_page:
            cols.append([])
        pages.append(cols[:])
        cols = []
        is_first_pg = False

    for item in items:
        h = item_h(item, mode)
        # First page uses reduced height (heading takes space); subsequent pages use full height
        limit = col_h_first if (is_first_pg and not cols) else col_h_cont
        if col_h_used + h > limit:
            flush_col()
            if len(cols) >= cols_per_page:
                flush_page()
                limit = col_h_cont
        col_items.append(item)
        col_h_used += h

    flush_col()
    if cols:
        flush_page()

    return pages

gi_pages = paginate(gi_items, GI_COL_H_P1, GI_COL_H_CONT, GI_COLS, 'gi')
vi_pages = paginate(vi_items, VI_COL_H_P1, VI_COL_H_CONT, VI_COLS, 'vi')
print(f'General Index: {len(gi_pages)} pages')
print(f'Verse Index:   {len(vi_pages)} pages')

# ── Page number assignment ─────────────────────────────────────────────────────
GI_START = 590
VI_START = GI_START + len(gi_pages)
print(f'GI pages {GI_START}-{GI_START+len(gi_pages)-1}, VI pages {VI_START}-{VI_START+len(vi_pages)-1}')

# ── HTML generation helpers ────────────────────────────────────────────────────
def gi_row(item):
    typ, text, page = item
    text_h = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    if typ == 'letter':
        return f'        <div class="gi-letter">{text_h}</div>\n'
    if typ == 'cat':
        return (f'        <div class="gi-cat-row">'
                f'<span class="gi-cat-label">{text_h}</span>'
                f'<span class="gi-ldots"></span>'
                f'<span class="gi-pg">{page}</span></div>\n')
    return (f'        <div class="gi-sub-row">'
            f'<span class="gi-sub-label">{text_h}</span>'
            f'<span class="gi-ldots"></span>'
            f'<span class="gi-pg">{page}</span></div>\n')

def vi_row(item):
    typ, data, pg_or_name = item
    if typ == 'surah':
        return (f'        <div class="surah-head">'
                f'<div class="surah-num">Surah {data}</div>'
                f'<div class="surah-name">{pg_or_name}</div>'
                f'</div>\n')
    ref_h = data.replace('&', '&amp;')
    return (f'        <div class="vx"><span class="vx-ref">{ref_h}</span>'
            f'<span class="vx-dots"></span>'
            f'<span class="vx-page">{pg_or_name}</span></div>\n')

def make_gi_page(p_idx, cols_data):
    page_num = GI_START + p_idx
    total    = len(gi_pages)
    label    = f'General Index — Page {p_idx+1} of {total}'
    heading  = ''
    if p_idx == 0:
        heading = (
            '    <div class="index-heading">General Index</div>\n'
            '    <div class="index-rule"></div>\n'
        )
    # Single-column: cols_data has exactly 1 column
    rows = ''.join(gi_row(i) for col in cols_data for i in col)
    return (
        f'<div class="page-label">{label}</div>\n'
        f'<div class="page">\n'
        f'  <div class="page-inner">\n'
        f'{heading}'
        f'    <div class="gi-list">\n'
        f'{rows}'
        f'    </div>\n'
        f'  <span class="running-page">{page_num}</span>\n'
        f'  </div>\n'
        f'</div>\n'
    )

def make_vi_page(p_idx, cols_data):
    page_num = VI_START + p_idx
    total    = len(vi_pages)
    label    = f'Quran Verse Index — Page {p_idx+1} of {total}'
    heading  = ''
    if p_idx == 0:
        heading = (
            '    <div class="index-heading">Quran Verse Index</div>\n'
            f'    <div class="index-sub">Volume I — The Quran · All {len(quran_entries)} entries</div>\n'
            '    <div class="index-rule"></div>\n'
        )
    col_htmls = []
    for col_items in cols_data:
        rows = ''.join(vi_row(i) for i in col_items)
        col_htmls.append(f'      <div class="vi-col">\n{rows}      </div>')
    cols_block = '\n'.join(col_htmls)
    return (
        f'<div class="page-label">{label}</div>\n'
        f'<div class="page">\n'
        f'  <div class="page-inner">\n'
        f'{heading}'
        f'    <div class="verse-columns">\n'
        f'{cols_block}\n'
        f'    </div>\n'
        f'  <span class="running-page">{page_num}</span>\n'
        f'  </div>\n'
        f'</div>\n'
    )

gi_html = '\n'.join(make_gi_page(i, cols) for i, cols in enumerate(gi_pages))
vi_html = '\n'.join(make_vi_page(i, cols) for i, cols in enumerate(vi_pages))

# ── Assemble section markers ────────────────────────────────────────────────────
sep = '═' * 54
new_sec12 = (
    f'<!-- {sep}\n'
    f'     SECTION 12 — GENERAL INDEX\n'
    f'     {sep} -->\n'
    f'<div class="section-divider">Section 12 — General Index</div>\n\n'
    + gi_html + '\n'
)

new_sec13 = (
    f'<!-- {sep}\n'
    f'     SECTION 13 — QURAN VERSE INDEX\n'
    f'     {sep} -->\n'
    f'<div class="section-divider">Section 13 — Quran Verse Index</div>\n\n'
    + vi_html + '\n'
)

# ── Splice into the book HTML ──────────────────────────────────────────────────
# Find section 12 and 13 by locating 'SECTION 12' and 'SECTION 13' text,
# then walking back to find the opening <!-- of each comment block.
def find_section_comment_start(text, label):
    """Find the position of the <!-- that opens the comment containing label."""
    idx = text.find(label)
    if idx == -1:
        return -1
    # Walk back to find the <!-- that directly precedes this section
    # Search within a 200-char window to avoid matching distant comments
    window_start = max(0, idx - 200)
    start = text.rfind('<!--', window_start, idx)
    return start

s12_start = find_section_comment_start(book_html, 'SECTION 12 —')
s13_start = find_section_comment_start(book_html, 'SECTION 13 —')

if s12_start == -1 or s13_start == -1:
    print(f'ERROR: Could not locate section comments (sec12={s12_start}, sec13={s13_start})')
    exit(1)

# Find where section 13 content ends (first <script> after s13)
script_pos = book_html.find('<script>', s13_start)
if script_pos == -1:
    script_pos = len(book_html)

tail = book_html[script_pos:]
front = book_html[:s12_start]

print(f'Splice: front={len(front):,} chars, tail={len(tail):,} chars')
new_book_html = front + new_sec12 + new_sec13 + tail

BOOK_FILE.write_text(new_book_html, encoding='utf-8')
print(f'\nWritten. Sections 12+13 replaced.')
print(f'General Index: {len(gi_pages)} pages, {len(gi_items)} items')
print(f'Verse Index:   {len(vi_pages)} pages, {len(vi_items)} items')
