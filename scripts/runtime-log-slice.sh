#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: scripts/runtime-log-slice.sh [--max-lines N] <raw-runtime-log>

Reads the raw runtime log without modifying it. Prints a bounded summary of
the first actionable errors and native/render/present/Wayland boundary lines.
The default selected-output limit is 120 lines.
EOF
    exit 2
}

max_lines=120
log_file=
while test "$#" -gt 0; do
    case "$1" in
        --max-lines)
            test "$#" -ge 2 || usage
            max_lines=$2
            shift 2
            ;;
        --help|-h)
            usage
            ;;
        -*)
            usage
            ;;
        *)
            test "$#" -eq 1 || usage
            log_file=$1
            shift
            ;;
    esac
done

test -n "$log_file" || usage
case "$max_lines" in
    ''|*[!0-9]*) echo "runtime-log-slice: max-lines must be numeric" >&2; exit 1 ;;
esac
test "$max_lines" -gt 0 || {
    echo "runtime-log-slice: max-lines must be positive" >&2
    exit 1
}
test -r "$log_file" || {
    echo "runtime-log-slice: raw log is not readable" >&2
    exit 1
}

awk -v max_lines="$max_lines" '
BEGIN {
    error_re = "ERROR|FATAL|segfault|SIGSEGV|OOPS|coredump|std::bad|channel-error|TIMEOUT|timeout|failed|FAIL"
    marker_re = "FLUORITE_NATIVE|FLUORITE_VIEWTARGET|FLR0026_(TARGET_DRAW2|VK_(QUEUE_PRESENT|PRESENT_BOUNDARY)|COMMIT|WAYLAND)|wl_(surface|subsurface)"
    error_limit = 8
    head_limit = int(max_lines / 2)
    if (head_limit < 1) head_limit = 1
    tail_limit = max_lines - head_limit
    if (tail_limit < 1) tail_limit = 1
}
{
    total++
    if ($0 ~ error_re) {
        error_total++
        if (error_count < error_limit) errors[++error_count] = $0
    }
    if ($0 ~ marker_re) {
        selected_total++
        if ($0 ~ /FLUORITE_NATIVE/) native_total++
        if ($0 ~ /FLUORITE_VIEWTARGET/) viewtarget_total++
        if ($0 ~ /FLR0026_TARGET_DRAW2/) draw_total++
        if ($0 ~ /FLR0026_VK_(QUEUE_PRESENT|PRESENT_BOUNDARY)/) present_total++
        if ($0 ~ /FLR0026_(COMMIT|WAYLAND)|wl_(surface|subsurface)/) wayland_total++
        if (selected_total <= max_lines) selected_all[selected_total] = $0
        if (selected_total <= head_limit) head[selected_total] = $0
        tail_slot = (selected_total - 1) % tail_limit + 1
        tail[tail_slot] = $0
    }
}
END {
    printf "runtime-log-slice=PASS total_lines=%d selected=%d errors=%d shown_limit=%d\n", total, selected_total, error_total, max_lines
    printf "counts=native:%d viewtarget:%d draw:%d present:%d wayland:%d\n", native_total, viewtarget_total, draw_total, present_total, wayland_total
    printf "--- first actionable errors (max %d) ---\n", error_limit
    if (error_count == 0) print "none"
    for (i = 1; i <= error_count; i++) print errors[i]
    printf "--- selected boundary lines ---\n"
    if (selected_total == 0) {
        print "none"
    } else if (selected_total <= max_lines) {
        for (i = 1; i <= selected_total; i++) print selected_all[i]
    } else {
        for (i = 1; i <= head_limit; i++) print head[i]
        printf "... omitted=%d selected lines ...\n", selected_total - max_lines
        start = (selected_total % tail_limit) + 1
        for (i = 0; i < tail_limit; i++) {
            slot = (start + i - 1) % tail_limit + 1
            print tail[slot]
        }
    }
}
' "$log_file"
