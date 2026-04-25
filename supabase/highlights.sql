-- ============================================================
-- Analyzing Islam — Highlights
-- Per-source, per-anchor user highlights with arbitrary colour.
--
-- Anchoring strategy:
--   Every reader on this site gives stable IDs to its smallest
--   navigable unit (s{surah}v{ayah}, h{n}, gen-{c}-{v}, etc.).
--   We anchor each highlight to ONE such id and store the
--   (start_off, end_off) character offsets within that element's
--   plain textContent. A multi-element selection becomes one row
--   per anchor sharing the same `group_id`.
--
-- Run after schema.sql.
-- ============================================================

create table if not exists public.highlights (
  id          bigserial primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  source      text not null,        -- 'quran', 'bukhari', 'bible-jhn', ...
  anchor_id   text not null,        -- 's1v1', 'h1', 'gen-1-1', ...
  start_off   int  not null,
  end_off     int  not null,
  text        text not null,        -- denormalised snippet (the highlight body)
  color       text not null default '#ffeb3b',
  group_id    uuid,                 -- ties multi-anchor selections together; null for singletons
  created_at  timestamptz default now(),
  check (start_off >= 0 and end_off > start_off)
);

create index if not exists idx_highlights_user_source on public.highlights (user_id, source);
create index if not exists idx_highlights_user_anchor on public.highlights (user_id, source, anchor_id);
create index if not exists idx_highlights_group       on public.highlights (group_id) where group_id is not null;

alter table public.highlights enable row level security;

drop policy if exists "highlights_select_own" on public.highlights;
create policy "highlights_select_own"
  on public.highlights for select
  using (auth.uid() = user_id);

drop policy if exists "highlights_insert_own" on public.highlights;
create policy "highlights_insert_own"
  on public.highlights for insert
  with check (auth.uid() = user_id);

drop policy if exists "highlights_update_own" on public.highlights;
create policy "highlights_update_own"
  on public.highlights for update
  using (auth.uid() = user_id);

drop policy if exists "highlights_delete_own" on public.highlights;
create policy "highlights_delete_own"
  on public.highlights for delete
  using (auth.uid() = user_id);
