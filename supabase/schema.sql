-- ============================================================
-- Analyzing Islam — Supabase schema for Phase 2
-- Paste this whole file into: Supabase dashboard → SQL Editor → New query → Run
-- Safe to re-run: all statements use IF NOT EXISTS / OR REPLACE.
-- ============================================================

-- ---------- 1. profiles table (1-to-1 with auth.users) ----------
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  display_name text,
  created_at timestamptz default now()
);

-- Auto-create a profile row when a new auth.user is created.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ---------- 2. bookmarks table ----------
-- entry_id is the stable HTML id of a catalog entry (e.g.,
-- "dihya-pattern-homoerotic-reading"). We denormalise title, ref,
-- source, strength, categories so the saved-entries page can filter
-- and render without re-fetching the catalog HTML.
create table if not exists public.bookmarks (
  id          bigserial primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  entry_id    text not null,
  entry_title text,
  entry_ref   text,       -- e.g., "Quran 4:34" or "Bukhari 2749"
  entry_url   text,       -- deep link back to the catalog page + anchor
  source      text,       -- e.g., "quran", "bukhari", "muslim", ...
  strength    text,       -- "basic" | "moderate" | "strong"
  categories  text[] default '{}',
  created_at  timestamptz default now(),
  unique (user_id, entry_id)
);

create index if not exists idx_bookmarks_user on public.bookmarks (user_id);
create index if not exists idx_bookmarks_user_source on public.bookmarks (user_id, source);
create index if not exists idx_bookmarks_user_strength on public.bookmarks (user_id, strength);

-- ---------- 3. notes table ----------
create table if not exists public.notes (
  id          bigserial primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  entry_id    text not null,
  content     text not null default '',
  updated_at  timestamptz default now(),
  unique (user_id, entry_id)
);

create index if not exists idx_notes_user on public.notes (user_id);

-- Keep updated_at fresh automatically.
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists touch_notes_updated_at on public.notes;
create trigger touch_notes_updated_at
  before update on public.notes
  for each row execute procedure public.touch_updated_at();

-- ---------- 4. Row-Level Security ----------
alter table public.profiles  enable row level security;
alter table public.bookmarks enable row level security;
alter table public.notes     enable row level security;

-- Profiles: users can see and edit their own row only.
drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
  on public.profiles for select
  using (auth.uid() = id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
  on public.profiles for update
  using (auth.uid() = id);

-- Bookmarks: users CRUD their own rows only.
drop policy if exists "bookmarks_select_own" on public.bookmarks;
create policy "bookmarks_select_own"
  on public.bookmarks for select
  using (auth.uid() = user_id);

drop policy if exists "bookmarks_insert_own" on public.bookmarks;
create policy "bookmarks_insert_own"
  on public.bookmarks for insert
  with check (auth.uid() = user_id);

drop policy if exists "bookmarks_update_own" on public.bookmarks;
create policy "bookmarks_update_own"
  on public.bookmarks for update
  using (auth.uid() = user_id);

drop policy if exists "bookmarks_delete_own" on public.bookmarks;
create policy "bookmarks_delete_own"
  on public.bookmarks for delete
  using (auth.uid() = user_id);

-- Notes: same — users CRUD their own rows only.
drop policy if exists "notes_select_own" on public.notes;
create policy "notes_select_own"
  on public.notes for select
  using (auth.uid() = user_id);

drop policy if exists "notes_insert_own" on public.notes;
create policy "notes_insert_own"
  on public.notes for insert
  with check (auth.uid() = user_id);

drop policy if exists "notes_update_own" on public.notes;
create policy "notes_update_own"
  on public.notes for update
  using (auth.uid() = user_id);

drop policy if exists "notes_delete_own" on public.notes;
create policy "notes_delete_own"
  on public.notes for delete
  using (auth.uid() = user_id);

-- Done. Confirm by running:
--   select * from public.bookmarks;    -- returns 0 rows for now
--   select * from public.notes;        -- returns 0 rows for now
