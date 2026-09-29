#!/bin/sh

. /run/user/1001/FLR-0350-gate-common.sh || exit 80

pidfile=$FLR0350_USER_DIR/flr0350-flutter.pid
startfile=$FLR0350_USER_DIR/flr0350-wrapper.start
execfile=$FLR0350_USER_DIR/flr0350-exec-result
gpidfile=$FLR0350_USER_DIR/flr0350-gdb.pid
gdbstartfile=$FLR0350_USER_DIR/flr0350-gdb.start
pid=$(cat "$pidfile" 2>/dev/null || true)
expected_start=$(cat "$startfile" 2>/dev/null || true)
gpid=$(cat "$gpidfile" 2>/dev/null || true)
expected_gstart=$(cat "$gdbstartfile" 2>/dev/null || true)
gcomm=$(cat "$FLR0350_PROC_ROOT/$gpid/comm" 2>/dev/null || true)
gstart=$(flr0350_proc_start "$gpid")
guid=$(flr0350_proc_uid "$gpid")
target_start=$(flr0350_proc_start "$pid")
target_uid=$(flr0350_proc_uid "$pid")
target_state=$(flr0350_proc_state "$pid")
target_gdb=$(flr0350_proc_tracer "$pid")
target_comm=$(cat "$FLR0350_PROC_ROOT/$pid/comm" 2>/dev/null || true)
target_exe=$(readlink "$FLR0350_PROC_ROOT/$pid/exe" 2>/dev/null || true)

exec_seen=0
if [ -n "$pid" ] && [ "$target_start" = "$expected_start" ] &&
    [ "$target_uid" = "$(id -u agl-driver)" ] && [ "$target_gdb" = "$gpid" ] &&
    [ "$target_comm" = flutter-auto ] && [ "$target_exe" = /usr/bin/flutter-auto ] &&
    grep -qx "FLR0350_SAME_PID_EXEC=PASS pid=$pid" "$execfile" 2>/dev/null; then
    exec_seen=1
fi
go_valid=0
if flr0350_load_identity &&
    flr0350_identity_matches_process "$pid" "$expected_start" "$(id -u agl-driver)" &&
    [ "$target_start" = "$expected_start" ] &&
    [ "$target_uid" = "$(id -u agl-driver)" ] && [ "$target_gdb" = "$gpid" ] &&
    [ "$gstart" = "$expected_gstart" ] && [ "$gcomm" = gdb ] && [ "$guid" = 0 ] &&
    flr0350_go_record_matches "$gpid" "$expected_gstart"; then
    go_valid=1
fi

if [ "$exec_seen" -ne 1 ] || [ "$go_valid" -ne 1 ]; then
    if [ -n "$pid" ] && [ -n "$expected_start" ] &&
        flr0350_load_identity &&
        flr0350_identity_matches_process "$pid" "$expected_start" "$target_uid" &&
        [ "$target_uid" = "$(id -u agl-driver)" ]; then
        if [ "$target_start" = "$expected_start" ] &&
            { [ "$target_state" = Z ] || [ "$target_state" = X ] || [ "$target_state" = x ]; }; then
            echo "FLR0350_UNRECORDED_TARGET_ABORT=PASS pid=$pid state=$target_state already-terminated=1"
        elif [ "$target_start" = "$expected_start" ]; then
            kill -KILL "$pid" 2>/dev/null || true
            i=0
            while [ "$i" -lt 20 ] && [ "$(flr0350_proc_start "$pid")" = "$expected_start" ] &&
                [ "$(flr0350_proc_state "$pid")" != Z ] &&
                [ "$(flr0350_proc_state "$pid")" != X ] &&
                [ "$(flr0350_proc_state "$pid")" != x ]; do
                sleep 0.1
                i=$((i + 1))
            done
            final_start=$(flr0350_proc_start "$pid")
            final_state=$(flr0350_proc_state "$pid")
            if [ "$final_start" = "$expected_start" ] &&
                [ "$final_state" != Z ] && [ "$final_state" != X ] && [ "$final_state" != x ]; then
                echo "FLR0350_UNRECORDED_TARGET_ABORT=FAIL pid=$pid state=${final_state:-unknown}"
                exit 81
            fi
            echo "FLR0350_UNRECORDED_TARGET_ABORT=PASS pid=$pid state=${final_state:-gone} go_record_valid=$go_valid exec_seen=$exec_seen"
        elif [ -z "$target_start" ]; then
            echo "FLR0350_UNRECORDED_TARGET_ABORT=PASS pid=$pid already-exited=1 go_record_valid=$go_valid exec_seen=$exec_seen"
        else
            echo "FLR0350_UNRECORDED_TARGET_ABORT=FAIL pid=$pid start=${target_start:-unknown} expected=$expected_start"
            exit 82
        fi
    elif [ -z "$target_start" ]; then
        echo "FLR0350_UNRECORDED_TARGET_ABORT=PASS pid=${pid:-missing} already-exited=1"
    else
        echo "FLR0350_UNRECORDED_TARGET_ABORT=FAIL pid=${pid:-missing} identity=unknown"
        exit 83
    fi
fi

if [ -z "$gcomm" ]; then
    echo FLR0350_GDB_INTERRUPT=not-running
elif [ "$gcomm" = gdb ] && [ "$gstart" = "$expected_gstart" ] &&
    [ "$guid" = 0 ] && kill -0 "$gpid" 2>/dev/null; then
    kill -INT "$gpid" 2>/dev/null || true
    echo "FLR0350_GDB_INTERRUPT=sent pid=$gpid start=$gstart"
    i=0
    while [ "$i" -lt 10 ] && [ "$(flr0350_proc_start "$gpid")" = "$expected_gstart" ] &&
        [ "$(cat "$FLR0350_PROC_ROOT/$gpid/comm" 2>/dev/null || true)" = gdb ]; do
        sleep 0.2
        i=$((i + 1))
    done
    if [ "$(flr0350_proc_start "$gpid")" = "$expected_gstart" ] &&
        [ "$(cat "$FLR0350_PROC_ROOT/$gpid/comm" 2>/dev/null || true)" = gdb ]; then
        kill -TERM "$gpid" 2>/dev/null || true
        echo FLR0350_GDB_TERM_FALLBACK=sent
    fi
else
    echo "FLR0350_GDB_INTERRUPT=FAIL identity_mismatch pid=${gpid:-missing} start=${gstart:-unknown} expected_start=${expected_gstart:-unknown} uid=${guid:-unknown}"
fi

remainder_start=$(flr0350_proc_start "$gpid")
remainder_comm=$(cat "$FLR0350_PROC_ROOT/$gpid/comm" 2>/dev/null || true)
if [ -z "$remainder_start" ] || [ "$remainder_start" != "$expected_gstart" ]; then
    echo FLR0350_GDB_REMAINDER=exited
else
    echo "FLR0350_GDB_REMAINDER=running comm=$remainder_comm start=$remainder_start"
fi
if [ -s "$FLR0350_USER_DIR/flr0350-gdb.log" ]; then
    grep -E 'FLR0350_|Hardware watchpoint|Old value|New value|Program received signal|error:|Error|Cannot|ptrace|failed|Failed|^#([0-9]+) ' \
        "$FLR0350_USER_DIR/flr0350-gdb.log" | tail -n 120 || true
fi
