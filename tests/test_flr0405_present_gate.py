#!/usr/bin/env python3
"""Focused regression tests for the FLR-0405 guest present gate."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "work/commands/FLR-0405-guest-live-gate.cmd"
MONITOR = ROOT / "work/commands/FLR-0405-guest-monitor-first-boundary.cmd"


def fixture_log() -> str:
    begin = lambda i: (
        f"FLR0026_VK_QUEUE_PRESENT_BEGIN queue=q swapchain=s index={i}"
    )
    result = lambda i: (
        "FLR0026_VK_QUEUE_PRESENT result=0 surface=x swapchain=s "
        f"index={i}"
    )
    # The emitter serializes C's escaped newline as literal backslash+n bytes;
    # physical log lines are not equivalent to individual marker records.
    return (
        "\\n".join((begin(0), begin(1), result(0)))
        + "\n"
        + "\\n".join((begin(2), result(1)))
        + "\n"
    )


def counter_program(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    match = re.search(
        r"""(?:out|counts)=\$\(awk '([^']+)' "\$[A-Za-z_][A-Za-z_0-9]*"\)""",
        source,
    )
    if match is None:
        raise AssertionError(f"missing one-pass present counter in {path.name}")
    return match.group(1)


def count_records(program: str, log: str) -> tuple[int, int, int, int]:
    result = subprocess.run(
        ["awk", program],
        input=log,
        text=True,
        check=True,
        capture_output=True,
    )
    return tuple(map(int, result.stdout.split()))


class Flr0405PresentGateTests(unittest.TestCase):
    def test_gate_counts_each_marker_not_each_physical_line(self) -> None:
        counts = count_records(counter_program(GATE), fixture_log())
        self.assertEqual((3, 2, 2, 0), counts)
        self.assertNotEqual(counts[0], counts[2], "unbalanced records must not report READY")

    def test_failed_return_is_total_but_not_successful(self) -> None:
        failed = fixture_log().replace(
            "result=0 surface=x swapchain=s index=1",
            "result=-4 surface=x swapchain=s index=1",
        )
        counts = count_records(counter_program(GATE), failed)
        self.assertEqual((3, 2, 1, 0), counts)
        self.assertGreater(counts[1] - counts[2], 0)

    def test_physically_split_marker_fails_closed(self) -> None:
        malformed = fixture_log().replace(
            "FLR0026_VK_QUEUE_PRESENT result=0 surface=x swapchain=s index=1",
            "FLR0026_VK_QUEUE_PRESENT result=0\nsurface=x swapchain=s index=1",
        )
        counts = count_records(counter_program(GATE), malformed)
        self.assertGreater(counts[3], 0)

    def test_marker_name_split_across_physical_line_fails_closed(self) -> None:
        malformed = fixture_log().replace(
            "FLR0026_VK_QUEUE_PRESENT result=0 surface=x swapchain=s index=1",
            "FLR0026_VK_QUEUE_\nPRESENT result=0 surface=x swapchain=s index=1",
        )
        counts = count_records(counter_program(GATE), malformed)
        self.assertGreater(counts[3], 0)

    def test_known_nonpresent_queue_markers_are_not_malformed(self) -> None:
        log = (
            "FLR0026_VK_QUEUE_SUBMIT_BEGIN queue=q fence=f\n"
            "FLR0026_VK_QUEUE_SUBMIT_DONE result=0 queue=q fence=f\n"
            + fixture_log()
        )
        self.assertEqual((3, 2, 2, 0), count_records(counter_program(GATE), log))

    def test_gate_and_monitor_share_the_same_one_pass_counter(self) -> None:
        self.assertEqual(counter_program(GATE), counter_program(MONITOR))

    def test_gate_rejects_malformed_marker_records(self) -> None:
        self.assertIn('if [ "$z" -gt 0 ]; then status=APP_LOG_MALFORMED', GATE.read_text())
        self.assertIn('if [ "$z" -gt 0 ]; then result=APP_LOG_MALFORMED', MONITOR.read_text())

    def test_monitor_uses_elapsed_time_and_rechecks_at_window_end(self) -> None:
        source = MONITOR.read_text(encoding="utf-8")
        self.assertIn('s+300', source)
        self.assertIn('((n-p)>=5)', source)
        self.assertIn('if ! check; then :; elif [ "$b" -ne "$r" ]', source)
        self.assertIn('SAMPLE_LIMIT_BEFORE_300S', source)
        self.assertNotIn("int($1)", source)
        self.assertNotIn("unmatched_samples", source)

    def test_ready_gate_requires_balanced_begins_total_returns_and_successes(self) -> None:
        source = GATE.read_text(encoding="utf-8")
        self.assertIn('if [ "$r" -gt "$b" ]', source)
        self.assertIn('if [ "$f" -gt 0 ]', source)
        self.assertIn(
            '[ "$b" -ge 2 ] && [ "$s" -ge 2 ] && [ "$b" -eq "$s" ]',
            source,
        )
        self.assertIn("present_return=$r", source)

    def test_guest_commands_are_single_line_and_valid_posix_shell(self) -> None:
        command_dir = ROOT / "work/commands"
        for path in sorted(command_dir.glob("FLR-0405-guest-*.cmd")):
            command = path.read_text(encoding="utf-8")
            self.assertEqual(1, len(command.splitlines()), path.name)
            result = subprocess.run(
                ["/bin/sh", "-n", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, f"{path.name}: {result.stderr}")

    def test_guest_identity_paths_match_the_fresh_host_run_id(self) -> None:
        command_dir = ROOT / "work/commands"
        commands = sorted(command_dir.glob("FLR-0405-guest-*.cmd"))
        self.assertTrue(commands)
        for path in commands:
            command = path.read_text(encoding="utf-8")
            self.assertIn("flr0405-0003", command, path.name)
            self.assertNotIn("flr0405-0001", command, path.name)

    def test_guest_commands_fit_serial_input_limit_and_measure_wrapper(self) -> None:
        command_dir = ROOT / "work/commands"
        marker = "__FLR_SERIAL_COMMAND_DONE_" + "0" * 24 + "__"
        commands = [
            (path.name, path.read_text(encoding="utf-8").rstrip("\n"))
            for path in sorted(command_dir.glob("FLR-0405-guest-*.cmd"))
        ]
        commands.append(
            (
                "post-capture live gate",
                "FLR0405_GATE_MODE=check; "
                "FLR0405_GATE_BASELINE_SUCCESS=9999999; "
                + GATE.read_text(encoding="utf-8").rstrip("\n"),
            )
        )
        for name, command in commands:
            command_bytes = len(command.encode("utf-8"))
            self.assertLessEqual(
                command_bytes,
                4096,
                f"serial-exec raw command limit exceeded: {name}",
            )
            wrapped = (
                command
                + "; rc=$?; stty echo; printf '\\nrc=%s\\n"
                + marker
                + "\\n' \"$rc\"\n"
            )
            self.assertEqual(
                99,
                len(wrapped.encode("utf-8")) - command_bytes,
                f"serial completion wrapper size changed: {name}",
            )


if __name__ == "__main__":
    unittest.main()
