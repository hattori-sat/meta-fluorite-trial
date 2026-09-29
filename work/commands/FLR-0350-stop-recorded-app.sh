#!/bin/sh

. /run/user/1001/FLR-0350-gate-common.sh || exit 80

pidfile=$FLR0350_USER_DIR/flr0350-flutter.pid
startfile=$FLR0350_USER_DIR/flr0350-wrapper.start
gate=$FLR0350_USER_DIR/flr0350-go.fifo
gdbpidfile=$FLR0350_USER_DIR/flr0350-gdb.pid
gdbstartfile=$FLR0350_USER_DIR/flr0350-gdb.start
pid=$(cat "$pidfile" 2>/dev/null || true)
expected=$(cat "$startfile" 2>/dev/null || true)
start=$(flr0350_proc_start "$pid")
state=$(flr0350_proc_state "$pid")
comm=$(cat "$FLR0350_PROC_ROOT/$pid/comm" 2>/dev/null || true)
uid=$(flr0350_proc_uid "$pid")
target_gone=0

if [ -n "$pid" ] && [ -n "$expected" ] && [ "$start" = "$expected" ] &&
    [ "$uid" = "$(id -u agl-driver)" ] &&
    flr0350_load_identity &&
    flr0350_identity_matches_process "$pid" "$expected" "$uid" &&
    { [ "$comm" = flutter-auto ] || [ "$comm" = sh ]; }; then
    if [ "$state" = Z ] || [ "$state" = X ] || [ "$state" = x ]; then
        echo "FLR0350_APP_STOP=PASS pid=$pid start=$expected state=$state already-terminated=1"
        target_gone=1
    else
        kill -TERM "$pid" 2>/dev/null || true
        i=0
        while [ "$i" -lt 20 ] && [ "$(flr0350_proc_start "$pid")" = "$expected" ] &&
            [ "$(flr0350_proc_state "$pid")" != Z ] &&
            [ "$(flr0350_proc_state "$pid")" != X ] &&
            [ "$(flr0350_proc_state "$pid")" != x ]; do
            sleep 0.2
            i=$((i + 1))
        done
        final_start=$(flr0350_proc_start "$pid")
        final_state=$(flr0350_proc_state "$pid")
        if [ "$final_start" != "$expected" ] || [ "$final_state" = Z ] ||
            [ "$final_state" = X ] || [ "$final_state" = x ]; then
            echo "FLR0350_APP_STOP=PASS pid=$pid start=$expected state=${final_state:-gone}"
            target_gone=1
        else
            echo "FLR0350_APP_STOP=FAIL pid=$pid start=$final_start state=${final_state:-unknown}"
        fi
    fi
elif [ -n "$pid" ] && [ -n "$expected" ] && [ "$start" = "$expected" ] &&
    { [ "$state" = Z ] || [ "$state" = X ] || [ "$state" = x ]; };
then
    echo "FLR0350_APP_STOP=PASS pid=$pid start=$expected state=$state already-terminated=1"
    target_gone=1
elif [ -n "$pid" ] && [ -n "$expected" ] && [ "$start" != "$expected" ]; then
    echo "FLR0350_APP_STOP=already-exited recorded_pid=$pid recorded_start=$expected"
    target_gone=1
elif [ -z "$pid" ] && [ ! -e "$gate" ] && [ ! -L "$gate" ]; then
    echo FLR0350_APP_STOP=not-launched
    target_gone=1
else
    echo "FLR0350_APP_STOP=FAIL identity_unknown pid=${pid:-missing} comm=${comm:-exited} start=${start:-unknown} expected=${expected:-unknown}"
fi

count=0
for candidate in $(pgrep -x flutter-auto 2>/dev/null || true); do
    candidate_state=$(flr0350_proc_state "$candidate")
    case "$candidate_state" in
        Z|X|x|'') ;;
        *) count=$((count + 1)) ;;
    esac
done
echo "flutter_processes=$count"
cleanup_ok=0
if [ "$target_gone" -eq 1 ] && [ "$count" -eq 0 ]; then
    if flr0350_load_run_id; then
        if [ -e "$FLR0350_ROOT_DIR/fifo.identity" ] || [ -L "$FLR0350_ROOT_DIR/fifo.identity" ]; then
            if flr0350_load_identity && [ "$FLR0350_ID_PID" = "$pid" ] &&
                [ "$FLR0350_ID_START" = "$expected" ] &&
                [ "$FLR0350_ID_UID" = "$(id -u agl-driver)" ]; then
                fifo_ok=0
                if [ -e "$gate" ] || [ -L "$gate" ]; then
                    gate_meta=$(stat -c '%u:%a' "$gate" 2>/dev/null || true)
                    if flr0350_identity_matches_gate &&
                        [ "$gate_meta" = "$(id -u agl-driver):600" ] && unlink "$gate"; then
                        echo FLR0350_FIFO_REMOVE=PASS identity=matched
                        fifo_ok=1
                    else
                        echo "FLR0350_FIFO_REMOVE=FAIL reason=identity-or-owner-mismatch meta=${gate_meta:-unknown}"
                    fi
                else
                    echo FLR0350_FIFO_REMOVE=PASS identity=already-absent
                    fifo_ok=1
                fi
                gdb_pid=$(cat "$gdbpidfile" 2>/dev/null || true)
                gdb_start=$(cat "$gdbstartfile" 2>/dev/null || true)
                markers_ok=1
                for record_path in "$FLR0350_ROOT_DIR"/*; do
                    [ -e "$record_path" ] || [ -L "$record_path" ] || continue
                    case "${record_path##*/}" in
                        run.id|fifo.identity|attach.auth|go.record) ;;
                        *) markers_ok=0 ;;
                    esac
                done
                for record in attach.auth go.record; do
                    record_path=$FLR0350_ROOT_DIR/$record
                    if [ -e "$record_path" ] || [ -L "$record_path" ]; then
                        case "$record" in
                            attach.auth) flr0350_auth_record_matches "$gdb_pid" "$gdb_start" ;;
                            go.record) flr0350_go_record_matches "$gdb_pid" "$gdb_start" ;;
                        esac || markers_ok=0
                    fi
                done
                if [ "$fifo_ok" -eq 1 ] && [ "$markers_ok" -eq 1 ]; then
                    for record in go.record attach.auth fifo.identity run.id; do
                        record_path=$FLR0350_ROOT_DIR/$record
                        if [ -e "$record_path" ] || [ -L "$record_path" ]; then
                            flr0350_root_file_valid "$record_path" && unlink "$record_path" || markers_ok=0
                        fi
                    done
                    if [ "$markers_ok" -eq 1 ] && rmdir "$FLR0350_ROOT_DIR" 2>/dev/null; then
                        cleanup_ok=1
                    fi
                fi
            fi
        elif [ ! -e "$gate" ] && [ ! -L "$gate" ] &&
            [ ! -e "$FLR0350_ROOT_DIR/attach.auth" ] &&
            [ ! -e "$FLR0350_ROOT_DIR/go.record" ]; then
            flr0350_root_file_valid "$FLR0350_ROOT_DIR/run.id" &&
                unlink "$FLR0350_ROOT_DIR/run.id" &&
                rmdir "$FLR0350_ROOT_DIR" 2>/dev/null && cleanup_ok=1
        fi
    elif [ ! -e "$FLR0350_ROOT_DIR" ] && [ ! -L "$FLR0350_ROOT_DIR" ] &&
        [ ! -e "$gate" ] && [ ! -L "$gate" ]; then
        cleanup_ok=1
    fi
fi

if [ "$cleanup_ok" -eq 1 ]; then
    echo FLR0350_FIFO_CLEANUP=PASS removed=run-owned-fifo-and-records
else
    echo FLR0350_FIFO_CLEANUP=FAIL reason=ownership-or-residual-record-unproven
fi
