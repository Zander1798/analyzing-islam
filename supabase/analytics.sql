-- ============================================================
-- Analyzing Islam — Creator analytics
-- Paste into Supabase → SQL Editor → Run. Safe to re-run.
-- Depends on: schema.sql (profiles, bookmarks, notes, builds, shared_builds),
-- highlights.sql, quiz-progress.sql.
-- ============================================================

-- ---------- admins ----------
create table if not exists public.admins (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);
alter table public.admins enable row level security;
-- No policies: clients can neither read nor write admins (only service role /
-- SQL editor can). is_creator() is SECURITY DEFINER so it still sees the rows.

create or replace function public.is_creator()
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select exists (select 1 from public.admins where user_id = auth.uid());
$$;
revoke all on function public.is_creator() from public;
grant execute on function public.is_creator() to anon, authenticated;

-- ---------- pageviews ----------
create table if not exists public.pageviews (
  id            bigserial primary key,
  path          text not null,
  referrer_host text,
  visitor       text,
  device        text,
  user_id       uuid,
  ts            timestamptz not null default now()
);
create index if not exists idx_pageviews_ts        on public.pageviews (ts);
create index if not exists idx_pageviews_ts_path    on public.pageviews (ts, path);
create index if not exists idx_pageviews_ts_visitor on public.pageviews (ts, visitor);
alter table public.pageviews enable row level security;

drop policy if exists "pageviews_insert_any" on public.pageviews;
create policy "pageviews_insert_any"
  on public.pageviews for insert
  with check (true);
-- No SELECT policy → no client can read raw rows. RPCs (definer) read them.

-- ---------- search_queries ----------
create table if not exists public.search_queries (
  id     bigserial primary key,
  q      text not null,
  source text,
  ts     timestamptz not null default now()
);
create index if not exists idx_search_queries_ts on public.search_queries (ts);
alter table public.search_queries enable row level security;

drop policy if exists "search_queries_insert_any" on public.search_queries;
create policy "search_queries_insert_any"
  on public.search_queries for insert
  with check (true);

-- ---------- gated RPCs ----------
create or replace function public.creator_kpis()
returns json
language plpgsql
security definer
set search_path = public
as $$
declare
  result json;
begin
  if not public.is_creator() then
    raise exception 'forbidden' using errcode = '42501';
  end if;
  select json_build_object(
    'pageviews', json_build_object(
      'today',     (select count(*) from pageviews where ts >= date_trunc('day', now())),
      'yesterday', (select count(*) from pageviews where ts >= date_trunc('day', now()) - interval '1 day' and ts < date_trunc('day', now())),
      'd7',        (select count(*) from pageviews where ts >= now() - interval '7 days'),
      'd30',       (select count(*) from pageviews where ts >= now() - interval '30 days')
    ),
    'uniques', json_build_object(
      'today',     (select count(distinct visitor) from pageviews where ts >= date_trunc('day', now())),
      'yesterday', (select count(distinct visitor) from pageviews where ts >= date_trunc('day', now()) - interval '1 day' and ts < date_trunc('day', now())),
      'd7',        (select count(distinct visitor) from pageviews where ts >= now() - interval '7 days'),
      'd30',       (select count(distinct visitor) from pageviews where ts >= now() - interval '30 days')
    ),
    'signups', json_build_object(
      'today',     (select count(*) from profiles where created_at >= date_trunc('day', now())),
      'yesterday', (select count(*) from profiles where created_at >= date_trunc('day', now()) - interval '1 day' and created_at < date_trunc('day', now())),
      'd7',        (select count(*) from profiles where created_at >= now() - interval '7 days'),
      'd30',       (select count(*) from profiles where created_at >= now() - interval '30 days')
    ),
    'total_users', (select count(*) from profiles),
    'conversion_30d', (
      select case when u = 0 then 0 else round(s::numeric / u, 4) end
      from (
        select (select count(distinct visitor) from pageviews where ts >= now() - interval '30 days') as u,
               (select count(*) from profiles where created_at >= now() - interval '30 days') as s
      ) t
    )
  ) into result;
  return result;
end;
$$;

create or replace function public.creator_traffic_daily(days int default 30)
returns table(day date, views bigint, uniques bigint)
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_creator() then raise exception 'forbidden' using errcode='42501'; end if;
  return query
    select d::date as day,
           coalesce(count(p.id), 0) as views,
           coalesce(count(distinct p.visitor), 0) as uniques
    from generate_series(date_trunc('day', now()) - ((days - 1) || ' days')::interval,
                         date_trunc('day', now()), '1 day') d
    left join pageviews p on date_trunc('day', p.ts) = d
    group by d order by d;
end; $$;

create or replace function public.creator_signups_daily(days int default 30)
returns table(day date, signups bigint)
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_creator() then raise exception 'forbidden' using errcode='42501'; end if;
  return query
    select d::date as day, coalesce(count(pr.id), 0) as signups
    from generate_series(date_trunc('day', now()) - ((days - 1) || ' days')::interval,
                         date_trunc('day', now()), '1 day') d
    left join profiles pr on date_trunc('day', pr.created_at) = d
    group by d order by d;
end; $$;

create or replace function public.creator_top_pages(days int default 7, lim int default 20)
returns table(path text, views bigint, uniques bigint)
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_creator() then raise exception 'forbidden' using errcode='42501'; end if;
  return query
    select p.path, count(*) as views, count(distinct p.visitor) as uniques
    from pageviews p where p.ts >= now() - (days || ' days')::interval
    group by p.path order by views desc limit lim;
end; $$;

create or replace function public.creator_top_referrers(days int default 7, lim int default 20)
returns table(referrer_host text, views bigint)
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_creator() then raise exception 'forbidden' using errcode='42501'; end if;
  return query
    select coalesce(nullif(p.referrer_host, ''), '(direct)') as referrer_host, count(*) as views
    from pageviews p where p.ts >= now() - (days || ' days')::interval
    group by 1 order by views desc limit lim;
end; $$;

create or replace function public.creator_device_split(days int default 7)
returns table(device text, views bigint)
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_creator() then raise exception 'forbidden' using errcode='42501'; end if;
  return query
    select coalesce(nullif(p.device, ''), 'unknown') as device, count(*) as views
    from pageviews p where p.ts >= now() - (days || ' days')::interval
    group by 1 order by views desc;
end; $$;

create or replace function public.creator_engagement()
returns json
language plpgsql security definer set search_path = public as $$
declare result json;
begin
  if not public.is_creator() then raise exception 'forbidden' using errcode='42501'; end if;
  select json_build_object(
    'bookmarks',     (select count(*) from bookmarks),
    'notes',         (select count(*) from notes),
    'builds',        (select count(*) from builds),
    'shared_builds', (select count(*) from shared_builds),
    'highlights',    (select count(*) from highlights),
    'goat_unlocks',  (select coalesce(sum(coalesce(array_length(unlocked_skins,1),0)),0) from quiz_progress),
    'quiz_users',    (select count(*) from quiz_progress)
  ) into result;
  return result;
end; $$;

create or replace function public.creator_top_bookmarked(lim int default 20)
returns table(entry_id text, entry_title text, count bigint)
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_creator() then raise exception 'forbidden' using errcode='42501'; end if;
  return query
    select b.entry_id, max(b.entry_title) as entry_title, count(*) as count
    from bookmarks b group by b.entry_id order by count desc limit lim;
end; $$;

create or replace function public.creator_top_searches(days int default 30, lim int default 20)
returns table(q text, count bigint)
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_creator() then raise exception 'forbidden' using errcode='42501'; end if;
  return query
    select lower(trim(s.q)) as q, count(*) as count
    from search_queries s
    where s.ts >= now() - (days || ' days')::interval and length(trim(s.q)) > 0
    group by 1 order by count desc limit lim;
end; $$;

-- Lock down execute: only logged-in users may call (RPC body still gates to admin).
revoke all on function public.creator_kpis(), public.creator_traffic_daily(int),
  public.creator_signups_daily(int), public.creator_top_pages(int,int),
  public.creator_top_referrers(int,int), public.creator_device_split(int),
  public.creator_engagement(), public.creator_top_bookmarked(int),
  public.creator_top_searches(int,int) from public;
grant execute on function public.creator_kpis(), public.creator_traffic_daily(int),
  public.creator_signups_daily(int), public.creator_top_pages(int,int),
  public.creator_top_referrers(int,int), public.creator_device_split(int),
  public.creator_engagement(), public.creator_top_bookmarked(int),
  public.creator_top_searches(int,int) to authenticated;
