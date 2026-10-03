#!/usr/bin/env bash
set -euo pipefail

fail() { echo "FLR0415_QEMU=FAIL reason=$1" >&2; exit 1; }
[ "$#" -eq 1 ] || fail 'usage: preflight|start'
mode=$1
case "$mode" in preflight|start) ;; *) fail invalid-mode ;; esac
: "${BUILD_EVIDENCE:?BUILD_EVIDENCE-role-required}"
[[ "$BUILD_EVIDENCE" = /* && -d "$BUILD_EVIDENCE" ]] || fail evidence-role-invalid
run_id=flr0415-0001
run_parent=$BUILD_EVIDENCE/$run_id
run_dir=$run_parent/qemu
qmp=$run_dir/qmp-0415.sock
serial_port=10940
ssh_port=10941
telnet_port=10942
memory_mb=6144
command_record=$BUILD_EVIDENCE/flr0414-0001/qemu/runqemu-1-command.txt
[ -r "$command_record" ] || fail prior-runqemu-record-missing
mapfile -t artifact_paths < <(python3 - "$command_record" <<'PY'
import shlex,sys
words=shlex.split(open(sys.argv[1]).read().strip())
if len(words)<4: raise SystemExit('saved runqemu command has fewer than four arguments')
print('\n'.join(words[1:4]))
PY
)
[ "${#artifact_paths[@]}" -eq 3 ] || fail prior-runqemu-artifact-parse
kernel=${artifact_paths[0]}
rootfs=${artifact_paths[1]}
qemuboot=${artifact_paths[2]}
case "$qemuboot" in */deploy/images/qemux86-64/*.qemuboot.conf) tmpdir=${qemuboot%/deploy/images/qemux86-64/*} ;; *) fail qemuboot-role-mismatch ;; esac
case "$tmpdir" in */tmp) build_dir=${tmpdir%/tmp} ;; *) fail build-tmpdir-role-mismatch ;; esac
[ -r "$build_dir/conf/local.conf" ] || fail fixed-build-local-conf-missing
[ -r "$build_dir/conf/templateconf.cfg" ] || fail fixed-build-templateconf-missing
grep -Eq "^MACHINE[[:space:]]*=[[:space:]]*['\"]?qemux86-64['\"]?[[:space:]]*$" "$build_dir/conf/local.conf" || fail fixed-machine-mismatch
tmp_setting=$(grep -E '^[[:space:]]*TMPDIR[[:space:]]*=' "$build_dir/conf/local.conf" | tail -n 1)
case "$tmp_setting" in *"$build_dir/tmp"*|*'${TOPDIR}/tmp'*) ;; *) fail fixed-tmpdir-role-mismatch ;; esac
resolved_tmpdir=$(readlink -f "$tmpdir")
resolved_config_tmpdir=$(readlink -f "$build_dir/tmp")
[ "$resolved_tmpdir" = "$resolved_config_tmpdir" ] || fail resolved-tmpdir-mismatch
check_digest() {
    local path=$1 expected=$2 actual
    [ -r "$path" ] || fail "artifact-unreadable:$(basename "$path")"
    actual=$(sha256sum "$path" | awk '{print $1}')
    [ "$actual" = "$expected" ] || fail "artifact-hash-mismatch:$(basename "$path")"
}
check_digest "$rootfs" f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08
check_digest "$kernel" 3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74
check_digest "$qemuboot" 3872b66339ac3601c704f1b54cab5630796ccf5f0f95ebc4e7077210e89d107f
templateconf=$(sed -n '1p' "$build_dir/conf/templateconf.cfg")
[ -n "$templateconf" ] || fail fixed-build-templateconf-empty
mapfile -t oe_candidates < <(find "$HOME" /mnt/yocto -maxdepth 10 \( -name .git -o -name .cache -o -name .local -o -name node_modules -o -name downloads -o -name sstate-cache -o -name tmp \) -prune -o -type f -path '*/external/poky/oe-init-build-env' -print 2>/dev/null | sort -u)
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

owner_result=$(python3 - <<'PY'
import os,pathlib
owners=[]
for e in os.scandir('/proc'):
 if not e.name.isdigit(): continue
 try:
  a=[os.fsdecode(x) for x in pathlib.Path('/proc/'+e.name+'/cmdline').read_bytes().split(b'\0') if x]
  x=pathlib.Path(os.readlink('/proc/'+e.name+'/exe')).name
  n=[pathlib.Path(v).name for v in a]
  r=set()
  if x.startswith('qemu-system-') or any(v.startswith('qemu-system-') for v in n): r.add('qemu')
  if x=='runqemu' or 'runqemu' in n: r.add('runqemu')
  if x=='flutter-auto' or 'flutter-auto' in n: r.add('flutter-auto')
  if x=='bitbake' or 'bitbake' in n: r.add('bitbake')
  if r: owners.append(','.join(sorted(r)))
 except (OSError,ProcessLookupError): pass
print(','.join(owners) if owners else 'none')
PY
)
[ "$owner_result" = none ] || fail "residual-owner:$owner_result"
for port in "$serial_port" "$ssh_port" "$telnet_port"; do
    if ss -H -ltn "( sport = :$port )" 2>/dev/null | grep -q .; then fail "port-in-use:$port"; fi
done

if [ "$mode" = preflight ]; then
    { [ ! -e "$run_parent" ] && [ ! -L "$run_parent" ]; } || fail run-id-already-consumed
    echo 'FLR0415_QEMU_PREFLIGHT=PASS image=FLR-0410-0001 qemu=NOT_STARTED owners=none ports=free'
    exit 0
fi

[ -d "$run_dir" ] || fail staged-run-directory-missing
[ -r "$run_dir/qemu-runtime-harness.sh" ] || fail harness-not-staged
[ -r "$run_dir/qemu-pixel-capture.py" ] || fail qmp-capture-not-staged
[ ! -e "$qmp" ] || fail stale-qmp-socket
harness=$run_dir/qemu-runtime-harness.sh
test "$(sha256sum "$harness" | awk '{print $1}')" = 4b6160e0e52d4c38ae113f86f686059142469206cd0287f5d856bbe72d6504ed || fail harness-hash-mismatch
test "$(sha256sum "$run_dir/qemu-pixel-capture.py" | awk '{print $1}')" = df826ef28df367d4de42225004f74ce3d2f016a8c2aea42275a8b13b5b233ef1 || fail qmp-capture-hash-mismatch
common=(--run-dir "$run_dir" --qmp "$qmp" --oe-init "$oe_init" --build-dir "$build_dir" --runqemu-bin "$runqemu_bin" --qemuboot "$qemuboot" --kernel "$kernel" --rootfs "$rootfs" --kernel-sha256 3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74 --rootfs-sha256 f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08 --serial-port "$serial_port" --ssh-port "$ssh_port" --telnet-port "$telnet_port" --memory-mb "$memory_mb")
"$harness" start "${common[@]}"
echo 'FLR0415_QEMU_START=PASS image=FLR-0410-0001 memory_mb=6144'
