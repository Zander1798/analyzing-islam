-- ============================================================
-- Analyzing Islam — Community profile extensions
-- Adds: bio, banner_url on profiles; a public_profiles view that
-- aggregates post + comment counts; relaxed community_members
-- SELECT RLS so we can render "communities this user is in" on a
-- public profile page; banner storage RLS in the avatars bucket.
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: schema.sql, community-schema.sql, profile-extensions.sql.
-- ============================================================

-- ---------- 1. Extra profile columns ----------
alter table public.profiles
  add column if not exists bio        text,
  add column if not exists banner_url text;

-- Bio: soft cap at 500 chars. Null is allowed.
do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'profiles_bio_length'
  ) then
    alter table public.profiles
      add constraint profiles_bio_length
      check (bio is null or char_length(bio) <= 500);
  end if;
end$$;

-- ---------- 2. profiles.post_count + comment_count ----------
-- Denormalised counters so every viewer sees accurate totals on a
-- public profile page regardless of RLS on the underlying posts /
-- comments tables. The earlier view aggregated via count(*) over
-- community_posts / post_comments, which inherits their RLS — so
-- viewers outside a private community saw 0 for the profile owner's
-- activity there. Triggers maintain these columns alongside the
-- existing community / post counter triggers.
alter table public.profiles
  add column if not exists post_count    integer not null default 0,
  add column if not exists comment_count integer not null default 0;

-- Maintain profiles.post_count from community_posts. Mirrors the
-- logic on community_posts.comment_count: INSERT / DELETE only count
-- when the row is visible (is_deleted = false), and UPDATE handles
-- the soft-delete / restore toggles.
create or replace function public.profiles_post_count_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    if coalesce(new.is_deleted, false) = false and new.author_id is not null then
      update public.profiles set post_count = post_count + 1 where id = new.author_id;
    end if;
  elsif tg_op = 'DELETE' then
    if coalesce(old.is_deleted, false) = false and old.author_id is not null then
      update public.profiles set post_count = greatest(post_count - 1, 0) where id = old.author_id;
    end if;
  elsif tg_op = 'UPDATE' then
    if coalesce(old.is_deleted, false) = false
       and coalesce(new.is_deleted, false) = true
       and old.author_id is not null then
      update public.profiles set post_count = greatest(post_count - 1, 0) where id = old.author_id;
    elsif coalesce(old.is_deleted, false) = true
          and coalesce(new.is_deleted, false) = false
          and new.author_id is not null then
      update public.profiles set post_count = post_count + 1 where id = new.author_id;
    end if;
  end if;
  return null;
end;
$$;

drop trigger if exists tr_profiles_post_count on public.community_posts;
create trigger tr_profiles_post_count
  after insert or update or delete on public.community_posts
  for each row execute procedure public.profiles_post_count_tr();

-- Maintain profiles.comment_count from post_comments — same shape.
create or replace function public.profiles_comment_count_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    if coalesce(new.is_deleted, false) = false and new.author_id is not null then
      update public.profiles set comment_count = comment_count + 1 where id = new.author_id;
    end if;
  elsif tg_op = 'DELETE' then
    if coalesce(old.is_deleted, false) = false and old.author_id is not null then
      update public.profiles set comment_count = greatest(comment_count - 1, 0) where id = old.author_id;
    end if;
  elsif tg_op = 'UPDATE' then
    if coalesce(old.is_deleted, false) = false
       and coalesce(new.is_deleted, false) = true
       and old.author_id is not null then
      update public.profiles set comment_count = greatest(comment_count - 1, 0) where id = old.author_id;
    elsif coalesce(old.is_deleted, false) = true
          and coalesce(new.is_deleted, false) = false
          and new.author_id is not null then
      update public.profiles set comment_count = comment_count + 1 where id = new.author_id;
    end if;
  end if;
  return null;
end;
$$;

drop trigger if exists tr_profiles_comment_count on public.post_comments;
create trigger tr_profiles_comment_count
  after insert or update or delete on public.post_comments
  for each row execute procedure public.profiles_comment_count_tr();

-- One-shot backfill from source of truth. Safe to re-run — it
-- rewrites the counters from the current (visible) row set.
update public.profiles p
   set post_count = coalesce((
         select count(*) from public.community_posts q
          where q.author_id = p.id
            and coalesce(q.is_deleted, false) = false
       ), 0);

update public.profiles p
   set comment_count = coalesce((
         select count(*) from public.post_comments c
          where c.author_id = p.id
            and coalesce(c.is_deleted, false) = false
       ), 0);

-- ---------- 3. public_profiles view ----------
-- Reads the counters straight off profiles, so the numbers no longer
-- depend on the viewer's RLS context. profiles is already select-any
-- via profile-extensions.sql; auth.users.created_at is the original
-- "joined on" timestamp.
--
-- Drop-before-create: the previous revision returned post_count /
-- comment_count as bigint (from count(*)). Now they're integer (from
-- the profiles columns). CREATE OR REPLACE VIEW can't change an
-- existing column's type, so we drop first. Safe because nothing else
-- in the schema depends on this view.
--
-- security_invoker = on: the view runs with the caller's RLS context
-- so it can't bypass base-table policies the way a default
-- (definer-style) view can. Dropping the auth.users join also clears
-- Supabase's "Exposed Auth Users" linter critical — profiles already
-- carries its own created_at seeded at signup, so the join wasn't
-- adding any information.
drop view if exists public.public_profiles;
create view public.public_profiles
  with (security_invoker = on)
  as
select
  p.id,
  p.username,
  p.avatar_url,
  p.banner_url,
  p.bio,
  p.created_at                 as joined_at,
  coalesce(p.post_count, 0)    as post_count,
  coalesce(p.comment_count, 0) as comment_count
from public.profiles p;

grant select on public.public_profiles to anon, authenticated;

-- ---------- 4. community_members: SELECT readable by anyone ----------
-- Needed so a public user profile can show "communities this user
-- is in". Only the fact of membership (community_id, user_id, role,
-- joined_at) becomes public — posts inside private communities
-- remain behind their existing RLS.
drop policy if exists "community_members_select_own_or_admin" on public.community_members;
drop policy if exists "community_members_select_public" on public.community_members;
drop policy if exists "community_members_select_any" on public.community_members;
create policy "community_members_select_any"
  on public.community_members for select
  using (true);

-- ---------- 5. Banner storage ----------
-- Keep everything in the existing avatars bucket — same per-user
-- folder, owner-only write, public read. The file paths we write
-- from the client look like:  <uid>/banner-<ts>.<ext>.
-- The existing avatars_* policies already match <uid>/... so this
-- needs no extra policy work; re-asserted below for clarity.
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true)
on conflict (id) do update set public = excluded.public;

-- ---------- Done ----------
-- Verify:
--   select column_name from information_schema.columns
--    where table_schema='public' and table_name='profiles'
--      and column_name in ('bio','banner_url');
--   select * from public.public_profiles limit 3;
--   select policyname from pg_policies
--    where schemaname='public' and tablename='community_members';
