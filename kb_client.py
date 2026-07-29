# kb_client.py
"""Network and database side of the chatbot knowledge-base ingest.

Kept separate from kb_parsers.py so the parsers stay pure and unit-testable.
Everything here that does NOT need a socket is a plain function, so the chunking
and batching logic is tested without a database or the edge runtime.

Three things here deviate from Task 8 as written in the plan. All three are
deliberate and all three would otherwise fail at runtime:

1. The embed function takes ``{"input": ...}`` and answers ``{"embeddings": [...]}``
   for a list. The plan sends ``{"texts": ...}``, which the deployed function
   rejects as an empty batch (400).
2. The embed function is **service_role only**. The plan passes the anon key,
   which now gets a flat 403 — the runtime's verify_jwt checks the signature,
   not the role, so the function checks the role itself.
3. Documents are CHUNKED. The plan embeds one bounded ``embed_text`` per
   document into ``kb_docs.embedding``; the bake-off (see
   docs/migration/CHATBOT-HANDOFF.md) measured 82% R@1 for 4x1800-char chunks
   against 62% for that, so chunks go to ``kb_chunks`` and ``kb_docs.embedding``
   is deliberately left NULL.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

import requests

# Batch size for the embed endpoint. The plan said 32; the handoff's trap 1 says
# keep it modest, because the edge runtime enforces a per-isolate CPU soft limit
# and the supervisor kills a worker that exceeds it — the caller just sees an
# opaque 500. At 9.4 docs/sec sequential there is nothing to gain from big
# batches, so this trades throughput we don't need for failures we don't want.
EMBED_BATCH = 10

# gte-small truncates at 512 tokens SILENTLY (handoff trap 3). 1800 chars is
# ~350 tokens, which is the bound kb_parsers already uses for embed_text. This
# is a hard ceiling on what is handed to the model, INCLUDING the heading
# prefix — never raise it without re-measuring.
CHUNK_CHAR_LIMIT = 1800

# Bake-off configuration B was "4 x 1800", and 4 is what the 82% R@1 was measured
# with. It is NOT a measured optimum — the bake-off's questions targeted content
# "past char 2500", which is still inside 4 chunks (~7200 chars), so nothing in
# it tested the cap at all.
#
# Measured against the real corpus 2026-07-29: at cap=4, 131 documents lose
# their tail, and 124 of them are dossiers whose bodies run to ~13,000 chars —
# so roughly HALF of nearly every dossier was unretrievable. Dossiers are the
# long-form arguments; that is the last content that should be silently
# truncated.
#
#     cap    chunks   docs losing content
#       4      5178                   131
#       8      5561                    13
#      12      5574                     0
#
# Full coverage costs +396 chunks against a 42,620-chunk corpus — under 1%, or
# about 40 seconds of a ~75-minute ingest. 12 makes the cap a safety valve
# against a pathological document rather than a real limit.
#
# ⚠ ONE COUPLING TO WATCH, for Task 10. match_corpus() over-fetches 240 chunks
# to yield 60 documents, a ratio chosen when 4 chunks per document was the
# ceiling. A query matching many long dossiers can now collapse 240 chunks into
# fewer than 60 documents. Only 1,664 of 39,106 documents have more than one
# chunk (every verse is one), so this is unlikely to bite in practice — but it
# is a real interaction, it was introduced here, and the recall fixture is where
# it should be measured rather than argued.
MAX_CHUNKS = 12

HASH_FIELDS = ("title", "ref", "source", "url", "body")

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"missing required environment variable: {name}")
    return v


def content_hash(doc: dict) -> str:
    """Stable hash of the fields that, when changed, require re-embedding."""
    payload = json.dumps(
        {k: doc.get(k) for k in HASH_FIELDS} | {"categories": sorted(doc.get("categories", []))},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _head(doc: dict) -> str:
    """The same title/ref/category prefix kb_parsers puts on embed_text."""
    parts = [doc.get("title") or "", doc.get("ref") or "", " ".join(doc.get("categories") or [])]
    return " · ".join(p for p in parts if p)


def _split_body(body: str, budget: int) -> list[str]:
    """Split body into <=budget-char pieces, preferring paragraph then word
    boundaries so a chunk never ends mid-word."""
    if budget <= 0:
        return []
    pieces: list[str] = []
    rest = body.strip()
    while rest:
        if len(rest) <= budget:
            pieces.append(rest)
            break
        window = rest[:budget]
        cut = window.rfind("\n")
        if cut < budget // 2:            # no usable paragraph break — try a space
            cut = window.rfind(" ")
        if cut < budget // 2:            # no usable break at all — hard cut
            cut = budget
        pieces.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    return [p for p in pieces if p]


def chunk_doc(doc: dict, limit: int = CHUNK_CHAR_LIMIT, max_chunks: int = MAX_CHUNKS) -> list[str]:
    """Split one document into the texts that will actually be embedded.

    Every chunk carries the document's heading, because a bare slice from the
    middle of an argument has no idea what it is about — the title and the
    scripture reference are most of what makes it findable. The heading is
    counted against the limit, so nothing handed to gte-small can exceed it and
    be silently truncated.

    A short document yields exactly one chunk, which is the old embed_text.
    """
    head = _head(doc)
    prefix = f"{head}\n" if head else ""
    budget = limit - len(prefix)

    body = (doc.get("body") or "").strip()
    if not body:
        # Nothing but a heading: still worth one chunk, otherwise the document
        # is unretrievable by vector at all.
        return [head[:limit]] if head else []

    if budget <= 0:
        # Pathological heading longer than the whole budget. Embed the heading
        # alone rather than emitting nothing.
        return [head[:limit]]

    return [f"{prefix}{piece}"[:limit] for piece in _split_body(body, budget)[:max_chunks]]


def chunks_were_truncated(doc: dict, limit: int = CHUNK_CHAR_LIMIT,
                          max_chunks: int = MAX_CHUNKS) -> bool:
    """True when max_chunks dropped part of the body — i.e. the document has
    content that is now unretrievable. Counted and reported by upsert_docs."""
    head = _head(doc)
    budget = limit - (len(head) + 1 if head else 0)
    body = (doc.get("body") or "").strip()
    if not body or budget <= 0:
        return False
    return len(_split_body(body, budget)) > max_chunks


def embed_texts(texts: list[str], embed_url: str, service_key: str,
                batch: int = EMBED_BATCH, post=None) -> list[list[float]]:
    """Embed via the deployed `embed` Edge Function.

    Retries the transient class only. A 403 means the wrong key and a 400 means
    the wrong body — retrying either just takes four times as long to report a
    configuration error, so they raise immediately.

    `post` is injectable so the retry logic can be tested without a network.
    """
    if not texts:
        return []
    send = post or requests.post

    out: list[list[float]] = []
    for i in range(0, len(texts), batch):
        group = texts[i:i + batch]
        for attempt in range(4):
            try:
                r = send(
                    embed_url,
                    json={"input": group},
                    headers={
                        "Authorization": f"Bearer {service_key}",
                        "apikey": service_key,
                        "content-type": "application/json",
                    },
                    timeout=120,
                )
                if r.status_code in RETRYABLE_STATUS:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
                if r.status_code >= 400:
                    raise SystemExit(
                        f"embed refused with HTTP {r.status_code}: {r.text[:300]}\n"
                        "403 means the key is not service_role — the anon key is "
                        "rejected on purpose."
                    )
                vectors = r.json()["embeddings"]
                if len(vectors) != len(group):
                    raise RuntimeError(
                        f"asked for {len(group)} embeddings, got {len(vectors)}"
                    )
                out.extend(vectors)
                break
            except SystemExit:
                raise
            except Exception as exc:
                if attempt == 3:
                    raise RuntimeError(
                        f"embed failed after 4 attempts: {exc}\n"
                        "A repeated 500 on a batch that used to work is usually the "
                        "edge runtime's CPU soft limit killing a used worker — try a "
                        "smaller batch."
                    ) from exc
                time.sleep(2 ** attempt)
    return out


def _existing_hashes(cur, kind: str) -> dict[str, str]:
    cur.execute("select slug, content_hash from kb_docs where kind = %s", (kind,))
    return dict(cur.fetchall())


def upsert_docs(docs: list[dict], db_url: str, embed_url: str, service_key: str,
                report=print) -> tuple[int, int]:
    """Upsert docs and their chunks, embedding only what changed.

    Returns (written, skipped). One transaction per kind, so a failure part-way
    through a long ingest leaves completed kinds committed rather than losing
    hours of embedding.
    """
    if not docs:
        return (0, 0)

    import psycopg2                    # imported here so the pure functions
    import psycopg2.extras             # above are testable without a driver

    written = skipped = truncated = 0

    by_kind: dict[str, list[dict]] = {}
    for d in docs:
        by_kind.setdefault(d["kind"], []).append(d)

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    try:
        for kind, group in by_kind.items():
            with conn.cursor() as cur:
                have = _existing_hashes(cur, kind)
                changed = []
                for d in group:
                    d["content_hash"] = content_hash(d)
                    if have.get(d["slug"]) == d["content_hash"]:
                        skipped += 1
                    else:
                        changed.append(d)

                if not changed:
                    continue

                # Chunk first, so one flat embed call covers the whole kind and
                # the batching in embed_texts stays meaningful.
                per_doc: list[list[str]] = []
                flat: list[str] = []
                for d in changed:
                    cs = chunk_doc(d)
                    per_doc.append(cs)
                    flat.extend(cs)
                    if chunks_were_truncated(d):
                        truncated += 1

                vectors = embed_texts(flat, embed_url, service_key)
                if len(vectors) != len(flat):
                    raise RuntimeError(
                        f"{kind}: expected {len(flat)} vectors, got {len(vectors)}"
                    )

                rows = psycopg2.extras.execute_values(
                    cur,
                    """
                    insert into kb_docs
                      (kind, slug, title, ref, source, categories, strength,
                       url, body, embed_text, content_hash, updated_at)
                    values %s
                    on conflict (kind, slug) do update set
                      title = excluded.title, ref = excluded.ref,
                      source = excluded.source, categories = excluded.categories,
                      strength = excluded.strength, url = excluded.url,
                      body = excluded.body, embed_text = excluded.embed_text,
                      content_hash = excluded.content_hash, updated_at = now()
                    returning id, slug
                    """,
                    [
                        (
                            d["kind"], d["slug"], d["title"], d.get("ref"), d.get("source"),
                            d.get("categories") or [], d.get("strength"), d["url"],
                            d["body"], d.get("embed_text"), d["content_hash"],
                        )
                        for d in changed
                    ],
                    template="(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())",
                    page_size=200,
                    fetch=True,
                )
                id_by_slug = {slug: doc_id for doc_id, slug in rows}

                # Replace chunks wholesale. An edited document can produce FEWER
                # chunks than before, and leftovers would keep matching queries
                # with text the document no longer contains.
                doc_ids = [id_by_slug[d["slug"]] for d in changed]
                cur.execute("delete from kb_chunks where doc_id = any(%s)", (doc_ids,))

                chunk_rows = []
                cursor = 0
                for d, cs in zip(changed, per_doc):
                    doc_id = id_by_slug[d["slug"]]
                    for ix, text in enumerate(cs):
                        chunk_rows.append((doc_id, ix, text, vectors[cursor]))
                        cursor += 1

                if chunk_rows:
                    psycopg2.extras.execute_values(
                        cur,
                        "insert into kb_chunks (doc_id, chunk_ix, embed_text, embedding) values %s",
                        chunk_rows,
                        template="(%s,%s,%s,%s::vector)",
                        page_size=200,
                    )

                written += len(changed)
            conn.commit()
            report(f"  {kind:10s} written {len(changed):6d}  chunks {len(flat):6d}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    if truncated:
        report(
            f"  NOTE: {truncated} document(s) exceeded {MAX_CHUNKS} chunks and lost "
            f"their tail. That content is not retrievable — raise MAX_CHUNKS and "
            f"re-measure with the Task 10 fixture if this number is material."
        )
    return (written, skipped)
