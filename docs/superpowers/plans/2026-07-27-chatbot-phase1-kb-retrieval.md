# Chatbot Phase 1 — Knowledge Base and Retrieval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the searchable knowledge base for the Analyzing Islam chatbot and prove that hybrid retrieval finds the right sources for real questions — at zero API cost.

**Architecture:** Python parsers convert the site's existing HTML (catalog entries, dossiers, Quran reader, interlinear Bible) plus a new authored doctrine directory into uniform `KbDoc` dicts. A Supabase Edge Function embeds text with the built-in `gte-small` model. An orchestrator upserts everything into a single `kb_docs` table carrying both a `tsvector` and a `vector(384)`. A SQL function `match_corpus()` fuses keyword and vector ranking with Reciprocal Rank Fusion and applies per-kind caps. A recall fixture of real questions asserts the right documents come back.

**Tech Stack:** Python 3.13 (`bs4`, `supabase`, `psycopg2`, `yt_dlp`), Postgres 15 + `pgvector`, Supabase Edge Functions (Deno), pytest.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-27-ai-chatbot-design.md`. Where this plan and the spec disagree, the spec wins — raise the conflict rather than silently choosing.
- **Phase 1 spends nothing on the Anthropic API.** No task here calls Claude. If a task seems to need it, stop and re-read the spec.
- Embedding model is `gte-small`, 384 dimensions, English only, truncates at 512 tokens. It runs *only* inside a Supabase Edge Function — there is no local Python path to it.
- Every `kb_docs` row needs a `url` that resolves to a real, existing page on the site. A citation pointing at a 404 is worse than no citation.
- Root-level build scripts are the established repo convention (`build_sources.py`, `build-category-pages.py`). Follow it. Tests load them via `importlib.util.spec_from_file_location`, as in `tests/test_build_sources.py`.
- Parsers must be **pure**: HTML string in, list of dicts out. No network, no database. This is what makes them unit-testable without a live Supabase.
- Do not run `build-catalog-pages.py` or any site rebuild during this phase. Per memory, that reverts the site-only strength reclassification.
- Never commit `.env`, service-role keys, or `SUPABASE_DB_URL` values.

---

## File Structure

| File | Responsibility |
|---|---|
| `supabase/chatbot-kb.sql` | `kb_docs` table, indexes, RLS, `match_corpus()`, `kb_find_ref()` |
| `supabase/functions/embed/index.ts` | Edge Function wrapping `gte-small` |
| `kb_parsers.py` | Pure parse functions, one per corpus tier |
| `kb_client.py` | Hashing, embed-function client, Supabase upsert |
| `build-kb.py` | CLI orchestrator for the text corpora |
| `build-video-kb.py` | CLI orchestrator for video transcripts |
| `kb-doctrine/*.md` | Authored Christian-doctrine reference documents |
| `tests/test_kb_parsers.py` | Parser unit tests (no DB) |
| `tests/test_kb_retrieval.py` | Recall integration test (needs DB) |
| `tests/fixtures/retrieval_questions.json` | The recall fixture |

Parsers live in one module because they share the `KbDoc` shape and change together when that shape changes. The database client is separate because it is the only part that touches the network.

---

### Task 1: Database schema and hybrid retrieval function

**Files:**
- Create: `supabase/chatbot-kb.sql`
- Test: `tests/test_kb_retrieval.py`

**Interfaces:**
- Produces: table `public.kb_docs`; `public.match_corpus(q_text text, q_embedding vector(384), match_count int, caps jsonb, filter_kinds text[], filter_cats text[])` returning `(id, kind, slug, title, ref, source, categories, url, body, score, kind_rank)`; `public.kb_find_ref(q_text text)` returning `setof kb_docs`.

- [ ] **Step 1: Write the SQL file**

```sql
-- supabase/chatbot-kb.sql
-- Analyzing Islam — chatbot knowledge base.
-- Paste into Supabase → SQL Editor → Run. Safe to re-run.

create extension if not exists vector;

create table if not exists public.kb_docs (
  id           bigserial primary key,
  kind         text not null check (kind in ('entry','dossier','verse','video','doctrine')),
  slug         text not null,
  title        text not null,
  ref          text,
  source       text,
  categories   text[] not null default '{}',
  strength     text,
  url          text not null,
  body         text not null,
  embed_text   text,
  embedding    vector(384),
  content_hash text not null,
  fts tsvector generated always as (
    to_tsvector('english', title || ' ' || coalesce(ref,'') || ' ' || body)
  ) stored,
  updated_at   timestamptz not null default now(),
  unique (kind, slug)
);

create index if not exists idx_kb_fts   on public.kb_docs using gin  (fts);
create index if not exists idx_kb_cats  on public.kb_docs using gin  (categories);
create index if not exists idx_kb_kind  on public.kb_docs (kind);
create index if not exists idx_kb_embed on public.kb_docs
  using hnsw (embedding vector_cosine_ops);

-- RLS on, no policies: anon/authenticated cannot read. Edge Functions use
-- service_role, which bypasses RLS. Mirrors the admins table in analytics.sql.
alter table public.kb_docs enable row level security;

-- ---------- hybrid retrieval ----------
create or replace function public.match_corpus(
  q_text       text,
  q_embedding  vector(384),
  match_count  int    default 20,
  caps         jsonb  default '{"dossier":4,"entry":8,"verse":4,"doctrine":4,"video":3}'::jsonb,
  filter_kinds text[] default null,
  filter_cats  text[] default null
)
returns table (
  id bigint, kind text, slug text, title text, ref text, source text,
  categories text[], url text, body text,
  score double precision, kind_rank bigint
)
language sql
stable
security definer
set search_path = public
as $$
  with q as (
    select websearch_to_tsquery('english', q_text) as tsq
  ),
  fts as (
    select s.id, row_number() over () as rank
    from (
      select d.id
      from kb_docs d, q
      where d.fts @@ q.tsq
        and (filter_kinds is null or d.kind = any(filter_kinds))
        and (filter_cats  is null or d.categories && filter_cats)
      order by ts_rank_cd(d.fts, q.tsq) desc, d.id
      limit 60
    ) s
  ),
  vec as (
    select s.id, row_number() over () as rank
    from (
      select d.id
      from kb_docs d
      where d.embedding is not null
        and (filter_kinds is null or d.kind = any(filter_kinds))
        and (filter_cats  is null or d.categories && filter_cats)
      order by d.embedding <=> q_embedding, d.id
      limit 60
    ) s
  ),
  fused as (
    select d.id, d.kind, d.slug, d.title, d.ref, d.source,
           d.categories, d.url, d.body,
           coalesce(1.0/(60 + f.rank), 0.0)
         + coalesce(1.0/(60 + v.rank), 0.0) as score
    from kb_docs d
    left join fts f on f.id = d.id
    left join vec v on v.id = d.id
    where f.id is not null or v.id is not null
  ),
  capped as (
    select *, row_number() over (partition by kind order by score desc, id) as kind_rank
    from fused
  )
  select id, kind, slug, title, ref, source, categories, url, body, score, kind_rank
  from capped
  where kind_rank <= coalesce((caps ->> kind)::int, 0)
  order by score desc, id
  limit match_count;
$$;

revoke all on function public.match_corpus(text, vector, int, jsonb, text[], text[]) from public;
grant execute on function public.match_corpus(text, vector, int, jsonb, text[], text[])
  to service_role;

-- ---------- exact-reference lookup ----------
-- Pins 'Quran 4:34', '4:34', 'Bukhari 5134', 'John 14:16' to the top of results.
create or replace function public.kb_find_ref(q_text text)
returns setof public.kb_docs
language sql
stable
security definer
set search_path = public
as $$
  select *
  from kb_docs
  where ref is not null
    and (
      -- 'Quran 4:34' / 'Q4:34' / bare '4:34'
      (q_text ~* '(^|\s)(q(uran)?\s*)?\d{1,3}:\d{1,3}(\s|$)'
        and ref ilike '%' || (regexp_match(q_text, '(\d{1,3}:\d{1,3})'))[1] || '%')
      -- 'Bukhari 5134', 'John 14:16'
      or (q_text ~* '(^|\s)[A-Za-z]{3,20}\s+\d{1,5}(:\d{1,3})?(\s|$)'
        and ref ilike '%' || (regexp_match(q_text, '([A-Za-z]{3,20}\s+\d{1,5}(?::\d{1,3})?)'))[1] || '%')
    )
  limit 3;
$$;

revoke all on function public.kb_find_ref(text) from public;
grant execute on function public.kb_find_ref(text) to service_role;
```

- [ ] **Step 2: Apply it and verify the objects exist**

```bash
# Requires SUPABASE_DB_URL (Project Settings → Database → Connection string → URI)
psql "$SUPABASE_DB_URL" -f supabase/chatbot-kb.sql
psql "$SUPABASE_DB_URL" -c "\d kb_docs"
psql "$SUPABASE_DB_URL" -c "\df match_corpus kb_find_ref"
```

Expected: `kb_docs` listed with a `vector(384)` column and a generated `fts` column; both functions listed.

- [ ] **Step 3: Write a SQL smoke test proving RRF fuses both lists**

```python
# tests/test_kb_retrieval.py
import os
import json
from pathlib import Path

import pytest

psycopg2 = pytest.importorskip("psycopg2")

DB_URL = os.environ.get("SUPABASE_DB_URL")
pytestmark = pytest.mark.skipif(
    not DB_URL, reason="SUPABASE_DB_URL not set; retrieval tests need a live database"
)
ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def cur():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    with conn.cursor() as c:
        yield c
    conn.close()


def test_match_corpus_fuses_keyword_and_vector(cur):
    """A doc found only by keyword and a doc found only by vector both survive."""
    zero = "[" + ",".join(["0"] * 384) + "]"
    cur.execute(
        "select kind, slug, score from match_corpus(%s, %s::vector, 20)",
        ("abrogation naskh", zero),
    )
    rows = cur.fetchall()
    assert rows, "no results — is the corpus loaded?"
    assert all(r[2] > 0 for r in rows), "every returned row must have a positive RRF score"


def test_match_corpus_respects_kind_caps(cur):
    zero = "[" + ",".join(["0"] * 384) + "]"
    cur.execute(
        "select kind, count(*) from match_corpus(%s, %s::vector, 40, %s::jsonb) group by kind",
        ("jesus crucifixion", zero, json.dumps({"entry": 2, "dossier": 1})),
    )
    counts = dict(cur.fetchall())
    assert counts.get("entry", 0) <= 2
    assert counts.get("dossier", 0) <= 1
    assert "verse" not in counts, "kinds absent from caps must be excluded entirely"
```

- [ ] **Step 4: Run it — it should skip, not fail, until the corpus is loaded**

Run: `pytest tests/test_kb_retrieval.py -v`
Expected: SKIPPED if `SUPABASE_DB_URL` is unset. With it set but no data, `test_match_corpus_fuses_keyword_and_vector` FAILS on "no results — is the corpus loaded?". Both are correct at this stage.

- [ ] **Step 5: Commit**

```bash
git add supabase/chatbot-kb.sql tests/test_kb_retrieval.py
git commit -m "feat(chatbot): kb_docs schema and hybrid match_corpus retrieval"
```

---

### Task 2: The embed Edge Function

**Files:**
- Create: `supabase/functions/embed/index.ts`

**Interfaces:**
- Produces: `POST /functions/v1/embed` accepting `{"texts": string[]}` (max 64) and returning `{"embeddings": number[][]}`, each 384 floats, in request order.

- [ ] **Step 1: Write the function**

```typescript
// supabase/functions/embed/index.ts
// Batch-embeds text with Supabase's built-in gte-small model (384 dims).
// Used by build-kb.py at ingest time and by the chat function at query time.

const session = new Supabase.ai.Session("gte-small");
const MAX_BATCH = 64;

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "POST only" }), {
      status: 405,
      headers: { "content-type": "application/json" },
    });
  }

  let texts: unknown;
  try {
    ({ texts } = await req.json());
  } catch {
    return new Response(JSON.stringify({ error: "invalid JSON body" }), {
      status: 400,
      headers: { "content-type": "application/json" },
    });
  }

  if (!Array.isArray(texts) || texts.length === 0) {
    return new Response(JSON.stringify({ error: "texts must be a non-empty array" }), {
      status: 400,
      headers: { "content-type": "application/json" },
    });
  }
  if (texts.length > MAX_BATCH) {
    return new Response(
      JSON.stringify({ error: `max ${MAX_BATCH} texts per request, got ${texts.length}` }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }

  const embeddings: number[][] = [];
  for (const t of texts) {
    if (typeof t !== "string" || t.trim() === "") {
      return new Response(JSON.stringify({ error: "every text must be a non-empty string" }), {
        status: 400,
        headers: { "content-type": "application/json" },
      });
    }
    // mean_pool + normalize is what pgvector cosine distance expects.
    const v = await session.run(t, { mean_pool: true, normalize: true });
    embeddings.push(v as number[]);
  }

  return new Response(JSON.stringify({ embeddings }), {
    headers: { "content-type": "application/json" },
  });
});
```

- [ ] **Step 2: Serve it locally and verify the shape**

```bash
npx supabase functions serve embed --no-verify-jwt
```

In a second terminal:

```bash
curl -s -X POST http://localhost:54321/functions/v1/embed \
  -H "content-type: application/json" \
  -d '{"texts":["Allah neither begets nor is begotten","the sun prostrates beneath the throne"]}' \
  | python -c "import json,sys; e=json.load(sys.stdin)['embeddings']; print(len(e), len(e[0]))"
```

Expected: `2 384`

- [ ] **Step 3: Verify a bad request is rejected**

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:54321/functions/v1/embed \
  -H "content-type: application/json" -d '{"texts":[]}'
```

Expected: `400`

- [ ] **Step 4: Deploy**

```bash
npx supabase functions deploy embed
```

- [ ] **Step 5: Commit**

```bash
git add supabase/functions/embed/index.ts
git commit -m "feat(chatbot): embed Edge Function wrapping gte-small"
```

---

### Task 3: Parse catalog entries

**Files:**
- Create: `kb_parsers.py`
- Create: `tests/test_kb_parsers.py`

**Interfaces:**
- Produces: `parse_entries(html: str, source: str) -> list[dict]`. Every parser in this module returns dicts with exactly these keys:

```python
{
  "kind":       str,        # 'entry' | 'dossier' | 'verse' | 'doctrine' | 'video'
  "slug":       str,        # unique within kind
  "title":      str,
  "ref":        str | None, # 'Bukhari 5134', 'Quran 4:34', 'John 14:16'
  "source":     str | None, # 'bukhari' | 'quran' | 'bible' | 'doctrine' | channel slug
  "categories": list[str],
  "strength":   str | None, # 'basic' | 'moderate' | 'strong'
  "url":        str,        # site-relative, e.g. 'catalog/bukhari.html#anchor'
  "body":       str,        # full prose handed to Claude
  "embed_text": str,        # composed field that gets embedded
}
```

The real markup, confirmed by inspection:

```html
<div class="entry" id="allah-seals-the-heart-…-70ffe9b8"
     data-category="morality allah" data-strength="basic">
  <div class="entry-header">
    <span class="entry-title">&quot;Allah seals the heart&quot; of Muslims who…</span>
    <span class="tag">Moral Problems</span>
    <span class="tag strength-basic">Basic</span>
    <span class="ref"><a class="cite-link" href="../read/abu-dawud.html#h1052">Abu Dawud 1052</a></span>
  </div>
  <section>
    <blockquote>"He who leaves the Friday prayer…"</blockquote>
    <h4>What the hadith says</h4>   <p>…</p>
    <h4>Why this is a problem</h4>  <p>…</p>
    <h4>The Muslim response</h4>    <p>…</p>
  </section>
</div>
```

- [ ] **Step 1: Write the failing test**

```python
# tests/test_kb_parsers.py
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SITE = ROOT / "site"


def _load():
    spec = importlib.util.spec_from_file_location("kb_parsers", ROOT / "kb_parsers.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kb = _load()


@pytest.fixture(scope="module")
def entries():
    html = (SITE / "catalog" / "abu-dawud.html").read_text(encoding="utf-8")
    return kb.parse_entries(html, "abu-dawud")


def test_parses_many_entries(entries):
    assert len(entries) > 100


def test_entry_has_required_fields(entries):
    e = entries[0]
    assert set(e) == {
        "kind", "slug", "title", "ref", "source", "categories",
        "strength", "url", "body", "embed_text",
    }
    assert e["kind"] == "entry"
    assert e["source"] == "abu-dawud"


def test_entry_title_is_unescaped(entries):
    """Titles carry &quot; in the HTML; the parser must decode it."""
    assert not any("&quot;" in e["title"] for e in entries)


def test_entry_url_points_at_its_anchor(entries):
    e = entries[0]
    assert e["url"] == f"catalog/abu-dawud.html#{e['slug']}"


def test_entry_body_includes_quote_and_argument(entries):
    e = next(e for e in entries if e["slug"].startswith("allah-seals-the-heart"))
    assert "Friday prayer" in e["body"]
    assert "Why this is a problem" in e["body"]


def test_entry_categories_and_strength_parsed(entries):
    e = next(e for e in entries if e["slug"].startswith("allah-seals-the-heart"))
    assert "morality" in e["categories"]
    assert e["strength"] == "basic"


def test_embed_text_is_bounded(entries):
    """gte-small truncates at 512 tokens; keep embed_text well under it."""
    assert all(len(e["embed_text"]) <= 1800 for e in entries)


def test_slugs_unique(entries):
    slugs = [e["slug"] for e in entries]
    assert len(slugs) == len(set(slugs))
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest tests/test_kb_parsers.py -v`
Expected: FAIL — `FileNotFoundError` / `ModuleNotFoundError` for `kb_parsers.py`.

- [ ] **Step 3: Write the parser**

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_kb_parsers.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add kb_parsers.py tests/test_kb_parsers.py
git commit -m "feat(chatbot): parse catalog entries into kb docs"
```

---

### Task 4: Parse dossiers

**Files:**
- Modify: `kb_parsers.py`
- Modify: `tests/test_kb_parsers.py`

**Interfaces:**
- Consumes: `_clean`, `_compose_embed_text` from Task 3.
- Produces: `parse_dossier(html: str, rel_path: str) -> dict | None`.

Confirmed markup: `article.arg-article` containing `h2.arg-title`, `div.arg-ref`, `div.arg-verse-box`, `div.arg-context`, `div.arg-conclusion-box`, `div.arg-responses` with `div.arg-response-item`. One dossier per file.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_kb_parsers.py

def test_parse_dossier_returns_one_doc():
    p = SITE / "arguments" / "bukhari" / "b01-aisha-age.html"
    doc = kb.parse_dossier(p.read_text(encoding="utf-8"), "arguments/bukhari/b01-aisha-age.html")
    assert doc is not None
    assert doc["kind"] == "dossier"
    assert doc["slug"] == "bukhari/b01-aisha-age"
    assert doc["url"] == "arguments/bukhari/b01-aisha-age.html"
    assert len(doc["title"]) > 5


def test_dossier_body_includes_responses():
    p = SITE / "arguments" / "bukhari" / "b01-aisha-age.html"
    doc = kb.parse_dossier(p.read_text(encoding="utf-8"), "arguments/bukhari/b01-aisha-age.html")
    assert len(doc["body"]) > 800, "a dossier is thesis-length, not a stub"


def test_parse_dossier_ignores_index_pages():
    """arguments/bukhari.html is a table of contents, not a dossier."""
    p = SITE / "arguments" / "bukhari.html"
    assert kb.parse_dossier(p.read_text(encoding="utf-8"), "arguments/bukhari.html") is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_kb_parsers.py -k dossier -v`
Expected: FAIL — `AttributeError: module 'kb_parsers' has no attribute 'parse_dossier'`.

- [ ] **Step 3: Implement**

```python
# append to kb_parsers.py

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
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_kb_parsers.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add kb_parsers.py tests/test_kb_parsers.py
git commit -m "feat(chatbot): parse dossiers into kb docs"
```

---

### Task 5: Parse the Quran reader

**Files:**
- Modify: `kb_parsers.py`
- Modify: `tests/test_kb_parsers.py`

**Interfaces:**
- Produces: `parse_quran_page(html: str, surah: int) -> list[dict]`.

Confirmed markup in `site/read/quran/<surah>.html`:

```html
<li id="s1v2" value="2">
  <span class="verse-number">2</span>
  <span class="verse-text">[All] praise is [due] to Allāh, Lord of the worlds</span>
  <span class="verse-arabic" lang="ar" dir="rtl">…</span>
</li>
```

The Arabic must be excluded — `to_tsvector('english', …)` and `gte-small` both handle only English, and including it pollutes both indexes.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_kb_parsers.py

@pytest.fixture(scope="module")
def surah1():
    html = (SITE / "read" / "quran" / "1.html").read_text(encoding="utf-8")
    return kb.parse_quran_page(html, 1)


def test_quran_parses_all_verses_of_al_fatiha(surah1):
    assert len(surah1) == 7


def test_quran_verse_shape(surah1):
    v = surah1[1]
    assert v["kind"] == "verse"
    assert v["source"] == "quran"
    assert v["slug"] == "quran/1:2"
    assert v["ref"] == "Quran 1:2"
    assert v["url"] == "read/quran/1.html#s1v2"
    assert "praise" in v["body"].lower()


def test_quran_body_excludes_arabic(surah1):
    """Arabic script would pollute the English tsvector and the embedding."""
    joined = " ".join(v["body"] for v in surah1)
    assert not re.search(r"[؀-ۿ]", joined)


def test_quran_112_3_is_findable():
    """The single most-cited verse in the Christian-doctrine taxonomy."""
    html = (SITE / "read" / "quran" / "112.html").read_text(encoding="utf-8")
    verses = kb.parse_quran_page(html, 112)
    v = next(v for v in verses if v["ref"] == "Quran 112:3")
    assert "begets" in v["body"].lower() or "begotten" in v["body"].lower()
```

Add `import re` to the test file's imports.

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_kb_parsers.py -k quran -v`
Expected: FAIL — no attribute `parse_quran_page`.

- [ ] **Step 3: Implement**

```python
# append to kb_parsers.py

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
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_kb_parsers.py -v`
Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
git add kb_parsers.py tests/test_kb_parsers.py
git commit -m "feat(chatbot): parse Quran reader verses into kb docs"
```

---

### Task 6: Parse the interlinear Bible

**Files:**
- Modify: `kb_parsers.py`
- Modify: `tests/test_kb_parsers.py`

**Interfaces:**
- Produces: `parse_bible_book(html: str, book_code: str) -> list[dict]`.

**Important context.** `site/read-external/bible/*.html` is an *interlinear*, not a running translation. Confirmed markup:

```html
<article class="bible-chapter" id="jhn-1" data-c="1">
  <ol class="bible-verses">
    <li class="bible-verse" id="jhn-1-1" data-v="1">
      <span class="verse-num">1</span>
      <span class="ilt-words">
        <span class="w" data-s="G1722"><span class="w-orig">Ἐν</span>
          <span class="w-trans">En</span><span class="w-gloss">In [the]</span></span>
        …
```

English is recoverable only by joining `.w-gloss` spans, which yields Greek word order: *"In [the] beginning was the Word, and the Word was with God…"*. Readable, but wooden. **Record this as a known limitation** — it degrades both FTS and embedding quality for Bible verses relative to the Quran, whose reader carries a real translation. If Bible recall proves poor in Task 10, the fix is a proper translation source, not a parser change.

Files use short book codes (`jhn`, `1co`, `gen`); `book_code` maps to a display name via `BIBLE_BOOKS`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_kb_parsers.py

@pytest.fixture(scope="module")
def john():
    html = (SITE / "read-external" / "bible" / "jhn.html").read_text(encoding="utf-8")
    return kb.parse_bible_book(html, "jhn")


def test_bible_parses_every_verse_in_john(john):
    assert len(john) > 800   # John has 879 verses


def test_bible_verse_shape(john):
    v = next(v for v in john if v["ref"] == "John 1:1")
    assert v["kind"] == "verse"
    assert v["source"] == "bible"
    assert v["slug"] == "bible/jhn-1-1"
    assert v["url"] == "read-external/bible/jhn.html#jhn-1-1"
    assert "beginning" in v["body"].lower()
    assert "word" in v["body"].lower()


def test_bible_body_excludes_greek(john):
    """Only the gloss is kept — Greek and transliteration pollute the index."""
    joined = " ".join(v["body"] for v in john[:50])
    assert not re.search(r"[Ͱ-Ͽ]", joined)


def test_bible_paraclete_verse_present(john):
    """John 14:17 is load-bearing for the Muhammad-in-the-Bible cluster."""
    v = next(v for v in john if v["ref"] == "John 14:17")
    assert "spirit" in v["body"].lower()
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_kb_parsers.py -k bible -v`
Expected: FAIL — no attribute `parse_bible_book`.

- [ ] **Step 3: Implement**

```python
# append to kb_parsers.py

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
    source language. See the plan's Task 6 note on this limitation.
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_kb_parsers.py -v`
Expected: 19 passed.

- [ ] **Step 5: Commit**

```bash
git add kb_parsers.py tests/test_kb_parsers.py
git commit -m "feat(chatbot): parse interlinear Bible into kb docs"
```

---

### Task 7: Doctrine reference layer

**Files:**
- Create: `kb-doctrine/README.md`
- Create: `kb-doctrine/trinity-not-three-gods.md`
- Create: `kb-doctrine/begets-not-eternal-generation.md`
- Create: `kb-doctrine/what-is-the-injeel.md`
- Modify: `kb_parsers.py`
- Modify: `tests/test_kb_parsers.py`

**Interfaces:**
- Produces: `parse_doctrine(md: str, filename: str) -> dict`.

Three seed documents only. The full ~30–50 covering §7 clusters A–G is a **content backlog owned by the site author**, not an engineering task — the whole point of the doctrine layer is that the theology is his, not a model's. The gap-rate metric will show which to write next.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_kb_parsers.py

def test_parse_doctrine_reads_frontmatter():
    md = (ROOT / "kb-doctrine" / "trinity-not-three-gods.md").read_text(encoding="utf-8")
    doc = kb.parse_doctrine(md, "trinity-not-three-gods.md")
    assert doc["kind"] == "doctrine"
    assert doc["slug"] == "trinity-not-three-gods"
    assert doc["source"] == "doctrine"
    assert doc["url"] == "doctrine/trinity-not-three-gods.html"
    assert "cluster-a" in doc["categories"]
    assert len(doc["body"]) > 200
    assert "---" not in doc["body"], "frontmatter must be stripped from the body"


def test_all_doctrine_files_parse():
    for p in sorted((ROOT / "kb-doctrine").glob("*.md")):
        if p.name == "README.md":
            continue
        doc = kb.parse_doctrine(p.read_text(encoding="utf-8"), p.name)
        assert doc["title"], f"{p.name} has no title in frontmatter"
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_kb_parsers.py -k doctrine -v`
Expected: FAIL — no attribute `parse_doctrine`.

- [ ] **Step 3: Write the seed documents**

`kb-doctrine/README.md`:

```markdown
# Doctrine reference layer

Authored Christian-doctrine documents for the chatbot. The site carries Christian
*scripture* but no Christian *doctrine*, so without these a Muslim asking "is the
Trinity three gods?" hits the not-covered path — the wrong answer to a good-faith
question.

These are indexed as `kind='doctrine'` and cited like any other source, which keeps
the grounding rule intact and keeps the theology the site author's rather than a
model's.

**Baseline: ecumenical creedal — Nicene and Chalcedonian.** That is the core all
three major traditions share, and exactly what Islamic objections target. Where a
question touches something Christians genuinely dispute among themselves (Marian
veneration, icons, the deuterocanon, predestination), describe the range rather than
picking a side.

**The narrow-claim rule applies.** Never attribute a position to a named scholar
without a source for it. See spec §7.

## Format

    ---
    slug: kebab-case-unique
    title: Sentence-case title
    cluster: A
    ---

    Markdown body.

`cluster` maps to the §7 taxonomy: A God's nature · B Christology · C Scripture ·
D Muhammad in the Bible · E Salvation · F Comparative · G Asymmetric standards.

## Backlog

Clusters A–G in spec §7 list roughly 30 more documents worth writing. Priority
order comes from the admin panel's gap-rate metric once the chatbot is live.
```

`kb-doctrine/trinity-not-three-gods.md`:

```markdown
---
slug: trinity-not-three-gods
title: The Trinity is not three gods
cluster: A
---

Christians confess one God. Not three gods, and not one God wearing three masks in
turn. The formula the ecumenical creeds settled on is *one in being, three in
persons* — one divine essence, subsisting eternally as Father, Son and Spirit.

The distinction that does the work is between **being** and **person**. Being answers
*what* something is; person answers *who*. Three men share one human nature but are
three beings, because human nature is divided among them. The Trinity is not that:
the divine essence is not divided into thirds. Each person is fully God, not a third
of God, and there is exactly one God.

This is why the standard arithmetic objection — 1+1+1=3 — does not land. It assumes
the three are being counted in the same category. They are not. The count is one in
the category of being and three in the category of person.

The Quran's polemic in Q5:116 addresses a triad of God, Jesus and **Mary**. Whatever
that describes, no Christian creed has ever taught it. A Muslim raising the Trinity
is often objecting to something Christians also reject.
```

`kb-doctrine/begets-not-eternal-generation.md`:

```markdown
---
slug: begets-not-eternal-generation
title: "Begets not" and what eternal generation means
cluster: A
---

Surah al-Ikhlas states that God "neither begets nor is begotten" (Q112:3), and
Q19:88–92 calls the claim that the Most Merciful has taken a son so monstrous the
heavens are ready to burst. This is the single most-repeated Muslim objection to
Christian belief.

It rests on a specific reading of *begotten* — as procreation. On that reading the
objection is entirely correct, and Christians reject the same thing. No creed has
ever taught that God took a consort and produced offspring. That is the pagan
theogony the Quran is arguing against, and Christians are not on the other side of
that argument.

What the creeds mean by *begotten* is eternal generation: the Son derives eternally
from the Father, without beginning, without division of essence, and without any
event in time. The Nicene phrase is precise about it — "begotten, not made" — and
"eternally begotten" rules out a moment when the Son began.

So the two claims do not actually collide. Q112:3 denies procreation; Nicaea denies
procreation. The disagreement is elsewhere, and it is worth locating honestly rather
than letting both sides argue past each other.
```

`kb-doctrine/what-is-the-injeel.md`:

```markdown
---
slug: what-is-the-injeel
title: What is the Injeel?
cluster: C
---

The Quran speaks of the Injeel as a scripture given to Jesus (Q5:46, Q57:27) and
instructs the people of the Gospel to judge by what God revealed in it (Q5:47).

Two readings are possible. Either the Injeel is a lost book given to Jesus and since
destroyed, or it is the Gospel Christians actually possessed. The second reading is
what the Quran's own instruction requires: Q5:47 tells the people of the Gospel to
judge by it, in the present tense, addressed to a seventh-century audience. An
instruction to judge by a book that no longer exists is not an instruction at all.

The first reading has a further problem. There is no manuscript, no citation, and no
patristic reference to a separate book of Jesus distinct from the four Gospels. The
manuscript tradition Christians held in the seventh century is the one we still hold,
and it is materially the same text.

This is where the Islamic Dilemma bites, and the site's dossiers develop it at
length: the Quran affirms a scripture that was in Christian hands at the time,
contradicts its contents, and elsewhere insists God's words cannot be changed. All
three cannot hold together.
```

- [ ] **Step 4: Implement the parser**

```python
# append to kb_parsers.py

def parse_doctrine(md: str, filename: str) -> dict:
    """Parse an authored doctrine markdown file with `---` frontmatter."""
    meta: dict[str, str] = {}
    body = md

    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end != -1:
            for line in md[3:end].strip().splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip().strip('"')
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
```

- [ ] **Step 5: Run to verify it passes**

Run: `pytest tests/test_kb_parsers.py -v`
Expected: 21 passed.

- [ ] **Step 6: Commit**

```bash
git add kb-doctrine kb_parsers.py tests/test_kb_parsers.py
git commit -m "feat(chatbot): doctrine reference layer with three seed documents"
```

---

### Task 8: Ingest client and orchestrator

**Files:**
- Create: `kb_client.py`
- Create: `build-kb.py`

**Interfaces:**
- Consumes: every `parse_*` function from Tasks 3–7.
- Produces:
  - `kb_client.content_hash(doc: dict) -> str`
  - `kb_client.embed_texts(texts: list[str], embed_url: str, anon_key: str) -> list[list[float]]`
  - `kb_client.upsert_docs(docs: list[dict], db_url: str, embed_url: str, anon_key: str) -> tuple[int, int]` returning `(written, skipped)`
  - `kb_client.env(name: str) -> str`

- [ ] **Step 1: Write the client**

```python
# kb_client.py
"""Network and database side of the chatbot knowledge-base ingest.

Kept separate from kb_parsers.py so parsers stay pure and unit-testable.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

import psycopg2
import psycopg2.extras
import requests

EMBED_BATCH = 32
HASH_FIELDS = ("title", "ref", "source", "url", "body")


def content_hash(doc: dict) -> str:
    """Stable hash of the fields that, when changed, require re-embedding."""
    payload = json.dumps(
        {k: doc.get(k) for k in HASH_FIELDS} | {"categories": sorted(doc.get("categories", []))},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def embed_texts(texts: list[str], embed_url: str, anon_key: str) -> list[list[float]]:
    """Embed via the deployed `embed` Edge Function. Retries transient failures."""
    out: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i:i + EMBED_BATCH]
        for attempt in range(4):
            try:
                r = requests.post(
                    embed_url,
                    json={"texts": batch},
                    headers={
                        "Authorization": f"Bearer {anon_key}",
                        "content-type": "application/json",
                    },
                    timeout=120,
                )
                r.raise_for_status()
                out.extend(r.json()["embeddings"])
                break
            except Exception as exc:
                if attempt == 3:
                    raise RuntimeError(f"embed failed after 4 attempts: {exc}") from exc
                time.sleep(2 ** attempt)
    return out


def _existing_hashes(cur, kind: str) -> dict[str, str]:
    cur.execute("select slug, content_hash from kb_docs where kind = %s", (kind,))
    return dict(cur.fetchall())


def upsert_docs(docs: list[dict], db_url: str, embed_url: str, anon_key: str) -> tuple[int, int]:
    """Upsert docs, embedding only those whose content_hash changed.

    Returns (written, skipped).
    """
    if not docs:
        return (0, 0)

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    written = skipped = 0

    try:
        with conn.cursor() as cur:
            by_kind: dict[str, list[dict]] = {}
            for d in docs:
                by_kind.setdefault(d["kind"], []).append(d)

            for kind, group in by_kind.items():
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

                vectors = embed_texts([d["embed_text"] for d in changed], embed_url, anon_key)

                psycopg2.extras.execute_values(
                    cur,
                    """
                    insert into kb_docs
                      (kind, slug, title, ref, source, categories, strength,
                       url, body, embed_text, embedding, content_hash, updated_at)
                    values %s
                    on conflict (kind, slug) do update set
                      title = excluded.title, ref = excluded.ref,
                      source = excluded.source, categories = excluded.categories,
                      strength = excluded.strength, url = excluded.url,
                      body = excluded.body, embed_text = excluded.embed_text,
                      embedding = excluded.embedding,
                      content_hash = excluded.content_hash, updated_at = now()
                    """,
                    [
                        (
                            d["kind"], d["slug"], d["title"], d["ref"], d["source"],
                            d["categories"], d["strength"], d["url"], d["body"],
                            d["embed_text"], vec, d["content_hash"],
                        )
                        for d, vec in zip(changed, vectors)
                    ],
                    template="(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector,%s,now())",
                    page_size=200,
                )
                written += len(changed)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return (written, skipped)


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"missing required environment variable: {name}")
    return v
```

- [ ] **Step 2: Write the orchestrator**

```python
# build-kb.py
"""Ingest the Analyzing Islam corpus into Supabase for chatbot retrieval.

Usage:
    export SUPABASE_DB_URL=postgresql://...
    export SUPABASE_EMBED_URL=https://<ref>.supabase.co/functions/v1/embed
    export SUPABASE_ANON_KEY=sb_publishable_...

    python build-kb.py                 # everything
    python build-kb.py --only entries  # one tier
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"

_spec = importlib.util.spec_from_file_location("kb_parsers", ROOT / "kb_parsers.py")
kb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kb)

_cspec = importlib.util.spec_from_file_location("kb_client", ROOT / "kb_client.py")
client = importlib.util.module_from_spec(_cspec)
_cspec.loader.exec_module(client)

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
        return

    db_url = client.env("SUPABASE_DB_URL")
    embed_url = client.env("SUPABASE_EMBED_URL")
    anon_key = client.env("SUPABASE_ANON_KEY")

    written, skipped = client.upsert_docs(docs, db_url, embed_url, anon_key)
    print(f"\nwritten {written}, unchanged {skipped}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Dry-run to verify parse counts before spending any embedding time**

Run: `python build-kb.py --dry-run`

Expected, approximately:

```
  entries      1524
  dossiers      147
  quran        6236
  bible       31100
  doctrine        3
  TOTAL       39010
```

If `entries` is not exactly 1524, stop — the parser is dropping rows and everything downstream inherits the error.

- [ ] **Step 4: Ingest for real**

```bash
python build-kb.py --only entries --only dossiers --only doctrine --only quran
python build-kb.py --only bible          # slowest; run separately
psql "$SUPABASE_DB_URL" -c "select kind, count(*) from kb_docs group by kind order by 2 desc"
```

- [ ] **Step 5: Verify idempotency — a second run must write nothing**

Run: `python build-kb.py --only doctrine`
Expected: `written 0, unchanged 3`

- [ ] **Step 6: Prove every citation URL resolves to a real anchor**

Spec §10 requires this, and it is the difference between a citation and a broken
promise. The repo already has precedent in `tests/test_quiz_links_resolve.py`.

```python
# tests/test_kb_urls_resolve.py
"""Every kb_docs url must resolve to a real file and a real anchor on the site.

A citation pointing at a 404 is worse than no citation, so this runs against the
parsed corpus rather than the database — it catches the bug before ingest.
"""
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SITE = ROOT / "site"

_spec = importlib.util.spec_from_file_location("build_kb", ROOT / "build-kb.py")
bk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bk)


def _anchors(path: Path) -> set[str]:
    html = path.read_text(encoding="utf-8")
    return set(re.findall(r'id="([^"]+)"', html))


@pytest.mark.parametrize("tier", ["entries", "dossiers", "doctrine"])
def test_urls_point_at_existing_pages(tier):
    docs = bk.COLLECTORS[tier]()
    assert docs, f"{tier} produced no documents"

    for d in docs:
        if d["url"].startswith("http"):
            continue                      # external (video) — not our file tree
        if d["kind"] == "doctrine":
            continue                      # doctrine pages are built in Phase 3
        page, _, anchor = d["url"].partition("#")
        assert (SITE / page).exists(), f"{d['slug']}: missing page {page}"


def test_entry_anchors_exist():
    """Spot-check anchors per catalog page — parsing all seven is slow."""
    docs = bk.collect_entries()
    by_page: dict[str, list[dict]] = {}
    for d in docs:
        by_page.setdefault(d["url"].split("#")[0], []).append(d)

    for page, group in by_page.items():
        ids = _anchors(SITE / page)
        for d in group[:25]:
            anchor = d["url"].split("#", 1)[1]
            assert anchor in ids, f"{page} has no anchor #{anchor}"


def test_entry_count_matches_catalog_index():
    """catalog-entries.json is the site's own count — the parse must agree."""
    import json
    index = json.loads(
        (SITE / "assets" / "data" / "catalog-entries.json").read_text(encoding="utf-8")
    )
    assert len(bk.collect_entries()) == len(index)
```

Run: `pytest tests/test_kb_urls_resolve.py -v`
Expected: all pass. A failure here means the parser is producing citations that
would 404 — fix the parser, never the assertion.

- [ ] **Step 7: Commit**

```bash
git add kb_client.py build-kb.py tests/test_kb_urls_resolve.py
git commit -m "feat(chatbot): ingest client, build-kb orchestrator, url resolution tests"
```

---

### Task 9: Video transcript ingest

**Files:**
- Create: `build-video-kb.py`

**Interfaces:**
- Consumes: `kb_client.upsert_docs`.
- Produces: `parse_vtt(vtt_text) -> list[tuple[int, str]]`, `chunk_cues(cues, words_per_chunk) -> list[tuple[int, str]]`.

Verified working: captions fetch cleanly and ASR renders "Quran", "Surah", "Allah", "Muhammad" correctly. Channel sizes sampled — Islam Critiqued 393, Testify 449, Apostate Prophet 485; expect ~2,700 across six channels and ~21,000 chunks.

**Fails soft.** A video whose captions can't be fetched is skipped and logged. Ingest never aborts — yt-dlp breaks periodically as YouTube changes, and a two-hour run must not die on video 1,900.

- [ ] **Step 1: Write the script**

```python
# build-video-kb.py
"""Ingest YouTube transcripts from the vetted channels in site/watch.html.

Usage:
    export SUPABASE_DB_URL=... SUPABASE_EMBED_URL=... SUPABASE_ANON_KEY=...
    python build-video-kb.py --limit 5      # smoke test first
    python build-video-kb.py                # full run, 2-3 hours
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import tempfile
from pathlib import Path

import yt_dlp

ROOT = Path(__file__).parent
SITE = ROOT / "site"

_cspec = importlib.util.spec_from_file_location("kb_client", ROOT / "kb_client.py")
client = importlib.util.module_from_spec(_cspec)
_cspec.loader.exec_module(client)

WORDS_PER_CHUNK = 250


def channels_from_watch_page() -> dict[str, dict]:
    """Read channel slug -> {name, url} out of WATCH_DATA in watch.html."""
    html = (SITE / "watch.html").read_text(encoding="utf-8")
    out: dict[str, dict] = {}
    for m in re.finditer(
        r"'([a-z0-9-]+)':\s*\{\s*name:\s*'([^']+)',\s*url:\s*'([^']+)'", html
    ):
        out[m.group(1)] = {"name": m.group(2), "url": m.group(3)}
    return out


def list_channel_videos(channel_url: str) -> list[dict]:
    opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"{channel_url}/videos", download=False)
    return [
        {"id": e["id"], "title": e.get("title") or e["id"]}
        for e in (info.get("entries") or [])
        if e.get("id")
    ]


def parse_vtt(vtt_text: str) -> list[tuple[int, str]]:
    """WebVTT -> [(start_seconds, line)], de-duplicating rolling-caption repeats."""
    cues: list[tuple[int, str]] = []
    ts = None
    seen: set[str] = set()
    for line in vtt_text.splitlines():
        m = re.match(r"(\d\d):(\d\d):(\d\d)\.\d+\s+-->", line)
        if m:
            ts = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            continue
        text = re.sub(r"<[^>]+>", "", line).strip()
        if not text or ts is None:
            continue
        if text.startswith(("WEBVTT", "Kind:", "Language:")) or text in seen:
            continue
        seen.add(text)
        cues.append((ts, text))
    return cues


def chunk_cues(cues, words_per_chunk: int = WORDS_PER_CHUNK) -> list[tuple[int, str]]:
    """Group cues into ~N-word passages, tagged with the first cue's timestamp."""
    chunks: list[tuple[int, str]] = []
    start, words = None, []
    for ts, text in cues:
        if start is None:
            start = ts
        words.extend(text.split())
        if len(words) >= words_per_chunk:
            chunks.append((start, " ".join(words)))
            start, words = None, []
    if words and start is not None:
        chunks.append((start, " ".join(words)))
    return chunks


def fetch_captions(video_id: str, tmp: Path) -> str | None:
    opts = {
        "quiet": True, "skip_download": True,
        "writesubtitles": True, "writeautomaticsub": True,
        "subtitleslangs": ["en.*"], "subtitlesformat": "vtt",
        "outtmpl": str(tmp / "%(id)s.%(ext)s"),
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    except Exception:
        return None
    files = sorted(tmp.glob(f"{video_id}*.vtt"))
    return files[0].read_text(encoding="utf-8") if files else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="videos per channel (smoke testing)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    channels = channels_from_watch_page()
    print(f"channels: {', '.join(channels)}")

    docs: list[dict] = []
    skipped: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for slug, ch in channels.items():
            try:
                videos = list_channel_videos(ch["url"])
            except Exception as exc:
                print(f"  ! {slug}: channel listing failed ({exc})")
                continue
            if args.limit:
                videos = videos[: args.limit]
            print(f"  {slug}: {len(videos)} videos")

            for v in videos:
                vtt = fetch_captions(v["id"], tmp)
                if not vtt:
                    skipped.append(v["id"])
                    continue
                for start, text in chunk_cues(parse_vtt(vtt)):
                    mm, ss = divmod(start, 60)
                    ref = f"{ch['name']} · {mm}:{ss:02d}"
                    docs.append({
                        "kind": "video",
                        "slug": f"{v['id']}#t={start}",
                        "title": v["title"],
                        "ref": ref,
                        "source": slug,
                        "categories": [],
                        "strength": None,
                        "url": f"https://www.youtube.com/watch?v={v['id']}&t={start}s",
                        "body": text,
                        "embed_text": f"{v['title']} · {ref}\n{text}"[:1800],
                    })

    print(f"\nchunks {len(docs)}, videos skipped (no captions) {len(skipped)}")
    if skipped:
        Path("video-ingest-skipped.json").write_text(json.dumps(skipped, indent=2))
        print("  skipped ids written to video-ingest-skipped.json")

    if args.dry_run or not docs:
        return

    written, unchanged = client.upsert_docs(
        docs,
        client.env("SUPABASE_DB_URL"),
        client.env("SUPABASE_EMBED_URL"),
        client.env("SUPABASE_ANON_KEY"),
    )
    print(f"written {written}, unchanged {unchanged}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test on two videos per channel**

Run: `python build-video-kb.py --limit 2 --dry-run`
Expected: six channel lines, roughly 60–100 chunks, few or no skips.

- [ ] **Step 3: Verify a timestamp deep link actually works**

Take any printed `url` and open it. Expected: YouTube opens at that moment, and the transcript text matches what is said there. If the timestamps are systematically off, `parse_vtt` is misreading cue starts — fix before the full run.

- [ ] **Step 4: Full run**

Run: `python build-video-kb.py`
Expected: ~2,700 videos, ~21,000 chunks, 2–3 hours. Skips are logged, not fatal.

- [ ] **Step 5: Commit**

```bash
git add build-video-kb.py
git commit -m "feat(chatbot): ingest YouTube transcripts as timestamped kb docs"
```

---

### Task 10: The recall fixture — does retrieval actually work?

**Files:**
- Create: `tests/fixtures/retrieval_questions.json`
- Modify: `tests/test_kb_retrieval.py`

**Interfaces:**
- Consumes: `match_corpus()`, `kb_find_ref()` from Task 1; a fully loaded `kb_docs`.

This is the task the whole phase exists for. If retrieval can't find the right material for these questions, nothing downstream matters — and it is far cheaper to learn that here than after the Edge Function and UI are built.

- [ ] **Step 1: Write the fixture**

```json
[
  {
    "q": "Is Allah a father in any sense?",
    "expect_refs": ["Quran 112:3"],
    "expect_kinds": ["verse", "doctrine"],
    "note": "Q112:3 is the load-bearing verse; the doctrine layer supplies eternal generation"
  },
  {
    "q": "Was Jesus a Muslim?",
    "expect_kinds": ["dossier", "entry"],
    "expect_categories": ["jesus"],
    "note": "thematic — no single entry answers it, synthesis across the Jesus cluster"
  },
  {
    "q": "Is the Trinity three gods?",
    "expect_slugs": ["trinity-not-three-gods"],
    "expect_kinds": ["doctrine"]
  },
  {
    "q": "What is the Injeel?",
    "expect_slugs": ["what-is-the-injeel"],
    "expect_kinds": ["doctrine", "dossier"]
  },
  {
    "q": "Is Muhammad prophesied in the Bible? What about the Paraclete?",
    "expect_refs": ["John 14:17"],
    "expect_kinds": ["verse"],
    "note": "cluster D is unanswerable without the Bible indexed"
  },
  {
    "q": "what does Quran 9:5 say",
    "expect_refs": ["Quran 9:5"],
    "expect_kinds": ["verse"],
    "note": "exact-reference lookup, must not be answered semantically"
  },
  {
    "q": "Bukhari 5134",
    "expect_refs": ["Bukhari 5134"],
    "note": "bare reference with no natural language around it"
  },
  {
    "q": "Does the Quran contradict itself about abrogation?",
    "expect_categories": ["abrogation"],
    "expect_kinds": ["entry", "dossier"]
  },
  {
    "q": "Why does the Quran deny the crucifixion?",
    "expect_refs": ["Quran 4:157"],
    "expect_kinds": ["verse", "entry"]
  },
  {
    "q": "al-Zutt",
    "expect_empty": true,
    "note": "Musnad Ahmad, outside the six canonical collections — must return nothing above threshold so the gap flow fires"
  }
]
```

- [ ] **Step 2: Write the failing test**

```python
# append to tests/test_kb_retrieval.py

FIXTURE = ROOT / "tests" / "fixtures" / "retrieval_questions.json"
EMBED_URL = os.environ.get("SUPABASE_EMBED_URL")
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
MIN_SCORE = 0.02


def _embed(text: str) -> str:
    import requests
    r = requests.post(
        EMBED_URL,
        json={"texts": [text]},
        headers={"Authorization": f"Bearer {ANON_KEY}", "content-type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    return "[" + ",".join(str(x) for x in r.json()["embeddings"][0]) + "]"


def _retrieve(cur, question: str) -> list[dict]:
    cur.execute(
        """
        select kind, slug, title, ref, categories, score
        from match_corpus(%s, %s::vector, 20)
        """,
        (question, _embed(question)),
    )
    cols = ["kind", "slug", "title", "ref", "categories", "score"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


@pytest.mark.skipif(not (EMBED_URL and ANON_KEY), reason="embed function env not set")
@pytest.mark.parametrize("case", json.loads(FIXTURE.read_text(encoding="utf-8")),
                         ids=lambda c: c["q"][:40])
def test_retrieval_recall(cur, case):
    rows = _retrieve(cur, case["q"])
    strong = [r for r in rows if r["score"] >= MIN_SCORE]

    if case.get("expect_empty"):
        assert not strong, (
            f"expected nothing above threshold for {case['q']!r}, got "
            f"{[r['title'] for r in strong[:3]]}"
        )
        return

    assert strong, f"no results above threshold for {case['q']!r}"

    for ref in case.get("expect_refs", []):
        assert any(r["ref"] == ref for r in rows), \
            f"{ref!r} missing from results for {case['q']!r}: {[r['ref'] for r in rows[:8]]}"

    for slug in case.get("expect_slugs", []):
        assert any(r["slug"] == slug for r in rows), \
            f"{slug!r} missing for {case['q']!r}"

    for kind in case.get("expect_kinds", []):
        assert any(r["kind"] == kind for r in rows), \
            f"no {kind!r} in results for {case['q']!r}"

    for cat in case.get("expect_categories", []):
        assert any(cat in (r["categories"] or []) for r in rows), \
            f"no result in category {cat!r} for {case['q']!r}"


@pytest.mark.skipif(not (EMBED_URL and ANON_KEY), reason="embed function env not set")
def test_exact_reference_pinning(cur):
    cur.execute("select ref from kb_find_ref(%s)", ("what does Quran 9:5 say",))
    refs = [r[0] for r in cur.fetchall()]
    assert any("9:5" in r for r in refs), f"kb_find_ref missed Quran 9:5, got {refs}"
```

- [ ] **Step 3: Run it**

Run: `pytest tests/test_kb_retrieval.py -v`
Expected on the first run: several failures. **This is the point of the task** — the failures tell you what to fix.

- [ ] **Step 4: Tune retrieval against the failures, not against the fixture**

Read each failure and diagnose before changing anything:

| Symptom | Likely cause | Fix |
|---|---|---|
| Exact-ref questions return thematic results | RRF is fusing but not pinning | Call `kb_find_ref()` first and prepend its rows |
| `al-Zutt` returns results above threshold | `MIN_SCORE` too low | Raise it; record the tuned value in the spec |
| Doctrine docs never surface | Only three exist and they lose on volume | Raise the `doctrine` cap, or accept until more are written |
| Bible verses rank poorly | Interlinear gloss word order (Task 6 note) | Real limitation — record it, don't paper over it |
| Nothing at all returns | Corpus not loaded, or embeddings null | `select count(*) from kb_docs where embedding is null` |

**Do not weaken an assertion to make a test pass.** The fixture encodes what the product must do. If a case is genuinely wrong, change it deliberately and say why in the commit message.

- [ ] **Step 5: Re-run until green**

Run: `pytest tests/test_kb_retrieval.py -v`
Expected: all pass.

- [ ] **Step 6: Record the tuned constants in the spec**

Add to spec §6 the values you actually landed on: `MIN_SCORE`, the per-kind caps, and whether `kb_find_ref()` needed pre-pending. Phase 2's Edge Function must use the same numbers, and it will be written by someone who wasn't here.

- [ ] **Step 7: Commit**

```bash
git add tests/fixtures/retrieval_questions.json tests/test_kb_retrieval.py \
        supabase/chatbot-kb.sql docs/superpowers/specs/2026-07-27-ai-chatbot-design.md
git commit -m "test(chatbot): retrieval recall fixture over real questions"
```

---

## Phase 1 exit criteria

Phase 1 is done when all of these hold:

- [ ] `pytest tests/test_kb_parsers.py` — all pass, no database needed
- [ ] `pytest tests/test_kb_retrieval.py` — all pass against a loaded corpus
- [ ] `select kind, count(*) from kb_docs group by kind` returns roughly: entry 1524, dossier 147, verse ~37300, doctrine 3, video ~21000
- [ ] `select count(*) from kb_docs where embedding is null` returns 0
- [ ] Re-running `build-kb.py` writes 0 rows (idempotent)
- [ ] A sampled video URL opens YouTube at the right moment
- [ ] Tuned retrieval constants are written back into spec §6

**Nothing here has called the Anthropic API or required Supabase Pro.** The go/no-go for Phase 2 is a judgement call on the recall results: if retrieval reliably finds the right material for the fixture questions, the expensive parts are worth building. If it doesn't, fix it here — it is the cheapest place this will ever be fixable.

## Known limitations carried into Phase 2

1. **Bible text is interlinear gloss**, so word order follows Greek and Hebrew. It degrades FTS and embedding quality relative to the Quran's real translation. If Bible recall is poor, the fix is a proper translation source, not a parser change.
2. **Only three doctrine documents exist.** Clusters A–G in spec §7 need roughly 30 more. This is authored content owned by the site author, and the gap-rate metric will prioritise it once live.
3. **Hadith beyond what entries quote is not indexed** (spec §5), and neither are Talmud, Mishnah, Ibn Kathir, Josephus, Enoch or the apocryphal gospels.
4. **Video ingest depends on yt-dlp**, which breaks when YouTube changes. Re-running for new uploads is a manual step.
