#!/usr/bin/env python3
"""FLR-0399 one-run live-QMP observer contract and guest command builder."""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from flr0399_process_cleanup import cleanup_exact_qmp_processes


RUN_ID_RE = re.compile(r"flr(?:0399|0400|0401)-[0-9]{4}\Z")
DEMO_BUNDLE = (
    "/usr/share/flutter/toyota-connected-tcna-packages-filament-scene-"
    "fluorite-examples-demo/3.32.5/release"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS = REPO_ROOT / "scripts" / "qemu-runtime-harness.sh"
PIXEL_CAPTURE = REPO_ROOT / "scripts" / "qemu-pixel-capture.py"
SERIAL_PORT = 10930
SERIAL_USER = "root"
SERIAL_PROMPT = "root@qemux86-64:~# "


@dataclass(frozen=True)
class Identity:
    pid: int
    uid: int
    start_time: int

    def __post_init__(self) -> None:
        if self.pid <= 0 or self.uid < 0 or self.start_time <= 0:
            raise ValueError("process identity fields are out of range")


@dataclass(frozen=True)
class Sample:
    state: str
    identity: Identity | None
    log_path: str
    detail: str = ""
    ready_count: int = 0
    present_begin: int = 0
    present_return: int = 0
    sun_count: int = 0


@dataclass(frozen=True)
class CaptureRecord:
    stage: str
    identity: Identity
    live: bool


@dataclass(frozen=True)
class Outcome:
    status: str
    captures: tuple[CaptureRecord, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class GuestCommands:
    log_path: str
    identity_path: str
    preflight: str
    launch: str
    ready: str
    present: str
    identity: str
    collect: str
    stop: str
    capture_present_stack: str


def evidence_collect_command(log_path: str, run_id: str) -> str:
    """Collect bounded GDB, kernel, and matching coredump evidence fail-closed."""
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run id must be a fresh FLR-0399/0400/0401 id")
    if not log_path or "\n" in log_path or "\r" in log_path:
        raise ValueError("evidence log path must be a non-empty single line")
    q = shlex.quote
    return (
        "set -eu; "
        f"log={q(log_path)}; "
        "if [ ! -r \"$log\" ]; then "
        "echo FLR0399_GDB_LOG=UNAVAILABLE; "
        "echo FLR0399_EVIDENCE_COLLECT=FAIL; exit 1; fi; "
        "sha256sum \"$log\"; tail -n 160 \"$log\"; "
        "if journal_output=$(journalctl -k -b -n 350 -o short-iso --no-pager 2>&1); "
        "then :; else query_rc=$?; "
        "printf 'FLR0399_KERNEL_QUERY=FAIL rc=%s\\n' \"$query_rc\"; "
        "printf '%s\\n' \"$journal_output\" | tail -n 8 | cut -c1-400 | "
        "sed 's/^/FLR0399_QUERY_DIAGNOSTIC: /'; "
        "exit \"$query_rc\"; fi; "
        "kernel_matches=$(printf '%s\\n' \"$journal_output\" | "
        "grep -E -C 1 'Oops|FEngine::loop|page fault|BUG:|RIP:|Call Trace:' | "
        "tail -n 40 || true); "
        "if [ -n \"$kernel_matches\" ]; then "
        "printf 'FLR0399_KERNEL_QUERY=PASS\\n%s\\n' \"$kernel_matches\"; "
        "else echo FLR0399_KERNEL_QUERY=EMPTY; fi; "
        "if ! command -v coredumpctl >/dev/null 2>&1; then "
        "echo FLR0399_COREDUMP_QUERY=UNAVAILABLE; "
        "echo FLR0399_EVIDENCE_COLLECT=FAIL; exit 127; fi; "
        "if core_journal=$(journalctl -b COREDUMP_EXE=/usr/bin/flutter-auto "
        "-n 20 -o json --no-pager 2>&1); then :; else query_rc=$?; "
        "printf 'FLR0399_COREDUMP_QUERY=FAIL journal_rc=%s\\n' \"$query_rc\"; "
        "printf '%s\\n' \"$core_journal\" | tail -n 8 | cut -c1-400 | "
        "sed 's/^/FLR0399_QUERY_DIAGNOSTIC: /'; "
        "exit \"$query_rc\"; fi; "
        "if [ -z \"$core_journal\" ]; then "
        "echo FLR0399_COREDUMP_QUERY=EMPTY; "
        "else "
        "if coredump_output=$(coredumpctl list --no-pager --no-legend "
        "COREDUMP_EXE=/usr/bin/flutter-auto 2>&1); then :; else query_rc=$?; "
        "printf 'FLR0399_COREDUMP_QUERY=FAIL rc=%s\\n' \"$query_rc\"; "
        "printf '%s\\n' \"$coredump_output\" | tail -n 8 | cut -c1-400 | "
        "sed 's/^/FLR0399_QUERY_DIAGNOSTIC: /'; "
        "exit \"$query_rc\"; fi; "
        "core_matches=$(printf '%s\\n' \"$coredump_output\" | "
        "grep -E 'flutter-auto|FEngine' | tail -n 5 || true); "
        "if [ -n \"$core_matches\" ]; then "
        "printf 'FLR0399_COREDUMP_QUERY=PASS\\n%s\\n' \"$core_matches\"; "
        "else echo FLR0399_COREDUMP_QUERY=FAIL journal-hit-without-coredump; "
        "exit 1; fi; fi; "
        "echo FLR0399_EVIDENCE_COLLECT=PASS"
    )


def guest_commands(run_id: str, *, launch_mode: str = "gdb-run") -> GuestCommands:
    """Build one-line serial-exec commands from one run-scoped log path."""
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run id must be a fresh FLR-0399/0400/0401 id")
    if launch_mode not in {"gdb-run", "direct"}:
        raise ValueError("launch mode must be gdb-run or direct")

    prefix = f"/run/user/1001/{run_id}"
    log_path = f"{prefix}-gdb.log"
    identity_path = f"{prefix}-app.identity"
    q = shlex.quote

    preflight = (
        "set -eu; "
        "test \"$(id -u agl-driver)\" = 1001; "
        "test -S /run/user/1001/wayland-0; "
        "test -x /usr/bin/flutter-auto; test -x /usr/bin/gdb; "
        f"test -d {q(DEMO_BUNDLE)}; "
        "test -z \"$(pgrep -u 1001 -x flutter-auto || true)\"; "
        f"test ! -e {q(log_path)}; test ! -e {q(identity_path)}; "
        "echo FLR0399_GUEST_PREFLIGHT=PASS"
    )

    inner = (
        f"log={q(log_path)}; "
        "env XDG_RUNTIME_DIR=/run/user/1001 WAYLAND_DISPLAY=wayland-0 "
        "FLR0026_NATIVE_MODEL_MATCH=sequoia FLR0026_NATIVE_MODEL_LIMIT=2 "
        "FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1 "
        "FLR0305_PRODUCTION_SCENE_LIGHT=1 "
        "/usr/bin/timeout --signal=TERM --kill-after=2s 150 "
        "/usr/bin/gdb -q --batch "
        "-ex 'set pagination off' "
        "-ex 'handle SIGSEGV stop print nopass' "
        "-ex run -ex 'thread apply all bt 8' "
        f"--args /usr/bin/flutter-auto -b {q(DEMO_BUNDLE)} "
        ">\"$log\" 2>&1; rc=$?; "
        "printf '\\nFLR0399_APP_EXIT_STATUS=%s\\n' \"$rc\" >>\"$log\"; "
        "exit \"$rc\""
    )
    if launch_mode == "direct":
        inner = (
            f"log={q(log_path)}; "
            "env XDG_RUNTIME_DIR=/run/user/1001 WAYLAND_DISPLAY=wayland-0 "
            "FLR0026_NATIVE_MODEL_MATCH=sequoia FLR0026_NATIVE_MODEL_LIMIT=2 "
            "FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1 "
            "FLR0305_PRODUCTION_SCENE_LIGHT=1 "
            "/usr/bin/timeout --signal=TERM --kill-after=2s 150 "
            f"/usr/bin/flutter-auto -b {q(DEMO_BUNDLE)} "
            ">\"$log\" 2>&1; rc=$?; "
            "printf '\\nFLR0399_APP_EXIT_STATUS=%s\\n' \"$rc\" >>\"$log\"; "
            "exit \"$rc\""
        )
    launch = (
        "set -eu; "
        f"log={q(log_path)}; identity={q(identity_path)}; "
        "test \"$(id -u agl-driver)\" = 1001; "
        "test -S /run/user/1001/wayland-0; test -x /usr/bin/gdb; "
        "test ! -e \"$log\"; test ! -e \"$identity\"; "
        "test -z \"$(pgrep -u 1001 -x flutter-auto || true)\"; "
        f"nohup su -s /bin/sh agl-driver -c {q(inner)} "
        "</dev/null >/dev/null 2>&1 & wrapper=$!; "
        "for n in $(seq 1 30); do "
        "pids=$(pgrep -u 1001 -x flutter-auto || true); set -- $pids; "
        "[ \"$#\" -eq 1 ] && break; sleep 0.1; done; "
        "set -- $pids; test \"$#\" -eq 1; pid=$1; "
        "uid=$(awk '/^Uid:/{print $2; exit}' \"/proc/$pid/status\"); "
        "start=$(awk '{print $22}' \"/proc/$pid/stat\"); "
        "if [ -r \"/proc/$wrapper/stat\" ]; then wrapper_start=$(awk '{print $22}' \"/proc/$wrapper/stat\"); else wrapper_start=none; fi; "
        "test \"$uid\" = 1001; test -n \"$start\"; "
        "printf '%s %s %s %s %s\\n' \"$pid\" \"$uid\" \"$start\" "
        f"\"$wrapper\" \"$wrapper_start\" >{q(identity_path)}; "
        "printf 'FLR0399_LAUNCH=PASS pid=%s uid=%s start=%s\\n' "
        "\"$pid\" \"$uid\" \"$start\""
    )

    def gate(stage: str, predicate: str) -> str:
        return (
            "set -eu; "
            f"log={q(log_path)}; identity={q(identity_path)}; "
            "if [ ! -r \"$log\" ]; then "
            f"printf 'FLR0399_STATE=LOG_MISSING LOG_PATH=%s\\n' \"$log\"; exit 0; fi; "
            "test -r \"$identity\" || { "
            f"printf 'FLR0399_STATE=IDENTITY_MISSING LOG_PATH=%s\\n' \"$log\"; exit 0; }}; "
            "read pid saved_uid saved_start wrapper saved_wrapper_start < \"$identity\"; "
            "state=WAITING; "
            "if [ -r \"/proc/$pid/status\" ]; then "
            "uid=$(awk '/^Uid:/{print $2; exit}' \"/proc/$pid/status\"); "
            "start=$(awk '{print $22}' \"/proc/$pid/stat\"); "
            "if [ \"$uid\" != \"$saved_uid\" ] || [ \"$start\" != \"$saved_start\" ]; then state=EXITED; "
            "elif grep -q 'Program received signal SIGSEGV' \"$log\"; then state=FAULT; "
            f"elif {predicate}; then state={stage}; fi; "
            "else uid=none; start=none; state=EXITED; fi; "
            f"ready=$(grep -c 'FLUORITE_SEQUOIA_LIT_MATERIAL_READY.*parameter=linear-float3' \"$log\" || true); "
            f"begins=$(grep -c 'FLR0026_VK_QUEUE_PRESENT_BEGIN' \"$log\" || true); "
            f"returns=$(grep -c 'FLR0026_VK_QUEUE_PRESENT result=' \"$log\" || true); "
            f"sun=$(grep -c 'FLR0305_PRODUCTION_SCENE_LIGHT_SETUP_DONE' \"$log\" || true); "
            "printf 'FLR0399_STATE=%s PID=%s UID=%s START=%s READY=%s PRESENT_BEGIN=%s PRESENT_RETURN=%s SUN=%s LOG_PATH=%s\\n' "
            "\"$state\" \"$pid\" \"$uid\" \"$start\" \"$ready\" \"$begins\" \"$returns\" \"$sun\" \"$log\""
        )

    ready = gate(
        "READY",
        "grep -q 'FLUORITE_SEQUOIA_LIT_MATERIAL_READY.*parameter=linear-float3' \"$log\"",
    )
    present = gate("PRESENT", "grep -q 'FLR0026_VK_QUEUE_PRESENT result=' \"$log\"")
    identity = (
        "set -eu; "
        f"log={q(log_path)}; identity={q(identity_path)}; "
        "if [ ! -r \"$log\" ]; then "
        f"printf 'FLR0399_STATE=LOG_MISSING LOG_PATH=%s\\n' \"$log\"; exit 0; fi; "
        "if [ ! -r \"$identity\" ]; then "
        f"printf 'FLR0399_STATE=IDENTITY_MISSING LOG_PATH=%s\\n' \"$log\"; exit 0; fi; "
        "read pid saved_uid saved_start wrapper saved_wrapper_start < \"$identity\"; "
        "if [ -r \"/proc/$pid/status\" ]; then "
        "uid=$(awk '/^Uid:/{print $2; exit}' \"/proc/$pid/status\"); "
        "start=$(awk '{print $22}' \"/proc/$pid/stat\"); "
        "else uid=none; start=none; fi; "
        "if [ \"$uid\" = \"$saved_uid\" ] && [ \"$start\" = \"$saved_start\" ]; then state=LIVE; else state=EXITED; fi; "
        "printf 'FLR0399_STATE=%s PID=%s UID=%s START=%s LOG_PATH=%s\\n' "
        "\"$state\" \"$pid\" \"$uid\" \"$start\" \"$log\""
    )
    collect = evidence_collect_command(log_path, run_id)
    stop = (
        "set -eu; "
        f"identity={q(identity_path)}; "
        "if [ ! -r \"$identity\" ]; then echo FLR0399_APP_STOP=NOT_LAUNCHED; exit 0; fi; "
        "read pid saved_uid saved_start wrapper saved_wrapper_start < \"$identity\"; "
        "if [ -r \"/proc/$pid/status\" ]; then "
        "uid=$(awk '/^Uid:/{print $2; exit}' \"/proc/$pid/status\"); "
        "start=$(awk '{print $22}' \"/proc/$pid/stat\"); "
        "if [ \"$uid\" = \"$saved_uid\" ] && [ \"$start\" = \"$saved_start\" ]; then kill -TERM \"$pid\"; fi; fi; "
        "sleep 2; "
        "if [ -r \"/proc/$wrapper/stat\" ]; then wrapper_start=$(awk '{print $22}' \"/proc/$wrapper/stat\"); "
        "if [ \"$wrapper_start\" = \"$saved_wrapper_start\" ]; then kill -TERM \"$wrapper\"; fi; fi; "
        "echo FLR0399_APP_STOP=REQUESTED"
    )

    gdb_program = (
        "import gdb\n"
        "threads=[t for t in gdb.selected_inferior().threads() if t.name == 'FEngine::loop']\n"
        "print('FLR0401_FENGINE_THREAD_COUNT=%d' % len(threads))\n"
        "expanded=0\n"
        "for t in threads:\n"
        " t.switch()\n"
        " try:\n"
        "  stack=gdb.execute('bt 8', to_string=True)\n"
        " except Exception as e:\n"
        "  print('FLR0401_STACK_ERROR thread=%s error=%s' % (t.num, e))\n"
        "  continue\n"
        " print('FLR0401_THREAD=%s name=%s' % (t.num, t.name))\n"
        " print(stack)\n"
        " if 'lvp_pipe_sync_wait' in stack and expanded == 0:\n"
        "  print('FLR0401_EXPANDED_WAIT_THREAD=%s' % t.num)\n"
        "  print(gdb.execute('bt 24', to_string=True))\n"
        "  expanded=1"
    )
    escaped_gdb_program = (
        gdb_program.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
    gdb_python = f'python exec("{escaped_gdb_program}")'
    capture_present_stack = (
        "set -eu; "
        f"log={q(log_path)}; identity={q(identity_path)}; "
        "if [ ! -r \"$log\" ]; then echo FLR0401_GDB_CAPTURE_RESULT=SKIP_LOG; exit 1; fi; "
        "if [ ! -r \"$identity\" ]; then echo FLR0401_GDB_CAPTURE_RESULT=SKIP_IDENTITY; exit 1; fi; "
        "read pid saved_uid saved_start wrapper saved_wrapper_start < \"$identity\"; "
        "case \"$pid:$saved_uid:$saved_start\" in *[!0-9:]*) "
        "echo FLR0401_GDB_CAPTURE_RESULT=INVALID_IDENTITY; exit 1;; esac; "
        "if [ \"$saved_uid\" != 1001 ] || [ ! -r \"/proc/$pid/status\" ]; then "
        "echo FLR0401_GDB_CAPTURE_RESULT=IDENTITY_MISSING; exit 1; fi; "
        "comm=$(cat \"/proc/$pid/comm\" 2>/dev/null || true); "
        "uid=$(awk '/^Uid:/{print $2; exit}' \"/proc/$pid/status\"); "
        "start=$(awk '{print $22}' \"/proc/$pid/stat\"); "
        "if [ \"$comm\" != flutter-auto ] || [ \"$uid\" != \"$saved_uid\" ] || "
        "[ \"$start\" != \"$saved_start\" ]; then "
        "echo FLR0401_GDB_CAPTURE_RESULT=IDENTITY_CHANGED; exit 1; fi; "
        "begins=$(grep -c 'FLR0026_VK_QUEUE_PRESENT_BEGIN' \"$log\" || true); "
        "returns=$(grep -c 'FLR0026_VK_QUEUE_PRESENT result=' \"$log\" || true); "
        "case \"$begins:$returns\" in *[!0-9:]*) "
        "echo FLR0401_GDB_CAPTURE_RESULT=INVALID_COUNTERS; exit 1;; esac; "
        "if [ \"$begins\" -le \"$returns\" ]; then "
        "echo FLR0401_GDB_CAPTURE_RESULT=PRESENT_MATCHED; exit 1; fi; "
        "printf 'FLR0401_GDB_CAPTURE_BEGIN pid=%s present_begin=%s present_return=%s\\n' "
        "\"$pid\" \"$begins\" \"$returns\" | tee -a \"$log\"; "
        "if /usr/bin/timeout --signal=TERM --kill-after=2s 18 "
        "/usr/bin/gdb -q --batch --nx "
        "-iex 'set pagination off' -iex 'set confirm off' "
        "-iex 'set print thread-events off' -iex 'set sysroot /' "
        "-iex 'set solib-absolute-prefix /' "
        "-iex 'set solib-search-path /usr/lib:/lib' "
        "-iex 'set auto-solib-add off' -p \"$pid\" "
        "-ex 'sharedlibrary libvulkan_lvp[.]so' "
        f"-ex {q(gdb_python)} -ex 'detach' >>\"$log\" 2>&1; "
        "then rc=0; else rc=$?; fi; "
        "if [ \"$rc\" -eq 0 ]; then result=COMPLETE; "
        "elif [ \"$rc\" -eq 124 ]; then result=TIMEOUT; "
        "else result=GDB_FAILED; fi; "
        "printf 'FLR0401_GDB_CAPTURE_RESULT=%s rc=%s pid=%s\\n' "
        "\"$result\" \"$rc\" \"$pid\" | tee -a \"$log\"; exit \"$rc\""
    )

    commands = GuestCommands(
        log_path=log_path,
        identity_path=identity_path,
        preflight=preflight,
        launch=launch,
        ready=ready,
        present=present,
        identity=identity,
        collect=collect,
        stop=stop,
        capture_present_stack=capture_present_stack,
    )
    if any("\n" in command or len(command) > 4096 for command in commands.__dict__.values() if isinstance(command, str)):
        raise ValueError("generated guest command exceeds serial-exec contract")
    return commands


def expected_run_dir(evidence_root: Path, run_id: str) -> Path:
    """Return the fixed Mini evidence path for a supported observer run id."""
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run id must be a fresh FLR-0399/0400/0401 id")
    root = evidence_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("evidence root must be an existing directory")
    return root / run_id / "qemu"


def state_poll_label(stage: str, sample_number: int) -> str:
    """Give each READY/PRESENT snapshot its own immutable evidence label."""
    if stage not in {"ready", "present"}:
        raise ValueError("poll stage must be ready or present")
    if sample_number <= 0:
        raise ValueError("state sample number must be positive")
    return f"{stage}-{sample_number:03d}"


def parse_state_output(output: str, *, stage: str) -> Sample:
    """Parse exactly one bounded, machine-readable guest state marker."""
    marker_lines = [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("FLR0399_STATE=")
    ]
    if len(marker_lines) != 1:
        raise ValueError("serial-exec output must contain exactly one FLR-0399 state marker")

    fields: dict[str, str] = {}
    for token in marker_lines[0].split():
        if "=" not in token:
            raise ValueError("malformed FLR-0399 state token")
        key, value = token.split("=", 1)
        if key in fields:
            raise ValueError("duplicate FLR-0399 state field")
        fields[key] = value
    state = fields.get("FLR0399_STATE", "")
    log_path = fields.get("LOG_PATH", "")
    if not log_path:
        raise ValueError("FLR-0399 state marker lacks its log path")
    if state not in {
        "READY", "PRESENT", "WAITING", "EXITED", "FAULT", "LIVE",
        "LOG_MISSING", "LOG_UNREADABLE", "IDENTITY_MISSING",
    }:
        raise ValueError("unknown FLR-0399 state value")

    identity: Identity | None = None
    raw_identity = [fields.get("PID"), fields.get("UID"), fields.get("START")]
    if any(value is not None for value in raw_identity):
        if all(value is not None and value.isdigit() for value in raw_identity):
            identity = Identity(*(int(value) for value in raw_identity if value is not None))
        elif state != "EXITED" or raw_identity[0] is None:
            raise ValueError("malformed FLR-0399 process identity")

    if state in {"READY", "PRESENT", "WAITING", "LIVE", "FAULT"} and identity is None:
        raise ValueError("live FLR-0399 state lacks process identity")
    counter_fields = {
        "READY": "ready_count",
        "PRESENT_BEGIN": "present_begin",
        "PRESENT_RETURN": "present_return",
        "SUN": "sun_count",
    }
    require_counters = state in {"READY", "PRESENT", "WAITING", "FAULT"} or any(
        key in fields for key in counter_fields
    )
    counters: dict[str, int] = {}
    for field_name, attribute in counter_fields.items():
        value = fields.get(field_name)
        if value is None:
            if require_counters:
                raise ValueError(f"FLR-0399 live state lacks {field_name} counter")
            counters[attribute] = 0
            continue
        if re.fullmatch(r"[0-9]+", value) is None:
            raise ValueError(f"FLR-0399 state has malformed {field_name} counter")
        counters[attribute] = int(value)
    return Sample(
        state=state,
        identity=identity,
        log_path=log_path,
        detail=fields.get("DETAIL", ""),
        **counters,
    )


def make_state_reader(
    commands: GuestCommands,
    serial: Callable[[str, str, float], str],
) -> Callable[[str, float], Sample]:
    """Bind state polling to unique serial artifacts and one guest log source."""
    poll_numbers = {"ready": 0, "present": 0}

    def read_state(stage: str, remaining: float) -> Sample:
        if stage in poll_numbers:
            poll_numbers[stage] += 1
            serial_label = state_poll_label(stage, poll_numbers[stage])
            command_stage = stage
        elif stage.startswith("identity-after-"):
            serial_label = stage
            command_stage = "identity"
        else:
            serial_label = stage
            command_stage = stage
        command = getattr(commands, command_stage)
        output = serial(serial_label, command, min(15.0, remaining))
        return parse_state_output(output, stage=command_stage)

    return read_state


def make_frame_capture(
    run_dir: Path,
    qmp: Path,
    run_id: str,
) -> Callable[[str, Identity, float], None]:
    """Capture every still and exactly one short video at the first live frame."""
    video_captured = False

    def capture_frame(stage: str, _identity: Identity, remaining: float) -> None:
        nonlocal video_captured
        capture_video = not video_captured
        _capture_qmp(
            run_dir,
            qmp,
            f"{run_id}-{stage.lower()}",
            video=capture_video,
            timeout_seconds=remaining,
        )
        if capture_video:
            video_captured = True

    return capture_frame


def run_once(
    *,
    read_state: Callable[[str, float], Sample],
    capture_frame: Callable[[str, Identity, float], None],
    preserve_evidence: Callable[[], None],
    teardown: Callable[[], None],
    expected_log_path: str,
    timeout_seconds: float,
    expected_uid: int = 1001,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    poll_interval_seconds: float = 2.0,
    deadline: float | None = None,
) -> Outcome:
    """Poll bounded guest snapshots until READY/present or the fixed deadline.

    The adapter for each guest-state read is responsible for a bounded,
    single serial-exec request. WAITING never extends the absolute deadline;
    its first live sample gets one diagnostic capture. Evidence preservation
    always precedes the single teardown callback.
    """
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be positive")

    deadline_at = deadline if deadline is not None else monotonic() + timeout_seconds
    captures: list[CaptureRecord] = []
    errors: list[str] = []
    status = "OBSERVER_FAILED"

    def read(stage: str) -> Sample:
        nonlocal status
        remaining = deadline_at - monotonic()
        if remaining <= 0:
            status = (
                "IDENTITY_DEADLINE_EXPIRED"
                if stage.startswith("identity-after-")
                else f"{stage.upper()}_DEADLINE_EXPIRED"
            )
            raise TimeoutError(status)
        sample = read_state(stage, remaining)
        if deadline_at - monotonic() <= 0:
            status = (
                "IDENTITY_DEADLINE_EXPIRED"
                if stage.startswith("identity-after-")
                else f"{stage.upper()}_DEADLINE_EXPIRED"
            )
            raise TimeoutError(status)
        if sample.log_path != expected_log_path:
            status = "LOG_SOURCE_MISMATCH"
            raise RuntimeError("observer log path differs from configured GDB log")
        if sample.state in ("LOG_MISSING", "LOG_UNREADABLE"):
            status = sample.state
            raise RuntimeError(sample.detail or sample.state.lower().replace("_", " "))
        return sample

    def capture_live(stage: str, before: Sample) -> bool:
        nonlocal status
        if before.identity is None:
            status = "IDENTITY_MISSING"
            return False
        if before.identity.uid != expected_uid:
            status = "IDENTITY_UID_MISMATCH"
            return False
        remaining = deadline_at - monotonic()
        if remaining <= 0:
            status = "CAPTURE_DEADLINE_EXPIRED"
            return False
        try:
            capture_frame(stage, before.identity, remaining)
        except Exception as exc:  # keep the evidence/teardown path alive
            errors.append(f"capture:{type(exc).__name__}:{exc}")
            status = "CAPTURE_FAILED"
            return False
        if deadline_at - monotonic() <= 0:
            captures.append(CaptureRecord(stage=stage, identity=before.identity, live=False))
            status = "CAPTURE_DEADLINE_EXPIRED"
            return False
        captures.append(CaptureRecord(stage=stage, identity=before.identity, live=False))
        after = read(f"identity-after-{stage.lower()}")
        if after.state != "LIVE" or after.identity != before.identity:
            status = "POST_EXIT" if after.state == "EXITED" else "IDENTITY_CHANGED"
            return False
        captures[-1] = CaptureRecord(stage=stage, identity=before.identity, live=True)
        return True

    def observe() -> str:
        nonlocal status
        waiting_captured = False

        def wait_for_state(stage: str, sample: Sample) -> Sample | None:
            nonlocal status, waiting_captured
            while sample.state == "WAITING":
                if not waiting_captured:
                    if not capture_live("WAITING", sample):
                        return None
                    waiting_captured = True
                remaining = deadline_at - monotonic()
                if remaining <= 0:
                    status = f"{stage.upper()}_DEADLINE_EXPIRED"
                    return None
                sleep(min(poll_interval_seconds, remaining))
                if deadline_at - monotonic() <= 0:
                    status = f"{stage.upper()}_DEADLINE_EXPIRED"
                    return None
                try:
                    sample = read(stage)
                except Exception as exc:
                    if status not in ("LOG_SOURCE_MISMATCH", "LOG_MISSING", "LOG_UNREADABLE"):
                        errors.append(f"{stage}:{type(exc).__name__}:{exc}")
                    return None
            return sample

        try:
            ready = read("ready")
        except Exception as exc:
            if status not in ("LOG_SOURCE_MISMATCH", "LOG_MISSING", "LOG_UNREADABLE"):
                errors.append(f"ready:{type(exc).__name__}:{exc}")
            return status
        ready = wait_for_state("ready", ready)
        if ready is None:
            return status
        if ready.state == "TIMEOUT":
            return "READY_TIMEOUT"

        if ready.state == "EXITED":
            return "APP_EXITED_BEFORE_READY"
        if ready.state == "FAULT":
            if capture_live("FAULT", ready):
                return "FAULT_BEFORE_READY"
            return status
        if ready.state != "READY":
            return "INVALID_READY_SAMPLE"
        if not capture_live("READY", ready):
            return status

        try:
            present = read("present")
        except Exception as exc:
            if status not in ("LOG_SOURCE_MISMATCH", "LOG_MISSING", "LOG_UNREADABLE"):
                errors.append(f"present:{type(exc).__name__}:{exc}")
            return status
        present = wait_for_state("present", present)
        if present is None:
            return status
        if present.state == "TIMEOUT":
            return "PRESENT_TIMEOUT"
        if present.state == "EXITED":
            return "APP_EXITED_AFTER_READY"
        if present.state == "FAULT":
            if capture_live("FAULT", present):
                return "FAULT_AFTER_READY"
            return status
        if present.state != "PRESENT":
            return "INVALID_PRESENT_SAMPLE"
        if not capture_live("PRESENT", present):
            return status
        return "OBSERVED"

    try:
        try:
            status = observe()
        except Exception as exc:
            errors.append(f"observer:{type(exc).__name__}:{exc}")
            if status == "OBSERVER_FAILED":
                status = "OBSERVER_ERROR"
    finally:
        try:
            preserve_evidence()
        except Exception as exc:
            errors.append(f"preserve:{type(exc).__name__}:{exc}")
            status = "EVIDENCE_PRESERVE_FAILED"
        try:
            teardown()
        except Exception as exc:
            errors.append(f"teardown:{type(exc).__name__}:{exc}")
            status = "TEARDOWN_FAILED"
    return Outcome(status, tuple(captures), tuple(errors))


def wrap_serial_child_command(command: str) -> str:
    """Run guest logic in a child shell so `exit` cannot kill serial-exec."""
    if "\n" in command or "\r" in command:
        raise ValueError("serial child command must be one line")
    wrapped = f"/bin/sh -c {shlex.quote(command)}"
    if len(wrapped) > 4096:
        raise ValueError("wrapped serial child command exceeds 4096 bytes")
    return wrapped


def _serial_exec(
    *,
    run_dir: Path,
    label: str,
    command: str,
    serial_port: int,
    timeout_seconds: float = 40.0,
) -> str:
    if timeout_seconds <= 0:
        raise TimeoutError("serial-exec deadline expired")
    command_file = run_dir / f"FLR-0399-{label}.cmd"
    output_file = run_dir / f"FLR-0399-{label}.serial.log"
    setup_output_file = run_dir / f"FLR-0399-{label}.setup.serial.log"
    harness_log = run_dir / f"FLR-0399-{label}.harness.log"
    for path in (command_file, output_file, setup_output_file, harness_log):
        if path.exists():
            raise FileExistsError(f"evidence path already exists: {path.name}")
    command_file.write_text(wrap_serial_child_command(command) + "\n", encoding="utf-8")
    command_file.chmod(0o600)
    process = subprocess.Popen(
        [
            str(HARNESS),
            "serial-exec",
            "--serial-port",
            str(serial_port),
            "--user",
            SERIAL_USER,
            "--prompt",
            SERIAL_PROMPT,
            "--command-file",
            str(command_file),
            "--output",
            str(output_file),
            "--setup-output",
            str(setup_output_file),
            "--timeout-seconds",
            str(max(1, math.ceil(timeout_seconds))),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=(os.name == "posix"),
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=1.0)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
        harness_log.write_text(
            (stdout or "")
            + (stderr or "")
            + f"\nserial-exec=TIMEOUT seconds={timeout_seconds:g}\n",
            encoding="utf-8",
        )
        if not output_file.exists():
            output_file.write_text(
                "serial-exec=TIMEOUT partial-serial-output=UNAVAILABLE\n",
                encoding="utf-8",
            )
        raise TimeoutError(f"serial-exec timed out at {label}; see {harness_log.name}") from exc

    harness_log.write_text((stdout or "") + (stderr or ""), encoding="utf-8")
    if process.returncode != 0:
        raise RuntimeError(f"serial-exec failed at {label}; see {harness_log.name}")
    if not output_file.is_file():
        raise RuntimeError(f"serial-exec produced no output at {label}")
    return output_file.read_text(encoding="utf-8", errors="replace")


def _capture_output(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def _run_qmp_capture_command(
    command: list[str], log_path: Path, timeout: float, label: str
) -> None:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        log_path.write_text(
            f"capture=TIMEOUT stage={label} seconds={timeout:g}\n"
            + _capture_output(exc.stdout)
            + _capture_output(exc.stderr),
            encoding="utf-8",
        )
        raise TimeoutError(f"QMP capture timed out at {label}; see {log_path.name}") from exc
    log_path.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"QMP capture failed at {label}; see {log_path.name}")


def _capture_qmp(
    run_dir: Path,
    qmp: Path,
    label: str,
    *,
    video: bool,
    timeout_seconds: float = 35.0,
) -> None:
    if timeout_seconds <= 0:
        raise TimeoutError("QMP capture deadline expired")
    capture_deadline = time.monotonic() + timeout_seconds

    def remaining_timeout() -> float:
        remaining = capture_deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("QMP capture deadline expired")
        return min(35.0, remaining)

    still = run_dir / f"FLR-0399-{label}.ppm"
    still_log = run_dir / f"FLR-0399-{label}.capture.log"
    if still.exists() or still_log.exists():
        raise FileExistsError(f"QMP capture evidence already exists for {label}")
    frames = run_dir / f"FLR-0399-{label}-frames"
    video_log = run_dir / f"FLR-0399-{label}-video.log"
    if video and (frames.exists() or video_log.exists()):
        raise FileExistsError(f"QMP video evidence already exists for {label}")
    _run_qmp_capture_command(
        [sys.executable, str(PIXEL_CAPTURE), "capture", "--socket", str(qmp), "--output", str(still)],
        still_log,
        remaining_timeout(),
        f"{label}-still",
    )
    if video:
        _run_qmp_capture_command(
            [
                sys.executable,
                str(PIXEL_CAPTURE),
                "video",
                "--socket",
                str(qmp),
                "--frames-dir",
                str(frames),
                "--frames",
                "4",
                "--interval",
                "0.25",
            ],
            video_log,
            remaining_timeout(),
            f"{label}-video",
        )


def _read_runtime_processes() -> list[str]:
    result = subprocess.run(
        ["ps", "-axo", "pid=,comm=,args="],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ps exited {result.returncode}")
    targets: list[str] = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) < 2:
            continue
        pid, comm = fields[:2]
        args = fields[2] if len(fields) == 3 else ""
        executable_names = [Path(token.strip("'\";," )).name for token in args.split()]
        is_target = (
            comm.startswith("qemu-system-")
            or comm in {"runqemu", "flutter-auto"}
            or any(
                name == "runqemu"
                or name == "flutter-auto"
                or name.startswith("qemu-system-")
                for name in executable_names
            )
        )
        if is_target:
            targets.append(f"pid={pid} comm={comm} args={args[:300]}")
    return targets


def _read_listening_ports() -> set[int]:
    ss = shutil.which("ss")
    if ss is not None:
        result = subprocess.run(
            [ss, "-H", "-ltn"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ss exited {result.returncode}")
        listening: set[int] = set()
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) < 4:
                continue
            port = fields[3].rsplit(":", 1)[-1]
            if port.isdigit():
                listening.add(int(port))
        return listening

    lsof = shutil.which("lsof")
    if lsof is None:
        raise RuntimeError("neither ss nor lsof is available")
    listening = set()
    for port in (10930, 10931, 10932):
        result = subprocess.run(
            [lsof, "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and len(result.stdout.splitlines()) > 1:
            listening.add(port)
        elif result.returncode not in (0, 1):
            raise RuntimeError(f"lsof exited {result.returncode} for port {port}")
    return listening


def verify_postflight(
    *,
    run_dir: Path,
    qmp: Path,
    ports: tuple[int, ...] = (10930, 10931, 10932),
    process_reader: Callable[[], list[str]] = _read_runtime_processes,
    listening_ports_reader: Callable[[], set[int]] = _read_listening_ports,
    report_name: str = "FLR-0399-postflight.log",
) -> tuple[str, ...]:
    """Verify runtime residue independently of whether QMP is still present."""
    errors: list[str] = []
    lines = ["FLR0399_POSTFLIGHT=START"]
    try:
        processes = process_reader()
    except Exception as exc:
        processes = []
        errors.append(f"process-scan-unavailable:{type(exc).__name__}")
    if processes:
        errors.append("runtime-process-residual")
        lines.append(f"processes={len(processes)}:RESIDUAL")
        lines.extend(processes)
    else:
        lines.append("processes=0")

    try:
        qmp_present = qmp.exists() or qmp.is_symlink()
    except OSError as exc:
        qmp_present = True
        errors.append(f"qmp-state-unavailable:{type(exc).__name__}")
    lines.append(f"qmp={'RESIDUAL' if qmp_present else 'ABSENT'}")
    if qmp_present:
        errors.append("qmp-socket-residual")

    try:
        listening = listening_ports_reader()
    except Exception as exc:
        listening = set()
        errors.append(f"port-scan-unavailable:{type(exc).__name__}")
        lines.append("ports=UNKNOWN")
    else:
        busy = [port for port in ports if port in listening]
        if busy:
            errors.extend(f"port-listener:{port}" for port in busy)
            lines.append("ports=" + ",".join(str(port) for port in busy) + ":LISTENING")
        else:
            lines.append("ports=" + ",".join(str(port) for port in ports) + ":FREE")

    lines.append(f"FLR0399_POSTFLIGHT={'FAIL' if errors else 'PASS'}")
    try:
        if Path(report_name).name != report_name:
            raise ValueError("postflight report name must be a basename")
        (run_dir / report_name).write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        errors.append(f"postflight-evidence-write-failed:{type(exc).__name__}")
    return tuple(errors)


def _analyze_capture(run_dir: Path, image: Path) -> None:
    regions = {
        "full": "0,0,1280,800",
        "sequoia": "440,220,400,360",
        "hud": "0,0,320,200",
    }
    for name, region in regions.items():
        output = run_dir / f"{image.stem}-{name}-analysis.log"
        result = subprocess.run(
            [
                sys.executable,
                str(PIXEL_CAPTURE),
                "analyze",
                "--input",
                str(image),
                "--region",
                region,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        output.write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"QMP pixel analysis failed: {image.name}/{name}")


def _encode_videos(run_dir: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        (run_dir / "FLR-0399-video-encode.log").write_text(
            "video-encode=UNKNOWN reason=ffmpeg-unavailable; raw QMP frames retained\n",
            encoding="utf-8",
        )
        return
    for frames in sorted(run_dir.glob("FLR-0399-*-frames")):
        output = run_dir / f"{frames.name[:-7]}.mp4"
        if output.exists():
            raise FileExistsError(f"evidence path already exists: {output.name}")
        result = subprocess.run(
            [
                ffmpeg,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                "4",
                "-i",
                str(frames / "frame-%05d.ppm"),
                "-frames:v",
                "4",
                "-pix_fmt",
                "yuv420p",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        (run_dir / f"{frames.name}-encode.log").write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        if result.returncode != 0 or not output.is_file():
            raise RuntimeError(f"QMP frame-to-video encoding failed: {frames.name}")


def observe(args: argparse.Namespace) -> int:
    run_id = args.run_id
    commands = guest_commands(run_id, launch_mode=args.launch_mode)
    expected = expected_run_dir(args.evidence_root, run_id)
    run_dir = args.run_dir.resolve(strict=True)
    if run_dir != expected or not run_dir.is_dir():
        raise ValueError("run directory must match the existing fixed Mini evidence role path")
    qmp = args.qmp.resolve()
    if qmp.parent != run_dir or not qmp.is_socket():
        raise ValueError("QMP socket must be live inside this run's evidence directory")
    if not HARNESS.is_file() or not PIXEL_CAPTURE.is_file():
        raise FileNotFoundError("committed runtime harness or QMP capture helper is missing")

    state = {"preserved": False, "teardown": False}
    teardown_errors: list[str] = []
    teardown_notes: list[str] = []
    deadline = time.monotonic() + args.timeout_seconds

    def remaining_budget() -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("FLR-0399 observer deadline expired")
        return remaining

    def serial(label: str, command: str, timeout_seconds: float = 40.0) -> str:
        return _serial_exec(
            run_dir=run_dir,
            label=label,
            command=command,
            serial_port=args.serial_port,
            timeout_seconds=min(40.0, timeout_seconds),
        )

    def preserve_evidence() -> None:
        if state["preserved"]:
            return
        state["preserved"] = True
        output = serial("collect", commands.collect)
        if "FLR0399_EVIDENCE_COLLECT=PASS" not in output:
            raise RuntimeError("bounded guest evidence marker missing")

    def teardown() -> None:
        if state["teardown"]:
            return
        state["teardown"] = True
        try:
            output = serial("stop", commands.stop)
            if "FLR0399_APP_STOP=" not in output:
                teardown_notes.append("guest-stop=UNCONFIRMED")
        except Exception as exc:
            teardown_notes.append(f"guest-stop=UNAVAILABLE:{type(exc).__name__}")
        if qmp.is_socket():
            try:
                result = subprocess.run(
                    [str(HARNESS), "qmp-quit", "--qmp", str(qmp)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=35,
                )
                (run_dir / "FLR-0399-qmp-quit.log").write_text(
                    result.stdout + result.stderr, encoding="utf-8"
                )
                if result.returncode != 0:
                    teardown_notes.append(f"qmp-quit=UNCONFIRMED rc={result.returncode}")
            except Exception as exc:
                teardown_notes.append(f"qmp-quit=UNAVAILABLE:{type(exc).__name__}")
        else:
            teardown_notes.append("qmp-quit=SKIPPED_SOCKET_ABSENT")

        pre_cleanup_errors = verify_postflight(
            run_dir=run_dir,
            qmp=qmp,
            report_name="FLR-0399-postflight-before-cleanup.log",
        )
        if pre_cleanup_errors:
            cleanup = cleanup_exact_qmp_processes(qmp, timeout_seconds=3.0)
            cleanup_lines = [
                f"residual={process.description}" for process in cleanup.remaining
            ]
            cleanup_lines.extend(f"error={error}" for error in cleanup.errors)
            cleanup_lines.append(
                "FLR0399_EXACT_CLEANUP="
                f"{'PASS' if not cleanup.remaining and not cleanup.errors else 'FAIL'} "
                f"residual={len(cleanup.remaining)} "
                f"qmp_socket_removed={str(cleanup.qmp_socket_removed).lower()}"
            )
            (run_dir / "FLR-0399-exact-qmp-cleanup.log").write_text(
                "\n".join(cleanup_lines) + "\n", encoding="utf-8"
            )
            if cleanup.remaining or cleanup.errors:
                teardown_errors.append("exact-qmp-cleanup-failed")
            else:
                teardown_notes.append("exact-qmp-cleanup=PASS")
        final_postflight_errors = verify_postflight(
            run_dir=run_dir,
            qmp=qmp,
            report_name="FLR-0399-postflight-final.log",
        )
        teardown_errors.extend(final_postflight_errors)
        teardown_log = [*teardown_notes, *teardown_errors]
        try:
            (run_dir / "FLR-0399-teardown.log").write_text(
                "\n".join(teardown_log) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            teardown_errors.append(f"teardown-evidence-write-failed:{type(exc).__name__}")
        if teardown_errors:
            raise RuntimeError("; ".join(teardown_errors))

    outcome: Outcome | None = None
    setup_error: str | None = None
    try:
        _capture_qmp(
            run_dir,
            qmp,
            "pre-launch",
            video=True,
            timeout_seconds=remaining_budget(),
        )
        preflight = serial(
            "preflight",
            commands.preflight,
            timeout_seconds=remaining_budget(),
        )
        if "FLR0399_GUEST_PREFLIGHT=PASS" not in preflight:
            raise RuntimeError("guest preflight marker missing")
        launch = serial("launch", commands.launch, timeout_seconds=remaining_budget())
        if "FLR0399_LAUNCH=PASS" not in launch:
            raise RuntimeError("guest launch marker missing")

        read_state = make_state_reader(commands, serial)

        capture_frame = make_frame_capture(run_dir, qmp, run_id)

        outcome = run_once(
            read_state=read_state,
            capture_frame=capture_frame,
            preserve_evidence=preserve_evidence,
            teardown=teardown,
            expected_log_path=commands.log_path,
            timeout_seconds=args.timeout_seconds,
            deadline=deadline,
        )
    except Exception as exc:
        setup_error = f"{type(exc).__name__}:{exc}"
        try:
            preserve_evidence()
        except Exception as preserve_exc:
            setup_error += f"; preserve:{type(preserve_exc).__name__}"
        try:
            teardown()
        except Exception as teardown_exc:
            setup_error += f"; teardown:{type(teardown_exc).__name__}"

    _encode_videos(run_dir)
    ppm_files = sorted(run_dir.glob("FLR-0399-*.ppm"))
    for image in ppm_files:
        _analyze_capture(run_dir, image)
    hashes = []
    for path in sorted(run_dir.glob("FLR-0399-*")):
        if path.is_file() and path.suffix in {".ppm", ".mp4"}:
            hashes.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (run_dir / "FLR-0399-capture-sha256.txt").write_text(
        "\n".join(hashes) + ("\n" if hashes else ""), encoding="utf-8"
    )

    if setup_error is not None:
        result_status = f"SETUP_FAILED {setup_error}"
        captures = ()
    else:
        assert outcome is not None
        result_status = outcome.status
        captures = outcome.captures
    lines = [f"FLR0399_OBSERVER_STATUS={result_status}"]
    for item in captures:
        lines.append(
            f"capture={item.stage} pid={item.identity.pid} uid={item.identity.uid} "
            f"start={item.identity.start_time} live_bracket={str(item.live).lower()}"
        )
    lines.extend(f"error={error}" for error in (outcome.errors if outcome else ()))
    lines.append("visual_gate=MANUAL_REVIEW_REQUIRED")
    (run_dir / "FLR-0399-controller-result.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))
    return 0 if outcome is not None and outcome.status in {"OBSERVED", "PRESENT_TIMEOUT"} else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    observe_parser = subparsers.add_parser("observe")
    observe_parser.add_argument("--run-id", required=True)
    observe_parser.add_argument("--evidence-root", type=Path, required=True)
    observe_parser.add_argument("--run-dir", type=Path, required=True)
    observe_parser.add_argument("--qmp", type=Path, required=True)
    observe_parser.add_argument("--serial-port", type=int, default=SERIAL_PORT)
    observe_parser.add_argument("--timeout-seconds", type=float, default=120.0)
    observe_parser.add_argument(
        "--launch-mode", choices=("gdb-run", "direct"), default="gdb-run"
    )
    args = parser.parse_args(argv)
    if args.operation == "observe":
        try:
            return observe(args)
        except Exception as exc:
            print(f"FLR0399_OBSERVER=FAIL reason={type(exc).__name__}:{exc}", file=sys.stderr)
            return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
