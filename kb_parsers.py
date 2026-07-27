# kb_parsers.py
"""Pure HTML -> KbDoc parsers for the chatbot knowledge base.

Every function takes HTML text and returns a list of dicts with a fixed shape
(see parse_entries). No network, no database — that lives in kb_client.py.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

EMBED_CHAR_LIMIT = 1800  # ~350 tokens, comfortably inside gte-small's 512


def _clean(text: str) -> str:
    """Collapse whitespace. BeautifulSoup already decodes entities."""
    return re.sub(r"\s+", " ", text or "").strip()


def _compose_embed_text(title: str, ref: str | None, categories: list[str], body: str) -> str:
    head = " · ".join(p for p in [title, ref or "", " ".join(categories)] if p)
    return f"{head}\n{body}"[:EMBED_CHAR_LIMIT]


def parse_entries(html: str, source: str) -> list[dict]:
    """Parse one catalog page (site/catalog/<source>.html) into entry docs."""
    soup = BeautifulSoup(html, "html.parser")
    docs: list[dict] = []

    for div in soup.select("div.entry[id]"):
        slug = div["id"]
        title_el = div.select_one(".entry-title")
        if not title_el:
            continue
        title = _clean(title_el.get_text())

        ref_el = div.select_one(".ref")
        ref = _clean(ref_el.get_text()) if ref_el else None

        categories = (div.get("data-category") or "").split()
        strength = div.get("data-strength")

        parts: list[str] = []
        for section in div.select("section"):
            for node in section.find_all(["blockquote", "h4", "p"], recursive=True):
                text = _clean(node.get_text())
                if not text:
                    continue
                parts.append(f"## {text}" if node.name == "h4" else text)
        body = "\n".join(parts)

        docs.append({
            "kind": "entry",
            "slug": slug,
            "title": title,
            "ref": ref,
            "source": source,
            "categories": categories,
            "strength": strength,
            "url": f"catalog/{source}.html#{slug}",
            "body": body,
            "embed_text": _compose_embed_text(title, ref, categories, body),
        })

    return docs


def parse_dossier(html: str, rel_path: str) -> dict | None:
    """Parse one dossier page. Returns None for index/TOC pages with no article."""
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article.arg-article")
    if not article:
        return None

    title_el = article.select_one(".arg-title")
    if not title_el:
        return None
    title = _clean(title_el.get_text())

    ref_el = article.select_one(".arg-ref")
    ref = _clean(ref_el.get_text()) if ref_el else None

    parts: list[str] = []
    for sel, prefix in [
        (".arg-verse-box", "Source: "),
        (".arg-context", ""),
        (".arg-conclusion-box", "Conclusion: "),
        (".arg-responses", "Muslim responses: "),
    ]:
        for node in article.select(sel):
            text = _clean(node.get_text(" "))
            if text:
                parts.append(prefix + text)
    body = "\n".join(parts)

    # 'arguments/bukhari/b01-aisha-age.html' -> 'bukhari/b01-aisha-age'
    slug = rel_path[len("arguments/"):].removesuffix(".html")
    source = slug.split("/")[0]

    return {
        "kind": "dossier",
        "slug": slug,
        "title": title,
        "ref": ref,
        "source": source,
        "categories": [],
        "strength": None,
        "url": rel_path,
        "body": body,
        "embed_text": _compose_embed_text(title, ref, [], body),
    }


def parse_quran_page(html: str, surah: int) -> list[dict]:
    """Parse one surah page from site/read/quran/<surah>.html."""
    soup = BeautifulSoup(html, "html.parser")
    docs: list[dict] = []

    for li in soup.select("li[id^='s']"):
        text_el = li.select_one(".verse-text")
        if not text_el:
            continue
        ayah = li.get("value") or ""
        if not ayah.isdigit():
            continue

        body = _clean(text_el.get_text())
        if not body:
            continue

        ref = f"Quran {surah}:{ayah}"
        docs.append({
            "kind": "verse",
            "slug": f"quran/{surah}:{ayah}",
            "title": ref,
            "ref": ref,
            "source": "quran",
            "categories": [],
            "strength": None,
            "url": f"read/quran/{surah}.html#{li['id']}",
            "body": body,
            "embed_text": _compose_embed_text(ref, None, [], body),
        })

    return docs


BIBLE_BOOKS = {
    "gen": "Genesis", "exo": "Exodus", "lev": "Leviticus", "num": "Numbers",
    "deu": "Deuteronomy", "jos": "Joshua", "jdg": "Judges", "rut": "Ruth",
    "1sa": "1 Samuel", "2sa": "2 Samuel", "1ki": "1 Kings", "2ki": "2 Kings",
    "1ch": "1 Chronicles", "2ch": "2 Chronicles", "ezr": "Ezra", "neh": "Nehemiah",
    "est": "Esther", "job": "Job", "psa": "Psalms", "pro": "Proverbs",
    "ecc": "Ecclesiastes", "sng": "Song of Songs", "isa": "Isaiah", "jer": "Jeremiah",
    "lam": "Lamentations", "ezk": "Ezekiel", "dan": "Daniel", "hos": "Hosea",
    "jol": "Joel", "amo": "Amos", "oba": "Obadiah", "jon": "Jonah", "mic": "Micah",
    "nam": "Nahum", "hab": "Habakkuk", "zep": "Zephaniah", "hag": "Haggai",
    "zec": "Zechariah", "mal": "Malachi",
    "mat": "Matthew", "mrk": "Mark", "luk": "Luke", "jhn": "John", "act": "Acts",
    "rom": "Romans", "1co": "1 Corinthians", "2co": "2 Corinthians",
    "gal": "Galatians", "eph": "Ephesians", "php": "Philippians",
    "col": "Colossians", "1th": "1 Thessalonians", "2th": "2 Thessalonians",
    "1ti": "1 Timothy", "2ti": "2 Timothy", "tit": "Titus", "phm": "Philemon",
    "heb": "Hebrews", "jas": "James", "1pe": "1 Peter", "2pe": "2 Peter",
    "1jn": "1 John", "2jn": "2 John", "3jn": "3 John", "jud": "Jude",
    "rev": "Revelation",
}


def parse_bible_book(html: str, book_code: str) -> list[dict]:
    """Parse one interlinear book page from site/read-external/bible/<code>.html.

    English is reconstructed from .w-gloss spans, so word order follows the
    source language (Greek/Hebrew), not natural English syntax. This is a
    known limitation: it degrades FTS/embedding quality relative to the
    Quran reader, which carries a real translation. If Bible recall proves
    poor downstream, the fix is a proper translation source, not this parser.
    """
    soup = BeautifulSoup(html, "html.parser")
    book_name = BIBLE_BOOKS.get(book_code, book_code.upper())
    docs: list[dict] = []

    for chapter in soup.select("article.bible-chapter[data-c]"):
        cnum = chapter["data-c"]
        for li in chapter.select("li.bible-verse[data-v]"):
            vnum = li["data-v"]
            glosses = [g.get_text() for g in li.select(".w-gloss")]
            body = _clean(" ".join(glosses))
            if not body:
                continue

            ref = f"{book_name} {cnum}:{vnum}"
            anchor = li.get("id") or f"{book_code}-{cnum}-{vnum}"
            docs.append({
                "kind": "verse",
                "slug": f"bible/{anchor}",
                "title": ref,
                "ref": ref,
                "source": "bible",
                "categories": [],
                "strength": None,
                "url": f"read-external/bible/{book_code}.html#{anchor}",
                "body": body,
                "embed_text": _compose_embed_text(ref, None, [], body),
            })

    return docs


def parse_doctrine(md: str, filename: str) -> dict:
    """Parse an authored doctrine markdown file with `---` frontmatter."""
    meta: dict[str, str] = {}
    body = md

    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end == -1:
            raise ValueError(
                f"{filename}: frontmatter opened with '---' but no closing '---' found"
            )
        for line in md[3:end].strip().splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] == '"':
                    v = v[1:-1]
                meta[k.strip()] = v
        body = md[end + 4:]

    body = body.strip()
    slug = meta.get("slug") or filename.removesuffix(".md")
    title = meta.get("title") or slug.replace("-", " ").capitalize()
    cluster = meta.get("cluster", "").strip().lower()

    return {
        "kind": "doctrine",
        "slug": slug,
        "title": title,
        "ref": None,
        "source": "doctrine",
        "categories": [f"cluster-{cluster}"] if cluster else [],
        "strength": None,
        "url": f"doctrine/{slug}.html",
        "body": body,
        "embed_text": _compose_embed_text(title, None, [], body),
    }
