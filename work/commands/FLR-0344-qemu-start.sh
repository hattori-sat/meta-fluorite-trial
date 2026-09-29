#!/usr/bin/env bash
set -euo pipefail

evidence_root=/mnt/yocto/evidence
prior_run_dir=$evidence_root/flr0335-0001/qemu
run_id=${FLR0344_RUN_ID:-flr0344-0001}
case "$run_id" in
    flr0344-[0-9][0-9][0-9][0-9]|flr0347-[0-9][0-9][0-9][0-9]|flr0348-[0-9][0-9][0-9][0-9]) ;;
    *) echo 'FLR0344_QEMU_START_FAIL reason=invalid-run-id' >&2; exit 1 ;;
esac
new_run_parent=$evidence_root/$run_id
run_dir=$new_run_parent/qemu
qmp_name=qmp-0344.sock
case "$run_id" in
    flr0347-*) qmp_name=qmp-0347.sock ;;
    flr0348-*) qmp_name=qmp-0348.sock ;;
esac
qmp=$run_dir/$qmp_name
harness=$prior_run_dir/qemu-runtime-harness.sh

fail() {
    echo "FLR0344_QEMU_START_FAIL reason=$1" >&2
    exit 1
}

test "$(sha256sum "$harness" | awk '{print $1}')" = \
    339472336f14387fd1b72c3d702e510de19ff710c5c203441733a7a59d79aa6d ||
    fail harness-identity
test "$(sha256sum "$prior_run_dir/qemu-pixel-capture.py" | awk '{print $1}')" = \
    992c0428cc85dc61ebdea1e49dc544eed528a961f06faf9dd7fe7de30795ec24 ||
    fail capture-helper-identity
[ ! -e "$run_dir" ] || fail run-directory-already-exists

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

mkdir -p -- "$new_run_parent"
mkdir -- "$run_dir"
cp -- "$0" "$run_dir/FLR-0344-qemu-start.sh"

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
