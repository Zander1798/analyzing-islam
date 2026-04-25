-- ============================================================
-- Analyzing Islam — Realtime publication
-- Adds the tables that drive live UI (messages, posts, comments,
-- friend requests) to Supabase's `supabase_realtime` publication
-- so row INSERT / UPDATE / DELETE events are broadcast to
-- subscribed clients. Without this, postgres_changes channels
-- on these tables receive nothing.
--
-- Paste into Supabase -> SQL Editor -> Run. Safe to re-run.
-- Depends on: schema.sql, community-schema.sql, friendships.sql,
-- messenger-schema.sql.
-- ============================================================

-- Helper: add `tbl` to supabase_realtime publication if it's not
-- already a member. Plain `alter publication ... add table` errors
-- on the second run, hence this guard.
do $$
declare
  t text;
  tables text[] := array[
    'public.direct_messages',
    'public.direct_threads',
    'public.friendships',
    'public.community_posts',
    'public.post_comments'
  ];
begin
  foreach t in array tables loop
    if not exists (
      select 1
        from pg_publication_tables
       where pubname = 'supabase_realtime'
         and schemaname || '.' || tablename = t
    ) then
      execute format('alter publication supabase_realtime add table %s', t);
    end if;
  end loop;
end $$;

notify pgrst, 'reload schema';
