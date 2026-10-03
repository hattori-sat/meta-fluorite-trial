#!/usr/bin/env python3
"""Bounded guest snapshot for FLR-0416 identity/present/kernel correlation."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


RUN_ID = "flr0417-0001"
ROOT = "/run/user/1001/" + RUN_ID
BASELINE_PATH = ROOT + "-kernel-baseline.json"
MAX_LOG_BYTES = 10 * 1024 * 1024
FAULT = re.compile(
    r"Oops:|BUG: unable to handle|kernel BUG|Out of memory|Killed process|"
    r"general protection fault|segfault",
    re.IGNORECASE,
)
PRESENT_BEGIN = "FLR0026_VK_QUEUE_PRESENT_BEGIN"
PRESENT_RETURN = "FLR0026_VK_QUEUE_PRESENT result="


class SnapshotError(RuntimeError):
    pass


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def proc_identity(proc_root, pid):
    directory = Path(proc_root) / str(pid)
    try:
        comm = (directory / "comm").read_text(encoding="utf-8").strip()
        status = (directory / "status").read_text(encoding="utf-8")
        stat = (directory / "stat").read_text(encoding="utf-8")
    except OSError as error:
        raise SnapshotError("proc identity unavailable: " + type(error).__name__) from error
    uid_match = re.search(r"^Uid:\s+(\d+)", status, re.MULTILINE)
    if uid_match is None:
        raise SnapshotError("proc identity UID unavailable")
    stat_tail = stat.rsplit(")", 1)
    if len(stat_tail) != 2:
        raise SnapshotError("proc stat command delimiter is invalid")
    fields = stat_tail[1].split()
    if len(fields) <= 19:
        raise SnapshotError("proc start token unavailable")
    return {
        "pid": int(pid),
        "uid": int(uid_match.group(1)),
        "start_token": fields[19],
        "comm": comm,
        "state": fields[0],
    }


def parse_present_counts(log_text):
    begins = 0
    returns = 0
    successes = 0
    for line in log_text.splitlines():
        if PRESENT_BEGIN in line:
            begins += 1
        if PRESENT_RETURN in line:
            returns += 1
            result = line.split(PRESENT_RETURN, 1)[1].lstrip()
            if result == "0" or result.startswith("0 ") or result.startswith("0\t"):
                successes += 1
    return {"begin": begins, "return": returns, "success": successes}


def parse_kernel_faults(kernel_text):
    matches = [line[:500] for line in kernel_text.splitlines() if FAULT.search(line)]
    return len(matches), matches[-16:]


def _verify_journal_cursor(cursor, runner):
    command = [
        "journalctl",
        "-k",
        "-b",
        "--no-pager",
        "-o",
        "cat",
        "--cursor=" + cursor,
        "--lines=+1",
        "--show-cursor",
    ]
    try:
        result = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=6,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SnapshotError(
            "kernel journal cursor anchor query failed: " + type(error).__name__
        ) from error
    if result.returncode != 0 or result.stderr:
        raise SnapshotError("kernel journal cursor anchor query returned an error")
    if len(result.stdout.encode("utf-8")) > MAX_LOG_BYTES:
        raise SnapshotError("kernel journal cursor anchor exceeds bounded size")
    cursor_lines = [
        line for line in result.stdout.splitlines()
        if line.startswith("-- cursor: ")
    ]
    if len(cursor_lines) != 1:
        raise SnapshotError("kernel journal cursor anchor is missing or ambiguous")
    observed = cursor_lines[0][len("-- cursor: ") :]
    if observed != cursor:
        raise SnapshotError("kernel journal cursor resolved to a different entry")


def _run_journal(after_cursor=None, runner=subprocess.run):
    command = ["journalctl", "-k", "-b", "--no-pager", "-o", "short-iso"]
    if after_cursor is not None:
        if not after_cursor or len(after_cursor) > 512 or any(ch.isspace() for ch in after_cursor):
            raise SnapshotError("kernel journal cursor is malformed")
        _verify_journal_cursor(after_cursor, runner)
        command.append("--after-cursor=" + after_cursor)
    command.append("--show-cursor")
    try:
        result = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SnapshotError("kernel journal query failed: " + type(error).__name__) from error
    if result.returncode != 0 or result.stderr:
        raise SnapshotError("kernel journal query returned an error")
    if len(result.stdout.encode("utf-8")) > MAX_LOG_BYTES:
        raise SnapshotError("kernel journal exceeds bounded snapshot size")
    if after_cursor is not None:
        # Recheck after the read as well: if rotation removed the anchor while
        # the query was running, journalctl may have resumed at a nearby entry.
        _verify_journal_cursor(after_cursor, runner)
    cursor_lines = [
        line for line in result.stdout.splitlines()
        if line.startswith("-- cursor: ")
    ]
    if after_cursor is not None and not cursor_lines and result.stdout.splitlines() == ["-- No entries --"]:
        # The exact anchor was verified separately; no later kernel entry is
        # an explicit zero-new-record observation.
        return "", after_cursor, "NO_NEW_ENTRIES"
    if len(cursor_lines) != 1:
        raise SnapshotError("kernel journal cursor is missing or ambiguous")
    cursor = cursor_lines[0][len("-- cursor: ") :]
    if not cursor or len(cursor) > 512 or any(ch.isspace() for ch in cursor):
        raise SnapshotError("kernel journal returned a malformed cursor")
    lines = [line for line in result.stdout.splitlines() if line not in cursor_lines]
    if "-- No entries --" in lines:
        raise SnapshotError("kernel journal empty marker conflicts with returned cursor")
    return "\n".join(lines), cursor, "NEW_ENTRIES"


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SnapshotError("required JSON artifact unavailable: " + Path(path).name) from error


def write_kernel_baseline(
    *,
    root=ROOT,
    boot_id_path="/proc/sys/kernel/random/boot_id",
    journal_text=None,
    journal_cursor=None,
    journal_observation=None,
    now=None,
):
    if journal_text is None:
        journal_text, journal_cursor, journal_observation = _run_journal()
    if (
        not isinstance(journal_cursor, str)
        or not journal_cursor
        or len(journal_cursor) > 512
        or any(ch.isspace() for ch in journal_cursor)
    ):
        raise SnapshotError("kernel baseline cursor is missing or malformed")
    fault_count, matches = parse_kernel_faults(journal_text)
    try:
        boot_id = Path(boot_id_path).read_text(encoding="utf-8").strip()
    except OSError as error:
        raise SnapshotError("guest boot ID unavailable") from error
    if not boot_id:
        raise SnapshotError("guest boot ID empty")
    wall_ns = time.time_ns() if now is None else int(now)
    record = {
        "event": "KERNEL_BASELINE",
        "run_id": RUN_ID,
        "guest_boot_id": boot_id,
        "guest_wall_ns": wall_ns,
        "guest_monotonic_ns": time.monotonic_ns(),
        "fault_count": fault_count,
        "matches": matches,
        "journal_cursor": journal_cursor,
        "journal_observation": journal_observation or "NEW_ENTRIES",
    }
    path = Path(root + "-kernel-baseline.json")
    try:
        with path.open("xb") as stream:
            stream.write(canonical_json(record).encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as error:
        raise SnapshotError("kernel baseline create-only write failed") from error
    os.chmod(path, 0o600)
    return record


def _read_gdb_log(path):
    try:
        size = os.path.getsize(path)
        if size > MAX_LOG_BYTES:
            raise SnapshotError("GDB log exceeds bounded snapshot size")
        with open(path, "rb") as stream:
            content = stream.read(MAX_LOG_BYTES + 1)
    except OSError as error:
        raise SnapshotError("GDB log unavailable") from error
    if len(content) > MAX_LOG_BYTES:
        raise SnapshotError("GDB log exceeds bounded snapshot size")
    return content.decode("utf-8", errors="replace"), hashlib.sha256(content).hexdigest()


def _process_observation(proc_root, expected, expected_comm, allow_exited):
    try:
        actual = proc_identity(proc_root, expected["pid"])
    except SnapshotError:
        if allow_exited and not (Path(proc_root) / str(expected["pid"])).exists():
            return {"state": "EXITED", "expected": expected, "actual": None, "matches": False}
        raise
    matched = (
        actual["pid"] == expected["pid"]
        and actual["uid"] == expected["uid"]
        and actual["start_token"] == str(expected["start_token"])
        and actual["comm"] == expected_comm
    )
    matched = matched and actual["state"] not in ("Z", "X")
    if actual["state"] == "Z":
        state = "ZOMBIE"
    elif actual["state"] == "X":
        state = "DEAD"
    else:
        state = "LIVE" if matched else "IDENTITY_MISMATCH"
    return {
        "state": state,
        "expected": expected,
        "actual": actual,
        "matches": matched,
    }


def collect_snapshot(
    stage,
    *,
    root=ROOT,
    proc_root="/proc",
    boot_id_path="/proc/sys/kernel/random/boot_id",
    journal_text=None,
    now_wall_ns=None,
    now_monotonic_ns=None,
    allow_exited=False,
):
    if stage not in ("load", "hit", "post"):
        raise SnapshotError("snapshot stage is invalid")
    armed = _read_json(root + "-armed.json")
    expected = {
        "guest_boot_id": armed.get("guest_boot_id"),
        "process": armed.get("process"),
        "gdb_process": armed.get("gdb_process"),
    }
    if not expected["guest_boot_id"] or not isinstance(expected["process"], dict) or not isinstance(expected["gdb_process"], dict):
        raise SnapshotError("armed identity is incomplete")
    try:
        boot_id = Path(boot_id_path).read_text(encoding="utf-8").strip()
    except OSError as error:
        raise SnapshotError("guest boot ID unavailable") from error
    if boot_id != expected["guest_boot_id"]:
        raise SnapshotError("guest boot ID changed")

    baseline = _read_json(root + "-kernel-baseline.json")
    if baseline.get("guest_boot_id") != boot_id or baseline.get("event") != "KERNEL_BASELINE":
        raise SnapshotError("kernel baseline identity mismatch")
    if journal_text is None:
        kernel_text, journal_cursor_after, journal_observation = _run_journal(
            after_cursor=baseline.get("journal_cursor")
        )
    else:
        kernel_text, journal_cursor_after = journal_text, "TEST_INJECTED_CURSOR"
        journal_observation = "INJECTED"
    new_fault_count, matches = parse_kernel_faults(kernel_text)
    fault_count = baseline.get("fault_count", 0) + new_fault_count
    if fault_count < baseline.get("fault_count", -1):
        raise SnapshotError("kernel fault counter decreased; evidence window is ambiguous")

    log_text, log_sha = _read_gdb_log(root + "-log")
    process = _process_observation(proc_root, expected["process"], "flutter-auto", allow_exited)
    gdb_process = _process_observation(proc_root, expected["gdb_process"], "gdb", allow_exited)
    if not allow_exited and (not process["matches"] or not gdb_process["matches"]):
        raise SnapshotError("app or GDB process identity mismatch")
    record = {
        "event": "GUEST_RUNTIME_SNAPSHOT",
        "run_id": RUN_ID,
        "stage": stage,
        **expected,
        "guest_wall_ns": time.time_ns() if now_wall_ns is None else int(now_wall_ns),
        "guest_monotonic_ns": time.monotonic_ns() if now_monotonic_ns is None else int(now_monotonic_ns),
        "process_observation": process,
        "gdb_observation": gdb_process,
        "present": parse_present_counts(log_text),
        "gdb_log_sha256": log_sha,
        "kernel": {
            "baseline": baseline["fault_count"],
            "current": fault_count,
            "delta": new_fault_count,
            "matches": matches,
            "journal_cursor_after": journal_cursor_after,
            "journal_observation": journal_observation,
        },
    }
    return record


def _emit(record):
    raw = canonical_json(record).encode("utf-8")
    print("FLR0416_GUEST_SNAPSHOT=" + base64.b64encode(raw).decode("ascii"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    baseline = subparsers.add_parser("baseline")
    baseline.add_argument("--root", default=ROOT)
    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--stage", choices=("load", "hit", "post"), required=True)
    snapshot.add_argument("--allow-exited", action="store_true")
    snapshot.add_argument("--root", default=ROOT)
    args = parser.parse_args(argv)
    try:
        if args.operation == "baseline":
            record = write_kernel_baseline(root=args.root)
        else:
            record = collect_snapshot(args.stage, root=args.root, allow_exited=args.allow_exited)
        _emit(record)
        return 0
    except SnapshotError as error:
        print("FLR0416_GUEST_SNAPSHOT=FAIL reason=" + str(error).replace(" ", "_"), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
