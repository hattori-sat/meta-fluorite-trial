#!/usr/bin/env python3
"""Safely stop only QEMU/runqemu processes that own one FLR-0399 QMP path."""

from __future__ import annotations

import argparse
import os
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    start_time: int
    comm: str
    argv: tuple[str, ...]

    @property
    def description(self) -> str:
        return f"pid={self.pid} start={self.start_time} comm={self.comm} args={' '.join(self.argv)[:300]}"


@dataclass(frozen=True)
class CleanupResult:
    remaining: tuple[ProcessIdentity, ...]
    errors: tuple[str, ...]
    qmp_socket_removed: bool


def _qmp_endpoints(argv: tuple[str, ...], *, is_runqemu: bool) -> set[str]:
    endpoints: set[str] = set()

    def add_qmp_value(value: str) -> None:
        if value.startswith("unix:"):
            endpoints.add(value[len("unix:") :].split(",", 1)[0])

    for index, argument in enumerate(argv):
        if argument == "-qmp" and index + 1 < len(argv):
            add_qmp_value(argv[index + 1])
        elif argument.startswith("-qmp="):
            add_qmp_value(argument[len("-qmp=") :])
        elif argument == "-chardev" and index + 1 < len(argv):
            chardev = argv[index + 1]
            if chardev.startswith("socket,"):
                fields = chardev.split(",")[1:]
                if "id=qmp" in fields:
                    for field in fields:
                        if field.startswith("path="):
                            endpoints.add(field[len("path=") :])

        if is_runqemu and argument.startswith("qmp=unix:"):
            add_qmp_value(argument[len("qmp=") :])
    return endpoints


def _read_process(proc_dir: Path, qmp_path: str) -> ProcessIdentity | None:
    try:
        comm = (proc_dir / "comm").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    try:
        raw_argv = (proc_dir / "cmdline").read_bytes()
    except PermissionError:
        if comm.startswith("qemu-system-") or comm == "runqemu":
            raise
        return None
    try:
        stat_text = (proc_dir / "stat").read_text(encoding="utf-8")
    except FileNotFoundError:
        return None

    argv = tuple(os.fsdecode(item) for item in raw_argv.split(b"\0") if item)
    if not argv:
        return None
    executable = Path(argv[0]).name
    is_qemu = executable.startswith("qemu-system-")
    interpreter = executable in {"python", "python2", "python3"} or executable.startswith(
        ("python2.", "python3.")
    )
    is_runqemu = executable == "runqemu" or (
        interpreter and len(argv) > 1 and Path(argv[1]).name == "runqemu"
    )
    if not (is_qemu or is_runqemu):
        return None
    if qmp_path not in _qmp_endpoints(argv, is_runqemu=is_runqemu):
        return None

    close_paren = stat_text.rfind(")")
    if close_paren < 0:
        raise ValueError(f"malformed proc stat for pid {proc_dir.name}")
    stat_fields = stat_text[close_paren + 1 :].split()
    if len(stat_fields) <= 19 or not stat_fields[19].isdigit():
        raise ValueError(f"missing start-time token for pid {proc_dir.name}")
    return ProcessIdentity(
        pid=int(proc_dir.name),
        start_time=int(stat_fields[19]),
        comm=comm,
        argv=argv,
    )


def _scan(proc_root: Path, qmp_path: str) -> tuple[list[ProcessIdentity], list[str]]:
    found: list[ProcessIdentity] = []
    errors: list[str] = []
    try:
        entries = tuple(proc_root.iterdir())
    except OSError as exc:
        return [], [f"proc-scan-failed:{type(exc).__name__}"]

    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            process = _read_process(entry, qmp_path)
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(f"proc-read-failed:{entry.name}:{type(exc).__name__}")
            continue
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if process is not None:
            found.append(process)
    return found, errors


def _same_identity(proc_root: Path, original: ProcessIdentity, qmp_path: str) -> tuple[bool, bool]:
    """Return (same exact process, pid now identifies a different QMP owner)."""
    try:
        current = _read_process(proc_root / str(original.pid), qmp_path)
    except FileNotFoundError:
        return False, False
    except OSError:
        return False, False
    if current is None:
        return False, False
    if current.start_time != original.start_time:
        return False, True
    return current.comm == original.comm and current.argv == original.argv, False


def cleanup_exact_qmp_processes(
    qmp: Path,
    *,
    proc_root: Path = Path("/proc"),
    timeout_seconds: float = 3.0,
    pidfd_open: Callable[[int, int], int] | None = None,
    pidfd_sender: Callable[[int, int], None] | None = None,
    fd_closer: Callable[[int], None] = os.close,
    sleeper: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> CleanupResult:
    """TERM, then KILL only unchanged QEMU identities carrying this QMP path."""
    if not qmp.is_absolute():
        raise ValueError("QMP path must be absolute")
    if timeout_seconds <= 0:
        raise ValueError("cleanup timeout must be positive")

    qmp_path = str(qmp)
    initial, scan_errors = _scan(proc_root, qmp_path)
    errors = list(scan_errors)
    if initial:
        pidfd_open = pidfd_open or getattr(os, "pidfd_open", None)
        pidfd_sender = pidfd_sender or getattr(signal, "pidfd_send_signal", None)
        if pidfd_open is None or pidfd_sender is None:
            return CleanupResult(
                tuple(initial), tuple(errors + ["pidfd-capability-unavailable"]), False
            )

    pidfds: dict[int, int] = {}
    try:
        for process in initial:
            try:
                pidfd = pidfd_open(process.pid, 0)
            except ProcessLookupError:
                continue
            except OSError as exc:
                errors.append(f"pidfd-open-failed:{process.pid}:{type(exc).__name__}")
                continue
            current, changed = _same_identity(proc_root, process, qmp_path)
            if changed:
                errors.append(f"pid-identity-changed:{process.pid}")
                fd_closer(pidfd)
                continue
            if not current:
                fd_closer(pidfd)
                continue
            pidfds[process.pid] = pidfd
            try:
                pidfd_sender(pidfd, signal.SIGTERM)
            except ProcessLookupError:
                continue
            except OSError as exc:
                errors.append(f"term-failed:{process.pid}:{type(exc).__name__}")

        deadline = monotonic() + timeout_seconds
        pending: list[ProcessIdentity] = []
        while True:
            pending = []
            for process in initial:
                if process.pid not in pidfds:
                    continue
                same, changed = _same_identity(proc_root, process, qmp_path)
                if changed:
                    marker = f"pid-identity-changed:{process.pid}"
                    if marker not in errors:
                        errors.append(marker)
                elif same:
                    pending.append(process)
            if not pending or monotonic() >= deadline:
                break
            sleeper(min(0.1, max(0.0, deadline - monotonic())))

        for process in pending:
            same, changed = _same_identity(proc_root, process, qmp_path)
            if changed:
                marker = f"pid-identity-changed:{process.pid}"
                if marker not in errors:
                    errors.append(marker)
                continue
            if not same:
                continue
            try:
                pidfd_sender(pidfds[process.pid], signal.SIGKILL)
            except ProcessLookupError:
                continue
            except OSError as exc:
                errors.append(f"kill-failed:{process.pid}:{type(exc).__name__}")

        grace_deadline = monotonic() + min(1.0, timeout_seconds)
        while True:
            remaining = []
            for process in initial:
                if process.pid not in pidfds:
                    continue
                same, changed = _same_identity(proc_root, process, qmp_path)
                if changed:
                    marker = f"pid-identity-changed:{process.pid}"
                    if marker not in errors:
                        errors.append(marker)
                elif same:
                    remaining.append(process)
            if not remaining or monotonic() >= grace_deadline:
                break
            sleeper(min(0.1, max(0.0, grace_deadline - monotonic())))

        current, final_scan_errors = _scan(proc_root, qmp_path)
        errors.extend(error for error in final_scan_errors if error not in errors)
        remaining = current

        socket_removed = False
        if not remaining and not errors:
            if qmp.is_symlink():
                errors.append("qmp-path-is-symlink")
            elif qmp.exists():
                if qmp.is_socket():
                    try:
                        qmp.unlink()
                        socket_removed = True
                    except OSError as exc:
                        errors.append(f"stale-qmp-unlink-failed:{type(exc).__name__}")
                else:
                    errors.append("qmp-path-exists-and-is-not-socket")

        return CleanupResult(tuple(remaining), tuple(errors), socket_removed)
    finally:
        for pidfd in pidfds.values():
            try:
                fd_closer(pidfd)
            except OSError:
                pass


def pidfd_capability() -> tuple[bool, str]:
    opener = getattr(os, "pidfd_open", None)
    sender = getattr(signal, "pidfd_send_signal", None)
    if opener is None or sender is None:
        return False, "python-pidfd-api-unavailable"
    pidfd = None
    try:
        pidfd = opener(os.getpid(), 0)
        sender(pidfd, 0)
        return True, "pidfd-open-and-signal0-pass"
    except OSError as exc:
        return False, f"pidfd-self-probe-failed:{type(exc).__name__}"
    finally:
        if pidfd is not None:
            os.close(pidfd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qmp", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=3.0)
    parser.add_argument("--check-capability", action="store_true")
    args = parser.parse_args(argv)
    if args.check_capability:
        available, reason = pidfd_capability()
        print(f"FLR0399_PIDFD={'PASS' if available else 'FAIL'} reason={reason}")
        return 0 if available else 1
    if args.qmp is None:
        parser.error("--qmp is required unless --check-capability is used")
    try:
        result = cleanup_exact_qmp_processes(
            args.qmp,
            timeout_seconds=args.timeout_seconds,
        )
    except Exception as exc:
        print(f"FLR0399_EXACT_CLEANUP=FAIL reason={type(exc).__name__}:{exc}")
        return 2

    for process in result.remaining:
        print(f"residual={process.description}")
    for error in result.errors:
        print(f"error={error}")
    print(
        "FLR0399_EXACT_CLEANUP="
        f"{'PASS' if not result.remaining and not result.errors else 'FAIL'} "
        f"residual={len(result.remaining)} qmp_socket_removed={str(result.qmp_socket_removed).lower()}"
    )
    return 0 if not result.remaining and not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
