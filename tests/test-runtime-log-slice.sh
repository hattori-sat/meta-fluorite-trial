#!/usr/bin/env bash
set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/fluorite-log-slice.XXXXXX")
trap 'rm -rf "$tmp_root"' EXIT
raw_log="$tmp_root/raw.log"
{
    printf '%s\n' 'boot noise'
    printf 'noise-%03d\n' $(seq 1 150)
    printf '%s\n' 'ERROR: first actionable boundary'
    printf 'FLUORITE_NATIVE_FRAME %03d\n' $(seq 1 10)
    printf '%s\n' 'FLR0026_TARGET_DRAW2 swapchain=true'
    printf '%s\n' 'FLR0026_VK_QUEUE_PRESENT result=0'
    printf '%s\n' 'wl_surface.commit'
} > "$raw_log"

before=$(shasum -a 256 "$raw_log" | awk '{print $1}')
output=$(bash "$repo_root/scripts/runtime-log-slice.sh" --max-lines 6 "$raw_log")
after=$(shasum -a 256 "$raw_log" | awk '{print $1}')

test "$before" = "$after"
printf '%s\n' "$output" | rg -q '^runtime-log-slice=PASS total_lines=165 selected=13 errors=1 shown_limit=6$'
printf '%s\n' "$output" | rg -q 'ERROR: first actionable boundary'
printf '%s\n' "$output" | rg -q 'FLUORITE_NATIVE_FRAME 001'
printf '%s\n' "$output" | rg -q 'FLR0026_VK_QUEUE_PRESENT result=0'
printf '%s\n' "$output" | rg -q 'wl_surface.commit'
printf '%s\n' "$output" | rg -q 'omitted=7 selected lines'

printf '%s\n' 'runtime log slice test: PASS'
