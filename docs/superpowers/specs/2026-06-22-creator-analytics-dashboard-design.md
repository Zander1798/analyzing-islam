# Creator-only analytics dashboard — design

**Date:** 2026-06-22
**Status:** Approved (pending spec review)

## Goal

A private dashboard tab, accessible only to the site creator, giving an always-current
review of how the Analyzing Islam site is doing: traffic, sign-up growth, feature
engagement, and content insights. Same dark site styling. No one but the creator can
see the tab **or** the underlying numbers.

## Decisions (from brainstorming)

- **Traffic capture:** self-hosted beacon → Supabase (all data in one place, private, free).
- **Metric groups:** all four — Traffic, Growth & sign-ups, Engagement, Content insights.
- **Freshness:** always live on open (date-bucketed cards + daily trend charts). A nightly
  roll-up is explicitly out of scope for v1.
- **Charts:** hand-rolled inline SVG/CSS (no external dependency; matches the site's
  vanilla-JS, framework-free style).
- **Admin identity:** membership in an `admins` table, seeded by the creator with the
  email they signed up to the site with (creator runs a one-line SQL; the email never has
  to be guessed here).

## Architecture

### 1. Access control — the "only me" guarantee

Two layers; the second is the real one.

- **Server-side (the actual guarantee).** New `public.admins` table holds admin user ids.
  A `SECURITY DEFINER` function `public.is_creator()` returns whether `auth.uid()` is in it.
  Every analytics read is a `SECURITY DEFINER` RPC that begins with
  `if not is_creator() then raise exception 'forbidden' using errcode = '42501'; end if;`
  The raw `pageviews` / `search_queries` tables have **no public SELECT** — they are read
  only through these gated RPCs. Result: even if a non-admin loads `admin.html` or calls an
  RPC directly, they get `forbidden` and zero data.
- **Client-side (convenience only).** `is_creator()` is also callable as a normal RPC that
  returns the *caller's own* admin status (safe — it reveals nothing about others). The
  account dropdown adds a "Dashboard" link only when that returns true; `admin.html`
  redirects non-admins to the home page on load. This is UX, not security.

Seeding (creator runs once in Supabase SQL editor, pasting their site email):
```sql
insert into public.admins (user_id)
select id from auth.users where email = 'YOUR_SITE_SIGNUP_EMAIL'
on conflict do nothing;
```

### 2. Traffic capture — `track.js` + `pageviews`

`pageviews` table:
```sql
create table public.pageviews (
  id            bigserial primary key,
  path          text not null,        -- location.pathname + hash (entry anchors kept)
  referrer_host text,                 -- host only, never the full URL
  visitor       text,                 -- anonymous random id from localStorage
  device        text,                 -- 'mobile' | 'desktop'
  user_id       uuid,                 -- nullable; set only if signed in
  ts            timestamptz not null default now()
);
-- indexes: (ts), (path), (visitor), (ts, path)
```
RLS: `insert` allowed for anon + authenticated (`with check (true)`); **no select policy**
(reads go through gated RPCs only).

`track.js` (loaded on every page, fire-and-forget, after auth.js so the client exists):
- Builds/reuses an anonymous `visitor` id in `localStorage` (`aig:visitor`, a random uuid;
  not PII, not cross-site).
- Inserts one row: `path = location.pathname + location.hash`, `referrer_host` =
  host parsed from `document.referrer` (empty if none/same-site), `device` from a simple
  `matchMedia("(max-width: 900px)")` check, `user_id` if `window.__session` is set.
- **Skips** when: `?embed=1` / `embed-mode` (Compare/Build iframes), `localhost`/`127.*`,
  `navigator.webdriver` true, or an obvious bot UA. Swallows all errors — never blocks or
  breaks the page. No `await` on the critical path.
- Privacy: no IP stored, no cookies, host-only referrer, anonymous id → no banner needed.

### 3. Search logging — `search_queries` (for Content insights)

In-site search isn't logged today, so "top search queries" starts accumulating at launch
(no history). Small `search_queries` table + a one-line hook in the existing search code
(`reader-search.js` and the Compare/Build search) to insert `{ q, source, ts }` on a
committed search. RLS: insert anon; no public select (read via gated RPC).
```sql
create table public.search_queries (
  id bigserial primary key,
  q text not null,
  source text,            -- reader slug / 'compare' / 'build' / 'catalog'
  ts timestamptz not null default now()
);
```

### 4. Metrics & RPCs (all `SECURITY DEFINER`, `is_creator()`-gated)

- `is_creator() → boolean` — ungated; returns caller's own admin status (for the UI link).
- `creator_kpis() → json` — for Today / Yesterday / 7d / 30d: pageviews, unique visitors,
  new sign-ups; plus total registered users and an overall visitor→sign-up conversion.
- `creator_traffic_daily(days int default 30) → table(day date, views bigint, uniques bigint)`.
- `creator_signups_daily(days int default 30) → table(day date, signups bigint)`.
- `creator_top_pages(days int default 7, lim int default 20) → table(path text, views bigint, uniques bigint)`.
- `creator_top_referrers(days int default 7, lim int default 20) → table(referrer_host text, views bigint)`.
- `creator_device_split(days int default 7) → table(device text, views bigint)`.
- `creator_engagement() → json` — totals: bookmarks, notes, builds, shared_builds,
  highlights, quiz unlocked-skins (sum), distinct users with quiz progress.
- `creator_top_bookmarked(lim int default 20) → table(entry_id text, entry_title text, count bigint)`.
- `creator_top_searches(days int default 30, lim int default 20) → table(q text, count bigint)`.

Cross-user aggregation requires `SECURITY DEFINER` because RLS otherwise hides other
users' rows. Each function returns only aggregates, never raw user rows.

### 5. Dashboard UI — `admin.html`

- Reuses `style.css` + the standard site nav/footer chrome (dark theme). Not linked in the
  public nav; reachable only via the account-dropdown "Dashboard" link (admin only) or the
  direct URL (which redirects non-admins).
- On load: `await is_creator()`; if false → redirect to `index.html`. If true → call the
  RPCs in parallel and render.
- Layout (top → bottom):
  1. **KPI cards** — a responsive grid: Pageviews, Unique visitors, New sign-ups, each
     showing Today / Yesterday / 7d / 30d; plus Total users and Conversion.
  2. **Trend charts** (hand-rolled inline SVG) — daily pageviews (+ uniques) and daily
     sign-ups over 30 days.
  3. **Engagement strip** — compact counters (bookmarks, notes, builds, shares,
     highlights, goat unlocks).
  4. **Tables** — Top pages, Top referrers, Device split, Most-bookmarked entries, Top
     searches. Each a simple styled table with a sensible row cap.
- A small date-range note ("live as of <time>") and a manual Refresh button.

### 6. Data flow

```
any page  → track.js → INSERT pageviews            (anon, fire-and-forget)
search    → search hook → INSERT search_queries    (anon, fire-and-forget)
admin.html → is_creator()? → [no] redirect home
                           → [yes] parallel RPC calls → render cards/charts/tables
```

### 7. Error handling

- `track.js` / search hook: try/catch swallow everything; never block render; skip on
  embed/localhost/bot.
- `admin.html`: if `is_creator()` fails or returns false → redirect; if a data RPC fails,
  render that section's error state ("Couldn't load — retry") without breaking the page.

### 8. Testing

- **Access control (most important):** a signed-in non-admin calling each `creator_*` RPC
  gets `forbidden`; direct `select` on `pageviews`/`search_queries` returns nothing; the
  admin gets data. (Scripted SQL checks against the schema, run in a scratch context.)
- **Aggregation correctness:** seed known rows, assert each RPC's counts/buckets.
- **`track.js` logic:** inserts the expected row shape; skips on embed/localhost/bot;
  visitor id persists across loads. (JS unit checks of the pure helpers; manual insert check.)
- **UI gate:** `admin.html` redirects when `is_creator()` is false.

## Privacy & cost notes

- Privacy-respecting by construction: anonymous visitor id, no IP, no cookies, host-only
  referrers — no consent banner required.
- Cost: each visit is one small insert. Fine at this site's scale on Supabase free tier.
  If volume ever grows, a nightly roll-up + pruning of raw rows is the follow-up (out of
  scope now). The project has been on the free tier and paused before — worth keeping the
  table lean (minimal columns, indexes only where queried).

## Out of scope (future)

- Nightly roll-up / raw-row pruning. Emailed daily digest. Multi-admin roles. Real-time
  live counts. Geo/country breakdown (needs IP geo — deliberately omitted for privacy).
  Bot filtering beyond the simple client-side skip.

## Setup steps (creator runs in Supabase SQL editor)

1. Run the analytics schema SQL (creates `admins`, `pageviews`, `search_queries`,
   `is_creator()`, and all `creator_*` RPCs with RLS).
2. Run the one-line `admins` seed with your site sign-up email (section 1).
3. Deploy the site (adds `track.js`, the search hook, the account-menu link, `admin.html`).
4. Sign in as the admin account → the Dashboard link appears → open it.
