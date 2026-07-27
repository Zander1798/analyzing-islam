#!/bin/bash
# ---------------------------------------------------------------------------
# analyzingislam.com — prove a backup can actually be restored.
# Stage 11a / Stage 12 gate: "an untested backup is a hope".
#
# Restores the newest (or a named) db-*.sql into a THROWAWAY database inside the
# same Postgres container, then compares every table's row count against the
# live database. Never writes to the live database. Drops the scratch DB at the
# end, including on failure.
#
#   ./test-restore.sh                      # newest backup
#   ./test-restore.sh ~/backups/db-X.sql   # a specific one
# ---------------------------------------------------------------------------
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
SCRATCH="restore_test_$$"
SRC="${1:-$(ls -1t "$BACKUP_DIR"/db-*.sql 2>/dev/null | head -1)}"

[ -n "$SRC" ] && [ -f "$SRC" ] || { echo "no backup found in $BACKUP_DIR"; exit 1; }
echo "restoring: $SRC ($(stat -c%s "$SRC") bytes)"

psql_admin() { docker exec -i supabase-db psql -U supabase_admin "$@"; }

cleanup() {
    psql_admin -d postgres -q -c "drop database if exists \"$SCRATCH\";" >/dev/null 2>&1 || true
}
trap cleanup EXIT

psql_admin -d postgres -q -c "drop database if exists \"$SCRATCH\";"
psql_admin -d postgres -q -c "create database \"$SCRATCH\";"

# The dump is schema-scoped, so the extensions its indexes depend on must exist
# in the scratch DB first (pg_trgm powers the search indexes; vector is the
# chatbot's). A restore that silently skips indexes is not a proven restore.
psql_admin -d "$SCRATCH" -q -c "create schema if not exists extensions;
  create extension if not exists pg_trgm  with schema public;
  create extension if not exists vector   with schema public;
  create extension if not exists pgcrypto with schema extensions;"   # schemas must mirror live, or the object diff reports phantom extras

echo "--- restoring (errors that name YOUR tables are real; role/extension noise is not) ---"
psql_admin -d "$SCRATCH" -v ON_ERROR_STOP=0 < "$SRC" > /tmp/restore-test.log 2>&1 || true
# Expected noise: --clean's DROP SCHEMA public fails because we deliberately
# pre-created pg_trgm/vector there; role and re-create collisions are normal too.
REAL_ERRORS=$(grep -i '^ERROR' /tmp/restore-test.log \
    | grep -viE 'already exists|does not exist|must be owner|permission denied for schema (auth|storage)|cannot drop schema public because other objects depend on it' || true)
if [ -n "$REAL_ERRORS" ]; then
    echo "!! unexpected restore errors:"; echo "$REAL_ERRORS" | head -20
fi
echo "restore log: $(grep -ci '^ERROR' /tmp/restore-test.log || true) ERROR lines total, \
$(echo "$REAL_ERRORS" | grep -c . || true) unexpected"

COUNT_SQL="
select n.nspname || '.' || c.relname as t,
       (xpath('/row/c/text()', query_to_xml(
          format('select count(*) as c from %I.%I', n.nspname, c.relname),
          false, true, '')))[1]::text::bigint as n
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where c.relkind = 'r' and n.nspname in ('public','auth','storage')
order by 1;"

psql_admin -d postgres  -At -F'|' -c "$COUNT_SQL" | sort > /tmp/counts-live.txt
psql_admin -d "$SCRATCH" -At -F'|' -c "$COUNT_SQL" | sort > /tmp/counts-restored.txt

echo
echo "--- row counts: live vs restored ---"
LIVE_T=$(wc -l < /tmp/counts-live.txt); REST_T=$(wc -l < /tmp/counts-restored.txt)
echo "tables: live=$LIVE_T restored=$REST_T"
RC=0
if diff -u /tmp/counts-live.txt /tmp/counts-restored.txt > /tmp/counts-diff.txt; then
    NONEMPTY=$(awk -F'|' '$2>0' /tmp/counts-live.txt | wc -l)
    TOTAL=$(awk -F'|' '{s+=$2} END {print s}' /tmp/counts-live.txt)
    echo "IDENTICAL — all $LIVE_T tables match ($NONEMPTY non-empty, $TOTAL rows total)"
    awk -F'|' '$2>0 {printf "    %-34s %s\n", $1, $2}' /tmp/counts-live.txt
else
    echo "MISMATCH:"; cat /tmp/counts-diff.txt; RC=1
fi

# Row counts can match while every index, RLS policy, function and trigger is
# missing — which would restore the data and lose the security model. Compare
# the schema objects by name, not just the rows.
echo
echo "--- schema objects: live vs restored ---"
OBJ_SQL="
select 'index:'  || schemaname || '.' || indexname  from pg_indexes where schemaname in ('public','auth','storage')
union all select 'policy:' || schemaname || '.' || tablename || '.' || policyname from pg_policies where schemaname in ('public','auth','storage')
union all select 'function:' || n.nspname || '.' || p.proname from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','auth','storage')
union all select 'trigger:' || c.relname || '.' || t.tgname from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace where not t.tgisinternal and n.nspname in ('public','auth','storage')
union all select 'view:' || schemaname || '.' || viewname from pg_views where schemaname in ('public','auth','storage')
union all select 'rls_enabled:' || n.nspname || '.' || c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.relrowsecurity and n.nspname in ('public','auth','storage');"
psql_admin -d postgres   -At -c "$OBJ_SQL" | sort > /tmp/obj-live.txt
psql_admin -d "$SCRATCH" -At -c "$OBJ_SQL" | sort > /tmp/obj-restored.txt
for k in index policy function trigger view rls_enabled; do
    a=$(grep -c "^$k:" /tmp/obj-live.txt || true)
    b=$(grep -c "^$k:" /tmp/obj-restored.txt || true)
    printf '    %-12s live=%-4s restored=%-4s %s\n' "$k" "$a" "$b" \
        "$([ "$a" = "$b" ] && echo OK || echo MISMATCH)"
done
if ! diff -u /tmp/obj-live.txt /tmp/obj-restored.txt > /tmp/obj-diff.txt; then
    echo "  objects present live but NOT restored (or vice versa):"
    grep -E '^[+-][^+-]' /tmp/obj-diff.txt | head -30
    RC=1
else
    echo "    all $(wc -l < /tmp/obj-live.txt) schema objects identical"
fi

echo
[ "$RC" = 0 ] && echo "RESTORE TEST PASSED" || echo "RESTORE TEST FAILED"
exit $RC
