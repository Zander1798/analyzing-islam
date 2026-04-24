-- ============================================================
-- Analyzing Islam — Community forum schema
-- Paste into: Supabase dashboard -> SQL Editor -> New query -> Run
-- Safe to re-run: every statement uses IF NOT EXISTS / OR REPLACE / ON CONFLICT.
-- Depends on the original schema.sql (profiles, touch_updated_at, builds).
-- ============================================================

-- Lenient/fuzzy search uses trigram similarity. One-time extension enable.
create extension if not exists pg_trgm;

-- ============================================================
-- 1. communities
-- ============================================================
create table if not exists public.communities (
  id           bigserial primary key,
  slug         text not null unique,
  name         text not null,
  description  text default '',
  icon_url     text,
  banner_url   text,
  is_private   boolean not null default false,
  owner_id     uuid not null references auth.users(id) on delete cascade,
  member_count integer not null default 0,
  post_count   integer not null default 0,
  created_at   timestamptz default now(),
  updated_at   timestamptz default now(),
  constraint slug_format check (slug ~ '^[a-z0-9][a-z0-9-]{1,40}$'),
  constraint name_len    check (char_length(name) between 2 and 80)
);

create index if not exists idx_communities_owner        on public.communities (owner_id);
create index if not exists idx_communities_name_trgm    on public.communities using gin (name gin_trgm_ops);
create index if not exists idx_communities_slug_trgm    on public.communities using gin (slug gin_trgm_ops);
create index if not exists idx_communities_desc_trgm    on public.communities using gin (description gin_trgm_ops);
create index if not exists idx_communities_members_desc on public.communities (member_count desc);

drop trigger if exists touch_communities_updated_at on public.communities;
create trigger touch_communities_updated_at
  before update on public.communities
  for each row execute procedure public.touch_updated_at();

-- ============================================================
-- 2. community_members
-- ============================================================
create table if not exists public.community_members (
  community_id bigint not null references public.communities(id) on delete cascade,
  user_id      uuid not null references auth.users(id) on delete cascade,
  role         text not null default 'member' check (role in ('owner','admin','member')),
  joined_at    timestamptz default now(),
  primary key (community_id, user_id)
);

create index if not exists idx_community_members_user on public.community_members (user_id);

-- ============================================================
-- 3. community_join_requests (only used for private communities)
-- ============================================================
create table if not exists public.community_join_requests (
  id           bigserial primary key,
  community_id bigint not null references public.communities(id) on delete cascade,
  user_id      uuid not null references auth.users(id) on delete cascade,
  status       text not null default 'pending' check (status in ('pending','approved','denied','cancelled')),
  message      text,
  created_at   timestamptz default now(),
  decided_at   timestamptz,
  decided_by   uuid references auth.users(id) on delete set null
);

-- Only one open request per (community, user).
create unique index if not exists uq_pending_request
  on public.community_join_requests (community_id, user_id)
  where status = 'pending';

create index if not exists idx_join_requests_community_status
  on public.community_join_requests (community_id, status);

-- ============================================================
-- 4. community_posts
-- ============================================================
create table if not exists public.community_posts (
  id              bigserial primary key,
  community_id    bigint not null references public.communities(id) on delete cascade,
  author_id       uuid not null references auth.users(id) on delete cascade,
  title           text not null,
  body_delta      jsonb not null default '{"ops":[]}'::jsonb,
  body_html       text not null default '',
  build_id        bigint references public.builds(id) on delete set null,
  build_snapshot  jsonb,
  score           integer not null default 0,
  comment_count   integer not null default 0,
  is_deleted      boolean not null default false,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  constraint title_len check (char_length(title) between 1 and 300)
);

create index if not exists idx_community_posts_community    on public.community_posts (community_id, created_at desc);
create index if not exists idx_community_posts_community_top on public.community_posts (community_id, score desc);
create index if not exists idx_community_posts_author       on public.community_posts (author_id);
create index if not exists idx_community_posts_title_trgm   on public.community_posts using gin (title gin_trgm_ops);

drop trigger if exists touch_community_posts_updated_at on public.community_posts;
create trigger touch_community_posts_updated_at
  before update on public.community_posts
  for each row execute procedure public.touch_updated_at();

-- ============================================================
-- 5. post_comments (threaded, depth <= 5)
-- ============================================================
create table if not exists public.post_comments (
  id                bigserial primary key,
  post_id           bigint not null references public.community_posts(id) on delete cascade,
  parent_comment_id bigint references public.post_comments(id) on delete cascade,
  author_id         uuid not null references auth.users(id) on delete cascade,
  body              text not null,
  depth             smallint not null default 0,
  score             integer not null default 0,
  is_deleted        boolean not null default false,
  created_at        timestamptz default now(),
  updated_at        timestamptz default now(),
  constraint body_len  check (char_length(body) between 1 and 10000),
  constraint depth_cap check (depth between 0 and 5)
);

create index if not exists idx_post_comments_post   on public.post_comments (post_id, created_at);
create index if not exists idx_post_comments_parent on public.post_comments (parent_comment_id);

drop trigger if exists touch_post_comments_updated_at on public.post_comments;
create trigger touch_post_comments_updated_at
  before update on public.post_comments
  for each row execute procedure public.touch_updated_at();

-- ============================================================
-- 6. post_votes / comment_votes
-- ============================================================
create table if not exists public.post_votes (
  post_id    bigint not null references public.community_posts(id) on delete cascade,
  user_id    uuid not null references auth.users(id) on delete cascade,
  value      smallint not null check (value in (-1, 1)),
  created_at timestamptz default now(),
  primary key (post_id, user_id)
);

create table if not exists public.comment_votes (
  comment_id bigint not null references public.post_comments(id) on delete cascade,
  user_id    uuid not null references auth.users(id) on delete cascade,
  value      smallint not null check (value in (-1, 1)),
  created_at timestamptz default now(),
  primary key (comment_id, user_id)
);

-- ============================================================
-- 7. community_reports (reactive moderation)
-- ============================================================
create table if not exists public.community_reports (
  id            bigserial primary key,
  community_id  bigint not null references public.communities(id) on delete cascade,
  reporter_id   uuid not null references auth.users(id) on delete cascade,
  post_id       bigint references public.community_posts(id) on delete cascade,
  comment_id    bigint references public.post_comments(id) on delete cascade,
  reason        text not null default 'other' check (reason in ('grotesque','violent','sexual','spam','harassment','other')),
  detail        text,
  status        text not null default 'open' check (status in ('open','dismissed','actioned')),
  created_at    timestamptz default now(),
  constraint must_target_one check ((post_id is not null) <> (comment_id is not null))
);

create index if not exists idx_reports_community_open
  on public.community_reports (community_id)
  where status = 'open';

-- ============================================================
-- 8. Denormalization triggers (keep counts and scores accurate)
-- ============================================================

-- communities.member_count
create or replace function public.cm_member_count_tr()
returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then
    update public.communities set member_count = member_count + 1 where id = new.community_id;
  elsif tg_op = 'DELETE' then
    update public.communities set member_count = greatest(member_count - 1, 0) where id = old.community_id;
  end if;
  return null;
end;
$$;

drop trigger if exists tr_community_member_count on public.community_members;
create trigger tr_community_member_count
  after insert or delete on public.community_members
  for each row execute procedure public.cm_member_count_tr();

-- communities.post_count
create or replace function public.cp_post_count_tr()
returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then
    update public.communities set post_count = post_count + 1 where id = new.community_id;
  elsif tg_op = 'DELETE' then
    update public.communities set post_count = greatest(post_count - 1, 0) where id = old.community_id;
  end if;
  return null;
end;
$$;

drop trigger if exists tr_community_post_count on public.community_posts;
create trigger tr_community_post_count
  after insert or delete on public.community_posts
  for each row execute procedure public.cp_post_count_tr();

-- community_posts.score from post_votes
create or replace function public.pv_score_tr()
returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then
    update public.community_posts set score = score + new.value where id = new.post_id;
  elsif tg_op = 'DELETE' then
    update public.community_posts set score = score - old.value where id = old.post_id;
  elsif tg_op = 'UPDATE' then
    update public.community_posts set score = score - old.value + new.value where id = new.post_id;
  end if;
  return null;
end;
$$;

drop trigger if exists tr_post_vote_score on public.post_votes;
create trigger tr_post_vote_score
  after insert or update or delete on public.post_votes
  for each row execute procedure public.pv_score_tr();

-- post_comments.score from comment_votes
create or replace function public.cv_score_tr()
returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then
    update public.post_comments set score = score + new.value where id = new.comment_id;
  elsif tg_op = 'DELETE' then
    update public.post_comments set score = score - old.value where id = old.comment_id;
  elsif tg_op = 'UPDATE' then
    update public.post_comments set score = score - old.value + new.value where id = new.comment_id;
  end if;
  return null;
end;
$$;

drop trigger if exists tr_comment_vote_score on public.comment_votes;
create trigger tr_comment_vote_score
  after insert or update or delete on public.comment_votes
  for each row execute procedure public.cv_score_tr();

-- community_posts.comment_count — reflects visible (non-soft-deleted)
-- comments so the feed card matches the rendered comment list (which
-- filters is_deleted = false). Fires on INSERT/UPDATE/DELETE so that
-- soft-deletes via UPDATE is_deleted = true are counted too.
create or replace function public.pc_count_tr()
returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then
    if new.is_deleted = false then
      update public.community_posts set comment_count = comment_count + 1 where id = new.post_id;
    end if;
  elsif tg_op = 'DELETE' then
    if old.is_deleted = false then
      update public.community_posts set comment_count = greatest(comment_count - 1, 0) where id = old.post_id;
    end if;
  elsif tg_op = 'UPDATE' then
    if old.is_deleted = false and new.is_deleted = true then
      update public.community_posts set comment_count = greatest(comment_count - 1, 0) where id = new.post_id;
    elsif old.is_deleted = true and new.is_deleted = false then
      update public.community_posts set comment_count = comment_count + 1 where id = new.post_id;
    end if;
  end if;
  return null;
end;
$$;

drop trigger if exists tr_post_comment_count on public.post_comments;
create trigger tr_post_comment_count
  after insert or update or delete on public.post_comments
  for each row execute procedure public.pc_count_tr();

-- post_comments.depth auto-set from parent + hard cap at 5
create or replace function public.pc_depth_tr()
returns trigger language plpgsql as $$
declare
  p_depth smallint;
begin
  if new.parent_comment_id is null then
    new.depth := 0;
  else
    select depth + 1 into p_depth from public.post_comments where id = new.parent_comment_id;
    new.depth := coalesce(p_depth, 1);
    if new.depth > 5 then
      raise exception 'comment nesting exceeds depth cap of 5';
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists tr_comment_depth on public.post_comments;
create trigger tr_comment_depth
  before insert on public.post_comments
  for each row execute procedure public.pc_depth_tr();

-- Auto-enroll creator as owner when a community is created.
create or replace function public.c_add_owner_member_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.community_members (community_id, user_id, role)
  values (new.id, new.owner_id, 'owner')
  on conflict do nothing;
  return new;
end;
$$;

drop trigger if exists tr_add_owner_member on public.communities;
create trigger tr_add_owner_member
  after insert on public.communities
  for each row execute procedure public.c_add_owner_member_tr();

-- When a join request is approved, auto-insert the membership row.
create or replace function public.jr_approved_tr()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.status = 'approved' and (old.status is distinct from 'approved') then
    insert into public.community_members (community_id, user_id, role)
    values (new.community_id, new.user_id, 'member')
    on conflict do nothing;
    new.decided_at := now();
  elsif new.status in ('denied','cancelled') and (old.status is distinct from new.status) then
    new.decided_at := now();
  end if;
  return new;
end;
$$;

drop trigger if exists tr_join_request_approved on public.community_join_requests;
create trigger tr_join_request_approved
  before update on public.community_join_requests
  for each row execute procedure public.jr_approved_tr();

-- ============================================================
-- 9. Helper functions used by RLS policies
-- ============================================================
create or replace function public.is_member(p_community_id bigint, p_user_id uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.community_members
    where community_id = p_community_id and user_id = p_user_id
  );
$$;

create or replace function public.is_community_admin(p_community_id bigint, p_user_id uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.community_members
    where community_id = p_community_id and user_id = p_user_id
      and role in ('owner','admin')
  );
$$;

-- ============================================================
-- 10. Row-Level Security
-- ============================================================
alter table public.communities              enable row level security;
alter table public.community_members        enable row level security;
alter table public.community_join_requests  enable row level security;
alter table public.community_posts          enable row level security;
alter table public.post_comments            enable row level security;
alter table public.post_votes               enable row level security;
alter table public.comment_votes            enable row level security;
alter table public.community_reports        enable row level security;

-- Communities: always discoverable (even private ones show name/banner).
-- Private enforcement is on posts/comments, not the community row.
drop policy if exists "communities_select_all"    on public.communities;
drop policy if exists "communities_insert_authed" on public.communities;
drop policy if exists "communities_update_admin"  on public.communities;
drop policy if exists "communities_delete_owner"  on public.communities;

create policy "communities_select_all"
  on public.communities for select using (true);

create policy "communities_insert_authed"
  on public.communities for insert
  with check (auth.uid() = owner_id);

create policy "communities_update_admin"
  on public.communities for update
  using (public.is_community_admin(id, auth.uid()));

create policy "communities_delete_owner"
  on public.communities for delete
  using (owner_id = auth.uid());

-- Members: readable by anyone (member counts, member list).
drop policy if exists "members_select_all"          on public.community_members;
drop policy if exists "members_insert_self_public"  on public.community_members;
drop policy if exists "members_delete_self_or_admin" on public.community_members;

create policy "members_select_all"
  on public.community_members for select using (true);

-- Direct self-join is only allowed for PUBLIC communities.
-- Private memberships are created by the approved-request trigger (security definer).
create policy "members_insert_self_public"
  on public.community_members for insert
  with check (
    auth.uid() = user_id
    and exists (
      select 1 from public.communities
      where id = community_id and is_private = false
    )
  );

create policy "members_delete_self_or_admin"
  on public.community_members for delete
  using (
    auth.uid() = user_id
    or public.is_community_admin(community_id, auth.uid())
  );

-- Join requests: user sees their own; admins see all for their community.
drop policy if exists "jr_select_own_or_admin" on public.community_join_requests;
drop policy if exists "jr_insert_self"         on public.community_join_requests;
drop policy if exists "jr_update_admin_or_self" on public.community_join_requests;

create policy "jr_select_own_or_admin"
  on public.community_join_requests for select
  using (auth.uid() = user_id or public.is_community_admin(community_id, auth.uid()));

create policy "jr_insert_self"
  on public.community_join_requests for insert
  with check (
    auth.uid() = user_id
    and exists (
      select 1 from public.communities
      where id = community_id and is_private = true
    )
  );

-- Admins approve/deny; the requester themselves can only cancel their own request.
create policy "jr_update_admin_or_self"
  on public.community_join_requests for update
  using (
    public.is_community_admin(community_id, auth.uid())
    or auth.uid() = user_id
  );

-- Posts: visible iff community is public OR viewer is a member.
drop policy if exists "posts_select_visible"      on public.community_posts;
drop policy if exists "posts_insert_member"       on public.community_posts;
drop policy if exists "posts_update_author_or_admin" on public.community_posts;
drop policy if exists "posts_delete_author_or_admin" on public.community_posts;

create policy "posts_select_visible"
  on public.community_posts for select
  using (
    exists (
      select 1 from public.communities c
      where c.id = community_id
        and (c.is_private = false or public.is_member(c.id, auth.uid()))
    )
  );

create policy "posts_insert_member"
  on public.community_posts for insert
  with check (
    auth.uid() = author_id
    and public.is_member(community_id, auth.uid())
  );

create policy "posts_update_author_or_admin"
  on public.community_posts for update
  using (auth.uid() = author_id or public.is_community_admin(community_id, auth.uid()));

create policy "posts_delete_author_or_admin"
  on public.community_posts for delete
  using (auth.uid() = author_id or public.is_community_admin(community_id, auth.uid()));

-- Comments inherit post visibility.
drop policy if exists "comments_select_visible"      on public.post_comments;
drop policy if exists "comments_insert_member"       on public.post_comments;
drop policy if exists "comments_update_author"       on public.post_comments;
drop policy if exists "comments_delete_author_or_admin" on public.post_comments;

create policy "comments_select_visible"
  on public.post_comments for select
  using (
    exists (
      select 1 from public.community_posts p
      join public.communities c on c.id = p.community_id
      where p.id = post_id
        and (c.is_private = false or public.is_member(c.id, auth.uid()))
    )
  );

create policy "comments_insert_member"
  on public.post_comments for insert
  with check (
    auth.uid() = author_id
    and exists (
      select 1 from public.community_posts p
      where p.id = post_id and public.is_member(p.community_id, auth.uid())
    )
  );

create policy "comments_update_author"
  on public.post_comments for update
  using (auth.uid() = author_id);

create policy "comments_delete_author_or_admin"
  on public.post_comments for delete
  using (
    auth.uid() = author_id
    or exists (
      select 1 from public.community_posts p
      where p.id = post_id and public.is_community_admin(p.community_id, auth.uid())
    )
  );

-- Votes: anyone can read aggregate counts; users manage only their own.
drop policy if exists "post_votes_select_any"  on public.post_votes;
drop policy if exists "post_votes_insert_own"  on public.post_votes;
drop policy if exists "post_votes_update_own"  on public.post_votes;
drop policy if exists "post_votes_delete_own"  on public.post_votes;

create policy "post_votes_select_any" on public.post_votes for select using (true);
create policy "post_votes_insert_own" on public.post_votes for insert with check (auth.uid() = user_id);
create policy "post_votes_update_own" on public.post_votes for update using (auth.uid() = user_id);
create policy "post_votes_delete_own" on public.post_votes for delete using (auth.uid() = user_id);

drop policy if exists "comment_votes_select_any"  on public.comment_votes;
drop policy if exists "comment_votes_insert_own"  on public.comment_votes;
drop policy if exists "comment_votes_update_own"  on public.comment_votes;
drop policy if exists "comment_votes_delete_own"  on public.comment_votes;

create policy "comment_votes_select_any" on public.comment_votes for select using (true);
create policy "comment_votes_insert_own" on public.comment_votes for insert with check (auth.uid() = user_id);
create policy "comment_votes_update_own" on public.comment_votes for update using (auth.uid() = user_id);
create policy "comment_votes_delete_own" on public.comment_votes for delete using (auth.uid() = user_id);

-- Reports: any logged-in user can file; only that community's admins can read/act.
drop policy if exists "reports_insert_self"  on public.community_reports;
drop policy if exists "reports_select_admin" on public.community_reports;
drop policy if exists "reports_update_admin" on public.community_reports;

create policy "reports_insert_self"
  on public.community_reports for insert
  with check (auth.uid() = reporter_id);

create policy "reports_select_admin"
  on public.community_reports for select
  using (public.is_community_admin(community_id, auth.uid()));

create policy "reports_update_admin"
  on public.community_reports for update
  using (public.is_community_admin(community_id, auth.uid()));

-- ============================================================
-- 11. Lenient search RPC (trigram similarity)
-- ============================================================
create or replace function public.search_all(q text, lim int default 20)
returns table (
  kind           text,
  id             text,
  title          text,
  subtitle       text,
  community_slug text,
  community_name text,
  score          integer,
  similarity     real
)
language sql stable security invoker set search_path = public as $$
  with communities_hit as (
    select
      'community'::text as kind,
      c.slug::text      as id,
      c.name            as title,
      coalesce(c.description,'') as subtitle,
      c.slug            as community_slug,
      c.name            as community_name,
      c.member_count    as score,
      greatest(
        similarity(c.name, q),
        similarity(c.slug, q),
        similarity(coalesce(c.description,''), q)
      ) as similarity
    from public.communities c
    where c.name % q or c.slug % q or c.description % q
  ),
  posts_hit as (
    select
      'post'::text            as kind,
      p.id::text              as id,
      p.title                 as title,
      left(p.body_html, 200)  as subtitle,
      c.slug                  as community_slug,
      c.name                  as community_name,
      p.score                 as score,
      similarity(p.title, q)  as similarity
    from public.community_posts p
    join public.communities c on c.id = p.community_id
    where p.title % q
      and p.is_deleted = false
      and (c.is_private = false or public.is_member(c.id, auth.uid()))
  )
  select * from (
    select * from communities_hit
    union all
    select * from posts_hit
  ) u
  order by similarity desc, score desc
  limit lim;
$$;

-- ============================================================
-- 12. Storage buckets + policies
-- ============================================================
insert into storage.buckets (id, name, public)
values ('community-icons', 'community-icons', true)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('community-banners', 'community-banners', true)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('community-post-images', 'community-post-images', true)
on conflict (id) do nothing;

-- Anyone can read from these buckets.
drop policy if exists "community_storage_read" on storage.objects;
create policy "community_storage_read"
  on storage.objects for select
  using (bucket_id in ('community-icons','community-banners','community-post-images'));

-- Authenticated user uploads, scoped so path starts with their own user_id
-- (first path segment = auth.uid). This keeps one user from clobbering another
-- user's files.
drop policy if exists "community_storage_upload" on storage.objects;
create policy "community_storage_upload"
  on storage.objects for insert
  with check (
    bucket_id in ('community-icons','community-banners','community-post-images')
    and auth.role() = 'authenticated'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- Owner can delete/update their own objects.
drop policy if exists "community_storage_delete" on storage.objects;
create policy "community_storage_delete"
  on storage.objects for delete
  using (
    bucket_id in ('community-icons','community-banners','community-post-images')
    and owner = auth.uid()
  );

drop policy if exists "community_storage_update" on storage.objects;
create policy "community_storage_update"
  on storage.objects for update
  using (
    bucket_id in ('community-icons','community-banners','community-post-images')
    and owner = auth.uid()
  );

-- ============================================================
-- 13. Seed communities
--     Owner = first existing user in auth.users. If no users yet,
--     this block is a no-op — re-run the file after your first signup.
-- ============================================================
do $$
declare
  seed_owner uuid;
begin
  select id into seed_owner from auth.users order by created_at asc limit 1;
  if seed_owner is null then
    raise notice 'No users found yet — seed block skipped. Re-run this file after you sign up.';
    return;
  end if;

  insert into public.communities (slug, name, description, is_private, owner_id) values
    ('general',          'General Discussion',  'Open discussion for everything site-related.',                         false, seed_owner),
    ('apologetics',      'Apologetics',         'Muslim apologetic responses to entries and counter-replies.',          false, seed_owner),
    ('share-your-build', 'Share Your Build',    'Post your builds, get feedback and critique from other users.',        false, seed_owner),
    ('quran',            'Quran',               'Discussion focused on Quranic passages.',                              false, seed_owner),
    ('hadith',           'Hadith',              'Discussion focused on the canonical Sunni hadith collections.',        false, seed_owner),
    ('ex-muslims',       'Ex-Muslims',          'Personal stories, deconversion, support.',                             false, seed_owner)
  on conflict (slug) do nothing;
end $$;

-- ============================================================
-- Done. Verify with:
--   select slug, name, is_private, member_count, post_count from public.communities;
--   select count(*) from public.community_members;
-- ============================================================
