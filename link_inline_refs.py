#!/usr/bin/env python3
"""
link_inline_refs.py
Adds cite-link anchors to unlinked verse/hadith/Bible references
in entry body text across all 7 catalog HTML files.

Rules:
  - Only processes <p> content inside <section> elements
  - Skips <blockquote> content (verse quotes stay as plain text)
  - Skips text already inside <a> tags
  - Keeps display text exactly as written (Q 2:65 stays Q 2:65)
"""

import re
from pathlib import Path

SITE_DIR = Path("C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site")

SOURCES = ["quran", "bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah"]

# Hadith collection → reader URL
HADITH_READERS = {
    "Bukhari":   "../read/bukhari.html",
    "Muslim":    "../read/muslim.html",
    "Abu Dawud": "../read/abu-dawud.html",
    "Tirmidhi":  "../read/tirmidhi.html",
    "Nasai":     "../read/nasai.html",
    "Ibn Majah": "../read/ibn-majah.html",
}

# OT book name (as it appears in prose) → Tanakh reader anchor slug
OT_BOOKS = {
    "Genesis":       "genesis",
    "Exodus":        "exodus",
    "Leviticus":     "leviticus",
    "Numbers":       "numbers",
    "Deuteronomy":   "deuteronomy",
    "Joshua":        "joshua",
    "Judges":        "judges",
    "Ruth":          "ruth",
    "1 Samuel":      "1samuel",
    "2 Samuel":      "2samuel",
    "1 Kings":       "1kings",
    "2 Kings":       "2kings",
    "1 Chronicles":  "1chronicles",
    "2 Chronicles":  "2chronicles",
    "Ezra":          "ezra",
    "Nehemiah":      "nehemiah",
    "Esther":        "esther",
    "Job":           "job",
    "Psalms":        "psalms",
    "Psalm":         "psalms",     # common singular usage
    "Proverbs":      "proverbs",
    "Ecclesiastes":  "ecclesiastes",
    "Song of Songs": "songofsongs",
    "Isaiah":        "isaiah",
    "Jeremiah":      "jeremiah",
    "Lamentations":  "lamentations",
    "Ezekiel":       "ezekiel",
    "Daniel":        "daniel",
    "Hosea":         "hosea",
    "Joel":          "joel",
    "Amos":          "amos",
    "Obadiah":       "obadiah",
    "Jonah":         "jonah",
    "Micah":         "micah",
    "Nahum":         "nahum",
    "Habakkuk":      "habakkuk",
    "Zephaniah":     "zephaniah",
    "Haggai":        "haggai",
    "Zechariah":     "zechariah",
    "Malachi":       "malachi",
}

# NT book name → NT reader anchor slug
NT_BOOKS = {
    "Matthew":          "matthew",
    "Mark":             "mark",
    "Luke":             "luke",
    "John":             "john",
    "Acts":             "acts",
    "Romans":           "romans",
    "1 Corinthians":    "1corinthians",
    "2 Corinthians":    "2corinthians",
    "Galatians":        "galatians",
    "Ephesians":        "ephesians",
    "Philippians":      "philippians",
    "Colossians":       "colossians",
    "1 Thessalonians":  "1thessalonians",
    "2 Thessalonians":  "2thessalonians",
    "1 Timothy":        "1timothy",
    "2 Timothy":        "2timothy",
    "Titus":            "titus",
    "Philemon":         "philemon",
    "Hebrews":          "hebrews",
    "James":            "james",
    "1 Peter":          "1peter",
    "2 Peter":          "2peter",
    "1 John":           "1john",
    "2 John":           "2john",
    "3 John":           "3john",
    "Jude":             "jude",
    "Revelation":       "revelation",
}


def make_quran_link(match):
    """Q S:V or Q S:V–V2  →  linked span keeping display text."""
    full = match.group(0)  # e.g. "Q 2:65" or "Q 3:169–170"
    surah = match.group(1)
    verse = match.group(2)
    anchor = f"s{surah}v{verse}"
    return f'<a class="cite-link" href="../read/quran.html#{anchor}">{full}</a>'


def make_hadith_link(match):
    """Bukhari 224  →  linked span."""
    full   = match.group(0)
    coll   = match.group(1)
    number = match.group(2)
    reader = HADITH_READERS.get(coll)
    if not reader:
        return full
    anchor = f"h{number}"
    return f'<a class="cite-link" href="{reader}#{anchor}">{full}</a>'


def make_bible_link(book_map, reader_path):
    """Returns a replacer function for a given Bible reader."""
    def replacer(match):
        full    = match.group(0)
        book    = match.group(1)
        chapter = match.group(2)
        verse   = match.group(3) if match.lastindex >= 3 and match.group(3) else None
        slug    = book_map.get(book)
        if not slug:
            return full
        anchor = f"{slug}-{chapter}" + (f"-{verse}" if verse else "")
        return f'<a class="cite-link" href="{reader_path}#{anchor}">{full}</a>'
    return replacer


def apply_ref_links(text):
    """Apply all ref-link substitutions to a plain-text fragment."""
    # ---- Quran: "Q S:V" or "Q S:V–V2" or "Q S:V-V2" ----
    text = re.sub(
        r'Q (\d+):(\d+)(?:[–\-]\d+)?',
        make_quran_link,
        text
    )

    # ---- Hadith: "Collection Number" ----
    # Build alternation from collection names (longest first to avoid partial matches)
    collections = sorted(HADITH_READERS.keys(), key=len, reverse=True)
    coll_pattern = '|'.join(re.escape(c) for c in collections)
    text = re.sub(
        rf'({coll_pattern}) (\d+)',
        make_hadith_link,
        text
    )

    # ---- OT Bible refs: "Book Chapter:Verse" ----
    # Sort by length (longest first) to match "Song of Songs" before "Song"
    ot_names = sorted(OT_BOOKS.keys(), key=len, reverse=True)
    ot_pattern = '|'.join(re.escape(b) for b in ot_names)
    text = re.sub(
        rf'({ot_pattern}) (\d+):(\d+)',
        make_bible_link(OT_BOOKS, "../read-external/tanakh.html"),
        text
    )

    # ---- NT Bible refs: "Book Chapter:Verse" ----
    nt_names = sorted(NT_BOOKS.keys(), key=len, reverse=True)
    nt_pattern = '|'.join(re.escape(b) for b in nt_names)
    text = re.sub(
        rf'({nt_pattern}) (\d+):(\d+)',
        make_bible_link(NT_BOOKS, "../read-external/new-testament.html"),
        text
    )

    return text


def process_section_html(section_html):
    """
    Process the inner HTML of a <section> element.
    Only links refs in <p> content; skips <blockquote> and text inside <a> tags.
    """
    # Split section into: blockquote blocks, existing links, and everything else
    # We process "everything else" chunks with apply_ref_links.
    #
    # Pattern explanation:
    #   Group 1: <blockquote>...</blockquote>  — skip
    #   Group 2: <a ...>...</a>               — skip (already linked)
    #   Text between groups: process
    skip_pattern = re.compile(
        r'(<blockquote[^>]*>.*?</blockquote>|<a[^>]*>.*?</a>)',
        re.DOTALL | re.IGNORECASE
    )

    parts = skip_pattern.split(section_html)
    # Even indices = processable text; odd indices = skip patterns
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            result.append(part)   # blockquote or existing link — unchanged
        else:
            result.append(apply_ref_links(part))

    return ''.join(result)


def process_catalog_file(source):
    """Process one catalog HTML file, linking all inline verse refs."""
    path = SITE_DIR / f"catalog/{source}.html"
    content = path.read_text(encoding='utf-8')

    # Find each <section> block and process it
    link_count = [0]

    def section_replacer(m):
        original = m.group(1)
        processed = process_section_html(original)
        added = processed.count('cite-link') - original.count('cite-link')
        link_count[0] += added
        return f'<section>{processed}</section>'

    new_content = re.sub(
        r'<section>(.*?)</section>',
        section_replacer,
        content,
        flags=re.DOTALL
    )

    path.write_text(new_content, encoding='utf-8')
    print(f"  {source:12s}: +{link_count[0]} cite-links added")
    return link_count[0]


def main():
    print("=== Linking inline verse references ===\n")
    total = 0
    for source in SOURCES:
        total += process_catalog_file(source)
    print(f"\nTotal cite-links added: {total}")
    print("\nDone. Verify a few entries then commit.")


if __name__ == '__main__':
    main()
