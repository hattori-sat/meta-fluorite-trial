#!/usr/bin/env bash
set -euo pipefail

fail() {
    echo "canonical repository check: FAIL"
    echo "Open the canonical meta-fluorite-trial clone before making changes."
    exit 1
}

root=$(git rev-parse --show-toplevel 2>/dev/null) || fail
origin=$(git -C "$root" remote get-url origin 2>/dev/null) || fail

case "${origin%.git}" in
    */meta-fluorite-trial) ;;
    *) fail ;;
esac

test -f "$root/TASKS.md" || fail
test -f "$root/AGENTS.md" || fail

echo "canonical repository check: PASS"
