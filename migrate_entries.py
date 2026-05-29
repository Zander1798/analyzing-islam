#!/usr/bin/env python3
"""
migrate_entries.py
Extract entries from 7 book HTML files and replace site catalog entries.
Also regenerates catalog-entries.json.
"""

import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

BOOKS_DIR = Path("C:/Users/zande/Documents/AI Workspace/Analyzing Islam Books/output")
SITE_DIR = Path("C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site")

BOOK_FILES = {
    "quran":     BOOKS_DIR / "book.html",
    "bukhari":   BOOKS_DIR / "book_v2.html",
    "muslim":    BOOKS_DIR / "book_vol3.html",
    "abu-dawud": BOOKS_DIR / "book_vol4.html",
    "tirmidhi":  BOOKS_DIR / "book_vol5.html",
    "nasai":     BOOKS_DIR / "book_vol6.html",
    "ibn-majah": BOOKS_DIR / "book_vol7.html",
}

READER_URLS = {
    "quran":     "../read/quran.html",
    "bukhari":   "../read/bukhari.html",
    "muslim":    "../read/muslim.html",
    "abu-dawud": "../read/abu-dawud.html",
    "tirmidhi":  "../read/tirmidhi.html",
    "nasai":     "../read/nasai.html",
    "ibn-majah": "../read/ibn-majah.html",
}

# Map book chapter/category names → site slugs
CHAPTER_TO_SLUG = {
    "Strange / Obscure": "strange",
    "Women": "women",
    "Prophetic Character": "prophet",
    "Warfare & Jihad": "warfare",
    "Eschatology": "eschatology",
    "Magic & Occult": "magic",
    "Magic": "magic",
    "Logical Inconsistency": "logic",
    "Science": "science",
    "Sexual Issues": "sexual",
    "Slavery & Captives": "slavery",
    "Child Marriage": "childmarriage",
    "LGBTQ / Gender": "lgbtq",
    "Apostasy & Blasphemy": "apostasy",
    "Governance": "governance",
    "Hudud": "hudud",
    "Treatment of Disbelievers": "disbelievers",
    "Antisemitism": "antisemitism",
    "Paradise": "paradise",
    "Hell": "hell",
    "Abrogation": "abrogation",
    "Contradictions": "contradiction",
    "Scripture Integrity": "scripture",
    "Allah's Character": "allah",
    "Allah": "allah",
    "Pre-Islamic Borrowings": "preislamic",
    "Ritual Absurdities": "ritual",
    "Ritual": "ritual",
    "Jesus / Christology": "jesus",
    "Prophetic Privileges": "privileges",
    "Moral Problems": "morality",
    "Incest": "incest",
    "Gross / Vile": "gross-vile",
    "Animals": "animals",
    "Medical / Magical": "magic",
}

SLUG_TO_DISPLAY = {
    "strange": "Strange / Obscure",
    "women": "Women",
    "prophet": "Prophetic Character",
    "warfare": "Warfare & Jihad",
    "eschatology": "Eschatology",
    "magic": "Magic & Occult",
    "logic": "Logical Inconsistency",
    "science": "Science",
    "sexual": "Sexual Issues",
    "slavery": "Slavery & Captives",
    "childmarriage": "Child Marriage",
    "lgbtq": "LGBTQ / Gender",
    "apostasy": "Apostasy & Blasphemy",
    "governance": "Governance",
    "hudud": "Hudud",
    "disbelievers": "Treatment of Disbelievers",
    "antisemitism": "Antisemitism",
    "paradise": "Paradise",
    "hell": "Hell",
    "abrogation": "Abrogation",
    "contradiction": "Contradictions",
    "scripture": "Scripture Integrity",
    "allah": "Allah's Character",
    "preislamic": "Pre-Islamic Borrowings",
    "ritual": "Ritual Absurdities",
    "jesus": "Jesus / Christology",
    "privileges": "Prophetic Privileges",
    "morality": "Moral Problems",
    "incest": "Incest",
    "gross-vile": "Gross / Vile",
    "animals": "Animals",
}

HADITH_READER = {
    "Muslim":    ("../read/muslim.html",    "Muslim"),
    "Bukhari":   ("../read/bukhari.html",   "Bukhari"),
    "Abu Dawud": ("../read/abu-dawud.html", "Abu Dawud"),
    "Tirmidhi":  ("../read/tirmidhi.html",  "Tirmidhi"),
    "Nasai":     ("../read/nasai.html",     "Nasai"),
    "Nasa'i":    ("../read/nasai.html",     "Nasa'i"),
    "Ibn Majah": ("../read/ibn-majah.html", "Ibn Majah"),
}


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

STOP_WORDS = {"a", "an", "the", "and", "or", "but", "of", "in", "on", "at",
              "to", "for", "with", "by", "from", "is", "are", "was", "were",
              "be", "as", "it", "its", "not", "no", "so", "do", "does",
              "this", "that", "he", "she", "who", "how", "why", "when",
              "what", "which"}


def make_slug(title: str, max_words: int = 5, max_len: int = 50) -> str:
    """Convert title to URL-friendly slug using first significant words."""
    # Remove quotes, em-dashes, special chars
    clean = re.sub(r'[""''‘’“”—–]', ' ', title)
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', clean)
    words = clean.lower().split()
    # Filter stop words unless we'd end up with < 2 words
    meaningful = [w for w in words if w not in STOP_WORDS]
    if len(meaningful) < 2:
        meaningful = words
    chosen = meaningful[:max_words]
    slug = '-'.join(chosen)
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip('-')
    return slug


# ---------------------------------------------------------------------------
# Verse link generators
# ---------------------------------------------------------------------------

def link_quran_refs(ref_text: str) -> str:
    """
    Convert 'Q 2:65, 5:60, 7:166' or 'Q 2:154, 3:169–170' into linked HTML.
    Keeps display text exactly as-is.
    """
    ref_text = ref_text.strip()
    if not ref_text:
        return ''

    # Split on comma or semicolon, preserving the separator text for re-join
    segments = re.split(r'([,;])', ref_text)
    result = []
    i = 0
    while i < len(segments):
        seg = segments[i]
        sep = segments[i + 1] if i + 1 < len(segments) else ''
        i += 2

        seg_stripped = seg.strip()

        # Try to match a Quran ref: optional "Q " then surah:verse
        m = re.match(r'^(Q\s*)?(\d+):(\d+)', seg_stripped)
        if m:
            surah = m.group(2)
            verse = m.group(3)
            anchor = f"s{surah}v{verse}"
            url = f"../read/quran.html#{anchor}"
            # Preserve any leading/trailing whitespace in seg
            leading = seg[: len(seg) - len(seg.lstrip())]
            trailing = seg[len(seg.rstrip()):]
            result.append(f'{leading}<a href="{url}">{seg_stripped}</a>{trailing}')
        else:
            result.append(seg)

        if sep:
            result.append(sep)

    return ''.join(result)


def link_hadith_refs(ref_text: str) -> str:
    """
    Convert 'Muslim 5127' or 'Abu Dawud 71, 72, 73' into linked HTML.
    Keeps display text exactly as-is.
    """
    ref_text = ref_text.strip()
    if not ref_text:
        return ''

    # Split on semicolons (each segment may have comma-separated numbers)
    segments = ref_text.split(';')
    linked_segs = []

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue

        # Find which collection this segment refers to
        matched_name = None
        matched_url = None
        for cname, (curl, _) in HADITH_READER.items():
            if seg.startswith(cname):
                matched_name = cname
                matched_url = curl
                break

        if not matched_name:
            # Unknown collection — return plain
            linked_segs.append(seg)
            continue

        after = seg[len(matched_name):]  # everything after the collection name

        # Strip parenthetical notes for link generation, keep for display
        # e.g. "3724(Night Journey details)" → number "3724", note "(Night Journey details)"
        paren_re = re.compile(r'\([^)]*\)')
        parens = paren_re.findall(after)
        after_no_paren = paren_re.sub('', after)

        # Split on commas (multiple hadith numbers from same collection)
        num_parts = [p.strip() for p in after_no_paren.split(',') if p.strip()]

        linked_parts = []
        for idx, np in enumerate(num_parts):
            nm = re.match(r'^(\d+)', np)
            if nm:
                num = nm.group(1)
                anchor = f"h{num}"
                url = f"{matched_url}#{anchor}"
                # First part keeps collection name prefix; rest are bare numbers
                display = f"{matched_name} {np}" if idx == 0 else np
                linked_parts.append(f'<a href="{url}">{display}</a>')
            else:
                # Non-numeric (e.g., "hadiths on end times")
                display = f"{matched_name} {np}" if idx == 0 else np
                linked_parts.append(display)

        result = ', '.join(linked_parts)
        # Re-add parenthetical notes
        for paren in parens:
            result += paren
        linked_segs.append(result)

    return '; '.join(linked_segs)


def generate_ref_html(ref_text: str, source: str) -> str:
    """Generate linked ref HTML from plain ref text."""
    ref_text = ref_text.strip()
    if not ref_text:
        return ''
    if source == 'quran':
        return link_quran_refs(ref_text)
    else:
        return link_hadith_refs(ref_text)


# ---------------------------------------------------------------------------
# Entry ID generation
# ---------------------------------------------------------------------------

def load_old_id_map() -> dict:
    """
    Load title→id map from the original catalog-entries.json (git HEAD version)
    so we preserve semantic IDs that bookmarks and external links depend on.
    Falls back to the backup file if git is unavailable.
    """
    import subprocess, tempfile, os
    # Try git first (most reliable — gets the pre-migration version)
    try:
        result = subprocess.run(
            ['git', 'show', 'HEAD:site/assets/data/catalog-entries.json'],
            capture_output=True, cwd=str(SITE_DIR.parent)
        )
        if result.returncode == 0:
            data = json.loads(result.stdout.decode('utf-8'))
            return {e['title'].strip(): e['id'] for e in data}
    except Exception:
        pass
    # Fallback: backup4 (closest to original count)
    backup = SITE_DIR / "assets/data/catalog-entries.backup4.json"
    if backup.exists():
        with open(backup, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {e['title'].strip(): e['id'] for e in data}
    return {}


def generate_entry_id(source: str, ref_text: str, title: str, used_ids: set,
                      old_id_map: dict = None) -> str:
    """
    Generate a unique semantic ID for a site entry.
    If the title matches an existing entry, reuse its old ID to preserve bookmarks/links.
    """
    # Try to reuse old ID if title matches exactly
    if old_id_map:
        old_id = old_id_map.get(title.strip())
        if old_id and old_id not in used_ids:
            used_ids.add(old_id)
            return old_id

    ref_text = ref_text.strip()
    title_slug = make_slug(title)

    if source == 'quran':
        m = re.search(r'(\d+):(\d+)', ref_text)
        if m:
            base = f"quran-s{m.group(1)}v{m.group(2)}-{title_slug}"
        else:
            base = f"quran-{title_slug}"
    else:
        m_num = re.search(r'\b(\d+)\b', ref_text)
        if m_num:
            base = f"{source}-{m_num.group(1)}-{title_slug}"
        else:
            base = f"{source}-{title_slug}"

    base = base[:70].rstrip('-')

    if base not in used_ids:
        used_ids.add(base)
        return base

    counter = 2
    while f"{base}-{counter}" in used_ids:
        counter += 1
    unique = f"{base}-{counter}"
    used_ids.add(unique)
    return unique


# ---------------------------------------------------------------------------
# Book HTML parsing
# ---------------------------------------------------------------------------

def get_section_text(heading_span, section_name: str) -> str:
    """Find the entry-body div immediately following a section-heading span."""
    sib = heading_span.find_next_sibling()
    while sib:
        if sib.name == 'div' and 'entry-body' in (sib.get('class') or []):
            return sib.decode_contents()
        # Stop if we hit another section heading
        if sib.name == 'span' and 'section-heading' in (sib.get('class') or []):
            break
        sib = sib.find_next_sibling()
    return ''


def parse_book_entries(source: str, old_id_map: dict) -> list:
    """Parse all entries from the book HTML file for a source."""
    book_file = BOOK_FILES[source]
    print(f"  Parsing {source} from {book_file.name} ...", end='', flush=True)

    with open(book_file, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    used_ids = set()
    entries = []

    for entry_div in soup.find_all('div', class_='entry-page'):
        classes = entry_div.get('class', [])
        if 'section-body' not in classes:
            continue

        # Title
        title_tag = entry_div.find('h2', class_='entry-heading')
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        # Chapter (primary category from data-chapter attribute)
        chapter = entry_div.get('data-chapter', '').strip()

        # Categories: data-chapter first, then category-tag spans
        categories = []
        primary_slug = CHAPTER_TO_SLUG.get(chapter)
        if primary_slug:
            categories.append(primary_slug)

        entry_meta = entry_div.find('div', class_='entry-meta')
        if entry_meta:
            for cat_span in entry_meta.find_all('span', class_='category-tag'):
                cat_text = cat_span.get_text(strip=True)
                slug = CHAPTER_TO_SLUG.get(cat_text)
                if slug and slug not in categories:
                    categories.append(slug)

        if not categories:
            categories = ['strange']  # fallback

        # Strength
        strength = 'basic'
        if entry_meta:
            badge = entry_meta.find('span', class_=re.compile(r'badge-(basic|moderate|strong)'))
            if badge:
                cls_list = badge.get('class', [])
                if 'badge-strong' in cls_list:
                    strength = 'strong'
                elif 'badge-moderate' in cls_list:
                    strength = 'moderate'

        # Verse refs (plain text)
        verse_refs_div = entry_div.find('div', class_='entry-verse-refs')
        ref_text = verse_refs_div.get_text(strip=True) if verse_refs_div else ''

        # Blockquote
        blockquote = entry_div.find('blockquote', class_='verse-quote')
        blockquote_html = blockquote.decode_contents().strip() if blockquote else ''

        # Section bodies
        sections = {}
        for heading_span in entry_div.find_all('span', class_='section-heading'):
            key = heading_span.get_text(strip=True)
            sections[key] = get_section_text(heading_span, key)

        # Generate site ID (reuse old if title matches)
        entry_id = generate_entry_id(source, ref_text, title, used_ids, old_id_map)

        entries.append({
            'id': entry_id,
            'source': source,
            'title': title,
            'ref_text': ref_text,
            'categories': categories,
            'strength': strength,
            'blockquote_html': blockquote_html,
            'sections': sections,
        })

    print(f" {len(entries)} entries")
    return entries


# ---------------------------------------------------------------------------
# Site HTML generation
# ---------------------------------------------------------------------------

def render_entry_html(entry: dict) -> str:
    """Render one entry as site catalog HTML."""
    source = entry['source']
    is_quran = (source == 'quran')

    entry_id    = entry['id']
    title       = entry['title']
    categories  = entry['categories']
    strength    = entry['strength']
    ref_text    = entry['ref_text']
    bq_html     = entry['blockquote_html']
    sections    = entry['sections']

    data_category = ' '.join(categories)

    # Linked ref
    ref_html = generate_ref_html(ref_text, source)

    # Category tag spans (display names)
    tags_html = ''
    for slug in categories:
        display = SLUG_TO_DISPLAY.get(slug, slug.replace('-', ' ').title())
        tags_html += f'\n    <span class="tag">{display}</span>'
    tags_html += f'\n    <span class="tag strength-{strength}">{strength.capitalize()}</span>'

    # Ref span
    ref_span = f'\n    <span class="ref">{ref_html}</span>' if ref_html else ''

    # Find section content (handle both "VERSE" and "HADITH" variants)
    def get_sec(*keys):
        for k in keys:
            v = sections.get(k, '').strip()
            if v:
                return v
        return ''

    what_html     = get_sec('WHAT THE VERSE SAYS', 'WHAT THE VERSES SAY', 'WHAT THE HADITH SAYS')
    why_html      = get_sec('WHY THIS IS A PROBLEM')
    response_html = get_sec('THE MUSLIM RESPONSE')
    fails_html    = get_sec('WHY IT FAILS')

    what_label = 'What the verse says' if is_quran else 'What the hadith says'

    section_parts = []
    if bq_html:
        section_parts.append(f'    <blockquote>{bq_html}</blockquote>')
    if what_html:
        section_parts.append(f'    <h4>{what_label}</h4>\n    {what_html}')
    if why_html:
        section_parts.append(f'    <h4>Why this is a problem</h4>\n    {why_html}')
    if response_html:
        section_parts.append(f'    <h4>The Muslim response</h4>\n    {response_html}')
    if fails_html:
        section_parts.append(f'    <h4>Why it fails</h4>\n    {fails_html}')

    section_inner = '\n'.join(section_parts)

    return (
        f'<div class="entry" id="{entry_id}" '
        f'data-category="{data_category}" data-strength="{strength}">\n'
        f'  <div class="entry-header">\n'
        f'    <span class="entry-title">{title}</span>'
        f'{tags_html}{ref_span}\n'
        f'  </div>\n'
        f'  <section>\n'
        f'{section_inner}\n'
        f'  </section>\n'
        f'</div>'
    )


def update_catalog_file(source: str, entries: list):
    """Replace the entries-container block in a catalog HTML file."""
    catalog_file = SITE_DIR / f"catalog/{source}.html"

    with open(catalog_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Rename cosmology → science in filter chip
    content = content.replace(
        'data-filter-value="cosmology">Cosmology',
        'data-filter-value="science">Science'
    )

    # Build new entries block
    entries_html = '\n\n'.join(render_entry_html(e) for e in entries)

    # Replace everything between <div id="entries-container"> and the empty-state div
    pattern = re.compile(
        r'(<div id="entries-container">)(.*?)(<div class="empty" id="empty-state")',
        re.DOTALL
    )

    def replacer(m):
        return m.group(1) + '\n\n' + entries_html + '\n\n    ' + m.group(3)

    new_content, n = pattern.subn(replacer, content)
    if n == 0:
        print(f"  WARNING: Could not find entries-container pattern in {catalog_file.name}")
        return

    with open(catalog_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  Written {catalog_file.name} ({len(entries)} entries)")


# ---------------------------------------------------------------------------
# catalog-entries.json
# ---------------------------------------------------------------------------

def write_catalog_json(all_entries: list):
    """Write catalog-entries.json from all entries."""
    json_entries = []
    for e in all_entries:
        json_entries.append({
            "id":         e['id'],
            "source":     e['source'],
            "title":      e['title'],
            "ref":        e['ref_text'],
            "categories": e['categories'],
            "strength":   e['strength'],
            "url":        f"catalog/{e['source']}.html#{e['id']}",
        })

    out_file = SITE_DIR / "assets/data/catalog-entries.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(json_entries, f, indent=2, ensure_ascii=False)

    print(f"\n  Written {out_file.name} ({len(json_entries)} entries total)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Migrating entries from books to site ===\n")

    sources_order = ["quran", "bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah"]
    all_entries = []

    print("Loading old entry IDs for preservation ...")
    old_id_map = load_old_id_map()
    print(f"  {len(old_id_map)} existing IDs loaded")

    print("\nParsing book HTML files:")
    for source in sources_order:
        entries = parse_book_entries(source, old_id_map)
        all_entries.extend(entries)

    print(f"\nTotal entries parsed: {len(all_entries)}")

    print("\nUpdating catalog HTML files:")
    for source in sources_order:
        source_entries = [e for e in all_entries if e['source'] == source]
        update_catalog_file(source, source_entries)

    print("\nWriting catalog-entries.json:")
    write_catalog_json(all_entries)

    # Summary by source
    print("\n=== Summary ===")
    for source in sources_order:
        count = sum(1 for e in all_entries if e['source'] == source)
        print(f"  {source:12s}: {count} entries")
    print(f"  {'TOTAL':12s}: {len(all_entries)} entries")

    print("\nDone. Review the output then commit.")


if __name__ == '__main__':
    main()
