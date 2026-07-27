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
