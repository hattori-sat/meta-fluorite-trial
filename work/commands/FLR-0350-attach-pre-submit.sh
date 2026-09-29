#!/bin/sh

. /run/user/1001/FLR-0350-gate-common.sh || exit 80

pidfile=$FLR0350_USER_DIR/flr0350-flutter.pid
startfile=$FLR0350_USER_DIR/flr0350-wrapper.start
gate=$FLR0350_USER_DIR/flr0350-go.fifo
script=$FLR0350_USER_DIR/flr0350-sync-producer.gdb
armed=$FLR0350_USER_DIR/flr0350-gdb-armed
gdbpidfile=$FLR0350_USER_DIR/flr0350-gdb.pid
gdbstartfile=$FLR0350_USER_DIR/flr0350-gdb.start
gdb_log=$FLR0350_USER_DIR/flr0350-gdb.log

pid=$(cat "$pidfile" 2>/dev/null || true)
expected_start=$(cat "$startfile" 2>/dev/null || true)
start=$(flr0350_proc_start "$pid")
state=$(flr0350_proc_state "$pid")
comm=$(cat "$FLR0350_PROC_ROOT/$pid/comm" 2>/dev/null || true)
uid=$(flr0350_proc_uid "$pid")
tracer=$(flr0350_proc_tracer "$pid")
syscall=$(cat "$FLR0350_PROC_ROOT/$pid/syscall" 2>/dev/null || true)
set -- $syscall
syscall_nr=${1:-unknown}
syscall_fd=${2:-unknown}
gate_stat=$(stat -L -c '%d:%i:%u:%a' "$gate" 2>/dev/null || true)
gate_id=${gate_stat%%:*}
gate_rest=${gate_stat#*:}
gate_ino=${gate_rest%%:*}
gate_owner=${gate_rest#*:}
gate_uid=${gate_owner%%:*}
gate_mode=${gate_owner#*:}
fd0=FAIL
fd3=FAIL
if flr0350_load_identity; then
    flr0350_identity_matches_process "$pid" "$start" "$uid" &&
        [ "$FLR0350_ID_DEV:$FLR0350_ID_INO" = "$gate_id:$gate_ino" ] &&
        [ "$(flr0350_object_id "$FLR0350_PROC_ROOT/$pid/fd/0")" = \
            "$FLR0350_ID_DEV:$FLR0350_ID_INO" ] && fd0=PASS
    [ "$(flr0350_object_id "$FLR0350_PROC_ROOT/$pid/fd/3")" = \
        "$FLR0350_ID_DEV:$FLR0350_ID_INO" ] && fd3=PASS
fi

values=
failed=
check() {
    name=$1
    shift
    if "$@"; then
        values="$values $name=PASS"
    else
        values="$values $name=FAIL"
        if [ -n "$failed" ]; then failed="$failed,$name"; else failed=$name; fi
    fi
}

check pid_present test -n "$pid"
check recorded_start_present test -n "$expected_start"
check start_match test "$start" = "$expected_start"
check comm_match test "$comm" = sh
check uid_match test "$uid" = "$(id -u agl-driver)"
check running_state test "$state" = S
check tracer_clear test "$tracer" = 0
check syscall_read test "$syscall_nr" = 0
check syscall_fd0 test "$syscall_fd" = 0x0
check gate_fifo test -p "$gate"
check gate_owner_mode test "$gate_uid:$gate_mode" = "$(id -u agl-driver):600"
check root_identity_loaded test -n "${FLR0350_ID_RUN_ID:-}"
check root_identity_process flr0350_identity_matches_process "$pid" "$start" "$uid"
check root_identity_fifo test "$FLR0350_ID_DEV:$FLR0350_ID_INO" = "$gate_id:$gate_ino"
check fd0_same_gate test "$fd0" = PASS
check fd3_same_gate test "$fd3" = PASS
check fd3_path_match test "$(readlink "$FLR0350_PROC_ROOT/$pid/fd/3" 2>/dev/null || true)" = "$gate"
check script_readable test -r "$script"
check armed_clear test ! -e "$armed"
check auth_clear test ! -e "$FLR0350_ROOT_DIR/attach.auth"
check go_clear test ! -e "$FLR0350_ROOT_DIR/go.record"
check gdb_pid_clear test ! -e "$gdbpidfile"
check gdb_start_clear test ! -e "$gdbstartfile"
check log_clear test ! -e "$gdb_log"

echo "FLR0350_GDB_ATTACH_PREFLIGHT$values fd0_same_gate=$fd0 fd3_same_gate=$fd3 syscall_nr=$syscall_nr syscall_fd=$syscall_fd"
if [ -n "$failed" ]; then
    echo "FLR0350_GDB_ATTACH=FAIL precondition failed=$failed"
    exit 0
fi

/bin/sh -c 'trap - INT; exec /usr/bin/gdb -q -batch -p "$1" -x "$2"' \
    _ "$pid" "$script" </dev/null >"$gdb_log" 2>&1 &
gdb_pid=$!
printf '%s\n' "$gdb_pid" >"$gdbpidfile"
gdb_start=
i=0
while [ "$i" -lt 10 ]; do
    gdb_start=$(flr0350_proc_start "$gdb_pid")
    [ -n "$gdb_start" ] && break
    sleep 0.1
    i=$((i + 1))
done
[ -z "$gdb_start" ] || printf '%s\n' "$gdb_start" >"$gdbstartfile"
echo "FLR0350_GDB_PID=$gdb_pid start=${gdb_start:-unknown} target_pid=$pid"

outcome=FAIL
i=0
while [ "$i" -lt 48 ]; do
    gdb_comm=$(cat "$FLR0350_PROC_ROOT/$gdb_pid/comm" 2>/dev/null || true)
    current_gdb_start=$(flr0350_proc_start "$gdb_pid")
    gdb_uid=$(flr0350_proc_uid "$gdb_pid")
    current_start=$(flr0350_proc_start "$pid")
    current_state=$(flr0350_proc_state "$pid")
    current_uid=$(flr0350_proc_uid "$pid")
    current_tracer=$(flr0350_proc_tracer "$pid")
    if flr0350_load_identity &&
        [ "$gdb_comm" = gdb ] && [ "$gdb_uid" = 0 ] &&
        [ "$current_gdb_start" = "$gdb_start" ] && kill -0 "$gdb_pid" 2>/dev/null &&
        [ "$current_start" = "$expected_start" ] && [ "$current_uid" = "$uid" ] &&
        { [ "$current_state" = t ] || [ "$current_state" = T ]; } &&
        [ "$current_tracer" = "$gdb_pid" ] &&
        flr0350_identity_matches_process "$pid" "$current_start" "$current_uid" &&
        flr0350_identity_matches_gate && flr0350_identity_matches_fds &&
        flr0350_auth_record_matches "$gdb_pid" "$gdb_start" &&
        grep -qx "FLR0350_GDB_ARMED=PASS target_pid=$pid gdb_pid=$gdb_pid" "$armed" 2>/dev/null; then
        outcome=PASS
        break
    fi
    [ "$gdb_comm" = gdb ] || break
    sleep 0.25
    i=$((i + 1))
done

if [ "$outcome" = PASS ]; then
    echo "FLR0350_GDB_ATTACH=PASS target_pid=$pid gdb_pid=$gdb_pid gdb_start=$gdb_start state=$current_state gate_identity=$FLR0350_ID_DEV:$FLR0350_ID_INO target_stopped=1 go_pending=1"
else
    echo "FLR0350_GDB_ATTACH=FAIL reason=stopped-attach-identity polls=$i comm=${gdb_comm:-exited} tracer=${current_tracer:-unknown} state=${current_state:-unknown} syscall=${syscall:-unknown}"
    if [ "$gdb_comm" = gdb ] && [ "$(flr0350_proc_start "$gdb_pid")" = "$gdb_start" ] && kill -0 "$gdb_pid" 2>/dev/null; then
        kill -INT "$gdb_pid" 2>/dev/null || true
        wait "$gdb_pid" 2>/dev/null || true
    fi
    sed -n '1,120p' "$gdb_log" 2>/dev/null || true
fi
