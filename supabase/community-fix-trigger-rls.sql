-- ============================================================
-- Analyzing Islam — Fix count/score trigger RLS
-- Why:
--   The denormalised count/score columns (member_count, post_count,
--   comment_count, score) are maintained by AFTER triggers. Those
--   trigger functions were created without SECURITY DEFINER, so their
--   internal UPDATEs run as the calling user. That means when a
--   regular member leaves a community, upvotes a post, or a non-admin
--   otherwise causes a count/score to change, the trigger's UPDATE on
--   `communities` / `community_posts` / `post_comments` is silently
--   blocked by the RLS policy that restricts updates to admins /
--   authors. Result: stale counts (e.g. member_count sticks at 2
--   after someone leaves).
--
-- Fix:
--   Re-create the five count/score trigger functions with
--   SECURITY DEFINER so they run as the function owner and bypass
--   RLS on the denormalised columns they maintain.
--
-- Plus: a one-shot resync at the bottom that rebuilds every cached
--   count from the source of truth (the membership / post / vote /
--   comment rows). Corrects any drift from the old bug.
--
-- Safe to re-run. Paste into Supabase -> SQL Editor -> Run.
-- ============================================================

-- 1. member_count on communities
create or replace function public.cm_member_count_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update public.communities set member_count = member_count + 1 where id = new.community_id;
  elsif tg_op = 'DELETE' then
    update public.communities set member_count = greatest(member_count - 1, 0) where id = old.community_id;
  end if;
  return null;
end;
$$;

-- 2. post_count on communities
create or replace function public.cp_post_count_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update public.communities set post_count = post_count + 1 where id = new.community_id;
  elsif tg_op = 'DELETE' then
    update public.communities set post_count = greatest(post_count - 1, 0) where id = old.community_id;
  end if;
  return null;
end;
$$;

-- 3. score on community_posts (from post_votes)
create or replace function public.pv_score_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update public.community_posts set score = score + new.value where id = new.post_id;
  elsif tg_op = 'DELETE' then
    update public.community_posts set score = score - old.value where id = old.post_id;
  elsif tg_op = 'UPDATE' then
    update public.community_posts set score = score - old.value + new.value where id = new.post_id;
  end if;
  return null;
end;
$$;

-- 4. score on post_comments (from comment_votes)
create or replace function public.cv_score_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update public.post_comments set score = score + new.value where id = new.comment_id;
  elsif tg_op = 'DELETE' then
    update public.post_comments set score = score - old.value where id = old.comment_id;
  elsif tg_op = 'UPDATE' then
    update public.post_comments set score = score - old.value + new.value where id = new.comment_id;
  end if;
  return null;
end;
$$;

-- 5. comment_count on community_posts
create or replace function public.pc_count_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update public.community_posts set comment_count = comment_count + 1 where id = new.post_id;
  elsif tg_op = 'DELETE' then
    update public.community_posts set comment_count = greatest(comment_count - 1, 0) where id = old.post_id;
  end if;
  return null;
end;
$$;

-- ============================================================
-- One-shot resync of every cached count/score. Corrects drift
-- from before the fix. Safe (no-op when already consistent).
-- ============================================================
update public.communities c
   set member_count = coalesce((
         select count(*) from public.community_members m
          where m.community_id = c.id
       ), 0);

update public.communities c
   set post_count = coalesce((
         select count(*) from public.community_posts p
          where p.community_id = c.id and p.is_deleted = false
       ), 0);

update public.community_posts p
   set score = coalesce((
         select sum(v.value) from public.post_votes v
          where v.post_id = p.id
       ), 0);

update public.community_posts p
   set comment_count = coalesce((
         select count(*) from public.post_comments k
          where k.post_id = p.id and k.is_deleted = false
       ), 0);

update public.post_comments k
   set score = coalesce((
         select sum(v.value) from public.comment_votes v
          where v.comment_id = k.id
       ), 0);

-- Verify (optional). Should show matching member counts.
select c.slug, c.member_count as cached,
       (select count(*) from public.community_members m where m.community_id = c.id) as actual
  from public.communities c
  order by c.slug;
