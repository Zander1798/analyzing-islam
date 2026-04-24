-- ============================================================
-- Analyzing Islam — Fix owner membership
-- Ensures every community's creator is enrolled as a member with role='owner'
-- so that posting, commenting, and sharing work end-to-end from day one.
-- Safe to re-run. Paste into Supabase -> SQL Editor -> Run.
-- ============================================================

-- 1. Backfill: any existing community that is missing its owner membership
--    (e.g. created before the trigger was in place) gets one now.
insert into public.community_members (community_id, user_id, role)
select c.id, c.owner_id, 'owner'
from public.communities c
where not exists (
  select 1 from public.community_members m
  where m.community_id = c.id and m.user_id = c.owner_id
);

-- 2. Re-assert the trigger that auto-enrolls the creator on new inserts.
--    (Idempotent — safe if already present.)
create or replace function public.c_add_owner_member_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.community_members (community_id, user_id, role)
  values (new.id, new.owner_id, 'owner')
  on conflict (community_id, user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists tr_add_owner_member on public.communities;
create trigger tr_add_owner_member
  after insert on public.communities
  for each row execute procedure public.c_add_owner_member_tr();

-- 3. Second-path RLS policy: the community's owner can also insert their
--    own membership row directly from the client. This is a safety net in
--    case the trigger ever misfires (e.g. under a strict session context).
--    The existing policies for public-community self-join and admin-remove
--    remain unchanged.
drop policy if exists "members_insert_owner" on public.community_members;
create policy "members_insert_owner"
  on public.community_members for insert
  with check (
    auth.uid() = user_id
    and exists (
      select 1 from public.communities c
      where c.id = community_id and c.owner_id = auth.uid()
    )
  );

-- 4. Verify:
--    Every community now has an owner member row.
--    Expected: 0 rows returned.
select c.id as community_id, c.slug, c.name
from public.communities c
left join public.community_members m
  on m.community_id = c.id and m.user_id = c.owner_id
where m.user_id is null;
