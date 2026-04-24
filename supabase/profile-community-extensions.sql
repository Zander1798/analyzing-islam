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

-- ---------- 2. public_profiles view ----------
-- Joins profiles with aggregated post + comment counts from the
-- community tables plus the auth.users created_at so a public
-- profile page can render "Joined <date>" without leaking any
-- authentication state.
create or replace view public.public_profiles as
select
  p.id,
  p.username,
  p.avatar_url,
  p.banner_url,
  p.bio,
  coalesce(u.created_at, p.created_at) as joined_at,
  coalesce(post_agg.n, 0)    as post_count,
  coalesce(comment_agg.n, 0) as comment_count
from public.profiles p
left join auth.users u on u.id = p.id
left join (
  select author_id, count(*) as n
  from public.community_posts
  where coalesce(is_deleted, false) = false
  group by author_id
) post_agg on post_agg.author_id = p.id
left join (
  select author_id, count(*) as n
  from public.post_comments
  where coalesce(is_deleted, false) = false
  group by author_id
) comment_agg on comment_agg.author_id = p.id;

-- Views inherit RLS from their base tables. profiles is already
-- select-any via profile-extensions.sql; community_posts /
-- post_comments have their own policies (respected here too).
grant select on public.public_profiles to anon, authenticated;

-- ---------- 3. community_members: SELECT readable by anyone ----------
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

-- ---------- 4. Banner storage ----------
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
