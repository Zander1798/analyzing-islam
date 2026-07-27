#!/bin/bash
# ===========================================================================
# Stage 10a — final sync, workstation side.
#
#   ./scripts/stage10a-final-sync.sh            # dump, ship, sync, verify
#   ./scripts/stage10a-final-sync.sh --dry-run  # dump + ship only, no restore
#
# Splits deliberately: the Supabase Cloud credential stays on the workstation
# (~/secrets/analyzingislam/pooler.env, mode 600) and never lands on the VPS.
# Everything from the dump onward runs in ~/stage10a-sync.sh on the VPS, which
# is idempotent, timed, and refuses to finish on any drift.
#
# Reads no secrets from the repo. Writes no secrets to the repo. The dump is
# written to /tmp on both machines — it contains password hashes, refresh
# tokens and private messages, and must NEVER be committed.
#
# Prereqs, once:
#   ~/secrets/analyzingislam/pooler.env   POOLER_URL='postgresql://...'
#   postgresql-client-17                  (Cloud is 17.6; a v16 pg_dump refuses)
#   scp -r supabase/ deploy@VPS:~/schema-src/
# ===========================================================================
set -euo pipefail

VPS="${VPS:-deploy@72.60.17.245}"
PG_DUMP="${PG_DUMP:-/usr/lib/postgresql/17/bin/pg_dump}"
SECRETS="$HOME/secrets/analyzingislam/pooler.env"
STAMP=$(date +%Y%m%d-%H%M)
DUMP="/tmp/supabase-cloud-$STAMP.sql"
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1
T0=$(date +%s)

step() { echo; echo "=== [$(( $(date +%s) - T0 ))s] $* ==="; }
die()  { echo "!! $*" >&2; exit 1; }

[ -f "$SECRETS" ] || die "missing $SECRETS"
[ -x "$PG_DUMP" ] || die "missing $PG_DUMP — apt install postgresql-client-17"
# shellcheck disable=SC1090
source "$SECRETS"
[ -n "${POOLER_URL:-}" ] || die "POOLER_URL not set in $SECRETS"

step "1. Fresh dump from Supabase Cloud (read-only)"
SRV=$(psql "$POOLER_URL" -tAc 'show server_version;')
echo "cloud server_version=$SRV, pg_dump=$("$PG_DUMP" --version | awk '{print $3}')"
"$PG_DUMP" --clean --if-exists --quote-all-identifiers --no-owner --no-privileges \
    --schema=public --schema=auth --schema=storage \
    "$POOLER_URL" > "$DUMP"
grep -q 'COPY "auth"."users"' "$DUMP" || die "dump has no auth.users data — refusing"
echo "dump: $DUMP ($(stat -c%s "$DUMP") bytes)"

step "2. Ship to the VPS"
scp -q "$DUMP" "$VPS:/tmp/"
# Schema sources must match the repo at cutover time, or the replay is stale.
rsync -az --delete supabase/ "$VPS:schema-src/"
echo "dump + $(ls -1 supabase/*.sql | wc -l) schema files shipped"

if [ "$DRY_RUN" = 1 ]; then
    echo; echo "--dry-run: stopping before the restore. Dump is at $VPS:$DUMP"
    exit 0
fi

step "3. Run the sync on the VPS"
ssh "$VPS" "~/stage10a-sync.sh '$DUMP'"

step "4. Shred the local dump (password hashes, refresh tokens, private messages)"
shred -u "$DUMP" 2>/dev/null || rm -f "$DUMP"
ssh "$VPS" "shred -u '$DUMP' 2>/dev/null || rm -f '$DUMP'"
echo "local and remote dumps removed"

echo
echo "TOTAL: $(( $(date +%s) - T0 ))s"
echo "Stage 10a complete. Cutover (10b DNS flip) is a separate, human-gated step."
