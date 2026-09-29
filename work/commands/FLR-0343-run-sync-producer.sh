#!/usr/bin/env bash
set -euo pipefail

[ "$#" -eq 1 ] || { echo 'Usage: FLR-0343-run-sync-producer.sh flr0343-NNNN' >&2; exit 2; }
run_id=$1
case "$run_id" in flr0343-[0-9][0-9][0-9][0-9]) ;; *) echo 'FLR0343_RUN_FAIL reason=invalid-run-id' >&2; exit 2 ;; esac
parent=/mnt/yocto/evidence/$run_id
run_dir=$parent/qemu
prior=/mnt/yocto/evidence/flr0335-0001/qemu
qmp=$run_dir/qmp-0343.sock
harness=$prior/qemu-runtime-harness.sh
capture=$prior/qemu-pixel-capture.py
cleanup_failed=0
[ ! -e "$parent/FLR-0343-runner.log" ] && [ ! -e "$parent/qemu-start.log" ] && [ ! -e "$run_dir" ] || {
    echo "FLR0343_RUN_FAIL reason=evidence-parent-already-used run_id=$run_id" >&2; exit 1;
}
mkdir -p -- "$parent"
exec > >(tee -a "$parent/FLR-0343-runner.log") 2>&1

guest_run() {
    local label=$1
    local file=$2
    local command_file=$run_dir/$file
    [ -f "$command_file" ] || command_file=$parent/$file
    "$harness" serial-exec --serial-port 10930 --user root \
        --prompt 'root@qemux86-64:~# ' --command-file "$command_file" \
        --output "$run_dir/$label.serial.log" >"$run_dir/$label.harness.log" 2>&1
}

cleanup() {
    local rc=$?
    trap - EXIT
    set +e
    if [ -S "$qmp" ]; then
        if [ -f "$parent/FLR-0343-interrupt-watch.cmd" ]; then
            guest_run cleanup-watch FLR-0343-interrupt-watch.cmd || cleanup_failed=1
        fi
        if [ -f "$parent/FLR-0343-stop-recorded-app.cmd" ]; then
            guest_run cleanup-app FLR-0343-stop-recorded-app.cmd || cleanup_failed=1
        fi
        "$harness" qmp-quit --qmp "$qmp" || cleanup_failed=1
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
        echo "cleanup=FAIL residual_targets=$residual residual_qmp=$qmp_left"
        cleanup_failed=1
    elif [ "$cleanup_failed" -eq 0 ]; then
        echo 'runner_trap=PASS residual_targets=0 residual_qmp=0'
    fi
    if [ "$rc" -eq 0 ] && [ "$cleanup_failed" -ne 0 ]; then rc=1; fi
    exit "$rc"
}
trap cleanup EXIT

echo FLR0343_RUN_BEGIN
FLR0343_RUN_ID=$run_id bash "$parent/FLR-0343-qemu-start.sh" >"$parent/qemu-start.log" 2>&1 || {
    tail -n 60 "$parent/qemu-start.log"; exit 1;
}
for file in FLR-0343-preflight.cmd FLR-0343-launch-production.cmd FLR-0343-poll-present.cmd \
    FLR-0343-start-watch.cmd FLR-0343-poll-watch.cmd FLR-0343-interrupt-watch.cmd \
    FLR-0343-capture-runtime-state.cmd FLR-0343-stop-recorded-app.cmd FLR-0343-sync-watch.gdb; do
    cp -- "$parent/$file" "$run_dir/$file"
done
"$harness" guest-ready --ssh-port 10931 --timeout-seconds 180 >"$run_dir/guest-ready.log" 2>&1
cat "$run_dir/guest-ready.log"
guest_run preflight FLR-0343-preflight.cmd
grep -F FLR0343_PREFLIGHT=PASS "$run_dir/preflight.serial.log"
"$capture" capture --socket "$qmp" --output "$run_dir/pre-launch.ppm" >"$run_dir/pre-launch-capture.log" 2>&1
cat "$run_dir/pre-launch-capture.log"
guest_run launch FLR-0343-launch-production.cmd
grep -F FLR0343_LAUNCH=PASS "$run_dir/launch.serial.log"

present_state=WINDOW_OPEN
for attempt in 1 2 3 4 5; do
    guest_run "present-poll-$attempt" FLR-0343-poll-present.cmd
    grep -E 'FLR0343_PRESENT_STATE=|guest_uptime=' "$run_dir/present-poll-$attempt.serial.log" | tail -n 8 || true
    if grep -Fq FLR0343_PRESENT_STATE=STALLED "$run_dir/present-poll-$attempt.serial.log"; then present_state=STALLED; break; fi
    if grep -Fq FLR0343_PRESENT_STATE=RETURNED "$run_dir/present-poll-$attempt.serial.log"; then present_state=RETURNED; break; fi
    if grep -Fq FLR0343_PRESENT_STATE=APP_EXITED "$run_dir/present-poll-$attempt.serial.log"; then present_state=APP_EXITED; break; fi
    if grep -Fq FLR0343_PRESENT_STATE=APP_PID_MISSING "$run_dir/present-poll-$attempt.serial.log"; then present_state=APP_PID_MISSING; break; fi
done
echo "FLR0343_PRESENT_RESULT=$present_state"

if [ "$present_state" = STALLED ]; then
    gdb_sha=$(sha256sum "$run_dir/FLR-0343-sync-watch.gdb" | awk '{print $1}')
    compressed=$(gzip -n -c "$run_dir/FLR-0343-sync-watch.gdb" | base64 | tr -d '\n')
    install="printf %s '$compressed' | base64 -d | gzip -dc > /run/user/1001/flr0343-sync-watch.gdb && chmod 600 /run/user/1001/flr0343-sync-watch.gdb && test \"\$(sha256sum /run/user/1001/flr0343-sync-watch.gdb | cut -d' ' -f1)\" = '$gdb_sha' && echo FLR0343_GDB_SCRIPT_INSTALL=PASS"
    install_len=$(printf '%s' "$install" | wc -c | tr -d ' ')
    [ "$install_len" -le 4096 ] || { echo "FLR0343_GDB_SCRIPT_INSTALL=FAIL bytes=$install_len"; exit 1; }
    printf '%s\n' "$install" >"$run_dir/install-gdb-script.cmd"
    guest_run install-gdb-script install-gdb-script.cmd
    grep -F FLR0343_GDB_SCRIPT_INSTALL=PASS "$run_dir/install-gdb-script.serial.log"
    guest_run watch FLR-0343-start-watch.cmd || echo FLR0343_GDB_WATCH_COMMAND=FAIL
    guest_run watch-result FLR-0343-poll-watch.cmd || echo FLR0343_GDB_RESULT_POLL=FAIL
    grep -E 'FLR0343_|Hardware watchpoint|Old value|New value|Program received signal|#([0-9]+) .*lvp_pipe_sync_wait|#([0-9]+) .*wsi_common_queue_present' \
        "$run_dir/watch-result.serial.log" | tail -n 100 || true
else
    echo "FLR0343_GDB_WATCH=SKIPPED present_state=$present_state"
fi

guest_run runtime-state FLR-0343-capture-runtime-state.cmd
grep -E 'guest_uptime=|tracked_pid=|app_process=|app_log_sha256=|gdb_log_sha256=|FLR0343_.*_count=|FLUORITE_VK_(SUBMIT_RETURN|PRESENT_CALL_BEGIN|QUEUE_PRESENT_ENTER|QUEUE_PRESENT_RETURN)|FLR0343_RUNTIME_STATE_DONE|Oops:|RIP:|CR2:|Call Trace:|BUG:|Killed process' \
    "$run_dir/runtime-state.serial.log" | tail -n 120 || true
"$capture" capture --socket "$qmp" --output "$run_dir/post-run.ppm" >"$run_dir/post-run-capture.log" 2>&1
"$capture" video --socket "$qmp" --frames-dir "$run_dir/post-run-frames" --frames 8 --interval 1 >"$run_dir/post-run-video.log" 2>&1
"$capture" analyze --input "$run_dir/post-run.ppm" --region 0,0,1280,800 >"$run_dir/post-run-full-analysis.log" 2>&1
"$capture" analyze --input "$run_dir/post-run.ppm" --region 0,200,1280,600 --reference "$run_dir/pre-launch.ppm" >"$run_dir/post-run-3d-roi-analysis.log" 2>&1
cat "$run_dir/post-run-capture.log" "$run_dir/post-run-video.log" "$run_dir/post-run-full-analysis.log" "$run_dir/post-run-3d-roi-analysis.log"
sha256sum "$run_dir/post-run.ppm" "$run_dir/post-run-frames"/*.ppm
guest_run stop-app FLR-0343-stop-recorded-app.cmd
grep -E 'app_stop=|flutter_processes=|FLR0343_APP_STOP_DONE' "$run_dir/stop-app.serial.log"
grep -F flutter_processes=0 "$run_dir/stop-app.serial.log"
"$harness" qmp-quit --qmp "$qmp" | tee "$run_dir/qmp-quit.log"
echo "FLR0343_RUN_DONE present=$present_state"
