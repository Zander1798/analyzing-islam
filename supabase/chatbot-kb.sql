-- ============================================================
-- Analyzing Islam — chatbot knowledge base (Phase 1, Task 1).
-- Safe to re-run: every statement is idempotent and none seeds data.
--
-- Target: the SELF-HOSTED Postgres on the VPS (pgvector is enabled there).
-- This file is replayed by scripts/vps/stage10a-sync.sh along with the rest
-- of supabase/*.sql, so it must never INSERT — see EXECUTION-PLAN correction
-- #6 for what a seeding "schema" file costs.
-- ============================================================

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

-- ---------- chunks ----------
-- Decision 2026-07-28 (Zander): store chunks in a CHILD table, not as extra
-- kb_docs rows. Driven by the bake-off in docs/migration/CHATBOT-HANDOFF.md —
-- 4x1800-char chunks on gte-small scored R@1 82% / MRR 0.893 against 62% /
-- 0.751 for one bounded embed_text per document, and beat nomic-on-full-
-- documents while staying at vector(384) on this box.
--
-- Child table so that kb_docs keeps ONE row per document: `unique (kind, slug)`
-- still holds, kb_find_ref() still returns whole documents, and title/body/
-- metadata are stored once rather than four times.
--
-- kb_docs.embed_text / kb_docs.embedding are deliberately LEFT IN PLACE. They
-- become unused once ingestion writes chunks, but dropping a populated column
-- is destructive and this file is replayed into production by
-- scripts/vps/stage10a-sync.sh. Retire them in a separate, deliberate migration
-- once chunked retrieval is proven.
create table if not exists public.kb_chunks (
  id         bigserial primary key,
  doc_id     bigint not null references public.kb_docs(id) on delete cascade,
  chunk_ix   int    not null,
  embed_text text   not null,
  embedding  vector(384),
  unique (doc_id, chunk_ix)
);

create index if not exists idx_kb_chunks_doc   on public.kb_chunks (doc_id);
create index if not exists idx_kb_chunks_embed on public.kb_chunks
  using hnsw (embedding vector_cosine_ops);

alter table public.kb_chunks enable row level security;

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
  -- Vector side searches CHUNKS and collapses them to documents, scoring each
  -- document as its BEST chunk — exactly what the bake-off measured.
  --
  -- Three levels, each load-bearing:
  --   inner  ANN over kb_chunks, filters applied HERE, over-fetch 240
  --   middle DISTINCT ON (doc_id) -> the best chunk of each document
  --   outer  re-rank those documents by distance, take 60
  --
  -- The middle level must ORDER BY doc_id first (DISTINCT ON requires it), so
  -- its output is in doc_id order, NOT similarity order. Without the outer
  -- re-rank, row_number() would number documents by id and the fusion step
  -- would silently receive garbage ranks. Do not collapse these two levels.
  --
  -- Filters are inside the ANN, not after it. Applying them to an already-
  -- truncated top-240 could return nothing at all when a narrow filter matches
  -- only documents outside that window — empty results on a legitimate query.
  --
  -- Over-fetches 240 chunks for 60 documents (4 chunks/doc) so a document whose
  -- chunks all rank well cannot crowd the candidate list below what fusion
  -- expects.
  --
  -- VERIFIED ON THE BOX 2026-07-28 against 500 docs / 2000 chunks. The planner
  -- keeps the HNSW index despite the join and the filters — it drives a Nested
  -- Loop *from* idx_kb_chunks_embed into kb_docs_pkey. Three plan shapes checked
  -- (bare ANN, join + null filters, join + real filter): 3/3 index scans, 0
  -- sequential scans of kb_chunks. The over-fetch delivers what it promises:
  -- 240 chunks in, exactly 60 documents out of DISTINCT ON.
  --
  -- On a NARROW filter (5 of 500 documents) the planner deliberately switches
  -- to idx_kb_kind -> idx_kb_chunks_doc and sorts exactly, rather than using
  -- HNSW — and returns all 5. That is the right call (an exact scan of ~20
  -- chunks beats an approximate index search) and it is the case this filter
  -- placement exists to protect: filters inside the ANN, so a narrow filter
  -- cannot come back empty.
  --
  -- Re-verify after the first real ingest — 2000 synthetic vectors are not
  -- 80,000 real ones, and `analyze` matters. If HNSW is ever abandoned on the
  -- broad path, pgvector 0.8+ iterative scans
  -- (`set hnsw.iterative_scan = relaxed_order`) are the intended fix; raising
  -- `hnsw.ef_search` is the cruder one.
  --
  -- Watch out when testing: give every chunk a DISTINCT vector. A generator
  -- that reuses one vector per document makes HNSW return ~148 rows for a
  -- LIMIT 240 and looks exactly like a recall bug. It is a test-data artefact.
  vec as (
    select s.id, row_number() over () as rank
    from (
      select best.id, best.dist
      from (
        select distinct on (c.doc_id) c.doc_id as id, c.dist
        from (
          select c2.doc_id, (c2.embedding <=> q_embedding) as dist
          from kb_chunks c2
          join kb_docs d on d.id = c2.doc_id
          where c2.embedding is not null
            and (filter_kinds is null or d.kind = any(filter_kinds))
            and (filter_cats  is null or d.categories && filter_cats)
          order by c2.embedding <=> q_embedding
          limit 240
        ) c
        order by c.doc_id, c.dist          -- DISTINCT ON needs doc_id first
      ) best
      order by best.dist, best.id          -- re-rank by similarity, not doc_id
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
