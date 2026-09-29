#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd -- "$repo_root"
start_script=$repo_root/work/commands/FLR-0350-qemu-start.sh
evidence_root=/mnt/yocto/evidence
prior_run_dir=$evidence_root/flr0335-0001/qemu
harness_source=$repo_root/scripts/qemu-runtime-harness.sh
capture=$prior_run_dir/qemu-pixel-capture.py
runtime_command_files=(
    FLR-0350-preflight.cmd
    FLR-0350-launch-paused-production.cmd
    FLR-0350-observe-fifo-read-gate.cmd
    FLR-0350-attach-pre-submit.cmd
    FLR-0350-release-go.cmd
    FLR-0350-wait-symbol-gate.cmd
    FLR-0350-wait-matched-wait.cmd
    FLR-0350-watch-window.cmd
    FLR-0350-interrupt-gdb.cmd
    FLR-0350-capture-runtime-state.cmd
    FLR-0350-stop-recorded-app.cmd
    FLR-0350-preflight-helper-collision.cmd
)
runtime_guest_scripts=(
    FLR-0350-gate-common.sh
    FLR-0350-attach-pre-submit.sh
    FLR-0350-release-go.sh
    FLR-0350-stop-recorded-app.sh
    FLR-0350-interrupt-gdb.sh
)

static_check() {
    bash -n "$0"
    bash -n "$start_script"
    python3 - "$repo_root" <<'PY'
import ast
import base64
import gzip
import re
import shlex
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
runner_text = (root / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
starter_text = (root / "work/commands/FLR-0350-qemu-start.sh").read_text()
preflight_call = 'FLR0350_RUN_ID="$run_id" bash "$start_script" preflight'
start_call = 'FLR0350_RUN_ID="$run_id" bash "$start_script" start'
evidence_create = 'mkdir -- "$parent"'
try:
    if not (runner_text.rindex(preflight_call) < runner_text.rindex(evidence_create)
            < runner_text.rindex(start_call)):
        raise SystemExit("fresh run-ID preflight/start order failed")
except ValueError as exc:
    raise SystemExit("fresh run-ID preflight/start contract missing") from exc
helper_stage = 'cp -- "$harness_source" "$parent/qemu-runtime-harness.sh"'
helper_select = 'harness=$parent/qemu-runtime-harness.sh'
runner_runtime = runner_text.split("run_id=$1\n", 1)[1]
if not re.search(r"(?m)^harness_source=\$repo_root/scripts/qemu-runtime-harness\.sh$", runner_text) or \
   helper_stage not in runner_runtime or helper_select not in runner_runtime:
    raise SystemExit("runtime helper source/staging/selection contract missing")
if not (runner_runtime.index(helper_stage) < runner_runtime.index(helper_select)
        < runner_runtime.rindex(start_call)):
    raise SystemExit("runtime helper must be staged and selected before QEMU start")
if not re.search(r"(?m)^harness_source=\$repo_root/scripts/qemu-runtime-harness\.sh$", starter_text) or \
   not re.search(r"(?m)^harness=\$new_run_parent/qemu-runtime-harness\.sh$", starter_text) or \
   'cmp -s "$harness_source" "$harness"' not in starter_text:
    raise SystemExit("QEMU starter runtime helper provenance contract missing")
head_blob = 'git -C "$repo_root" show "HEAD:scripts/qemu-runtime-harness.sh"'
if head_blob not in runner_runtime or head_blob not in starter_text or \
   '[ -x "$harness_source" ]' not in runner_runtime or \
   '[ -x "$harness" ]' not in starter_text:
    raise SystemExit("runtime helper must be executable and byte-identical to committed HEAD")
if "harness=$prior_run_dir/qemu-runtime-harness.sh" in runner_text.splitlines() or \
   "harness=$prior_run_dir/qemu-runtime-harness.sh" in starter_text.splitlines():
    raise SystemExit("runtime helper still selects or pins a prior-run copy")
capture_sha = "992c0428cc85dc61ebdea1e49dc544eed528a961f06faf9dd7fe7de30795ec24"
if 'capture=$prior_run_dir/qemu-pixel-capture.py' not in runner_text or \
   'capture=$prior_run_dir/qemu-pixel-capture.py' not in starter_text or \
   capture_sha not in starter_text:
    raise SystemExit("historical QMP pixel-capture helper identity changed")
if "${FLR0350_RUN_ID:?" not in starter_text or \
   '--check-run-id "$run_id"' not in starter_text or \
   "${FLR0350_RUN_ID:-flr0350-0001}" in starter_text:
    raise SystemExit("QEMU starter run-ID validation contract failed")
cleanup_body = runner_text.split("cleanup() {", 1)[1].split("\n}\ntrap cleanup EXIT", 1)[0]
if not (
    cleanup_body.index("FLR-0350-interrupt-gdb.cmd")
    < cleanup_body.index('if [ "$gdb_stopped" -eq 1 ]; then')
    < cleanup_body.index("capture_evidence || cleanup_failed=1")
):
    raise SystemExit("failure cleanup may capture while GDB stop is unconfirmed")
if "FLR0350_POST_RUN_CAPTURE=SKIPPED reason=gdb-stop-not-confirmed" not in cleanup_body:
    raise SystemExit("failure cleanup must report skipped capture when GDB remains active")
if "FLR0350_UNRECORDED_TARGET_ABORT=FAIL" not in cleanup_body:
    raise SystemExit("failure cleanup must not interrupt GDB after an unproven target abort")

inventory = re.search(r"(?ms)^runtime_command_files=\(\n(.*?)^\)", runner_text)
if not inventory:
    raise SystemExit("static guest-command inventory missing")
command_names = re.findall(r"(?m)^\s*(FLR-0350-[\w.-]+\.cmd)\s*$", inventory.group(1))
if not command_names or len(command_names) != len(set(command_names)):
    raise SystemExit("static guest-command inventory is empty or duplicated")
static_calls = set(re.findall(
    r"(?m)^\s*guest_run\s+\S+\s+(FLR-0350-[\w.-]+\.cmd)\s*$",
    runner_text,
))
missing_calls = static_calls - set(command_names)
if missing_calls:
    raise SystemExit("static guest commands missing from inventory: " + ",".join(sorted(missing_calls)))
commands = root / "work/commands"
for name in command_names:
    path = commands / name
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise SystemExit("serial-command-source-unreadable: " + name) from exc
    if len(data.splitlines()) != 1 or len(data.rstrip(b"\n")) > 4096:
        raise SystemExit("serial-command shape/size failed: " + name)
    subprocess.run(["sh", "-n", str(path)], check=True)

script_inventory = re.search(r"(?ms)^runtime_guest_scripts=\(\n(.*?)^\)", runner_text)
if not script_inventory:
    raise SystemExit("guest helper-script inventory missing")
script_names = re.findall(r"(?m)^\s*(FLR-0350-[\w.-]+\.sh)\s*$", script_inventory.group(1))
if not script_names or len(script_names) != len(set(script_names)):
    raise SystemExit("guest helper-script inventory is empty or duplicated")
for name in script_names:
    path = commands / name
    if not path.is_file():
        raise SystemExit("guest helper-script missing: " + name)
    subprocess.run(["sh", "-n", str(path)], check=True)

gdb_path = commands / "FLR-0350-sync-producer.gdb"
gdb_text = gdb_path.read_text()
blocks = re.findall(r"(?ms)^python\n(.*?)^end\s*$", gdb_text)
if not blocks:
    raise SystemExit("GDB Python blocks missing")
for block in blocks:
    ast.parse(block)
if "catch exec" not in gdb_text or "catch fork" not in gdb_text or \
   "catch vfork" not in gdb_text or "catch load libvulkan_lvp.so" not in gdb_text:
    raise SystemExit("GDB catchpoint policy missing")

base = (commands / "FLR-0344-launch-production.cmd").read_text()
candidate = (commands / "FLR-0350-launch-paused-production.cmd").read_text()
base_env = dict(re.findall(r"export ([A-Z0-9_]+)=([^;]+);", base))
match = re.search(r"env\s+(.+?)\s+/bin/sh -c", candidate)
if not match:
    raise SystemExit("FLR-0350 environment block missing")
candidate_env = dict(token.split("=", 1) for token in shlex.split(match.group(1)) if "=" in token)
if candidate_env != base_env:
    raise SystemExit("diagnostic environment differs from FLR-0344")

def flutter_args(text, run_id):
    match = re.search(r"/usr/bin/flutter-auto\s+(.*?)>/run/user/1001/" + run_id + r"-production\.log", text)
    if not match:
        raise SystemExit("Flutter CLI arguments missing for " + run_id)
    return shlex.split(match.group(1).strip())

if flutter_args(base, "flr0344") != flutter_args(candidate, "flr0350"):
    raise SystemExit("Flutter CLI arguments differ from FLR-0344")
if re.search(r"\bexit\s+", (commands / "FLR-0350-wait-matched-wait.cmd").read_text()):
    raise SystemExit("wait poll must return through serial prompt, not exit shell")

packed = base64.b64encode(gzip.compress(gdb_path.read_bytes(), mtime=0)).decode()
chunks = [packed[i:i + 2000] for i in range(0, len(packed), 2000)]
if any(len(chunk) > 2000 or (index < len(chunks) - 1 and len(chunk) % 4)
       for index, chunk in enumerate(chunks)):
    raise SystemExit("GDB script transfer chunk boundary invalid")
if any(len("printf %s '" + chunk + "' | base64 -d >> /run/user/1001/flr0350-sync-producer.gdb.gz") > 4096
       for chunk in chunks):
    raise SystemExit("GDB script transfer command exceeds serial limit")
init_command = subprocess.run(
    [sys.executable, str(root / "scripts/flr0350_launch_gate.py"),
     "--render-identity-init", "flr0362-0001"],
    check=True, capture_output=True, text=True,
).stdout.rstrip("\n")
if "\n" in init_command or len(init_command.encode()) > 4096:
    raise SystemExit("run-identity initialization command exceeds serial limit")
preflight = runner_runtime.index("guest_run preflight FLR-0350-preflight.cmd")
helper_preflight = runner_runtime.index("guest_run helper-preflight FLR-0350-preflight-helper-collision.cmd")
identity_init = runner_runtime.index("guest_run init-run-identity init-run-identity.cmd")
launch = runner_runtime.index("guest_run launch FLR-0350-launch-paused-production.cmd")
if not preflight < helper_preflight < identity_init < launch:
    raise SystemExit("root identity init must follow guest preflight and precede launch")
print("FLR0350_STATIC_CHECK=PASS commands=%d gdb_python_blocks=%d transfer_chunks=%d" %
      (len(command_names), len(blocks), len(chunks)))
print("FLR0350_PROFILE_MATCH=PASS environment=exact cli=exact target=qemux86-64")
print("FLR0350_RUN_ID_HANDOFF=PASS preflight-before-evidence start-same-id")
print("FLR0350_RUNTIME_HELPER_CONTRACT=PASS source=repo staged=run-parent callers=runner+starter")
print("FLR0350_RUNTIME_HELPER_HEAD=PASS committed-blob=source=staged executable=true")
print("FLR0350_PIXEL_CAPTURE_IDENTITY=PASS historical-helper-sha-pinned")
PY
    python3 "$repo_root/tests/test_flr0350_launch_gate.py"
    python3 "$repo_root/scripts/flr0350_launch_gate.py" --check-run-id flr0356-0001
    if python3 "$repo_root/scripts/flr0350_launch_gate.py" --check-run-id flr0350-0001; then
        echo FLR0350_RUN_ID_REUSE_GATE=FAIL
        return 1
    fi
    echo FLR0350_RUN_ID_REUSE_GATE=PASS
}

if [ "$#" -eq 1 ] && [ "$1" = --check ]; then
    bash scripts/assert-canonical-repository.sh
    static_check
    echo 'FLR0350_TARGET_PREFLIGHT=NOT_RUN qemu=NOT_STARTED'
    exit 0
fi
[ "$#" -eq 1 ] || {
    echo 'Usage: FLR-0350-run-sync-producer.sh --check | flrNNNN-NNNN' >&2
    exit 2
}
run_id=$1
python3 "$repo_root/scripts/flr0350_launch_gate.py" --check-run-id "$run_id" || exit 2

bash scripts/assert-canonical-repository.sh
static_check
for file in "${runtime_command_files[@]}"; do
    [ -r "$repo_root/work/commands/$file" ] || {
        echo "FLR0350_COMMAND_STAGE=FAIL reason=source-not-readable file=$file" >&2
        exit 1
    }
done
parent=$evidence_root/$run_id
run_dir=$parent/qemu
qmp=$run_dir/qmp-0350.sock
cleanup_failed=0
guest_ready=0
capture_attempted=0
runtime_state_saved=0
window_result=NOT_REACHED
match_lifetime=UNKNOWN
run_result=UNKNOWN

{ [ ! -e "$parent" ] && [ ! -L "$parent" ]; } || {
    echo 'FLR0350_RUN_FAIL reason=evidence-run-id-already-used' >&2
    exit 1
}
if preflight_output=$(FLR0350_RUN_ID="$run_id" bash "$start_script" preflight 2>&1); then
    :
else
    preflight_rc=$?
    printf '%s\n' "$preflight_output" >&2
    exit "$preflight_rc"
fi
[ -x "$harness_source" ] || {
    echo 'FLR0350_RUNTIME_HELPER=FAIL reason=source-not-executable' >&2
    exit 1
}
source_commit=$(git -C "$repo_root" rev-parse HEAD) || {
    echo 'FLR0350_RUNTIME_HELPER=FAIL reason=commit-unavailable' >&2
    exit 1
}
committed_harness_sha=$(git -C "$repo_root" show "HEAD:scripts/qemu-runtime-harness.sh" |
    sha256sum | awk '{print $1}')
source_harness_sha=$(sha256sum "$harness_source" | awk '{print $1}')
[ "$source_harness_sha" = "$committed_harness_sha" ] || {
    echo 'FLR0350_RUNTIME_HELPER=FAIL reason=source-not-at-HEAD' >&2
    exit 1
}
mkdir -- "$parent"
exec > >(tee -a "$parent/FLR-0350-runner.log") 2>&1
printf '%s\n' "$preflight_output" | tee "$parent/qemu-preflight.log"
for file in "${runtime_command_files[@]}"; do
    cp -- "$repo_root/work/commands/$file" "$parent/$file"
done
for file in "${runtime_guest_scripts[@]}"; do
    source_file=$repo_root/work/commands/$file
    committed_sha=$(git -C "$repo_root" show "HEAD:work/commands/$file" |
        sha256sum | awk '{print $1}')
    source_sha=$(sha256sum "$source_file" | awk '{print $1}')
    [ "$source_sha" = "$committed_sha" ] || {
        echo "FLR0350_GUEST_SCRIPT=FAIL reason=source-not-at-HEAD file=$file"
        exit 1
    }
    cp -- "$source_file" "$parent/$file"
    cmp -s "$source_file" "$parent/$file" || {
        echo "FLR0350_GUEST_SCRIPT=FAIL reason=staged-source-mismatch file=$file"
        exit 1
    }
    staged_sha=$(sha256sum "$parent/$file" | awk '{print $1}')
    [ "$staged_sha" = "$committed_sha" ] || {
        echo "FLR0350_GUEST_SCRIPT=FAIL reason=staged-not-committed-bytes file=$file"
        exit 1
    }
    echo "FLR0350_GUEST_SCRIPT=PASS file=$file sha256=$staged_sha"
done
cp -- "$harness_source" "$parent/qemu-runtime-harness.sh"
harness=$parent/qemu-runtime-harness.sh
if ! cmp -s "$harness_source" "$harness"; then
    echo 'FLR0350_RUNTIME_HELPER=FAIL reason=staged-source-mismatch' >&2
    exit 1
fi
harness_sha=$(sha256sum "$harness" | awk '{print $1}')
[ -x "$harness" ] && [ "$harness_sha" = "$committed_harness_sha" ] || {
    echo 'FLR0350_RUNTIME_HELPER=FAIL reason=staged-not-committed-bytes' >&2
    exit 1
}
echo "FLR0350_RUNTIME_HELPER=PASS source_commit=$source_commit committed_sha256=$committed_harness_sha source_sha256=$source_harness_sha staged_sha256=$harness_sha"
echo "FLR0350_COMMAND_STAGE=PASS location=evidence-parent count=${#runtime_command_files[@]}"

guest_run() {
    local label=$1
    local file=$2
    local command_file=$run_dir/$file
    [ -f "$command_file" ] || command_file=$parent/$file
    "$harness" serial-exec --serial-port 10930 --user root \
        --prompt 'root@qemux86-64:~# ' --command-file "$command_file" \
        --output "$run_dir/$label.serial.log" >"$run_dir/$label.harness.log" 2>&1
}

capture_evidence() {
    [ "$capture_attempted" -eq 0 ] || return 0
    capture_attempted=1
    [ -S "$qmp" ] || { echo FLR0350_QMP_CAPTURE=UNAVAILABLE; return 1; }
    "$capture" capture --socket "$qmp" --output "$run_dir/post-run.ppm" >"$run_dir/post-run-capture.log" 2>&1
    "$capture" video --socket "$qmp" --frames-dir "$run_dir/post-run-frames" \
        --frames 8 --interval 1 >"$run_dir/post-run-video.log" 2>&1
    "$capture" analyze --input "$run_dir/post-run.ppm" --region 0,0,1280,800 \
        >"$run_dir/post-run-full-analysis.log" 2>&1
    if [ -s "$run_dir/pre-launch.ppm" ]; then
        "$capture" analyze --input "$run_dir/post-run.ppm" --region 0,200,1280,600 \
            --reference "$run_dir/pre-launch.ppm" >"$run_dir/post-run-3d-roi-analysis.log" 2>&1
    fi
    cat "$run_dir/post-run-capture.log" "$run_dir/post-run-video.log" \
        "$run_dir/post-run-full-analysis.log"
    [ ! -f "$run_dir/post-run-3d-roi-analysis.log" ] || cat "$run_dir/post-run-3d-roi-analysis.log"
    sha256sum "$run_dir/post-run.ppm"
    shopt -s nullglob
    local frames=("$run_dir"/post-run-frames/*.ppm)
    ((${#frames[@]} == 0)) || sha256sum "${frames[@]}"
    echo FLR0350_QMP_CAPTURE=PASS files=still+8-frames
}

cleanup() {
    local rc=$?
    local gdb_stopped=1
    trap - EXIT
    set +e
    if [ -S "$qmp" ]; then
        if [ "$guest_ready" -eq 1 ]; then
            if ! guest_run cleanup-gdb FLR-0350-interrupt-gdb.cmd; then
                cleanup_failed=1
                gdb_stopped=0
            fi
            if grep -Eq 'FLR0350_UNRECORDED_TARGET_ABORT=FAIL|FLR0350_GDB_INTERRUPT=FAIL|FLR0350_GDB_REMAINDER=running' \
                "$run_dir/cleanup-gdb.serial.log" 2>/dev/null; then
                cleanup_failed=1
                gdb_stopped=0
            fi
            if [ "$gdb_stopped" -eq 1 ]; then
                if [ "$runtime_state_saved" -eq 0 ]; then
                    guest_run cleanup-runtime-state FLR-0350-capture-runtime-state.cmd || cleanup_failed=1
                fi
                if [ "$capture_attempted" -eq 0 ]; then
                    capture_evidence || cleanup_failed=1
                fi
                guest_run cleanup-app FLR-0350-stop-recorded-app.cmd || cleanup_failed=1
                grep -Fq 'flutter_processes=0' "$run_dir/cleanup-app.serial.log" 2>/dev/null || cleanup_failed=1
                grep -Fq 'FLR0350_FIFO_CLEANUP=PASS' "$run_dir/cleanup-app.serial.log" 2>/dev/null || cleanup_failed=1
            else
                echo FLR0350_POST_RUN_CAPTURE=SKIPPED reason=gdb-stop-not-confirmed
            fi
        elif [ "$capture_attempted" -eq 0 ]; then
            capture_evidence || cleanup_failed=1
        fi
        "$harness" qmp-quit --qmp "$qmp" >"$run_dir/qmp-quit.log" 2>&1 || cleanup_failed=1
        cat "$run_dir/qmp-quit.log" 2>/dev/null || true
    fi
    residual=$(ps -axo pid=,ppid=,stat=,args= | awk '
        $3 !~ /^Z/ {
            executable=$4; sub(/^.*\//, "", executable)
            script=$5; sub(/^.*\//, "", script)
            if (executable ~ /^qemu-system-/ || executable == "runqemu" ||
                executable == "flutter-auto" ||
                (executable ~ /^python[0-9.]*$/ && script == "runqemu"))
                print $1, executable
        }
    ')
    if [ -n "$residual" ] || [ -e "$qmp" ]; then
        qmp_left=0
        [ ! -e "$qmp" ] || qmp_left=1
        echo "FLR0350_CLEANUP=FAIL residual_targets=$residual residual_qmp=$qmp_left"
        cleanup_failed=1
    elif [ "$cleanup_failed" -eq 0 ]; then
        echo 'FLR0350_CLEANUP=PASS residual_targets=0 residual_qmp=0'
    else
        echo FLR0350_CLEANUP=FAIL reason=guest-teardown-or-capture-incomplete residual_targets=0 residual_qmp=0
    fi
    if [ "$rc" -eq 0 ] && [ "$cleanup_failed" -ne 0 ]; then rc=1; fi
    exit "$rc"
}
trap cleanup EXIT

echo "FLR0350_RUN_BEGIN id=$run_id diagnostic_profile=FLR0344-0348 memory_mib=6144"
FLR0350_RUN_ID="$run_id" bash "$start_script" start >"$parent/qemu-start.log" 2>&1 || {
    tail -n 60 "$parent/qemu-start.log"
    exit 1
}
for file in "${runtime_command_files[@]}"; do
    cp -- "$parent/$file" "$run_dir/$file"
done
cp -- "$repo_root/work/commands/FLR-0350-sync-producer.gdb" "$run_dir/FLR-0350-sync-producer.gdb"
"$harness" guest-ready --ssh-port 10931 --timeout-seconds 180 >"$run_dir/guest-ready.log" 2>&1
cat "$run_dir/guest-ready.log"
guest_ready=1

"$capture" capture --socket "$qmp" --output "$run_dir/pre-launch.ppm" \
    >"$run_dir/pre-launch-capture.log" 2>&1
cat "$run_dir/pre-launch-capture.log"
guest_run preflight FLR-0350-preflight.cmd
grep -F 'FLR0350_PREFLIGHT=PASS' "$run_dir/preflight.serial.log"
guest_run helper-preflight FLR-0350-preflight-helper-collision.cmd
grep -F 'FLR0350_HELPER_PREFLIGHT=PASS' "$run_dir/helper-preflight.serial.log"

python3 scripts/flr0350_launch_gate.py --render-identity-init "$run_id" \
    >"$run_dir/init-run-identity.cmd"
[ "$(wc -c <"$run_dir/init-run-identity.cmd" | tr -d ' ')" -le 4097 ] || {
    echo FLR0350_RUN_ID_INIT=FAIL reason=command-too-large
    exit 1
}
guest_run init-run-identity init-run-identity.cmd
grep -F 'FLR0350_RUN_ID_INIT=PASS' "$run_dir/init-run-identity.serial.log"

gdb_script=$run_dir/FLR-0350-sync-producer.gdb
gdb_sha=$(sha256sum "$gdb_script" | awk '{print $1}')
packed=$(gzip -n -c "$gdb_script" | base64 | tr -d '\n')
chunk_size=2000
offset=0
chunk_index=1
while [ "$offset" -lt "${#packed}" ]; do
    chunk=${packed:$offset:$chunk_size}
    if [ "$chunk_index" -eq 1 ]; then
        install="test ! -e /run/user/1001/flr0350-sync-producer.gdb.gz && printf %s '$chunk' | base64 -d > /run/user/1001/flr0350-sync-producer.gdb.gz && echo FLR0350_GDB_CHUNK_$chunk_index=PASS"
    else
        install="test -f /run/user/1001/flr0350-sync-producer.gdb.gz && printf %s '$chunk' | base64 -d >> /run/user/1001/flr0350-sync-producer.gdb.gz && echo FLR0350_GDB_CHUNK_$chunk_index=PASS"
    fi
    [ "$(printf '%s' "$install" | wc -c | tr -d ' ')" -le 4096 ] || { echo FLR0350_GDB_TRANSFER=FAIL command-too-large; exit 1; }
    install_file=$run_dir/install-gdb-chunk-$chunk_index.cmd
    printf '%s\n' "$install" >"$install_file"
    guest_run "install-gdb-chunk-$chunk_index" "install-gdb-chunk-$chunk_index.cmd"
    grep -F "FLR0350_GDB_CHUNK_$chunk_index=PASS" "$run_dir/install-gdb-chunk-$chunk_index.serial.log"
    offset=$((offset + chunk_size))
    chunk_index=$((chunk_index + 1))
done
finalize="test ! -e /run/user/1001/flr0350-sync-producer.gdb && test ! -L /run/user/1001/flr0350-sync-producer.gdb && test ! -e /run/user/1001/flr0350-sync-producer.gdb.tmp && test ! -L /run/user/1001/flr0350-sync-producer.gdb.tmp && gzip -dc /run/user/1001/flr0350-sync-producer.gdb.gz > /run/user/1001/flr0350-sync-producer.gdb.tmp && chmod 600 /run/user/1001/flr0350-sync-producer.gdb.tmp && test \"\$(sha256sum /run/user/1001/flr0350-sync-producer.gdb.tmp | cut -d' ' -f1)\" = '$gdb_sha' && mv /run/user/1001/flr0350-sync-producer.gdb.tmp /run/user/1001/flr0350-sync-producer.gdb && unlink /run/user/1001/flr0350-sync-producer.gdb.gz && echo FLR0350_GDB_SCRIPT_INSTALL=PASS"
[ "$(printf '%s' "$finalize" | wc -c | tr -d ' ')" -le 4096 ] || { echo FLR0350_GDB_TRANSFER=FAIL finalize-too-large; exit 1; }
printf '%s\n' "$finalize" >"$run_dir/install-gdb-finalize.cmd"
guest_run install-gdb-finalize install-gdb-finalize.cmd
grep -F 'FLR0350_GDB_SCRIPT_INSTALL=PASS' "$run_dir/install-gdb-finalize.serial.log"

for guest_script in "${runtime_guest_scripts[@]}"; do
    script_sha=$(sha256sum "$parent/$guest_script" | awk '{print $1}')
    packed=$(gzip -n -c "$parent/$guest_script" | base64 | tr -d '\n')
    offset=0
    chunk_index=1
    guest_path=/run/user/1001/$guest_script
    while [ "$offset" -lt "${#packed}" ]; do
        chunk=${packed:$offset:$chunk_size}
        compressed_path=$guest_path.gz
        if [ "$chunk_index" -eq 1 ]; then
            install="test ! -e '$compressed_path' && test ! -L '$compressed_path' && printf %s '$chunk' | base64 -d > '$compressed_path' && echo FLR0350_GUEST_SCRIPT_CHUNK_$chunk_index=PASS"
        else
            install="test -f '$compressed_path' && printf %s '$chunk' | base64 -d >> '$compressed_path' && echo FLR0350_GUEST_SCRIPT_CHUNK_$chunk_index=PASS"
        fi
        [ "$(printf '%s' "$install" | wc -c | tr -d ' ')" -le 4096 ] || {
            echo "FLR0350_GUEST_SCRIPT=FAIL reason=chunk-too-large file=$guest_script"
            exit 1
        }
        install_file=$run_dir/install-guest-script-$chunk_index.cmd
        printf '%s\n' "$install" >"$install_file"
        guest_run "install-guest-script-$guest_script-$chunk_index" "$install-guest-script-$chunk_index.cmd"
        grep -F 'FLR0350_GUEST_SCRIPT_CHUNK_' "$run_dir/install-guest-script-$guest_script-$chunk_index.serial.log"
        offset=$((offset + chunk_size))
        chunk_index=$((chunk_index + 1))
    done
    finalize="test ! -e '$guest_path' && test ! -L '$guest_path' && test ! -e '$guest_path.tmp' && test ! -L '$guest_path.tmp' && gzip -dc '$compressed_path' > '$guest_path.tmp' && chmod 600 '$guest_path.tmp' && test \"\$(sha256sum '$guest_path.tmp' | cut -d' ' -f1)\" = '$script_sha' && mv '$guest_path.tmp' '$guest_path' && unlink '$compressed_path' && echo FLR0350_GUEST_SCRIPT_INSTALL=PASS"
    [ "$(printf '%s' "$finalize" | wc -c | tr -d ' ')" -le 4096 ] || {
        echo "FLR0350_GUEST_SCRIPT=FAIL reason=finalize-too-large file=$guest_script"
        exit 1
    }
    printf '%s\n' "$finalize" >"$run_dir/install-guest-script-finalize.cmd"
    guest_run "install-guest-script-finalize-$guest_script" install-guest-script-finalize.cmd
    grep -F 'FLR0350_GUEST_SCRIPT_INSTALL=PASS' "$run_dir/install-guest-script-finalize-$guest_script.serial.log"
done

guest_run launch FLR-0350-launch-paused-production.cmd
grep -F 'FLR0350_LAUNCH=PASS' "$run_dir/launch.serial.log"
grep -F 'FLR0350_LAUNCH_WRAPPER=READY' "$run_dir/launch.serial.log"
guest_run observe-gate FLR-0350-observe-fifo-read-gate.cmd
python3 scripts/flr0350_launch_gate.py --validate \
    "$run_id" "$run_dir/launch.serial.log" "$run_dir/observe-gate.serial.log"
guest_run attach-gdb FLR-0350-attach-pre-submit.cmd
grep -F 'FLR0350_GDB_ATTACH=PASS' "$run_dir/attach-gdb.serial.log"
guest_run release-go FLR-0350-release-go.cmd
grep -F 'FLR0350_GO_RECORD=PASS' "$run_dir/release-go.serial.log"
grep -F 'FLR0350_EXEC=PASS' "$run_dir/release-go.serial.log"
guest_run symbol-gate FLR-0350-wait-symbol-gate.cmd
if grep -Fq 'FLR0350_SYMBOL_GATE_POLL=PASS' "$run_dir/symbol-gate.serial.log"; then
    run_result=WAIT_NOT_REACHED
else
    run_result=SYMBOL_GATE_UNKNOWN
fi

if [ "$run_result" = WAIT_NOT_REACHED ]; then
    poll=0
    while [ "$poll" -lt 14 ]; do
        poll=$((poll + 1))
        guest_run "wait-poll-$poll" FLR-0350-wait-matched-wait.cmd
        poll_result=$(grep -E '^FLR0350_WAIT_POLL=' "$run_dir/wait-poll-$poll.serial.log" | tail -n 1 | cut -d= -f2 | cut -d' ' -f1)
        echo "FLR0350_WAIT_POLL_HOST=$poll result=${poll_result:-missing}"
        case "$poll_result" in
            PASS)
                match_lifetime=$(grep -E '^FLR0350_MATCHED_WAIT=1 ' "$run_dir/wait-poll-$poll.serial.log" | tail -n 1 | sed -n 's/.* lifetime=\([^ ]*\).*/\1/p')
                [ -n "$match_lifetime" ] || match_lifetime=UNKNOWN
                guest_run watch-window FLR-0350-watch-window.cmd
                window_result=$(grep -E '^FLR0350_WATCH_WINDOW=' "$run_dir/watch-window.serial.log" | tail -n 1 | cut -d= -f2 | cut -d' ' -f1)
                if [ "$window_result" = HIT ] || [ "$window_result" = NO_HIT ]; then
                    if [ "$match_lifetime" = PASS ]; then
                        run_result="MATCHED_WAIT_${window_result}_LIFETIME_PASS"
                    else
                        run_result="MATCHED_WAIT_${window_result}_LIFETIME_UNKNOWN"
                    fi
                else
                    run_result=WATCH_WINDOW_UNKNOWN
                fi
                break
                ;;
            OPEN) ;;
            WATCHPOINTS_FAILED) run_result=WAIT_WATCHPOINTS_FAILED; break ;;
            PROCESS_IDENTITY_LOST) run_result=PROCESS_IDENTITY_LOST; break ;;
            WINDOW_EXPIRED) run_result=WAIT_WINDOW_EXPIRED; break ;;
            *) run_result=${poll_result:-WAIT_POLL_UNKNOWN}; break ;;
        esac
    done
fi

guest_run stop-gdb FLR-0350-interrupt-gdb.cmd
grep -E 'FLR0350_GDB_(INTERRUPT|REMAINDER|TERM_FALLBACK)|FLR0350_SYNC_WRITE|FLR0350_MATCHED_WAIT|FLR0350_COVERAGE_GAP|Hardware watchpoint|Old value|New value|Program received signal|error:|Error|Cannot|ptrace|failed|Failed|^#([0-9]+) ' \
    "$run_dir/stop-gdb.serial.log" | tail -n 120 || true
if grep -Eq 'FLR0350_UNRECORDED_TARGET_ABORT=FAIL|FLR0350_GDB_INTERRUPT=FAIL|FLR0350_GDB_REMAINDER=running' "$run_dir/stop-gdb.serial.log"; then
    echo FLR0350_GDB_TEARDOWN=FAIL
    exit 1
fi
guest_run runtime-state FLR-0350-capture-runtime-state.cmd
runtime_state_saved=1
grep -E 'guest_uptime=|FLR0350_|FLUORITE_VK_(SUBMIT_RETURN|PRESENT_CALL_BEGIN|QUEUE_PRESENT_ENTER|QUEUE_PRESENT_RETURN)|FLUORITE_NATIVE_WAYLAND_COMMIT|flutter_processes=|RIP:|Call Trace:|BUG:|Killed process' \
    "$run_dir/runtime-state.serial.log" | tail -n 120 || true
capture_evidence
guest_run stop-app FLR-0350-stop-recorded-app.cmd
grep -E 'FLR0350_APP_STOP=|FLR0350_FIFO_CLEANUP=|flutter_processes=' "$run_dir/stop-app.serial.log"
grep -F 'flutter_processes=0' "$run_dir/stop-app.serial.log"
grep -F 'FLR0350_FIFO_CLEANUP=PASS' "$run_dir/stop-app.serial.log"
"$harness" qmp-quit --qmp "$qmp" | tee "$run_dir/qmp-quit.log"
echo "FLR0350_RUN_DONE result=$run_result watch_window=$window_result lifetime=$match_lifetime"
