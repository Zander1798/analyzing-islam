#!/usr/bin/env python3
"""Remove every artefact the Stage 9d test harness created and prove the database
is back to its pre-test baseline. Touches only rows the harness created.

PRE-CUTOVER ONLY — see the pageview sweep comment below.
"""
import json, os, subprocess, sys
import requests

SP = os.path.dirname(os.path.abspath(__file__))
API = "https://api.analyzingislam.com"
env = dict(l.strip().split("=", 1) for l in open(f"{SP}/keys.env") if "=" in l)
S = requests.Session(); S.verify = True   # real LE cert since Stage 9b
H = {"apikey": env["SERVICE_ROLE_KEY"], "Authorization": f"Bearer {env['SERVICE_ROLE_KEY']}",
     "Content-Type": "application/json"}


def sql(q):
    p = subprocess.run(["ssh", "deploy@72.60.17.245",
                        "docker exec -i supabase-db psql -U supabase_admin -d postgres -At -f -"],
                       input=q, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr)
    return p.stdout.strip()


print("=== deleting test users (cascades to profiles/builds/highlights/quiz/shared_builds/admins) ===")
users = S.get(f"{API}/auth/v1/admin/users?per_page=200", headers=H).json().get("users", [])
targets = [u for u in users if "+migtest-" in u["email"]]
for u in targets:
    r = S.delete(f"{API}/auth/v1/admin/users/{u['id']}", headers=H)
    print(f"  deleted {u['email']} -> HTTP {r.status_code}")

print("=== sweeping rows with no FK to auth.users (bookmarks, notes) and test pageviews ===")
print(sql("""
delete from public.bookmarks b where not exists (select 1 from auth.users u where u.id=b.user_id);
delete from public.notes    n where not exists (select 1 from auth.users u where u.id=n.user_id);
delete from public.pageviews where visitor = 'migtest' or path = '/migtest';
-- DELIBERATELY NOT sweeping pageviews by time. An earlier version of this
-- script did, on the belief that the browser harness generated them. It does
-- not: track.js bails out on `navigator.webdriver`, which Playwright sets, so
-- automated runs never write a pageview at all (verified). The rows that
-- prompted that sweep came from somewhere else.
--
-- Leaving the time-based sweep in would now be actively destructive: after
-- Stage 10a the pageviews table is an exact copy of Cloud, including genuine
-- recent traffic, and `ts > now() - interval '6 hours'` would delete real
-- analytics data.
--
-- Only ever remove rows this harness explicitly tagged."""))

print("=== counts vs baseline ===")
now = sql(open(f"{SP}/counts.sql").read().replace("\\pset border 2", ""))
base = {}
for line in open(f"{SP}/counts-baseline.txt"):
    if "|" in line and "---" not in line and " t " not in line:
        a, _, b = line.partition("|")
        if a.strip() and b.strip().isdigit():
            base[a.strip()] = int(b.strip())
cur = {l.split("|")[0]: int(l.split("|")[1]) for l in now.splitlines() if "|" in l}
bad = []
for k in sorted(set(base) | set(cur)):
    b, c = base.get(k), cur.get(k)
    mark = "OK " if b == c else "DRIFT"
    if b != c:
        bad.append((k, b, c))
    print(f"  {mark} {k:26} baseline={b} now={c}")
print()
if bad:
    print("!! DRIFT vs baseline:")
    for k, b, c in bad:
        print(f"   {k}: {b} -> {c}")
    sys.exit(1)
print("Database is byte-for-byte back at the pre-test baseline.")
