#!/bin/bash
# ===========================================================================
# stage10a-sync.sh — the final sync, as one idempotent, timed, verified run.
#
#   ~/stage10a-sync.sh ~/supabase-backup-YYYYMMDD.sql
#
# Runs ON THE VPS. Takes a fresh Supabase Cloud dump (produced on the
# workstation, which is where the Cloud credential lives) and brings the
# self-hosted stack to exactly Cloud's state.
#
# WHY THIS SCRIPT EXISTS
# ----------------------
# The `--clean` restore silently undoes four earlier stages: it drops the
# auth/storage ownership and grants (4b2), it wipes the public-schema objects
# the repo SQL created (4d), it reinstates Cloud's absolute storage URLs
# (Stage 6), and it restores object metadata carrying Cloud's version UUIDs
# that the local files cannot satisfy (Stage 5). Doing those five things by
# hand, in order, minutes before a DNS flip is how migrations break. This
# does them in one command, verifies each, and refuses to continue on drift.
#
# TWO TRAPS THIS ENCODES
# ----------------------
#  * `analytics-verify.sql` is a TEST script, not schema. Its cleanup runs
#    `delete from public.search_queries where q = 'aisha'` and the one real
#    row is literally 'aisha'. It is excluded, by name, always.
#  * `community-schema.sql` carries a six-community demo seed. Rather than
#    hardcoding "keep ids 8 and 9" (which silently deletes anything created
#    since), this snapshots the real id set from the freshly restored Cloud
#    data and removes exactly what the replay adds.
#
# `docker exec` WITHOUT `-i` discards stdin and exits 0, so every SQL call
# below uses `-i` and every write is re-queried.
# ===========================================================================
set -euo pipefail

DUMP="${1:-}"
COMPOSE_DIR="$HOME/supabase-selfhost"
SCHEMA_SRC="${SCHEMA_SRC:-$HOME/schema-src}"
CLOUD_REF="${CLOUD_REF:-cndmksrilytnpgstvmxb}"
CLOUD_HOST="https://${CLOUD_REF}.supabase.co"
NEW_HOST="${NEW_HOST:-https://api.analyzingislam.com}"
WORK="$HOME/.stage10a"
T0=$(date +%s)

[ -n "$DUMP" ] && [ -f "$DUMP" ] || { echo "usage: $0 <dump.sql>"; exit 1; }
mkdir -p "$WORK"

phase() { echo; echo "=== [$(( $(date +%s) - T0 ))s] $* ==="; }
die()   { echo "!! FAILED: $*" >&2; exit 1; }
psqli() { docker exec -i supabase-db psql -U supabase_admin -d postgres "$@"; }
q()     { psqli -At -c "$1"; }

COUNT_SQL="select n.nspname||'.'||c.relname, (xpath('/row/c/text()', query_to_xml(
    format('select count(*) as c from %I.%I', n.nspname, c.relname), false, true, '')))[1]::text::bigint
  from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where c.relkind='r' and n.nspname in ('public','auth','storage') order by 1"

# --------------------------------------------------------------- 0. preflight
phase "0. Preflight"
SZ=$(stat -c%s "$DUMP")
grep -q 'COPY "auth"."users"' "$DUMP" || die "dump has no auth.users COPY block — refusing"
[ "$SZ" -gt 100000 ] || die "dump is only $SZ bytes — refusing"
echo "dump: $DUMP ($SZ bytes)"
[ -d "$SCHEMA_SRC" ] || die "schema source missing at $SCHEMA_SRC (scp the repo's supabase/ dir there)"
echo "schema files: $(ls -1 "$SCHEMA_SRC"/*.sql | wc -l) (analytics-verify.sql will be SKIPPED)"
SERVICE_KEY=$(grep '^SERVICE_ROLE_KEY=' "$COMPOSE_DIR/.env" | cut -d= -f2-)
[ -n "$SERVICE_KEY" ] || die "SERVICE_ROLE_KEY not found in $COMPOSE_DIR/.env"

# ------------------------------------------------- 1. safety backup FIRST
phase "1. Safety backup of the CURRENT state before touching anything"
"$HOME/backup.sh" || die "pre-sync backup failed — refusing to restore over unbacked-up data"

# --------------------------------------------------------------- 2. restore
phase "2. Restore the Cloud dump as supabase_admin"
# Cloud has no iceberg_* tables; the self-hosted storage-api creates
# storage.iceberg_namespaces / iceberg_tables, and both carry an FK to
# storage.buckets_analytics. So the dump's DROPs for buckets_analytics, its
# pkey, the buckettype enum and the storage schema all fail on dependency,
# then the re-CREATE hits "already exists"/"multiple primary keys". Likewise
# DROP SCHEMA public fails because pg_trgm and vector live there. Every one
# of those is confined to objects this site never reads — but "confined"
# is asserted below, not assumed.
grep -A2 'COPY "storage"."buckets_analytics"' "$DUMP" | grep -q '^\\\.' \
    || die "storage.buckets_analytics has DATA in this dump — its restore failed above, so that data would be LOST. Stop and handle it."
psqli -v ON_ERROR_STOP=0 < "$DUMP" > "$WORK/restore.log" 2>&1 || true
BAD=$(grep -i '^ERROR' "$WORK/restore.log" \
      | grep -viE 'already exists|does not exist|must be owner|permission denied' \
      | grep -viE 'cannot drop (constraint buckets_analytics_pkey|table storage\.buckets_analytics|type storage\.buckettype)' \
      | grep -viE 'cannot drop schema (storage|public) because other objects depend on it' \
      | grep -viE 'multiple primary keys for table "buckets_analytics"' || true)
[ -z "$BAD" ] || { echo "$BAD" | head -20; die "restore produced unexpected errors (see $WORK/restore.log)"; }
echo "restore ok ($(grep -ci '^ERROR' "$WORK/restore.log" || true) expected-noise ERROR lines, 0 unexpected)"

# This is the TARGET state: pure Cloud, before any local replay touches it.
q "$COUNT_SQL" | sort > "$WORK/counts-cloud.txt"
q "select id from public.communities order by 1"        | sort > "$WORK/communities-cloud.txt"
q "select community_id||':'||user_id from public.community_members" | sort > "$WORK/members-cloud.txt"
echo "cloud baseline captured: $(wc -l < "$WORK/counts-cloud.txt") tables, \
$(wc -l < "$WORK/communities-cloud.txt") communities"

# --------------------------------------------- 3. ownership + grants (4b2)
phase "3. Repair auth/storage ownership AND privileges (the restore dropped both)"
# The dump is --no-owner --no-privileges and --clean DROPs+recreates the auth and
# storage SCHEMAS, so after a restore those schemas are owned by the restoring
# superuser with an empty ACL. Two distinct things are lost and BOTH must come
# back; the original Stage 4b2 only fixed the first:
#
#   ownership  -> GoTrue runs as supabase_auth_admin, storage-api as
#                 supabase_storage_admin. Without this they cannot ALTER/own.
#   privileges -> anon/authenticated need USAGE on schema auth just to call
#                 auth.uid() inside every RLS policy, and the storage-api needs
#                 table privileges on storage.*. Losing these produces
#                 "permission denied for table buckets" on upload and breaks
#                 every RLS policy that calls auth.uid().
#
# Values below are taken verbatim from the supabase/postgres image's own
# init-scripts (/etc/postgresql-custom/init-scripts). Granting the API roles
# table access on storage is what a fresh self-host does and is safe here:
# service_role has BYPASSRLS, and anon/authenticated are gated by the 12 RLS
# policies on storage.objects (storage.buckets has RLS on with no policies, so
# clients cannot enumerate buckets).
psqli -q <<'SQL'
do $$ declare r record; begin
  for r in select tablename from pg_tables where schemaname='auth' loop
    execute format('alter table auth.%I owner to supabase_auth_admin', r.tablename); end loop;
  for r in select sequencename from pg_sequences where schemaname='auth' loop
    execute format('alter sequence auth.%I owner to supabase_auth_admin', r.sequencename); end loop;
  for r in select tablename from pg_tables where schemaname='storage' loop
    execute format('alter table storage.%I owner to supabase_storage_admin', r.tablename); end loop;
  for r in select sequencename from pg_sequences where schemaname='storage' loop
    execute format('alter sequence storage.%I owner to supabase_storage_admin', r.sequencename); end loop;
end $$;

grant usage on schema auth    to anon, authenticated, service_role, postgres, dashboard_user, supabase_auth_admin;
grant usage on schema storage to anon, authenticated, service_role, postgres, dashboard_user, supabase_storage_admin;
grant all   on schema auth    to postgres, dashboard_user;
grant all   on schema storage to postgres, dashboard_user;

-- auth: admin tooling only. anon/authenticated deliberately get schema USAGE
-- (for auth.uid()) but NEVER table access to auth.users.
grant all privileges on all tables    in schema auth to supabase_auth_admin, postgres, dashboard_user;
grant all privileges on all sequences in schema auth to supabase_auth_admin, postgres, dashboard_user;
grant all privileges on all routines  in schema auth to supabase_auth_admin, postgres, dashboard_user;

-- storage: the API roles need table access; RLS does the gating.
grant all privileges on all tables    in schema storage to supabase_storage_admin, postgres, dashboard_user, anon, authenticated, service_role;
grant all privileges on all sequences in schema storage to supabase_storage_admin, postgres, dashboard_user, anon, authenticated, service_role;
grant all privileges on all routines  in schema storage to supabase_storage_admin, postgres, dashboard_user, anon, authenticated, service_role;
SQL

# `-h 127.0.0.1` is REQUIRED, not cosmetic. docker exec runs as root inside the
# container and the image's pg_hba is:
#     local all supabase_admin trust
#     local all all            peer map=supabase_map
#     host  all all 127.0.0.1/32 trust
# so a unix-socket connection as supabase_auth_admin fails PEER AUTHENTICATION —
# which reads like a grants failure but is not. (EXECUTION-PLAN Stage 4b2
# documented the socket form; it can never succeed as written.)
AU=$(docker exec -i supabase-db psql -h 127.0.0.1 -U supabase_auth_admin    -d postgres -At -c 'select count(*) from auth.users' 2>&1 || true)
SO=$(docker exec -i supabase-db psql -h 127.0.0.1 -U supabase_storage_admin -d postgres -At -c 'select count(*) from storage.objects' 2>&1 || true)
[[ "$AU" =~ ^[0-9]+$ ]] || die "supabase_auth_admin cannot read auth.users: $AU"
[[ "$SO" =~ ^[0-9]+$ ]] || die "supabase_storage_admin cannot read storage.objects: $SO"
AUTH_USAGE=$(q "select count(*) from (select has_schema_privilege(r, 'auth', 'USAGE') ok
                 from unnest(array['anon','authenticated','service_role']) r) x where ok")
SB=$(q "select count(*) from (select has_table_privilege(r, 'storage.buckets', 'SELECT') ok
         from unnest(array['service_role','anon','authenticated']) r) x where ok")
[ "$AUTH_USAGE" = "3" ] || die "only $AUTH_USAGE/3 API roles have USAGE on schema auth — every RLS policy calling auth.uid() would fail"
[ "$SB" = "3" ] || die "only $SB/3 API roles can SELECT storage.buckets — uploads would 403"
echo "ownership ok (auth.users=$AU storage.objects=$SO); privileges ok (auth USAGE $AUTH_USAGE/3, storage.buckets SELECT $SB/3)"

# ------------------------------------------------------- 4. schema replay
phase "4. Replay repo schema files (EXCLUDING analytics-verify.sql)"
: > "$WORK/schema-replay.log"
for f in "$SCHEMA_SRC"/*.sql; do
    if [ "$(basename "$f")" = "analytics-verify.sql" ]; then
        echo "SKIP (test script, deletes real search_queries rows): $(basename "$f")" \
            | tee -a "$WORK/schema-replay.log"
        continue
    fi
    echo "=== $(basename "$f")" >> "$WORK/schema-replay.log"
    psqli -v ON_ERROR_STOP=0 < "$f" >> "$WORK/schema-replay.log" 2>&1 || true
done
UNEXPECTED=$(grep -i '^ERROR' "$WORK/schema-replay.log" \
    | grep -viE 'already exists|does not exist|duplicate key|cannot drop|is not a|multiple primary keys' || true)
echo "replay: $(grep -ci '^ERROR' "$WORK/schema-replay.log" || true) ERROR lines, \
$(echo "$UNEXPECTED" | grep -c . || true) unexpected"
[ -z "$UNEXPECTED" ] || { echo "$UNEXPECTED" | head -15; echo "(continuing — review $WORK/schema-replay.log)"; }

# ------------------------------------------------------- 5. seed reconcile
phase "5. Reconcile the demo seed the replay inserts"
q "select id from public.communities order by 1" | sort > "$WORK/communities-after.txt"
EXTRA=$(comm -13 "$WORK/communities-cloud.txt" "$WORK/communities-after.txt" | tr '\n' ',' | sed 's/,$//')
if [ -n "$EXTRA" ]; then
    echo "removing seeded community ids: $EXTRA"
    psqli -q -c "begin;
        delete from public.community_members where community_id in ($EXTRA);
        delete from public.communities        where id           in ($EXTRA);
        commit;"
else
    echo "no seeded communities to remove"
fi
# Sequences must land past the real max, or the next insert collides.
psqli -q <<'SQL'
select setval('public.communities_id_seq',
              coalesce((select max(id) from public.communities), 1), true);
select setval('public.search_queries_id_seq',
              coalesce((select max(id) from public.search_queries), 1), true);
SQL
echo "sequences: communities=$(q "select last_value from public.communities_id_seq") \
search_queries=$(q "select last_value from public.search_queries_id_seq")"

# Now every table must be back at the pure-Cloud baseline. Anything else that
# drifted is a schema file writing data it should not — fail loudly.
q "$COUNT_SQL" | sort > "$WORK/counts-after-replay.txt"
if ! diff -u "$WORK/counts-cloud.txt" "$WORK/counts-after-replay.txt" > "$WORK/counts-drift.txt"; then
    echo "!! row counts drifted from the Cloud baseline after replay+reconcile:"
    grep -E '^[+-][^+-]' "$WORK/counts-drift.txt"
    die "unreconciled drift — do NOT cut over"
fi
echo "all $(wc -l < "$WORK/counts-cloud.txt") tables match the Cloud baseline exactly"

# ------------------------------------------------ 6. rewrite absolute URLs
phase "6. Rewrite Cloud storage URLs -> $NEW_HOST"
# Derived, not hardcoded: sweep EVERY text column in public. Stage 6 originally
# listed four columns and communities.banner_url was nearly missed.
psqli -q <<SQL
do \$\$
declare r record; n bigint; total bigint := 0;
begin
  for r in
    select c.table_schema s, c.table_name t, c.column_name col
    from information_schema.columns c
    join pg_class pc on pc.relname = c.table_name
    join pg_namespace pn on pn.oid = pc.relnamespace and pn.nspname = c.table_schema
    where c.table_schema = 'public' and c.data_type in ('text','character varying')
      and pc.relkind = 'r'
  loop
    execute format('update %I.%I set %I = replace(%I, %L, %L) where %I like %L',
                   r.s, r.t, r.col, r.col, '$CLOUD_HOST', '$NEW_HOST', r.col, '%$CLOUD_REF%');
    get diagnostics n = row_count;
    if n > 0 then
      raise notice 'rewrote % rows in %.%.%', n, r.s, r.t, r.col;
      total := total + n;
    end if;
  end loop;
  raise notice 'total rows rewritten: %', total;
end \$\$;
SQL
REMAIN=$(psqli -At <<SQL
select coalesce(sum(n),0) from (
  select (xpath('/row/c/text()', query_to_xml(
    format('select count(*) as c from %I.%I where %I like ''%%$CLOUD_REF%%''',
           c.table_schema, c.table_name, c.column_name), false, true, '')))[1]::text::bigint n
  from information_schema.columns c
  join pg_class pc on pc.relname=c.table_name
  join pg_namespace pn on pn.oid=pc.relnamespace and pn.nspname=c.table_schema
  where c.table_schema='public' and c.data_type in ('text','character varying') and pc.relkind='r'
) x;
SQL
)
[ "$REMAIN" = "0" ] || die "$REMAIN values still contain $CLOUD_REF after the rewrite"
echo "absolute-URL sweep: 0 remaining references to $CLOUD_REF"

# ------------------------------------------- 7. restart, THEN storage re-upload
phase "7. Restart auth/rest/storage, THEN kong, BEFORE the upload"
# Ordering here is load-bearing, and the EXECUTION-PLAN had it wrong twice over.
#
#  (a) The restart must come BEFORE the storage upload, not after (the plan put
#      it at step 5, after the loop). storage-api caches its schema/connection
#      view and every PUT fails against a freshly --clean-restored database.
#
#  (b) Kong MUST be restarted after them. `docker compose restart` gives each
#      container a NEW IP on the bridge network, and Kong caches the old one in
#      its DNS resolver. Measured: Kong kept dialling 172.19.0.9:5000 with
#      "connect() failed (111: Connection refused)" while storage had moved to
#      172.19.0.7, producing bursts of 502s that no amount of retrying fixes
#      until Kong's DNS TTL happens to expire. This is the same failure mode
#      already recorded for `docker swarm leave` breaking Docker's embedded DNS.
#      At cutover that would be intermittent 502s on the live API.
(cd "$COMPOSE_DIR" && docker compose restart auth rest storage) 2>&1 | tail -3
(cd "$COMPOSE_DIR" && docker compose restart kong) 2>&1 | tail -1
for i in $(seq 1 45); do
    H=$(docker ps --filter name=supabase-auth --filter name=supabase-rest \
                  --filter name=supabase-storage --filter name=supabase-kong \
                  --format '{{.Status}}' | grep -c healthy || true)
    [ "$H" = "4" ] && break
    sleep 2
done
echo "auth/rest/storage/kong healthy: $H/4"
[ "$H" = "4" ] || die "services did not return healthy"
# Prove Kong now resolves storage to the CURRENT container IP, rather than
# discovering it one 502 at a time.
SIP=$(docker inspect supabase-storage --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
KIP=$(docker exec supabase-kong sh -c 'getent hosts storage' 2>/dev/null | awk '{print $1}')
[ "$SIP" = "$KIP" ] || die "kong resolves storage to $KIP but it is at $SIP — restart kong"
echo "kong -> storage resolves to $SIP (current)"
sleep 3

# ------------------------------------------------- 7. storage re-upload
phase "8. Re-upload storage objects through the Storage API"
# The restored metadata carries Cloud's version UUIDs again, so the local files
# no longer satisfy bucket/key/version. Never `docker cp` — always the API.
q "select bucket_id || '/' || name from storage.objects" > "$WORK/storage-paths.txt"
TOTAL=$(grep -c . "$WORK/storage-paths.txt" || true)
mkdir -p "$HOME/storage-backup"
UP=0; DLF=0; UPF=0
while IFS= read -r p; do
    [ -z "$p" ] && continue
    if ! curl -sfL --create-dirs -o "$HOME/storage-backup/$p" "$CLOUD_HOST/storage/v1/object/public/$p"; then
        echo "  DL-FAILED: $p"; DLF=$((DLF+1)); continue
    fi
    ctype=$(file -b --mime-type "$HOME/storage-backup/$p")
    # Retry with backoff. Immediately after `docker compose restart storage` the
    # container reports healthy while its pool is still warming, and Kong returns
    # intermittent 502s on the upstream. Measured: 26/26 fail with no retry,
    # 15/26 with a 4-try 1s backoff, 1/26 with 4-try 1-3s, 0/26 here. Every one
    # succeeded on a manual retry seconds later, so this is flakiness, not a
    # broken object — but the read-back below is what actually proves it.
    ok=0
    for attempt in 1 2 3 4 5 6; do
        code=$(curl -s -o /dev/null -w '%{http_code}' -X POST \
            "http://localhost:8000/storage/v1/object/$p" \
            -H "Authorization: Bearer $SERVICE_KEY" -H "apikey: $SERVICE_KEY" \
            -H "x-upsert: true" -H "Content-Type: $ctype" \
            --data-binary "@$HOME/storage-backup/$p")
        case "$code" in 200|201) ok=1; break;; esac
        sleep $((attempt * 3))
    done
    if [ "$ok" = 1 ]; then UP=$((UP+1)); else echo "  UP-FAILED ($code): $p"; UPF=$((UPF+1)); fi
done < "$WORK/storage-paths.txt"
echo "storage: $UP/$TOTAL uploaded, $DLF download failures, $UPF upload failures"
[ "$DLF" = "0" ] && [ "$UPF" = "0" ] || die "storage sync incomplete"

# The POST status is what the API claimed. This is what a browser will actually
# get — the only check that proves disk and metadata agree.
BADGET=0
while IFS= read -r p; do
    [ -z "$p" ] && continue
    read -r code size <<<"$(curl -s -o /dev/null -w '%{http_code} %{size_download}' \
        "http://localhost:8000/storage/v1/object/public/$p")"
    if [ "$code" != "200" ] || [ "$size" -lt 1 ]; then
        echo "  READBACK-FAILED ($code, $size bytes): $p"; BADGET=$((BADGET+1))
    fi
done < "$WORK/storage-paths.txt"
[ "$BADGET" = "0" ] || die "$BADGET objects do not serve after upload"
echo "read-back: all $TOTAL objects serve 200 with a body"

# ------------------------------------------------------------ 8. restart
# ------------------------------------------------------------ 9. verify
phase "9. Verify"
ANON=$(grep '^ANON_KEY=' "$COMPOSE_DIR/.env" | cut -d= -f2-)
fail=0
chk() { # name expected actual
    if [ "$2" = "$3" ]; then printf '  OK   %-46s %s\n' "$1" "$3"
    else printf '  FAIL %-46s expected %s got %s\n' "$1" "$2" "$3"; fail=1; fi
}
chk "REST public_profiles" 200 "$(curl -s -o /dev/null -w '%{http_code}' \
    -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
    'http://localhost:8000/rest/v1/public_profiles?select=username&limit=1')"
chk "RPC is_creator" 200 "$(curl -s -o /dev/null -w '%{http_code}' -X POST \
    -H "apikey: $ANON" -H "Authorization: Bearer $ANON" -H 'Content-Type: application/json' \
    -d '{}' 'http://localhost:8000/rest/v1/rpc/is_creator')"
chk "auth health" 200 "$(curl -s -o /dev/null -w '%{http_code}' \
    -H "apikey: $ANON" 'http://localhost:8000/auth/v1/health')"
FIRST=$(head -1 "$WORK/storage-paths.txt")
chk "storage object serves" 200 "$(curl -s -o /dev/null -w '%{http_code}' \
    "http://localhost:8000/storage/v1/object/public/$FIRST")"
chk "cloud URL references remaining" 0 "$REMAIN"
q "$COUNT_SQL" | sort > "$WORK/counts-final.txt"
if diff -q "$WORK/counts-cloud.txt" "$WORK/counts-final.txt" >/dev/null; then
    printf '  OK   %-46s %s tables\n' "row counts == Cloud" "$(wc -l < "$WORK/counts-final.txt")"
else
    printf '  FAIL %-46s\n' "row counts == Cloud"; diff -u "$WORK/counts-cloud.txt" "$WORK/counts-final.txt"; fail=1
fi

echo
ELAPSED=$(( $(date +%s) - T0 ))
if [ "$fail" = 0 ]; then
    echo "STAGE 10a SYNC COMPLETE in ${ELAPSED}s — the stack matches Cloud."
    echo "Cutover (Stage 10b DNS flip) is the ONLY remaining step."
else
    echo "STAGE 10a SYNC FAILED after ${ELAPSED}s — DO NOT CUT OVER."
    exit 1
fi
