#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo 'Usage: FLR-0339-run-present-stack.sh flr0339-NNNN' >&2
    exit 2
fi
run_id=$1
case "$run_id" in
    flr0339-[0-9][0-9][0-9][0-9]) ;;
    *) echo 'FLR0339_RUN_FAIL reason=invalid-run-id' >&2; exit 2 ;;
esac
parent=/mnt/yocto/evidence/$run_id
run_dir=$parent/qemu
prior_run_dir=/mnt/yocto/evidence/flr0335-0001/qemu
qmp=$run_dir/qmp-0339.sock
harness=$prior_run_dir/qemu-runtime-harness.sh
capture=$prior_run_dir/qemu-pixel-capture.py
serial_port=10930
ssh_port=10931
cleanup_failed=0

if [ -e "$parent/FLR-0339-runner.log" ] || [ -e "$parent/qemu-start.log" ] || [ -e "$run_dir" ]; then
    echo "FLR0339_RUN_FAIL reason=evidence-parent-already-used run_id=$run_id" >&2
    exit 1
fi
mkdir -p -- "$parent"
exec > >(tee -a "$parent/FLR-0339-runner.log") 2>&1

guest_run() {
    local label=$1
    local command_file=$2
    "$harness" serial-exec --serial-port "$serial_port" --user root \
        --prompt 'root@qemux86-64:~# ' --command-file "$run_dir/$command_file" \
        --output "$run_dir/$label.serial.log" >"$run_dir/$label.harness.log" 2>&1
}

cleanup() {
    local rc=$?
    trap - EXIT
    set +e
    if [ -S "$qmp" ]; then
        if [ ! -f "$run_dir/FLR-0339-stop-recorded-app.cmd" ] &&
            [ -f "$parent/FLR-0339-stop-recorded-app.cmd" ]; then
            cp -- "$parent/FLR-0339-stop-recorded-app.cmd" "$run_dir/"
        fi
        if [ -f "$run_dir/FLR-0339-stop-recorded-app.cmd" ]; then
            guest_run cleanup-app FLR-0339-stop-recorded-app.cmd || cleanup_failed=1
        fi
        "$harness" qmp-quit --qmp "$qmp" || cleanup_failed=1
    fi
    local residual
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
        echo "cleanup=FAIL residual_targets=${residual:-none} residual_qmp=$([ -e "$qmp" ] && echo 1 || echo 0)"
        cleanup_failed=1
    elif [ "$cleanup_failed" -eq 0 ]; then
        echo 'runner_trap=PASS residual_targets=0 residual_qmp=0'
    fi
    if [ "$rc" -eq 0 ] && [ "$cleanup_failed" -ne 0 ]; then
        rc=1
    fi
    exit "$rc"
}
trap cleanup EXIT

echo 'FLR0339_RUN_BEGIN'
FLR0339_RUN_ID=$run_id bash "$parent/FLR-0339-qemu-start.sh" >"$parent/qemu-start.log" 2>&1 || {
    tail -n 60 "$parent/qemu-start.log"
    exit 1
}
for command_file in \
    FLR-0339-preflight.cmd FLR-0339-launch-production.cmd \
    FLR-0339-poll-present.cmd FLR-0339-capture-present-stack.cmd \
    FLR-0339-capture-runtime-state.cmd FLR-0339-stop-recorded-app.cmd; do
    cp -- "$parent/$command_file" "$run_dir/$command_file"
done

"$harness" guest-ready --ssh-port "$ssh_port" --timeout-seconds 180 \
    >"$run_dir/guest-ready.log" 2>&1
cat "$run_dir/guest-ready.log"
guest_run preflight FLR-0339-preflight.cmd
grep -F 'FLR0339_PREFLIGHT=PASS' "$run_dir/preflight.serial.log"

"$capture" capture --socket "$qmp" --output "$run_dir/pre-launch.ppm" \
    >"$run_dir/pre-launch-capture.log" 2>&1
cat "$run_dir/pre-launch-capture.log"
guest_run launch FLR-0339-launch-production.cmd
grep -F 'FLR0339_LAUNCH=PASS' "$run_dir/launch.serial.log"

present_state=WINDOW_OPEN
for attempt in 1 2 3 4 5; do
    guest_run "present-poll-$attempt" FLR-0339-poll-present.cmd
    grep -E 'FLR0339_PRESENT_STATE=|guest_uptime=' \
        "$run_dir/present-poll-$attempt.serial.log" | tail -n 8 || true
    if grep -Fq 'FLR0339_PRESENT_STATE=STALLED' "$run_dir/present-poll-$attempt.serial.log"; then
        present_state=STALLED
        break
    fi
    if grep -Fq 'FLR0339_PRESENT_STATE=RETURNED' "$run_dir/present-poll-$attempt.serial.log"; then
        present_state=RETURNED
        break
    fi
    if grep -Fq 'FLR0339_PRESENT_STATE=APP_EXITED' "$run_dir/present-poll-$attempt.serial.log"; then
        present_state=APP_EXITED
        break
    fi
done
echo "FLR0339_PRESENT_RESULT=$present_state"

if [ "$present_state" = STALLED ]; then
    guest_run present-stack FLR-0339-capture-present-stack.cmd || {
        echo 'FLR0339_GDB_CAPTURE=FAIL'
    }
    grep -E 'FLR0339_GDB_|gdb_exit=|gdb_log_sha256=|Thread [0-9]+|LWP|FEngine::loop|vkQueuePresent|Vulkan|futex|ioctl|detached|error:|Cannot' \
        "$run_dir/present-stack.serial.log" | tail -n 160 || true
else
    echo "FLR0339_GDB_CAPTURE=SKIPPED present_state=$present_state"
fi

"$capture" capture --socket "$qmp" --output "$run_dir/post-run.ppm" \
    >"$run_dir/post-run-capture.log" 2>&1
"$capture" video --socket "$qmp" --frames-dir "$run_dir/post-run-frames" \
    --frames 8 --interval 1 >"$run_dir/post-run-video.log" 2>&1
"$capture" analyze --input "$run_dir/post-run.ppm" --region 0,0,1280,800 \
    >"$run_dir/post-run-full-analysis.log" 2>&1
"$capture" analyze --input "$run_dir/post-run.ppm" --region 0,200,1280,600 \
    --reference "$run_dir/pre-launch.ppm" >"$run_dir/post-run-3d-roi-analysis.log" 2>&1
cat "$run_dir/post-run-capture.log" "$run_dir/post-run-video.log" \
    "$run_dir/post-run-full-analysis.log" "$run_dir/post-run-3d-roi-analysis.log"

guest_run runtime-state FLR-0339-capture-runtime-state.cmd
grep -E 'guest_uptime=|tracked_pid=|app_process=|gdb_log_sha256=|FLR0026_.*_count=|FLUORITE_.*_count=|FLR0339_RUNTIME_STATE_DONE|Oops:|RIP:|CR2:|Call Trace:|BUG:|Killed process' \
    "$run_dir/runtime-state.serial.log" | tail -n 120 || true
guest_run stop-app FLR-0339-stop-recorded-app.cmd
grep -E 'app_stop=|flutter_processes=|FLR0339_APP_STOP_DONE' "$run_dir/stop-app.serial.log"
grep -F 'flutter_processes=0' "$run_dir/stop-app.serial.log"
"$harness" qmp-quit --qmp "$qmp" | tee "$run_dir/qmp-quit.log"
echo "FLR0339_RUN_DONE present=$present_state"
