# build-kb.py
"""Ingest the Analyzing Islam corpus into the self-hosted Supabase for chatbot retrieval.

Usage:
    export SUPABASE_DB_URL=postgresql://...
    export SUPABASE_EMBED_URL=https://api.analyzingislam.com/functions/v1/embed
    export SUPABASE_SERVICE_ROLE_KEY=...        # NOT the anon key — embed 403s on it

    python build-kb.py --dry-run       # parse and count, touch nothing
    python build-kb.py                 # everything
    python build-kb.py --only entries  # one tier

Run bulk ingestion OFF-PEAK. The box has 2 vCPU and now serves the live site.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Hyphenated filenames are not importable, and kb_parsers is deliberately not a
# package — load both by path.
kb = _load("kb_parsers", ROOT / "kb_parsers.py")
client = _load("kb_client", ROOT / "kb_client.py")

CATALOG_SOURCES = [
    "quran", "bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah",
]


def collect_entries() -> list[dict]:
    docs = []
    for src in CATALOG_SOURCES:
        p = SITE / "catalog" / f"{src}.html"
        if p.exists():
            docs += kb.parse_entries(p.read_text(encoding="utf-8"), src)
    return docs


def collect_dossiers() -> list[dict]:
    docs = []
    for p in sorted((SITE / "arguments").rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        doc = kb.parse_dossier(p.read_text(encoding="utf-8"), rel)
        if doc:
            docs.append(doc)
    return docs


def collect_quran() -> list[dict]:
    docs = []
    for p in sorted((SITE / "read" / "quran").glob("*.html")):
        if p.stem.isdigit():
            docs += kb.parse_quran_page(p.read_text(encoding="utf-8"), int(p.stem))
    return docs


def collect_bible() -> list[dict]:
    docs = []
    for p in sorted((SITE / "read-external" / "bible").glob("*.html")):
        docs += kb.parse_bible_book(p.read_text(encoding="utf-8"), p.stem)
    return docs


def collect_doctrine() -> list[dict]:
    d = ROOT / "kb-doctrine"
    return [
        kb.parse_doctrine(p.read_text(encoding="utf-8"), p.name)
        for p in sorted(d.glob("*.md"))
        if p.name != "README.md"
    ]


COLLECTORS = {
    "entries": collect_entries,
    "dossiers": collect_dossiers,
    "quran": collect_quran,
    "bible": collect_bible,
    "doctrine": collect_doctrine,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(COLLECTORS), action="append")
    ap.add_argument("--dry-run", action="store_true",
                    help="parse and report counts without touching the database")
    args = ap.parse_args()

    names = args.only or list(COLLECTORS)
    docs: list[dict] = []
    for name in names:
        got = COLLECTORS[name]()
        print(f"  {name:10s} {len(got):6d}")
        docs += got
    print(f"  {'TOTAL':10s} {len(docs):6d}")

    if args.dry_run:
        chunks = sum(len(client.chunk_doc(d)) for d in docs)
        capped = sum(1 for d in docs if client.chunks_were_truncated(d))
        print(f"  {'chunks':10s} {chunks:6d}   (what actually gets embedded)")
        if capped:
            print(f"  {'capped':10s} {capped:6d}   documents losing their tail at "
                  f"{client.MAX_CHUNKS} chunks")
        return

    db_url = client.env("SUPABASE_DB_URL")
    embed_url = client.env("SUPABASE_EMBED_URL")
    service_key = client.env("SUPABASE_SERVICE_ROLE_KEY")

    written, skipped = client.upsert_docs(docs, db_url, embed_url, service_key)
    print(f"\nwritten {written}, unchanged {skipped}")


if __name__ == "__main__":
    main()
