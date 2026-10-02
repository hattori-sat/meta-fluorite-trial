#!/usr/bin/env bash
set -euo pipefail

# Bounded QEMU contract for the Fluorite runtime loop.  The caller supplies
# role paths; this script never creates a build directory, cache, or second
# QEMU instance.

usage() {
    cat <<'EOF'
Usage:
  qemu-runtime-harness.sh preflight --run-dir DIR --qmp SOCKET \
    --oe-init FILE --build-dir DIR --runqemu-bin FILE --qemuboot FILE \
    --kernel FILE --rootfs FILE \
    --kernel-sha256 HEX --rootfs-sha256 HEX \
    --serial-port PORT --ssh-port PORT --telnet-port PORT \
    [--memory-mb MB]
  qemu-runtime-harness.sh start [the same options]
  qemu-runtime-harness.sh guest-ready --ssh-port PORT [--timeout-seconds SECONDS]
  qemu-runtime-harness.sh serial-login --serial-port PORT \
    --user USER --prompt PROMPT --command-file FILE
  qemu-runtime-harness.sh serial-exec --serial-port PORT \
    --user USER --prompt PROMPT --command-file FILE --output FILE \
    [--setup-output FILE] [--timeout-seconds SECONDS]
  qemu-runtime-harness.sh summary --log FILE
  qemu-runtime-harness.sh qmp-quit --qmp SOCKET

The QEMU profile is headless and QMP-first.  Evidence belongs in the caller's
existing run directory; raw logs are not printed by summary mode.
EOF
}

fail() {
    echo "result=FAIL reason=$1" >&2
    exit 1
}

need_command() {
    command -v "$1" >/dev/null 2>&1 || fail "missing-command:$1"
}

absolute_path() {
    case "$1" in
        /*) ;;
        *) fail "path-not-absolute:$1" ;;
    esac
}

valid_port() {
    case "$1" in
        ''|*[!0-9]*) fail "invalid-port:$1" ;;
    esac
    [ "$1" -ge 1 ] && [ "$1" -le 65535 ] || fail "invalid-port:$1"
}

valid_memory_mb() {
    case "$1" in
        ''|*[!0-9]*) fail "invalid-memory-mb:$1" ;;
    esac
    [ "$1" -ge 512 ] || fail "memory-mb-too-small:$1"
}

file_sha256() {
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    elif command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        fail 'missing-command:shasum-or-sha256sum'
    fi
}

check_digest() {
    file=$1
    expected=$2
    case "$expected" in
        ''|*[!a-fA-F0-9]*) fail "invalid-sha256:$file" ;;
    esac
    [ "${#expected}" -eq 64 ] || fail "invalid-sha256:$file"
    actual=$(file_sha256 "$file")
    [ "$actual" = "$expected" ] || fail "sha256-mismatch:$file"
}

target_processes() {
    # Linux comm truncates QEMU names; runqemu is an interpreted Python script.
    # Match executable tokens, never arbitrary shell text containing a name.
    ps -axo pid=,ppid=,stat=,args= | awk '
        $3 !~ /^Z/ {
            executable=$4; sub(/^.*\//, "", executable)
            script=$5; sub(/^.*\//, "", script)
            if (executable ~ /^qemu-system-/ || executable == "runqemu" ||
                executable == "flutter-auto" ||
                (executable ~ /^python[0-9.]*$/ && script == "runqemu"))
                print $1, executable
        }
    '
}

check_port_free() {
    port=$1
    if command -v lsof >/dev/null 2>&1; then
        if lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | awk 'NR > 1 { found=1 } END { exit found ? 0 : 1 }'; then
            fail "port-in-use:$port"
        fi
    elif command -v ss >/dev/null 2>&1; then
        if ss -H -ltn "( sport = :$port )" 2>/dev/null | grep -q .; then
            fail "port-in-use:$port"
        fi
    else
        fail 'missing-command:lsof-or-ss'
    fi
}

parse_options() {
    run_dir=
    qmp=
    runqemu_bin=
    oe_init=
    build_dir=
    qemuboot=
    kernel=
    rootfs=
    kernel_sha256=
    rootfs_sha256=
    serial_port=
    ssh_port=
    telnet_port=
    memory_mb=2048
    timeout_seconds=60
    serial_user=root
    serial_prompt=
    command_file=
    output_file=
    setup_output_file=
    log_file=

    while [ "$#" -gt 0 ]; do
        case "$1" in
            --run-dir) run_dir=${2:-}; shift 2 ;;
            --qmp) qmp=${2:-}; shift 2 ;;
            --runqemu-bin) runqemu_bin=${2:-}; shift 2 ;;
            --oe-init) oe_init=${2:-}; shift 2 ;;
            --build-dir) build_dir=${2:-}; shift 2 ;;
            --qemuboot) qemuboot=${2:-}; shift 2 ;;
            --kernel) kernel=${2:-}; shift 2 ;;
            --rootfs) rootfs=${2:-}; shift 2 ;;
            --kernel-sha256) kernel_sha256=${2:-}; shift 2 ;;
            --rootfs-sha256) rootfs_sha256=${2:-}; shift 2 ;;
            --serial-port) serial_port=${2:-}; shift 2 ;;
            --ssh-port) ssh_port=${2:-}; shift 2 ;;
            --telnet-port) telnet_port=${2:-}; shift 2 ;;
            --memory-mb) memory_mb=${2:-}; shift 2 ;;
            --timeout-seconds) timeout_seconds=${2:-}; shift 2 ;;
            --user) serial_user=${2:-}; shift 2 ;;
            --prompt) serial_prompt=${2:-}; shift 2 ;;
            --command-file) command_file=${2:-}; shift 2 ;;
            --output) output_file=${2:-}; shift 2 ;;
            --setup-output) setup_output_file=${2:-}; shift 2 ;;
            --log) log_file=${2:-}; shift 2 ;;
            --help) usage; exit 0 ;;
            *) fail "unknown-option:$1" ;;
        esac
    done
}

preflight_checks() {
    absolute_path "$run_dir"
    absolute_path "$qmp"
    absolute_path "$runqemu_bin"
    absolute_path "$oe_init"
    absolute_path "$build_dir"
    absolute_path "$qemuboot"
    absolute_path "$kernel"
    absolute_path "$rootfs"
    [ -d "$run_dir" ] || fail 'existing-run-dir-required'
    case "$qmp" in
        "$run_dir"/*) ;;
        *) fail 'qmp-outside-run-dir' ;;
    esac
    [ -x "$runqemu_bin" ] || fail "runqemu-not-executable:$runqemu_bin"
    [ -r "$oe_init" ] || fail "oe-init-not-readable:$oe_init"
    [ -d "$build_dir" ] || fail "build-dir-not-found:$build_dir"
    [ -r "$qemuboot" ] || fail "qemuboot-not-readable:$qemuboot"
    [ -r "$kernel" ] || fail "kernel-not-readable:$kernel"
    [ -r "$rootfs" ] || fail "rootfs-not-readable:$rootfs"
    [ ! -e "$qmp" ] || fail "stale-qmp-socket:$qmp"
    check_digest "$kernel" "$kernel_sha256"
    check_digest "$rootfs" "$rootfs_sha256"
    valid_port "$serial_port"
    valid_port "$ssh_port"
    valid_port "$telnet_port"
    valid_memory_mb "$memory_mb"
    [ "$serial_port" != "$ssh_port" ] || fail 'duplicate-port:serial-ssh'
    [ "$serial_port" != "$telnet_port" ] || fail 'duplicate-port:serial-telnet'
    [ "$ssh_port" != "$telnet_port" ] || fail 'duplicate-port:ssh-telnet'
    target_lines=$(target_processes)
    [ -z "$target_lines" ] || fail 'residual-target-process'
    check_port_free "$serial_port"
    check_port_free "$ssh_port"
    check_port_free "$telnet_port"
    echo "preflight=PASS qmp=$qmp serial=$serial_port ssh=$ssh_port telnet=$telnet_port"
}

start_qemu() {
    preflight_checks >/dev/null
    need_command nohup
    need_command python3
    runqemu_log=$run_dir/runqemu-start.log
    runqemu_console=$run_dir/runqemu-console.log
    runqemu_command=$run_dir/runqemu-command.txt
    runqemu_pidfile=$run_dir/runqemu.pid
    # Preserve every previous attempt in this one evidence directory.
    attempt=1
    while [ -e "$run_dir/runqemu-$attempt-start.log" ]; do
        attempt=$((attempt + 1))
    done
    runqemu_log=$run_dir/runqemu-$attempt-start.log
    runqemu_console=$run_dir/runqemu-$attempt-console.log
    runqemu_boot_serial=$run_dir/runqemu-$attempt-boot-serial.log
    runqemu_command=$run_dir/runqemu-$attempt-command.txt
    : > "$runqemu_log"
    : > "$runqemu_console"
    : > "$runqemu_boot_serial"
    : > "$runqemu_command"

    # Keep the official Yocto runqemu profile.  Source the existing Yocto
    # environment so runqemu-ifup, runqemu-ifdown, and hosttools are resolved.
    # The QMP value includes the
    # unix: character-driver prefix; nographic disables SDL for headless QMP.
    # SDL_VIDEODRIVER is intentionally not used.
    qmp_arg="qmp=unix:$qmp"
    # Place the explicit memory override after the qemuboot defaults. This
    # keeps the deploy artifact immutable while allowing a bounded runtime
    # experiment to avoid guest OOM.
    serial_arg="qemuparams=-m $memory_mb -serial tcp:localhost:$serial_port,server,nowait -serial file:$runqemu_boot_serial"
    runqemu_args=("$kernel" "$rootfs" "$qemuboot" "$qmp_arg" snapshot slirp nographic "$serial_arg")
    printf '%q ' "$runqemu_bin" "${runqemu_args[@]}" > "$runqemu_command"
    printf '\n' >> "$runqemu_command"
    # QEMU hostfwd requires a numeric address, unlike its serial TCP endpoint.
    loopback=$(python3 -c 'import ipaddress, socket; a=socket.gethostbyname("localhost"); assert ipaddress.ip_address(a).is_loopback; print(a)')
    QB_SLIRP_OPT="-netdev user,id=net0,hostfwd=tcp:$loopback:$ssh_port-:22,hostfwd=tcp:$loopback:$telnet_port-:23" \
    nohup bash -c 'set -e; . "$1" "$2" >/dev/null; shift 2; exec "$@"' \
        _ "$oe_init" "$build_dir" "$runqemu_bin" "${runqemu_args[@]}" \
        > "$runqemu_console" 2> "$runqemu_log" &
    runqemu_pid=$!
    printf '%s\n' "$runqemu_pid" > "$runqemu_pidfile"

    i=0
    while [ "$i" -lt 50 ]; do
        if [ -S "$qmp" ] && qmp_ready "$qmp"; then
            echo "start=PASS pid=$runqemu_pid qmp=$qmp"
            exit 0
        fi
        if ! kill -0 "$runqemu_pid" 2>/dev/null; then
            echo 'start=FAIL reason=qemu-exited-before-qmp' >&2
            summary_log "$runqemu_log" >&2 || true
            summary_log "$runqemu_console" >&2 || true
            if [ -e "$qmp" ] && [ -z "$(target_processes)" ]; then
                unlink "$qmp" || true
            fi
            exit 1
        fi
        sleep 0.2
        i=$((i + 1))
    done
    echo 'start=FAIL reason=qmp-timeout' >&2
    summary_log "$runqemu_log" >&2 || true
    summary_log "$runqemu_console" >&2 || true
    if [ -e "$qmp" ] && [ -z "$(target_processes)" ]; then
        unlink "$qmp" || true
    fi
    exit 1
}

qmp_ready() {
    python3 - "$1" <<'PY'
import json
import socket
import sys

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(1)
try:
    sock.connect(sys.argv[1])
    data = b""
    while b"\n" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            raise RuntimeError("qmp-greeting-closed")
        data += chunk
    greeting = json.loads(data.split(b"\n", 1)[0].decode())
    if "QMP" not in greeting:
        raise RuntimeError("qmp-greeting-invalid")
except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
    raise SystemExit(1)
finally:
    sock.close()
PY
}

serial_login() {
    need_command python3
    absolute_path "$command_file"
    [ -r "$command_file" ] || fail "command-file-not-readable:$command_file"
    [ -n "$serial_user" ] || fail 'empty-serial-user'
    [ -n "$serial_prompt" ] || fail 'empty-serial-prompt'
    valid_port "$serial_port"
    command_text=$(awk 'NR == 1 { print; next } { bad=1 } END { exit bad ? 1 : 0 }' "$command_file") ||
        fail 'command-file-must-have-one-line'
    [ -n "$command_text" ] || fail 'empty-command-file'
    [ "${#command_text}" -le 4096 ] || fail 'command-file-too-large'
    python3 - "$serial_port" "$serial_user" "$serial_prompt" "$command_text" <<'PY'
import socket
import sys
import time

port, user, prompt, command = sys.argv[1:]
deadline = time.monotonic() + 30
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(1)
sock.connect(("localhost", int(port)))
sock.sendall(b"\n")
buf = b""
prompt_b = prompt.encode()
while time.monotonic() < deadline:
    try:
        chunk = sock.recv(4096)
    except socket.timeout:
        continue
    if not chunk:
        break
    buf = (buf + chunk)[-16384:]
    if prompt_b in buf:
        break
    if b"login:" in buf:
        sock.sendall((user + "\n").encode())
        break
else:
    print("serial=FAIL reason=prompt-timeout", file=sys.stderr)
    raise SystemExit(1)

deadline = time.monotonic() + 30
while prompt_b not in buf and time.monotonic() < deadline:
    try:
        chunk = sock.recv(4096)
    except socket.timeout:
        continue
    if not chunk:
        break
    buf = (buf + chunk)[-16384:]
if prompt_b not in buf:
    print("serial=FAIL reason=exact-prompt-not-reached", file=sys.stderr)
    raise SystemExit(1)
sock.sendall((command + "\n").encode())
print("serial=PASS prompt-synchronized=true")
PY
}

serial_exec() {
    need_command python3
    absolute_path "$command_file"
    absolute_path "$output_file"
    [ -n "$setup_output_file" ] || setup_output_file=$output_file.setup
    absolute_path "$setup_output_file"
    [ "$setup_output_file" != "$output_file" ] || fail 'setup-output-must-differ-from-output'
    [ -r "$command_file" ] || fail "command-file-not-readable:$command_file"
    [ -n "$serial_user" ] || fail 'empty-serial-user'
    [ -n "$serial_prompt" ] || fail 'empty-serial-prompt'
    valid_port "$serial_port"
    case "$timeout_seconds" in
        ''|*[!0-9]*) fail "invalid-timeout-seconds:$timeout_seconds" ;;
    esac
    [ "$timeout_seconds" -ge 1 ] && [ "$timeout_seconds" -le 600 ] ||
        fail "invalid-timeout-seconds:$timeout_seconds"
    command_text=$(awk 'NR == 1 { print; next } { bad=1 } END { exit bad ? 1 : 0 }' "$command_file") ||
        fail 'command-file-must-have-one-line'
    [ -n "$command_text" ] || fail 'empty-command-file'
    [ "${#command_text}" -le 4096 ] || fail 'command-file-too-large'
    exec python3 - "$serial_port" "$serial_user" "$serial_prompt" "$command_text" "$output_file" "$setup_output_file" "$timeout_seconds" <<'PY'
import re
import secrets
import socket
import sys
import time
from pathlib import Path

port, user, prompt, command, output, setup_output, timeout_seconds = sys.argv[1:]
timeout_seconds = int(timeout_seconds)
marker = "__FLR_SERIAL_COMMAND_DONE_" + secrets.token_hex(12) + "__"
if marker in command or "\n" in command or "\r" in command:
    print("serial-exec=FAIL reason=unsafe-command", file=sys.stderr)
    raise SystemExit(1)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Path(output).write_bytes(b"")
Path(setup_output).write_bytes(b"")
deadline = time.monotonic() + timeout_seconds
setup_bytes = 0
command_bytes = 0
setup_truncated = False
command_truncated = False
setup_limit = 64 * 1024
command_limit = 1024 * 1024
truncation_marker = b"\n[serial transcript truncated at configured limit]\n"

def append_bounded(path, data, current, limit, already_truncated):
    remaining = max(0, limit - current)
    if remaining:
        with Path(path).open("ab") as transcript:
            transcript.write(data[:remaining])
            transcript.flush()
    current += min(remaining, len(data))
    truncated = already_truncated or len(data) > remaining
    if truncated and not already_truncated:
        with Path(path).open("ab") as transcript:
            transcript.write(truncation_marker)
            transcript.flush()
    return current, truncated

def require_remaining(stage):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        print(f"serial-exec=FAIL reason=deadline-expired stage={stage}", file=sys.stderr)
        raise SystemExit(124)
    sock.settimeout(min(1.0, remaining))
    return remaining

require_remaining("connect")
try:
    sock.connect(("localhost", int(port)))
except socket.timeout:
    print("serial-exec=FAIL reason=deadline-expired stage=connect", file=sys.stderr)
    raise SystemExit(124)
require_remaining("initial-newline")
sock.sendall(b"\n")
buf = bytearray()
prompt_b = prompt.encode()
login_sent = False
while True:
    require_remaining("login-prompt")
    try:
        chunk = sock.recv(4096)
    except socket.timeout:
        continue
    if not chunk:
        break
    setup_bytes, setup_truncated = append_bounded(
        setup_output, chunk, setup_bytes, setup_limit, setup_truncated
    )
    buf.extend(chunk)
    if len(buf) > 65536:
        del buf[:-65536]
    require_remaining("login-response")
    if b"login:" in buf and not login_sent:
        require_remaining("login-send")
        sock.sendall((user + "\n").encode())
        login_sent = True
    if prompt_b in buf:
        break
if prompt_b not in buf:
    print("serial-exec=FAIL reason=exact-prompt-not-reached", file=sys.stderr)
    raise SystemExit(1)

# Phase 1 contains no nonce: input echo cannot forge the later probe marker.
# Its prompt is only a sequencing barrier, never readiness evidence.
setup_command = b"stty -echo; __FLR_SERIAL_STTY_RC=$?\n"
buf.clear()
require_remaining("echo-off-send")
sock.sendall(setup_command)
while True:
    require_remaining("echo-off-prompt")
    try:
        chunk = sock.recv(4096)
    except socket.timeout:
        continue
    if not chunk:
        break
    setup_bytes, setup_truncated = append_bounded(
        setup_output, chunk, setup_bytes, setup_limit, setup_truncated
    )
    buf.extend(chunk)
    if setup_truncated:
        print("serial-exec=FAIL reason=echo-off-transcript-limit-exceeded", file=sys.stderr)
        raise SystemExit(1)
    require_remaining("echo-off-prompt-response")
    if prompt_b in buf:
        break
if prompt_b not in buf:
    print("serial-exec=FAIL reason=echo-off-prompt-not-reached", file=sys.stderr)
    raise SystemExit(1)
buf.clear()

# Phase 2 proves that phase 1 ran: if tty echo is still enabled, this input
# nonce appears in the echoed command as well as in printf's output.
setup_marker = ("__FLR_SERIAL_SETUP_DONE_" + secrets.token_hex(12) + "__").encode()
probe_command = (
    "printf '\\n"
    + setup_marker.decode()
    + ":%s\\n' \"$__FLR_SERIAL_STTY_RC\"\n"
).encode()
require_remaining("echo-off-probe-send")
sock.sendall(probe_command)
status_pattern = re.compile(
    rb"(?:^|\r?\n)" + re.escape(setup_marker) + rb":([0-9]+)\r?\n"
)
status_match = None
while True:
    status_match = status_pattern.search(bytes(buf))
    if status_match is not None and prompt_b in buf[status_match.end():]:
        break
    require_remaining("echo-off-marker-and-prompt")
    try:
        chunk = sock.recv(4096)
    except socket.timeout:
        continue
    if not chunk:
        break
    setup_bytes, setup_truncated = append_bounded(
        setup_output, chunk, setup_bytes, setup_limit, setup_truncated
    )
    buf.extend(chunk)
    if setup_truncated:
        print("serial-exec=FAIL reason=echo-off-transcript-limit-exceeded", file=sys.stderr)
        raise SystemExit(1)
    require_remaining("echo-off-marker-and-prompt-response")
if status_match is None:
    print("serial-exec=FAIL reason=echo-off-marker-not-observed", file=sys.stderr)
    raise SystemExit(1)
if prompt_b not in buf[status_match.end():]:
    print("serial-exec=FAIL reason=echo-off-prompt-not-reached", file=sys.stderr)
    raise SystemExit(1)
if status_match.group(1) != b"0":
    print("serial-exec=FAIL reason=echo-off-marker-status-invalid", file=sys.stderr)
    raise SystemExit(1)
if bytes(buf).count(setup_marker) != 1:
    print("serial-exec=FAIL reason=echo-off-response-unexpected", file=sys.stderr)
    raise SystemExit(1)

setup_tail = bytes(buf[status_match.end():])
prompt_start = setup_tail.find(prompt_b)
if (
    setup_tail.count(prompt_b) != 1
    or prompt_start + len(prompt_b) != len(setup_tail)
):
    print("serial-exec=FAIL reason=echo-off-response-unexpected", file=sys.stderr)
    raise SystemExit(1)

# Catch adjacent prompt residue split across TCP reads. This bounded quiet
# check does not claim that a serial stream can never emit later bytes.
quiet_window = 0.05
remaining = require_remaining("echo-off-post-prompt-quiet")
if remaining <= quiet_window:
    print("serial-exec=FAIL reason=deadline-expired stage=echo-off-post-prompt-quiet", file=sys.stderr)
    raise SystemExit(124)
sock.settimeout(quiet_window)
try:
    trailing = sock.recv(4096)
except socket.timeout:
    trailing = None
if trailing is not None:
    if trailing:
        setup_bytes, setup_truncated = append_bounded(
            setup_output, trailing, setup_bytes, setup_limit, setup_truncated
        )
    print("serial-exec=FAIL reason=echo-off-response-unexpected", file=sys.stderr)
    raise SystemExit(1)
require_remaining("echo-off-post-prompt-quiet-complete")
buf.clear()

wrapped = (
    command
    + "; rc=$?; stty echo; printf '\\nrc=%s\\n"
    + marker
    + "\\n' \"$rc\"\n"
)
require_remaining("guest-command-send")
sock.sendall(wrapped.encode())
while marker.encode() not in buf:
    require_remaining("guest-command-output")
    try:
        chunk = sock.recv(4096)
    except socket.timeout:
        continue
    if not chunk:
        break
    buf.extend(chunk)
    if len(buf) > 65536:
        del buf[:-65536]
    command_bytes, command_truncated = append_bounded(
        output, chunk, command_bytes, command_limit, command_truncated
    )
    require_remaining("guest-command-response")
if marker.encode() not in buf:
    print("serial-exec=FAIL reason=completion-marker-not-observed", file=sys.stderr)
    raise SystemExit(1)

if command_truncated:
    print("serial-exec=FAIL reason=command-output-limit-exceeded", file=sys.stderr)
    raise SystemExit(1)
match = re.search(
    rb"rc=(\d+)\r?\n" + re.escape(marker.encode()),
    bytes(buf),
)
if match is None:
    print("serial-exec=FAIL reason=completion-status-not-observed", file=sys.stderr)
    raise SystemExit(1)
status = int(match.group(1))
if status != 0:
    print(f"serial-exec=FAIL command_status={status} output={output}", file=sys.stderr)
    raise SystemExit(1)
print(f"serial-exec=PASS command_status=0 output={output}")
PY
}

guest_ready() {
    need_command python3
    valid_port "$ssh_port"
    case "$timeout_seconds" in
        ''|*[!0-9]*) fail "invalid-timeout-seconds:$timeout_seconds" ;;
    esac
    [ "$timeout_seconds" -ge 1 ] && [ "$timeout_seconds" -le 600 ] ||
        fail "invalid-timeout-seconds:$timeout_seconds"
    python3 - "$ssh_port" "$timeout_seconds" <<'PY'
import socket
import sys
import time

port = int(sys.argv[1])
timeout = int(sys.argv[2])
deadline = time.monotonic() + timeout
attempt = 0
last_error = "connection-not-ready"
while time.monotonic() < deadline:
    attempt += 1
    try:
        with socket.create_connection(("localhost", port), timeout=2) as sock:
            sock.settimeout(2)
            banner = sock.recv(128)
            if banner.startswith(b"SSH-"):
                print(f"guest-ready=PASS ssh_port={port} attempt={attempt}")
                raise SystemExit(0)
            last_error = f"unexpected-banner:{banner[:32]!r}"
    except (OSError, socket.timeout) as exc:
        last_error = f"{type(exc).__name__}:{exc}"
    time.sleep(1)
print(f"guest-ready=FAIL ssh_port={port} timeout_seconds={timeout} last={last_error}", file=sys.stderr)
raise SystemExit(1)
PY
}

summary_log() {
    log=$1
    [ -r "$log" ] || fail "log-not-readable:$log"
    tail -n 400 "$log" | awk '
        BEGIN { count = 0 }
        /Application Id:|FRAME_BEGIN|FRAME_END|SHAPE_READY|camera applied|queue submit|end-frame|ERROR|error:|segfault|SIGSEGV|Oops|page fault|Cannot|Failed/ {
            if (count < 120) { print substr($0, 1, 400); count++ }
        }
        END { print "summary=PASS selected_lines=" count }
    '
}

qmp_quit() {
    need_command python3
    absolute_path "$qmp"
    [ -S "$qmp" ] || fail "qmp-socket-not-found:$qmp"
    python3 - "$qmp" <<'PY'
import json
import socket
import sys

path = sys.argv[1]
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect(path)
buf = b""

def receive_object():
    global buf
    while b"\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            raise RuntimeError("qmp-connection-closed")
        buf += chunk
    line, buf = buf.split(b"\n", 1)
    return json.loads(line.decode())

receive_object()
sock.sendall(b'{"execute":"qmp_capabilities"}\r\n')
cap = receive_object()
if cap.get("error"):
    raise RuntimeError("qmp-capabilities-rejected")
sock.sendall(b'{"execute":"quit"}\r\n')
quit_reply = receive_object()
if quit_reply.get("error"):
    raise RuntimeError("qmp-quit-rejected")
print("qmp=PASS capabilities=negotiated quit=accepted")
PY

    i=0
    while [ "$i" -lt 50 ]; do
        target_lines=$(target_processes)
        if [ -z "$target_lines" ]; then
            if [ -e "$qmp" ]; then
                unlink "$qmp" || fail 'stale-qmp-unlink-failed'
            fi
            [ ! -e "$qmp" ] || fail 'qmp-socket-remains'
            echo 'cleanup=PASS residual_targets=0 residual_qmp=0'
            exit 0
        fi
        sleep 0.2
        i=$((i + 1))
    done
    fail 'target-process-remains-after-qmp-quit'
}

mode=${1:-}
[ -n "$mode" ] || { usage >&2; exit 2; }
shift
parse_options "$@"

case "$mode" in
    preflight)
        preflight_checks
        ;;
    start)
        start_qemu
        ;;
    guest-ready)
        guest_ready
        ;;
    serial-login)
        serial_login
        ;;
    serial-exec)
        serial_exec
        ;;
    summary)
        summary_log "$log_file"
        ;;
    qmp-quit)
        qmp_quit
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
