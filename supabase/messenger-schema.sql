-- ============================================================
-- Analyzing Islam — Direct-message schema (messenger)
-- Threads + messages between two accepted friends. RLS keeps every
-- thread / message visible only to its two participants. Creating
-- a thread requires an accepted friendship (enforced via RPC).
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: schema.sql, friendships.sql.
-- ============================================================

-- ---------- 1. direct_threads ----------
-- One row per pair of users. user_a / user_b are always stored
-- sorted (least/greatest) so the pair is canonical and the unique
-- index covers both "A → B" and "B → A" in one row.
create table if not exists public.direct_threads (
  id                     bigserial primary key,
  user_a                 uuid not null references auth.users(id) on delete cascade,
  user_b                 uuid not null references auth.users(id) on delete cascade,
  last_message_at        timestamptz,
  last_message_preview   text,
  last_sender_id         uuid references auth.users(id) on delete set null,
  last_read_by_a         timestamptz,
  last_read_by_b         timestamptz,
  created_at             timestamptz not null default now(),
  constraint direct_threads_distinct check (user_a <> user_b),
  constraint direct_threads_sorted   check (user_a < user_b)
);

create unique index if not exists uq_direct_threads_pair
  on public.direct_threads (user_a, user_b);

create index if not exists idx_direct_threads_user_a on public.direct_threads(user_a);
create index if not exists idx_direct_threads_user_b on public.direct_threads(user_b);
create index if not exists idx_direct_threads_last   on public.direct_threads(last_message_at desc);

-- ---------- 2. direct_messages ----------
-- attachments is a jsonb array of { type: 'image'|'video', url, name, size }
create table if not exists public.direct_messages (
  id           bigserial primary key,
  thread_id    bigint not null references public.direct_threads(id) on delete cascade,
  sender_id    uuid   not null references auth.users(id) on delete cascade,
  body         text   not null default '',
  attachments  jsonb  not null default '[]'::jsonb,
  is_deleted   boolean not null default false,
  created_at   timestamptz not null default now()
);

create index if not exists idx_direct_messages_thread
  on public.direct_messages(thread_id, created_at);
create index if not exists idx_direct_messages_sender
  on public.direct_messages(sender_id);

-- ---------- 3. Row-level security ----------
alter table public.direct_threads  enable row level security;
alter table public.direct_messages enable row level security;

-- Threads: only visible / mutable to the two participants.
drop policy if exists "dm_threads_select_participants" on public.direct_threads;
create policy "dm_threads_select_participants"
  on public.direct_threads for select
  using (auth.uid() = user_a or auth.uid() = user_b);

drop policy if exists "dm_threads_update_participants" on public.direct_threads;
create policy "dm_threads_update_participants"
  on public.direct_threads for update
  using (auth.uid() = user_a or auth.uid() = user_b)
  with check (auth.uid() = user_a or auth.uid() = user_b);

drop policy if exists "dm_threads_delete_participants" on public.direct_threads;
create policy "dm_threads_delete_participants"
  on public.direct_threads for delete
  using (auth.uid() = user_a or auth.uid() = user_b);

-- No direct INSERT policy — thread rows are created by the
-- start_or_get_dm() RPC (security definer) so we can enforce the
-- friendship requirement server-side.

-- Messages: readable only by the two thread participants, writable
-- only by the sender and only if they're a participant.
drop policy if exists "dm_messages_select_participants" on public.direct_messages;
create policy "dm_messages_select_participants"
  on public.direct_messages for select
  using (
    exists (
      select 1 from public.direct_threads t
      where t.id = thread_id
        and (auth.uid() = t.user_a or auth.uid() = t.user_b)
    )
  );

drop policy if exists "dm_messages_insert_sender" on public.direct_messages;
create policy "dm_messages_insert_sender"
  on public.direct_messages for insert
  with check (
    auth.uid() = sender_id
    and exists (
      select 1 from public.direct_threads t
      where t.id = thread_id
        and (auth.uid() = t.user_a or auth.uid() = t.user_b)
    )
  );

-- Sender can soft-delete their own message (set is_deleted = true).
drop policy if exists "dm_messages_update_sender" on public.direct_messages;
create policy "dm_messages_update_sender"
  on public.direct_messages for update
  using (auth.uid() = sender_id)
  with check (auth.uid() = sender_id);

-- ---------- 4. Maintain the thread's "last message" denorm ----------
create or replace function public.dm_thread_touch_last()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.direct_threads
     set last_message_at      = new.created_at,
         last_message_preview = case
           when coalesce(new.body, '') <> '' then left(new.body, 180)
           when jsonb_array_length(coalesce(new.attachments, '[]'::jsonb)) > 0 then '[attachment]'
           else null
         end,
         last_sender_id       = new.sender_id
   where id = new.thread_id;
  return new;
end;
$$;

drop trigger if exists tr_dm_thread_touch_last on public.direct_messages;
create trigger tr_dm_thread_touch_last
  after insert on public.direct_messages
  for each row execute procedure public.dm_thread_touch_last();

-- ---------- 5. start_or_get_dm RPC ----------
-- Given a peer user id, returns the existing thread id or creates
-- a new one. Requires an accepted friendship between caller and
-- peer, so random users can't DM each other cold.
create or replace function public.start_or_get_dm(peer_id uuid)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
  me uuid := auth.uid();
  a  uuid;
  b  uuid;
  tid bigint;
begin
  if me is null then raise exception 'not authenticated'; end if;
  if peer_id is null or peer_id = me then
    raise exception 'peer_id required and must differ from self';
  end if;

  -- Friendship check: accepted in either direction.
  if not exists (
    select 1 from public.friendships f
    where f.status = 'accepted'
      and (
        (f.requester_id = me and f.addressee_id = peer_id)
        or (f.requester_id = peer_id and f.addressee_id = me)
      )
  ) then
    raise exception 'you must be friends with this user to message them';
  end if;

  a := least(me, peer_id);
  b := greatest(me, peer_id);

  select id into tid from public.direct_threads
   where user_a = a and user_b = b limit 1;

  if tid is null then
    insert into public.direct_threads (user_a, user_b)
    values (a, b)
    returning id into tid;
  end if;

  return tid;
end;
$$;

revoke all on function public.start_or_get_dm(uuid) from public;
grant execute on function public.start_or_get_dm(uuid) to authenticated;

-- ---------- 6. Mark-read helper ----------
-- Updates last_read_by_<a|b> for the caller on the given thread.
create or replace function public.dm_mark_read(p_thread_id bigint)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  me uuid := auth.uid();
begin
  if me is null then return; end if;
  update public.direct_threads
     set last_read_by_a = case when user_a = me then now() else last_read_by_a end,
         last_read_by_b = case when user_b = me then now() else last_read_by_b end
   where id = p_thread_id
     and (user_a = me or user_b = me);
end;
$$;

revoke all on function public.dm_mark_read(bigint) from public;
grant execute on function public.dm_mark_read(bigint) to authenticated;

-- ---------- 7. DM attachments storage bucket ----------
-- Public-read; owner-only write scoped to dm-attachments/<uid>/...
insert into storage.buckets (id, name, public)
values ('dm-attachments', 'dm-attachments', true)
on conflict (id) do update set public = excluded.public;

drop policy if exists "dm_attach_public_read"  on storage.objects;
drop policy if exists "dm_attach_owner_insert" on storage.objects;
drop policy if exists "dm_attach_owner_update" on storage.objects;
drop policy if exists "dm_attach_owner_delete" on storage.objects;

create policy "dm_attach_public_read"
  on storage.objects for select
  to public
  using (bucket_id = 'dm-attachments');

create policy "dm_attach_owner_insert"
  on storage.objects for insert
  to authenticated
  with check (
    bucket_id = 'dm-attachments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "dm_attach_owner_update"
  on storage.objects for update
  to authenticated
  using (
    bucket_id = 'dm-attachments'
    and (storage.foldername(name))[1] = auth.uid()::text
  )
  with check (
    bucket_id = 'dm-attachments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "dm_attach_owner_delete"
  on storage.objects for delete
  to authenticated
  using (
    bucket_id = 'dm-attachments'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

notify pgrst, 'reload schema';
