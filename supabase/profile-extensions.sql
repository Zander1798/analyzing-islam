-- ============================================================
-- Analyzing Islam — Profile extensions: username, avatar, deactivate
-- Paste into: Supabase dashboard -> SQL Editor -> New query -> Run
-- Safe to re-run: every statement uses IF NOT EXISTS / OR REPLACE.
-- Depends on the original schema.sql (profiles + handle_new_user).
-- ============================================================

-- ---------- 1. Extend profiles with username + avatar_url ----------
alter table public.profiles
  add column if not exists username   text,
  add column if not exists avatar_url text;

-- Usernames: lowercase, 3-20 chars, letters/digits/underscore, must start
-- with a letter or digit (no leading underscore). Case-insensitive unique.
do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'profiles_username_format'
  ) then
    alter table public.profiles
      add constraint profiles_username_format
      check (username is null or username ~ '^[a-z0-9][a-z0-9_]{2,19}$');
  end if;
end$$;

create unique index if not exists uq_profiles_username_ci
  on public.profiles (lower(username))
  where username is not null;

-- ---------- 2. Pick up username from signup metadata ----------
-- signUp({ options: { data: { username: "..." } } }) stores the chosen
-- username in auth.users.raw_user_meta_data. The trigger copies it into
-- profiles.username on account creation.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  meta_username text;
begin
  meta_username := nullif(
    lower(trim(coalesce(new.raw_user_meta_data ->> 'username', ''))),
    ''
  );
  -- If the metadata username violates the format constraint, skip it
  -- (the profile row is still created; the user can set one later).
  if meta_username is not null
     and meta_username !~ '^[a-z0-9][a-z0-9_]{2,19}$' then
    meta_username := null;
  end if;

  insert into public.profiles (id, email, username)
  values (new.id, new.email, meta_username)
  on conflict (id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ---------- 3. Self-service account deletion (RPC) ----------
-- Supabase client SDK cannot delete auth.users directly, so expose a
-- SECURITY DEFINER function the signed-in user can call. It deletes
-- *their own* row from auth.users; the existing ON DELETE CASCADE on
-- profiles/bookmarks/notes/builds/shared_builds cleans up the rest.
create or replace function public.delete_current_user()
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
  uid uuid := auth.uid();
begin
  if uid is null then
    raise exception 'not authenticated';
  end if;
  delete from auth.users where id = uid;
end;
$$;

revoke all on function public.delete_current_user() from public;
grant execute on function public.delete_current_user() to authenticated;

-- ---------- 4. Avatars storage bucket ----------
-- Public-read bucket; writes are locked down by RLS below to the owner's
-- own folder (avatars/<user_id>/...).
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true)
on conflict (id) do update
  set public = excluded.public;

-- Anyone (including anon) can read avatar files — they're displayed
-- site-wide, next to posts, shares, the nav, etc.
drop policy if exists "avatars_public_read" on storage.objects;
create policy "avatars_public_read"
  on storage.objects for select
  using (bucket_id = 'avatars');

-- Only the owning user can upload/replace/delete their own files, and
-- only inside the folder named after their uuid.
drop policy if exists "avatars_owner_insert" on storage.objects;
create policy "avatars_owner_insert"
  on storage.objects for insert
  with check (
    bucket_id = 'avatars'
    and auth.uid() is not null
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists "avatars_owner_update" on storage.objects;
create policy "avatars_owner_update"
  on storage.objects for update
  using (
    bucket_id = 'avatars'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists "avatars_owner_delete" on storage.objects;
create policy "avatars_owner_delete"
  on storage.objects for delete
  using (
    bucket_id = 'avatars'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- ---------- 5. Open up profile reads ----------
-- The original schema only lets users see their own profile row, which is
-- fine for private data but blocks showing @usernames and avatars next to
-- other people's shared builds / community posts. Relax SELECT to "any
-- authenticated user can read public-facing profile columns of anyone".
-- (Column-level policies are not supported; anyone can SELECT profiles,
-- but the only columns we ever surface are username, avatar_url, email.
-- email is not sensitive in this product — it's already shown on shares.)
drop policy if exists "profiles_select_own" on public.profiles;
drop policy if exists "profiles_select_any" on public.profiles;
create policy "profiles_select_any"
  on public.profiles for select
  using (true);

-- ---------- 6. Allow users to self-insert / upsert their own row ----------
-- The original schema has no INSERT policy on profiles — rows are created
-- by the handle_new_user trigger (security definer) only. But our client
-- upserts to profiles when the user saves a username or avatar, and an
-- upsert's INSERT leg needs an INSERT policy or it fails with RLS errors
-- whenever a profile row is missing for any reason.
drop policy if exists "profiles_insert_self" on public.profiles;
create policy "profiles_insert_self"
  on public.profiles for insert
  with check (auth.uid() = id);

-- ---------- Done ----------
-- Verify with:
--   select id, email, username, avatar_url from public.profiles limit 5;
--   select id, name, public from storage.buckets where id = 'avatars';
