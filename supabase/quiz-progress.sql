-- ============================================================
-- Analyzing Islam — Quiz progress
-- One row per user: the highest unlocked quiz level and the set of
-- goat skin IDs the user has earned. Written by goat-skins.js via
-- upsert on conflict(user_id).
--
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: schema.sql (touch_updated_at).
-- ============================================================

create table if not exists public.quiz_progress (
  user_id        uuid primary key references auth.users(id) on delete cascade,
  unlocked_level integer  not null default 1,
  unlocked_skins text[]   not null default '{standard}',
  updated_at     timestamptz not null default now()
);

drop trigger if exists touch_quiz_progress_updated_at on public.quiz_progress;
create trigger touch_quiz_progress_updated_at
  before update on public.quiz_progress
  for each row execute procedure public.touch_updated_at();

alter table public.quiz_progress enable row level security;

drop policy if exists "quiz_progress_select_own" on public.quiz_progress;
create policy "quiz_progress_select_own"
  on public.quiz_progress for select
  using (auth.uid() = user_id);

drop policy if exists "quiz_progress_insert_own" on public.quiz_progress;
create policy "quiz_progress_insert_own"
  on public.quiz_progress for insert
  with check (auth.uid() = user_id);

drop policy if exists "quiz_progress_update_own" on public.quiz_progress;
create policy "quiz_progress_update_own"
  on public.quiz_progress for update
  using (auth.uid() = user_id);

drop policy if exists "quiz_progress_delete_own" on public.quiz_progress;
create policy "quiz_progress_delete_own"
  on public.quiz_progress for delete
  using (auth.uid() = user_id);

-- Verify:
--   select * from public.quiz_progress limit 5;
