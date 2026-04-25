-- ============================================================
-- Analyzing Islam — Community counter reconciliation
-- Two pieces:
--   1. Patch communities.post_count trigger so soft-deletes /
--      restores (UPDATE is_deleted) keep the count accurate. The
--      original cp_post_count_tr only fired on INSERT/DELETE, so a
--      soft-deleted post was still counted in About-Community ->
--      Posts even though the post list filtered it out.
--   2. recompute_community_counts() — resyncs member_count and
--      post_count from source-of-truth (community_members,
--      community_posts where is_deleted = false). Mirrors the
--      profile-counts reconciler so any drift can be cleaned up.
--
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: community-schema.sql.
-- ============================================================

-- ---------- 1. Soft-delete-aware post_count trigger ----------
create or replace function public.cp_post_count_tr()
returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then
    if coalesce(new.is_deleted, false) = false then
      update public.communities
         set post_count = post_count + 1
       where id = new.community_id;
    end if;
  elsif tg_op = 'DELETE' then
    if coalesce(old.is_deleted, false) = false then
      update public.communities
         set post_count = greatest(post_count - 1, 0)
       where id = old.community_id;
    end if;
  elsif tg_op = 'UPDATE' then
    if coalesce(old.is_deleted, false) = false
       and coalesce(new.is_deleted, false) = true then
      update public.communities
         set post_count = greatest(post_count - 1, 0)
       where id = old.community_id;
    elsif coalesce(old.is_deleted, false) = true
          and coalesce(new.is_deleted, false) = false then
      update public.communities
         set post_count = post_count + 1
       where id = new.community_id;
    end if;
  end if;
  return null;
end;
$$;

drop trigger if exists tr_community_post_count on public.community_posts;
create trigger tr_community_post_count
  after insert or update or delete on public.community_posts
  for each row execute procedure public.cp_post_count_tr();

-- ---------- 2. Reconciliation function ----------
create or replace function public.recompute_community_counts(p_id bigint default null)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  affected integer;
begin
  with target as (
    select id from public.communities
     where p_id is null or id = p_id
  ),
  member_counts as (
    select t.id, coalesce(count(m.user_id), 0)::int as n
      from target t
      left join public.community_members m on m.community_id = t.id
     group by t.id
  ),
  post_counts as (
    select t.id, coalesce(count(q.id), 0)::int as n
      from target t
      left join public.community_posts q
        on q.community_id = t.id
       and coalesce(q.is_deleted, false) = false
     group by t.id
  )
  update public.communities c
     set member_count = mc.n,
         post_count   = pc.n
    from member_counts mc, post_counts pc
   where mc.id = c.id and pc.id = c.id
     and (c.member_count is distinct from mc.n
       or c.post_count   is distinct from pc.n);

  get diagnostics affected = row_count;
  return affected;
end;
$$;

revoke all on function public.recompute_community_counts(bigint) from public;
grant execute on function public.recompute_community_counts(bigint) to authenticated;

-- One-shot reconciliation for every community. Picks up any drift
-- left over from the pre-patch trigger that ignored soft-deletes.
select public.recompute_community_counts();

-- ---------- Done ----------
-- Verify:
--   select id, slug, member_count, post_count from public.communities
--    where slug = 'general';
--   select public.recompute_community_counts(
--     (select id from public.communities where slug = 'general')
--   );
