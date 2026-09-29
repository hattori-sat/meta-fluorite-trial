#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo 'Usage: FLR-0338-run-hardware-breakpoint.sh flr0338-NNNN' >&2
    exit 2
fi
run_id=$1
case "$run_id" in
    flr0338-[0-9][0-9][0-9][0-9]) ;;
    *) echo 'FLR0338_RUN_FAIL reason=invalid-run-id' >&2; exit 2 ;;
esac
parent=/mnt/yocto/evidence/$run_id
run_dir=$parent/qemu
prior_run_dir=/mnt/yocto/evidence/flr0335-0001/qemu
qmp=$run_dir/qmp-0338.sock
harness=$prior_run_dir/qemu-runtime-harness.sh
capture=$prior_run_dir/qemu-pixel-capture.py
serial_port=10930
ssh_port=10931
cleanup_failed=0

mkdir -p -- "$parent"
exec > >(tee -a "$parent/FLR-0338-runner.log") 2>&1

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
        for command_file in FLR-0338-stop-debugger.cmd FLR-0338-stop-recorded-app.cmd; do
            if [ ! -f "$run_dir/$command_file" ] && [ -f "$parent/$command_file" ]; then
                cp -- "$parent/$command_file" "$run_dir/$command_file"
            fi
        done
        if [ -f "$run_dir/FLR-0338-stop-debugger.cmd" ]; then
            guest_run cleanup-debugger FLR-0338-stop-debugger.cmd || cleanup_failed=1
        fi
        if [ -f "$run_dir/FLR-0338-stop-recorded-app.cmd" ]; then
            guest_run cleanup-app FLR-0338-stop-recorded-app.cmd || cleanup_failed=1
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

echo 'FLR0338_RUN_BEGIN'
FLR0338_RUN_ID=$run_id bash "$parent/FLR-0338-qemu-start.sh" >"$parent/qemu-start.log" 2>&1 || {
    tail -n 60 "$parent/qemu-start.log"
    exit 1
}
for command_file in \
    FLR-0338-preflight.cmd FLR-0338-launch-production.cmd \
    FLR-0338-start-hwbp.cmd FLR-0338-poll-hwbp.cmd \
    FLR-0338-stop-debugger.cmd FLR-0338-stop-recorded-app.cmd \
    FLR-0338-capture-runtime-state.cmd; do
    cp -- "$parent/$command_file" "$run_dir/$command_file"
done

"$harness" guest-ready --ssh-port "$ssh_port" --timeout-seconds 180 \
    >"$run_dir/guest-ready.log" 2>&1
cat "$run_dir/guest-ready.log"
guest_run preflight FLR-0338-preflight.cmd
grep -F 'FLR0338_PREFLIGHT=PASS' "$run_dir/preflight.serial.log"

"$capture" capture --socket "$qmp" --output "$run_dir/pre-launch.ppm" \
    >"$run_dir/pre-launch-capture.log" 2>&1
cat "$run_dir/pre-launch-capture.log"
guest_run launch FLR-0338-launch-production.cmd
grep -F 'FLR0338_LAUNCH=PASS' "$run_dir/launch.serial.log"
sleep 3
guest_run start-hwbp FLR-0338-start-hwbp.cmd
grep -F 'FLR0338_GDB_START=PASS' "$run_dir/start-hwbp.serial.log"

breakpoint_status=WAITING
for attempt in 1 2 3 4; do
    if ! guest_run "poll-$attempt" FLR-0338-poll-hwbp.cmd; then
        echo "FLR0338_POLL_TRANSPORT=FAIL attempt=$attempt"
        breakpoint_status=POLL_ERROR
        break
    fi
    grep -E 'FLR0338_STATUS=|FLR0338_ARMED_PC=|FLR0338_STOP_PC=|Hardware assisted breakpoint|Cannot insert|hardware breakpoint|ptrace|Program received signal|Error' \
        "$run_dir/poll-$attempt.serial.log" | tail -n 32 || true
    if grep -Fq 'FLR0338_STATUS=HIT ' "$run_dir/poll-$attempt.serial.log"; then
        breakpoint_status=HIT
        break
    fi
    if grep -Fq 'FLR0338_STATUS=STOPPED_OTHER ' "$run_dir/poll-$attempt.serial.log"; then
        breakpoint_status=STOPPED_OTHER
        break
    fi
    if grep -Fq 'FLR0338_STATUS=EXITED_NO_HIT' "$run_dir/poll-$attempt.serial.log"; then
        breakpoint_status=EXITED_NO_HIT
        break
    fi
done
echo "FLR0338_BREAKPOINT_RESULT=$breakpoint_status"

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

guest_run runtime-state FLR-0338-capture-runtime-state.cmd || {
    echo 'FLR0338_RUNTIME_STATE=FAIL'
    exit 1
}
grep -E 'guest_uptime=|tracked_pid=|app_process=|gdb_log_sha256=|FLR0338_ARMED_PC=|FLR0338_STOP_PC=|Hardware assisted breakpoint|FLR0026_.*_count=|FLUORITE_.*_count=|FLR0338_RUNTIME_STATE_DONE|Oops:|RIP:|CR2:|Call Trace:|BUG:|Killed process' \
    "$run_dir/runtime-state.serial.log" | tail -n 100 || true

guest_run stop-debugger FLR-0338-stop-debugger.cmd
guest_run stop-app FLR-0338-stop-recorded-app.cmd
grep -E 'gdb_stop=|app_stop=|flutter_processes=|FLR0338_APP_STOP_DONE' \
    "$run_dir/stop-debugger.serial.log" "$run_dir/stop-app.serial.log"
grep -F 'flutter_processes=0' "$run_dir/stop-app.serial.log"
"$harness" qmp-quit --qmp "$qmp" | tee "$run_dir/qmp-quit.log"
echo "FLR0338_RUN_DONE breakpoint=$breakpoint_status"
