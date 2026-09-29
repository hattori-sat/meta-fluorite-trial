#!/bin/sh

. /run/user/1001/FLR-0350-gate-common.sh || exit 80

pidfile=$FLR0350_USER_DIR/flr0350-flutter.pid
startfile=$FLR0350_USER_DIR/flr0350-wrapper.start
gdbpidfile=$FLR0350_USER_DIR/flr0350-gdb.pid
gdbstartfile=$FLR0350_USER_DIR/flr0350-gdb.start
armed=$FLR0350_USER_DIR/flr0350-gdb-armed
execfile=$FLR0350_USER_DIR/flr0350-exec-result
gate=$FLR0350_USER_DIR/flr0350-go.fifo
go_timefile=$FLR0350_USER_DIR/flr0350-go-uptime

write_go_while_stopped() {
    pid=$1
    expected_start=$2
    gdb_pid=$3
    gdb_start=$4
    flr0350_load_identity || { echo FLR0350_GO=FAIL reason=identity-record; return 1; }
    start=$(flr0350_proc_start "$pid")
    state=$(flr0350_proc_state "$pid")
    uid=$(flr0350_proc_uid "$pid")
    tracer=$(flr0350_proc_tracer "$pid")
    [ "$start" = "$expected_start" ] &&
        flr0350_identity_matches_process "$pid" "$start" "$uid" &&
        { [ "$state" = t ] || [ "$state" = T ]; } &&
        [ "$tracer" = "$gdb_pid" ] &&
        [ "$(flr0350_proc_start "$gdb_pid")" = "$gdb_start" ] &&
        flr0350_identity_matches_gate && flr0350_identity_matches_fds &&
        flr0350_auth_record_matches "$gdb_pid" "$gdb_start" || {
            echo "FLR0350_GO=FAIL reason=initial-stopped-identity state=${state:-unknown} tracer=${tracer:-unknown}"
            return 1
        }

    exec 3>"$gate" || { echo FLR0350_GO_WRITE=FAIL reason=fifo-open; return 1; }
    writer_fd=${FLR0350_WRITER_FD_PATH:-$FLR0350_PROC_ROOT/$$/fd/3}
    writer_id=$(flr0350_object_id "$writer_fd")

    flr0350_load_identity || { echo FLR0350_GO=FAIL reason=post-open-record; exec 3>&-; return 1; }
    start_after=$(flr0350_proc_start "$pid")
    state_after=$(flr0350_proc_state "$pid")
    uid_after=$(flr0350_proc_uid "$pid")
    tracer_after=$(flr0350_proc_tracer "$pid")
    gdb_start_after=$(flr0350_proc_start "$gdb_pid")
    if [ "$writer_id" != "$FLR0350_ID_DEV:$FLR0350_ID_INO" ] ||
        [ "$start_after" != "$expected_start" ] ||
        [ "$uid_after" != "$uid" ] ||
        { [ "$state_after" != t ] && [ "$state_after" != T ]; } ||
        [ "$tracer_after" != "$gdb_pid" ] ||
        [ "$gdb_start_after" != "$gdb_start" ] ||
        ! flr0350_identity_matches_process "$pid" "$start_after" "$uid_after" ||
        ! flr0350_identity_matches_gate || ! flr0350_identity_matches_fds ||
        ! flr0350_auth_record_matches "$gdb_pid" "$gdb_start"; then
        echo "FLR0350_GO=FAIL reason=post-open-identity writer=$writer_id state=${state_after:-unknown}"
        exec 3>&-
        return 1
    fi

    if ! printf '%s\n' FLR0350_GO >&3; then
        echo FLR0350_GO_WRITE=FAIL reason=fifo-write
        exec 3>&-
        return 1
    fi
    exec 3>&-
    echo "FLR0350_GO_WRITE=PASS writer=$writer_id bytes=11 target_stopped=1"
    go_record="1 $FLR0350_RUN_ID $pid $start_after $uid_after $FLR0350_ID_DEV $FLR0350_ID_INO $gdb_pid $gdb_start $FLR0350_ID_DEV $FLR0350_ID_INO 11"
    if ! flr0350_write_once "$FLR0350_ROOT_DIR/go.record" "$go_record"; then
        echo FLR0350_GO_RECORD=FAIL reason=publication-after-write token=unconsumed
        return 1
    fi
    go_uptime=$(cut -d' ' -f1 /proc/uptime 2>/dev/null || true)
    if [ -n "$go_uptime" ] && ! printf '%s\n' "$go_uptime" >"$go_timefile"; then
        echo FLR0350_GO_TIME=FAIL reason=auxiliary-marker
    elif [ -z "$go_uptime" ]; then
        echo FLR0350_GO_TIME=UNKNOWN reason=guest-uptime-unavailable
    fi
    echo FLR0350_GO_RECORD=PASS token=queued target_stopped=1
    return 0
}

if [ "${1:-}" = --write-go ]; then
    shift
    write_go_while_stopped "$@"
    exit $?
fi

pid=$(cat "$pidfile" 2>/dev/null || true)
expected_start=$(cat "$startfile" 2>/dev/null || true)
gdb_pid=$(cat "$gdbpidfile" 2>/dev/null || true)
expected_gdb_start=$(cat "$gdbstartfile" 2>/dev/null || true)
start=$(flr0350_proc_start "$pid")
state=$(flr0350_proc_state "$pid")
uid=$(flr0350_proc_uid "$pid")
tracer=$(flr0350_proc_tracer "$pid")
gdb_start=$(flr0350_proc_start "$gdb_pid")
gdb_comm=$(cat "$FLR0350_PROC_ROOT/$gdb_pid/comm" 2>/dev/null || true)
gdb_uid=$(flr0350_proc_uid "$gdb_pid")

if ! flr0350_load_identity ||
    [ "$start" != "$expected_start" ] || [ "$uid" != "$(id -u agl-driver)" ] ||
    [ "$gdb_start" != "$expected_gdb_start" ] || [ "$gdb_comm" != gdb ] ||
    [ "$gdb_uid" != 0 ] || [ "$tracer" != "$gdb_pid" ] ||
    { [ "$state" != t ] && [ "$state" != T ]; } ||
    ! flr0350_identity_matches_process "$pid" "$start" "$uid" ||
    ! flr0350_identity_matches_gate || ! flr0350_identity_matches_fds ||
    ! flr0350_auth_record_matches "$gdb_pid" "$expected_gdb_start" ||
    [ -e "$FLR0350_ROOT_DIR/go.record" ] || [ -L "$FLR0350_ROOT_DIR/go.record" ] ||
    [ -e "$go_timefile" ] || [ -L "$go_timefile" ] ||
    [ -e "$execfile" ] || [ -L "$execfile" ] ||
    ! grep -qx "FLR0350_GDB_ARMED=PASS target_pid=$pid gdb_pid=$gdb_pid" "$armed" 2>/dev/null ||
    ! kill -0 "$gdb_pid" 2>/dev/null; then
    echo "FLR0350_GO=FAIL reason=stopped-target-or-authorization pid=${pid:-missing} state=${state:-unknown} tracer=${tracer:-unknown} gdb=${gdb_pid:-missing}"
    exit 0
fi

timeout 2 /bin/sh "$0" --write-go "$pid" "$expected_start" \
    "$gdb_pid" "$expected_gdb_start"
write_status=$?
if [ "$write_status" -ne 0 ]; then
    echo "FLR0350_GO=FAIL reason=writer-command status=$write_status"
    exit 0
fi

exec_status=UNKNOWN
i=0
while [ "$i" -lt 20 ]; do
    current_start=$(flr0350_proc_start "$pid")
    current_comm=$(cat "$FLR0350_PROC_ROOT/$pid/comm" 2>/dev/null || true)
    current_exe=$(readlink "$FLR0350_PROC_ROOT/$pid/exe" 2>/dev/null || true)
    current_tracer=$(flr0350_proc_tracer "$pid")
    current_uid=$(flr0350_proc_uid "$pid")
    if [ "$current_start" = "$expected_start" ] &&
        [ "$current_comm" = flutter-auto ] &&
        [ "$current_exe" = /usr/bin/flutter-auto ] &&
        [ "$current_tracer" = "$gdb_pid" ] &&
        [ "$current_uid" = "$(id -u agl-driver)" ] &&
        flr0350_go_record_matches "$gdb_pid" "$expected_gdb_start" &&
        grep -q "FLR0350_SAME_PID_EXEC=PASS pid=$pid" "$execfile" 2>/dev/null; then
        echo "pid=$pid start=$current_start comm=$current_comm exe=$current_exe tracer=$current_tracer"
        echo FLR0350_EXEC=PASS
        exec_status=PASS
        break
    fi
    sleep 0.2
    i=$((i + 1))
done
if [ "$exec_status" != PASS ]; then
    echo "FLR0350_EXEC=UNKNOWN polls=$i comm=${current_comm:-unknown} state=$(flr0350_proc_state "$pid") go_record=$(flr0350_root_file_valid "$FLR0350_ROOT_DIR/go.record" && echo present || echo missing)"
fi
