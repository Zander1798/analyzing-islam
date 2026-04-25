-- ============================================================
-- Analyzing Islam — Profile counter reconciliation
-- Recomputes profiles.post_count / comment_count / friend_count
-- from the source-of-truth tables (community_posts, post_comments,
-- friendships). Triggers in profile-community-extensions.sql and
-- friendships.sql keep these counters live, but if anything ever
-- drifts (manual edits, future trigger changes, restored backups)
-- this function resyncs the affected profiles.
--
-- Usage:
--   select public.recompute_profile_counts();             -- all users
--   select public.recompute_profile_counts('<uuid>');     -- one user
--
-- The function is SECURITY DEFINER so it can update profiles even
-- when called by a non-owner (e.g. an admin or a cron job). Execute
-- is granted to authenticated only — anon never needs to call this.
--
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: schema.sql, community-schema.sql,
--             profile-community-extensions.sql, friendships.sql.
-- ============================================================

-- Self-bootstrap the counter columns. profile-community-extensions.sql
-- adds post_count / comment_count, friendships.sql adds friend_count.
-- We re-declare them here so this script can run standalone — useful
-- when the older migrations haven't been applied yet on a given env.
alter table public.profiles
  add column if not exists post_count    integer not null default 0,
  add column if not exists comment_count integer not null default 0,
  add column if not exists friend_count  integer not null default 0;

create or replace function public.recompute_profile_counts(p_id uuid default null)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  affected integer;
begin
  with target as (
    select id from public.profiles
     where p_id is null or id = p_id
  ),
  post_counts as (
    select t.id, coalesce(count(q.id), 0)::int as n
      from target t
      left join public.community_posts q
        on q.author_id = t.id
       and coalesce(q.is_deleted, false) = false
     group by t.id
  ),
  comment_counts as (
    select t.id, coalesce(count(c.id), 0)::int as n
      from target t
      left join public.post_comments c
        on c.author_id = t.id
       and coalesce(c.is_deleted, false) = false
     group by t.id
  ),
  friend_counts as (
    select t.id, coalesce(count(f.id), 0)::int as n
      from target t
      left join public.friendships f
        on f.status = 'accepted'
       and (f.requester_id = t.id or f.addressee_id = t.id)
     group by t.id
  )
  update public.profiles p
     set post_count    = pc.n,
         comment_count = cc.n,
         friend_count  = fc.n
    from post_counts pc, comment_counts cc, friend_counts fc
   where pc.id = p.id and cc.id = p.id and fc.id = p.id
     and (p.post_count    is distinct from pc.n
       or p.comment_count is distinct from cc.n
       or p.friend_count  is distinct from fc.n);

  get diagnostics affected = row_count;
  return affected;
end;
$$;

revoke all on function public.recompute_profile_counts(uuid) from public;
grant execute on function public.recompute_profile_counts(uuid) to authenticated;

-- One-shot reconciliation for every existing profile. Idempotent —
-- only rows whose stored counters disagree with the recomputed values
-- are updated.
select public.recompute_profile_counts();

-- ---------- Done ----------
-- Verify a single user:
--   select id, username, post_count, comment_count, friend_count
--     from public.profiles where username = 'zandervv';
--   select public.recompute_profile_counts(
--     (select id from public.profiles where username = 'zandervv')
--   );
