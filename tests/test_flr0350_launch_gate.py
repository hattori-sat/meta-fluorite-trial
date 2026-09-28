#!/usr/bin/env python3
"""Regression tests for the production FLR-0350 launch-gate predicate."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.flr0350_launch_gate import (  # noqa: E402
    GATE_MARKER,
    GateObservationError,
    LAUNCH_MARKER,
    PROC_STAT_START_AWK,
    extract_proc_stat_starttime,
    is_fresh_run_id,
    main,
    validate_gate_output,
)


def observation(**overrides: str) -> dict[str, str]:
    fields = {
        "version": "1",
        "pid": "708",
        "start": "10001",
        "start_after": "10001",
        "recorded_start": "10001",
        "uid": "1001",
        "comm": "sh",
        "state": "S",
        "tracer": "0",
        "syscall": "read",
        "nr": "0",
        "arg1": "0x0",
        "target_type": "fifo",
        "target_dev": "17",
        "target_ino": "88",
        "gate_type": "fifo",
        "gate_dev": "17",
        "gate_ino": "88",
        "gate_uid": "1001",
        "gate_mode": "600",
    }
    fields.update(overrides)
    return fields


def render(fields: dict[str, str]) -> str:
    launch = (
        f"{LAUNCH_MARKER} pid={fields['pid']} start={fields['start']} "
        f"uid={fields['uid']} comm={fields['comm']}"
    )
    gate = GATE_MARKER + " " + " ".join(
        f"{key}={value}" for key, value in fields.items()
    )
    return launch + "\n" + gate


class LaunchGatePredicateTests(unittest.TestCase):
    def test_same_fifo_passes_for_fd_zero_and_fd_three(self) -> None:
        for actual_fd in ("0x0", "0x3"):
            with self.subTest(actual_fd=actual_fd):
                accepted = validate_gate_output(render(observation(arg1=actual_fd)))
                self.assertEqual(accepted["arg1"], actual_fd)

    def test_correct_fd_three_cannot_hide_wrong_actual_read_target(self) -> None:
        # The syscall says read(fd=0); an unrelated fd=3 symlink cannot make
        # this reported actual-FD target match the run-owned FIFO.
        with self.assertRaises(GateObservationError):
            validate_gate_output(
                render(observation(arg1="0x0", target_ino="89", gate_ino="88"))
            )

    def test_duplicate_gate_marker_is_rejected(self) -> None:
        line = render(observation())
        with self.assertRaises(GateObservationError):
            validate_gate_output(line + "\n" + line.splitlines()[1])

    def test_duplicate_launch_marker_is_rejected(self) -> None:
        line = render(observation()).splitlines()[0]
        with self.assertRaises(GateObservationError):
            validate_gate_output(
                line + "\n" + line + "\n" + render(observation()).splitlines()[1]
            )

    def test_missing_gate_marker_is_rejected(self) -> None:
        with self.assertRaises(GateObservationError):
            validate_gate_output("FLR0350_LAUNCH_WRAPPER=READY pid=708")

    def test_duplicate_field_is_rejected(self) -> None:
        with self.assertRaises(GateObservationError):
            validate_gate_output(render(observation()) + " pid=708")

    def test_missing_field_is_rejected(self) -> None:
        fields = observation()
        del fields["target_ino"]
        with self.assertRaises(GateObservationError):
            validate_gate_output(render(fields))

    def test_unknown_field_is_rejected(self) -> None:
        with self.assertRaises(GateObservationError):
            validate_gate_output(render(observation(unreviewed_fd="3")))

    def test_malformed_key_value_is_rejected(self) -> None:
        with self.assertRaises(GateObservationError):
            validate_gate_output(render(observation()).replace("pid=708", "pid"))

    def test_marker_must_be_the_first_token(self) -> None:
        launch, gate = render(observation()).splitlines()
        with self.assertRaises(GateObservationError):
            validate_gate_output(launch + "\nprefix " + gate)

    def test_launch_identity_must_match_gate_observation(self) -> None:
        launch, gate = render(observation()).splitlines()
        with self.assertRaises(GateObservationError):
            validate_gate_output(launch.replace("pid=708", "pid=709") + "\n" + gate)

    def test_actual_target_must_match_gate_type_device_inode(self) -> None:
        for changes in (
            {"target_type": "regular file"},
            {"gate_type": "regular file"},
            {"target_dev": "18"},
            {"target_ino": "89"},
        ):
            with self.subTest(changes=changes), self.assertRaises(
                GateObservationError
            ):
                validate_gate_output(render(observation(**changes)))

    def test_process_and_syscall_identity_must_match(self) -> None:
        for changes in (
            {"version": "2"},
            {"pid": "0"},
            {"start": "-1"},
            {"start_after": "10002"},
            {"recorded_start": "10002"},
            {"uid": "0"},
            {"comm": "flutter-auto"},
            {"state": "R"},
            {"tracer": "99"},
            {"syscall": "write"},
            {"nr": "1"},
            {"gate_uid": "0"},
            {"gate_mode": "666"},
        ):
            with self.subTest(changes=changes), self.assertRaises(
                GateObservationError
            ):
                validate_gate_output(render(observation(**changes)))

    def test_unknown_numeric_values_fail_closed(self) -> None:
        for field, value in (
            ("pid", "unknown"),
            ("target_dev", ""),
            ("gate_ino", "0xzz"),
            ("arg1", "-1"),
        ):
            with self.subTest(field=field), self.assertRaises(GateObservationError):
                validate_gate_output(render(observation(**{field: value})))


class ProcStatAndRunnerContractTests(unittest.TestCase):
    def test_proc_stat_starttime_handles_spaces_and_parentheses_in_comm(self) -> None:
        fields_after_comm = ["S"] + [str(index) for index in range(1, 20)]
        fields_after_comm[19] = "424242"
        stat_line = "123 (worker with ) embedded parens) " + " ".join(
            fields_after_comm
        )
        self.assertEqual(extract_proc_stat_starttime(stat_line), "424242")

    def test_proc_stat_starttime_rejects_malformed_input(self) -> None:
        with self.assertRaises(ValueError):
            extract_proc_stat_starttime("123 worker-without-parentheses S 1 2")

    def test_guest_identity_commands_use_the_tested_proc_stat_parser(self) -> None:
        command_files = sorted((ROOT / "work/commands").glob("FLR-0350-*.cmd"))
        covered = [
            path
            for path in command_files
            if "awk '{print $22}'" in path.read_text()
            or PROC_STAT_START_AWK in path.read_text()
        ]
        self.assertGreater(len(covered), 0)
        for path in covered:
            with self.subTest(command=path.name):
                source = path.read_text()
                self.assertNotIn("awk '{print $22}'", source)
                self.assertIn(PROC_STAT_START_AWK, source)

    def test_host_runner_validates_before_attach_and_go(self) -> None:
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        launch = runner.index(
            "guest_run launch FLR-0350-launch-paused-production.cmd"
        )
        observe = runner.index(
            "guest_run observe-gate FLR-0350-observe-fifo-read-gate.cmd"
        )
        validate = runner.index("scripts/flr0350_launch_gate.py", observe)
        attach = runner.index("guest_run attach-gdb FLR-0350-attach-pre-submit.cmd")
        release = runner.index("guest_run release-go FLR-0350-release-go.cmd")
        self.assertLess(launch, observe)
        self.assertLess(observe, validate)
        self.assertLess(validate, attach)
        self.assertLess(attach, release)
        self.assertNotIn("grep -F 'FLR0350_FIFO_READ_GATE=PASS'", runner)

    def test_launch_saves_wrapper_identity_before_gate_observation(self) -> None:
        launch = (
            ROOT / "work/commands/FLR-0350-launch-paused-production.cmd"
        ).read_text()
        observe = (
            ROOT / "work/commands/FLR-0350-observe-fifo-read-gate.cmd"
        ).read_text()
        self.assertLess(
            launch.index('printf \'%s\\n\' "$start" > "$startfile"'),
            launch.index("FLR0350_LAUNCH_WRAPPER=READY"),
        )
        self.assertIn('"/proc/$pid/fd/$read_fd"', observe)
        self.assertIn("stat -L -c '%d %i'", observe)
        self.assertIn("stat -L -c '%d %i %u %a'", observe)
        self.assertNotIn('"/proc/$pid/fd/3"', observe)

    def test_guest_cleanup_never_uses_process_wide_kill(self) -> None:
        stop = (ROOT / "work/commands/FLR-0350-stop-recorded-app.cmd").read_text()
        self.assertNotIn("pkill", stop)
        self.assertNotIn("killall", stop)
        guarded_signal = (
            '[ "$start" = "$expected" ] && '
            '[ "$uid" = "$(id -u agl-driver)" ]'
        )
        self.assertIn(guarded_signal, stop)
        self.assertLess(stop.index(guarded_signal), stop.index('kill -TERM "$pid"'))

    def test_run_id_must_be_fresh_and_ticket_correlated(self) -> None:
        self.assertTrue(is_fresh_run_id("flr0355-0001"))
        self.assertFalse(is_fresh_run_id("flr0350-0001"))
        self.assertFalse(is_fresh_run_id("flr0355-0001/../reuse"))
        self.assertFalse(is_fresh_run_id("not-a-run-id"))

    def test_validator_cli_accepts_the_separate_launch_and_gate_logs(self) -> None:
        launch, gate = render(observation()).splitlines()
        with tempfile.TemporaryDirectory() as directory:
            launch_path = Path(directory) / "launch.log"
            gate_path = Path(directory) / "gate.log"
            launch_path.write_text(launch + "\n", encoding="utf-8")
            gate_path.write_text(gate + "\n", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                result = main(["--validate", str(launch_path), str(gate_path)])
        self.assertEqual(result, 0)
        self.assertIn("FLR0350_FIFO_READ_GATE=PASS", output.getvalue())

    def test_run_id_cli_rejects_consumed_identifier(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(["--check-run-id", "flr0350-0001"])
        self.assertEqual(result, 2)
        self.assertIn("FLR0350_RUN_ID=REJECTED", output.getvalue())


if __name__ == "__main__":
    unittest.main()
