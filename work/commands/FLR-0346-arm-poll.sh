#!/bin/sh
set -eu

if [ "$#" -ne 5 ]; then
    echo 'FLR0346_ARM_WAIT=FAIL usage' >&2
    exit 2
fi

pid_file=$1
gdb_log=$2
proc_root=$3
poll_limit=$4
poll_interval=$5
armed_marker=FLR0344_WATCHPOINTS_ARMED=1

case "$poll_limit" in
    ''|*[!0-9]*|0) echo 'FLR0346_ARM_WAIT=FAIL invalid-poll-limit' >&2; exit 2 ;;
esac

if [ ! -s "$pid_file" ]; then
    echo 'FLR0346_ARM_WAIT=FAIL missing-pidfile'
    exit 2
fi
gdb_pid=$(cat "$pid_file")
case "$gdb_pid" in
    ''|*[!0-9]*) echo 'FLR0346_ARM_WAIT=FAIL invalid-pidfile' >&2; exit 2 ;;
esac
if [ ! -e "$gdb_log" ]; then
    echo 'FLR0346_ARM_WAIT=FAIL missing-logfile'
    exit 2
fi

armed=0
polls=0
while [ "$polls" -lt "$poll_limit" ]; do
    if grep -Fq "$armed_marker" "$gdb_log" 2>/dev/null; then
        armed=1
        break
    fi
    gdb_state=$(ps -p "$gdb_pid" -o stat= 2>/dev/null | tr -d ' ')
    gdb_comm=$(cat "$proc_root/$gdb_pid/comm" 2>/dev/null || true)
    if [ -z "$gdb_state" ] || [ "${gdb_state#Z}" != "$gdb_state" ] ||
        [ "$gdb_comm" != gdb ]; then
        break
    fi
    sleep "$poll_interval"
    polls=$((polls + 1))
done

if [ "$armed" -eq 1 ]; then
    guest_uptime=$(cut -d' ' -f1 /proc/uptime 2>/dev/null || echo unavailable)
    echo "FLR0346_ARM_WAIT=PASS armed=1 polls=$polls guest_uptime=$guest_uptime"
    exit 0
fi

gdb_state=$(ps -p "$gdb_pid" -o stat= 2>/dev/null | tr -d ' ')
gdb_comm=$(cat "$proc_root/$gdb_pid/comm" 2>/dev/null || true)
[ -n "$gdb_comm" ] || gdb_comm=exited
[ -n "$gdb_state" ] || gdb_state=exited
echo "FLR0346_ARM_WAIT=FAIL marker_not_seen polls=$polls gdb_comm=$gdb_comm gdb_state=$gdb_state"

if [ "$gdb_comm" = gdb ] && [ "${gdb_state#Z}" = "$gdb_state" ]; then
    kill -INT "$gdb_pid" 2>/dev/null || true
    attempt=0
    while [ "$attempt" -lt 10 ]; do
        gdb_state=$(ps -p "$gdb_pid" -o stat= 2>/dev/null | tr -d ' ')
        [ -n "$gdb_state" ] && [ "${gdb_state#Z}" = "$gdb_state" ] || break
        sleep 0.2
        attempt=$((attempt + 1))
    done
    gdb_state=$(ps -p "$gdb_pid" -o stat= 2>/dev/null | tr -d ' ')
    if [ -n "$gdb_state" ] && [ "${gdb_state#Z}" = "$gdb_state" ]; then
        kill -TERM "$gdb_pid" 2>/dev/null || true
        echo 'FLR0346_GDB_TERM_FALLBACK=sent'
    fi
    wait "$gdb_pid" 2>/dev/null || true
fi

echo FLR0346_GDB_TRANSCRIPT_BEGIN
sed -n '1,80p' "$gdb_log"
echo FLR0346_GDB_TRANSCRIPT_END
exit 1
