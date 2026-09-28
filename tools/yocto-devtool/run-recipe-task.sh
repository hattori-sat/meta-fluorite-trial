#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Usage: $0 <recipe> <parse|patch|compile|install|package|populate_sysroot>" >&2
    exit 2
}

fail() {
    echo "fluorite-recipe-task: $1" >&2
    exit 1
}

test "$#" -eq 2 || usage
recipe=$1
task=$2

case "$recipe" in
    agl-ivi-image-*|core-image-*) fail "image recipes are forbidden in the Mac verification container" ;;
esac
case "$task" in
    parse|patch|compile|install|package|populate_sysroot) ;;
    *) usage ;;
esac

BITBAKE_BIN=${BITBAKE_BIN:-bitbake}
command -v "$BITBAKE_BIN" >/dev/null 2>&1 || fail "BitBake is not available; source the pinned Yocto environment"
if test "$task" = parse; then
    exec "$BITBAKE_BIN" -p "$recipe"
fi
exec "$BITBAKE_BIN" "$recipe" -c "$task"
