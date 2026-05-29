#!/usr/bin/env python3
"""
update_stats.py
Recalculates all hardcoded numbers in stats.html from catalog-entries.json.
Updates: overall strength distribution, rank table, cat-meta lines, stack bars.
"""

import re
import json
from pathlib import Path
from collections import defaultdict

SITE_DIR = Path("C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site")

# Load catalog
with open(SITE_DIR / "assets/data/catalog-entries.json", 'r', encoding='utf-8') as f:
    catalog = json.load(f)

TOTAL = len(catalog)

# Overall strength
overall = {'basic': 0, 'moderate': 0, 'strong': 0}
for e in catalog:
    overall[e['strength']] = overall.get(e['strength'], 0) + 1

# Per-category strength
cat_stats = defaultdict(lambda: {'total': 0, 'basic': 0, 'moderate': 0, 'strong': 0})
for e in catalog:
    for cat in e.get('categories', []):
        cat_stats[cat]['total'] += 1
        cat_stats[cat][e['strength']] += 1

def pct(n, d):
    return round(n / d * 100) if d else 0

def pct1(n, d):
    return round(n / d * 100, 1) if d else 0.0

# --- Read stats.html ---
stats_path = SITE_DIR / "stats.html"
text = stats_path.read_text(encoding='utf-8')

# === 1. Overall strength distribution bars ===
b = overall['basic'];    b_pct  = pct1(b, TOTAL)
m = overall['moderate']; m_pct  = pct1(m, TOTAL)
s = overall['strong'];   s_pct  = pct1(s, TOTAL)

# Replace Basic bar
text = re.sub(
    r'(bar-fill b-basic" style="width: )[^"]+(")',
    rf'\g<1>{b_pct}%\g<2>', text)
text = re.sub(
    r'(<span class="bar-num">)\d+ &middot; \d+%(</span>)',
    rf'\g<1>{b} &middot; {round(b_pct)}%\g<2>', text, count=1)

# Replace Moderate bar
text = re.sub(
    r'(bar-fill b-moderate" style="width: )[^"]+(")',
    rf'\g<1>{m_pct}%\g<2>', text)
# Find second bar-num (moderate)
bar_nums = list(re.finditer(r'<span class="bar-num">\d+ &middot; \d+%</span>', text))
if len(bar_nums) >= 2:
    old = bar_nums[1].group(0)
    new = f'<span class="bar-num">{m} &middot; {round(m_pct)}%</span>'
    text = text[:bar_nums[1].start()] + new + text[bar_nums[1].end():]

# Replace Strong bar
text = re.sub(
    r'(bar-fill b-strong" style="width: )[^"]+(")',
    rf'\g<1>{s_pct}%\g<2>', text)
bar_nums = list(re.finditer(r'<span class="bar-num">\d+ &middot; \d+%</span>', text))
if len(bar_nums) >= 3:
    old = bar_nums[2].group(0)
    new = f'<span class="bar-num">{s} &middot; {round(s_pct)}%</span>'
    text = text[:bar_nums[2].start()] + new + text[bar_nums[2].end():]

# Update the strength section lede - update the 75%/three-in-ten claims
strong_overall_pct = round(pct1(overall['moderate'] + overall['strong'], TOTAL))
text = re.sub(
    r'Of the 1,\d{3} rated entries, <strong>\d+% land at Moderate or above</strong>',
    f'Of the {TOTAL:,} rated entries, <strong>{strong_overall_pct}% land at Moderate or above</strong>',
    text
)

# === 2. Rank table — rebuild tbody ===
# Sort by % strong
ranked = sorted(cat_stats.items(), key=lambda x: -pct(x[1]['strong'], x[1]['total']))
# Only include categories with at least 10 entries and pct_strong >= 40%
top_cats = [(cat, cs) for cat, cs in ranked
            if cs['total'] >= 10 and pct(cs['strong'], cs['total']) >= 40]

SLUG_DISPLAY = {
    'strange': 'Strange / Obscure', 'women': 'Women', 'prophet': 'Prophetic Character',
    'logic': 'Logical Inconsistency', 'disbelievers': 'Treatment of Disbelievers',
    'science': 'Science', 'contradiction': 'Contradictions', 'morality': 'Moral Problems',
    'eschatology': 'Eschatology', 'governance': 'Governance', 'warfare': 'Warfare & Jihad',
    'jesus': 'Jesus / Christology', 'allah': "Allah's Character", 'hudud': 'Hudud',
    'ritual': 'Ritual Absurdities', 'abrogation': 'Abrogation', 'antisemitism': 'Antisemitism',
    'magic': 'Magic & Occult', 'sexual': 'Sexual Issues', 'scripture': 'Scripture Integrity',
    'privileges': 'Prophetic Privileges', 'slavery': 'Slavery &amp; Captives',
    'preislamic': 'Pre-Islamic Borrowings', 'hell': 'Hell', 'paradise': 'Paradise',
    'apostasy': 'Apostasy &amp; Blasphemy', 'lgbtq': 'LGBTQ / Gender',
    'childmarriage': 'Child Marriage', 'gross-vile': 'Gross / Vile', 'incest': 'Incest',
    'animals': 'Animals',
}

def make_table_row(cat, cs):
    display = SLUG_DISPLAY.get(cat, cat.replace('-', ' ').title())
    p = pct(cs['strong'], cs['total'])
    hot = ' hot' if p >= 50 else ''
    return (f'        <tr><td><a href="category/{cat}.html">{display}</a></td>'
            f'<td class="n">{cs["total"]}</td><td class="n">{cs["strong"]}</td>'
            f'<td class="pct{hot}">{p}%</td></tr>')

new_tbody = '\n'.join(make_table_row(cat, cs) for cat, cs in top_cats)
text = re.sub(
    r'(<thead>.*?</thead>)\s*<tbody>.*?</tbody>',
    rf'\1\n      <tbody>\n{new_tbody}\n      </tbody>',
    text, flags=re.DOTALL)

# === 3. Cat-meta lines — update count and % Strong ===
# Pattern: "NNN entries · PP% Strong-tier · <a href="category/SLUG.html">"
def replace_cat_meta(m):
    slug = m.group('slug')
    cs = cat_stats.get(slug)
    if not cs or cs['total'] == 0:
        return m.group(0)
    total = cs['total']
    p = pct(cs['strong'], total)
    return f'<div class="cat-meta">{total} entries · {p}% Strong-tier · <a href="category/{slug}.html">Browse category →</a></div>'

text = re.sub(
    r'<div class="cat-meta">\d+ entries · \d+% Strong-tier · <a href="category/(?P<slug>[^"]+)\.html">Browse category →</a></div>',
    replace_cat_meta, text)

# === 4. Stack bars — update widths ===
# Pattern used with each cat-section: looks up the id="cat-SLUG" above each stack-bar
def replace_stack(m):
    # Find slug from surrounding context — we'll do a different approach below
    return m.group(0)  # placeholder

# Better approach: process the HTML section by section
def update_stack_bars(text):
    # Find each cat-section and update its stack bar
    sections = re.finditer(r'<section class="cat-section[^"]*" id="cat-([^"]+)">', text)
    offsets = []
    for sec in sections:
        slug = sec.group(1)
        # Find the stack-bar div after this point
        bar_start = text.find('<div class="stack-bar">', sec.end())
        if bar_start == -1:
            continue
        bar_end = text.find('</div>', bar_start) + len('</div>')
        cs = cat_stats.get(slug)
        if not cs or cs['total'] == 0:
            continue
        t = cs['total']
        basic_w  = pct1(cs['basic'], t)
        mod_w    = pct1(cs['moderate'], t)
        strong_w = pct1(cs['strong'], t)
        new_bar = (f'<div class="stack-bar">'
                   f'<span class="s-basic" style="width:{basic_w}%"></span>'
                   f'<span class="s-moderate" style="width:{mod_w}%"></span>'
                   f'<span class="s-strong" style="width:{strong_w}%"></span>'
                   f'</div>')
        offsets.append((bar_start, bar_end, new_bar))

    # Apply replacements in reverse to preserve offsets
    for start, end, new in reversed(offsets):
        text = text[:start] + new + text[end:]
    return text

text = update_stack_bars(text)

# === 5. Total count in metric grid ===
text = re.sub(r'(<div class="n">)1,\d{3}(</div><span class="l">Catalog entries)',
              rf'\g<1>{TOTAL:,}\2', text)

# === 6. The lede "75% land at Moderate" text ===
moderate_strong_pct = round(pct1(m + s, TOTAL))
text = re.sub(
    r'<strong>\d+% land at Moderate or above</strong>',
    f'<strong>{moderate_strong_pct}% land at Moderate or above</strong>',
    text
)

# Write back
stats_path.write_text(text, encoding='utf-8')
print(f"stats.html updated successfully.")
print(f"  Total: {TOTAL:,}")
print(f"  Basic: {b} ({round(b_pct)}%)  Moderate: {m} ({round(m_pct)}%)  Strong: {s} ({round(s_pct)}%)")
print(f"  Moderate+Strong: {moderate_strong_pct}%")
print(f"  Top-tier table rows: {len(top_cats)}")
print(f"  Cat-section stack bars updated for all categories")
