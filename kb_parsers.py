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
