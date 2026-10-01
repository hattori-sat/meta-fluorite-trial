import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from flr0399_live_capture import (  # noqa: E402
    Identity,
    Sample,
    expected_run_dir,
    guest_commands,
    parse_state_output,
    run_once,
)


class LiveCaptureControllerTests(unittest.TestCase):
    def run_controller(self, samples, capture=None):
        events = []
        sample_iter = iter(samples)

        def read_state(stage, timeout_seconds):
            events.append(("read", stage, timeout_seconds))
            return next(sample_iter)

        def save_evidence():
            events.append(("save",))

        def teardown():
            events.append(("teardown",))

        def capture_frame(stage, identity):
            events.append(("capture", stage, identity))
            if capture is not None:
                capture(stage, identity)

        result = run_once(
            read_state=read_state,
            capture_frame=capture_frame,
            preserve_evidence=save_evidence,
            teardown=teardown,
            expected_log_path="/run/user/1001/flr0399-0001-gdb.log",
            timeout_seconds=10,
            monotonic=lambda: 0.0,
        )
        return result, events

    def test_missing_log_fails_once_before_parse_or_capture(self):
        result, events = self.run_controller(
            [
                Sample(
                    state="LOG_MISSING",
                    identity=None,
                    log_path="/run/user/1001/flr0399-0001-gdb.log",
                    detail="runtime log does not exist",
                )
            ]
        )

        self.assertEqual("LOG_MISSING", result.status)
        self.assertEqual((), result.captures)
        self.assertEqual(["ready"], [event[1] for event in events if event[0] == "read"])
        self.assertEqual([("save",), ("teardown",)], events[-2:])

    def test_ready_and_first_present_are_captured_only_with_same_live_identity(self):
        identity = Identity(pid=694, uid=1001, start_time=23470)
        result, events = self.run_controller(
            [
                Sample("READY", identity, "/run/user/1001/flr0399-0001-gdb.log"),
                Sample("LIVE", identity, "/run/user/1001/flr0399-0001-gdb.log"),
                Sample("PRESENT", identity, "/run/user/1001/flr0399-0001-gdb.log"),
                Sample("LIVE", identity, "/run/user/1001/flr0399-0001-gdb.log"),
            ]
        )

        self.assertEqual("OBSERVED", result.status)
        self.assertEqual(["READY", "PRESENT"], [item.stage for item in result.captures])
        self.assertTrue(all(item.live for item in result.captures))
        self.assertEqual(
            ["ready", "identity", "present", "identity"],
            [event[1] for event in events if event[0] == "read"],
        )
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))
        self.assertLess(events.index(("save",)), events.index(("teardown",)))

    def test_capture_bracketed_by_process_exit_is_not_live_evidence(self):
        identity = Identity(pid=694, uid=1001, start_time=23470)
        result, events = self.run_controller(
            [
                Sample("READY", identity, "/run/user/1001/flr0399-0001-gdb.log"),
                Sample("EXITED", None, "/run/user/1001/flr0399-0001-gdb.log"),
            ]
        )

        self.assertEqual("POST_EXIT", result.status)
        self.assertEqual(1, len(result.captures))
        self.assertFalse(result.captures[0].live)
        self.assertNotIn("present", [event[1] for event in events if event[0] == "read"])

    def test_identity_change_during_capture_is_rejected(self):
        before = Identity(pid=694, uid=1001, start_time=23470)
        after = Identity(pid=694, uid=1001, start_time=98765)
        result, _ = self.run_controller(
            [
                Sample("READY", before, "/run/user/1001/flr0399-0001-gdb.log"),
                Sample("LIVE", after, "/run/user/1001/flr0399-0001-gdb.log"),
            ]
        )

        self.assertEqual("IDENTITY_CHANGED", result.status)
        self.assertFalse(result.captures[0].live)

    def test_missing_or_mismatched_log_source_is_fail_closed(self):
        result, events = self.run_controller(
            [Sample("READY", Identity(694, 1001, 23470), "/run/user/1001/other.log")]
        )

        self.assertEqual("LOG_SOURCE_MISMATCH", result.status)
        self.assertFalse(any(event[0] == "capture" for event in events))
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))

    def test_ready_deadline_is_bounded_and_teardown_still_runs_once(self):
        result, events = self.run_controller(
            [Sample("TIMEOUT", None, "/run/user/1001/flr0399-0001-gdb.log")]
        )

        self.assertEqual("READY_TIMEOUT", result.status)
        self.assertFalse(any(event[0] == "capture" for event in events))
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))

    def test_capture_exception_preserves_evidence_and_tears_down_once(self):
        identity = Identity(694, 1001, 23470)

        def fail_capture(stage, _identity):
            raise RuntimeError(f"capture failed at {stage}")

        result, events = self.run_controller(
            [Sample("READY", identity, "/run/user/1001/flr0399-0001-gdb.log")],
            capture=fail_capture,
        )

        self.assertEqual("CAPTURE_FAILED", result.status)
        self.assertEqual([("save",), ("teardown",)], events[-2:])
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))

    def test_preserve_failure_does_not_skip_single_teardown(self):
        events = []

        def read_state(stage, _timeout):
            events.append(("read", stage))
            return Sample(
                "LOG_MISSING",
                None,
                "/run/user/1001/flr0399-0001-gdb.log",
            )

        def preserve():
            events.append(("save",))
            raise OSError("serial evidence collection failed")

        def teardown():
            events.append(("teardown",))

        result = run_once(
            read_state=read_state,
            capture_frame=lambda _stage, _identity: None,
            preserve_evidence=preserve,
            teardown=teardown,
            expected_log_path="/run/user/1001/flr0399-0001-gdb.log",
            timeout_seconds=10,
        )

        self.assertEqual("EVIDENCE_PRESERVE_FAILED", result.status)
        self.assertEqual([("save",), ("teardown",)], events[-2:])
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))


class GuestCommandContractTests(unittest.TestCase):
    def test_run_directory_is_ticket_scoped_under_the_explicit_evidence_role(self):
        with tempfile.TemporaryDirectory() as evidence_root:
            expected = expected_run_dir(Path(evidence_root), "flr0399-0001")
            self.assertEqual(
                Path(evidence_root).resolve() / "flr0399-0001" / "qemu", expected
            )

        with tempfile.TemporaryDirectory() as evidence_root:
            with self.assertRaises(ValueError):
                expected_run_dir(Path(evidence_root), "../flr0399-0001")

    def test_generated_commands_parse_as_bash_and_posix_sh(self):
        commands = guest_commands("flr0399-0001")

        for shell in ("bash", "sh"):
            for name, command in commands.__dict__.items():
                if not isinstance(command, str) or name.endswith("_path"):
                    continue
                with self.subTest(shell=shell, command=name):
                    result = subprocess.run(
                        [shell, "-n", "-c", command],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(0, result.returncode, result.stderr)

    def test_exact_image_qemu_start_helper_parses_as_bash(self):
        start_helper = Path(__file__).parents[1] / "work/commands/FLR-0399-qemu-start.sh"
        result = subprocess.run(
            ["bash", "-n", str(start_helper)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_launch_and_observer_share_one_guest_log_path(self):
        commands = guest_commands("flr0399-0001")

        self.assertEqual(
            "/run/user/1001/flr0399-0001-gdb.log", commands.log_path
        )
        for command in (
            commands.preflight,
            commands.launch,
            commands.ready,
            commands.present,
            commands.identity,
            commands.collect,
        ):
            self.assertIn(commands.log_path, command)
        self.assertLess(commands.ready.index("test -r"), commands.ready.index("grep -c"))
        self.assertIn("FLR0399_STATE=LOG_MISSING", commands.ready)
        self.assertNotIn("integer expression expected", commands.ready)
        self.assertTrue(
            all(
                len(command) <= 4096
                for command in (
                    commands.preflight,
                    commands.launch,
                    commands.ready,
                    commands.present,
                    commands.identity,
                    commands.collect,
                    commands.stop,
                )
            )
        )

    def test_state_parser_requires_exactly_one_marker_and_live_identity(self):
        sample = parse_state_output(
            "FLR0399_STATE=READY PID=694 UID=1001 START=23470 "
            "READY=1 PRESENT_BEGIN=0 PRESENT_RETURN=0 SUN=0 "
            "LOG_PATH=/run/user/1001/flr0399-0001-gdb.log\n",
            stage="ready",
        )
        self.assertEqual("READY", sample.state)
        self.assertEqual(Identity(694, 1001, 23470), sample.identity)

        with self.assertRaises(ValueError):
            parse_state_output(
                "FLR0399_STATE=READY LOG_PATH=/run/user/1001/a.log\n",
                stage="ready",
            )
        with self.assertRaises(ValueError):
            parse_state_output(
                "FLR0399_STATE=READY LOG_PATH=/run/user/1001/a.log\n"
                "FLR0399_STATE=READY LOG_PATH=/run/user/1001/a.log\n",
                stage="ready",
            )

    def test_waiting_is_a_single_bounded_timeout_not_a_poll_loop(self):
        sample = parse_state_output(
            "FLR0399_STATE=WAITING PID=694 UID=1001 START=23470 "
            "READY=0 PRESENT_BEGIN=0 PRESENT_RETURN=0 SUN=0 "
            "LOG_PATH=/run/user/1001/flr0399-0001-gdb.log\n",
            stage="ready",
        )
        self.assertEqual("TIMEOUT", sample.state)

    def test_guest_command_builder_rejects_non_ticket_run_ids(self):
        for run_id in ("flr0396-0001", "flr0399-0", "../flr0399-0001", ""):
            with self.subTest(run_id=run_id):
                with self.assertRaises(ValueError):
                    guest_commands(run_id)


if __name__ == "__main__":
    unittest.main()
