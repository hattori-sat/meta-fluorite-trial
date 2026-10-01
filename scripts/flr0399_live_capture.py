#!/usr/bin/env python3
"""FLR-0399 one-run live-QMP observer contract and guest command builder."""

from __future__ import annotations

import argparse
import hashlib
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


RUN_ID_RE = re.compile(r"flr0399-[0-9]{4}\Z")
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


def guest_commands(run_id: str) -> GuestCommands:
    """Build one-line serial-exec commands from one run-scoped log path."""
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run id must be a fresh FLR-0399 id: flr0399-NNNN")

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
            f"state=WAITING; for n in $(seq 1 100); do "
            f"if {predicate}; then state={stage}; break; fi; "
            "if [ ! -r \"/proc/$pid/status\" ]; then state=EXITED; break; fi; "
            "if grep -q 'Program received signal SIGSEGV' \"$log\"; then state=FAULT; break; fi; "
            "uid=$(awk '/^Uid:/{print $2; exit}' \"/proc/$pid/status\"); "
            "start=$(awk '{print $22}' \"/proc/$pid/stat\"); "
            "if [ \"$uid\" != \"$saved_uid\" ] || [ \"$start\" != \"$saved_start\" ]; then state=EXITED; break; fi; "
            "sleep 0.2; done; "
            "if [ -r \"/proc/$pid/status\" ]; then "
            "uid=$(awk '/^Uid:/{print $2; exit}' \"/proc/$pid/status\"); "
            "start=$(awk '{print $22}' \"/proc/$pid/stat\"); "
            "else uid=none; start=none; fi; "
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
    collect = (
        "set -eu; "
        f"log={q(log_path)}; "
        "if [ -r \"$log\" ]; then "
        "sha256sum \"$log\"; tail -n 160 \"$log\"; "
        "else echo FLR0399_GDB_LOG=UNAVAILABLE; fi; "
        "journalctl -k -b -n 350 -o short-iso --no-pager 2>/dev/null | "
        "grep -E -C 1 'Oops|FEngine::loop|page fault|BUG:|RIP:|Call Trace:' | tail -n 40 || true; "
        "coredumpctl list --no-pager --no-legend 2>/dev/null | "
        "grep -E 'flutter-auto|FEngine' | tail -n 5 || true; "
        "echo FLR0399_EVIDENCE_COLLECT=PASS"
    )
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
    )
    if any("\n" in command or len(command) > 4096 for command in commands.__dict__.values() if isinstance(command, str)):
        raise ValueError("generated guest command exceeds serial-exec contract")
    return commands


def expected_run_dir(evidence_root: Path, run_id: str) -> Path:
    """Return the one Mini evidence role path for a valid FLR-0399 run id."""
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run id must be a fresh FLR-0399 id: flr0399-NNNN")
    root = evidence_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("evidence root must be an existing directory")
    return root / run_id / "qemu"


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

    if state in {"READY", "PRESENT", "LIVE", "FAULT"} and identity is None:
        raise ValueError("live FLR-0399 state lacks process identity")
    if state == "WAITING" and stage in {"ready", "present"}:
        state = "TIMEOUT"
    return Sample(
        state=state,
        identity=identity,
        log_path=log_path,
        detail=fields.get("DETAIL", ""),
    )


def run_once(
    *,
    read_state: Callable[[str, float], Sample],
    capture_frame: Callable[[str, Identity], None],
    preserve_evidence: Callable[[], None],
    teardown: Callable[[], None],
    expected_log_path: str,
    timeout_seconds: float,
    expected_uid: int = 1001,
    monotonic: Callable[[], float] = time.monotonic,
) -> Outcome:
    """Observe READY/present once; capture only with a stable live identity.

    The adapter for each guest-state read is responsible for a bounded,
    single serial-exec request. This controller never retries a missing log.
    Evidence preservation always precedes the single teardown callback.
    """
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    deadline = monotonic() + timeout_seconds
    captures: list[CaptureRecord] = []
    errors: list[str] = []
    status = "OBSERVER_FAILED"

    def read(stage: str) -> Sample:
        nonlocal status
        remaining = max(0.0, deadline - monotonic())
        sample = read_state(stage, remaining)
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
        try:
            capture_frame(stage, before.identity)
        except Exception as exc:  # keep the evidence/teardown path alive
            errors.append(f"capture:{type(exc).__name__}:{exc}")
            status = "CAPTURE_FAILED"
            return False
        captures.append(CaptureRecord(stage=stage, identity=before.identity, live=False))
        after = read("identity")
        if after.state != "LIVE" or after.identity != before.identity:
            status = "POST_EXIT" if after.state == "EXITED" else "IDENTITY_CHANGED"
            return False
        captures[-1] = CaptureRecord(stage=stage, identity=before.identity, live=True)
        return True

    def observe() -> str:
        nonlocal status
        try:
            ready = read("ready")
        except Exception as exc:
            if status not in ("LOG_SOURCE_MISMATCH", "LOG_MISSING", "LOG_UNREADABLE"):
                errors.append(f"ready:{type(exc).__name__}:{exc}")
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


def _serial_exec(
    *,
    run_dir: Path,
    label: str,
    command: str,
    serial_port: int,
) -> str:
    command_file = run_dir / f"FLR-0399-{label}.cmd"
    output_file = run_dir / f"FLR-0399-{label}.serial.log"
    harness_log = run_dir / f"FLR-0399-{label}.harness.log"
    for path in (command_file, output_file, harness_log):
        if path.exists():
            raise FileExistsError(f"evidence path already exists: {path.name}")
    command_file.write_text(command + "\n", encoding="utf-8")
    command_file.chmod(0o600)
    result = subprocess.run(
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
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=40,
    )
    harness_log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"serial-exec failed at {label}; see {harness_log.name}")
    if not output_file.is_file():
        raise RuntimeError(f"serial-exec produced no output at {label}")
    return output_file.read_text(encoding="utf-8", errors="replace")


def _capture_qmp(run_dir: Path, qmp: Path, label: str, *, video: bool) -> None:
    still = run_dir / f"FLR-0399-{label}.ppm"
    still_log = run_dir / f"FLR-0399-{label}.capture.log"
    if still.exists() or still_log.exists():
        raise FileExistsError(f"QMP capture evidence already exists for {label}")
    frames = run_dir / f"FLR-0399-{label}-frames"
    video_log = run_dir / f"FLR-0399-{label}-video.log"
    if video and (frames.exists() or video_log.exists()):
        raise FileExistsError(f"QMP video evidence already exists for {label}")
    result = subprocess.run(
        [sys.executable, str(PIXEL_CAPTURE), "capture", "--socket", str(qmp), "--output", str(still)],
        check=False,
        capture_output=True,
        text=True,
        timeout=35,
    )
    still_log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"QMP still capture failed at {label}")
    if video:
        result = subprocess.run(
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
            check=False,
            capture_output=True,
            text=True,
            timeout=35,
        )
        video_log.write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"QMP video-frame capture failed at {label}")


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
    commands = guest_commands(run_id)
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

    def serial(label: str, command: str) -> str:
        return _serial_exec(
            run_dir=run_dir,
            label=label,
            command=command,
            serial_port=args.serial_port,
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
        if qmp.is_socket():
            try:
                output = serial("stop", commands.stop)
                if "FLR0399_APP_STOP=" not in output:
                    teardown_errors.append("guest stop marker missing")
            except Exception as exc:
                teardown_errors.append(f"guest stop: {type(exc).__name__}")
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
                teardown_errors.append("QMP quit failed")
        if teardown_errors:
            raise RuntimeError("; ".join(teardown_errors))

    outcome: Outcome | None = None
    setup_error: str | None = None
    try:
        _capture_qmp(run_dir, qmp, "pre-launch", video=True)
        preflight = serial("preflight", commands.preflight)
        if "FLR0399_GUEST_PREFLIGHT=PASS" not in preflight:
            raise RuntimeError("guest preflight marker missing")
        launch = serial("launch", commands.launch)
        if "FLR0399_LAUNCH=PASS" not in launch:
            raise RuntimeError("guest launch marker missing")

        def read_state(stage: str, _remaining: float) -> Sample:
            command = getattr(commands, stage)
            return parse_state_output(serial(stage, command), stage=stage)

        def capture_frame(stage: str, _identity: Identity) -> None:
            _capture_qmp(run_dir, qmp, f"{run_id}-{stage.lower()}", video=stage == "READY")

        outcome = run_once(
            read_state=read_state,
            capture_frame=capture_frame,
            preserve_evidence=preserve_evidence,
            teardown=teardown,
            expected_log_path=commands.log_path,
            timeout_seconds=args.timeout_seconds,
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
    observe_parser.add_argument("--timeout-seconds", type=float, default=48.0)
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
