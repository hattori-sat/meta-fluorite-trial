#!/bin/sh

FLR0350_USER_DIR=${FLR0350_USER_DIR:-/run/user/1001}
FLR0350_ROOT_DIR=${FLR0350_ROOT_DIR:-/run/flr0350}
FLR0350_PROC_ROOT=${FLR0350_PROC_ROOT:-/proc}

flr0350_root_dir_valid() {
    [ -d "$FLR0350_ROOT_DIR" ] && [ ! -L "$FLR0350_ROOT_DIR" ] &&
        [ "$(stat -c '%u:%a' "$FLR0350_ROOT_DIR" 2>/dev/null || true)" = 0:700 ]
}

flr0350_root_file_valid() {
    [ -f "$1" ] && [ ! -L "$1" ] &&
        [ "$(stat -c '%u:%a' "$1" 2>/dev/null || true)" = 0:600 ] &&
        [ "$(wc -l <"$1" 2>/dev/null | tr -d ' ')" = 1 ]
}

flr0350_load_run_id() {
    flr0350_root_dir_valid || return 1
    flr0350_root_file_valid "$FLR0350_ROOT_DIR/run.id" || return 1
    FLR0350_RUN_ID=$(cat "$FLR0350_ROOT_DIR/run.id" 2>/dev/null || true)
    case "$FLR0350_RUN_ID" in
        flr[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]) return 0 ;;
        *) return 1 ;;
    esac
}

flr0350_load_identity() {
    flr0350_load_run_id || return 1
    flr0350_root_file_valid "$FLR0350_ROOT_DIR/fifo.identity" || return 1
    FLR0350_ID_EXTRA=
    IFS=' ' read -r FLR0350_ID_VERSION FLR0350_ID_RUN_ID FLR0350_ID_PID \
        FLR0350_ID_START FLR0350_ID_UID FLR0350_ID_DEV FLR0350_ID_INO \
        FLR0350_ID_EXTRA < "$FLR0350_ROOT_DIR/fifo.identity" || return 1
    [ "$FLR0350_ID_VERSION" = 1 ] &&
        [ "$FLR0350_ID_RUN_ID" = "$FLR0350_RUN_ID" ] &&
        [ -z "$FLR0350_ID_EXTRA" ] || return 1
    for value in "$FLR0350_ID_PID" "$FLR0350_ID_START" "$FLR0350_ID_UID" \
        "$FLR0350_ID_DEV" "$FLR0350_ID_INO"; do
        case "$value" in ''|*[!0-9]*) return 1 ;; esac
    done
    [ "$FLR0350_ID_PID" -gt 0 ] && [ "$FLR0350_ID_START" -gt 0 ] &&
        [ "$FLR0350_ID_INO" -gt 0 ]
}

flr0350_proc_start() {
    awk '{sub(/^.*\) /, ""); print $20}' "$FLR0350_PROC_ROOT/$1/stat" 2>/dev/null
}

flr0350_proc_state() {
    awk '{sub(/^.*\) /, ""); print $1}' "$FLR0350_PROC_ROOT/$1/stat" 2>/dev/null
}

flr0350_proc_uid() {
    awk '/^Uid:/ {print $2; exit}' "$FLR0350_PROC_ROOT/$1/status" 2>/dev/null
}

flr0350_proc_tracer() {
    awk '/^TracerPid:/ {print $2; exit}' "$FLR0350_PROC_ROOT/$1/status" 2>/dev/null
}

flr0350_object_id() {
    stat -L -c '%d:%i' "$1" 2>/dev/null
}

flr0350_identity_matches_process() {
    [ "$1" = "$FLR0350_ID_PID" ] &&
        [ "$2" = "$FLR0350_ID_START" ] &&
        [ "$3" = "$FLR0350_ID_UID" ]
}

flr0350_identity_matches_gate() {
    [ -p "$FLR0350_USER_DIR/flr0350-go.fifo" ] &&
        [ ! -L "$FLR0350_USER_DIR/flr0350-go.fifo" ] &&
        [ "$(flr0350_object_id "$FLR0350_USER_DIR/flr0350-go.fifo")" = \
            "$FLR0350_ID_DEV:$FLR0350_ID_INO" ]
}

flr0350_identity_matches_fds() {
    [ "$(flr0350_object_id "$FLR0350_PROC_ROOT/$FLR0350_ID_PID/fd/0")" = \
        "$FLR0350_ID_DEV:$FLR0350_ID_INO" ] &&
        [ "$(flr0350_object_id "$FLR0350_PROC_ROOT/$FLR0350_ID_PID/fd/3")" = \
        "$FLR0350_ID_DEV:$FLR0350_ID_INO" ]
}

flr0350_auth_record_matches() {
    flr0350_root_file_valid "$FLR0350_ROOT_DIR/attach.auth" || return 1
    FLR0350_AUTH_EXTRA=
    IFS=' ' read -r FLR0350_AUTH_VERSION FLR0350_AUTH_RUN_ID \
        FLR0350_AUTH_PID FLR0350_AUTH_START FLR0350_AUTH_UID \
        FLR0350_AUTH_DEV FLR0350_AUTH_INO FLR0350_AUTH_GDB_PID \
        FLR0350_AUTH_GDB_START FLR0350_AUTH_EXTRA \
        < "$FLR0350_ROOT_DIR/attach.auth" || return 1
    [ "$FLR0350_AUTH_VERSION" = 1 ] &&
        [ "$FLR0350_AUTH_RUN_ID" = "$FLR0350_RUN_ID" ] &&
        [ "$FLR0350_AUTH_PID" = "$FLR0350_ID_PID" ] &&
        [ "$FLR0350_AUTH_START" = "$FLR0350_ID_START" ] &&
        [ "$FLR0350_AUTH_UID" = "$FLR0350_ID_UID" ] &&
        [ "$FLR0350_AUTH_DEV" = "$FLR0350_ID_DEV" ] &&
        [ "$FLR0350_AUTH_INO" = "$FLR0350_ID_INO" ] &&
        [ "$FLR0350_AUTH_GDB_PID" = "$1" ] &&
        [ "$FLR0350_AUTH_GDB_START" = "$2" ] &&
        [ -z "$FLR0350_AUTH_EXTRA" ]
}

flr0350_go_record_matches() {
    flr0350_root_file_valid "$FLR0350_ROOT_DIR/go.record" || return 1
    FLR0350_GO_EXTRA=
    IFS=' ' read -r FLR0350_GO_VERSION FLR0350_GO_RUN_ID FLR0350_GO_PID \
        FLR0350_GO_START FLR0350_GO_UID FLR0350_GO_DEV FLR0350_GO_INO \
        FLR0350_GO_GDB_PID FLR0350_GO_GDB_START FLR0350_GO_WRITER_DEV \
        FLR0350_GO_WRITER_INO FLR0350_GO_BYTES FLR0350_GO_EXTRA \
        < "$FLR0350_ROOT_DIR/go.record" || return 1
    [ "$FLR0350_GO_VERSION" = 1 ] &&
        [ "$FLR0350_GO_RUN_ID" = "$FLR0350_RUN_ID" ] &&
        [ "$FLR0350_GO_PID" = "$FLR0350_ID_PID" ] &&
        [ "$FLR0350_GO_START" = "$FLR0350_ID_START" ] &&
        [ "$FLR0350_GO_UID" = "$FLR0350_ID_UID" ] &&
        [ "$FLR0350_GO_DEV" = "$FLR0350_ID_DEV" ] &&
        [ "$FLR0350_GO_INO" = "$FLR0350_ID_INO" ] &&
        [ "$FLR0350_GO_GDB_PID" = "$1" ] &&
        [ "$FLR0350_GO_GDB_START" = "$2" ] &&
        [ "$FLR0350_GO_WRITER_DEV" = "$FLR0350_ID_DEV" ] &&
        [ "$FLR0350_GO_WRITER_INO" = "$FLR0350_ID_INO" ] &&
        [ "$FLR0350_GO_BYTES" = 11 ] &&
        [ -z "$FLR0350_GO_EXTRA" ]
}

flr0350_write_once() {
    path=$1
    content=$2
    { [ ! -e "$path" ] && [ ! -L "$path" ]; } || return 1
    (umask 077; set -C; printf '%s\n' "$content" >"$path") 2>/dev/null || return 1
    flr0350_root_file_valid "$path"
}
