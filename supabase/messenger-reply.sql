-- ============================================================
-- Analyzing Islam — Direct messages: reply-to-message
-- Adds direct_messages.reply_to_id so a DM can quote an older
-- message in the same thread (WhatsApp-style). Constrained so a
-- reply can only point at another message in the same thread —
-- enforced by trigger, since CHECK constraints can't subquery.
--
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: messenger-schema.sql.
-- ============================================================

alter table public.direct_messages
  add column if not exists reply_to_id bigint
    references public.direct_messages(id) on delete set null;

create index if not exists idx_direct_messages_reply_to
  on public.direct_messages(reply_to_id);

-- Enforce same-thread for reply targets. Without this a client
-- could insert a reply_to_id pointing at a message in another
-- thread, which would leak across DM boundaries when the bubble
-- renders the quoted preview.
create or replace function public.dm_reply_same_thread()
returns trigger language plpgsql as $$
declare
  parent_thread bigint;
begin
  if new.reply_to_id is null then return new; end if;
  select thread_id into parent_thread
    from public.direct_messages where id = new.reply_to_id;
  if parent_thread is null then
    new.reply_to_id := null;
    return new;
  end if;
  if parent_thread <> new.thread_id then
    raise exception 'reply_to_id must reference a message in the same thread';
  end if;
  return new;
end;
$$;

drop trigger if exists tr_dm_reply_same_thread on public.direct_messages;
create trigger tr_dm_reply_same_thread
  before insert or update on public.direct_messages
  for each row execute procedure public.dm_reply_same_thread();

notify pgrst, 'reload schema';
