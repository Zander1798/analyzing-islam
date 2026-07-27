#!/usr/bin/env python3
import re, json
from pathlib import Path

catalog = json.loads(Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\site\assets\data\catalog-entries.json').read_text(encoding='utf-8'))
quran = [e for e in catalog if e.get('source') == 'quran']

html = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran.html').read_text(encoding='utf-8', errors='ignore')

sec_pos = {int(m.group(1)): m.start() for m in re.finditer(r'SECTION (\d+)', html)}
s10 = sec_pos[10]
s12 = sec_pos[12]
chunk10 = html[s10:s12]

PAGE_PAT  = re.compile(r'<div class="page entry-page">(.*?)</div>\s*</div>', re.DOTALL)
RP_PAT    = re.compile(r'<span class="running-page">(\d+)</span>')
TITLE_PAT = re.compile(r'<div class="entry-title"[^>]*>(.*?)</div>', re.DOTALL)
REF_PAT   = re.compile(r'<span class="entry-ref">(.*?)</span>', re.DOTALL)

html_entries = []
for m in PAGE_PAT.finditer(chunk10):
    inner = m.group(1)
    rp    = RP_PAT.search(inner)
    title = TITLE_PAT.search(inner)
    ref_m = REF_PAT.search(inner)
    if rp and title:
        page_num   = int(rp.group(1))
        title_text = re.sub(r'<[^>]+>', '', title.group(1)).strip()
        ref_text   = re.sub(r'<[^>]+>', '', ref_m.group(1)).strip() if ref_m else ''
        html_entries.append({'title': title_text, 'page': page_num, 'ref': ref_text})

print(f'HTML entries: {len(html_entries)}')

# Show sample HTML title vs catalog title for an unmatched entry
# The second quran entry in catalog that might be unmatched
cat_entry = quran[1]  # quran-s9v30-ezra
print(f'\nCatalog title repr: {repr(cat_entry["title"][:80])}')
print(f'Catalog ref: {cat_entry["ref"]}')

# Find matching HTML entry by ref
for he in html_entries:
    if he['ref'] == cat_entry['ref']:
        print(f'HTML entry with same ref:')
        print(f'  title repr: {repr(he["title"][:80])}')
        print(f'  match: {he["title"] == cat_entry["title"]}')
        break

# Check: does ref-based matching work?
# Build ref -> page map (using only FIRST entry per ref for page 1)
ref_to_first_page = {}
for he in html_entries:
    if he['ref'] and he['ref'] not in ref_to_first_page:
        ref_to_first_page[he['ref']] = he['page']

print(f'\nUnique refs in HTML: {len(ref_to_first_page)}')
print(f'Unique refs in catalog quran: {len(set(e["ref"] for e in quran))}')

# Show unmatched catalog refs
cat_refs = set(e['ref'] for e in quran)
html_refs = set(ref_to_first_page.keys())
only_in_cat = cat_refs - html_refs
only_in_html = html_refs - cat_refs
print(f'Refs only in catalog: {len(only_in_cat)}')
if only_in_cat:
    print('  First 5:', sorted(only_in_cat)[:5])
print(f'Refs only in HTML: {len(only_in_html)}')
if only_in_html:
    print('  First 5:', sorted(only_in_html)[:5])

# Now try to get a page number for each catalog entry via ref
# Use ref as key, keeping lowest page for multi-entry refs
from collections import defaultdict
ref_to_pages = defaultdict(list)
for he in html_entries:
    if he['ref']:
        ref_to_pages[he['ref']].append(he['page'])

matched_by_ref = 0
for ce in quran:
    if ce['ref'] in ref_to_pages:
        matched_by_ref += 1

print(f'\nMatched by ref: {matched_by_ref} / {len(quran)}')
