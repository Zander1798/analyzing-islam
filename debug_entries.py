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
ID_PAT    = re.compile(r'id="(quran-[^"]+)"')
REF_PAT   = re.compile(r'<span class="entry-ref">(.*?)</span>', re.DOTALL)
CH_PAT    = re.compile(r'<span class="running-chapter">.*?Chapter (\d+).*?</span>')

html_entries = []
for m in PAGE_PAT.finditer(chunk10):
    inner = m.group(1)
    rp    = RP_PAT.search(inner)
    title = TITLE_PAT.search(inner)
    id_m  = ID_PAT.search(inner)
    ref_m = REF_PAT.search(inner)
    ch_m  = CH_PAT.search(inner)
    if rp and title:
        page_num   = int(rp.group(1))
        title_text = re.sub(r'<[^>]+>', '', title.group(1)).strip()
        entry_id   = id_m.group(1) if id_m else None
        ref_text   = re.sub(r'<[^>]+>', '', ref_m.group(1)).strip() if ref_m else ''
        ch_num     = int(ch_m.group(1)) if ch_m else None
        html_entries.append({
            'title': title_text,
            'page':  page_num,
            'id':    entry_id,
            'ref':   ref_text,
            'ch':    ch_num,
        })

print(f'HTML entries: {len(html_entries)}')
with_id    = [e for e in html_entries if e['id']]
without_id = [e for e in html_entries if not e['id']]
print(f'With ID: {len(with_id)}, Without ID: {len(without_id)}')

# Show first 3 with IDs
for e in with_id[:3]:
    print(f'  id={e["id"]}, page={e["page"]}, ch={e["ch"]}')
    print(f'  title={e["title"][:80]}')

print()
# Build id -> page map
id_to_page = {e['id']: e['page'] for e in html_entries if e['id']}
print(f'ID-to-page map entries: {len(id_to_page)}')

# Match catalog entries
matched = 0
unmatched_ids = []
for ce in quran:
    if ce['id'] in id_to_page:
        matched += 1
    else:
        unmatched_ids.append(ce['id'])

print(f'Matched by ID: {matched} / {len(quran)}')
print(f'Unmatched: {len(unmatched_ids)}')
if unmatched_ids:
    print('First 5 unmatched catalog IDs:')
    for uid in unmatched_ids[:5]:
        print(f'  {uid}')
    # Check if they appear in HTML at all
    print('First unmatched in HTML?')
    for uid in unmatched_ids[:3]:
        found = uid in html[s10:s12]
        print(f'  {uid}: {"YES" if found else "NO"}')
