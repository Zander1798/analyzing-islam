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
