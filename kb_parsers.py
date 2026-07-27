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
