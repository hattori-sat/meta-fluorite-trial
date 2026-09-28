#!/usr/bin/env bash
set -euo pipefail

root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
harness=$root/scripts/qemu-runtime-harness.sh

test -x "$harness"
bash -n "$harness"

for mode in preflight start guest-ready serial-login serial-exec summary qmp-quit; do
    grep -Fq "${mode})" "$harness"
done
grep -Fq 'qmp_capabilities' "$harness"
grep -Fq 'qmp=unix:' "$harness"
grep -Fq 'serial file:' "$harness"
grep -Fq 'snapshot' "$harness"
grep -Fq 'SDL_VIDEODRIVER' "$harness"
grep -Fq 'tail -n 400' "$harness"
grep -Fq 'FRAME_BEGIN' "$harness"
grep -Fq 'Application Id:' "$harness"
grep -Fq 'cleanup=PASS' "$harness"
grep -Fq '__FLR_SERIAL_COMMAND_DONE_7B31__' "$harness"
# Process-name behavior and embedded Python compilation are exercised by
# test_qemu_runtime_harness.py, including Linux comm truncation.
grep -Fq 'runqemu' "$harness"
grep -Fq 'flutter-auto' "$harness"

if grep -Eq 'pkill|killall|rm[[:space:]]+-rf' "$harness"; then
    echo 'harness must not use broad process kills or recursive deletion' >&2
    exit 1
fi

echo 'QEMU/runtime harness contract: PASS'
