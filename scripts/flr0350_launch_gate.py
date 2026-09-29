#!/usr/bin/env python3
"""Validate the FLR-0350 guest's blocked-read FIFO observation fail-closed."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Sequence

GATE_MARKER = "FLR0350_GATE_OBSERVATION"
LAUNCH_MARKER = "FLR0350_LAUNCH_WRAPPER=READY"
PROC_STAT_START_AWK = r'{sub(/^.*\) /,""); print $20}'
LAUNCH_FIELDS = frozenset({"pid", "start", "uid", "comm"})
REQUIRED_FIELDS = frozenset(
    {
        "version",
        "run_id",
        "identity_record",
        "identity_pid",
        "identity_start",
        "identity_uid",
        "identity_dev",
        "identity_ino",
        "pid",
        "start",
        "start_after",
        "recorded_start",
        "uid",
        "comm",
        "state",
        "tracer",
        "syscall",
        "nr",
        "arg1",
        "target_type",
        "target_dev",
        "target_ino",
        "gate_type",
        "gate_dev",
        "gate_ino",
        "gate_uid",
        "gate_mode",
    }
)
RUN_ID_PATTERN = re.compile(r"flr[0-9]{4}-[0-9]{4}\Z")
CONSUMED_RUN_IDS = frozenset({"flr0350-0001"})


class GateObservationError(ValueError):
    """A missing, ambiguous, malformed, or unsafe guest observation."""


def _parse_marker(
    output: str, marker: str, expected_fields: frozenset[str]
) -> dict[str, str]:
    marker_lines = [line for line in output.splitlines() if marker in line]
    if not marker_lines:
        raise GateObservationError("marker-missing")
    if len(marker_lines) != 1:
        raise GateObservationError("marker-duplicate")

    tokens = marker_lines[0].split()
    if not tokens or tokens[0] != marker:
        raise GateObservationError("marker-not-first")

    fields: dict[str, str] = {}
    for token in tokens[1:]:
        if token.count("=") != 1:
            raise GateObservationError("malformed-field")
        key, value = token.split("=", 1)
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or not value:
            raise GateObservationError("malformed-field")
        if key in fields:
            raise GateObservationError("duplicate-field")
        if key not in expected_fields:
            raise GateObservationError("unknown-field")
        fields[key] = value

    if fields.keys() != expected_fields:
        raise GateObservationError("required-field-missing")
    return fields


def is_fresh_run_id(value: str) -> bool:
    """Accept a ticket-shaped ID only if it is not already consumed here."""
    return bool(RUN_ID_PATTERN.fullmatch(value)) and value not in CONSUMED_RUN_IDS


def render_identity_init_command(run_id: str) -> str:
    """Create a root-owned run directory and exclusive run-ID marker on guest."""
    if not is_fresh_run_id(run_id):
        raise GateObservationError("invalid-or-consumed-run-id")
    quoted_run_id = "'" + run_id + "'"
    return (
        '(umask 077; d=/run/flr0350; '
        'if [ -e "$d" ] || [ -L "$d" ]; then '
        'echo FLR0350_RUN_ID_INIT=FAIL reason=collision; '
        'elif mkdir -m 700 "$d" '
        '&& [ "$(stat -c \'%u:%a\' "$d" 2>/dev/null)" = 0:700 ] '
        '&& (set -C; printf \'%s\\n\' '
        + quoted_run_id
        + ' > "$d/run.id") && [ -f "$d/run.id" ] '
        '&& [ ! -L "$d/run.id" ] '
        '&& [ "$(stat -c \'%u:%a\' "$d/run.id" 2>/dev/null)" = 0:600 ] '
        '&& [ "$(cat "$d/run.id" 2>/dev/null)" = '
        + quoted_run_id
        + ' ]; then echo FLR0350_RUN_ID_INIT=PASS; '
        'else echo FLR0350_RUN_ID_INIT=FAIL reason=init; fi)'
    )


def _unsigned(value: str, field: str) -> int:
    if re.fullmatch(r"0x[0-9a-fA-F]+", value):
        return int(value[2:], 16)
    if re.fullmatch(r"[0-9]+", value):
        return int(value, 10)
    raise GateObservationError("invalid-number-" + field)


def validate_gate_output(
    output: str, expected_run_id: str | None = None
) -> dict[str, str]:
    """Parse and validate the exact observation consumed by the host runner."""
    launch = _parse_marker(output, LAUNCH_MARKER, LAUNCH_FIELDS)
    fields = _parse_marker(output, GATE_MARKER, REQUIRED_FIELDS)

    if fields["version"] != "2":
        raise GateObservationError("unsupported-version")
    if not is_fresh_run_id(fields["run_id"]):
        raise GateObservationError("invalid-or-consumed-run-id")
    if expected_run_id is not None and fields["run_id"] != expected_run_id:
        raise GateObservationError("run-id-mismatch")
    if fields["identity_record"] != "PASS":
        raise GateObservationError("identity-record-not-passed")
    pid = _unsigned(fields["pid"], "pid")
    start = _unsigned(fields["start"], "start")
    start_after = _unsigned(fields["start_after"], "start_after")
    recorded_start = _unsigned(fields["recorded_start"], "recorded_start")
    launch_pid = _unsigned(launch["pid"], "launch_pid")
    launch_start = _unsigned(launch["start"], "launch_start")
    uid = _unsigned(fields["uid"], "uid")
    tracer = _unsigned(fields["tracer"], "tracer")
    syscall_number = _unsigned(fields["nr"], "nr")
    actual_read_fd = _unsigned(fields["arg1"], "arg1")
    target_device = _unsigned(fields["target_dev"], "target_dev")
    target_inode = _unsigned(fields["target_ino"], "target_ino")
    gate_device = _unsigned(fields["gate_dev"], "gate_dev")
    gate_inode = _unsigned(fields["gate_ino"], "gate_ino")
    gate_uid = _unsigned(fields["gate_uid"], "gate_uid")
    identity_pid = _unsigned(fields["identity_pid"], "identity_pid")
    identity_start = _unsigned(fields["identity_start"], "identity_start")
    identity_uid = _unsigned(fields["identity_uid"], "identity_uid")
    identity_device = _unsigned(fields["identity_dev"], "identity_dev")
    identity_inode = _unsigned(fields["identity_ino"], "identity_ino")

    if (
        pid == 0
        or start == 0
        or start != start_after
        or start != recorded_start
        or pid != launch_pid
        or start != launch_start
        or fields["uid"] != launch["uid"]
        or fields["comm"] != launch["comm"]
    ):
        raise GateObservationError("process-identity-unstable")
    if (identity_pid, identity_start, identity_uid) != (pid, start, uid):
        raise GateObservationError("persisted-process-identity-mismatch")
    if (identity_device, identity_inode) != (gate_device, gate_inode):
        raise GateObservationError("persisted-fifo-identity-mismatch")
    if uid != 1001 or fields["comm"] != "sh" or fields["state"] != "S":
        raise GateObservationError("wrapper-identity-mismatch")
    if tracer != 0:
        raise GateObservationError("wrapper-already-traced")
    if fields["syscall"] != "read" or syscall_number != 0:
        raise GateObservationError("syscall-mismatch")
    # The descriptor number is intentionally not fixed: validate the object it
    # actually names, not an assumed FD such as 0 or 3.
    if actual_read_fd < 0:
        raise GateObservationError("invalid-read-fd")
    if fields["target_type"] != "fifo" or fields["gate_type"] != "fifo":
        raise GateObservationError("not-a-fifo")
    if (target_device, target_inode) != (gate_device, gate_inode):
        raise GateObservationError("fifo-object-mismatch")
    if gate_uid != 1001 or fields["gate_mode"] != "600":
        raise GateObservationError("gate-ownership-mismatch")

    return fields


def extract_proc_stat_starttime(stat_line: str) -> str:
    """Use the same last-comm-delimiter AWK expression embedded in guest cmds."""
    try:
        result = subprocess.run(
            ["awk", PROC_STAT_START_AWK],
            input=stat_line,
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("proc-stat-parser-failed") from exc
    values = result.stdout.split()
    if len(values) != 1 or not re.fullmatch(r"[0-9]+", values[0]):
        raise ValueError("proc-stat-starttime-invalid")
    return values[0]


def _usage() -> int:
    print(
        "usage: flr0350_launch_gate.py --validate <run-id> <launch-log> <gate-log> "
        "| --check-run-id <id>",
        file=sys.stderr,
    )
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == "--check-run-id":
        if not is_fresh_run_id(args[1]):
            print("FLR0350_RUN_ID=REJECTED reason=invalid-or-consumed")
            return 2
        print("FLR0350_RUN_ID=PASS")
        return 0
    if len(args) == 2 and args[0] == "--render-identity-init":
        try:
            print(render_identity_init_command(args[1]))
        except GateObservationError as exc:
            print("FLR0350_RUN_ID_INIT=REJECTED reason=" + str(exc))
            return 2
        return 0
    if len(args) == 4 and args[0] == "--validate":
        try:
            expected_run_id = args[1]
            if not is_fresh_run_id(expected_run_id):
                raise GateObservationError("invalid-or-consumed-run-id")
            output = "\n".join(
                Path(path).read_text(encoding="utf-8") for path in args[2:]
            )
            fields = validate_gate_output(output, expected_run_id=expected_run_id)
        except (OSError, UnicodeError):
            print("FLR0350_FIFO_READ_GATE=FAIL reason=observation-unavailable")
            return 2
        except GateObservationError as exc:
            print("FLR0350_FIFO_READ_GATE=FAIL reason=" + str(exc))
            return 1
        print(
            "FLR0350_FIFO_READ_GATE=PASS"
            + " run_id="
            + fields["run_id"]
            + " pid="
            + fields["pid"]
            + " start="
            + fields["start"]
            + " read_fd="
            + str(_unsigned(fields["arg1"], "arg1"))
            + " gate_dev="
            + fields["gate_dev"]
            + " gate_ino="
            + fields["gate_ino"]
        )
        return 0
    return _usage()


if __name__ == "__main__":
    raise SystemExit(main())
