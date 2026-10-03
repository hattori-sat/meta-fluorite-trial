#!/usr/bin/env python3
"""Fail-closed host controller for the single FLR-0416 QEMU observation."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path


RUN_ID = "flr0418-0001"
QMP_SOCKET_NAME = "qmp-0418.sock"
ATTEMPT_CLAIM_NAMES = {
    "start": "FLR0418-start-claim",
    "controller": "FLR0418-controller-claim",
}
ACK_COLLECTION_SECONDS = 540
SERIAL_WAIT_COMPLETION_RESERVE_SECONDS = 15
MINIMUM_MARKER_TIMEOUT_SECONDS = (
    SERIAL_WAIT_COMPLETION_RESERVE_SECONDS + 2
)
ABORT_GRACE_SECONDS = 50
GUEST_DIR = "/run/user/1001/" + RUN_ID
GUEST_ROOT = "/run/user/1001/" + RUN_ID
PROC_ROOT = "/proc"
DEMO_BUNDLE = (
    "/usr/share/flutter/toyota-connected-tcna-packages-filament-scene-"
    "fluorite-examples-demo/3.32.5/release"
)
SERIAL_USER = "root"
SERIAL_PROMPT = "root@qemux86-64:~# "
SERIAL_COMMAND_LIMIT = 4096
SERIAL_PAYLOAD_CHUNK = 3000
GUEST_FETCH_CHUNK = 32768


def parse_marker_timeout_seconds(value):
    try:
        seconds = int(value)
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError("marker timeout must be an integer") from error
    if not (MINIMUM_MARKER_TIMEOUT_SECONDS <= seconds <= ACK_COLLECTION_SECONDS):
        raise argparse.ArgumentTypeError(
            "marker timeout must be between %d and %d seconds"
            % (MINIMUM_MARKER_TIMEOUT_SECONDS, ACK_COLLECTION_SECONDS)
        )
    return seconds


REQUIRED_GUEST = {
    "load": {RUN_ID + "-armed.json", RUN_ID + "-load-ready.json"},
    "hit": {
        RUN_ID + "-armed.json",
        RUN_ID + "-hit-begin",
        RUN_ID + "-hit-record.json",
        RUN_ID + "-hit-ready.json",
    },
}
REQUIRED_MINI = {
    "load": {RUN_ID + "-load-bracket.json", RUN_ID + "-qmp-load-still.ppm"},
    "hit": {
        RUN_ID + "-hit-bracket.json",
        RUN_ID + "-qmp-hit-still.ppm",
        *(RUN_ID + "-qmp-hit-frame-%04d.ppm" % index for index in range(8)),
    },
}
IDENTITY_KEYS = ("guest_boot_id", "process", "gdb_process")


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def _process_start_token(pid):
    try:
        stat_tail = (
            Path("/proc") / str(pid) / "stat"
        ).read_text(encoding="ascii").rsplit(")", 1)[1].split()
    except (OSError, IndexError) as error:
        raise RuntimeError("claim owner process start identity is unavailable") from error
    if len(stat_tail) <= 19 or not stat_tail[19].isdigit():
        raise RuntimeError("claim owner process start identity is malformed")
    return stat_tail[19]


def create_attempt_claim(run_dir, role):
    """Create one durable, no-replace claim for this ticket's one-shot run."""
    if role not in ATTEMPT_CLAIM_NAMES:
        raise ValueError("attempt claim role is invalid")
    evidence = os.environ.get("BUILD_EVIDENCE", "")
    if not evidence or not Path(evidence).is_absolute() or not Path(evidence).is_dir():
        raise RuntimeError("BUILD_EVIDENCE role is missing or invalid")
    run_dir = Path(run_dir).resolve(strict=True)
    expected = Path(evidence).resolve(strict=True) / RUN_ID / "qemu"
    if run_dir != expected:
        raise RuntimeError("attempt claim run directory differs from the fixed evidence role")

    claim_dir = run_dir / ATTEMPT_CLAIM_NAMES[role]
    start_token = _process_start_token(os.getpid())
    claim_dir.mkdir(mode=0o700)
    owner = {
        "event": "FLR0418_ATTEMPT_CLAIM",
        "role": role,
        "run_id": RUN_ID,
        "pid": os.getpid(),
        "start_token": start_token,
        "created_wall_ns": time.time_ns(),
    }
    owner_path = claim_dir / "owner.json"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(owner_path, flags, 0o600)
    try:
        payload = canonical_json(owner).encode("utf-8")
        remaining = memoryview(payload)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("claim owner write made no progress")
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    for directory in (claim_dir, run_dir):
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    return claim_dir


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def parse_p6_ppm(data, expected_width=1280, expected_height=800):
    """Validate one complete, exact-size QMP P6 RGB framebuffer."""
    if not isinstance(data, bytes):
        raise TypeError("PPM payload must be bytes")
    whitespace = b" \t\r\n\f\v"
    position = 0

    def token():
        nonlocal position
        while position < len(data):
            if data[position] in whitespace:
                position += 1
                continue
            if data[position] == ord("#"):
                newline = data.find(b"\n", position)
                if newline < 0:
                    raise ValueError("unterminated PPM comment")
                position = newline + 1
                continue
            break
        start = position
        while position < len(data) and data[position] not in whitespace:
            position += 1
        if start == position:
            raise ValueError("incomplete PPM header")
        return data[start:position]

    try:
        magic = token()
        width = int(token())
        height = int(token())
        max_value = int(token())
    except (ValueError, OverflowError) as error:
        raise ValueError("invalid PPM header") from error
    if magic != b"P6":
        raise ValueError("QMP frame is not binary P6 PPM")
    if width != expected_width or height != expected_height:
        raise ValueError("QMP frame dimensions differ from 1280x800")
    if max_value != 255:
        raise ValueError("QMP frame max value is not 255")
    if position >= len(data) or data[position] not in whitespace:
        raise ValueError("PPM header lacks raster separator")
    if data[position : position + 2] == b"\r\n":
        position += 2
    else:
        position += 1
    expected_bytes = width * height * 3
    if len(data) - position != expected_bytes:
        raise ValueError("QMP PPM raster length is incomplete or has trailing data")
    return width, height


def final_capture_status(
    status, errors, qmp_socket_absent, *, teardown_verified=True
):
    """Make capture and teardown errors visible in the exit status."""
    if errors or not qmp_socket_absent or teardown_verified is not True:
        if status == "DIAGNOSTIC_CAPTURE_PASS":
            status = "DIAGNOSTIC_CAPTURE_INCOMPLETE"
        return status, 1
    return status, 0 if status == "DIAGNOSTIC_CAPTURE_PASS" else 1


def controller_final_record(
    result,
    *,
    qemu_identity_verified,
    qemu_process_gone,
    postflight_verified,
    qmp_quit_status,
    teardown_errors,
    qmp_socket_absent,
):
    """Record teardown independently from the diagnostic capture verdict."""
    record = dict(result)
    teardown_errors = list(teardown_errors)
    record["event"] = "FLR0416_CONTROLLER_FINAL"
    record["teardown_errors"] = teardown_errors
    record["qemu_process_gone"] = qemu_process_gone is True
    record["postflight_verified"] = postflight_verified is True
    record["qmp_quit_status"] = qmp_quit_status
    qemu_identity = record.get("qemu_host_identity")
    valid_qemu_identity = (
        isinstance(qemu_identity, dict)
        and isinstance(qemu_identity.get("pid"), int)
        and qemu_identity["pid"] > 1
        and re.fullmatch(r"[0-9]+", str(qemu_identity.get("start_token", ""))) is not None
    )
    record["teardown_verified"] = bool(
        qemu_identity_verified is True
        and valid_qemu_identity
        and qemu_process_gone is True
        and postflight_verified is True
        and qmp_quit_status in (
            "PASS",
            "ALREADY_EXITED",
            "FAILED_BUT_GONE",
            "EXITED_DURING_TEARDOWN",
        )
        and not teardown_errors
        and qmp_socket_absent is True
    )
    record["qmp_socket_absent"] = qmp_socket_absent
    return record


def qemu_identity_process_state(expected, pid_text, stat_text):
    """Return SAME, GONE, or UNKNOWN for the recorded PID/start-time pair."""
    if (
        not isinstance(expected, dict)
        or type(expected.get("pid")) is not int
        or expected["pid"] <= 1
        or re.fullmatch(r"[0-9]+", str(expected.get("start_token", ""))) is None
        or not isinstance(pid_text, str)
        or re.fullmatch(r"[0-9]+", pid_text.strip()) is None
        or int(pid_text.strip()) != expected["pid"]
    ):
        return "UNKNOWN"
    if stat_text is None:
        return "GONE"
    if not isinstance(stat_text, str):
        return "UNKNOWN"
    try:
        stat_tail = stat_text.rsplit(")", 1)[1].split()
    except IndexError:
        return "UNKNOWN"
    if len(stat_tail) <= 19 or re.fullmatch(r"[0-9]+", stat_tail[19]) is None:
        return "UNKNOWN"
    return "SAME" if stat_tail[19] == str(expected["start_token"]) else "GONE"


def diagnostic_capture_evidence_complete(
    *,
    load_ready_valid,
    load_bracket_verified,
    hit_ready_valid,
    hit_bracket_verified,
    post_bracket_verified,
    post_pixel_analysis,
    present_success_delta,
    kernel_fault_delta,
    after_continue_event,
):
    """Only call a diagnostic capture complete when every measurement exists."""
    return bool(
        load_ready_valid is True
        and load_bracket_verified is True
        and hit_ready_valid is True
        and hit_bracket_verified is True
        and post_bracket_verified is True
        and isinstance(post_pixel_analysis, dict)
        and post_pixel_analysis.get("status") == "PASS"
        and isinstance(present_success_delta, int)
        and present_success_delta > 0
        and isinstance(kernel_fault_delta, int)
        and kernel_fault_delta >= 0
        and after_continue_event == "AFTER_CONTINUE_STOP_OR_EXIT"
    )


def validate_release_acceptance(payload, stage, identity, manifest, release):
    if stage not in ("load", "hit"):
        return False
    try:
        record = json.loads(payload.decode("utf-8"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    expected = _validate_identity(identity)
    return bool(
        isinstance(record, dict)
        and record.get("event") == "GUEST_RELEASE_ACCEPTED"
        and record.get("run_id") == RUN_ID
        and record.get("stage") == stage
        and all(record.get(key) == value for key, value in expected.items())
        and record.get("manifest_sha256") == sha256_bytes(manifest)
        and record.get("release_sha256") == sha256_bytes(release)
    )


def _validate_identity(identity):
    if not isinstance(identity, dict) or not identity.get("guest_boot_id"):
        raise ValueError("identity lacks guest boot ID")
    for key in ("process", "gdb_process"):
        record = identity.get(key)
        if not isinstance(record, dict):
            raise ValueError("identity lacks " + key)
        if record.get("uid") != 1001:
            raise ValueError("identity UID mismatch")
        if not isinstance(record.get("pid"), int) or record["pid"] <= 0:
            raise ValueError("identity PID is invalid")
        if re.fullmatch(r"[0-9]+", str(record.get("start_token", ""))) is None:
            raise ValueError("identity start token is invalid")
    return {key: identity[key] for key in IDENTITY_KEYS}


def payload_chunks(payload, max_chars=SERIAL_PAYLOAD_CHUNK):
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if max_chars < 4:
        raise ValueError("base64 chunk size is too small")
    encoded = base64.b64encode(payload).decode("ascii")
    return tuple(encoded[index : index + max_chars] for index in range(0, len(encoded), max_chars)) or ("",)


def payload_shell_commands(remote_path, payload, owner="agl-driver"):
    """Stage complete bytes privately, then publish the destination atomically."""
    destination = Path(remote_path)
    allowed = destination.parent == Path(GUEST_DIR) or re.fullmatch(
        r"/run/user/1001/flr0418-0001-(?:load|hit)-(?:manifest|release|abort)\.json",
        remote_path,
    )
    if not allowed or destination.name in (".", "..") or "\n" in remote_path or "\r" in remote_path:
        raise ValueError("remote payload path is outside the FLR-0416 guest scope")
    if owner not in ("agl-driver", "root"):
        raise ValueError("unsupported guest payload owner")
    if not payload:
        raise ValueError("refusing to publish an empty guest payload")
    if destination.parent == Path(GUEST_DIR):
        temporary = str(destination.parent / (".partial-" + sha256_bytes(payload) + "-" + destination.name))
    else:
        temporary = str(Path(GUEST_DIR) / (".partial-" + sha256_bytes(payload) + "-" + destination.name))
    quoted_temporary = shlex.quote(temporary)
    quoted_destination = shlex.quote(remote_path)
    chunks = payload_chunks(payload)
    commands = []
    total = len(chunks) + 1
    for index, chunk in enumerate(chunks):
        operation = ">" if index == 0 else ">>"
        prefix = "set -eu; umask 077; "
        if index == 0:
            prefix += "set -C; "
        command = prefix + "printf '%s' " + shlex.quote(chunk) + " | base64 -d " + operation + " " + quoted_temporary
        if index + 1 == len(chunks):
            command += "; chmod 600 " + quoted_temporary
            if owner == "agl-driver":
                command += "; chown agl-driver:agl-driver " + quoted_temporary
        command += (
            "; printf 'FLR0416_PAYLOAD=PASS index=%d total=%d\\n' "
            + str(index + 1)
            + " "
            + str(total)
        )
        if len(command) > SERIAL_COMMAND_LIMIT:
            raise ValueError("serial payload command exceeds 4096 characters")
        commands.append(command)
    commit_code = (
        "import os,sys;tmp,dst=sys.argv[1:3];"
        "fd=os.open(tmp,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0));os.fsync(fd);os.close(fd);"
        "os.link(tmp,dst);os.unlink(tmp);"
        "fd=os.open(os.path.dirname(dst),os.O_RDONLY);os.fsync(fd);os.close(fd);"
        "print('FLR0416_PAYLOAD=PASS index=%d total=%d')"
        % (total, total)
    )
    commit = (
        "set -eu; python3 -c "
        + shlex.quote(commit_code)
        + " "
        + quoted_temporary
        + " "
        + quoted_destination
    )
    if len(commit) > SERIAL_COMMAND_LIMIT:
        raise ValueError("guest payload commit command exceeds serial contract")
    commands.append(commit)
    return tuple(commands)


def wait_marker_shell_command(suffix, timeout, gdb_pid, gdb_start_token):
    """Build a one-line guest wait that reports an outcome without exiting its shell."""
    path = GUEST_ROOT + "-" + suffix
    marker = "FLR0416_WAIT=" + suffix + ":"
    return (
        "set -eu; p="
        + str(gdb_pid)
        + "; expected="
        + shlex.quote(str(gdb_start_token))
        + "; proc_root="
        + shlex.quote(PROC_ROOT)
        + "; wait_for_marker() { n=0; while [ \"$n\" -lt "
        + str(timeout)
        + " ]; do if [ -s "
        + shlex.quote(GUEST_ROOT + "-observer-error")
        + " ]; then return 10; fi; if [ -s "
        + shlex.quote(path)
        + " ]; then return 0; fi; start=$(awk '{print $22}' \"$proc_root/$p/stat\" 2>/dev/null || true); if [ ! -r \"$proc_root/$p/stat\" ] || [ \"$start\" != \"$expected\" ]; then return 11; fi; sleep 1 || return 13; n=$((n+1)); done; return 12; }; if wait_for_marker; then wait_status=0; else wait_status=$?; fi; case \"$wait_status\" in 0) outcome=READY;; 10) outcome=OBSERVER_ERROR;; 11) outcome=GDB_EXITED_OR_CHANGED;; 12) outcome=TIMEOUT;; *) outcome=WAIT_COMMAND_ERROR;; esac; printf '%s%s\\n' "
        + shlex.quote(marker)
        + " \"$outcome\""
    )


def decode_guest_file(output, name):
    marker = "FLR0416_FILE=" + name + ":"
    matches = [line.strip()[len(marker) :] for line in output.splitlines() if line.strip().startswith(marker)]
    if len(matches) != 1:
        raise ValueError("guest file response must contain exactly one named payload")
    try:
        return base64.b64decode(matches[0].encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as error:
        raise ValueError("guest file response is not valid base64") from error


def decode_guest_chunk(output, offset):
    marker = "FLR0416_CHUNK=" + str(offset) + ":"
    matches = [line.strip()[len(marker) :] for line in output.splitlines() if line.strip().startswith(marker)]
    if len(matches) != 1:
        raise ValueError("guest chunk response must contain exactly one matching offset")
    try:
        return base64.b64decode(matches[0].encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as error:
        raise ValueError("guest chunk response is not valid base64") from error


def decode_guest_snapshot(output):
    marker = "FLR0416_GUEST_SNAPSHOT="
    matches = [line.strip()[len(marker) :] for line in output.splitlines() if line.strip().startswith(marker)]
    if len(matches) != 1:
        raise ValueError("guest snapshot response must contain exactly one record")
    try:
        value = json.loads(base64.b64decode(matches[0].encode("ascii"), validate=True).decode("utf-8"))
    except (UnicodeEncodeError, binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("guest snapshot response is invalid") from error
    if not isinstance(value, dict) or value.get("event") != "GUEST_RUNTIME_SNAPSHOT":
        raise ValueError("guest snapshot event is invalid")
    return value


def guest_file_size_command(path):
    if not path.startswith("/run/user/1001/flr0418-0001") or "\n" in path:
        raise ValueError("guest artifact path is outside the FLR-0416 scope")
    return "set -eu; test -f " + shlex.quote(path) + "; printf 'FLR0416_SIZE=%s\\n' \"$(wc -c < " + shlex.quote(path) + " | tr -d ' ')\""


def guest_file_chunk_command(path, offset, size=GUEST_FETCH_CHUNK):
    if not path.startswith("/run/user/1001/flr0418-0001") or "\n" in path:
        raise ValueError("guest artifact path is outside the FLR-0416 scope")
    if offset < 0 or size < 1 or size > GUEST_FETCH_CHUNK:
        raise ValueError("guest artifact chunk range is invalid")
    code = (
        "import base64,sys;f=open(sys.argv[1],'rb');f.seek(int(sys.argv[2]));"
        "d=f.read(int(sys.argv[3]));print('FLR0416_CHUNK=%s:%s'%(sys.argv[2],base64.b64encode(d).decode('ascii')))"
    )
    command = (
        "set -eu; python3 -c "
        + shlex.quote(code)
        + " "
        + shlex.quote(path)
        + " "
        + str(offset)
        + " "
        + str(size)
    )
    if len(command) > SERIAL_COMMAND_LIMIT:
        raise ValueError("guest artifact read command exceeds serial contract")
    return command


def create_once(path, payload):
    path = Path(path)
    if not isinstance(payload, bytes):
        raise TypeError("evidence payload must be bytes")
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


class CaptureController:
    """One exact QEMU/guest run; no retry, substitution, or broad process kill."""

    guest_sources = (
        "FLR-0416-gdb-smoke.gdb",
        "FLR-0416-prearm-libllvm.gdb",
        "FLR-0416-guest-gdb-smoke.cmd",
        "flr0416_gdb_observer.py",
        "flr0416_gdb_callback.py",
        "flr0416_guest_snapshot.py",
    )

    def __init__(
        self,
        run_dir,
        qmp,
        serial_port=10943,
        repo_root=None,
        post_release_seconds=8,
        marker_timeout_seconds=ACK_COLLECTION_SECONDS,
    ):
        self.repo_root = Path(repo_root or Path(__file__).resolve().parents[1]).resolve(strict=True)
        self.run_dir = Path(run_dir).resolve(strict=True)
        self.qmp = Path(qmp).resolve()
        self.serial_port = int(serial_port)
        self.post_release_seconds = int(post_release_seconds)
        self.marker_timeout_seconds = int(marker_timeout_seconds)
        if not (0 <= self.post_release_seconds <= 300):
            raise ValueError("post-release observation is outside the bounded range")
        if not (
            MINIMUM_MARKER_TIMEOUT_SECONDS
            <= self.marker_timeout_seconds
            <= ACK_COLLECTION_SECONDS
        ):
            raise ValueError("marker timeout is outside the bounded range")
        self.harness = self.repo_root / "scripts/qemu-runtime-harness.sh"
        self.pixel_capture = self.repo_root / "scripts/qemu-pixel-capture.py"
        self.start_script = self.repo_root / "work/commands/FLR-0416-qemu-start.sh"
        self.guest_root = GUEST_ROOT
        self.guest_cache = {}
        self.serial_index = 0
        self.identity = None
        self.launch_identity = None
        self.gdb_process = None
        self.status = "NOT_STARTED"
        self.errors = []
        self.teardown_warnings = []
        self.qemu_identity_verified = False
        self.qemu_identity = None
        self.qemu_process_gone = False
        self.postflight_verified = False
        self.qmp_quit_status = "NOT_ATTEMPTED"
        self._ack_deadline = None
        self._active_ack_stage = None
        self._prepared_ack_deadlines = {}
        self._abort_deadline = None

    def _prepare_ack_window(self, stage):
        if stage not in ("load", "hit"):
            raise ValueError("ACK collection stage is invalid")
        if stage == self._active_ack_stage or stage in self._prepared_ack_deadlines:
            raise RuntimeError("ACK collection deadline is already prepared")
        self._prepared_ack_deadlines[stage] = (
            time.monotonic() + self.marker_timeout_seconds
        )

    def _begin_ack_window(self, stage, *, reuse_active=False):
        if self._ack_deadline is not None:
            if reuse_active and self._active_ack_stage == stage:
                return self._ack_deadline
            raise RuntimeError("an ACK collection window is already active")
        self._active_ack_stage = stage
        self._ack_deadline = self._prepared_ack_deadlines.pop(stage, None)
        if self._ack_deadline is None:
            self._ack_deadline = time.monotonic() + self.marker_timeout_seconds
        return self._ack_deadline

    def _end_ack_window(self):
        self._ack_deadline = None
        self._active_ack_stage = None

    def _begin_abort_window(self):
        if self._abort_deadline is not None:
            raise RuntimeError("an abort publication window is already active")
        self._abort_deadline = time.monotonic() + ABORT_GRACE_SECONDS

    def _end_abort_window(self):
        self._abort_deadline = None

    def _bounded_timeout(self, requested, *, respect_deadline=True):
        timeout = float(requested)
        if timeout <= 0:
            raise ValueError("operation timeout must be positive")
        deadline = (
            self._ack_deadline
            if respect_deadline and self._ack_deadline is not None
            else self._abort_deadline
        )
        if deadline is None:
            return timeout
        remaining = deadline - time.monotonic()
        if remaining <= 0.1:
            name = "ACK collection" if deadline == self._ack_deadline else "abort publication"
            raise TimeoutError(name + " deadline expired")
        return min(timeout, remaining)

    def _save_once(self, name, payload):
        if Path(name).name != name:
            raise ValueError("evidence filename must be a basename")
        path = self.run_dir / name
        create_once(path, payload)
        return path

    def _check_layout(self):
        evidence = os.environ.get("BUILD_EVIDENCE", "")
        if not evidence or not Path(evidence).is_absolute() or not Path(evidence).is_dir():
            raise RuntimeError("BUILD_EVIDENCE role is missing or invalid")
        expected_run = Path(evidence).resolve(strict=True) / RUN_ID / "qemu"
        if self.run_dir != expected_run:
            raise RuntimeError("run directory differs from fixed BUILD_EVIDENCE role")
        if self.qmp != self.run_dir / QMP_SOCKET_NAME or not self.qmp.is_socket():
            raise RuntimeError("QMP socket is not the exact live FLR-0416 socket")
        if not (self.run_dir / "FLR0416-staged-files.sha256").is_file():
            raise RuntimeError("committed helper staging manifest is missing")
        self._verify_qemu_identity()
        self.qemu_identity_verified = True
        if not self.harness.is_file() or not self.pixel_capture.is_file():
            raise RuntimeError("committed runtime harness or QMP capture helper is missing")
        if not (1 <= self.serial_port <= 65535):
            raise RuntimeError("serial port is outside the TCP port range")
        guard = subprocess.run(
            ["bash", str(self.repo_root / "scripts/assert-canonical-repository.sh")],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=self.repo_root,
        )
        self._save_once(
            "FLR0416-canonical-guard.log",
            (guard.stdout + guard.stderr).encode("utf-8"),
        )
        if guard.returncode != 0:
            raise RuntimeError("canonical repository guard failed")

    def _verify_qemu_identity(self):
        pid_path = self.run_dir / "runqemu.pid"
        try:
            pid_text = pid_path.read_text(encoding="ascii").strip()
        except OSError as error:
            raise RuntimeError("recorded runqemu PID is unavailable") from error
        if re.fullmatch(r"[0-9]+", pid_text) is None or int(pid_text) <= 1:
            raise RuntimeError("recorded runqemu PID is malformed")
        proc = Path("/proc") / pid_text
        try:
            stat_tail = (proc / "stat").read_text(encoding="ascii").rsplit(")", 1)[1].split()
            command = (proc / "cmdline").read_bytes()
        except (OSError, IndexError) as error:
            raise RuntimeError("recorded runqemu process is no longer inspectable") from error
        if len(stat_tail) <= 19 or stat_tail[0].startswith("Z"):
            raise RuntimeError("recorded runqemu process is not live")
        if os.fsencode(str(self.qmp)) not in command or b"runqemu" not in command:
            raise RuntimeError("live PID does not match the recorded QMP run")
        current = {"pid": int(pid_text), "start_token": stat_tail[19]}
        if self.qemu_identity is None:
            self.qemu_identity = current
        elif current != self.qemu_identity:
            raise RuntimeError("recorded runqemu PID/start identity changed")
        return int(pid_text)

    def _qemu_identity_state(self):
        if not isinstance(self.qemu_identity, dict):
            return "UNKNOWN"
        pid_path = self.run_dir / "runqemu.pid"
        try:
            pid_text = pid_path.read_text(encoding="ascii")
        except OSError:
            return "UNKNOWN"
        if re.fullmatch(r"[0-9]+", pid_text.strip()) is None:
            return "UNKNOWN"
        proc_stat = Path("/proc") / str(self.qemu_identity.get("pid")) / "stat"
        try:
            stat_text = proc_stat.read_text(encoding="ascii")
        except FileNotFoundError:
            stat_text = None
        except OSError:
            return "UNKNOWN"
        return qemu_identity_process_state(self.qemu_identity, pid_text, stat_text)

    def _wait_qemu_identity_gone(self, timeout_seconds=10):
        deadline = time.monotonic() + timeout_seconds
        while True:
            state = self._qemu_identity_state()
            if state == "GONE":
                return True
            if state != "SAME":
                return False
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(0.1, remaining))

    def _serial(
        self,
        label,
        command,
        timeout_seconds=40,
        *,
        respect_deadline=True,
        minimum_guest_timeout_seconds=None,
        deadline_reserve_seconds=0,
    ):
        if "\n" in command or "\r" in command or len(command) > SERIAL_COMMAND_LIMIT:
            raise ValueError("guest command violates one-line/4096-byte serial contract")
        requested_timeout = float(timeout_seconds)
        if minimum_guest_timeout_seconds is not None:
            minimum_guest_timeout_seconds = int(minimum_guest_timeout_seconds)
            if minimum_guest_timeout_seconds < 1:
                raise ValueError("minimum guest timeout must be positive")
        deadline_reserve_seconds = int(deadline_reserve_seconds)
        if deadline_reserve_seconds < 0:
            raise ValueError("serial deadline reserve cannot be negative")
        bounded_timeout = self._bounded_timeout(
            requested_timeout + 2, respect_deadline=respect_deadline
        )
        active_deadline = (
            self._ack_deadline
            if respect_deadline and self._ack_deadline is not None
            else self._abort_deadline
        )
        if active_deadline is not None:
            remaining = active_deadline - time.monotonic()
            guest_timeout = min(int(requested_timeout), int(remaining) - 2)
            if guest_timeout < 1:
                raise TimeoutError("serial command has no guest timeout budget")
            if (
                minimum_guest_timeout_seconds is not None
                and guest_timeout < minimum_guest_timeout_seconds
            ):
                raise TimeoutError(
                    "serial timeout is shorter than guest wait marker"
                )
            outer_timeout = min(guest_timeout + 2, bounded_timeout, remaining)
            if outer_timeout - guest_timeout < 2:
                raise TimeoutError("serial command has insufficient controller grace")
            if remaining - outer_timeout < deadline_reserve_seconds:
                raise TimeoutError("serial deadline cannot preserve completion reserve")
        else:
            guest_timeout = max(1, min(600, int(requested_timeout)))
            outer_timeout = max(10, requested_timeout + 15)
        self.serial_index += 1
        safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "-", label)[:60]
        stem = "FLR0416-serial-%03d-%s" % (self.serial_index, safe_label)
        command_file = self._save_once((stem + ".cmd"), command.encode("utf-8"))
        output_file = self.run_dir / (stem + ".out")
        setup_file = self.run_dir / (stem + ".setup")
        runner_log = self.run_dir / (stem + ".runner.log")
        argv = [
            str(self.harness),
            "serial-exec",
            "--serial-port",
            str(self.serial_port),
            "--user",
            SERIAL_USER,
            "--prompt",
            SERIAL_PROMPT,
            "--command-file",
            str(command_file),
            "--output",
            str(output_file),
            "--setup-output",
            str(setup_file),
            "--timeout-seconds",
            str(max(1, min(600, guest_timeout))),
        ]
        if active_deadline is not None:
            dispatch_remaining = active_deadline - time.monotonic()
            guest_timeout = min(guest_timeout, int(dispatch_remaining) - 2)
            if guest_timeout < 1:
                raise TimeoutError("serial command has no guest timeout budget")
            if (
                minimum_guest_timeout_seconds is not None
                and guest_timeout < minimum_guest_timeout_seconds
            ):
                raise TimeoutError("serial timeout is shorter than guest wait marker")
            outer_timeout = min(
                guest_timeout + 2, bounded_timeout, dispatch_remaining
            )
            if outer_timeout - guest_timeout < 2:
                raise TimeoutError("serial command has insufficient controller grace")
            if dispatch_remaining - outer_timeout < deadline_reserve_seconds:
                raise TimeoutError(
                    "serial deadline cannot preserve completion reserve"
                )
            argv[argv.index("--timeout-seconds") + 1] = str(
                max(1, min(600, guest_timeout))
            )
        try:
            result = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
                timeout=outer_timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            self._save_once(
                runner_log.name,
                ("serial controller exception=" + type(error).__name__ + "\n").encode(),
            )
            raise RuntimeError("serial-exec did not return within its bound") from error
        self._save_once(runner_log.name, (result.stdout + result.stderr).encode("utf-8"))
        if result.returncode != 0 or "serial-exec=PASS command_status=0" not in result.stdout:
            raise RuntimeError("serial-exec failed at " + safe_label)
        if not output_file.is_file():
            raise RuntimeError("serial-exec produced no guest output at " + safe_label)
        return output_file.read_text(encoding="utf-8", errors="replace")

    def _guest_setup(self):
        stale_guest_paths = [GUEST_DIR, GUEST_ROOT + "-host.identity", GUEST_ROOT + "-log"]
        stale_guest_paths.extend(
            GUEST_ROOT + suffix
            for suffix in (
                "-armed.json",
                "-load-ready.json",
                "-load-manifest.json",
                "-load-release.json",
                "-load-abort.json",
                "-load-release-accepted.json",
                "-load-abort-accepted.json",
                "-load-release-timeout.json",
                "-hit-begin",
                "-hit-record.json",
                "-hit-ready.json",
                "-hit-manifest.json",
                "-hit-release.json",
                "-hit-abort.json",
                "-hit-release-accepted.json",
                "-hit-abort-accepted.json",
                "-hit-release-timeout.json",
                "-after-continue.json",
                "-observer-error",
                "-kernel-baseline.json",
            )
        )
        preflight = (
            "set -eu; test \"$(id -u agl-driver)\" = 1001; "
            "test -x /usr/bin/gdb; test -x /usr/bin/python3; "
            "test -x /usr/bin/timeout; test -x /usr/bin/env; "
            "test -x /usr/bin/nohup; test -x /usr/bin/flutter-auto; "
            "test -x /usr/bin/readelf; test -S /run/user/1001/wayland-0; "
            "test -d " + shlex.quote(DEMO_BUNDLE) + "; "
            "test -z \"$(pgrep -u 1001 -x flutter-auto || true)\"; "
            "test -z \"$(pgrep -u 1001 -x gdb || true)\"; "
            "for f in " + " ".join(shlex.quote(path) for path in stale_guest_paths) + "; do "
            "test ! -e \"$f\" || { echo FLR0416_GUEST_PREFLIGHT=FAIL_stale_run; exit 1; }; done; "
            "echo FLR0416_GUEST_PREFLIGHT=PASS"
        )
        output = self._serial("guest-preflight", preflight)
        if "FLR0416_GUEST_PREFLIGHT=PASS" not in output:
            raise RuntimeError("guest preflight marker missing")
        create_dir = (
            "set -eu; install -d -m 700 -o agl-driver -g agl-driver "
            + shlex.quote(GUEST_DIR)
            + "; test \"$(stat -c %u "
            + shlex.quote(GUEST_DIR)
            + ")\" = 1001; echo FLR0416_GUEST_DIR=READY"
        )
        output = self._serial("guest-run-dir", create_dir)
        if "FLR0416_GUEST_DIR=READY" not in output:
            raise RuntimeError("guest run directory creation was not verified")

        for name in self.guest_sources:
            local = self.repo_root / "work/commands" / name
            if not local.is_file() or local.is_symlink():
                raise RuntimeError("guest source is unavailable: " + name)
            content = local.read_bytes()
            digest = sha256_bytes(content)
            remote = GUEST_DIR + "/" + name
            commands = payload_shell_commands(remote, content)
            for index, command in enumerate(commands, 1):
                result = self._serial("upload-" + name + "-%03d" % index, command)
                if "FLR0416_PAYLOAD=PASS index=%d total=%d" % (index, len(commands)) not in result:
                    raise RuntimeError("guest upload chunk marker mismatch: " + name)
            verify = (
                "set -eu; actual=$(sha256sum "
                + shlex.quote(remote)
                + " | awk '{print $1}'); test \"$actual\" = "
                + digest
                + "; printf 'FLR0416_GUEST_FILE_HASH=PASS name=%s sha256=%s\\n' "
                + shlex.quote(name)
                + " \"$actual\""
            )
            result = self._serial("verify-" + name, verify)
            if "FLR0416_GUEST_FILE_HASH=PASS name=" + name + " sha256=" + digest not in result:
                raise RuntimeError("guest file hash mismatch: " + name)

        smoke_path = self.repo_root / "work/commands/FLR-0416-guest-gdb-smoke.cmd"
        smoke = self._serial("gdb-api-smoke", smoke_path.read_text(encoding="utf-8").strip(), 30)
        if "FLR0416_GDB_SMOKE=PASS app=NOT_STARTED hwbp=NOT_ATTEMPTED" not in smoke:
            raise RuntimeError("guest GDB API smoke marker missing")

        baseline_command = "/usr/bin/python3 " + shlex.quote(GUEST_DIR + "/flr0416_guest_snapshot.py") + " baseline"
        baseline_out = self._serial("kernel-baseline", baseline_command, 25)
        baseline = decode_guest_json(baseline_out, "KERNEL_BASELINE")
        self._save_once(RUN_ID + "-kernel-baseline.json", canonical_json(baseline).encode())
        self.identity = None

    def _launch_gdb(self):
        root = GUEST_ROOT
        log = root + "-log"
        gdb_file = GUEST_DIR + "/FLR-0416-prearm-libllvm.gdb"
        inner = (
            "umask 077; nohup /usr/bin/timeout --signal=TERM --kill-after=2s 1800s "
            "/usr/bin/env -i HOME=/home/agl-driver PATH=/usr/bin:/bin "
            "XDG_RUNTIME_DIR=/run/user/1001 WAYLAND_DISPLAY=wayland-0 "
            "/usr/bin/gdb -q -nx -nh -batch -x "
            + shlex.quote(gdb_file)
            + " --args /usr/bin/flutter-auto -b "
            + shlex.quote(DEMO_BUNDLE)
            + " >"
            + shlex.quote(log)
            + " 2>&1 </dev/null & echo $!"
        )
        launch = (
            "set -eu; test -z \"$(pgrep -u 1001 -x flutter-auto || true)\"; "
            "test -z \"$(pgrep -u 1001 -x gdb || true)\"; "
            "test ! -e "
            + shlex.quote(log)
            + "; wrapper=$(su -s /bin/sh agl-driver -c "
            + shlex.quote(inner)
            + "); case \"$wrapper\" in ''|*[!0-9]*) echo FLR0416_LAUNCH=FAIL_wrapper; exit 1;; esac; "
            "test \"$(cat /proc/$wrapper/comm)\" = timeout; "
            "test \"$(awk '/^Uid:/{print $2; exit}' /proc/$wrapper/status)\" = 1001; "
            "wrapper_start=$(awk '{print $22}' /proc/$wrapper/stat); gdbpid=; "
            "for n in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do "
            "gdbpid=$(pgrep -P \"$wrapper\" -x gdb || true); test -n \"$gdbpid\" && break; sleep 0.25; done; "
            "test -n \"$gdbpid\" || { echo FLR0416_LAUNCH=FAIL_gdb-child; exit 1; }; "
            "test \"$(awk '/^Uid:/{print $2; exit}' /proc/$gdbpid/status)\" = 1001; "
            "gdbstart=$(awk '{print $22}' /proc/$gdbpid/stat); "
            "printf '%s %s %s %s\\n' \"$wrapper\" \"$wrapper_start\" \"$gdbpid\" \"$gdbstart\" > "
            + shlex.quote(root + "-host.identity")
            + "; echo FLR0416_LAUNCH=PASS"
        )
        output = self._serial("launch-gdb-example-demo", launch, 30)
        if "FLR0416_LAUNCH=PASS" not in output:
            raise RuntimeError("GDB/Example Demo launch identity was not recorded")
        host_identity = self._fetch_guest(GUEST_ROOT + "-host.identity", RUN_ID + "-host.identity")
        fields = host_identity.decode("ascii").split()
        if len(fields) != 4 or any(re.fullmatch(r"[0-9]+", value) is None for value in fields):
            raise RuntimeError("GDB launcher identity record is malformed")
        self.launch_identity = {
            "wrapper": {"pid": int(fields[0]), "start_token": fields[1]},
            "gdb_process": {"pid": int(fields[2]), "uid": 1001, "start_token": fields[3]},
        }
        return output

    def _wait_marker(self, suffix, timeout_seconds=None):
        marker = "FLR0416_WAIT=" + suffix + ":"
        timeout = (
            self.marker_timeout_seconds
            if timeout_seconds is None
            else max(1, min(ACK_COLLECTION_SECONDS, int(timeout_seconds)))
        )
        active_deadline = (
            self._ack_deadline
            if self._ack_deadline is not None
            else self._abort_deadline
        )
        if active_deadline is not None:
            remaining = active_deadline - time.monotonic()
            wait_budget = (
                int(remaining)
                - SERIAL_WAIT_COMPLETION_RESERVE_SECONDS
            )
            if wait_budget < 1:
                raise TimeoutError("wait marker has no serial completion reserve")
            timeout = min(
                timeout,
                wait_budget,
            )
        gdb = self.launch_identity["gdb_process"]
        command = wait_marker_shell_command(
            suffix, timeout, gdb["pid"], gdb["start_token"]
        )
        output = self._serial(
            "wait-" + suffix,
            command,
            timeout + 10,
            minimum_guest_timeout_seconds=timeout + 2,
            deadline_reserve_seconds=2,
        )
        outcomes = [
            line.strip()[len(marker) :]
            for line in output.splitlines()
            if line.strip().startswith(marker)
        ]
        if len(outcomes) != 1:
            raise RuntimeError("guest wait marker response is missing or duplicated")
        outcome = outcomes[0]
        if outcome == "READY":
            return
        if outcome not in (
            "OBSERVER_ERROR",
            "GDB_EXITED_OR_CHANGED",
            "TIMEOUT",
            "WAIT_COMMAND_ERROR",
        ):
            raise RuntimeError("guest wait marker response has an invalid outcome")
        raise RuntimeError("guest wait ended for " + suffix + ": " + outcome)

    def _fetch_guest(self, remote_path, local_name):
        if remote_path in self.guest_cache:
            return self.guest_cache[remote_path]
        if (self.run_dir / local_name).exists():
            raise RuntimeError("refusing to overwrite existing evidence: " + local_name)
        size_output = self._serial("size-" + local_name, guest_file_size_command(remote_path), 20)
        values = [line.strip().split("=", 1)[1] for line in size_output.splitlines() if line.strip().startswith("FLR0416_SIZE=")]
        if len(values) != 1 or re.fullmatch(r"[0-9]+", values[0]) is None:
            raise RuntimeError("guest artifact size response is malformed")
        size = int(values[0])
        if size < 1 or size > 1024 * 1024:
            raise RuntimeError("guest artifact exceeds one-MiB transfer bound")
        output = bytearray()
        offset = 0
        while offset < size:
            command = guest_file_chunk_command(remote_path, offset)
            chunk_output = self._serial("chunk-" + local_name + "-%06d" % offset, command, 25)
            chunk = decode_guest_chunk(chunk_output, offset)
            expected_size = min(GUEST_FETCH_CHUNK, size - offset)
            if len(chunk) != expected_size:
                raise RuntimeError("guest artifact chunk has an unexpected size")
            output.extend(chunk)
            offset += len(chunk)
        if len(output) != size:
            raise RuntimeError("guest artifact transfer size mismatch")
        content = bytes(output)
        self._save_once(local_name, content)
        self.guest_cache[remote_path] = content
        return content

    def _guest_snapshot(self, stage, allow_exited=False):
        command = (
            "/usr/bin/python3 "
            + shlex.quote(GUEST_DIR + "/flr0416_guest_snapshot.py")
            + " snapshot --stage "
            + shlex.quote(stage)
        )
        if allow_exited:
            command += " --allow-exited"
        output = self._serial("snapshot-" + stage, command, 45)
        record = decode_guest_snapshot(output)
        if self.identity is not None and any(record.get(key) != self.identity[key] for key in IDENTITY_KEYS):
            raise RuntimeError("guest snapshot identity differs from armed GDB target")
        self._save_once(
            RUN_ID + "-guest-" + stage + "-%03d.json" % (self.serial_index),
            canonical_json(record).encode("utf-8"),
        )
        return record

    def _capture_one(self, name):
        output_path = self.run_dir / name
        log_path = self.run_dir / (name + ".capture.json")
        if output_path.exists() or log_path.exists():
            raise RuntimeError("QMP artifact already exists: " + name)
        start_wall = time.time_ns()
        start_mono = time.monotonic_ns()
        try:
            result = subprocess.run(
                [sys.executable, str(self.pixel_capture), "capture", "--socket", str(self.qmp), "--output", str(output_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=self._bounded_timeout(40),
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            detail = {"event": "QMP_CAPTURE", "name": name, "status": "FAIL", "error": type(error).__name__}
            self._save_once(log_path.name, canonical_json(detail).encode())
            raise RuntimeError("QMP capture failed: " + name) from error
        end_mono = time.monotonic_ns()
        end_wall = time.time_ns()
        if result.returncode != 0 or not output_path.is_file() or output_path.stat().st_size == 0:
            detail = {
                "event": "QMP_CAPTURE",
                "name": name,
                "status": "FAIL",
                "returncode": result.returncode,
                "stderr": result.stderr[-1000:],
            }
            self._save_once(log_path.name, canonical_json(detail).encode())
            raise RuntimeError("QMP did not create a valid full-screen frame: " + name)
        content = output_path.read_bytes()
        try:
            width, height = parse_p6_ppm(content)
        except ValueError as error:
            self._save_once(
                log_path.name,
                canonical_json(
                    {
                        "event": "QMP_CAPTURE",
                        "name": name,
                        "status": "FAIL",
                        "size": len(content),
                        "sha256": sha256_bytes(content),
                        "error": str(error),
                    }
                ).encode(),
            )
            raise RuntimeError("QMP frame failed full-screen PPM validation: " + name) from error
        record = {
            "event": "QMP_CAPTURE",
            "name": name,
            "status": "PASS",
            "format": "P6-PPM",
            "width": width,
            "height": height,
            "size": len(content),
            "sha256": sha256_bytes(content),
            "host_wall_ns": [start_wall, end_wall],
            "host_monotonic_ns": [start_mono, end_mono],
        }
        self._save_once(log_path.name, canonical_json(record).encode())
        return content, record

    def _capture_sequence(self, stage, frame_count):
        names = []
        still_name = RUN_ID + "-qmp-" + stage + "-still.ppm"
        content, metadata = self._capture_one(still_name)
        files = {still_name: content}
        names.append(metadata)
        for index in range(frame_count):
            if index:
                time.sleep(0.25)
            name = RUN_ID + "-qmp-" + stage + "-frame-%04d.ppm" % index
            content, metadata = self._capture_one(name)
            files[name] = content
            names.append(metadata)
        video_status = "PENDING_MAC_PREVIEW" if frame_count >= 2 else "NOT_REQUESTED"
        report = {
            "event": "QMP_CAPTURE_SET",
            "run_id": RUN_ID,
            "stage": stage,
            "still_and_frames": names,
            "video_status": video_status,
            "video_preview": {
                "status": video_status,
                "transcode_host": "Mac",
                "nominal_playback_fps": 4,
                "requested_inter_frame_sleep_ms": 250,
                "real_time_video": False,
            } if frame_count >= 2 else None,
        }
        report_name = RUN_ID + "-qmp-" + stage + "-capture.json"
        report_payload = canonical_json(report).encode("utf-8")
        self._save_once(report_name, report_payload)
        files[report_name] = report_payload
        return files

    def _capture_stage(self, stage, frame_count):
        before = None
        after = None
        before_error = None
        after_error = None
        files = {}
        try:
            before = self._guest_snapshot(stage, allow_exited=(stage == "post"))
        except Exception as error:
            before_error = type(error).__name__ + ":" + str(error)
        host_mono_start = time.monotonic_ns()
        host_wall_start = time.time_ns()
        try:
            files = self._capture_sequence(stage, frame_count)
        except Exception as error:
            self.errors.append("QMP-" + stage + ":" + type(error).__name__ + ":" + str(error))
        host_mono_end = time.monotonic_ns()
        host_wall_end = time.time_ns()
        try:
            after = self._guest_snapshot(stage, allow_exited=(stage == "post"))
        except Exception as error:
            after_error = type(error).__name__ + ":" + str(error)

        hashes = {name: sha256_bytes(data) for name, data in files.items()}
        if before is not None and after is not None:
            try:
                bracket = build_bracket(
                    stage,
                    self.identity,
                    before,
                    after,
                    host_mono_start,
                    host_mono_end,
                    hashes,
                    host_wall_start,
                    host_wall_end,
                )
                verified = True
            except Exception as error:
                verified = False
                bracket = self._unverified_bracket(
                    stage, host_mono_start, host_mono_end, host_wall_start, host_wall_end,
                    before, after, hashes, "bracket-validation:" + type(error).__name__
                )
        else:
            verified = False
            reason = ";".join(item for item in (before_error, after_error) if item) or "guest-snapshot-unavailable"
            bracket = self._unverified_bracket(
                stage, host_mono_start, host_mono_end, host_wall_start, host_wall_end,
                before, after, hashes, reason
            )
        bracket_name = RUN_ID + "-" + stage + "-bracket.json"
        bracket_path = self.run_dir / bracket_name
        self._save_once(bracket_name, bracket)
        files[bracket_name] = bracket
        return files, verified, before, after

    def _unverified_bracket(self, stage, mono_start, mono_end, wall_start, wall_end, before, after, hashes, reason):
        return canonical_json(
            {
                "event": "QMP_CAPTURE_BRACKET",
                "run_id": RUN_ID,
                "stage": stage,
                **self.identity,
                "host_request_monotonic_ns": [mono_start, mono_end],
                "host_request_wall_ns": [wall_start, wall_end],
                "guest_before": before if before is not None else "UNKNOWN",
                "guest_after": after if after is not None else "UNKNOWN",
                "clock_origins_comparable": False,
                "capture_sha256": hashes,
                "verified": False,
                "error": reason,
            }
        ).encode("utf-8")

    def _snapshot_stage_files(self, stage):
        names = sorted(REQUIRED_GUEST[stage])
        if stage == "hit":
            names.append(RUN_ID + "-load-ready.json")
        result = {}
        for name in names:
            remote_path = "/run/user/1001/" + name
            if remote_path in self.guest_cache:
                result[name] = self.guest_cache[remote_path]
            else:
                result[name] = self._fetch_guest(remote_path, name)
        return result

    def _publish_release(self, stage, manifest):
        if not isinstance(manifest, bytes) or not manifest:
            raise TypeError("release manifest must be the exact saved bytes")
        manifest_name = RUN_ID + "-" + stage + "-manifest.json"
        manifest_path = self.run_dir / manifest_name
        if not manifest_path.is_file() or manifest_path.read_bytes() != manifest:
            raise RuntimeError("release manifest differs from the saved evidence")
        release = build_release(stage, self.identity, manifest)
        release_name = RUN_ID + "-" + stage + "-release.json"
        self._save_once(release_name, release)
        remote_manifest = GUEST_ROOT + "-" + stage + "-manifest.json"
        remote_release = GUEST_ROOT + "-" + stage + "-release.json"
        for label, remote, payload in (
            (stage + "-manifest", remote_manifest, manifest),
            (stage + "-release", remote_release, release),
        ):
            commands = payload_shell_commands(remote, payload)
            for index, command in enumerate(commands, 1):
                output = self._serial("publish-" + label + "-%03d" % index, command, 25)
                if "FLR0416_PAYLOAD=PASS index=%d total=%d" % (index, len(commands)) not in output:
                    raise RuntimeError("guest release payload marker mismatch")
        return release

    def _wait_release_acceptance(self, stage, manifest, release):
        suffix = stage + "-release-accepted.json"
        self._wait_marker(suffix, 30)
        payload = self._fetch_guest(
            GUEST_ROOT + "-" + suffix,
            RUN_ID + "-" + suffix,
        )
        if not validate_release_acceptance(
            payload, stage, self.identity, manifest, release
        ):
            raise RuntimeError("guest did not accept this exact release manifest")
        return json.loads(payload.decode("utf-8"))

    def _publish_abort(self, stage, reason):
        owns_window = self._abort_deadline is None
        if owns_window:
            self._begin_abort_window()
        try:
            payload = build_abort(stage, self.identity, reason)
            name = RUN_ID + "-" + stage + "-abort.json"
            self._save_once(name, payload)
            remote = GUEST_ROOT + "-" + stage + "-abort.json"
            commands = payload_shell_commands(remote, payload)
            for index, command in enumerate(commands, 1):
                output = self._serial(
                    "publish-abort-" + stage + "-%03d" % index,
                    command,
                    25,
                    respect_deadline=False,
                )
                if "FLR0416_PAYLOAD=PASS index=%d total=%d" % (index, len(commands)) not in output:
                    raise RuntimeError("guest abort payload marker mismatch")
        finally:
            if owns_window:
                self._end_abort_window()

    def _abort_stage_failure(self, stage, result):
        # Stop the expired collection budget before spending the guest's
        # separate, shorter grace period on an identity-bound abort.
        self._end_ack_window()
        self._prepared_ack_deadlines.clear()
        self._begin_abort_window()
        abort_record = result.setdefault("stages", {}).setdefault(
            stage + "_failure_abort",
            {"publication": "NOT_STARTED", "guest_acceptance": "UNKNOWN"},
        )
        try:
            if self.identity is None and stage == "load" and self.launch_identity is not None:
                try:
                    self._load_identity()
                except Exception as error:
                    self.errors.append(
                        "load-abort-identity-unavailable:" + type(error).__name__
                    )
            if self.identity is None:
                abort_record["publication"] = "SKIPPED_IDENTITY_UNKNOWN"
                self.errors.append(stage + "-abort=SKIPPED_identity_unknown")
                return
            try:
                abort_record["publication"] = "IN_PROGRESS"
                self._publish_abort(stage, "controller_stage_error")
                abort_record["publication"] = "PUBLISHED"
            except Exception as error:
                abort_record["publication"] = "UNKNOWN"
                self.errors.append(stage + "-abort=FAIL_" + type(error).__name__)
        finally:
            self._end_abort_window()

    def _load_identity(self):
        armed = self._fetch_guest(GUEST_ROOT + "-armed.json", RUN_ID + "-armed.json")
        identity = _artifact_identity(armed, "armed")
        self.identity = _validate_identity(identity)
        if self.identity["gdb_process"] != self.launch_identity["gdb_process"]:
            raise RuntimeError("GDB process changed between launcher and load stop")
        return armed

    def _preserve_bounded_log(self):
        if self.launch_identity is None:
            return
        name = RUN_ID + "-gdb.log"
        if (self.run_dir / name).exists():
            return
        try:
            self._fetch_guest(GUEST_ROOT + "-log", name)
        except Exception:
            selected = (
                "set -eu; log=" + shlex.quote(GUEST_ROOT + "-log") + "; test -r \"$log\"; "
                "grep -E 'FLR0416_|Program received signal|Hardware assisted breakpoint|Cannot insert|Oops:|BUG:|FEngine::loop|present.*(begin|return|success)' \"$log\" | tail -n 240 || true"
            )
            try:
                excerpt = self._serial("selected-gdb-log", selected, 20)
                self._save_once(RUN_ID + "-gdb-selected.log", excerpt.encode("utf-8"))
            except Exception as error:
                self.errors.append("gdb-log-unavailable:" + type(error).__name__)

    def _interrupt_and_wait(self):
        after_path = GUEST_ROOT + "-after-continue.json"
        existing = self._serial(
            "after-continue-exists",
            "if [ -s " + shlex.quote(after_path) + " ]; then echo FLR0416_AFTER_CONTINUE=READY; else echo FLR0416_AFTER_CONTINUE=WAIT; fi",
            15,
        )
        if "FLR0416_AFTER_CONTINUE=READY" not in existing:
            output = self._serial(
                "interrupt-gdb",
                interrupt_gdb_command(
                    self.identity["gdb_process"],
                    self.identity["process"],
                    expected_gdb=self.launch_identity["gdb_process"],
                ),
                20,
            )
            if "FLR0416_GDB_INTERRUPT=REQUESTED" not in output:
                raise RuntimeError("exact GDB interrupt was not acknowledged")
            self._wait_marker("after-continue.json", 20)
        content = self._fetch_guest(after_path, RUN_ID + "-after-continue.json")
        try:
            record = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError("GDB after-continue record is invalid") from error
        if record.get("event") != "AFTER_CONTINUE_STOP_OR_EXIT":
            raise RuntimeError("GDB did not write the after-continue boundary")
        target = record.get("expected_target")
        if not isinstance(target, dict) or any(
            target.get(key) != self.identity[key] for key in IDENTITY_KEYS
        ):
            raise RuntimeError("after-continue record target identity mismatch")
        if record.get("guest_boot_id") != self.identity["guest_boot_id"]:
            raise RuntimeError("after-continue record guest boot ID mismatch")
        if not isinstance(record.get("gdb_observation"), dict) or record["gdb_observation"].get("matches") is not True:
            raise RuntimeError("after-continue GDB identity is not verified")
        process = record.get("process_observation")
        if not isinstance(process, dict) or not (
            process.get("matches") is True or process.get("state") in ("EXITED", "DEAD")
        ):
            raise RuntimeError("after-continue inferior liveness is not verified")
        if record.get("stop_classification") not in (
            "inferior_live_all_threads_stopped",
            "inferior_exited",
        ):
            raise RuntimeError("after-continue stop/exit state is ambiguous")
        return record

    def _analyze_post_frames(self, mini_files):
        first = RUN_ID + "-qmp-post-frame-0000.ppm"
        last = RUN_ID + "-qmp-post-frame-0007.ppm"
        if first not in mini_files or last not in mini_files:
            return {"status": "UNKNOWN", "reason": "required-frame-missing"}
        command = [
            sys.executable,
            str(self.pixel_capture),
            "analyze",
            "--input",
            str(self.run_dir / last),
            "--region",
            "full",
            "--reference",
            str(self.run_dir / first),
        ]
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=45)
        name = RUN_ID + "-qmp-post-pixel-diff.json"
        if result.returncode != 0:
            self._save_once(name, canonical_json({"status": "FAIL", "stderr": result.stderr[-1000:]}).encode())
            return {"status": "FAIL", "reason": "pixel-analysis-failed"}
        payload = result.stdout.encode("utf-8")
        self._save_once(name, payload)
        try:
            record = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "UNKNOWN", "reason": "pixel-analysis-json-invalid"}
        if not isinstance(record, dict):
            return {"status": "UNKNOWN", "reason": "pixel-analysis-record-invalid"}
        changed_pixels = record.get("changed_pixels")
        changed_ratio = record.get("changed_ratio")
        if (
            record.get("width") != 1280
            or record.get("height") != 800
            or record.get("comparison") != "reference"
            or not isinstance(changed_pixels, int)
            or isinstance(changed_pixels, bool)
            or not 0 <= changed_pixels <= 1280 * 800
            or not isinstance(changed_ratio, (float, int))
            or isinstance(changed_ratio, bool)
            or not 0.0 <= changed_ratio <= 1.0
            or abs(changed_ratio - changed_pixels / (1280 * 800)) > 1e-12
            or record.get("ppm_sha256") != sha256_bytes((self.run_dir / last).read_bytes())
        ):
            return {"status": "UNKNOWN", "reason": "pixel-analysis-fields-invalid"}
        return {
            "status": "PASS",
            "changed_pixels": changed_pixels,
            "changed_ratio": changed_ratio,
            "reference_frame_sha256": sha256_bytes((self.run_dir / first).read_bytes()),
            "sample_frame_sha256": record["ppm_sha256"],
        }

    def _record_result(self, data):
        payload = canonical_json(data).encode("utf-8")
        path = self.run_dir / "FLR0416-controller-result.json"
        if path.exists():
            # A prior controller run consumed this run ID; never replace its outcome.
            raise RuntimeError("controller result already exists; run ID is consumed")
        self._save_once(path.name, payload)

    def _qmp_quit_and_postflight(self):
        qmp_path_present = self.qmp.exists() or self.qmp.is_symlink()
        if qmp_path_present and not self.qmp.is_socket():
            self.qmp_quit_status = "INVALID_SOCKET_PATH"
            self.errors.append("qmp-quit=SKIPPED_path-not-socket")
        elif not qmp_path_present:
            state = self._qemu_identity_state()
            if state == "GONE":
                self.qmp_quit_status = "ALREADY_EXITED"
            else:
                self.qmp_quit_status = "SKIPPED_SOCKET_ABSENT_" + state
                self.teardown_warnings.append("qmp-quit=SKIPPED_socket-absent-state=" + state)
        else:
            try:
                self._verify_qemu_identity()
            except Exception as error:
                if self._qemu_identity_state() == "GONE":
                    self.qmp_quit_status = "ALREADY_EXITED"
                    self.teardown_warnings.append(
                        "qmp-quit=identity-was-gone:" + type(error).__name__
                    )
                else:
                    self.qmp_quit_status = "IDENTITY_UNVERIFIED"
                    self.errors.append(
                        "qmp-quit=SKIPPED_identity-unverified:" + type(error).__name__
                    )
            else:
                result = subprocess.run(
                    [str(self.harness), "qmp-quit", "--qmp", str(self.qmp)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=40,
                )
                self._save_once(
                    "FLR0416-qmp-quit.log",
                    (result.stdout + result.stderr).encode("utf-8"),
                )
                self.qmp_quit_status = "PASS" if result.returncode == 0 else "FAILED"
        self.qemu_process_gone = self._wait_qemu_identity_gone()
        if not self.qemu_process_gone:
            self.errors.append("qemu-process-identity-remains-or-unknown")
        elif self.qmp_quit_status == "FAILED":
            self.qmp_quit_status = "FAILED_BUT_GONE"
            self.teardown_warnings.append("qmp-quit=FAIL_but-exact-process-identity-gone")
        elif self.qmp_quit_status.startswith("SKIPPED_SOCKET_ABSENT_"):
            self.qmp_quit_status = "EXITED_DURING_TEARDOWN"
        if self.qmp.exists() or self.qmp.is_symlink():
            self.errors.append("qmp-socket-remains")
        result = subprocess.run(
            ["bash", str(self.start_script), "postflight"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self._save_once(
            "FLR0416-postflight.log",
            (result.stdout + result.stderr).encode("utf-8"),
        )
        expected_marker = "FLR0416_POSTFLIGHT=PASS image=FLR-0410-0001 qmp=absent target_owners=0 ports=free"
        self.postflight_verified = (
            result.returncode == 0 and expected_marker in result.stdout.splitlines()
        )
        if not self.postflight_verified:
            self.errors.append("postflight=FAIL rc=" + str(result.returncode))

    def _run_load_stage(self, result):
        self._begin_ack_window("load", reuse_active=True)
        abort_attempted = False
        release_acknowledged = False
        try:
            self._wait_marker("load-ready.json")
            armed = self._load_identity()
            load_ready = self._fetch_guest(
                GUEST_ROOT + "-load-ready.json", RUN_ID + "-load-ready.json"
            )
            ready_valid = validate_stage_ready("load", load_ready, self.identity)
            result["stages"]["load_ready"] = {
                "identity": self.identity,
                "ready_valid": ready_valid,
            }
            load_mini, load_bracket_ok, _, _ = self._capture_stage("load", 0)
            load_guest = {
                RUN_ID + "-armed.json": armed,
                RUN_ID + "-load-ready.json": load_ready,
            }
            load_manifest = build_manifest("load", self.identity, load_guest, load_mini)
            self._save_once(RUN_ID + "-load-manifest.json", load_manifest)
            if not ready_valid or not load_bracket_ok:
                result["stages"]["load"] = {
                    "bracket_verified": load_bracket_ok,
                    "ready_valid": ready_valid,
                    "abort_publication": "IN_PROGRESS",
                    "abort_guest_acceptance": "UNKNOWN",
                }
                abort_attempted = True
                self._publish_abort("load", "load_boundary_or_QMP_bracket_unverified")
                result["status"] = "LOAD_STAGE_ABORT_REQUESTED"
                result["stages"]["load"]["abort_publication"] = "PUBLISHED"
                return False

            self._prepare_ack_window("hit")
            result["stages"]["load"] = {
                "bracket_verified": True,
                "manifest_sha256": sha256_bytes(load_manifest),
                "release_publication": "IN_PROGRESS",
                "guest_release_acceptance": "UNKNOWN",
                "inferior_held_after_error": "UNKNOWN_IF_RELEASE_PUBLISHED",
            }
            load_release = self._publish_release("load", load_manifest)
            result["stages"]["load"]["release_publication"] = "PUBLISHED"
            load_acceptance = self._wait_release_acceptance(
                "load", load_manifest, load_release
            )
            release_acknowledged = True
            result["stages"]["load"]["guest_release_acceptance"] = "ACCEPTED"
            result["stages"]["load"]["guest_acceptance_sha256"] = sha256_bytes(
                canonical_json(load_acceptance).encode("utf-8")
            )
            return True
        except Exception:
            stage_record = result["stages"].get("load")
            if isinstance(stage_record, dict):
                if stage_record.get("release_publication") == "IN_PROGRESS":
                    stage_record["release_publication"] = "UNKNOWN"
                if stage_record.get("abort_publication") == "IN_PROGRESS":
                    stage_record["abort_publication"] = "UNKNOWN"
                if not release_acknowledged:
                    stage_record["guest_release_acceptance"] = "UNKNOWN"
            if not abort_attempted and not release_acknowledged:
                self._abort_stage_failure("load", result)
            raise
        finally:
            self._end_ack_window()

    def _run_hit_stage(self, result):
        self._begin_ack_window("hit")
        abort_attempted = False
        release_acknowledged = False
        try:
            self._wait_marker("hit-ready.json")
            hit_files = self._snapshot_stage_files("hit")
            hit_ready = hit_files[RUN_ID + "-hit-ready.json"]
            hit_valid = validate_stage_ready("hit", hit_ready, self.identity)
            hit_mini, hit_bracket_ok, _, _ = self._capture_stage("hit", 8)
            hit_manifest = build_manifest("hit", self.identity, hit_files, hit_mini)
            self._save_once(RUN_ID + "-hit-manifest.json", hit_manifest)
            result["stages"]["hit"] = {
                "ready_valid": hit_valid,
                "bracket_verified": hit_bracket_ok,
                "manifest_sha256": sha256_bytes(hit_manifest),
            }
            if not hit_valid or not hit_bracket_ok:
                result["stages"]["hit"]["abort_publication"] = "IN_PROGRESS"
                result["stages"]["hit"]["abort_guest_acceptance"] = "UNKNOWN"
                abort_attempted = True
                self._publish_abort("hit", "first_hit_evidence_or_QMP_bracket_unverified")
                result["status"] = "HIT_STAGE_ABORT_REQUESTED"
                result["stages"]["hit"]["abort_publication"] = "PUBLISHED"
                return False

            result["stages"]["hit"]["release_publication"] = "IN_PROGRESS"
            result["stages"]["hit"]["guest_release_acceptance"] = "UNKNOWN"
            result["stages"]["hit"]["inferior_held_after_error"] = (
                "UNKNOWN_IF_RELEASE_PUBLISHED"
            )
            hit_release = self._publish_release("hit", hit_manifest)
            result["stages"]["hit"]["release_publication"] = "PUBLISHED"
            hit_acceptance = self._wait_release_acceptance(
                "hit", hit_manifest, hit_release
            )
            release_acknowledged = True
            result["stages"]["hit"]["guest_release_acceptance"] = "ACCEPTED"
            result["stages"]["hit"]["release_acknowledged"] = True
            result["stages"]["hit"]["guest_acceptance_sha256"] = sha256_bytes(
                canonical_json(hit_acceptance).encode("utf-8")
            )
            return True
        except Exception:
            stage_record = result["stages"].get("hit")
            if isinstance(stage_record, dict):
                if stage_record.get("release_publication") == "IN_PROGRESS":
                    stage_record["release_publication"] = "UNKNOWN"
                if stage_record.get("abort_publication") == "IN_PROGRESS":
                    stage_record["abort_publication"] = "UNKNOWN"
                if not release_acknowledged:
                    stage_record["guest_release_acceptance"] = "UNKNOWN"
            if not abort_attempted and not release_acknowledged:
                self._abort_stage_failure("hit", result)
            raise
        finally:
            self._end_ack_window()

    def run(self):
        try:
            create_attempt_claim(self.run_dir, "controller")
        except Exception as error:
            reason = "already-claimed" if isinstance(error, FileExistsError) else type(error).__name__
            print("FLR0418_CONTROLLER_CLAIM=FAIL reason=" + reason, file=sys.stderr)
            return 1

        result = {
            "run_id": RUN_ID,
            "image": "FLR-0410-0001",
            "status": "RUNNING",
            "product_acceptance": "NOT_CLAIMED",
            "qemu_build": "NOT_RUN",
            "qemu_host_identity": "UNKNOWN",
            "stages": {},
            "errors": self.errors,
        }
        exit_code = 1
        try:
            self._check_layout()
            result["qemu_host_identity"] = self.qemu_identity
            self._record_result({**result, "status": "CONTROLLER_STARTED"})
            # Prelaunch QMP is a system-health frame, never a product verdict.
            self._guest_setup()
            prelaunch, prelaunch_meta = self._capture_one(RUN_ID + "-qmp-pre-launch-still.ppm")
            result["stages"]["pre_launch"] = {"qmp_sha256": prelaunch_meta["sha256"], "classification": "SYSTEM_FRAME_ONLY"}

            self._begin_ack_window("load")
            self._launch_gdb()
            if self._run_load_stage(result) and self._run_hit_stage(result):
                release_base = self._guest_snapshot("post", allow_exited=True)
                self._save_once(
                    RUN_ID + "-post-release-start.json",
                    canonical_json(release_base).encode("utf-8"),
                )
                time.sleep(self.post_release_seconds)
                post_mini, post_bracket_ok, _, post_after = self._capture_stage("post", 8)
                after_continue = self._interrupt_and_wait()
                self._preserve_bounded_log()

                release_present = release_base.get("present", {})
                final_present = (post_after or {}).get("present", {})
                post_pixel_change = self._analyze_post_frames(post_mini)
                result["stages"]["post_release"] = {
                    "bracket_verified": post_bracket_ok,
                    "present_success_at_release": release_present.get("success"),
                    "present_success_after_window": final_present.get("success"),
                    "present_success_delta": (
                        final_present.get("success", 0) - release_present.get("success", 0)
                        if isinstance(final_present.get("success"), int) and isinstance(release_present.get("success"), int)
                        else None
                    ),
                    "kernel_fault_delta": (post_after or {}).get("kernel", {}).get("delta"),
                    "after_continue_event": after_continue.get("event"),
                    "pixel_change": post_pixel_change,
                }
                if not diagnostic_capture_evidence_complete(
                    load_ready_valid=result["stages"]["load_ready"]["ready_valid"],
                    load_bracket_verified=result["stages"]["load"]["bracket_verified"],
                    hit_ready_valid=result["stages"]["hit"]["ready_valid"],
                    hit_bracket_verified=result["stages"]["hit"]["bracket_verified"],
                    post_bracket_verified=post_bracket_ok,
                    post_pixel_analysis=post_pixel_change,
                    present_success_delta=result["stages"]["post_release"]["present_success_delta"],
                    kernel_fault_delta=result["stages"]["post_release"]["kernel_fault_delta"],
                    after_continue_event=after_continue.get("event"),
                ):
                    raise RuntimeError("diagnostic capture lacks complete post-release evidence")
                result["status"] = "DIAGNOSTIC_CAPTURE_PASS"
                exit_code = 0
        except (Exception, KeyboardInterrupt) as error:
            result["status"] = "DIAGNOSTIC_CAPTURE_FAIL"
            result["error"] = type(error).__name__ + ":" + str(error)
            self.errors.append(result["error"])
            try:
                if self.launch_identity is not None:
                    self._preserve_bounded_log()
            except Exception as preserve_error:
                self.errors.append("evidence-preservation=" + type(preserve_error).__name__)
        finally:
            self._end_ack_window()
            self._prepared_ack_deadlines.clear()
            if self.qemu_identity_verified and isinstance(self.qemu_identity, dict):
                result["qemu_host_identity"] = dict(self.qemu_identity)
            teardown_error_start = len(self.errors)
            if self.qemu_identity_verified:
                try:
                    self._qmp_quit_and_postflight()
                except Exception as teardown_error:
                    self.errors.append("teardown=" + type(teardown_error).__name__ + ":" + str(teardown_error))
            else:
                self.errors.append("qmp-quit=SKIPPED_identity-unverified")
            result["errors"] = list(self.errors)
            result["qmp_socket_absent"] = not self.qmp.exists() and not self.qmp.is_symlink()
            result["teardown_warnings"] = list(self.teardown_warnings)
            result["product_acceptance"] = "NOT_CLAIMED"
            result["completed_host_wall_ns"] = time.time_ns()
            final_result = controller_final_record(
                result,
                qemu_identity_verified=self.qemu_identity_verified,
                qemu_process_gone=self.qemu_process_gone,
                postflight_verified=self.postflight_verified,
                qmp_quit_status=self.qmp_quit_status,
                teardown_errors=self.errors[teardown_error_start:],
                qmp_socket_absent=result["qmp_socket_absent"],
            )
            result["status"], cleanup_status = final_capture_status(
                result["status"],
                result["errors"],
                result["qmp_socket_absent"],
                teardown_verified=final_result["teardown_verified"],
            )
            if cleanup_status != 0:
                exit_code = 1
            final_result = controller_final_record(
                result,
                qemu_identity_verified=self.qemu_identity_verified,
                qemu_process_gone=self.qemu_process_gone,
                postflight_verified=self.postflight_verified,
                qmp_quit_status=self.qmp_quit_status,
                teardown_errors=self.errors[teardown_error_start:],
                qmp_socket_absent=result["qmp_socket_absent"],
            )
            final_path = self.run_dir / "FLR0416-controller-final.json"
            try:
                self._save_once(final_path.name, canonical_json(final_result).encode("utf-8"))
            except Exception as error:
                self.errors.append("final-result-write=" + type(error).__name__)
                exit_code = 1
        return exit_code


def decode_guest_json(output, expected_event):
    marker = "FLR0416_GUEST_SNAPSHOT="
    matches = [line.strip()[len(marker) :] for line in output.splitlines() if line.strip().startswith(marker)]
    if len(matches) != 1:
        raise ValueError("guest JSON response must contain exactly one record")
    try:
        record = json.loads(base64.b64decode(matches[0].encode("ascii"), validate=True).decode("utf-8"))
    except (UnicodeEncodeError, binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("guest JSON response is invalid") from error
    if not isinstance(record, dict) or record.get("event") != expected_event:
        raise ValueError("guest JSON event mismatch")
    return record


def guest_file_command(path, name):
    if not name or re.fullmatch(r"[A-Za-z0-9_.-]+", name) is None:
        raise ValueError("guest artifact name is invalid")
    if not path.startswith("/run/user/1001/flr0418-0001") or "\n" in path:
        raise ValueError("guest artifact path is outside the FLR-0416 scope")
    quoted = shlex.quote(path)
    return (
        "set -eu; test -f "
        + quoted
        + "; printf 'FLR0416_FILE="
        + name
        + ":'; base64 -w0 "
        + quoted
        + "; printf '\\n'"
    )


def _artifact_identity(payload, stage):
    try:
        record = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("guest identity artifact is not JSON") from error
    if stage == "armed":
        candidate = record
    elif stage == "load":
        candidate = record.get("target", {})
    elif stage == "hit":
        candidate = record
    elif stage == "hit-ready":
        candidate = record.get("target", {})
    else:
        raise ValueError("unsupported guest identity artifact")
    return {key: candidate.get(key) for key in IDENTITY_KEYS}


def validate_stage_ready(stage, ready_payload, identity):
    """Require the guest's exact all-stop boundary before creating an ACK."""
    expected = _validate_identity(identity)
    try:
        ready = json.loads(ready_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    target = ready.get("target", {})
    if any(target.get(key) != value for key, value in expected.items()):
        return False
    threads = ready.get("thread_states")
    if (
        ready.get("all_app_threads_stopped") is not True
        or not isinstance(threads, list)
        or not threads
        or any(not isinstance(thread, dict) or thread.get("stopped") is not True for thread in threads)
    ):
        return False
    if stage == "load":
        return bool(
            ready.get("event") == "LOAD_READY"
            and ready.get("stop_boundary") == "catch-load-libLLVM"
            and ready.get("load_catchpoint_disabled") is True
        )
    if stage != "hit":
        return False
    hit = ready.get("hit")
    breakpoint = ready.get("breakpoint", {})
    if not isinstance(hit, dict) or not isinstance(breakpoint, dict):
        return False
    try:
        breakpoint_address = int(breakpoint.get("address", "0"), 16)
    except (TypeError, ValueError):
        return False
    return bool(
        ready.get("event") == "HIT_READY"
        and ready.get("stop_boundary") == "temporary-hardware-breakpoint"
        and ready.get("release_eligible") is True
        and ready.get("release_blockers") == []
        and hit.get("event") == "HIT_RECORD"
        and hit.get("guest_boot_id") == expected["guest_boot_id"]
        and hit.get("process") == expected["process"]
        and hit.get("gdb_process") == expected["gdb_process"]
        and hit.get("target_pc_match") is True
        and hit.get("identity_match") is True
        and hit.get("errors") == {}
        and isinstance(hit.get("pc"), int)
        and hit.get("pc_mapping") != "UNKNOWN"
        and isinstance(hit.get("caller_resume_pc"), int)
        and hit.get("caller_mapping") != "UNKNOWN"
        and breakpoint.get("type") == "hardware"
        and breakpoint_address == hit.get("pc")
        and ready.get("hit") == hit
    )


def build_manifest(stage, identity, guest_files, mini_files):
    """Build a canonical, identity-bound controller manifest from verified bytes."""
    if stage not in REQUIRED_GUEST:
        raise ValueError("stage must be load or hit")
    expected_identity = _validate_identity(identity)
    if not REQUIRED_GUEST[stage].issubset(guest_files):
        raise ValueError("required guest evidence is missing")
    if not REQUIRED_MINI[stage].issubset(mini_files):
        raise ValueError("required Mini evidence is missing")

    files = {}
    for name, content in guest_files.items():
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or not name.startswith(RUN_ID + "-")
            or not isinstance(content, bytes)
            or not content
        ):
            raise ValueError("guest evidence file is invalid")
        files[name] = {"source": "guest", "sha256": sha256_bytes(content), "size": len(content)}

    id_artifacts = {
        RUN_ID + "-armed.json": "armed",
        RUN_ID + "-load-ready.json": "load",
        RUN_ID + "-hit-record.json": "hit",
        RUN_ID + "-hit-ready.json": "hit-ready",
    }
    for name, kind in id_artifacts.items():
        if name in guest_files and _artifact_identity(guest_files[name], kind) != expected_identity:
            raise ValueError("guest artifact identity mismatch: " + name)
    if stage == "hit" and guest_files.get(RUN_ID + "-hit-begin") != b"HIT_BEGIN\n":
        raise ValueError("first-hit marker is missing or invalid")

    for name, content in mini_files.items():
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or not name.startswith(RUN_ID + "-")
            or name in files
            or not isinstance(content, bytes)
            or not content
        ):
            raise ValueError("Mini evidence file is invalid")
        files[name] = {"source": "mini", "sha256": sha256_bytes(content), "size": len(content)}

    return canonical_json(
        {
            "event": "EVIDENCE_MANIFEST",
            "run_id": RUN_ID,
            "stage": stage,
            **expected_identity,
            "controller_acknowledged": True,
            "files": files,
        }
    ).encode("utf-8")


def build_release(stage, identity, manifest_payload):
    if stage not in REQUIRED_GUEST:
        raise ValueError("stage must be load or hit")
    expected_identity = _validate_identity(identity)
    try:
        manifest = json.loads(manifest_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("release manifest is invalid JSON") from error
    if any(manifest.get(key) != value for key, value in expected_identity.items()):
        raise ValueError("release manifest identity mismatch")
    if manifest.get("run_id") != RUN_ID or manifest.get("stage") != stage:
        raise ValueError("release manifest run or stage mismatch")
    return canonical_json(
        {
            "event": "CONTROLLER_ACK",
            "run_id": RUN_ID,
            "stage": stage,
            **expected_identity,
            "manifest_path": GUEST_ROOT + "-" + stage + "-manifest.json",
            "manifest_sha256": sha256_bytes(manifest_payload),
            "acknowledged": True,
        }
    ).encode("utf-8")


def build_abort(stage, identity, reason):
    if stage not in REQUIRED_GUEST or not reason or len(reason) > 256:
        raise ValueError("abort stage or reason is invalid")
    return canonical_json(
        {
            "event": "CONTROLLER_ABORT",
            "run_id": RUN_ID,
            "stage": stage,
            **_validate_identity(identity),
            "reason": reason,
        }
    ).encode("utf-8")


def validate_bracket_samples(stage, identity, before, after):
    """Apply the same identity, stage, clock, process, and counter rules at both ends."""
    if stage not in ("load", "hit", "post"):
        raise ValueError("unsupported QMP bracket stage")
    expected = _validate_identity(identity)
    samples = (before, after)
    for sample in samples:
        if (
            not isinstance(sample, dict)
            or sample.get("event") != "GUEST_RUNTIME_SNAPSHOT"
            or sample.get("run_id") != RUN_ID
            or sample.get("stage") != stage
            or type(sample.get("guest_wall_ns")) is not int
            or sample["guest_wall_ns"] < 0
            or type(sample.get("guest_monotonic_ns")) is not int
            or sample["guest_monotonic_ns"] < 0
        ):
            raise ValueError("guest clock or capture-stage sample is invalid")
        if any(sample.get(key) != value for key, value in expected.items()):
            raise ValueError("guest identity changed across QMP capture")
        for observation_key, process_key, expected_comm in (
            ("process_observation", "process", "flutter-auto"),
            ("gdb_observation", "gdb_process", "gdb"),
        ):
            observation = sample.get(observation_key)
            actual = observation.get("actual") if isinstance(observation, dict) else None
            if (
                not isinstance(observation, dict)
                or observation.get("matches") is not True
                or observation.get("state") != "LIVE"
                or not isinstance(actual, dict)
                or any(actual.get(key) != value for key, value in expected[process_key].items())
                or actual.get("comm") != expected_comm
                or not isinstance(actual.get("state"), str)
                or actual["state"] in ("Z", "X")
            ):
                raise ValueError(observation_key + " is not the matching live process")
        inferior_state = sample["process_observation"]["actual"]["state"]
        if stage in ("load", "hit") and inferior_state not in ("T", "t"):
            raise ValueError(stage + " capture bracket does not show the stopped inferior")
        if stage == "post" and inferior_state in ("T", "t"):
            raise ValueError("post-release capture bracket shows a stopped inferior")
        present = sample.get("present")
        kernel = sample.get("kernel")
        if (
            not isinstance(present, dict)
            or any(type(present.get(key)) is not int or present[key] < 0 for key in ("begin", "return", "success"))
            or not isinstance(kernel, dict)
            or any(type(kernel.get(key)) is not int or kernel[key] < 0 for key in ("baseline", "current", "delta"))
            or kernel["current"] < kernel["baseline"]
            or kernel["delta"] != kernel["current"] - kernel["baseline"]
        ):
            raise ValueError("present or kernel counters are inconsistent")
    first, last = samples
    if last["guest_monotonic_ns"] < first["guest_monotonic_ns"]:
        raise ValueError("guest monotonic time moved backwards across QMP capture")
    if first["kernel"]["baseline"] != last["kernel"]["baseline"]:
        raise ValueError("kernel fault baseline changed across QMP capture")
    if any(last["present"][key] < first["present"][key] for key in ("begin", "return", "success")):
        raise ValueError("present counter moved backwards across QMP capture")
    return expected


def build_bracket(
    stage,
    identity,
    before,
    after,
    host_start_ns,
    host_end_ns,
    capture_hashes,
    host_wall_start_ns=None,
    host_wall_end_ns=None,
):
    if stage not in ("load", "hit", "post"):
        raise ValueError("unsupported QMP bracket stage")
    expected = _validate_identity(identity)
    if (
        not isinstance(host_start_ns, int)
        or not isinstance(host_end_ns, int)
        or host_end_ns < host_start_ns
    ):
        raise ValueError("host interval is invalid")
    if host_wall_start_ns is None or host_wall_end_ns is None:
        raise ValueError("host wall interval is missing")
    if not isinstance(host_wall_start_ns, int) or not isinstance(host_wall_end_ns, int):
        raise ValueError("host wall interval is invalid")
    if host_wall_end_ns < host_wall_start_ns:
        raise ValueError("host wall interval is invalid")
    validate_bracket_samples(stage, identity, before, after)
    if not isinstance(capture_hashes, dict) or any(
        re.fullmatch(r"[0-9a-f]{64}", value) is None
        for value in capture_hashes.values()
    ):
        raise ValueError("QMP capture hash is invalid")
    required_captures = {
        "load": {RUN_ID + "-qmp-load-still.ppm"},
        "hit": {
            RUN_ID + "-qmp-hit-still.ppm",
            *(RUN_ID + "-qmp-hit-frame-%04d.ppm" % index for index in range(8)),
        },
        "post": {
            RUN_ID + "-qmp-post-still.ppm",
            *(RUN_ID + "-qmp-post-frame-%04d.ppm" % index for index in range(8)),
        },
    }[stage]
    if not required_captures.issubset(capture_hashes):
        raise ValueError("required complete QMP frame set is missing")
    return canonical_json(
        {
            "event": "QMP_CAPTURE_BRACKET",
            "run_id": RUN_ID,
            "stage": stage,
            **expected,
            "host_request_monotonic_ns": [host_start_ns, host_end_ns],
            "host_request_wall_ns": [host_wall_start_ns, host_wall_end_ns],
            "guest_before": before,
            "guest_after": after,
            "clock_origins_comparable": False,
            "capture_sha256": capture_hashes,
            "verified": True,
        }
    ).encode("utf-8")


def _validate_process_record(record, expected_comm):
    if not isinstance(record, dict) or record.get("uid") != 1001:
        raise ValueError("process identity UID mismatch")
    if not isinstance(record.get("pid"), int) or record["pid"] <= 0:
        raise ValueError("process identity PID is invalid")
    if re.fullmatch(r"[0-9]+", str(record.get("start_token", ""))) is None:
        raise ValueError("process identity start token is invalid")
    return {
        "pid": record["pid"],
        "uid": 1001,
        "start_token": str(record["start_token"]),
        "comm": expected_comm,
    }


def gdb_interrupt_python_source():
    return "\n".join(
        (
            "import os, signal, sys",
            "gp, gs, ap, ass = sys.argv[1:5]",
            "def identity(pid):",
            "    with open('/proc/%s/status' % pid, encoding='ascii') as f:",
            "        status = f.read()",
            "    with open('/proc/%s/comm' % pid, encoding='ascii') as f:",
            "        comm = f.read().strip()",
            "    with open('/proc/%s/stat' % pid, encoding='ascii') as f:",
            "        fields = f.read().rsplit(')', 1)[1].split()",
            "    uid = int(next(x.split()[1] for x in status.splitlines() if x.startswith('Uid:')))",
            "    return uid, comm, fields[19]",
            "gu, gc, gt = identity(gp)",
            "au, ac, at = identity(ap)",
            "with open('/proc/%s/status' % ap, encoding='ascii') as f:",
            "    tracer = int(next(x.split()[1] for x in f if x.startswith('TracerPid:'))) ",
            "assert (gu, gc, gt) == (1001, 'gdb', gs)",
            "assert (au, ac, at) == (1001, 'flutter-auto', ass)",
            "assert tracer == int(gp)",
            "assert hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal')",
            "fd = os.pidfd_open(int(gp), 0)",
            "try:",
            "    assert identity(gp) == (1001, 'gdb', gs)",
            "    assert identity(ap) == (1001, 'flutter-auto', ass)",
            "    with open('/proc/%s/status' % ap, encoding='ascii') as f:",
            "        tracer = int(next(x.split()[1] for x in f if x.startswith('TracerPid:'))) ",
            "    assert tracer == int(gp)",
            "    signal.pidfd_send_signal(fd, signal.SIGINT)",
            "finally:",
            "    os.close(fd)",
            "print('FLR0416_GDB_INTERRUPT=REQUESTED')",
        )
    )


def interrupt_gdb_command(gdb_process, app_process, expected_gdb=None):
    """Signal only the identity-checked debugger while it still traces this app."""
    gdb = _validate_process_record(gdb_process, "gdb")
    app = _validate_process_record(app_process, "flutter-auto")
    if expected_gdb is not None and gdb != _validate_process_record(expected_gdb, "gdb"):
        raise ValueError("GDB process identity mismatch")
    encoded_code = base64.b64encode(
        gdb_interrupt_python_source().encode("utf-8")
    ).decode("ascii")
    one_line_code = "import base64;exec(base64.b64decode('" + encoded_code + "'))"
    command = (
        "set -eu; python3 -c "
        + shlex.quote(one_line_code)
        + " "
        + str(gdb["pid"])
        + " "
        + shlex.quote(gdb["start_token"])
        + " "
        + str(app["pid"])
        + " "
        + shlex.quote(app["start_token"])
    )
    if len(command) > SERIAL_COMMAND_LIMIT:
        raise ValueError("exact GDB interrupt command exceeds serial contract")
    return command


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--qmp", type=Path)
    parser.add_argument("--claim-only", choices=("start",))
    parser.add_argument("--serial-port", type=int, default=10943)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument(
        "--marker-timeout-seconds",
        type=parse_marker_timeout_seconds,
        default=ACK_COLLECTION_SECONDS,
        help="shared maximum per-stage collection window (default: 540 seconds)",
    )
    parser.add_argument("--post-release-seconds", type=int, default=8)
    args = parser.parse_args(argv)
    if args.claim_only:
        try:
            create_attempt_claim(args.run_dir, args.claim_only)
        except Exception as error:
            reason = "already-claimed" if isinstance(error, FileExistsError) else type(error).__name__
            print("FLR0418_START_CLAIM=FAIL reason=" + reason, file=sys.stderr)
            return 1
        print("FLR0418_START_CLAIM=PASS run_id=" + RUN_ID)
        return 0
    if args.qmp is None:
        parser.error("--qmp is required for capture mode")
    repo_root = args.repo_root or (Path(os.environ["REPO_ROOT"]) if os.environ.get("REPO_ROOT") else None)
    if repo_root is None:
        parser.error("--repo-root or REPO_ROOT role is required")
    controller = CaptureController(
        args.run_dir,
        args.qmp,
        serial_port=args.serial_port,
        repo_root=repo_root,
        post_release_seconds=args.post_release_seconds,
        marker_timeout_seconds=args.marker_timeout_seconds,
    )
    return controller.run()


if __name__ == "__main__":
    raise SystemExit(main())
