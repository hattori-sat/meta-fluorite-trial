#!/usr/bin/env bash
set -euo pipefail

fail() {
    echo "FLR0350_QEMU_START=FAIL reason=$1" >&2
    exit 1
}

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
[ "$#" -eq 1 ] || fail 'usage: preflight|start'
mode=$1
case "$mode" in
    preflight) ;;
    start) ;;
    *) fail invalid-mode ;;
esac
: "${FLR0350_RUN_ID:?FLR0350_RUN_ID-is-required}"
run_id=$FLR0350_RUN_ID
python3 "$repo_root/scripts/flr0350_launch_gate.py" --check-run-id "$run_id" >/dev/null ||
    fail invalid-or-consumed-run-id

evidence_root=/mnt/yocto/evidence
prior_run_dir=$evidence_root/flr0335-0001/qemu
new_run_parent=$evidence_root/$run_id
run_dir=$new_run_parent/qemu
qmp=$run_dir/qmp-0350.sock
harness_source=$repo_root/scripts/qemu-runtime-harness.sh
harness=$new_run_parent/qemu-runtime-harness.sh
capture=$prior_run_dir/qemu-pixel-capture.py

if [ "$mode" = preflight ]; then
    { [ ! -e "$new_run_parent" ] && [ ! -L "$new_run_parent" ]; } ||
        fail evidence-parent-already-exists
else
    [ -d "$new_run_parent" ] || fail evidence-parent-missing
fi
{ [ ! -e "$run_dir" ] && [ ! -L "$run_dir" ]; } || fail run-directory-already-exists

if [ "$mode" = preflight ]; then
    [ -x "$harness_source" ] || fail runtime-helper-source-not-executable
    source_commit=$(git -C "$repo_root" rev-parse HEAD) || fail runtime-helper-commit-unavailable
    helper_commit_sha=$(git -C "$repo_root" show "HEAD:scripts/qemu-runtime-harness.sh" |
        sha256sum | awk '{print $1}')
    helper_source_sha=$(sha256sum "$harness_source" | awk '{print $1}')
    [ "$helper_source_sha" = "$helper_commit_sha" ] || fail runtime-helper-not-committed
    echo "FLR0350_RUNTIME_HELPER_PREFLIGHT=PASS source_commit=$source_commit committed_sha256=$helper_commit_sha source_sha256=$helper_source_sha staged=NOT_CREATED"
else
    [ -x "$harness" ] || fail runtime-helper-not-staged-or-executable
    cmp -s "$harness_source" "$harness" || fail runtime-helper-source-mismatch
    source_commit=$(git -C "$repo_root" rev-parse HEAD) || fail runtime-helper-commit-unavailable
    helper_commit_sha=$(git -C "$repo_root" show "HEAD:scripts/qemu-runtime-harness.sh" |
        sha256sum | awk '{print $1}')
    helper_source_sha=$(sha256sum "$harness_source" | awk '{print $1}')
    helper_staged_sha=$(sha256sum "$harness" | awk '{print $1}')
    [ "$helper_source_sha" = "$helper_commit_sha" ] || fail runtime-helper-not-committed
    [ "$helper_source_sha" = "$helper_staged_sha" ] || fail runtime-helper-sha-mismatch
    echo "FLR0350_RUNTIME_HELPER=PASS source_commit=$source_commit committed_sha256=$helper_commit_sha source_sha256=$helper_source_sha staged_sha256=$helper_staged_sha"
fi
test "$(sha256sum "$capture" | awk '{print $1}')" = \
    992c0428cc85dc61ebdea1e49dc544eed528a961f06faf9dd7fe7de30795ec24 ||
    fail capture-helper-identity

target_lines=$(ps -axo pid=,ppid=,stat=,args= | awk '
    $3 !~ /^Z/ {
        executable=$4; sub(/^.*\//, "", executable)
        script=$5; sub(/^.*\//, "", script)
        if (executable ~ /^qemu-system-/ || executable == "runqemu" ||
            executable == "flutter-auto" ||
            (executable ~ /^python[0-9.]*$/ && script == "runqemu"))
            print $1, executable
    }
')
[ -z "$target_lines" ] || fail residual-runtime-process

check_port_free() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        if lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null |
            awk 'NR > 1 { found=1 } END { exit found ? 0 : 1 }'; then
            fail "port-in-use:$port"
        fi
    elif command -v ss >/dev/null 2>&1; then
        if ss -H -ltn "( sport = :$port )" 2>/dev/null | grep -q .; then
            fail "port-in-use:$port"
        fi
    else
        fail missing-command:lsof-or-ss
    fi
}
for port in 10930 10931 10932; do
    check_port_free "$port"
done

mapfile -d '' -t saved_args < <(python3 - "$prior_run_dir/runqemu-1-command.txt" <<'PY'
import shlex
import sys
from pathlib import Path

argv = shlex.split(Path(sys.argv[1]).read_text())
if len(argv) < 4 or Path(argv[0]).name != "runqemu":
    raise SystemExit("saved runqemu command shape mismatch")
sys.stdout.buffer.write(b"\0".join(x.encode() for x in argv[:4]) + b"\0")
PY
)
[ "${#saved_args[@]}" -eq 4 ] || fail saved-command-parse
runqemu_bin=${saved_args[0]}
kernel=${saved_args[1]}
rootfs=${saved_args[2]}
qemuboot=${saved_args[3]}

build_dir=$(dirname "$qemuboot")
while [ "$build_dir" != / ] && [ ! -r "$build_dir/conf/local.conf" ]; do
    build_dir=$(dirname "$build_dir")
done
[ -r "$build_dir/conf/local.conf" ] || fail build-dir-not-found

oe_dir=$(dirname "$(readlink -f "$runqemu_bin")")
while [ "$oe_dir" != / ] && [ ! -r "$oe_dir/oe-init-build-env" ]; do
    oe_dir=$(dirname "$oe_dir")
done
[ -r "$oe_dir/oe-init-build-env" ] || fail oe-init-not-found
oe_init=$oe_dir/oe-init-build-env

[ -x "$runqemu_bin" ] || fail runqemu-not-executable
[ -r "$kernel" ] || fail kernel-not-readable
[ -r "$rootfs" ] || fail rootfs-not-readable
[ -r "$qemuboot" ] || fail qemuboot-not-readable
test "$(sha256sum "$kernel" | awk '{print $1}')" = \
    3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74 ||
    fail kernel-sha256
test "$(sha256sum "$rootfs" | awk '{print $1}')" = \
    5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec ||
    fail rootfs-sha256
test "$(sha256sum "$qemuboot" | awk '{print $1}')" = \
    ef5309f471e4bd159febbbc2c630368ec609d21900179b3694a6fb6c16f8c44a ||
    fail qemuboot-sha256

if [ "$mode" = preflight ]; then
    echo "FLR0350_QEMU_PREFLIGHT=PASS id=$run_id qemu=NOT_STARTED"
    exit 0
fi

mkdir -- "$run_dir"
cp -- "$(readlink -f "$0")" "$run_dir/FLR-0350-qemu-start.sh"

"$harness" preflight \
    --run-dir "$run_dir" --qmp "$qmp" \
    --oe-init "$oe_init" --build-dir "$build_dir" \
    --runqemu-bin "$runqemu_bin" --qemuboot "$qemuboot" \
    --kernel "$kernel" --rootfs "$rootfs" \
    --kernel-sha256 3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74 \
    --rootfs-sha256 5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec \
    --serial-port 10930 --ssh-port 10931 --telnet-port 10932 --memory-mb 6144

"$harness" start \
    --run-dir "$run_dir" --qmp "$qmp" \
    --oe-init "$oe_init" --build-dir "$build_dir" \
    --runqemu-bin "$runqemu_bin" --qemuboot "$qemuboot" \
    --kernel "$kernel" --rootfs "$rootfs" \
    --kernel-sha256 3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74 \
    --rootfs-sha256 5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec \
    --serial-port 10930 --ssh-port 10931 --telnet-port 10932 --memory-mb 6144
