#!/usr/bin/env python3
"""
update_site_files.py
Updates cosmology→science and entry counts across site HTML/JS files.
"""

import re
import json
import shutil
from pathlib import Path

SITE_DIR = Path("C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site")

# Load new category counts from generated JSON
with open(SITE_DIR / "assets/data/catalog-entries.json", 'r', encoding='utf-8') as f:
    catalog = json.load(f)

cat_counts = {}
for entry in catalog:
    for cat in entry.get('categories', []):
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

TOTAL = len(catalog)
print(f"Total entries: {TOTAL}")
print("Category counts:", {k: v for k, v in sorted(cat_counts.items(), key=lambda x: -x[1])})


# ---------------------------------------------------------------------------
# index.html — update totals + category counts + cosmology→science
# ---------------------------------------------------------------------------
def update_index():
    path = SITE_DIR / "index.html"
    text = path.read_text(encoding='utf-8')

    # Total entry count (multiple occurrences)
    text = text.replace('1,549', '1,541')
    text = text.replace('1549', '1541')

    # Cosmology → Science
    text = text.replace('category/cosmology.html', 'category/science.html')
    text = text.replace('<h3>Cosmology</h3>', '<h3>Science</h3>')

    # Category card counts — update each by matching category card pattern
    # Map: category page slug → new count
    count_map = {
        'abrogation':    cat_counts.get('abrogation', 0),
        'scripture':     cat_counts.get('scripture', 0),
        'contradiction': cat_counts.get('contradiction', 0),
        'logic':         cat_counts.get('logic', 0),
        'morality':      cat_counts.get('morality', 0),
        'allah':         cat_counts.get('allah', 0),
        'science':       cat_counts.get('science', 0),   # was cosmology
        'preislamic':    cat_counts.get('preislamic', 0),
        'magic':         cat_counts.get('magic', 0),
        'ritual':        cat_counts.get('ritual', 0),
        'prophet':       cat_counts.get('prophet', 0),
        'privileges':    cat_counts.get('privileges', 0),
        'jesus':         cat_counts.get('jesus', 0),
        'women':         cat_counts.get('women', 0),
        'sexual':        cat_counts.get('sexual', 0),
        'childmarriage': cat_counts.get('childmarriage', 0),
        'lgbtq':         cat_counts.get('lgbtq', 0),
        'slavery':       cat_counts.get('slavery', 0),
        'hudud':         cat_counts.get('hudud', 0),
        'warfare':       cat_counts.get('warfare', 0),
        'apostasy':      cat_counts.get('apostasy', 0),
        'governance':    cat_counts.get('governance', 0),
        'disbelievers':  cat_counts.get('disbelievers', 0),
        'antisemitism':  cat_counts.get('antisemitism', 0),
        'paradise':      cat_counts.get('paradise', 0),
        'hell':          cat_counts.get('hell', 0),
        'eschatology':   cat_counts.get('eschatology', 0),
        'strange':       cat_counts.get('strange', 0),
        'incest':        cat_counts.get('incest', 0),
        'gross-vile':    cat_counts.get('gross-vile', 0),
    }

    # Replace counts inside category cards by matching the href anchor
    def replace_count(m):
        slug = m.group(1)
        count = count_map.get(slug)
        if count is None:
            return m.group(0)
        return f'{m.group(0)[:m.start(2)-m.start(0)]}{count} entries{m.group(0)[m.end(2)-m.start(0):]}'

    # Pattern: category/X.html ... <span class="count">NN entries</span>
    # Use a block-level pattern per card
    for slug, count in count_map.items():
        pattern = re.compile(
            r'(href="category/' + re.escape(slug) + r'\.html"[^>]*>.*?<span class="count">)(\d+) entries(</span>)',
            re.DOTALL
        )
        text = pattern.sub(lambda m: m.group(1) + str(count) + ' entries' + m.group(3), text)

    path.write_text(text, encoding='utf-8')
    print("  Updated index.html")


# ---------------------------------------------------------------------------
# about.html — update total count + cosmology→science
# ---------------------------------------------------------------------------
def update_about():
    path = SITE_DIR / "about.html"
    text = path.read_text(encoding='utf-8')

    text = text.replace('1,549', '1,541')
    text = text.replace('1549', '1541')
    text = text.replace('<strong>Cosmology</strong>', '<strong>Science</strong>')
    text = text.replace(
        'Cosmology</strong> — sun prostrating under the Throne, seven heavens, flat-earth imagery, 60-cubit Adam, the moon split.',
        'Science</strong> — flat-earth cosmology, sun prostrating under the Throne, seven heavens, 60-cubit Adam, the moon split, scientific errors embedded in scripture.'
    )

    path.write_text(text, encoding='utf-8')
    print("  Updated about.html")


# ---------------------------------------------------------------------------
# build-editor.js — update cosmology→science category reference
# ---------------------------------------------------------------------------
def update_build_editor():
    path = SITE_DIR / "assets/js/build-editor.js"
    text = path.read_text(encoding='utf-8')

    text = text.replace(
        '{ slug: "ct-cosmology",     title: "Cosmology",                  path: "category/cosmology.html",     group: "Catalog · by category" }',
        '{ slug: "ct-science",       title: "Science",                    path: "category/science.html",       group: "Catalog · by category" }'
    )

    path.write_text(text, encoding='utf-8')
    print("  Updated build-editor.js")


# ---------------------------------------------------------------------------
# category/science.html — create from cosmology.html with renamed content
# ---------------------------------------------------------------------------
def create_science_category():
    cosmology_path = SITE_DIR / "category/cosmology.html"
    science_path = SITE_DIR / "category/science.html"

    text = cosmology_path.read_text(encoding='utf-8')

    # Replace all cosmology references with science
    text = text.replace('cosmology', 'science')
    text = text.replace('Cosmology', 'Science')

    # Update the tagline / description to match Science category
    text = text.replace(
        'Sun prostrating under the Throne, seven heavens, flat-earth imagery, 60-cubit Adam, the moon split.',
        'Flat-earth cosmology, sun prostrating under the Throne, seven heavens, 60-cubit Adam, the moon split, and scientific errors embedded in scripture.'
    )
    text = text.replace(
        'Sun prostrating under the Throne, seven heavens, flat-earth imagery, 60-cubit Adam, the moon split',
        'Flat-earth cosmology, sun prostrating under the Throne, seven heavens, 60-cubit Adam, the moon split'
    )

    # Update entry count in section title
    new_count = cat_counts.get('science', 0)
    text = re.sub(r'\d+ entries in this category', f'{new_count} entries in this category', text)

    science_path.write_text(text, encoding='utf-8')
    print(f"  Created category/science.html ({new_count} entries)")


# ---------------------------------------------------------------------------
# catalog.html — update cosmology→science if referenced there
# ---------------------------------------------------------------------------
def update_catalog_page():
    path = SITE_DIR / "catalog.html"
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    if 'cosmology' not in text.lower():
        return
    text = text.replace('cosmology', 'science').replace('Cosmology', 'Science')
    path.write_text(text, encoding='utf-8')
    print("  Updated catalog.html")


# ---------------------------------------------------------------------------
# faq.html + goat.html + stats.html — update total count refs
# ---------------------------------------------------------------------------
def update_count_refs():
    for fname in ['faq.html', 'goat.html', 'stats.html', 'play.html', 'compare.html', 'build.html']:
        path = SITE_DIR / fname
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        if '1,549' not in text and '1549' not in text and 'cosmology' not in text.lower():
            continue
        changed = False
        if '1,549' in text:
            text = text.replace('1,549', '1,541')
            changed = True
        if '1549' in text:
            text = text.replace('1549', '1541')
            changed = True
        if 'cosmology' in text.lower():
            text = text.replace('cosmology', 'science').replace('Cosmology', 'Science')
            changed = True
        if changed:
            path.write_text(text, encoding='utf-8')
            print(f"  Updated {fname}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
print("\nUpdating site files...")
update_index()
update_about()
update_build_editor()
create_science_category()
update_catalog_page()
update_count_refs()
print("\nDone.")
