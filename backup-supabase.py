"""
Supabase data backup — dumps every user-data table to timestamped JSON files.

Why this exists
---------------
Free-tier Supabase only keeps daily backups for 7 days and you cannot
self-restore them. If a row gets deleted (bug, bad migration, malicious
user, project pause), it is gone. This script gives you an off-Supabase
copy so the worst case is "restore from the last local dump" instead of
"data is gone forever."

What it backs up
----------------
Every user-data table in supabase/schema.sql + the community/messenger
extensions: profiles, bookmarks, notes, builds, shared_builds, friendships,
highlights, communities, community_members, community_posts, community_post_comments,
community_post_reactions, messenger_threads, messenger_thread_members,
messenger_messages, messenger_message_reactions, messenger_notifications.

It does NOT back up auth.users (Supabase manages that) or storage objects.

How to run
----------
1. Get your service_role key (NOT the anon key) from:
   Supabase dashboard -> Project Settings -> API -> service_role secret
2. Set it as an env var (Windows PowerShell):
       $env:SUPABASE_SERVICE_ROLE = "eyJhbGci..."
   Or bash:
       export SUPABASE_SERVICE_ROLE="eyJhbGci..."
3. python backup-supabase.py

Output: backups/<UTC-timestamp>/<table>.json

The service_role key bypasses Row-Level Security, which is what you want
for a full backup. Never commit it to git or paste it into the browser.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SUPABASE_URL = "https://cndmksrilytnpgstvmxb.supabase.co"

TABLES = [
    "profiles",
    "bookmarks",
    "notes",
    "builds",
    "shared_builds",
    "friendships",
    "highlights",
    "communities",
    "community_members",
    "community_posts",
    "community_post_comments",
    "community_post_reactions",
    "messenger_threads",
    "messenger_thread_members",
    "messenger_messages",
    "messenger_message_reactions",
    "messenger_notifications",
]

PAGE_SIZE = 1000


def fetch_table(service_key: str, table: str) -> list:
    rows = []
    offset = 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit={PAGE_SIZE}&offset={offset}"
        req = urllib.request.Request(
            url,
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                page = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 404 or "does not exist" in body.lower():
                print(f"  [skip] {table}: not present in this project")
                return None
            raise RuntimeError(f"{table}: HTTP {e.code} - {body}") from e

        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE


def main() -> int:
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE")
    if not service_key:
        print("ERROR: SUPABASE_SERVICE_ROLE env var not set.")
        print("Get it from Supabase dashboard -> Project Settings -> API -> service_role.")
        return 1

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = Path(__file__).parent / "backups" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Backing up to: {out_dir}")

    summary = {}
    started = time.time()
    for table in TABLES:
        print(f"  -> {table} ...", end=" ", flush=True)
        try:
            rows = fetch_table(service_key, table)
        except Exception as e:
            print(f"FAILED: {e}")
            summary[table] = {"status": "error", "error": str(e)}
            continue

        if rows is None:
            summary[table] = {"status": "missing"}
            continue

        path = out_dir / f"{table}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        size_kb = path.stat().st_size / 1024
        print(f"{len(rows)} rows ({size_kb:.1f} KB)")
        summary[table] = {"status": "ok", "rows": len(rows), "bytes": path.stat().st_size}

    manifest = {
        "timestamp_utc": stamp,
        "supabase_url": SUPABASE_URL,
        "duration_seconds": round(time.time() - started, 2),
        "tables": summary,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Done in {manifest['duration_seconds']}s. Manifest: {out_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
