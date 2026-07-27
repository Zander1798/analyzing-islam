#!/bin/bash
# ---------------------------------------------------------------------------
# analyzingislam.com — nightly backup of the self-hosted Supabase stack.
# Stage 11a of docs/migration/EXECUTION-PLAN.md.
#
# Design notes (each one is a bug the original runbook version had):
#   * Storage lives in the BIND MOUNT ~/supabase-selfhost/volumes/storage, not
#     /var/lib/docker/volumes. Tarring the latter backs up nothing and needs root.
#   * Prune BOTH artefact patterns. The original pruned *.sql only, so the tars
#     grew without limit.
#   * No `|| true`. A swallowed failure produces a backup directory full of
#     confidence and no data. set -euo pipefail + an ERR trap instead.
#   * Write to .partial and rename only on success, so a failed run can never
#     leave a truncated file that looks like a backup.
#   * Assert the dump actually contains rows before accepting it — an empty but
#     syntactically valid dump is the failure mode that hurts most.
#   * Dump flags mirror Stage 4a exactly, so the documented restore procedure
#     (4b restore as supabase_admin, then 4b2 ownership/grants) applies unchanged.
# ---------------------------------------------------------------------------
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
STORAGE_DIR="$HOME/supabase-selfhost/volumes/storage"
RETAIN_DAYS="${RETAIN_DAYS:-14}"
STAMP=$(date +%Y%m%d-%H%M)
STATUS_FILE="$BACKUP_DIR/LAST_RUN"

log() { echo "[$(date -Is)] $*"; }

fail() {
    local line=$1
    log "FAILED at line $line"
    printf 'FAIL %s line=%s\n' "$(date -Is)" "$line" > "$STATUS_FILE"
    logger -t ai-backup "analyzingislam backup FAILED at line $line"
    rm -f "$BACKUP_DIR"/*.partial
    exit 1
}
trap 'fail $LINENO' ERR

mkdir -p "$BACKUP_DIR"

# ---- 1. database -----------------------------------------------------------
DB_OUT="$BACKUP_DIR/db-$STAMP.sql"
log "dumping database -> $(basename "$DB_OUT")"
docker exec supabase-db pg_dump -U supabase_admin -d postgres \
    --clean --if-exists --quote-all-identifiers --no-owner --no-privileges \
    --schema=public --schema=auth --schema=storage \
    > "$DB_OUT.partial"

# An empty-but-valid dump is the dangerous case: assert real content.
USERS=$(grep -c 'COPY "auth"."users"' "$DB_OUT.partial" || true)
BYTES=$(stat -c%s "$DB_OUT.partial")
if [ "$USERS" -lt 1 ] || [ "$BYTES" -lt 100000 ]; then
    log "dump failed sanity check: auth.users COPY blocks=$USERS bytes=$BYTES"
    false
fi
mv "$DB_OUT.partial" "$DB_OUT"
log "database ok: $BYTES bytes"

# ---- 2. roles --------------------------------------------------------------
# Restoring into a fresh Postgres needs the role definitions to exist first.
ROLES_OUT="$BACKUP_DIR/roles-$STAMP.sql"
docker exec supabase-db pg_dumpall -U supabase_admin --globals-only --no-role-passwords \
    > "$ROLES_OUT.partial"
mv "$ROLES_OUT.partial" "$ROLES_OUT"
log "roles ok: $(stat -c%s "$ROLES_OUT") bytes"

# ---- 3. storage objects ----------------------------------------------------
STO_OUT="$BACKUP_DIR/storage-$STAMP.tar.gz"
[ -d "$STORAGE_DIR" ] || { log "storage bind mount missing: $STORAGE_DIR"; false; }
tar czf "$STO_OUT.partial" -C "$HOME/supabase-selfhost/volumes" storage
FILES=$(tar tzf "$STO_OUT.partial" | grep -c -v '/$' || true)
DB_OBJECTS=$(docker exec supabase-db psql -U supabase_admin -d postgres -At \
    -c 'select count(*) from storage.objects')
if [ "$FILES" -lt "$DB_OBJECTS" ]; then
    log "storage tar has $FILES files but storage.objects has $DB_OBJECTS rows"
    false
fi
mv "$STO_OUT.partial" "$STO_OUT"
log "storage ok: $FILES files for $DB_OBJECTS rows"

# ---- 4. prune BOTH patterns ------------------------------------------------
PRUNED=$(find "$BACKUP_DIR" -maxdepth 1 -type f \
    \( -name '*.sql' -o -name '*.tar.gz' \) -mtime +"$RETAIN_DAYS" -print -delete | wc -l)
log "pruned $PRUNED artefacts older than $RETAIN_DAYS days"

printf 'OK %s db=%s roles=%s storage=%s files=%s\n' \
    "$(date -Is)" "$(basename "$DB_OUT")" "$(basename "$ROLES_OUT")" \
    "$(basename "$STO_OUT")" "$FILES" > "$STATUS_FILE"
log "done. $(du -sh "$BACKUP_DIR" | cut -f1) in $BACKUP_DIR"
