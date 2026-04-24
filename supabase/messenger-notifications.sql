-- ============================================================
-- Analyzing Islam — Messenger notifications
-- Adds a per-friendship "addressee_seen_at" timestamp so the red
-- notification badge on the Messages tab can count only friend
-- requests the recipient hasn't looked at yet. Opening the Requests
-- panel calls mark_incoming_requests_seen() which sets the stamp on
-- all still-pending rows for the caller.
--
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: friendships.sql.
-- ============================================================

alter table public.friendships
  add column if not exists addressee_seen_at timestamptz;

create index if not exists idx_friendships_addressee_unseen
  on public.friendships (addressee_id)
  where status = 'pending' and addressee_seen_at is null;

-- Mark every pending friend request addressed to the caller as seen.
-- SECURITY DEFINER bypasses the strict friendships_update_involved
-- policy (which only permits status flips to accepted/declined) so
-- we can touch the timestamp without changing the request state.
create or replace function public.mark_incoming_requests_seen()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  me uuid := auth.uid();
  n  integer;
begin
  if me is null then return 0; end if;
  update public.friendships
     set addressee_seen_at = now()
   where addressee_id = me
     and status = 'pending'
     and addressee_seen_at is null;
  get diagnostics n = row_count;
  return coalesce(n, 0);
end;
$$;

revoke all on function public.mark_incoming_requests_seen() from public;
grant execute on function public.mark_incoming_requests_seen() to authenticated;

notify pgrst, 'reload schema';
