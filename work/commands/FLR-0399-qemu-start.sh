#!/usr/bin/env bash
set -euo pipefail

fail() {
    echo "FLR0399_QEMU_START=FAIL reason=$1" >&2
    exit 1
}

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
[ "$#" -eq 1 ] || fail 'usage: preflight|start'
mode=$1
case "$mode" in
    preflight|start) ;;
    *) fail invalid-mode ;;
esac

: "${FLR0399_RUN_ID:?FLR0399_RUN_ID-is-required}"
[[ "$FLR0399_RUN_ID" =~ ^flr0399-[0-9]{4}$ ]] || fail invalid-run-id
run_id=$FLR0399_RUN_ID
: "${BUILD_DIR:?BUILD_DIR-role-required}"
: "${BUILD_TMPDIR:?BUILD_TMPDIR-role-required}"
: "${BUILD_EVIDENCE:?BUILD_EVIDENCE-role-required}"
build_dir=$BUILD_DIR
build_tmpdir=$BUILD_TMPDIR
evidence_root=$BUILD_EVIDENCE
[[ "$build_dir" = /* && "$build_tmpdir" = /* && "$evidence_root" = /* ]] ||
    fail build-roles-must-be-absolute
run_parent=$evidence_root/$run_id
run_dir=$run_parent/qemu
qmp=$run_dir/qmp-0399.sock
serial_port=10930
ssh_port=10931
telnet_port=10932
memory_mb=6144
kernel_sha=3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74
rootfs_sha=80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c
qemuboot_sha=2363530e2f39d4e57465cb89e724327f699b8ab6247d9e1bb75fdc2a60780c10

for source in \
    scripts/flr0399_live_capture.py \
    scripts/flr0399_process_cleanup.py \
    scripts/qemu-runtime-harness.sh \
    scripts/qemu-pixel-capture.py \
    work/commands/FLR-0399-qemu-start.sh; do
    current=$(sha256sum "$repo_root/$source" | awk '{print $1}') || fail "source-unreadable:$source"
    committed=$(git -C "$repo_root" show "HEAD:$source" | sha256sum | awk '{print $1}') ||
        fail "source-not-committed:$source"
    [ "$current" = "$committed" ] || fail "source-differs-from-HEAD:$source"
done

pidfd_probe=$(python3 "$repo_root/scripts/flr0399_process_cleanup.py" --check-capability) ||
    fail 'exact-cleanup-requires-linux-pidfd'
printf '%s\n' "$pidfd_probe"

[ -d "$evidence_root" ] || fail evidence-role-missing
[ -r "$build_dir/conf/local.conf" ] || fail fixed-build-local-conf-missing
[ -r "$build_dir/conf/templateconf.cfg" ] || fail fixed-build-templateconf-missing
{ [ ! -e "$run_parent" ] && [ ! -L "$run_parent" ]; } || fail run-id-already-consumed

grep -Eq "^MACHINE[[:space:]]*=[[:space:]]*['\"]?qemux86-64['\"]?[[:space:]]*$" \
    "$build_dir/conf/local.conf" || fail fixed-machine-mismatch
tmpdir_setting=$(grep -E '^[[:space:]]*TMPDIR[[:space:]]*=' "$build_dir/conf/local.conf" | tail -n 1)
case "$tmpdir_setting" in
    *"$build_dir/tmp"*|*'${TOPDIR}/tmp'*|*'$TOPDIR/tmp'*) tmpdir=$build_dir/tmp ;;
    *) fail fixed-tmpdir-role-mismatch ;;
esac
resolved_tmpdir=$(readlink -f "$tmpdir") || fail fixed-tmpdir-unresolvable
resolved_build_tmpdir=$(readlink -f "$build_tmpdir") || fail BUILD_TMPDIR-role-unresolvable
[ "$resolved_tmpdir" = "$resolved_build_tmpdir" ] || fail BUILD_TMPDIR-role-mismatch
deploy=$tmpdir/deploy/images/qemux86-64
qemuboot=$deploy/agl-ivi-image-flutter-qemux86-64.rootfs-20261001044407.qemuboot.conf
kernel=$deploy/bzImage
rootfs=$deploy/agl-ivi-image-flutter-qemux86-64.rootfs-20261001044407.ext4

check_digest() {
    local path=$1 expected=$2 actual
    [ -r "$path" ] || fail "artifact-unreadable:$(basename "$path")"
    actual=$(sha256sum "$path" | awk '{print $1}')
    [ "$actual" = "$expected" ] || fail "artifact-hash-mismatch:$(basename "$path")"
}
check_digest "$qemuboot" "$qemuboot_sha"
check_digest "$kernel" "$kernel_sha"
check_digest "$rootfs" "$rootfs_sha"

templateconf=$(sed -n '1p' "$build_dir/conf/templateconf.cfg")
[ -n "$templateconf" ] || fail fixed-build-templateconf-empty
mapfile -t oe_candidates < <(
    find "$HOME" /mnt/yocto -maxdepth 10 \
        \( -name .git -o -name .cache -o -name .local -o -name node_modules \
        -o -name downloads -o -name sstate-cache -o -name tmp \) -prune -o \
        -type f -path '*/external/poky/oe-init-build-env' -print 2>/dev/null | sort -u
)
matching_oe=()
for candidate in "${oe_candidates[@]}"; do
    poky=${candidate%/oe-init-build-env}
    if [[ "$templateconf" = /* ]]; then template_dir=$templateconf; else template_dir=$poky/$templateconf; fi
    [ -d "$template_dir" ] && [ -x "$poky/scripts/runqemu" ] && matching_oe+=("$candidate")
done
[ "${#matching_oe[@]}" -eq 1 ] || fail "oe-init-template-match-count:${#matching_oe[@]}"
oe_init=${matching_oe[0]}
runqemu_bin=${oe_init%/oe-init-build-env}/scripts/runqemu

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
        if lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | awk 'NR > 1 { found=1 } END { exit found ? 0 : 1 }'; then
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
for port in "$serial_port" "$ssh_port" "$telnet_port"; do check_port_free "$port"; done

if [ "$mode" = preflight ]; then
    echo "FLR0399_QEMU_PREFLIGHT=PASS run_id=$run_id memory_mb=$memory_mb image=0334 qemu=NOT_STARTED"
    exit 0
fi

mkdir -- "$run_parent"
mkdir -- "$run_dir"
cp -- "$(readlink -f "${BASH_SOURCE[0]}")" "$run_dir/FLR-0399-qemu-start.sh"
cp -- "$repo_root/scripts/flr0399_process_cleanup.py" "$run_dir/FLR-0399-process-cleanup.py"
harness=$repo_root/scripts/qemu-runtime-harness.sh
if "$harness" start \
    --run-dir "$run_dir" --qmp "$qmp" \
    --oe-init "$oe_init" --build-dir "$build_dir" \
    --runqemu-bin "$runqemu_bin" --qemuboot "$qemuboot" \
    --kernel "$kernel" --rootfs "$rootfs" \
    --kernel-sha256 "$kernel_sha" --rootfs-sha256 "$rootfs_sha" \
    --serial-port "$serial_port" --ssh-port "$ssh_port" \
    --telnet-port "$telnet_port" --memory-mb "$memory_mb"; then
    echo "FLR0399_QEMU_START=PASS run_id=$run_id memory_mb=$memory_mb image=0334"
else
    start_status=$?
    cleanup_log=$run_dir/FLR-0399-start-failure-cleanup.log
    {
        echo "start=FAIL exit_status=$start_status"
        if [ -S "$qmp" ]; then
            if "$harness" qmp-quit --qmp "$qmp"; then
                echo qmp-quit=PASS
            else
                qmp_status=$?
                echo "qmp-quit=FAIL exit_status=$qmp_status"
            fi
        else
            echo qmp-quit=SKIPPED_SOCKET_ABSENT
        fi
        if python3 "$repo_root/scripts/flr0399_process_cleanup.py" \
            --qmp "$qmp" --timeout-seconds 3; then
            echo exact-qmp-process-cleanup=PASS
        else
            cleanup_status=$?
            echo "exact-qmp-process-cleanup=FAIL exit_status=$cleanup_status"
        fi
    } >"$cleanup_log" 2>&1
    echo "FLR0399_QEMU_START=FAIL run_id=$run_id exit_status=$start_status cleanup_log=$cleanup_log" >&2
    exit "$start_status"
fi
