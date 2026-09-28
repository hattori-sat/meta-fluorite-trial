#!/usr/bin/env bash
set -euo pipefail

[ "$#" -eq 1 ] || { echo 'Usage: FLR-0344-run-sync-watch.sh flr0344-NNNN|flr0347-NNNN|flr0348-NNNN' >&2; exit 2; }
run_id=$1
case "$run_id" in flr0344-[0-9][0-9][0-9][0-9]|flr0347-[0-9][0-9][0-9][0-9]|flr0348-[0-9][0-9][0-9][0-9]) ;; *) echo 'FLR0344_RUN_FAIL reason=invalid-run-id' >&2; exit 2 ;; esac
parent=/mnt/yocto/evidence/$run_id
run_dir=$parent/qemu
prior=/mnt/yocto/evidence/flr0335-0001/qemu
qmp_name=qmp-0344.sock
case "$run_id" in
    flr0347-*) qmp_name=qmp-0347.sock ;;
    flr0348-*) qmp_name=qmp-0348.sock ;;
esac
qmp=$run_dir/$qmp_name
harness=$prior/qemu-runtime-harness.sh
capture=$prior/qemu-pixel-capture.py
cleanup_failed=0
[ ! -e "$parent/FLR-0344-runner.log" ] && [ ! -e "$parent/qemu-start.log" ] && [ ! -e "$run_dir" ] || {
    echo "FLR0344_RUN_FAIL reason=evidence-parent-already-used run_id=$run_id" >&2; exit 1;
}
mkdir -p -- "$parent"
exec > >(tee -a "$parent/FLR-0344-runner.log") 2>&1

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
        if [ -f "$parent/FLR-0344-interrupt-gdb.cmd" ]; then
            guest_run cleanup-watch FLR-0344-interrupt-gdb.cmd || cleanup_failed=1
        fi
        if [ -f "$parent/FLR-0344-stop-recorded-app.cmd" ]; then
            guest_run cleanup-app FLR-0344-stop-recorded-app.cmd || cleanup_failed=1
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

echo FLR0344_RUN_BEGIN
FLR0344_RUN_ID=$run_id bash "$parent/FLR-0344-qemu-start.sh" >"$parent/qemu-start.log" 2>&1 || {
    tail -n 60 "$parent/qemu-start.log"; exit 1;
}
for file in FLR-0344-preflight.cmd FLR-0344-launch-production.cmd FLR-0344-poll-present.cmd \
    FLR-0344-launch-gdb.cmd FLR-0344-wait-armed.cmd FLR-0344-watch-window.cmd \
    FLR-0344-poll-watch.cmd FLR-0344-interrupt-gdb.cmd \
    FLR-0344-capture-runtime-state.cmd FLR-0344-stop-recorded-app.cmd; do
    cp -- "$parent/$file" "$run_dir/$file"
done
gdb_script_file=FLR-0344-sync-watch.gdb
case "$run_id" in flr0348-*) gdb_script_file=FLR-0348-sync-watch.gdb ;; esac
cp -- "$parent/$gdb_script_file" "$run_dir/$gdb_script_file"
arm_wait_command=FLR-0344-wait-armed.cmd
arm_wait_pass_marker='FLR0344_ARM_WAIT=PASS armed=1'
case "$run_id" in
    flr0347-*|flr0348-*)
        cp -- "$parent/FLR-0346-arm-poll.sh" "$run_dir/FLR-0346-arm-poll.sh"
        cp -- "$parent/FLR-0346-wait-armed.cmd" "$run_dir/FLR-0346-wait-armed.cmd"
        arm_wait_command=FLR-0346-wait-armed.cmd
        arm_wait_pass_marker='FLR0346_ARM_WAIT=PASS armed=1'
        ;;
esac
"$harness" guest-ready --ssh-port 10931 --timeout-seconds 180 >"$run_dir/guest-ready.log" 2>&1
cat "$run_dir/guest-ready.log"
guest_run preflight FLR-0344-preflight.cmd
grep -F FLR0344_PREFLIGHT=PASS "$run_dir/preflight.serial.log"
"$capture" capture --socket "$qmp" --output "$run_dir/pre-launch.ppm" >"$run_dir/pre-launch-capture.log" 2>&1
cat "$run_dir/pre-launch-capture.log"
guest_run launch FLR-0344-launch-production.cmd
grep -F FLR0344_LAUNCH=PASS "$run_dir/launch.serial.log"

present_state=WINDOW_OPEN
for attempt in 1 2 3 4 5; do
    guest_run "present-poll-$attempt" FLR-0344-poll-present.cmd
    grep -E 'FLR0344_PRESENT_STATE=|guest_uptime=' "$run_dir/present-poll-$attempt.serial.log" | tail -n 8 || true
    if grep -Fq FLR0344_PRESENT_STATE=STALLED "$run_dir/present-poll-$attempt.serial.log"; then present_state=STALLED; break; fi
    if grep -Fq FLR0344_PRESENT_STATE=RETURNED "$run_dir/present-poll-$attempt.serial.log"; then present_state=RETURNED; break; fi
    if grep -Fq FLR0344_PRESENT_STATE=APP_EXITED "$run_dir/present-poll-$attempt.serial.log"; then present_state=APP_EXITED; break; fi
    if grep -Fq FLR0344_PRESENT_STATE=APP_PID_MISSING "$run_dir/present-poll-$attempt.serial.log"; then present_state=APP_PID_MISSING; break; fi
done
echo "FLR0344_PRESENT_RESULT=$present_state"

if [ "$present_state" = STALLED ]; then
    gdb_sha=$(sha256sum "$run_dir/$gdb_script_file" | awk '{print $1}')
    compressed=$(gzip -n -c "$run_dir/$gdb_script_file" | base64 | tr -d '\n')
    install="printf %s '$compressed' | base64 -d | gzip -dc > /run/user/1001/flr0344-sync-watch.gdb && chmod 600 /run/user/1001/flr0344-sync-watch.gdb && test \"\$(sha256sum /run/user/1001/flr0344-sync-watch.gdb | cut -d' ' -f1)\" = '$gdb_sha' && echo FLR0344_GDB_SCRIPT_INSTALL=PASS"
    install_len=$(printf '%s' "$install" | wc -c | tr -d ' ')
    [ "$install_len" -le 4096 ] || { echo "FLR0344_GDB_SCRIPT_INSTALL=FAIL bytes=$install_len"; exit 1; }
    printf '%s\n' "$install" >"$run_dir/install-gdb-script.cmd"
    guest_run install-gdb-script install-gdb-script.cmd
    grep -F FLR0344_GDB_SCRIPT_INSTALL=PASS "$run_dir/install-gdb-script.serial.log"
    if [ "$arm_wait_command" = FLR-0346-wait-armed.cmd ]; then
        helper_sha=$(sha256sum "$run_dir/FLR-0346-arm-poll.sh" | awk '{print $1}')
        helper_compressed=$(gzip -n -c "$run_dir/FLR-0346-arm-poll.sh" | base64 | tr -d '\n')
        install_helper="printf %s '$helper_compressed' | base64 -d | gzip -dc > /run/user/1001/flr0346-arm-poll.sh && chmod 700 /run/user/1001/flr0346-arm-poll.sh && test \"\$(sha256sum /run/user/1001/flr0346-arm-poll.sh | cut -d' ' -f1)\" = '$helper_sha' && echo FLR0346_ARM_HELPER_INSTALL=PASS"
        helper_install_len=$(printf '%s' "$install_helper" | wc -c | tr -d ' ')
        [ "$helper_install_len" -le 4096 ] || { echo "FLR0346_ARM_HELPER_INSTALL=FAIL bytes=$helper_install_len"; exit 1; }
        printf '%s\n' "$install_helper" >"$run_dir/install-arm-helper.cmd"
        guest_run install-arm-helper install-arm-helper.cmd
        grep -F FLR0346_ARM_HELPER_INSTALL=PASS "$run_dir/install-arm-helper.serial.log"
    fi
    guest_run gdb-launch FLR-0344-launch-gdb.cmd || echo FLR0344_GDB_LAUNCH_COMMAND=FAIL
    grep -F FLR0344_GDB_LAUNCH=PASS "$run_dir/gdb-launch.serial.log" || true
    guest_run arm-wait "$arm_wait_command" || echo FLR0344_GDB_ARM_WAIT_COMMAND=FAIL
    grep -E 'FLR0344_|FLR0346_|FLR0348_|Hardware watchpoint|Old value|New value|Program received signal|error:|Error|Cannot|ptrace|Undefined|No such|^#([0-9]+) ' \
        "$run_dir/arm-wait.serial.log" | tail -n 100 || true
    if grep -Fq "$arm_wait_pass_marker" "$run_dir/arm-wait.serial.log"; then
        guest_run watch-window FLR-0344-watch-window.cmd || echo FLR0344_GDB_WATCH_WINDOW_COMMAND=FAIL
    else
        echo FLR0344_GDB_WATCH_WINDOW=SKIPPED arm-failed
    fi
    guest_run watch-result FLR-0344-poll-watch.cmd || echo FLR0344_GDB_RESULT_POLL=FAIL
    grep -E 'FLR0344_|FLR0346_|FLR0348_|Hardware watchpoint|Old value|New value|Program received signal|error:|Error|Cannot|ptrace|Undefined|No such|^#([0-9]+) ' \
        "$run_dir/watch-result.serial.log" | tail -n 100 || true
else
    echo "FLR0344_GDB_WATCH=SKIPPED present_state=$present_state"
fi

guest_run runtime-state FLR-0344-capture-runtime-state.cmd
grep -E 'guest_uptime=|tracked_pid=|app_process=|app_log_sha256=|gdb_log_sha256=|FLR0344_.*_count=|FLR0348_.*_count=|FLUORITE_VK_(SUBMIT_RETURN|PRESENT_CALL_BEGIN|QUEUE_PRESENT_ENTER|QUEUE_PRESENT_RETURN)|FLR0344_RUNTIME_STATE_DONE|Oops:|RIP:|CR2:|Call Trace:|BUG:|Killed process' \
    "$run_dir/runtime-state.serial.log" | tail -n 120 || true
"$capture" capture --socket "$qmp" --output "$run_dir/post-run.ppm" >"$run_dir/post-run-capture.log" 2>&1
"$capture" video --socket "$qmp" --frames-dir "$run_dir/post-run-frames" --frames 8 --interval 1 >"$run_dir/post-run-video.log" 2>&1
"$capture" analyze --input "$run_dir/post-run.ppm" --region 0,0,1280,800 >"$run_dir/post-run-full-analysis.log" 2>&1
"$capture" analyze --input "$run_dir/post-run.ppm" --region 0,200,1280,600 --reference "$run_dir/pre-launch.ppm" >"$run_dir/post-run-3d-roi-analysis.log" 2>&1
cat "$run_dir/post-run-capture.log" "$run_dir/post-run-video.log" "$run_dir/post-run-full-analysis.log" "$run_dir/post-run-3d-roi-analysis.log"
sha256sum "$run_dir/post-run.ppm" "$run_dir/post-run-frames"/*.ppm
guest_run stop-app FLR-0344-stop-recorded-app.cmd
grep -E 'app_stop=|flutter_processes=|FLR0344_APP_STOP_DONE' "$run_dir/stop-app.serial.log"
grep -F flutter_processes=0 "$run_dir/stop-app.serial.log"
"$harness" qmp-quit --qmp "$qmp" | tee "$run_dir/qmp-quit.log"
echo "FLR0344_RUN_DONE present=$present_state"
