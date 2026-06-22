-- 1. Seed two fake pageviews + a search, then check aggregates as the table owner.
insert into public.pageviews(path, referrer_host, visitor, device)
  values ('/catalog.html','google.com','v1','desktop'),
         ('/catalog.html','','v2','mobile');
insert into public.search_queries(q, source) values ('aisha','catalog');

-- These run as the SQL-editor superuser (bypasses the gate via owner rights on
-- the definer functions is NOT triggered here — call them to confirm they exist):
select public.creator_kpis();                      -- expect json with pageviews.d30 >= 2
select * from public.creator_top_pages(30, 5);      -- expect /catalog.html with views=2, uniques=2
select * from public.creator_top_referrers(30, 5);  -- expect google.com=1, (direct)=1
select * from public.creator_top_searches(30, 5);   -- expect aisha=1

-- 2. Gate check: simulate a non-admin. In Supabase, create a throwaway user,
--    sign in as them in the JS client, and call rpc('creator_kpis') — expect a
--    403/"forbidden". (Documented manual step; see Task 7 for the scripted check.)

-- 3. Cleanup the seed rows:
delete from public.pageviews where visitor in ('v1','v2');
delete from public.search_queries where q = 'aisha';
