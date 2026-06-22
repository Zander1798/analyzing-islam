# Creator-only Analytics Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A private dashboard (`admin.html`) showing live site traffic, sign-up growth, engagement, and content insights — visible and queryable only by the site creator.

**Architecture:** A site-wide JS beacon (`track.js`) inserts anonymous pageview rows into a new Supabase `pageviews` table; search boxes log queries to `search_queries`. All reads happen through `SECURITY DEFINER` RPCs gated by an `is_creator()` check against an `admins` table, so non-admins get nothing even with the URL. The dashboard page reuses the site's dark styling and renders KPI cards, hand-rolled SVG trend charts, and tables from those RPCs. A "Dashboard" link is added to the account dropdown only for the admin.

**Tech Stack:** Supabase Postgres (SQL: tables, RLS, `SECURITY DEFINER` plpgsql/sql functions); vanilla browser JS (no framework); Python injector scripts (existing pattern) for site-wide `<script>` wiring; Node for JS unit tests; static hosting on GitHub Pages.

## Global Constraints

- **Access is sealed server-side.** Every `creator_*` RPC must begin with `if not public.is_creator() then raise exception 'forbidden' using errcode = '42501'; end if;`. `pageviews` and `search_queries` have **no public SELECT policy** — reads go only through gated RPCs. Client-side hiding is convenience only.
- **Admin identity** = membership in `public.admins(user_id)`, seeded by the creator with a one-line SQL using their site sign-up email. Never hard-code a UID or email in committed code.
- **Privacy by construction:** no IP, no cookies, host-only referrers, anonymous random `visitor` id in localStorage (`aig:visitor`). No consent banner.
- **`track.js` never breaks a page:** fire-and-forget, all errors swallowed, no `await` on the render path. Skips when `?embed=1`/`embed-mode`, `localhost`/`127.*`, `navigator.webdriver`, or an obvious bot UA.
- **Charts are hand-rolled inline SVG/CSS** — no external chart library.
- **Dashboard reuses `style.css` + standard nav/footer chrome** (dark theme); dashboard-specific styles live in `site/assets/css/admin.css`.
- **`pageviews.path`** = `location.pathname + location.hash` (keeps entry anchors). **`referrer_host`** = host only.
- **RPC names/signatures are fixed** (see Task 1); the dashboard and tests depend on them exactly.
- Deploy = push `site/**` to `main` (GitHub Pages). SQL is applied by hand in the Supabase SQL editor — it is never auto-run.

---

### Task 1: Analytics schema, RLS, and RPCs (`supabase/analytics.sql`)

Create the full database layer in one re-runnable SQL file: `admins`, `pageviews`, `search_queries`, `is_creator()`, and all `creator_*` RPCs with RLS. Because this environment has no local Postgres, correctness is verified by applying the file to Supabase and running the check queries in Step 4 (a non-admin must get `forbidden`; an admin must get data).

**Files:**
- Create: `supabase/analytics.sql`
- Create: `supabase/analytics-verify.sql` (check queries + expected results)

**Interfaces:**
- Produces (consumed by Tasks 5 & 6 and the dashboard):
  - `public.is_creator() returns boolean` — ungated; true iff caller is in `admins`.
  - `public.creator_kpis() returns json` — keys: `pageviews{today,yesterday,d7,d30}`, `uniques{today,yesterday,d7,d30}`, `signups{today,yesterday,d7,d30}`, `total_users`, `conversion_30d` (signups_30d / uniques_30d, 0 if no uniques).
  - `public.creator_traffic_daily(days int default 30) returns table(day date, views bigint, uniques bigint)`.
  - `public.creator_signups_daily(days int default 30) returns table(day date, signups bigint)`.
  - `public.creator_top_pages(days int default 7, lim int default 20) returns table(path text, views bigint, uniques bigint)`.
  - `public.creator_top_referrers(days int default 7, lim int default 20) returns table(referrer_host text, views bigint)`.
  - `public.creator_device_split(days int default 7) returns table(device text, views bigint)`.
  - `public.creator_engagement() returns json` — keys: `bookmarks, notes, builds, shared_builds, highlights, goat_unlocks, quiz_users`.
  - `public.creator_top_bookmarked(lim int default 20) returns table(entry_id text, entry_title text, count bigint)`.
  - `public.creator_top_searches(days int default 30, lim int default 20) returns table(q text, count bigint)`.

- [ ] **Step 1: Write `supabase/analytics.sql`**

```sql
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
```

- [ ] **Step 2: Write `supabase/analytics-verify.sql`** (run after applying, in Supabase SQL editor)

```sql
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
```

- [ ] **Step 3: Review the SQL for the gate invariant**

Confirm by reading: every `creator_*` function body's FIRST statement is the
`is_creator()` guard; `pageviews`/`search_queries` have an INSERT policy but **no
SELECT policy**; `admins` has **no policies at all**; `is_creator` is `security definer`.

- [ ] **Step 4: Apply + verify against Supabase**

The creator runs `supabase/analytics.sql` then `supabase/analytics-verify.sql` in the
Supabase SQL editor and confirms the expected outputs in Step 2's comments. Record the
results. (No local Postgres in CI; this is the authoritative correctness check. The
non-admin `forbidden` check is scripted in Task 7.)

- [ ] **Step 5: Commit**

```bash
git add supabase/analytics.sql supabase/analytics-verify.sql
git commit -m "feat(analytics): schema, RLS, and admin-gated RPCs"
```

---

### Task 2: Pageview beacon (`site/assets/js/track.js`)

A self-contained beacon: pure helper functions (TDD-tested in Node) plus a fire-and-forget
insert via the existing `window.__supabase` client. Also exposes `window.AIG.trackSearch`.

**Files:**
- Create: `site/assets/js/track.js`
- Create: `tests/test_track_js.mjs` (Node test of the pure helpers)

**Interfaces:**
- Consumes: `window.__supabase` (from `auth.js`), `window.__session` (optional).
- Produces (for Task 4): `window.AIG.trackSearch(q, source)` — inserts a `search_queries` row (fire-and-forget, deduped to one call per committed search).

- [ ] **Step 1: Write the failing Node test**

```javascript
// tests/test_track_js.mjs
import assert from "node:assert";
import { readFileSync } from "node:fs";
import vm from "node:vm";

// Load track.js into a sandbox with a fake window, exposing its internals via
// window.AIG.__test (track.js attaches helpers there when window.AIG.__test exists).
function load(sandboxWindow) {
  const code = readFileSync(new URL("../site/assets/js/track.js", import.meta.url), "utf8");
  const ctx = { window: sandboxWindow, document: sandboxWindow.document, localStorage: sandboxWindow.localStorage,
                navigator: sandboxWindow.navigator, location: sandboxWindow.location, matchMedia: sandboxWindow.matchMedia,
                URL: URL, URLSearchParams: URLSearchParams, setTimeout: setTimeout, console: console };
  ctx.window.matchMedia = sandboxWindow.matchMedia;
  vm.createContext(ctx);
  vm.runInContext(code, ctx);
  return ctx.window.AIG.__test;
}

function fakeWindow(over = {}) {
  const store = {};
  return {
    AIG: { __test: true },
    document: { querySelector: () => null, documentElement: { classList: { contains: () => false } },
                body: { classList: { contains: () => false } }, referrer: over.referrer || "" },
    localStorage: { getItem: (k) => store[k] ?? null, setItem: (k, v) => { store[k] = String(v); } },
    navigator: { webdriver: false, userAgent: over.ua || "Mozilla/5.0 (real browser)" },
    location: { pathname: over.pathname || "/catalog.html", hash: over.hash || "", search: over.search || "", hostname: over.hostname || "analyzingislam.com" },
    matchMedia: (q) => ({ matches: !!over.mobile }),
    addEventListener: () => {},
    __supabase: null,
  };
}

// referrerHost: host only, empty for same-site or none
{
  const t = load(fakeWindow({ referrer: "https://www.google.com/search?q=x", hostname: "analyzingislam.com" }));
  assert.equal(t.referrerHost("https://www.google.com/search?q=x", "analyzingislam.com"), "www.google.com");
  assert.equal(t.referrerHost("https://analyzingislam.com/index.html", "analyzingislam.com"), ""); // same-site
  assert.equal(t.referrerHost("", "analyzingislam.com"), "");
}
// device: mobile vs desktop
{
  const t = load(fakeWindow({ mobile: true }));
  assert.equal(t.device(), "mobile");
  const t2 = load(fakeWindow({ mobile: false }));
  assert.equal(t2.device(), "desktop");
}
// visitorId: stable across calls, persisted
{
  const w = fakeWindow();
  const t = load(w);
  const a = t.visitorId(); const b = t.visitorId();
  assert.equal(a, b);
  assert.match(a, /^[0-9a-f-]{16,}$/i);
}
// shouldSkip: bots, embed, localhost, webdriver
{
  assert.equal(load(fakeWindow({ ua: "Googlebot/2.1" })).shouldSkip(), true);
  assert.equal(load(fakeWindow({ search: "?embed=1" })).shouldSkip(), true);
  assert.equal(load(fakeWindow({ hostname: "localhost" })).shouldSkip(), true);
  const w = fakeWindow(); w.navigator.webdriver = true;
  assert.equal(load(w).shouldSkip(), true);
  assert.equal(load(fakeWindow()).shouldSkip(), false);
}
// pagePath: pathname + hash
{
  const t = load(fakeWindow({ pathname: "/catalog.html", hash: "#entry-x" }));
  assert.equal(t.pagePath(), "/catalog.html#entry-x");
}
console.log("track.js helper tests passed");
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node tests/test_track_js.mjs`
Expected: FAIL — `site/assets/js/track.js` does not exist (or `window.AIG.__test` undefined).

- [ ] **Step 3: Write `site/assets/js/track.js`**

```javascript
// Anonymous pageview + search beacon. Fire-and-forget; never blocks or breaks a page.
// Privacy: no IP, no cookies, host-only referrer, random localStorage visitor id.
(function () {
  "use strict";
  var W = window;

  var BOT_RE = /(bot|crawl|spider|slurp|bingpreview|facebookexternalhit|embedly|whatsapp|telegram|headless|lighthouse|preview|monitor|pingdom|gtmetrix)/i;

  function referrerHost(ref, selfHost) {
    if (!ref) return "";
    try {
      var h = new URL(ref).hostname;
      if (!h || h === selfHost) return "";
      return h;
    } catch (_) { return ""; }
  }
  function device() {
    try { return (W.matchMedia && W.matchMedia("(max-width: 900px)").matches) ? "mobile" : "desktop"; }
    catch (_) { return "desktop"; }
  }
  function visitorId() {
    try {
      var v = W.localStorage.getItem("aig:visitor");
      if (!v) {
        v = (W.crypto && W.crypto.randomUUID) ? W.crypto.randomUUID()
            : (Date.now().toString(16) + Math.random().toString(16).slice(2));
        W.localStorage.setItem("aig:visitor", v);
      }
      return v;
    } catch (_) { return ""; }
  }
  function pagePath() { return (W.location.pathname || "/") + (W.location.hash || ""); }
  function shouldSkip() {
    try {
      var host = W.location.hostname || "";
      if (host === "localhost" || /^127\./.test(host) || host === "") return true;
      if (W.navigator && W.navigator.webdriver) return true;
      if (BOT_RE.test((W.navigator && W.navigator.userAgent) || "")) return true;
      var p = new URLSearchParams(W.location.search || "");
      if (p.get("embed") === "1") return true;
      var de = W.document.documentElement, bo = W.document.body;
      if (de && de.classList.contains("embed-mode")) return true;
      if (bo && bo.classList.contains("embed-mode")) return true;
    } catch (_) {}
    return false;
  }

  function sb() { return W.__supabase || null; }
  function uid() { var s = W.__session; return (s && s.user && s.user.id) || null; }

  function sendPageview() {
    var client = sb();
    if (!client) return; // auth.js not ready yet — caller retries
    try {
      client.from("pageviews").insert({
        path: pagePath().slice(0, 400),
        referrer_host: referrerHost(W.document.referrer, W.location.hostname).slice(0, 200),
        visitor: visitorId(),
        device: device(),
        user_id: uid(),
      }).then(function () {}, function () {});
    } catch (_) {}
  }

  function trackSearch(q, source) {
    q = (q || "").trim();
    if (!q) return;
    var client = sb();
    if (!client) return;
    try {
      client.from("search_queries").insert({ q: q.slice(0, 200), source: (source || "").slice(0, 40) })
        .then(function () {}, function () {});
    } catch (_) {}
  }

  // Public API + (test-only) helper exposure.
  W.AIG = W.AIG || {};
  W.AIG.trackSearch = trackSearch;
  if (W.AIG.__test) {
    W.AIG.__test = { referrerHost: referrerHost, device: device, visitorId: visitorId,
                     pagePath: pagePath, shouldSkip: shouldSkip };
    return; // under test: don't fire the beacon
  }

  if (shouldSkip()) return;
  // The Supabase client is created by auth.js (deferred). Try now, then retry a
  // few times until it exists, then once on auth-state as a final safety net.
  var tries = 0;
  (function fire() {
    if (sb()) { sendPageview(); return; }
    if (tries++ < 40) { setTimeout(fire, 50); return; }
    W.addEventListener("auth-state", function once() { W.removeEventListener("auth-state", once); sendPageview(); });
  })();
})();
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node tests/test_track_js.mjs`
Expected: `track.js helper tests passed`. Also `node --check site/assets/js/track.js`.

- [ ] **Step 5: Commit**

```bash
git add site/assets/js/track.js tests/test_track_js.mjs
git commit -m "feat(analytics): anonymous pageview + search beacon"
```

---

### Task 3: Wire the beacon onto every page (`add-track-script.py`)

Add the `track.js` script tag site-wide using the project's injector pattern, and to the
canonical block in `sync-auth-scripts.py` so future pages get it too.

**Files:**
- Create: `add-track-script.py`
- Modify: `sync-auth-scripts.py` (add track.js to `auth_script_block`)
- Test: `tests/test_add_track_script.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_add_track_script.py
import subprocess, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

def test_track_injected_after_auth_ui_everywhere():
    subprocess.run([sys.executable, str(ROOT / "add-track-script.py")], cwd=ROOT, check=True)
    pages = [p for p in SITE.rglob("*.html") if "auth-ui.js" in p.read_text(encoding="utf-8")]
    assert pages, "no auth-ui pages found"
    missing = [str(p) for p in pages if "assets/js/track.js" not in p.read_text(encoding="utf-8")]
    assert not missing, f"track.js missing on {len(missing)} pages, e.g. {missing[:3]}"

def test_idempotent_no_duplicate_track_tags():
    subprocess.run([sys.executable, str(ROOT / "add-track-script.py")], cwd=ROOT, check=True)
    sample = SITE / "index.html"
    assert sample.read_text(encoding="utf-8").count('assets/js/track.js"') == 1
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_add_track_script.py -q`
Expected: FAIL — `add-track-script.py` missing.

- [ ] **Step 3: Write `add-track-script.py`**

```python
"""Insert <script src=".../assets/js/track.js" defer></script> immediately after
the auth-ui.js tag on every page that has it and lacks track.js. Idempotent.
Mirrors sync-auth-scripts.py. Run as the LAST decorator (after split_readers.py)."""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
# captures the relative prefix used by the auth-ui.js tag so track.js matches depth
AUTHUI_RE = re.compile(r'(<script\s+src=")((?:\.\./)*)(assets/js/auth-ui\.js)("[^>]*></script>)', re.I)

def process(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    if "assets/js/track.js" in html:
        return False
    m = AUTHUI_RE.search(html)
    if not m:
        return False
    prefix = m.group(2)
    track = f'\n<script src="{prefix}assets/js/track.js" defer></script>'
    new = html[:m.end()] + track + html[m.end():]
    path.write_text(new, encoding="utf-8")
    return True

def main():
    changed = 0
    for p in SITE.rglob("*.html"):
        if p.name.endswith(".orig.html"):
            continue
        if process(p):
            changed += 1
    print(f"track.js injected into {changed} pages")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Update `sync-auth-scripts.py`'s `auth_script_block`**

Append one line so newly-synced pages also get the beacon. In `sync-auth-scripts.py`,
change `auth_script_block` to add, after the `auth-ui.js` line:

```python
        f'<script src="{prefix}assets/js/track.js" defer></script>\n'
```

- [ ] **Step 5: Run tests + the injector**

Run: `python add-track-script.py` then `python -m pytest tests/test_add_track_script.py -q`
Expected: prints a non-zero injected count on first run; tests PASS; a second
`python add-track-script.py` reports `0 pages` (idempotent).

- [ ] **Step 6: Commit**

```bash
git add add-track-script.py sync-auth-scripts.py tests/test_add_track_script.py
git commit -m "feat(analytics): inject track.js site-wide (beacon on every page)"
```

Note: the generated `site/read/**` pages get the beacon here. If `split_readers.py` is
re-run later it strips it (regenerates from `.orig`); re-run `add-track-script.py` after.
Document this in the pipeline order alongside `build-split-readers.sh`.

---

### Task 4: Log searches (`window.AIG.trackSearch` hooks)

Call the beacon when a user runs a search, so Content-insights "top searches" fills up.

**Files:**
- Modify: `site/assets/js/reader-search.js` (in `tryJump`, log the committed query)
- Modify: `site/assets/js/app.js` IF it hosts the catalog search input — otherwise skip and note it.
- Test: `tests/test_search_logging.mjs` (Node: assert reader-search calls `AIG.trackSearch`)

- [ ] **Step 1: Write the failing test**

```javascript
// tests/test_search_logging.mjs — structural: the hook exists and is called with a source.
import assert from "node:assert";
import { readFileSync } from "node:fs";
const src = readFileSync(new URL("../site/assets/js/reader-search.js", import.meta.url), "utf8");
assert.ok(/AIG\s*&&\s*window\.AIG\.trackSearch|window\.AIG\s*&&\s*window\.AIG\.trackSearch/.test(src)
         || /AIG\.trackSearch\(/.test(src), "reader-search.js must call window.AIG.trackSearch");
console.log("search logging hook present");
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node tests/test_search_logging.mjs`
Expected: FAIL — no `trackSearch` call yet.

- [ ] **Step 3: Add the hook in `reader-search.js`**

In `tryJump()` (the function that runs when the user commits a search), at the very top
after computing `q`, add:

```javascript
      try { if (window.AIG && window.AIG.trackSearch) window.AIG.trackSearch(q, slug || "reader"); } catch (_) {}
```

(Place it right after `const q = (input.value || "").trim(); if (!q) {...} return;` so only
non-empty committed searches are logged. `slug` is already in scope in `mount()`.)

If `site/assets/js/app.js` contains a catalog search input handler, add the same one-liner
there with source `"catalog"`. If no such handler exists, note it in the report and skip —
do not invent one.

- [ ] **Step 4: Run the test + node check**

Run: `node tests/test_search_logging.mjs` then `node --check site/assets/js/reader-search.js`
Expected: `search logging hook present`; node check clean.

- [ ] **Step 5: Commit**

```bash
git add site/assets/js/reader-search.js tests/test_search_logging.mjs
git commit -m "feat(analytics): log committed searches to search_queries"
```

---

### Task 5: Account-menu "Dashboard" link (admin-only)

Add a "📊 Dashboard" item to the account dropdown, shown only when `is_creator()` returns true.

**Files:**
- Modify: `site/assets/js/auth-ui.js`
- Test: `tests/test_auth_ui_admin_link.mjs` (Node: menu logic with mocked rpc)

- [ ] **Step 1: Write the failing test**

```javascript
// tests/test_auth_ui_admin_link.mjs
import assert from "node:assert";
import { readFileSync } from "node:fs";
const src = readFileSync(new URL("../site/assets/js/auth-ui.js", import.meta.url), "utf8");
// The menu must contain an admin Dashboard item that is gated behind an is_creator rpc.
assert.ok(/admin\.html/.test(src), "auth-ui must link to admin.html");
assert.ok(/is_creator/.test(src), "auth-ui must check is_creator via rpc before showing the link");
assert.ok(/auth-menu-admin/.test(src), "admin link should carry a stable class for show/hide");
console.log("auth-ui admin link wiring present");
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node tests/test_auth_ui_admin_link.mjs`
Expected: FAIL.

- [ ] **Step 3: Implement in `auth-ui.js`**

In `buildLoggedInControl`, add the Dashboard item to the menu HTML (hidden by default),
immediately before the "My saved entries" line:

```javascript
      '<a href="' + prefix + 'admin.html" class="auth-menu-item auth-menu-admin" role="menuitem" hidden>📊 Dashboard</a>' +
```

Then, after `wrap.appendChild(menu);`, reveal it only for the admin:

```javascript
    // Show the creator dashboard link only when the server confirms admin status.
    try {
      if (window.__supabase && sess && sess.user) {
        window.__supabase.rpc("is_creator").then(function (res) {
          if (res && res.data === true) {
            var link = menu.querySelector(".auth-menu-admin");
            if (link) link.hidden = false;
          }
        }, function () {});
      }
    } catch (_) {}
```

- [ ] **Step 4: Run the test + node check**

Run: `node tests/test_auth_ui_admin_link.mjs` then `node --check site/assets/js/auth-ui.js`
Expected: pass; clean.

- [ ] **Step 5: Commit**

```bash
git add site/assets/js/auth-ui.js tests/test_auth_ui_admin_link.mjs
git commit -m "feat(analytics): admin-only Dashboard link in account menu"
```

---

### Task 6: Dashboard page (`admin.html` + `admin-dashboard.js` + `admin.css`)

The dashboard UI: gate-redirect, fetch the RPCs, render KPI cards, hand-rolled SVG trend
charts, and tables — in the site's dark style.

**Files:**
- Create: `site/admin.html`
- Create: `site/assets/js/admin-dashboard.js`
- Create: `site/assets/css/admin.css`
- Test: `tests/test_admin_dashboard.mjs` (Node: pure render/format/SVG helpers)

**Interfaces:**
- Consumes: `window.__supabase`, `window.__authReady`, and the Task 1 RPCs.
- Produces (test seam): `window.AIG_DASH` with pure helpers `fmtInt(n)`, `kpiCardHtml(label, vals)`, `barsSvg(series, opts)`, `lineSvg(series, opts)`, `tableHtml(rows, cols)`.

- [ ] **Step 1: Write the failing test**

```javascript
// tests/test_admin_dashboard.mjs
import assert from "node:assert";
import { readFileSync } from "node:fs";
import vm from "node:vm";
function load() {
  const code = readFileSync(new URL("../site/assets/js/admin-dashboard.js", import.meta.url), "utf8");
  const win = { AIG_DASH: { __test: true }, document: { readyState: "complete", addEventListener(){} },
                addEventListener(){}, location:{ href:"" } };
  const ctx = { window: win, document: win.document };
  vm.createContext(ctx); vm.runInContext(code, ctx);
  return win.AIG_DASH;
}
const D = load();
assert.equal(D.fmtInt(1234567), "1,234,567");
assert.equal(D.fmtInt(0), "0");
// KPI card includes label and all four buckets
{
  const h = D.kpiCardHtml("Pageviews", { today: 5, yesterday: 4, d7: 30, d30: 100 });
  ["Pageviews","5","4","30","100"].forEach(s => assert.ok(h.includes(s), "card missing " + s));
}
// bars svg: one <rect> per point, escapes nothing weird, has viewBox
{
  const svg = D.barsSvg([{label:"a",value:1},{label:"b",value:3},{label:"c",value:0}], {});
  assert.ok(svg.includes("<svg"));
  assert.equal((svg.match(/<rect/g) || []).length >= 3, true);
}
// line svg: a polyline with N points
{
  const svg = D.lineSvg([{label:"d1",value:1},{label:"d2",value:2},{label:"d3",value:5}], {});
  assert.ok(svg.includes("<polyline") || svg.includes("<path"));
}
// table: header + one row per data row, html-escaped
{
  const html = D.tableHtml([{ path: "/x", views: 9 }], [["path","Page"],["views","Views"]]);
  assert.ok(html.includes("<th") && html.includes("Page") && html.includes("/x") && html.includes("9"));
  const esc = D.tableHtml([{ path: "<b>", views: 1 }], [["path","Page"],["views","Views"]]);
  assert.ok(esc.includes("&lt;b&gt;") && !esc.includes("<b>"));
}
console.log("admin-dashboard helper tests passed");
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node tests/test_admin_dashboard.mjs`
Expected: FAIL — file missing.

- [ ] **Step 3: Write `site/assets/js/admin-dashboard.js`**

```javascript
// Creator dashboard: gate, fetch RPCs, render. Pure helpers exposed on window.AIG_DASH
// for tests; the orchestrator runs only in a real browser.
(function () {
  "use strict";
  var W = window;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c];
    });
  }
  function fmtInt(n) {
    n = Number(n) || 0;
    return n.toLocaleString("en-US");
  }
  function kpiCardHtml(label, vals) {
    vals = vals || {};
    function cell(k, t) {
      return '<div class="kpi-cell"><span class="kpi-cell-label">' + t + '</span>' +
             '<span class="kpi-cell-val">' + fmtInt(vals[k]) + '</span></div>';
    }
    return '<div class="kpi-card"><h3 class="kpi-title">' + esc(label) + '</h3>' +
           '<div class="kpi-grid">' + cell("today","Today") + cell("yesterday","Yesterday") +
           cell("d7","7-day") + cell("d30","30-day") + '</div></div>';
  }
  // Simple bar chart. series: [{label, value}]. Returns an inline SVG string.
  function barsSvg(series, opts) {
    series = series || []; opts = opts || {};
    var w = opts.width || 720, h = opts.height || 160, pad = 18;
    var max = Math.max(1, Math.max.apply(null, series.map(function (d) { return d.value || 0; }).concat([0])));
    var n = Math.max(1, series.length);
    var bw = (w - pad * 2) / n;
    var bars = series.map(function (d, i) {
      var bh = Math.round((h - pad * 2) * (d.value || 0) / max);
      var x = pad + i * bw + bw * 0.1, y = h - pad - bh;
      return '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + (bw * 0.8).toFixed(1) +
             '" height="' + bh + '" rx="1.5"><title>' + esc(d.label) + ": " + fmtInt(d.value) + '</title></rect>';
    }).join("");
    return '<svg class="chart chart-bars" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" role="img">' +
           bars + '</svg>';
  }
  // Simple line chart via polyline.
  function lineSvg(series, opts) {
    series = series || []; opts = opts || {};
    var w = opts.width || 720, h = opts.height || 160, pad = 18;
    var vals = series.map(function (d) { return d.value || 0; });
    var max = Math.max(1, Math.max.apply(null, vals.concat([0])));
    var n = Math.max(1, series.length - 1);
    var pts = series.map(function (d, i) {
      var x = pad + (w - pad * 2) * (series.length === 1 ? 0 : i / n);
      var y = h - pad - (h - pad * 2) * (d.value || 0) / max;
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
    return '<svg class="chart chart-line" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" role="img">' +
           '<polyline fill="none" stroke-width="2" points="' + pts + '"></polyline></svg>';
  }
  function tableHtml(rows, cols) {
    rows = rows || []; cols = cols || [];
    var head = "<tr>" + cols.map(function (c) { return '<th>' + esc(c[1]) + "</th>"; }).join("") + "</tr>";
    var body = rows.map(function (r) {
      return "<tr>" + cols.map(function (c) { return "<td>" + esc(r[c[0]]) + "</td>"; }).join("") + "</tr>";
    }).join("");
    return '<table class="dash-table"><thead>' + head + "</thead><tbody>" + body + "</tbody></table>";
  }

  W.AIG_DASH = W.AIG_DASH || {};
  var api = { fmtInt: fmtInt, kpiCardHtml: kpiCardHtml, barsSvg: barsSvg, lineSvg: lineSvg, tableHtml: tableHtml, esc: esc };
  if (W.AIG_DASH.__test) { W.AIG_DASH = api; return; }
  W.AIG_DASH = api;

  // ---- orchestrator (browser only) ----
  function set(id, html) { var el = document.getElementById(id); if (el) el.innerHTML = html; }
  function fail(id) { set(id, '<div class="dash-error">Couldn’t load — <button class="dash-retry">retry</button></div>'); }

  async function rpc(name, args) {
    var res = await W.__supabase.rpc(name, args || {});
    if (res.error) throw res.error;
    return res.data;
  }

  async function render() {
    try {
      var kpis = await rpc("creator_kpis");
      set("kpi-cards",
        kpiCardHtml("Pageviews", kpis.pageviews) +
        kpiCardHtml("Unique visitors", kpis.uniques) +
        kpiCardHtml("New sign-ups", kpis.signups) +
        '<div class="kpi-card"><h3 class="kpi-title">Totals</h3><div class="kpi-grid">' +
          '<div class="kpi-cell"><span class="kpi-cell-label">Users</span><span class="kpi-cell-val">' + fmtInt(kpis.total_users) + '</span></div>' +
          '<div class="kpi-cell"><span class="kpi-cell-label">Conv. 30d</span><span class="kpi-cell-val">' + ((kpis.conversion_30d*100)||0).toFixed(1) + '%</span></div>' +
        '</div></div>');
    } catch (e) { fail("kpi-cards"); }

    try {
      var td = await rpc("creator_traffic_daily", { days: 30 });
      set("chart-traffic", barsSvg(td.map(function (r) { return { label: r.day, value: r.views }; }), {}));
    } catch (e) { fail("chart-traffic"); }
    try {
      var sd = await rpc("creator_signups_daily", { days: 30 });
      set("chart-signups", lineSvg(sd.map(function (r) { return { label: r.day, value: r.signups }; }), {}));
    } catch (e) { fail("chart-signups"); }

    try {
      var eng = await rpc("creator_engagement");
      var items = [["bookmarks","Bookmarks"],["notes","Notes"],["builds","Builds"],
                   ["shared_builds","Shares"],["highlights","Highlights"],["goat_unlocks","Goat unlocks"]];
      set("engagement", items.map(function (k) {
        return '<div class="eng-stat"><span class="eng-val">' + fmtInt(eng[k[0]]) + '</span><span class="eng-label">' + k[1] + '</span></div>';
      }).join(""));
    } catch (e) { fail("engagement"); }

    try { set("top-pages", tableHtml(await rpc("creator_top_pages", { days: 7, lim: 20 }),
            [["path","Page"],["views","Views"],["uniques","Uniques"]])); } catch (e) { fail("top-pages"); }
    try { set("top-referrers", tableHtml(await rpc("creator_top_referrers", { days: 7, lim: 20 }),
            [["referrer_host","Referrer"],["views","Views"]])); } catch (e) { fail("top-referrers"); }
    try { set("device-split", tableHtml(await rpc("creator_device_split", { days: 7 }),
            [["device","Device"],["views","Views"]])); } catch (e) { fail("device-split"); }
    try { set("top-bookmarked", tableHtml(await rpc("creator_top_bookmarked", { lim: 20 }),
            [["entry_title","Entry"],["count","Saves"]])); } catch (e) { fail("top-bookmarked"); }
    try { set("top-searches", tableHtml(await rpc("creator_top_searches", { days: 30, lim: 20 }),
            [["q","Query"],["count","Count"]])); } catch (e) { fail("top-searches"); }

    var stamp = document.getElementById("dash-stamp");
    if (stamp) stamp.textContent = "Live as of " + new Date().toLocaleString();
  }

  async function boot() {
    await (W.__authReady || Promise.resolve());
    if (!W.__supabase) { location.href = "index.html"; return; }
    var ok = false;
    try { var res = await W.__supabase.rpc("is_creator"); ok = res && res.data === true; } catch (e) { ok = false; }
    if (!ok) { location.href = "index.html"; return; }
    var gate = document.getElementById("dash-gate"); if (gate) gate.hidden = true;
    var root = document.getElementById("dash-root"); if (root) root.hidden = false;
    render();
    document.addEventListener("click", function (e) {
      if (e.target && e.target.classList && e.target.classList.contains("dash-retry")) render();
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
```

- [ ] **Step 4: Write `site/admin.html`**

Use the exact site chrome (copy the `<head>` + `<nav class="site-nav">` block from
`site/saved.html` so favicons, nav, and the script include order match), set the title to
"Dashboard", add `<link rel="stylesheet" href="assets/css/admin.css">`, and use this body +
script order. Keep `dash-root` hidden until the gate passes.

```html
<main class="dash-wrap">
  <div id="dash-gate" class="dash-gate">Checking access…</div>
  <div id="dash-root" hidden>
    <header class="dash-head">
      <h1>Creator dashboard</h1>
      <p class="dash-sub" id="dash-stamp">Loading…</p>
    </header>
    <section class="kpi-row" id="kpi-cards"></section>
    <section class="dash-block"><h2>Traffic — last 30 days</h2><div id="chart-traffic"></div></section>
    <section class="dash-block"><h2>Sign-ups — last 30 days</h2><div id="chart-signups"></div></section>
    <section class="dash-block"><h2>Engagement</h2><div class="eng-row" id="engagement"></div></section>
    <div class="dash-cols">
      <section class="dash-block"><h2>Top pages (7d)</h2><div id="top-pages"></div></section>
      <section class="dash-block"><h2>Top referrers (7d)</h2><div id="top-referrers"></div></section>
      <section class="dash-block"><h2>Devices (7d)</h2><div id="device-split"></div></section>
      <section class="dash-block"><h2>Most-bookmarked</h2><div id="top-bookmarked"></div></section>
      <section class="dash-block"><h2>Top searches (30d)</h2><div id="top-searches"></div></section>
    </div>
  </div>
</main>
<!-- scripts: supabase CDN, config.js, auth.js (defer), auth-ui.js (defer),
     goat-skins.js, goat.js, track.js (defer), then: -->
<script src="assets/js/admin-dashboard.js" defer></script>
```

When the gate passes, `admin-dashboard.js`'s `boot()` already hides `#dash-gate` and
unhides `#dash-root` (see Step 3). The `admin.html` markup just needs both elements
present with the ids used above.

- [ ] **Step 5: Write `site/assets/css/admin.css`**

```css
/* Creator dashboard — dark, matches style.css tokens. */
.dash-wrap { max-width: 1100px; margin: 0 auto; padding: 24px 16px 64px; }
.dash-gate { color: var(--muted, #888); padding: 48px 0; text-align: center; }
.dash-head h1 { margin: 0 0 4px; }
.dash-sub { color: var(--muted, #888); font-size: 13px; margin: 0 0 20px; }
.kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 24px; }
.kpi-card { background: #000; border: 1px solid rgba(255,255,255,.15); border-radius: 8px; padding: 14px 16px; }
.kpi-title { font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted,#9a9a9a); margin: 0 0 10px; }
.kpi-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px 12px; }
.kpi-cell { display: flex; flex-direction: column; }
.kpi-cell-label { font-size: 11px; color: var(--muted,#888); }
.kpi-cell-val { font-size: 20px; font-weight: 700; }
.dash-block { background: #000; border: 1px solid rgba(255,255,255,.12); border-radius: 8px; padding: 14px 16px; margin-bottom: 18px; }
.dash-block h2 { font-size: 14px; margin: 0 0 12px; }
.dash-cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px,1fr)); gap: 18px; }
.chart { width: 100%; height: 160px; }
.chart-bars rect { fill: var(--accent, #c9962f); }
.chart-line polyline { stroke: var(--accent, #c9962f); }
.eng-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px,1fr)); gap: 12px; }
.eng-stat { background: rgba(255,255,255,.03); border-radius: 6px; padding: 12px; text-align: center; }
.eng-val { display: block; font-size: 22px; font-weight: 700; }
.eng-label { font-size: 12px; color: var(--muted,#888); }
.dash-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.dash-table th, .dash-table td { text-align: left; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,.08); }
.dash-table th { color: var(--muted,#9a9a9a); font-weight: 600; }
.dash-table td:first-child { max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dash-error { color: #e06b6b; font-size: 13px; }
.dash-retry { background: none; border: 1px solid currentColor; color: inherit; border-radius: 4px; padding: 2px 8px; cursor: pointer; }
```

- [ ] **Step 6: Run tests + injector + node checks**

Run: `node tests/test_admin_dashboard.mjs` then `node --check site/assets/js/admin-dashboard.js`
then `python add-track-script.py` (so `admin.html` itself gets the beacon).
Expected: helper tests pass; node check clean; injector adds track.js to `admin.html`.

- [ ] **Step 7: Commit**

```bash
git add site/admin.html site/assets/js/admin-dashboard.js site/assets/css/admin.css tests/test_admin_dashboard.mjs
git commit -m "feat(analytics): creator dashboard page (cards, SVG charts, tables)"
```

---

### Task 7: Integration verification + deploy

Apply the SQL, seed the admin, deploy, and verify end-to-end (beacon writes; dashboard
loads for the admin; non-admin is forbidden).

**Files:** none (verification + deploy).

- [ ] **Step 1: Apply SQL + seed admin (creator, in Supabase)**

Run `supabase/analytics.sql`. Then seed (creator pastes their site sign-up email):

```sql
insert into public.admins (user_id)
select id from auth.users where email = 'YOUR_SITE_SIGNUP_EMAIL' on conflict do nothing;
select count(*) from public.admins;  -- expect 1
```

- [ ] **Step 2: Full JS test sweep + injector run**

```bash
node tests/test_track_js.mjs && node tests/test_admin_dashboard.mjs \
  && node tests/test_search_logging.mjs && node tests/test_auth_ui_admin_link.mjs
python -m pytest tests/test_add_track_script.py -q
python add-track-script.py     # ensure every page (incl. admin.html) has the beacon
```
Expected: all green; injector idempotent (0 on a second run).

- [ ] **Step 3: Stage generated pages + deploy**

```bash
git add site
git commit -m "chore(analytics): beacon injected site-wide"
git push origin main
gh run watch "$(gh run list --workflow=pages.yml --limit 1 --json databaseId -q '.[0].databaseId')" --exit-status
```

- [ ] **Step 4: Live verification**

1. Open the live site (not localhost) on a couple of pages, then in Supabase:
   `select count(*), max(ts) from public.pageviews;` — expect rows appearing.
2. Sign in as the **admin** → account menu shows **📊 Dashboard** → open `admin.html` →
   cards/charts/tables render; `select` errors do not appear.
3. **Gate check (scripted):** sign in as a throwaway **non-admin** in the browser console
   on the live site and run:
   ```js
   await window.__supabase.rpc('creator_kpis')
   ```
   Expect `error` with code `42501` / "forbidden" and `data === null`. Also confirm the
   non-admin sees no Dashboard link and `admin.html` redirects them home.
4. Confirm a search on a reader page inserts into `search_queries`
   (`select count(*) from public.search_queries;`).

- [ ] **Step 5: Record results in the report and finish**

Document the verification outputs. If the non-admin gate check returns data instead of
`forbidden`, STOP — that is a security defect; re-check Task 1's guards before considering
the feature done.

---

## Notes for the implementer

- **The security gate is the whole point.** If any `creator_*` RPC returns data to a
  non-admin, the feature has failed regardless of how nice the UI looks. Task 7 Step 4.3 is
  the gate test; treat its failure as Critical.
- **No local Postgres** is assumed; SQL correctness is verified against the live Supabase
  project (Tasks 1 & 7). The JS is genuinely unit-tested in Node (pure helpers).
- **Pipeline ordering:** `add-track-script.py` must run after `split_readers.py` (and after
  any reader rebuild), or the generated reader pages won't carry the beacon. Add it to the
  documented build order next to `build-split-readers.sh`.
- **Don't hard-code identity:** admin status is data (`admins` table), seeded by the creator.
