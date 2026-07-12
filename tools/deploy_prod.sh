#!/usr/bin/env bash
# Renders and deploys the 0ver.org site on the production host.
#
# Run hourly from cron via a small server-local stub that first
# fast-forwards ~/zerover-src to origin/master, then execs this script
# from the fresh checkout. Builds land in ~/zerover/builds/<utcstamp>-<sha>/
# and ~/zerover/public is an atomically-swapped symlink to the live build,
# so a failed run never replaces the live site.
#
# Subcommands:
#   (none)                 render + deploy if HEAD isn't already live
#   rollback               revert to the previously live build (run twice
#                          to roll forward again)
#   report-failure <msg>   log + report an external failure (used by the
#                          cron stub when git pull fails)
#
# Failures are reported to Sentry when ~/zerover/.sentry_dsn exists
# (plain DSN on one line); otherwise reporting is log-only.
set -euo pipefail

SRC="$HOME/zerover-src"
WEB="$HOME/zerover"
BUILDS="$WEB/builds"
PUBLIC="$WEB/public"
PREV_FILE="$WEB/.previous_build"
DSN_FILE="$WEB/.sentry_dsn"
PYTHON="$SRC/.venv/bin/python"
CHERT="$SRC/.venv/bin/chert"
KEEP=10
MONITOR_SLUG="deploy-0ver"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

_sentry_parts() {  # stdout: "<key> <host> <project>"; fails if no DSN file
    local dsn rest key host project
    dsn=$(cat "$DSN_FILE" 2>/dev/null) || return 1
    [[ -n "$dsn" ]] || return 1
    rest=${dsn#https://}
    key=${rest%%@*}
    rest=${rest#*@}
    host=${rest%%/*}
    project=${rest##*/}
    echo "$key $host $project"
}

sentry_event() {  # $1 = message; never fails the caller
    local parts key host project msg
    parts=$(_sentry_parts) || { log "no sentry dsn; event not sent"; return 0; }
    read -r key host project <<<"$parts"
    msg=${1//\"/\\\"}
    msg=${msg//$'\n'/ }
    curl -sS -m 10 -o /dev/null "https://$host/api/$project/store/" \
        -H 'Content-Type: application/json' \
        -H "X-Sentry-Auth: Sentry sentry_version=7, sentry_key=$key, sentry_client=deploy-prod-sh/1.0" \
        -d "{\"message\":\"$msg\",\"level\":\"error\",\"platform\":\"other\",\"logger\":\"deploy_prod.sh\",\"server_name\":\"0ver-prod\",\"tags\":{\"component\":\"site-deploy\"}}" \
        || log "sentry event send failed"
}

sentry_checkin() {  # $1 = ok|error; never fails the caller
    local parts key host project
    parts=$(_sentry_parts) || return 0
    read -r key host project <<<"$parts"
    curl -sS -m 10 -o /dev/null \
        "https://$host/api/$project/cron/$MONITOR_SLUG/$key/?status=$1" \
        || log "sentry check-in failed"
}

die() {
    log "ERROR: $*"
    sentry_event "0ver deploy failed: $*"
    sentry_checkin error
    exit 1
}

swap_public() {  # $1 = absolute build dir; rename(2) is atomic for nginx
    ln -sfn "$1" "$PUBLIC.tmp"
    mv -T "$PUBLIC.tmp" "$PUBLIC"
}

case "${1:-}" in
rollback)
    prev=$(cat "$PREV_FILE" 2>/dev/null) || die "no $PREV_FILE to roll back to"
    [[ -d "$prev" ]] || die "previous build $prev is gone"
    cur=$(readlink -f "$PUBLIC")
    swap_public "$prev"
    echo "$cur" > "$PREV_FILE"
    log "rolled back: public -> $prev (roll forward by running rollback again)"
    exit 0
    ;;
report-failure)
    die "${2:-unspecified failure reported by cron stub}"
    ;;
esac

cd "$SRC"
sha=$(git rev-parse --short HEAD)

current=$(readlink "$PUBLIC" 2>/dev/null || true)
if [[ -n "$current" && "$current" == *"-$sha" ]]; then
    log "up to date at $sha; nothing to do"
    sentry_checkin ok
    exit 0
fi

# Input gate: never render from a corrupt data file.
"$PYTHON" -c "import json; json.load(open('projects.json'))" \
    || die "projects.json does not parse; aborting before render"

rm -rf site
render_out=$("$CHERT" render 2>&1) || die "chert render failed: ${render_out##*$'\n'}"
err_count=$(grep -c '^E+' <<<"$render_out" || true)
[[ "$err_count" -eq 0 ]] || die "chert render logged $err_count E+ line(s)"

# Output gates: page exists, project table rendered, placeholders replaced.
[[ -s site/index.html ]] || die "site/index.html missing or empty"
grep -q 'class="zv-table"' site/index.html || die "project table missing from index.html"
if grep -q 'PROJECT_TABLE\]' site/index.html; then
    die "unreplaced table placeholder in index.html"
fi

build="$BUILDS/$(date -u +%Y%m%dT%H%M%S)-$sha"
mkdir -p "$BUILDS"
cp -a site "$build"

[[ -n "$current" ]] && echo "$current" > "$PREV_FILE"
swap_public "$build"
log "deployed $sha -> $build"
sentry_checkin ok

# Prune timestamped builds beyond the newest $KEEP ('legacy' never matches 20*).
ls -1dt "$BUILDS"/20* 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -rf
