#!/usr/bin/env python3
"""Bounded guest snapshot for FLR-0416 identity/present/kernel correlation."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import selectors
import subprocess
import sys
import time
from pathlib import Path


RUN_ID = "flr0421-0001"
ROOT = "/run/user/1001/" + RUN_ID
BASELINE_PATH = ROOT + "-kernel-baseline.json"
MAX_LOG_BYTES = 10 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024
MAX_CURSOR_BYTES = 512
JOURNAL_CHUNK_BYTES = 64 * 1024
MAX_FAULT_SUMMARIES = 16
JOURNAL_TIMEOUT_SECONDS = 10
ANCHOR_TIMEOUT_SECONDS = 6
EMPTY_MARKER = b"-- No entries --"
CURSOR_PREFIX = b"-- cursor: "
FAULT = re.compile(
    r"Oops:|BUG: unable to handle|kernel BUG|Out of memory|Killed process|"
    r"general protection fault|segfault",
    re.IGNORECASE,
)
PRESENT_BEGIN = "FLR0026_VK_QUEUE_PRESENT_BEGIN"
PRESENT_RETURN = "FLR0026_VK_QUEUE_PRESENT result="


class SnapshotError(RuntimeError):
    def __init__(self, message, diagnostics=None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


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


def _fault_summary(line):
    text = line.decode("utf-8", errors="replace")
    if not FAULT.search(text):
        return None
    if re.search(r"Oops:|kernel BUG|BUG:", text, re.IGNORECASE):
        category = "KERNEL_FAULT"
    elif re.search(r"Out of memory|Killed process", text, re.IGNORECASE):
        category = "MEMORY"
    else:
        category = "PROCESS_FAULT"
    return {
        "category": category,
        "line_bytes": len(line),
        "line_sha256": hashlib.sha256(line).hexdigest(),
    }


def parse_kernel_faults(kernel_text):
    matches = []
    for line in kernel_text.splitlines():
        summary = _fault_summary(line.encode("utf-8"))
        if summary is not None:
            matches.append(summary)
    return len(matches), matches[-MAX_FAULT_SUMMARIES:]


class _JournalStream:
    def __init__(self, max_line_bytes, retain_first_line=False):
        self.max_line_bytes = max_line_bytes
        self.retain_first_line = retain_first_line
        self.stdout_hash = hashlib.sha256()
        self.stderr_hash = hashlib.sha256()
        self.stdout_bytes = 0
        self.stderr_bytes = 0
        self.line_count = 0
        self.empty_marker_count = 0
        self.empty_marker_line = None
        self.cursor_count = 0
        self.cursor_line = None
        self.cursor_value = None
        self.cursor_malformed = False
        self.other_line_count = 0
        self.fault_count = 0
        self.fault_matches = []
        self.first_line = None
        self._line = bytearray()
        self.line_overflow = False

    def add_stderr(self, chunk):
        self.stderr_hash.update(chunk)
        self.stderr_bytes += len(chunk)

    def _consume_line(self, raw_line):
        line_number = self.line_count
        self.line_count += 1
        if self.retain_first_line and self.first_line is None:
            self.first_line = bytes(raw_line[:256])
        if raw_line == EMPTY_MARKER:
            self.empty_marker_count += 1
            if self.empty_marker_line is None:
                self.empty_marker_line = line_number
        elif raw_line.startswith(CURSOR_PREFIX):
            self.cursor_count += 1
            if self.cursor_line is None:
                self.cursor_line = line_number
            value = raw_line[len(CURSOR_PREFIX):]
            if (
                not value
                or len(value) > MAX_CURSOR_BYTES
                or any(byte < 33 or byte > 126 for byte in value)
            ):
                self.cursor_malformed = True
            elif self.cursor_count == 1:
                self.cursor_value = bytes(value)
        else:
            self.other_line_count += 1
        summary = _fault_summary(raw_line)
        if summary is not None:
            self.fault_count += 1
            self.fault_matches.append(summary)
            if len(self.fault_matches) > MAX_FAULT_SUMMARIES:
                del self.fault_matches[0]

    def add_stdout(self, chunk):
        self.stdout_hash.update(chunk)
        self.stdout_bytes += len(chunk)
        offset = 0
        while offset < len(chunk):
            newline = chunk.find(b"\n", offset)
            if newline < 0:
                fragment = chunk[offset:]
                if len(self._line) + len(fragment) > self.max_line_bytes:
                    self.line_overflow = True
                    return
                self._line.extend(fragment)
                return
            fragment = chunk[offset:newline]
            if len(self._line) + len(fragment) > self.max_line_bytes:
                self.line_overflow = True
                return
            self._line.extend(fragment)
            self._consume_line(bytes(self._line))
            self._line.clear()
            offset = newline + 1

    def finish(self, complete):
        if complete and self._line:
            self._consume_line(bytes(self._line))
            self._line.clear()


class JournalCommand:
    def __init__(
        self,
        stream,
        *,
        returncode,
        complete,
        timed_out=False,
        oversized=False,
        line_overflow=False,
        truncated=False,
        total_bytes_seen=0,
        reaped=True,
        collector_error=None,
    ):
        self.stream = stream
        self.returncode = returncode
        self.complete = complete
        self.timed_out = timed_out
        self.oversized = oversized
        self.line_overflow = line_overflow
        self.truncated = truncated
        self.total_bytes_seen = total_bytes_seen
        self.reaped = reaped
        self.collector_error = collector_error
        cursor = stream.cursor_value
        self.cursor_value = (
            cursor.decode("ascii") if cursor is not None and not stream.cursor_malformed else None
        )

    @property
    def stdout_bytes(self):
        return self.stream.stdout_bytes

    @property
    def stderr_bytes(self):
        return self.stream.stderr_bytes

    @property
    def stderr_empty(self):
        return self.stderr_bytes == 0

    @property
    def fault_count(self):
        return self.stream.fault_count

    @property
    def fault_matches(self):
        return list(self.stream.fault_matches)

    def summary(self, include_faults=True):
        result = {
            "returncode": self.returncode,
            "complete": self.complete,
            "timed_out": self.timed_out,
            "oversized": self.oversized,
            "line_overflow": self.line_overflow,
            "truncated": self.truncated,
            "reaped": self.reaped,
            "collector_error": self.collector_error,
            "total_bytes_seen": self.total_bytes_seen,
            "stdout_bytes": self.stdout_bytes,
            "stdout_sha256": self.stream.stdout_hash.hexdigest(),
            "stderr_bytes": self.stderr_bytes,
            "stderr_sha256": self.stream.stderr_hash.hexdigest(),
            "stderr_empty": self.stderr_empty,
            "stdout_line_count": self.stream.line_count,
            "empty_marker_count": self.stream.empty_marker_count,
            "empty_marker_line": self.stream.empty_marker_line,
            "cursor_count": self.stream.cursor_count,
            "cursor_line": self.stream.cursor_line,
            "cursor_malformed": self.stream.cursor_malformed,
            "cursor_sha256": (
                hashlib.sha256(self.stream.cursor_value).hexdigest()
                if self.stream.cursor_count == 1
                and self.stream.cursor_value is not None
                and not self.stream.cursor_malformed
                else None
            ),
            "other_line_count": self.stream.other_line_count,
            "fault_count": self.fault_count,
        }
        if include_faults:
            result["fault_matches"] = self.fault_matches
        return result


def _result_from_runner(
    command, timeout, max_output_bytes, max_line_bytes, runner, retain_first_line
):
    stream = _JournalStream(max_line_bytes, retain_first_line=retain_first_line)
    try:
        result = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        if isinstance(stdout, str):
            stdout = stdout.encode("utf-8")
        if isinstance(stderr, str):
            stderr = stderr.encode("utf-8")
        stream.add_stdout(stdout[:max_output_bytes + 1])
        stream.add_stderr(stderr[:max_output_bytes + 1])
        total = min(len(stdout) + len(stderr), max_output_bytes + 1)
        return JournalCommand(
            stream,
            returncode=None,
            complete=False,
            timed_out=True,
            truncated=True,
            total_bytes_seen=total,
            collector_error="TimeoutExpired",
        )
    except OSError as error:
        return JournalCommand(
            stream,
            returncode=None,
            complete=False,
            truncated=True,
            collector_error=type(error).__name__,
        )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if isinstance(stdout, str):
        stdout = stdout.encode("utf-8")
    if isinstance(stderr, str):
        stderr = stderr.encode("utf-8")
    total = len(stdout) + len(stderr)
    budget = max_output_bytes + 1
    stdout_part = stdout[:budget]
    stream.add_stdout(stdout_part)
    remaining = max(0, budget - len(stdout_part))
    stream.add_stderr(stderr[:remaining])
    oversized = total > max_output_bytes
    line_overflow = stream.line_overflow
    truncated = oversized or line_overflow
    stream.finish(complete=not truncated)
    return JournalCommand(
        stream,
        returncode=result.returncode,
        complete=not truncated,
        oversized=oversized,
        line_overflow=line_overflow,
        truncated=truncated,
        total_bytes_seen=min(total, budget),
        collector_error=None,
    )


def _stop_and_reap(process):
    if process.poll() is None:
        try:
            process.terminate()
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                return False
    return process.poll() is not None


def _collect_bounded_command(
    command,
    *,
    timeout=JOURNAL_TIMEOUT_SECONDS,
    max_output_bytes=MAX_LOG_BYTES,
    max_line_bytes=MAX_LINE_BYTES,
    retain_first_line=False,
    runner=None,
):
    if runner is not None:
        return _result_from_runner(
            command,
            timeout,
            max_output_bytes,
            max_line_bytes,
            runner,
            retain_first_line,
        )

    stream = _JournalStream(max_line_bytes, retain_first_line=retain_first_line)
    selector = selectors.DefaultSelector()
    process = None
    total = 0
    timed_out = False
    oversized = False
    line_overflow = False
    collector_error = None
    deadline = time.monotonic() + timeout
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            close_fds=True,
        )
        for name, pipe in (("stdout", process.stdout), ("stderr", process.stderr)):
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, name)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            events = selector.select(min(remaining, 0.1))
            for key, _ in events:
                available = max_output_bytes - total
                read_size = min(JOURNAL_CHUNK_BYTES, max(1, available + 1))
                try:
                    chunk = os.read(key.fileobj.fileno(), read_size)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                total += len(chunk)
                if key.data == "stdout":
                    stream.add_stdout(chunk)
                    line_overflow = stream.line_overflow
                else:
                    stream.add_stderr(chunk)
                if total > max_output_bytes:
                    oversized = True
                    break
                if line_overflow:
                    break
            if timed_out or oversized or line_overflow:
                break
        if not timed_out and not oversized and not line_overflow:
            remaining = max(0, deadline - time.monotonic())
            try:
                process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timed_out = True
    except OSError as error:
        collector_error = type(error).__name__
    finally:
        if process is not None and process.poll() is None:
            reaped = _stop_and_reap(process)
        elif process is not None:
            reaped = process.poll() is not None
        else:
            reaped = False
        for key in list(selector.get_map().values()):
            try:
                selector.unregister(key.fileobj)
            except Exception:
                pass
            try:
                key.fileobj.close()
            except OSError:
                pass
        selector.close()

    returncode = process.returncode if process is not None else None
    truncated = timed_out or oversized or line_overflow or collector_error is not None
    complete = (
        not truncated
        and reaped
        and not selector.get_map()
        and returncode is not None
    )
    stream.finish(complete=complete)
    return JournalCommand(
        stream,
        returncode=returncode,
        complete=complete,
        timed_out=timed_out,
        oversized=oversized,
        line_overflow=line_overflow,
        truncated=truncated,
        total_bytes_seen=total,
        reaped=reaped,
        collector_error=collector_error,
    )


class JournalResult:
    def __init__(self, fault_count, fault_matches, cursor, observation, diagnostics):
        self.fault_count = fault_count
        self.fault_matches = fault_matches
        self.cursor = cursor
        self.observation = observation
        self.diagnostics = diagnostics


def _journalctl_version(runner=None):
    result = _collect_bounded_command(
        ["journalctl", "--version"],
        timeout=2,
        max_output_bytes=1024,
        max_line_bytes=256,
        retain_first_line=True,
        runner=runner,
    )
    if (
        not result.complete
        or result.returncode != 0
        or not result.stderr_empty
        or result.stream.first_line is None
    ):
        return "UNKNOWN"
    line = result.stream.first_line.decode("ascii", errors="replace")
    match = re.match(r"^systemd\s+([0-9]+(?:\.[0-9]+)*)\b", line)
    return "systemd-" + match.group(1) if match else "UNKNOWN"


def _verify_journal_cursor(cursor, runner, diagnostics, label):
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
    result = _collect_bounded_command(
        command,
        timeout=ANCHOR_TIMEOUT_SECONDS,
        runner=runner,
    )
    exact = (
        result.complete
        and result.returncode == 0
        and result.stderr_empty
        and not result.collector_error
        and result.stream.cursor_count == 1
        and not result.stream.cursor_malformed
        and result.cursor_value == cursor
    )
    summary = result.summary(include_faults=False)
    summary["cursor_equal_anchor"] = (
        result.cursor_value == cursor if result.stream.cursor_count == 1 else None
    )
    summary["exact_anchor"] = exact
    diagnostics["anchor_" + label] = summary
    if not exact:
        raise SnapshotError(
            "kernel journal cursor anchor did not resolve exactly",
            diagnostics=diagnostics,
        )
    return True


def _run_journal(after_cursor=None, runner=None):
    diagnostics = {
        "collector": "flr0421-bounded-v1",
        "systemd_version": _journalctl_version(runner) if runner is None else "TEST",
    }
    if after_cursor is not None:
        try:
            cursor_bytes = after_cursor.encode("ascii")
        except (AttributeError, UnicodeEncodeError) as error:
            raise SnapshotError("kernel journal cursor is malformed") from error
        if (
            not cursor_bytes
            or len(cursor_bytes) > MAX_CURSOR_BYTES
            or any(byte < 33 or byte > 126 for byte in cursor_bytes)
        ):
            raise SnapshotError("kernel journal cursor is malformed")
        diagnostics["baseline_cursor_sha256"] = hashlib.sha256(cursor_bytes).hexdigest()
        _verify_journal_cursor(after_cursor, runner, diagnostics, "before")

    command = ["journalctl", "-k", "-b", "--no-pager", "-o", "short-iso"]
    if after_cursor is not None:
        command.append("--after-cursor=" + after_cursor)
    command.append("--show-cursor")
    result = _collect_bounded_command(command, runner=runner)
    query = result.summary()
    query["classification"] = "UNCLASSIFIED"
    if after_cursor is not None and result.stream.cursor_count == 1:
        query["cursor_equal_anchor"] = result.cursor_value == after_cursor
    else:
        query["cursor_equal_anchor"] = None
    diagnostics["query"] = query

    if after_cursor is not None:
        _verify_journal_cursor(after_cursor, runner, diagnostics, "after")

    if (
        not result.complete
        or result.returncode != 0
        or not result.stderr_empty
        or result.collector_error
        or not result.reaped
    ):
        raise SnapshotError(
            "kernel journal query was incomplete or returned an error",
            diagnostics=diagnostics,
        )
    if result.stream.cursor_malformed:
        raise SnapshotError("kernel journal returned a malformed cursor", diagnostics)

    if result.stream.empty_marker_count:
        exact_empty = (
            result.stream.empty_marker_count == 1
            and result.stream.empty_marker_line == 0
            and result.stream.other_line_count == 0
        )
        if not exact_empty or after_cursor is None:
            query["classification"] = "INVALID_EMPTY_RESULT"
            raise SnapshotError(
                "kernel journal empty result was not exact",
                diagnostics=diagnostics,
            )
        if result.stream.cursor_count == 0 and result.stream.line_count == 1:
            query["classification"] = "NO_NEW_ENTRIES_NO_CURSOR"
            return JournalResult(
                0,
                [],
                after_cursor,
                "NO_NEW_ENTRIES",
                diagnostics,
            )
        if (
            result.stream.cursor_count == 1
            and result.stream.line_count == 2
            and result.stream.cursor_line == 1
            and result.cursor_value == after_cursor
        ):
            query["classification"] = "NO_NEW_ENTRIES_EQUAL_CURSOR"
            return JournalResult(
                0,
                [],
                after_cursor,
                "NO_NEW_ENTRIES",
                diagnostics,
            )
        query["classification"] = "INVALID_EMPTY_CURSOR"
        raise SnapshotError(
            "kernel journal empty marker cursor did not equal the verified anchor",
            diagnostics=diagnostics,
        )

    if result.stream.cursor_count != 1 or result.cursor_value is None:
        query["classification"] = "INVALID_CURSOR_COUNT"
        raise SnapshotError(
            "kernel journal cursor is missing or ambiguous",
            diagnostics=diagnostics,
        )
    query["classification"] = "NEW_ENTRIES"
    return JournalResult(
        result.fault_count,
        result.fault_matches,
        result.cursor_value,
        "NEW_ENTRIES",
        diagnostics,
    )


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
    journal_diagnostics = {}
    if journal_text is None:
        journal = _run_journal()
        journal_cursor = journal.cursor
        journal_observation = journal.observation
        fault_count, matches = journal.fault_count, journal.fault_matches
        journal_diagnostics = journal.diagnostics
    else:
        fault_count, matches = parse_kernel_faults(journal_text)
        journal_diagnostics = {
            "collector": "test-injected",
            "classification": journal_observation or "NEW_ENTRIES",
        }
    if (
        not isinstance(journal_cursor, str)
        or not journal_cursor
        or len(journal_cursor) > 512
        or any(ch.isspace() for ch in journal_cursor)
    ):
        raise SnapshotError("kernel baseline cursor is missing or malformed")
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
        "journal_diagnostics": journal_diagnostics,
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
        journal = _run_journal(after_cursor=baseline.get("journal_cursor"))
        journal_cursor_after = journal.cursor
        journal_observation = journal.observation
        new_fault_count, matches = journal.fault_count, journal.fault_matches
        journal_diagnostics = journal.diagnostics
    else:
        journal_cursor_after = "TEST_INJECTED_CURSOR"
        journal_observation = "INJECTED"
        new_fault_count, matches = parse_kernel_faults(journal_text)
        journal_diagnostics = {"collector": "test-injected"}
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
            "journal_cursor_after_sha256": hashlib.sha256(
                journal_cursor_after.encode("ascii")
            ).hexdigest(),
            "journal_observation": journal_observation,
            "journal_diagnostics": journal_diagnostics,
        },
    }
    return record


def _emit(record):
    public = dict(record)
    cursor = public.pop("journal_cursor", None)
    if isinstance(cursor, str):
        public["journal_cursor_sha256"] = hashlib.sha256(
            cursor.encode("ascii")
        ).hexdigest()
    raw = canonical_json(public).encode("utf-8")
    print("FLR0416_GUEST_SNAPSHOT=" + base64.b64encode(raw).decode("ascii"))


def _failure_marker(error):
    message = str(error)
    reason_codes = {
        "kernel journal cursor anchor did not resolve exactly": "journal_anchor_unresolved",
        "kernel journal cursor is malformed": "journal_cursor_malformed",
        "kernel journal returned a malformed cursor": "journal_cursor_malformed",
        "kernel journal query was incomplete or returned an error": "journal_query_incomplete",
        "kernel journal empty result was not exact": "journal_empty_result_invalid",
        "kernel journal empty marker cursor did not equal the verified anchor": "journal_empty_cursor_mismatch",
        "kernel journal cursor is missing or ambiguous": "journal_cursor_missing_or_ambiguous",
    }
    safe_codes = set(reason_codes.values()) | {"snapshot_failed"}
    reason = reason_codes.get(message, message if message in safe_codes else "snapshot_failed")
    diagnostics = canonical_json(error.diagnostics).encode("utf-8")
    encoded = base64.b64encode(diagnostics).decode("ascii")
    return "FLR0416_GUEST_SNAPSHOT=FAIL reason=" + reason + " diagnostics=" + encoded


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
        print(_failure_marker(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
