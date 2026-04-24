-- ============================================================
-- Analyzing Islam — Friendships
-- One row per friend request / accepted friendship between two users.
-- requester_id  = whoever clicked "Add friend"
-- addressee_id  = recipient (can accept / decline)
-- status        = pending | accepted | declined
-- Deleting the row covers cancel / decline / unfriend. A declined row
-- is kept briefly so the requester sees the outcome; unfriend just
-- removes the row outright.
--
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: schema.sql.
-- ============================================================

create table if not exists public.friendships (
  id             bigserial primary key,
  requester_id   uuid not null references auth.users(id) on delete cascade,
  addressee_id   uuid not null references auth.users(id) on delete cascade,
  status         text not null default 'pending'
                 check (status in ('pending','accepted','declined')),
  created_at     timestamptz not null default now(),
  decided_at     timestamptz,
  constraint friendships_distinct_parties check (requester_id <> addressee_id)
);

-- At most one pairing between any two users, regardless of direction.
create unique index if not exists uq_friendships_pair
  on public.friendships (least(requester_id, addressee_id), greatest(requester_id, addressee_id));

create index if not exists idx_friendships_requester on public.friendships(requester_id);
create index if not exists idx_friendships_addressee on public.friendships(addressee_id);

alter table public.friendships enable row level security;

drop policy if exists "friendships_select_involved" on public.friendships;
drop policy if exists "friendships_insert_self"    on public.friendships;
drop policy if exists "friendships_update_involved" on public.friendships;
drop policy if exists "friendships_delete_involved" on public.friendships;

-- Both parties can read the row (so each sees the friendship status).
create policy "friendships_select_involved"
  on public.friendships for select
  using (auth.uid() = requester_id or auth.uid() = addressee_id);

-- Only the requester can create a pending row, and only about someone
-- else. The unique pair index prevents duplicate pairings in either
-- direction.
create policy "friendships_insert_self"
  on public.friendships for insert
  with check (
    auth.uid() = requester_id
    and requester_id <> addressee_id
    and status = 'pending'
  );

-- Addressee accepts/declines; requester can't mutate their own request
-- beyond pending (they cancel via delete).
create policy "friendships_update_involved"
  on public.friendships for update
  using (auth.uid() = addressee_id)
  with check (auth.uid() = addressee_id and status in ('accepted','declined'));

-- Either party can remove the row (cancel pending, unfriend, clear a
-- declined record).
create policy "friendships_delete_involved"
  on public.friendships for delete
  using (auth.uid() = requester_id or auth.uid() = addressee_id);

-- ============================================================
-- Friend counter on profiles — kept in sync via triggers so every
-- viewer sees an accurate count without a per-request aggregation.
-- Only accepted friendships count. Pending / declined rows don't
-- contribute. Same denormalised-counter pattern used for
-- profiles.post_count and profiles.comment_count.
-- ============================================================

alter table public.profiles
  add column if not exists friend_count integer not null default 0;

create or replace function public.friendships_count_tr()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  was_accepted boolean;
  now_accepted boolean;
begin
  if tg_op = 'INSERT' then
    if new.status = 'accepted' then
      update public.profiles set friend_count = friend_count + 1 where id = new.requester_id;
      update public.profiles set friend_count = friend_count + 1 where id = new.addressee_id;
    end if;
  elsif tg_op = 'DELETE' then
    if old.status = 'accepted' then
      update public.profiles set friend_count = greatest(friend_count - 1, 0) where id = old.requester_id;
      update public.profiles set friend_count = greatest(friend_count - 1, 0) where id = old.addressee_id;
    end if;
  elsif tg_op = 'UPDATE' then
    was_accepted := old.status = 'accepted';
    now_accepted := new.status = 'accepted';
    if was_accepted and not now_accepted then
      update public.profiles set friend_count = greatest(friend_count - 1, 0) where id = new.requester_id;
      update public.profiles set friend_count = greatest(friend_count - 1, 0) where id = new.addressee_id;
    elsif now_accepted and not was_accepted then
      update public.profiles set friend_count = friend_count + 1 where id = new.requester_id;
      update public.profiles set friend_count = friend_count + 1 where id = new.addressee_id;
    end if;
  end if;
  return null;
end;
$$;

drop trigger if exists tr_friendships_count on public.friendships;
create trigger tr_friendships_count
  after insert or update or delete on public.friendships
  for each row execute procedure public.friendships_count_tr();

-- One-shot backfill from source of truth. Safe to re-run.
update public.profiles p
   set friend_count = coalesce((
         select count(*) from public.friendships f
          where f.status = 'accepted'
            and (f.requester_id = p.id or f.addressee_id = p.id)
       ), 0);

-- Refresh public_profiles to expose friend_count alongside the other
-- denormalised counters. Drop-before-create because the view's column
-- list is changing — CREATE OR REPLACE VIEW can't add a trailing column
-- if anything else depends on the existing shape.
drop view if exists public.public_profiles;
create view public.public_profiles as
select
  p.id,
  p.username,
  p.avatar_url,
  p.banner_url,
  p.bio,
  coalesce(u.created_at, p.created_at) as joined_at,
  coalesce(p.post_count, 0)    as post_count,
  coalesce(p.comment_count, 0) as comment_count,
  coalesce(p.friend_count, 0)  as friend_count
from public.profiles p
left join auth.users u on u.id = p.id;

grant select on public.public_profiles to anon, authenticated;
