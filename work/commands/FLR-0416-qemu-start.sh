#!/usr/bin/env bash
set -euo pipefail

fail() { echo "FLR0416_QEMU=FAIL reason=$1" >&2; exit 1; }
[ "$#" -eq 1 ] || fail 'usage: preflight|prepare|start|capture|postflight'
mode=$1
case "$mode" in preflight|prepare|start|capture|postflight) ;; *) fail invalid-mode ;; esac
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
: "${BUILD_EVIDENCE:?BUILD_EVIDENCE-role-required}"
[[ "$BUILD_EVIDENCE" = /* && -d "$BUILD_EVIDENCE" && ! -L "$BUILD_EVIDENCE" ]] || fail evidence-role-invalid

run_parent=$BUILD_EVIDENCE/flr0418-0001
run_dir=$run_parent/qemu
qmp=$run_dir/qmp-0418.sock
if [ "$mode" = preflight ] || [ "$mode" = prepare ]; then
    { [ ! -e "$run_parent" ] && [ ! -L "$run_parent" ]; } || fail run-id-already-consumed
fi
if [ "$mode" = start ] && { [ -e "$run_dir/FLR0418-start-claim" ] || [ -L "$run_dir/FLR0418-start-claim" ]; }; then
    fail start-attempt-already-claimed
fi
serial_port=10943
ssh_port=10944
telnet_port=10945
memory_mb=6144
command_record=$BUILD_EVIDENCE/flr0414-0001/qemu/runqemu-1-command.txt
[ -r "$command_record" ] || fail prior-runqemu-record-missing

mapfile -t artifact_paths < <(python3 - "$command_record" <<'PY'
import shlex
import sys

words = shlex.split(open(sys.argv[1], encoding="utf-8").read().strip())
if len(words) < 4:
    raise SystemExit("saved runqemu command has fewer than four arguments")
print("\n".join(words[1:4]))
PY
)
[ "${#artifact_paths[@]}" -eq 3 ] || fail runqemu-artifact-parse
kernel=${artifact_paths[0]}
rootfs=${artifact_paths[1]}
qemuboot=${artifact_paths[2]}
case "$qemuboot" in
    */deploy/images/qemux86-64/*.qemuboot.conf) tmpdir=${qemuboot%/deploy/images/qemux86-64/*} ;;
    *) fail qemuboot-role-mismatch ;;
esac
case "$tmpdir" in */tmp) build_dir=${tmpdir%/tmp} ;; *) fail build-tmpdir-role-mismatch ;; esac
[ -r "$build_dir/conf/local.conf" ] || fail fixed-build-local-conf-missing
[ -r "$build_dir/conf/templateconf.cfg" ] || fail fixed-build-templateconf-missing
grep -Eq "^MACHINE[[:space:]]*=[[:space:]]*['\"]?qemux86-64['\"]?[[:space:]]*$" "$build_dir/conf/local.conf" || fail fixed-machine-mismatch
tmp_setting=$(grep -E '^[[:space:]]*TMPDIR[[:space:]]*=' "$build_dir/conf/local.conf" | tail -n 1) || fail fixed-tmpdir-setting-unavailable
case "$tmp_setting" in *"$build_dir/tmp"*|*'${TOPDIR}/tmp'*) ;; *) fail fixed-tmpdir-role-mismatch ;; esac
[ "$(readlink -f "$tmpdir")" = "$(readlink -f "$build_dir/tmp")" ] || fail resolved-tmpdir-mismatch

check_digest() {
    local path=$1 expected=$2 actual
    [ -r "$path" ] || fail "artifact-unreadable:$(basename "$path")"
    actual=$(sha256sum "$path" | awk '{print $1}')
    [ "$actual" = "$expected" ] || fail "artifact-hash-mismatch:$(basename "$path")"
}
check_digest "$rootfs" f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08
check_digest "$kernel" 3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74
check_digest "$qemuboot" 3872b66339ac3601c704f1b54cab5630796ccf5f0f95ebc4e7077210e89d107f

preflight_helper=$repo_root/work/commands/flr0416_qemu_preflight.py
[ -r "$preflight_helper" ] && [ ! -L "$preflight_helper" ] || fail preflight-helper-unavailable
stage_sources=(
    scripts/qemu-runtime-harness.sh
    scripts/qemu-pixel-capture.py
    scripts/flr0399_process_cleanup.py
    scripts/flr0416_live_capture.py
    work/commands/FLR-0416-qemu-start.sh
    work/commands/flr0416_qemu_preflight.py
    work/commands/FLR-0416-gdb-smoke.gdb
    work/commands/FLR-0416-prearm-libllvm.gdb
    work/commands/FLR-0416-guest-gdb-smoke.cmd
    work/commands/flr0416_gdb_observer.py
    work/commands/flr0416_gdb_callback.py
    work/commands/flr0416_guest_snapshot.py
)

run_host_preflight() {
    command -v python3 >/dev/null 2>&1 || fail python3-unavailable
    if ! python3 "$preflight_helper" --port "$serial_port" --port "$ssh_port" --port "$telnet_port"; then
        fail host-ownership-or-port-state-unverified
    fi
}

check_headroom() {
    local free_kb available_kb
    free_kb=$(df -Pk "$BUILD_EVIDENCE" | awk 'NR == 2 {print $4}') || fail disk-headroom-query-failed
    case "$free_kb" in ''|*[!0-9]*) fail disk-headroom-unavailable ;; esac
    [ "$free_kb" -ge 1048576 ] || fail disk-headroom-under-1GiB
    available_kb=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo) || fail memory-headroom-query-failed
    case "$available_kb" in ''|*[!0-9]*) fail memory-headroom-unavailable ;; esac
    [ "$available_kb" -ge 8388608 ] || fail memory-headroom-under-8GiB
}

if [ "$mode" = preflight ]; then
    check_headroom
    run_host_preflight
    echo 'FLR0416_QEMU_PREFLIGHT=PASS image=FLR-0410-0001 run_id=fresh headroom=PASS'
    exit 0
fi

if [ "$mode" = prepare ]; then
    check_headroom
    run_host_preflight
    for source in "${stage_sources[@]}"; do
        source_path=$repo_root/$source
        [[ -f "$source_path" && ! -L "$source_path" ]] || fail "stage-source-unavailable:${source##*/}"
    done
    umask 077
    mkdir -- "$run_parent" || fail run-parent-create-failed
    mkdir -- "$run_dir" || fail run-directory-create-failed
    : > "$run_dir/FLR0416-staged-files.sha256"
    for source in "${stage_sources[@]}"; do
        source_path=$repo_root/$source
        staged_path=$run_dir/${source##*/}
        cp -- "$source_path" "$staged_path" || fail "stage-copy-failed:${source##*/}"
        source_sha=$(sha256sum "$source_path" | awk '{print $1}') || fail "stage-source-hash-failed:${source##*/}"
        staged_sha=$(sha256sum "$staged_path" | awk '{print $1}') || fail "stage-copy-hash-failed:${source##*/}"
        [ "$source_sha" = "$staged_sha" ] || fail "stage-copy-mismatch:${source##*/}"
        printf '%s  %s\n' "$source_sha" "${source##*/}" >> "$run_dir/FLR0416-staged-files.sha256"
    done
    echo "FLR0416_STAGE=PASS run_id=flr0418-0001 files=${#stage_sources[@]}"
    exit 0
fi

if [ "$mode" = postflight ]; then
    [[ ! -e "$qmp" && ! -L "$qmp" ]] || fail qmp-socket-remains
    run_host_preflight
    echo 'FLR0416_POSTFLIGHT=PASS image=FLR-0410-0001 qmp=absent target_owners=0 ports=free'
    exit 0
fi

if [ "$mode" = capture ]; then
    [[ -d "$run_parent" && ! -L "$run_parent" && -d "$run_dir" && ! -L "$run_dir" ]] || fail staged-run-directory-missing
    [[ -S "$qmp" && ! -L "$qmp" ]] || fail exact-qmp-socket-not-live
    [[ -s "$run_dir/FLR0416-staged-files.sha256" && ! -L "$run_dir/FLR0416-staged-files.sha256" ]] || fail staged-file-manifest-missing
    test "$(sha256sum "$run_dir/qemu-runtime-harness.sh" | awk '{print $1}')" = 4b6160e0e52d4c38ae113f86f686059142469206cd0287f5d856bbe72d6504ed || fail harness-hash-mismatch
    test "$(sha256sum "$run_dir/qemu-pixel-capture.py" | awk '{print $1}')" = df826ef28df367d4de42225004f74ce3d2f016a8c2aea42275a8b13b5b233ef1 || fail qmp-capture-hash-mismatch
    for source in "${stage_sources[@]}"; do
        source_path=$repo_root/$source
        staged_path=$run_dir/${source##*/}
        [[ -f "$source_path" && ! -L "$source_path" && -f "$staged_path" && ! -L "$staged_path" ]] || fail "staged-source-missing:${source##*/}"
        source_sha=$(sha256sum "$source_path" | awk '{print $1}') || fail "stage-source-hash-failed:${source##*/}"
        staged_sha=$(sha256sum "$staged_path" | awk '{print $1}') || fail "stage-copy-hash-failed:${source##*/}"
        [ "$source_sha" = "$staged_sha" ] || fail "stage-copy-mismatch:${source##*/}"
        grep -Fxq "$source_sha  ${source##*/}" "$run_dir/FLR0416-staged-files.sha256" || fail "stage-manifest-mismatch:${source##*/}"
    done
    exec python3 "$repo_root/scripts/flr0416_live_capture.py" \
        --repo-root "$repo_root" \
        --run-dir "$run_dir" \
        --qmp "$qmp" \
        --serial-port "$serial_port"
fi

[[ -d "$run_parent" && ! -L "$run_parent" && -d "$run_dir" && ! -L "$run_dir" ]] || fail staged-run-directory-missing
[[ -f "$run_dir/qemu-runtime-harness.sh" && ! -L "$run_dir/qemu-runtime-harness.sh" ]] || fail harness-not-staged
[[ -f "$run_dir/qemu-pixel-capture.py" && ! -L "$run_dir/qemu-pixel-capture.py" ]] || fail qmp-capture-not-staged
[[ ! -e "$qmp" && ! -L "$qmp" ]] || fail stale-qmp-socket
harness=$run_dir/qemu-runtime-harness.sh
pixel_capture=$run_dir/qemu-pixel-capture.py
test "$(sha256sum "$harness" | awk '{print $1}')" = 4b6160e0e52d4c38ae113f86f686059142469206cd0287f5d856bbe72d6504ed || fail harness-hash-mismatch
test "$(sha256sum "$pixel_capture" | awk '{print $1}')" = df826ef28df367d4de42225004f74ce3d2f016a8c2aea42275a8b13b5b233ef1 || fail qmp-capture-hash-mismatch
[[ -s "$run_dir/FLR0416-staged-files.sha256" && ! -L "$run_dir/FLR0416-staged-files.sha256" ]] || fail staged-file-manifest-missing
for source in "${stage_sources[@]}"; do
    source_path=$repo_root/$source
    staged_path=$run_dir/${source##*/}
    [[ -f "$source_path" && ! -L "$source_path" && -f "$staged_path" && ! -L "$staged_path" ]] || fail "staged-source-missing:${source##*/}"
    source_sha=$(sha256sum "$source_path" | awk '{print $1}') || fail "stage-source-hash-failed:${source##*/}"
    staged_sha=$(sha256sum "$staged_path" | awk '{print $1}') || fail "stage-copy-hash-failed:${source##*/}"
    [ "$source_sha" = "$staged_sha" ] || fail "stage-copy-mismatch:${source##*/}"
    grep -Fxq "$source_sha  ${source##*/}" "$run_dir/FLR0416-staged-files.sha256" || fail "stage-manifest-mismatch:${source##*/}"
done
templateconf=$(sed -n '1p' "$build_dir/conf/templateconf.cfg")
[ -n "$templateconf" ] || fail fixed-build-templateconf-empty
oe_candidates_file=$run_dir/FLR0416-oe-init-candidates.nul
[[ ! -e "$oe_candidates_file" && ! -L "$oe_candidates_file" ]] || fail stale-oe-discovery-file
if ! find "$HOME" /mnt/yocto -maxdepth 10 \( -name .git -o -name .cache -o -name .local -o -name node_modules -o -name downloads -o -name sstate-cache -o -name tmp \) -prune -o -type f -path '*/external/poky/oe-init-build-env' -print0 > "$oe_candidates_file"; then
    fail oe-init-discovery-failed
fi
mapfile -d '' -t oe_candidates < "$oe_candidates_file"
rm -- "$oe_candidates_file" || fail oe-discovery-file-cleanup-failed
matching_oe=()
for candidate in "${oe_candidates[@]}"; do
    poky=${candidate%/oe-init-build-env}
    if [[ "$templateconf" = /* ]]; then template_dir=$templateconf; else template_dir=$poky/$templateconf; fi
    [ -d "$template_dir" ] && [ -x "$poky/scripts/runqemu" ] && matching_oe+=("$candidate")
done
[ "${#matching_oe[@]}" -eq 1 ] || fail "oe-init-template-match-count:${#matching_oe[@]}"
oe_init=${matching_oe[0]}
runqemu_bin=${oe_init%/oe-init-build-env}/scripts/runqemu
[ -x "$runqemu_bin" ] || fail runqemu-not-executable

check_headroom
run_host_preflight
python3 "$repo_root/scripts/flr0416_live_capture.py" \
    --claim-only start --run-dir "$run_dir" || fail start-attempt-claim-failed
"$harness" start --run-dir "$run_dir" --qmp "$qmp" --oe-init "$oe_init" --build-dir "$build_dir" --runqemu-bin "$runqemu_bin" --qemuboot "$qemuboot" --kernel "$kernel" --rootfs "$rootfs" --kernel-sha256 3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74 --rootfs-sha256 f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08 --serial-port "$serial_port" --ssh-port "$ssh_port" --telnet-port "$telnet_port" --memory-mb "$memory_mb"
echo 'FLR0416_QEMU_START=PASS image=FLR-0410-0001 memory_mb=6144'
