-- ============================================================
-- Analyzing Islam — Quiz progress: add selected_skin
-- Stores which goat skin the user has CHOSEN (not just unlocked),
-- so the selection syncs across devices instead of living only in
-- per-device localStorage. Written by goat-skins.js via the same
-- upsert on conflict(user_id) as the rest of the row.
--
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: quiz-progress.sql.
-- ============================================================

alter table public.quiz_progress
  add column if not exists selected_skin text not null default 'standard';

-- Verify:
--   select user_id, unlocked_level, selected_skin from public.quiz_progress limit 5;
