import base64
import hashlib
import io
import json
import os
import re
import signal
import shlex
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from flr0399_live_capture import (  # noqa: E402
    Identity,
    Sample,
    evidence_collect_command,
    expected_run_dir,
    guest_commands,
    make_frame_capture,
    make_state_reader,
    parse_state_output,
    run_once,
    state_poll_label,
    verify_postflight,
    wrap_serial_child_command,
    _serial_exec,
)
import flr0399_live_capture as live_capture  # noqa: E402
from flr0399_process_cleanup import cleanup_exact_qmp_processes  # noqa: E402


def write_analysis_test_ppm(path, width, height, pixels):
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode() + pixels)


class QmpAnalysisTests(unittest.TestCase):
    def test_720x400_capture_analyzes_available_rois_and_skips_sequoia(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "small.ppm"
            write_analysis_test_ppm(image, 720, 400, bytes(720 * 400 * 3))

            live_capture._analyze_capture(root, image)

            full = json.loads((root / "small-full-analysis.log").read_text())
            hud = json.loads((root / "small-hud-analysis.log").read_text())
            sequoia = json.loads(
                (root / "small-sequoia-analysis.log").read_text()
            )
            self.assertEqual((full["width"], full["height"]), (720, 400))
            self.assertEqual((hud["width"], hud["height"]), (720, 400))
            self.assertEqual(sequoia["status"], "SKIPPED_OUTSIDE_CAPTURE")
            self.assertEqual((sequoia["width"], sequoia["height"]), (720, 400))
            self.assertEqual(sequoia["region"], [440, 220, 400, 360])

    def test_malformed_ppm_remains_fatal_instead_of_being_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "malformed.ppm"
            image.write_bytes(b"not a PPM")

            with self.assertRaisesRegex(RuntimeError, "QMP pixel analysis failed"):
                live_capture._analyze_capture(root, image)

            full_log = (root / "malformed-full-analysis.log").read_text()
            self.assertIn("unsupported PPM format", full_log)


def add_fake_process(proc_root, pid, comm, argv, start_time):
    process_dir = Path(proc_root) / str(pid)
    process_dir.mkdir(parents=True, exist_ok=True)
    (process_dir / "comm").write_text(comm + "\n", encoding="utf-8")
    (process_dir / "cmdline").write_bytes(b"\0".join(arg.encode() for arg in argv) + b"\0")
    stat_fields = ["S", *(["0"] * 18), str(start_time)]
    (process_dir / "stat").write_text(
        f"{pid} ({comm}) {' '.join(stat_fields)}\n", encoding="utf-8"
    )


def fake_pidfd_arguments(sender):
    def opener(pid, flags):
        if flags != 0:
            raise AssertionError(f"unexpected pidfd flags: {flags}")
        return pid

    return {
        "pidfd_open": opener,
        "pidfd_sender": sender,
        "fd_closer": lambda _pidfd: None,
    }


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

        def capture_frame(stage, identity, _remaining):
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
            [
                "ready",
                "identity-after-ready",
                "present",
                "identity-after-present",
            ],
            [event[1] for event in events if event[0] == "read"],
        )
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))
        self.assertLess(events.index(("save",)), events.index(("teardown",)))

    def test_each_identity_bracket_has_a_unique_serial_evidence_label(self):
        identity = Identity(pid=694, uid=1001, start_time=23470)
        result, events = self.run_controller(
            [
                Sample("READY", identity, "/run/user/1001/flr0399-0001-gdb.log"),
                Sample("LIVE", identity, "/run/user/1001/flr0399-0001-gdb.log"),
                Sample("PRESENT", identity, "/run/user/1001/flr0399-0001-gdb.log"),
                Sample("LIVE", identity, "/run/user/1001/flr0399-0001-gdb.log"),
            ]
        )

        identity_reads = [
            event[1] for event in events if event[0] == "read" and event[1].startswith("identity")
        ]
        self.assertEqual("OBSERVED", result.status)
        self.assertEqual(
            ["identity-after-ready", "identity-after-present"], identity_reads
        )

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

    def test_waiting_captures_once_then_polls_until_ready_and_present(self):
        now = [0.0]
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0400-0001-gdb.log"
        samples = iter(
            [
                Sample("WAITING", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("WAITING", identity, log_path),
                Sample("READY", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("PRESENT", identity, log_path),
                Sample("LIVE", identity, log_path),
            ]
        )
        events = []

        def read_state(stage, timeout_seconds):
            events.append(("read", stage, timeout_seconds))
            return next(samples)

        def capture(stage, captured_identity, _remaining):
            events.append(("capture", stage, captured_identity))

        def sleep(seconds):
            events.append(("sleep", seconds))
            now[0] += seconds

        result = run_once(
            read_state=read_state,
            capture_frame=capture,
            preserve_evidence=lambda: events.append(("preserve",)),
            teardown=lambda: events.append(("teardown",)),
            expected_log_path=log_path,
            timeout_seconds=10,
            monotonic=lambda: now[0],
            sleep=sleep,
            poll_interval_seconds=2,
        )

        self.assertEqual("OBSERVED", result.status)
        self.assertEqual(["WAITING", "READY", "PRESENT"], [item.stage for item in result.captures])
        self.assertTrue(all(item.live for item in result.captures))
        self.assertEqual(1, sum(event[:2] == ("capture", "WAITING") for event in events))
        self.assertEqual(2, sum(event[0] == "sleep" for event in events))
        self.assertLess(events.index(("preserve",)), events.index(("teardown",)))
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))

    def test_present_waiting_is_polled_until_present(self):
        now = [0.0]
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0400-0001-gdb.log"
        samples = iter(
            [
                Sample("READY", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("WAITING", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("WAITING", identity, log_path),
                Sample("PRESENT", identity, log_path),
                Sample("LIVE", identity, log_path),
            ]
        )
        events = []

        def read_state(stage, timeout_seconds):
            events.append(("read", stage, timeout_seconds))
            return next(samples)

        def sleep(seconds):
            events.append(("sleep", seconds))
            now[0] += seconds

        result = run_once(
            read_state=read_state,
            capture_frame=lambda stage, _identity, _remaining: events.append(("capture", stage)),
            preserve_evidence=lambda: events.append(("preserve",)),
            teardown=lambda: events.append(("teardown",)),
            expected_log_path=log_path,
            timeout_seconds=10,
            monotonic=lambda: now[0],
            sleep=sleep,
            poll_interval_seconds=2,
        )

        self.assertEqual("OBSERVED", result.status)
        self.assertEqual(["READY", "WAITING", "PRESENT"], [item.stage for item in result.captures])
        self.assertEqual(
            [("sleep", 2), ("sleep", 2)],
            [event for event in events if event[0] == "sleep"],
        )

    def test_present_waiting_uses_same_monotonic_deadline_as_ready(self):
        now = [0.0]
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0400-0001-gdb.log"
        samples = iter(
            [
                Sample("READY", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("WAITING", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("WAITING", identity, log_path),
            ]
        )
        events = []

        def read_state(stage, timeout_seconds):
            events.append(("read", stage, timeout_seconds))
            return next(samples)

        def sleep(seconds):
            events.append(("sleep", seconds))
            now[0] += seconds

        result = run_once(
            read_state=read_state,
            capture_frame=lambda stage, _identity, _remaining: events.append(("capture", stage)),
            preserve_evidence=lambda: events.append(("preserve",)),
            teardown=lambda: events.append(("teardown",)),
            expected_log_path=log_path,
            timeout_seconds=3,
            monotonic=lambda: now[0],
            sleep=sleep,
            poll_interval_seconds=2,
        )

        self.assertEqual("PRESENT_DEADLINE_EXPIRED", result.status, events)
        self.assertEqual(2, sum(event[0] == "read" and event[1] == "present" for event in events))
        self.assertEqual(
            [("sleep", 2), ("sleep", 1)],
            [event for event in events if event[0] == "sleep"],
        )
        self.assertEqual(
            [("capture", "READY"), ("capture", "WAITING")],
            [event for event in events if event[0] == "capture"],
        )
        self.assertLess(events.index(("preserve",)), events.index(("teardown",)))

    def test_repeated_waiting_does_not_reset_deadline_or_start_late_read(self):
        now = [0.0]
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0400-0001-gdb.log"
        samples = iter(
            [
                Sample("WAITING", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("WAITING", identity, log_path),
                Sample("WAITING", identity, log_path),
            ]
        )
        events = []

        def read_state(stage, timeout_seconds):
            events.append(("read", stage, timeout_seconds))
            return next(samples)

        def sleep(seconds):
            events.append(("sleep", seconds))
            now[0] += seconds

        result = run_once(
            read_state=read_state,
            capture_frame=lambda stage, _identity, _remaining: events.append(("capture", stage)),
            preserve_evidence=lambda: events.append(("preserve",)),
            teardown=lambda: events.append(("teardown",)),
            expected_log_path=log_path,
            timeout_seconds=5,
            monotonic=lambda: now[0],
            sleep=sleep,
            poll_interval_seconds=2,
        )

        self.assertEqual("READY_DEADLINE_EXPIRED", result.status)
        self.assertEqual(3, sum(event[0] == "read" and event[1] == "ready" for event in events))
        self.assertEqual([("sleep", 2), ("sleep", 2), ("sleep", 1)], [event for event in events if event[0] == "sleep"])
        self.assertEqual([("capture", "WAITING")], [event for event in events if event[0] == "capture"])
        self.assertLess(events.index(("preserve",)), events.index(("teardown",)))
        self.assertEqual(1, sum(event[0] == "preserve" for event in events))
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))

    def test_expired_deadline_does_not_issue_a_guest_read(self):
        clock_values = iter((0.0, 10.0))
        reads = []
        result = run_once(
            read_state=lambda stage, _timeout: reads.append(stage),
            capture_frame=lambda _stage, _identity, _remaining: None,
            preserve_evidence=lambda: None,
            teardown=lambda: None,
            expected_log_path="/run/user/1001/flr0399-0001-gdb.log",
            timeout_seconds=10,
            monotonic=lambda: next(clock_values),
        )

        self.assertEqual("READY_DEADLINE_EXPIRED", result.status)
        self.assertEqual([], reads)

    def test_slow_guest_read_cannot_authorize_a_capture_after_deadline(self):
        now = [0.0]
        identity = Identity(694, 1001, 23470)
        reads = []
        captures = []

        def read_state(stage, _timeout):
            reads.append(stage)
            now[0] = 11.0
            return Sample("READY", identity, "/run/user/1001/flr0399-0001-gdb.log")

        result = run_once(
            read_state=read_state,
            capture_frame=lambda stage, _identity, _remaining: captures.append(stage),
            preserve_evidence=lambda: None,
            teardown=lambda: None,
            expected_log_path="/run/user/1001/flr0399-0001-gdb.log",
            timeout_seconds=10,
            monotonic=lambda: now[0],
        )

        self.assertEqual("READY_DEADLINE_EXPIRED", result.status)
        self.assertEqual(["ready"], reads)
        self.assertEqual([], captures)

    def test_remaining_deadline_is_passed_to_each_read_and_capture(self):
        now = [0.0]
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0399-0001-gdb.log"
        samples = iter(
            [
                Sample("READY", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("PRESENT", identity, log_path),
                Sample("LIVE", identity, log_path),
            ]
        )
        read_budgets = []
        capture_budgets = []

        def read_state(stage, remaining):
            read_budgets.append((stage, remaining))
            if stage == "ready":
                now[0] += 2
            return next(samples)

        def capture_frame(_stage, _identity, remaining):
            capture_budgets.append(remaining)
            now[0] += 1

        result = run_once(
            read_state=read_state,
            capture_frame=capture_frame,
            preserve_evidence=lambda: None,
            teardown=lambda: None,
            expected_log_path=log_path,
            timeout_seconds=10,
            monotonic=lambda: now[0],
        )

        self.assertEqual("OBSERVED", result.status)
        self.assertEqual(
            [
                ("ready", 10.0),
                ("identity-after-ready", 7.0),
                ("present", 7.0),
                ("identity-after-present", 6.0),
            ],
            read_budgets,
        )
        self.assertEqual([8.0, 7.0], capture_budgets)

    def test_capture_exception_preserves_evidence_and_tears_down_once(self):
        identity = Identity(694, 1001, 23470)

        def fail_capture(stage, _identity, _remaining):
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
            capture_frame=lambda _stage, _identity, _remaining: None,
            preserve_evidence=preserve,
            teardown=teardown,
            expected_log_path="/run/user/1001/flr0399-0001-gdb.log",
            timeout_seconds=10,
        )

        self.assertEqual("EVIDENCE_PRESERVE_FAILED", result.status)
        self.assertEqual([("save",), ("teardown",)], events[-2:])
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))

    def test_unmatched_present_stack_is_bracketed_and_still_precedes_gdb(self):
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0401-0001-gdb.log"
        samples = iter(
            [
                Sample("READY", identity, log_path, present_begin=1, present_return=0),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("PRESENT", identity, log_path, present_begin=1, present_return=1),
                Sample("LIVE", identity, log_path),
            ]
        )
        events = []

        def read_state(stage, remaining):
            events.append(("read", stage, remaining))
            return next(samples)

        def capture_frame(stage, _identity, _remaining):
            events.append(("still", stage))

        def capture_stack(sample, remaining):
            events.append(("gdb", sample.present_begin, sample.present_return, remaining))

        result = run_once(
            read_state=read_state,
            capture_frame=capture_frame,
            capture_present_stack=capture_stack,
            preserve_evidence=lambda: events.append(("preserve",)),
            teardown=lambda: events.append(("teardown",)),
            expected_log_path=log_path,
            timeout_seconds=10,
            monotonic=lambda: 0.0,
        )

        self.assertEqual("OBSERVED", result.status)
        self.assertEqual(
            ["READY", "PRESENT_UNMATCHED", "PRESENT"],
            [item.stage for item in result.captures],
        )
        self.assertTrue(all(item.live for item in result.captures))
        self.assertEqual(1, sum(event[0] == "gdb" for event in events))
        self.assertLess(events.index(("still", "PRESENT_UNMATCHED")), next(
            index for index, event in enumerate(events) if event[0] == "gdb"
        ))
        self.assertEqual(
            [
                "ready",
                "identity-after-ready",
                "identity-before-present-stack",
                "identity-after-present-still",
                "identity-after-present-stack",
                "present",
                "identity-after-present",
            ],
            [event[1] for event in events if event[0] == "read"],
        )
        self.assertLess(events.index(("preserve",)), events.index(("teardown",)))

    def test_matched_present_counters_do_not_trigger_stack_capture(self):
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0401-0001-gdb.log"
        samples = iter(
            [
                Sample("READY", identity, log_path, present_begin=1, present_return=1),
                Sample("LIVE", identity, log_path),
                Sample("TIMEOUT", None, log_path),
            ]
        )
        callbacks = []

        result = run_once(
            read_state=lambda _stage, _remaining: next(samples),
            capture_frame=lambda _stage, _identity, _remaining: None,
            capture_present_stack=lambda sample, _remaining: callbacks.append(sample),
            preserve_evidence=lambda: None,
            teardown=lambda: None,
            expected_log_path=log_path,
            timeout_seconds=10,
            monotonic=lambda: 0.0,
        )

        self.assertEqual("PRESENT_TIMEOUT", result.status)
        self.assertEqual([], callbacks)

    def test_missing_or_wrong_uid_identity_never_authorizes_stack_capture(self):
        log_path = "/run/user/1001/flr0401-0001-gdb.log"
        cases = (("missing", None), ("wrong uid", Identity(694, 1000, 23470)))
        for label, identity in cases:
            with self.subTest(identity=label):
                callbacks = []
                result = run_once(
                    read_state=lambda _stage, _remaining: Sample(
                        "READY", identity, log_path, present_begin=1, present_return=0
                    ),
                    capture_frame=lambda _stage, _identity, _remaining: None,
                    capture_present_stack=lambda sample, _remaining: callbacks.append(sample),
                    preserve_evidence=lambda: None,
                    teardown=lambda: None,
                    expected_log_path=log_path,
                    timeout_seconds=10,
                    monotonic=lambda: 0.0,
                )

                self.assertEqual([], callbacks)
                self.assertIn(result.status, {"IDENTITY_MISSING", "IDENTITY_UID_MISMATCH"})

    def test_repeated_unmatched_waiting_samples_trigger_stack_only_once(self):
        now = [0.0]
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0401-0001-gdb.log"
        samples = iter(
            [
                Sample("READY", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("WAITING", identity, log_path, present_begin=1, present_return=0),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("WAITING", identity, log_path, present_begin=2, present_return=0),
                Sample("WAITING", identity, log_path, present_begin=3, present_return=0),
            ]
        )
        events = []

        def read_state(stage, _remaining):
            events.append(("read", stage))
            return next(samples)

        def sleep(seconds):
            events.append(("sleep", seconds))
            now[0] += seconds

        result = run_once(
            read_state=read_state,
            capture_frame=lambda stage, _identity, _remaining: events.append(("still", stage)),
            capture_present_stack=lambda sample, _remaining: events.append(
                ("gdb", sample.present_begin, sample.present_return)
            ),
            preserve_evidence=lambda: events.append(("preserve",)),
            teardown=lambda: events.append(("teardown",)),
            expected_log_path=log_path,
            timeout_seconds=3,
            monotonic=lambda: now[0],
            sleep=sleep,
            poll_interval_seconds=1,
        )

        self.assertEqual("PRESENT_DEADLINE_EXPIRED", result.status, events)
        self.assertEqual(1, sum(event[0] == "gdb" for event in events))
        self.assertEqual(3, sum(event[0] == "read" and event[1] == "present" for event in events))
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))
        self.assertLess(events.index(("preserve",)), events.index(("teardown",)))

    def test_deadline_expiry_before_stack_identity_check_prevents_gdb_work(self):
        now = [0.0]
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0401-0001-gdb.log"
        callbacks = []
        reads = []

        def read_state(stage, _remaining):
            reads.append(stage)
            return Sample("READY", identity, log_path, present_begin=1, present_return=0)

        def capture_frame(_stage, _identity, _remaining):
            now[0] = 10.0

        result = run_once(
            read_state=read_state,
            capture_frame=capture_frame,
            capture_present_stack=lambda sample, _remaining: callbacks.append(sample),
            preserve_evidence=lambda: None,
            teardown=lambda: None,
            expected_log_path=log_path,
            timeout_seconds=10,
            monotonic=lambda: now[0],
        )

        self.assertEqual("CAPTURE_DEADLINE_EXPIRED", result.status)
        self.assertEqual(["ready"], reads)
        self.assertEqual([], callbacks)

    def test_expired_attach_deadline_does_not_issue_post_attach_guest_read(self):
        now = [0.0]
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0401-0001-gdb.log"
        samples = iter(
            [
                Sample("READY", identity, log_path, present_begin=1, present_return=0),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
            ]
        )
        reads = []
        callbacks = []
        events = []

        def read_state(stage, _remaining):
            reads.append(stage)
            return next(samples)

        def capture_stack(_sample, _remaining):
            callbacks.append("started")
            now[0] = 10.0

        result = run_once(
            read_state=read_state,
            capture_frame=lambda _stage, _identity, _remaining: None,
            capture_present_stack=capture_stack,
            preserve_evidence=lambda: events.append("preserve"),
            teardown=lambda: events.append("teardown"),
            expected_log_path=log_path,
            timeout_seconds=10,
            monotonic=lambda: now[0],
        )

        self.assertEqual("IDENTITY_DEADLINE_EXPIRED", result.status)
        self.assertEqual(["started"], callbacks)
        self.assertNotIn("identity-after-present-stack", reads)
        self.assertEqual(["preserve", "teardown"], events)

    def test_stack_callback_timeout_is_recorded_and_evidence_precedes_teardown(self):
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0401-0001-gdb.log"
        samples = iter(
            [
                Sample("READY", identity, log_path, present_begin=1, present_return=0),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("TIMEOUT", None, log_path),
            ]
        )
        events = []

        def capture_stack(_sample, _remaining):
            events.append(("gdb",))
            raise TimeoutError("bounded attach timed out")

        result = run_once(
            read_state=lambda stage, _remaining: (events.append(("read", stage)), next(samples))[1],
            capture_frame=lambda stage, _identity, _remaining: events.append(("still", stage)),
            capture_present_stack=capture_stack,
            preserve_evidence=lambda: events.append(("preserve",)),
            teardown=lambda: events.append(("teardown",)),
            expected_log_path=log_path,
            timeout_seconds=10,
            monotonic=lambda: 0.0,
        )

        self.assertEqual("PRESENT_STACK_COMPLETION_UNCONFIRMED", result.status)
        self.assertIn("present-stack:TimeoutError:bounded attach timed out", result.errors)
        self.assertNotIn(("read", "identity-after-present-stack"), events)
        self.assertEqual(1, sum(event[0] == "teardown" for event in events))
        self.assertLess(events.index(("preserve",)), events.index(("teardown",)))

    def test_present_stack_deadline_budget_stops_guest_gdb_before_identity_reserve(self):
        self.assertEqual((18, 24.0), live_capture.present_stack_timeouts(120.0))
        self.assertEqual((5, 11.0), live_capture.present_stack_timeouts(26.0))
        self.assertIsNone(live_capture.present_stack_timeouts(25.9))
        self.assertIsNone(live_capture.present_stack_timeouts(float("inf")))

    def test_unconfirmed_gdb_result_stops_all_later_guest_serial_reads(self):
        identity = Identity(694, 1001, 23470)
        log_path = "/run/user/1001/flr0401-0001-gdb.log"
        samples = iter(
            [
                Sample("READY", identity, log_path, present_begin=1, present_return=0),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
                Sample("LIVE", identity, log_path),
            ]
        )
        events = []

        def capture_stack(_sample, _remaining):
            events.append(("gdb-started",))
            raise TimeoutError("serial did not confirm guest GDB completion")

        result = run_once(
            read_state=lambda stage, _remaining: (events.append(("read", stage)), next(samples))[1],
            capture_frame=lambda stage, _identity, _remaining: events.append(("still", stage)),
            capture_present_stack=capture_stack,
            preserve_evidence=lambda: events.append(("preserve",)),
            teardown=lambda: events.append(("teardown",)),
            expected_log_path=log_path,
            timeout_seconds=10,
            monotonic=lambda: 0.0,
        )

        self.assertEqual("PRESENT_STACK_COMPLETION_UNCONFIRMED", result.status)
        self.assertNotIn(("read", "identity-after-present-stack"), events)
        self.assertEqual([("preserve",), ("teardown",)], events[-2:])


class GuestCommandContractTests(unittest.TestCase):
    def test_empty_coredump_journal_is_valid_when_coredumpctl_has_no_matches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "bin"
            tools.mkdir()
            log = root / "flr0399-gdb.log"
            log.write_text("bounded gdb log\n", encoding="utf-8")
            coredump_calls = root / "coredumpctl-called"

            def install_tool(name, body):
                tool = tools / name
                tool.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
                tool.chmod(0o755)

            install_tool("sha256sum", "printf 'fixture-sha  %s\\n' \"$1\"")
            install_tool(
                "journalctl",
                "case \" $* \" in *COREDUMP_EXE=*) exit 0;; *) printf 'kernel journal empty\\n';; esac",
            )
            install_tool(
                "coredumpctl",
                f"printf called > {coredump_calls}; exit 1",
            )
            environment = os.environ.copy()
            environment["PATH"] = f"{tools}{os.pathsep}{environment['PATH']}"
            result = subprocess.run(
                ["sh", "-c", evidence_collect_command(str(log), "flr0399-0001")],
                env=environment,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("FLR0399_COREDUMP_QUERY=EMPTY", result.stdout)
            self.assertIn("FLR0399_EVIDENCE_COLLECT=PASS", result.stdout)
            self.assertFalse(coredump_calls.exists())

    def test_qmp_capture_timeout_keeps_partial_stdout_and_stderr(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "capture.log"
            timeout = subprocess.TimeoutExpired(
                ["qmp-capture"], 0.1, output=b"partial stdout\n", stderr=b"partial stderr\n"
            )
            with mock.patch.object(subprocess, "run", side_effect=timeout):
                with self.assertRaises(TimeoutError):
                    live_capture._run_qmp_capture_command(
                        ["qmp-capture"], log, 0.1, "regression-test"
                    )

            contents = log.read_text(encoding="utf-8")
            self.assertIn("capture=TIMEOUT stage=regression-test", contents)
            self.assertIn("partial stdout", contents)
            self.assertIn("partial stderr", contents)

    def test_serial_exec_timeout_kills_worker_group_and_preserves_partial_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            worker_pid_file = root / "worker.pid"
            harness = root / "serial-worker.sh"
            harness.write_text(
                "#!/bin/sh\n"
                "while [ $# -gt 0 ]; do\n"
                "  if [ \"$1\" = --output ]; then output=$2; shift 2; else shift; fi\n"
                "done\n"
                "printf 'partial serial bytes\\n' > \"$output\"\n"
                "printf 'partial stdout\\n'\n"
                "printf 'partial stderr\\n' >&2\n"
                f"sleep 30 & echo $! > {worker_pid_file}\n"
                "wait\n",
                encoding="utf-8",
            )
            harness.chmod(0o755)

            try:
                with mock.patch.object(live_capture, "HARNESS", harness):
                    with self.assertRaises(TimeoutError):
                        _serial_exec(
                            run_dir=root,
                            label="deadline",
                            command="true",
                            serial_port=10930,
                            timeout_seconds=1.0,
                        )

                output = (root / "FLR-0399-deadline.serial.log").read_text(
                    encoding="utf-8"
                )
                harness_output = (root / "FLR-0399-deadline.harness.log").read_text(
                    encoding="utf-8"
                )
                self.assertIn("partial serial bytes", output)
                self.assertIn("partial stdout", harness_output)
                self.assertIn("partial stderr", harness_output)
                self.assertIn("serial-exec=TIMEOUT", harness_output)

                worker_pid = int(worker_pid_file.read_text(encoding="utf-8"))
                with self.assertRaises(ProcessLookupError):
                    os.kill(worker_pid, 0)
            finally:
                if worker_pid_file.exists():
                    try:
                        os.kill(int(worker_pid_file.read_text(encoding="utf-8")), signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_failed_start_cleanup_signals_only_the_exact_run_qemu(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proc_root = root / "proc"
            proc_root.mkdir()
            qmp = root / "run-qmp.sock"
            add_fake_process(
                proc_root,
                101,
                "qemu-system-x86_64",
                ["/usr/bin/qemu-system-x86_64", "-qmp", f"unix:{qmp}"],
                1234,
            )
            add_fake_process(
                proc_root,
                102,
                "qemu-system-x86_64",
                ["/usr/bin/qemu-system-x86_64", "-qmp", "unix:/other/run.sock"],
                2345,
            )
            signals = []

            def send_signal(pidfd, sig):
                pid = pidfd
                signals.append((pid, sig))
                if sig == signal.SIGTERM:
                    (proc_root / str(pid)).rename(root / f"exited-{pid}")

            result = cleanup_exact_qmp_processes(
                qmp,
                proc_root=proc_root,
                **fake_pidfd_arguments(send_signal),
                timeout_seconds=0.01,
                sleeper=lambda _seconds: None,
            )

            self.assertEqual([(101, signal.SIGTERM)], signals)
            self.assertEqual((), result.remaining)
            self.assertEqual((), result.errors)

    def test_failed_start_cleanup_requires_exact_qmp_argument_and_launch_executable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proc_root = root / "proc"
            proc_root.mkdir()
            qmp = root / "run-qmp.sock"
            add_fake_process(
                proc_root,
                101,
                "qemu-system-x86_64",
                ["/usr/bin/qemu-system-x86_64", "-qmp", f"unix:{qmp}-similar"],
                1234,
            )
            add_fake_process(
                proc_root,
                102,
                "python3",
                [
                    "/usr/bin/python3",
                    "/opt/launcher.py",
                    "/usr/bin/qemu-system-x86_64",
                    "-qmp",
                    f"unix:{qmp}",
                ],
                2345,
            )
            signals = []
            result = cleanup_exact_qmp_processes(
                qmp,
                proc_root=proc_root,
                **fake_pidfd_arguments(
                    lambda pidfd, sig: signals.append((pidfd, sig))
                ),
                timeout_seconds=0.01,
                sleeper=lambda _seconds: None,
            )

            self.assertEqual([], signals)
            self.assertEqual((), result.remaining)
            self.assertEqual((), result.errors)

    def test_failed_start_cleanup_matches_runqemu_and_exact_qmp_chardev(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proc_root = root / "proc"
            proc_root.mkdir()
            qmp = root / "run-qmp.sock"
            add_fake_process(
                proc_root,
                101,
                "python3",
                [
                    "/usr/bin/python3",
                    "/yocto/scripts/runqemu",
                    "qemux86-64",
                    f"qmp=unix:{qmp}",
                ],
                1234,
            )
            add_fake_process(
                proc_root,
                102,
                "qemu-system-x86",
                [
                    "/usr/bin/qemu-system-x86_64",
                    "-chardev",
                    f"socket,id=qmp,path={qmp},server=on,wait=off",
                ],
                2345,
            )
            add_fake_process(
                proc_root,
                103,
                "python3",
                [
                    "/usr/bin/python3",
                    "/tmp/runqemu-helper.py",
                    f"qmp=unix:{qmp}",
                ],
                3456,
            )
            signals = []

            def send_signal(pidfd, sig):
                signals.append((pidfd, sig))
                if sig == signal.SIGTERM:
                    (proc_root / str(pidfd)).rename(root / f"exited-{pidfd}")

            result = cleanup_exact_qmp_processes(
                qmp,
                proc_root=proc_root,
                **fake_pidfd_arguments(send_signal),
                timeout_seconds=0.01,
                sleeper=lambda _seconds: None,
            )

            self.assertEqual({(101, signal.SIGTERM), (102, signal.SIGTERM)}, set(signals))
            self.assertEqual((), result.remaining)
            self.assertEqual((), result.errors)

    def test_failed_start_cleanup_never_kills_a_reused_pid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proc_root = root / "proc"
            proc_root.mkdir()
            qmp = root / "run-qmp.sock"
            argv = ["/usr/bin/qemu-system-x86_64", "-qmp", f"unix:{qmp}"]
            add_fake_process(proc_root, 101, "qemu-system-x86_64", argv, 1234)
            signals = []

            def send_signal(pidfd, sig):
                pid = pidfd
                signals.append((pid, sig))
                if sig == signal.SIGTERM:
                    add_fake_process(proc_root, pid, "qemu-system-x86_64", argv, 9876)

            result = cleanup_exact_qmp_processes(
                qmp,
                proc_root=proc_root,
                **fake_pidfd_arguments(send_signal),
                timeout_seconds=0.01,
                sleeper=lambda _seconds: None,
            )

            self.assertEqual([(101, signal.SIGTERM)], signals)
            self.assertTrue(any("pid-identity-changed:101" in error for error in result.errors))

    def test_failed_start_cleanup_rechecks_identity_after_opening_pidfd(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proc_root = root / "proc"
            proc_root.mkdir()
            qmp = root / "run-qmp.sock"
            argv = ["/usr/bin/qemu-system-x86_64", "-qmp", f"unix:{qmp}"]
            add_fake_process(proc_root, 101, "qemu-system-x86_64", argv, 1234)
            signals = []

            def opener(pid, flags):
                self.assertEqual(0, flags)
                add_fake_process(proc_root, pid, "qemu-system-x86_64", argv, 5678)
                return pid

            result = cleanup_exact_qmp_processes(
                qmp,
                proc_root=proc_root,
                pidfd_open=opener,
                pidfd_sender=lambda pidfd, sig: signals.append((pidfd, sig)),
                fd_closer=lambda _pidfd: None,
                timeout_seconds=0.01,
                sleeper=lambda _seconds: None,
            )

            self.assertEqual([], signals)
            self.assertTrue(any("pid-identity-changed:101" in error for error in result.errors))
            self.assertEqual(1, len(result.remaining))

    def test_failed_start_cleanup_removes_only_a_stale_qmp_socket(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proc_root = root / "proc"
            proc_root.mkdir()

            class StaleSocketPath:
                def __init__(self, path):
                    self.path = path
                    self.removed = False

                def __str__(self):
                    return str(self.path)

                def is_absolute(self):
                    return True

                def is_symlink(self):
                    return False

                def exists(self):
                    return not self.removed

                def is_socket(self):
                    return not self.removed

                def unlink(self):
                    self.removed = True

            qmp = StaleSocketPath(root / "run-qmp.sock")

            result = cleanup_exact_qmp_processes(
                qmp,
                proc_root=proc_root,
                **fake_pidfd_arguments(
                    lambda _pidfd, _sig: self.fail("no process may be signalled")
                ),
                timeout_seconds=0.01,
                sleeper=lambda _seconds: None,
            )

            self.assertTrue(result.qmp_socket_removed)
            self.assertTrue(qmp.removed)
            self.assertEqual((), result.errors)

    def test_postflight_verifies_processes_ports_and_missing_qmp_independently(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            qmp = root / "qmp-0399.sock"
            errors = verify_postflight(
                run_dir=root,
                qmp=qmp,
                ports=(10930, 10931, 10932),
                process_reader=lambda: [],
                listening_ports_reader=lambda: set(),
            )

            self.assertEqual((), errors)
            report = (root / "FLR-0399-postflight.log").read_text(encoding="utf-8")
            self.assertIn("qmp=ABSENT", report)
            self.assertIn("processes=0", report)
            self.assertIn("ports=10930,10931,10932:FREE", report)
            self.assertIn("FLR0399_POSTFLIGHT=PASS", report)

    def test_postflight_fails_closed_for_residual_target_or_port_listener(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            qmp = root / "qmp-0399.sock"
            errors = verify_postflight(
                run_dir=root,
                qmp=qmp,
                ports=(10930, 10931),
                process_reader=lambda: ["pid=75 comm=qemu-system-x86_64 args=runqemu"],
                listening_ports_reader=lambda: {10931},
            )

            self.assertTrue(any("runtime-process-residual" in error for error in errors))
            self.assertTrue(any("port-listener:10931" in error for error in errors))
            report = (root / "FLR-0399-postflight.log").read_text(encoding="utf-8")
            self.assertIn("FLR0399_POSTFLIGHT=FAIL", report)

    def test_postflight_fails_closed_when_process_or_port_scan_is_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def unavailable():
                raise OSError("scanner unavailable")

            errors = verify_postflight(
                run_dir=root,
                qmp=root / "qmp-0399.sock",
                ports=(10930,),
                process_reader=unavailable,
                listening_ports_reader=unavailable,
            )

            self.assertTrue(any("process-scan-unavailable" in error for error in errors))
            self.assertTrue(any("port-scan-unavailable" in error for error in errors))
            report = (root / "FLR-0399-postflight.log").read_text(encoding="utf-8")
            self.assertIn("ports=UNKNOWN", report)
            self.assertIn("FLR0399_POSTFLIGHT=FAIL", report)

    def test_postflight_failure_is_retained_when_final_recheck_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            qmp = root / "qmp-0399.sock"
            before = "FLR-0399-postflight-before-cleanup.log"
            final = "FLR-0399-postflight-final.log"

            first_errors = verify_postflight(
                run_dir=root,
                qmp=qmp,
                process_reader=lambda: ["qemu-system-x86_64 residual"],
                listening_ports_reader=lambda: {10930},
                report_name=before,
            )
            second_errors = verify_postflight(
                run_dir=root,
                qmp=qmp,
                process_reader=lambda: [],
                listening_ports_reader=lambda: set(),
                report_name=final,
            )

            self.assertIn("runtime-process-residual", first_errors)
            self.assertIn("port-listener:10930", first_errors)
            self.assertEqual((), second_errors)
            self.assertIn("FLR0399_POSTFLIGHT=FAIL", (root / before).read_text())
            self.assertIn("FLR0399_POSTFLIGHT=PASS", (root / final).read_text())
            self.assertIn("qemu-system-x86_64 residual", (root / before).read_text())

    def test_guest_exit_stays_inside_child_and_serial_completion_marker_survives(self):
        marker = "__FLR_SERIAL_COMMAND_DONE_7B31__"
        for child_status in (0, 23):
            with self.subTest(child_status=child_status):
                child = wrap_serial_child_command(
                    f"set -eu; printf CHILD_RAN; exit {child_status}"
                )
                parent = (
                    "stty() { :; }; "
                    f"{child}; rc=$?; stty echo; "
                    f"printf '\\nrc=%s\\n{marker}\\n' \"$rc\""
                )
                result = subprocess.run(
                    ["bash", "-c", parent],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("CHILD_RAN", result.stdout)
                self.assertIn(f"rc={child_status}", result.stdout)
                self.assertIn(marker, result.stdout)

    def test_evidence_collection_fails_closed_on_missing_log_or_failed_queries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "bin"
            tools.mkdir()
            log = root / "flr0399-0001-gdb.log"

            def install_tool(name, body):
                tool = tools / name
                tool.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
                tool.chmod(0o755)

            install_tool("sha256sum", "printf 'fixture-sha  %s\\n' \"$1\"")
            install_tool(
                "journalctl",
                "case \" $* \" in *COREDUMP_EXE=*) :;; *) printf 'kernel journal empty\\n';; esac",
            )
            install_tool("coredumpctl", "exit 0")
            environment = os.environ.copy()
            environment["PATH"] = f"{tools}{os.pathsep}{environment['PATH']}"
            command = evidence_collect_command(str(log), "flr0399-0001")

            missing = subprocess.run(
                ["sh", "-c", command], env=environment, capture_output=True, text=True
            )
            self.assertNotEqual(0, missing.returncode)
            self.assertIn("FLR0399_GDB_LOG=UNAVAILABLE", missing.stdout)
            self.assertNotIn("FLR0399_EVIDENCE_COLLECT=PASS", missing.stdout)

            log.write_text("bounded gdb evidence\n", encoding="utf-8")
            install_tool("journalctl", "printf 'journal access denied\\n' >&2; exit 17")
            journal_failure = subprocess.run(
                ["sh", "-c", command], env=environment, capture_output=True, text=True
            )
            self.assertNotEqual(0, journal_failure.returncode)
            self.assertIn("FLR0399_KERNEL_QUERY=FAIL rc=17", journal_failure.stdout)
            self.assertIn("journal access denied", journal_failure.stdout)
            self.assertNotIn("FLR0399_EVIDENCE_COLLECT=PASS", journal_failure.stdout)

            install_tool(
                "journalctl",
                "case \" $* \" in *COREDUMP_EXE=*) printf 'focused coredump journal unavailable\\n' >&2; exit 23;; *) printf 'kernel journal empty\\n';; esac",
            )
            focused_journal_failure = subprocess.run(
                ["sh", "-c", command], env=environment, capture_output=True, text=True
            )
            self.assertNotEqual(0, focused_journal_failure.returncode)
            self.assertIn(
                "FLR0399_COREDUMP_QUERY=FAIL journal_rc=23",
                focused_journal_failure.stdout,
            )
            self.assertIn(
                "focused coredump journal unavailable",
                focused_journal_failure.stdout,
            )
            self.assertNotIn(
                "FLR0399_EVIDENCE_COLLECT=PASS", focused_journal_failure.stdout
            )

            install_tool(
                "journalctl",
                "case \" $* \" in *COREDUMP_EXE=*) printf '{\\\"COREDUMP_EXE\\\":\\\"/usr/bin/flutter-auto\\\"}\\n';; *) printf 'kernel journal empty\\n';; esac",
            )
            install_tool("coredumpctl", "printf 'coredump index unavailable\\n' >&2; exit 19")
            coredump_failure = subprocess.run(
                ["sh", "-c", command], env=environment, capture_output=True, text=True
            )
            self.assertNotEqual(0, coredump_failure.returncode)
            self.assertIn("FLR0399_COREDUMP_QUERY=FAIL rc=19", coredump_failure.stdout)
            self.assertIn("coredump index unavailable", coredump_failure.stdout)
            self.assertNotIn("FLR0399_EVIDENCE_COLLECT=PASS", coredump_failure.stdout)

            install_tool(
                "journalctl",
                "case \" $* \" in *COREDUMP_EXE=*) :;; *) printf 'kernel journal empty\\n';; esac",
            )
            install_tool("coredumpctl", "exit 0")
            empty_success = subprocess.run(
                ["sh", "-c", command], env=environment, capture_output=True, text=True
            )
            self.assertEqual(0, empty_success.returncode, empty_success.stderr)
            self.assertIn("FLR0399_KERNEL_QUERY=EMPTY", empty_success.stdout)
            self.assertIn("FLR0399_COREDUMP_QUERY=EMPTY", empty_success.stdout)
            self.assertIn("FLR0399_EVIDENCE_COLLECT=PASS", empty_success.stdout)

    def test_run_directory_is_ticket_scoped_under_the_explicit_evidence_role(self):
        with tempfile.TemporaryDirectory() as evidence_root:
            expected = expected_run_dir(Path(evidence_root), "flr0399-0001")
            self.assertEqual(
                Path(evidence_root).resolve() / "flr0399-0001" / "qemu", expected
            )

        with tempfile.TemporaryDirectory() as evidence_root:
            expected = expected_run_dir(Path(evidence_root), "flr0401-0001")
            self.assertEqual(
                Path(evidence_root).resolve() / "flr0401-0001" / "qemu", expected
            )

        with tempfile.TemporaryDirectory() as evidence_root:
            with self.assertRaises(ValueError):
                expected_run_dir(Path(evidence_root), "../flr0399-0001")

    def test_generated_commands_parse_as_bash_and_posix_sh(self):
        for run_id in ("flr0399-0001", "flr0400-0001", "flr0401-0001"):
            for launch_mode in ("gdb-run", "direct"):
                commands = guest_commands(run_id, launch_mode=launch_mode)
                for shell in ("bash", "sh"):
                    for name, command in commands.__dict__.items():
                        if (
                            not isinstance(command, str)
                            or name.endswith("_path")
                            or name == "present_stack_script"
                        ):
                            continue
                        with self.subTest(
                            run_id=run_id,
                            launch_mode=launch_mode,
                            shell=shell,
                            command=name,
                        ):
                            result = subprocess.run(
                                [shell, "-n", "-c", command],
                                check=False,
                                capture_output=True,
                                text=True,
                            )
                            self.assertEqual(0, result.returncode, result.stderr)

    def test_default_gdb_run_launch_command_is_byte_for_byte_unchanged(self):
        commands = guest_commands("flr0400-0001")

        self.assertEqual(
            "132c0299c7f04835b72c61fa35272040f4f61d3aadec49f0deeee1d3676deade",
            hashlib.sha256(commands.launch.encode()).hexdigest(),
        )

    def test_direct_launch_keeps_the_exact_demo_profile_without_gdb_parent(self):
        commands = guest_commands("flr0401-0001", launch_mode="direct")
        launch = commands.launch

        self.assertIn("su -s /bin/sh agl-driver", launch)
        self.assertIn("test \"$(id -u agl-driver)\" = 1001", launch)
        self.assertIn("XDG_RUNTIME_DIR=/run/user/1001", launch)
        self.assertIn("WAYLAND_DISPLAY=wayland-0", launch)
        self.assertIn("FLR0026_NATIVE_MODEL_MATCH=sequoia", launch)
        self.assertIn("FLR0026_NATIVE_MODEL_LIMIT=2", launch)
        self.assertIn("FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1", launch)
        self.assertIn("FLR0305_PRODUCTION_SCENE_LIGHT=1", launch)
        self.assertIn("/usr/bin/timeout --signal=TERM --kill-after=2s 150", launch)
        self.assertIn("/usr/bin/flutter-auto -b", launch)
        self.assertIn(
            "/usr/share/flutter/toyota-connected-tcna-packages-filament-scene-"
            "fluorite-examples-demo/3.32.5/release",
            launch,
        )
        self.assertIn('test ! -e "$log" && : >"$log" || exit 1;', launch)
        self.assertIn('>>"$log" 2>&1', launch)
        self.assertNotIn('>"$log" 2>&1', launch.replace('>>"$log" 2>&1', ""))
        self.assertIn("printf '%s %s %s %s %s\\n'", launch)
        self.assertIn('"$pid" "$uid" "$start"', launch)
        self.assertNotIn("/usr/bin/gdb -q --batch", launch)
        self.assertNotIn("--args", launch)
        self.assertIn(commands.log_path, commands.ready)
        self.assertIn("command -v base64", commands.preflight)
        self.assertIn("command -v sha256sum", commands.preflight)
        self.assertIn(commands.present_stack_script_path, commands.preflight)

    def test_present_stack_command_is_identity_and_unmatched_gated_and_bounded(self):
        commands = guest_commands("flr0401-0001", launch_mode="direct")
        command = commands.capture_present_stack

        self.assertIn(commands.log_path, command)
        self.assertIn(commands.identity_path, command)
        self.assertIn(commands.present_stack_script_path, command)
        self.assertIn('trap \'rm -f "$script"\' EXIT', command)
        self.assertIn(commands.present_stack_script_path, commands.prepare_present_stack)
        self.assertIn(commands.present_stack_script_path, commands.cleanup_present_stack)
        encoded = re.search(
            r"printf '%s' ([A-Za-z0-9+/=]+) \| base64 -d",
            commands.prepare_present_stack,
        )
        self.assertIsNotNone(encoded)
        self.assertEqual(
            commands.present_stack_script.encode(),
            base64.b64decode(encoded.group(1)),
        )
        self.assertIn("FLR0401_GDB_SCRIPT=READY sha256=", commands.prepare_present_stack)
        self.assertIn(
            hashlib.sha256(commands.present_stack_script.encode()).hexdigest(),
            commands.prepare_present_stack,
        )
        self.assertIn("FLR0401_GDB_SCRIPT=CLEANED", commands.cleanup_present_stack)
        self.assertIn('read pid saved_uid saved_start wrapper saved_wrapper_start', command)
        self.assertIn('uid=$(awk', command)
        self.assertIn('start=$(awk', command)
        self.assertIn("PRESENT_BEGIN", command)
        self.assertIn("FLR0026_VK_QUEUE_PRESENT result=", command)
        self.assertIn("present_return=%s", command)
        self.assertIn('if [ "$begins" -le "$returns" ]', command)
        self.assertLess(
            command.index('if [ "$begins" -le "$returns" ]'),
            command.index("/usr/bin/gdb"),
        )
        self.assertIn(
            'timeout --signal=TERM --kill-after=2s __FLR0401_GDB_TIMEOUT__',
            command,
        )
        rendered_short = live_capture.render_present_stack_command(command, 5)
        rendered_max = live_capture.render_present_stack_command(command, 18)
        self.assertIn('timeout --signal=TERM --kill-after=2s 5', rendered_short)
        self.assertIn('timeout --signal=TERM --kill-after=2s 18', rendered_max)
        for rendered in (rendered_short, rendered_max):
            self.assertEqual(0, subprocess.run(["sh", "-n"], input=rendered, text=True).returncode)
        self.assertIn('FLR0401_EXPECTED_PID="$pid"', command)
        self.assertIn('FLR0401_EXPECTED_UID="$saved_uid"', command)
        self.assertIn('FLR0401_EXPECTED_START="$saved_start"', command)
        gdb_begin = command.index("/usr/bin/gdb ")
        gdb_end = command.index(' >>"$log" 2>&1', gdb_begin)
        gdb_argv = shlex.split(command[gdb_begin:gdb_end])
        self.assertEqual("/usr/bin/gdb", gdb_argv[0])
        self.assertIn("--nx", gdb_argv)
        self.assertLess(gdb_argv.index("-iex"), gdb_argv.index("-p"))
        self.assertEqual("$pid", gdb_argv[gdb_argv.index("-p") + 1])
        self.assertIn("set sysroot /", gdb_argv)
        self.assertIn("set solib-absolute-prefix /", gdb_argv)
        self.assertIn("set solib-search-path /usr/lib:/lib", gdb_argv)
        self.assertIn("set auto-solib-add off", gdb_argv)
        self.assertEqual("$pid", gdb_argv[gdb_argv.index("-p") + 1])
        self.assertEqual("$script", gdb_argv[gdb_argv.index("-x") + 1])
        self.assertGreater(gdb_argv.index("-x"), gdb_argv.index("-p"))
        python_blocks = []
        active_block = None
        for line in commands.present_stack_script.splitlines():
            if active_block is None and line == "python":
                active_block = []
            elif active_block is not None and line == "end":
                python_blocks.append("\n".join(active_block))
                active_block = None
            elif active_block is not None:
                active_block.append(line)
        self.assertIsNone(active_block)
        self.assertEqual(2, len(python_blocks))
        for block in python_blocks:
            compile(block, "<generated-gdb-python>", "exec")
        identity_source, stack_source = python_blocks
        self.assertIn("gdb.selected_inferior().pid", identity_source)
        self.assertIn("FLR0401_EXPECTED_PID", identity_source)
        self.assertIn("/proc/%d/stat", identity_source)
        self.assertIn("FLR0401_EXPECTED_START", identity_source)
        self.assertIn("comm", identity_source)
        self.assertIn("gdb.execute('quit 4')", identity_source)
        self.assertLess(
            commands.present_stack_script.index("gdb.selected_inferior().pid"),
            commands.present_stack_script.index("sharedlibrary libvulkan_lvp[.]so"),
        )
        self.assertIn("t.name=='FEngine::loop'", stack_source)
        self.assertIn("gdb.execute('bt 8'", stack_source)
        self.assertIn("'lvp_pipe_sync_wait' in stack", stack_source)
        self.assertIn("gdb.execute('bt 24'", stack_source)
        self.assertIn("FLR0401_STACK_COLLECTION=NO_MATCHING_THREAD", stack_source)
        self.assertIn("FLR0401_STACK_COLLECTION=PARTIAL", stack_source)
        self.assertIn("FLR0401_STACK_COLLECTION=COMPLETE", stack_source)
        self.assertNotIn("thread apply all", stack_source)
        self.assertIn('>>"$log" 2>&1', command)
        self.assertIn('elif [ "$rc" -eq 4 ]; then result=IDENTITY_CHANGED;', command)
        self.assertIn('elif [ "$rc" -eq 5 ]; then result=NO_MATCHING_THREAD;', command)
        self.assertIn('elif [ "$rc" -eq 6 ]; then result=STACK_INCOMPLETE;', command)
        self.assertIn("FLR0401_GDB_CAPTURE_RESULT=", command)
        self.assertNotIn("\n", command)
        self.assertLessEqual(len(command), 4096)
        self.assertLessEqual(len(wrap_serial_child_command(command)), 4096)
        self.assertLessEqual(len(commands.prepare_present_stack), 4096)
        self.assertLessEqual(
            len(wrap_serial_child_command(commands.prepare_present_stack)), 4096
        )

    def test_nonzero_gdb_diagnostic_returns_completed_serial_command_with_marker(self):
        run_id = "flr0401-0099"
        commands = guest_commands(run_id, launch_mode="direct")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            guest_root = root / "guest"
            guest_run = guest_root / "run/user/1001"
            proc_root = root / "proc"
            tools = root / "bin"
            guest_run.mkdir(parents=True)
            proc = proc_root / "694"
            proc.mkdir(parents=True)
            tools.mkdir()
            (guest_run / f"{run_id}-gdb.log").write_text(
                "FLR0026_VK_QUEUE_PRESENT_BEGIN\n", encoding="utf-8"
            )
            (guest_run / f"{run_id}-app.identity").write_text(
                "694 1001 23470 0 0\n", encoding="utf-8"
            )
            (guest_run / f"{run_id}-present-stack.gdb").write_text(
                "prepared gdb script\n", encoding="utf-8"
            )
            (proc / "comm").write_text("flutter-auto\n", encoding="utf-8")
            (proc / "status").write_text(
                "Name:\tflutter-auto\nUid:\t1001\t1001\t1001\t1001\n",
                encoding="utf-8",
            )
            stat_fields = ["S", *(["0"] * 18), "23470"]
            (proc / "stat").write_text(
                f"694 (flutter-auto) {' '.join(stat_fields)}\n", encoding="utf-8"
            )
            timeout = tools / "timeout"
            timeout.write_text(
                "#!/bin/sh\n"
                "[ \"$1\" = --signal=TERM ] && shift\n"
                "[ \"$1\" = --kill-after=2s ] && shift\n"
                "shift\n"
                "exec \"$@\"\n",
                encoding="utf-8",
            )
            timeout.chmod(0o755)
            gdb = tools / "gdb"
            gdb_called = root / "gdb-called"
            gdb.write_text(
                f"#!/bin/sh\nprintf called >{shlex.quote(str(gdb_called))}\nexit 5\n",
                encoding="utf-8",
            )
            gdb.chmod(0o755)

            command = live_capture.render_present_stack_command(
                commands.capture_present_stack, 5
            )
            command = command.replace("/run/user/1001", str(guest_run))
            command = command.replace("/proc/", f"{proc_root}/")
            command = command.replace("/usr/bin/timeout", str(timeout))
            command = command.replace("/usr/bin/gdb", str(gdb))
            result = subprocess.run(
                ["sh", "-c", command], capture_output=True, text=True, check=False
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(
                "FLR0401_GDB_CAPTURE_RESULT=NO_MATCHING_THREAD rc=5 pid=694",
                result.stdout,
            )
            self.assertIn(
                "FLR0401_GDB_CAPTURE_RESULT=NO_MATCHING_THREAD rc=5 pid=694",
                (guest_run / f"{run_id}-gdb.log").read_text(),
            )
            self.assertTrue(gdb_called.exists())
            self.assertFalse((guest_run / f"{run_id}-present-stack.gdb").exists())

            (guest_run / f"{run_id}-gdb.log").write_text(
                "FLR0026_VK_QUEUE_PRESENT_BEGIN\nFLR0026_VK_QUEUE_PRESENT result=0\n",
                encoding="utf-8",
            )
            (guest_run / f"{run_id}-present-stack.gdb").write_text(
                "prepared gdb script\n", encoding="utf-8"
            )
            gdb_called.unlink()
            matched = subprocess.run(
                ["sh", "-c", command], capture_output=True, text=True, check=False
            )

            self.assertEqual(0, matched.returncode, matched.stderr)
            self.assertIn("FLR0401_GDB_CAPTURE_RESULT=PRESENT_MATCHED", matched.stdout)
            self.assertIn(
                "FLR0401_GDB_CAPTURE_RESULT=PRESENT_MATCHED",
                (guest_run / f"{run_id}-gdb.log").read_text(),
            )
            self.assertFalse(gdb_called.exists())
            self.assertFalse((guest_run / f"{run_id}-present-stack.gdb").exists())

    def test_stack_script_never_reports_complete_without_a_collected_frame(self):
        commands = guest_commands("flr0401-0001", launch_mode="direct")
        blocks = []
        active = None
        for line in commands.present_stack_script.splitlines():
            if active is None and line == "python":
                active = []
            elif active is not None and line == "end":
                blocks.append("\n".join(active))
                active = None
            elif active is not None:
                active.append(line)
        stack_source = blocks[1]

        class GdbQuit(Exception):
            pass

        class Thread:
            num = 1
            name = "FEngine::loop"

            def switch(self):
                return None

        def evaluate(threads, stack_output):
            def execute(command, to_string=False):
                if command == "bt 8":
                    if isinstance(stack_output, Exception):
                        raise stack_output
                    return stack_output
                if command.startswith("quit "):
                    raise GdbQuit(command)
                return ""

            fake_gdb = SimpleNamespace(
                selected_inferior=lambda: SimpleNamespace(threads=lambda: threads),
                execute=execute,
            )
            output = io.StringIO()
            with mock.patch.dict(sys.modules, {"gdb": fake_gdb}):
                with redirect_stdout(output):
                    try:
                        exec(stack_source, {})
                    except GdbQuit as exc:
                        return str(exc), output.getvalue()
            return "returned", output.getvalue()

        no_threads_exit, no_threads_output = evaluate([], "#0 unused\n")
        no_frame_exit, no_frame_output = evaluate([Thread()], "No stack.\n")
        command_error_exit, command_error_output = evaluate(
            [Thread()], RuntimeError("backtrace unavailable")
        )
        complete_exit, complete_output = evaluate([Thread()], "#0 0x1234 in frame\n")

        self.assertEqual("quit 5", no_threads_exit)
        self.assertIn("FLR0401_STACK_COLLECTION=NO_MATCHING_THREAD", no_threads_output)
        self.assertEqual("quit 6", no_frame_exit)
        self.assertIn("FLR0401_STACK_COLLECTION=NO_STACK", no_frame_output)
        self.assertEqual("quit 6", command_error_exit)
        self.assertIn("FLR0401_STACK_COLLECTION=NO_STACK", command_error_output)
        self.assertNotIn("FLR0401_STACK_COLLECTION=COMPLETE", no_threads_output)
        self.assertNotIn("FLR0401_STACK_COLLECTION=COMPLETE", no_frame_output)
        self.assertNotIn("FLR0401_STACK_COLLECTION=COMPLETE", command_error_output)
        self.assertEqual("returned", complete_exit)
        self.assertIn("FLR0401_STACK_COLLECTION=COMPLETE count=1", complete_output)

    def test_gdb_identity_script_rejects_a_reused_pid_before_stack_inspection(self):
        commands = guest_commands("flr0401-0001", launch_mode="direct")
        identity_source = []
        active = False
        for line in commands.present_stack_script.splitlines():
            if not active and line == "python":
                active = True
                continue
            if active and line == "end":
                break
            if active:
                identity_source.append(line)
        source = "\n".join(identity_source)

        class GdbQuit(Exception):
            pass

        def run(saved_start, actual_start):
            calls = []
            fake_gdb = SimpleNamespace(
                selected_inferior=lambda: SimpleNamespace(pid=694),
                execute=lambda command, **_kwargs: (
                    calls.append(command),
                    (_ for _ in ()).throw(GdbQuit(command))
                    if command.startswith("quit ")
                    else "",
                )[1],
            )
            stat_fields = ["S", *("0" for _ in range(18)), str(actual_start)]
            proc_files = {
                "/proc/694/status": "Name:\tflutter-auto\nUid:\t1001\t1001\t1001\t1001\n",
                "/proc/694/stat": f"694 (flutter-auto) {' '.join(stat_fields)}\n",
                "/proc/694/comm": "flutter-auto\n",
            }

            def open_proc(path, *_args, **_kwargs):
                return io.StringIO(proc_files[path])

            output = io.StringIO()
            environment = {
                "FLR0401_EXPECTED_PID": "694",
                "FLR0401_EXPECTED_UID": "1001",
                "FLR0401_EXPECTED_START": str(saved_start),
            }
            with mock.patch.dict(sys.modules, {"gdb": fake_gdb}):
                with mock.patch.dict(os.environ, environment):
                    with mock.patch("builtins.open", side_effect=open_proc):
                        with redirect_stdout(output):
                            try:
                                exec(source, {})
                            except GdbQuit as exc:
                                return str(exc), output.getvalue(), calls
            return "returned", output.getvalue(), calls

        same_exit, same_output, same_calls = run(23470, 23470)
        reused_exit, reused_output, reused_calls = run(23470, 23471)

        self.assertEqual("returned", same_exit)
        self.assertIn("FLR0401_GDB_IDENTITY=PASS", same_output)
        self.assertEqual("quit 4", reused_exit)
        self.assertIn("FLR0401_GDB_CAPTURE_RESULT=IDENTITY_CHANGED", reused_output)
        self.assertEqual(["detach", "quit 4"], reused_calls)
        self.assertNotIn("detach", same_calls)

    def test_observe_cli_accepts_and_passes_the_direct_launch_mode(self):
        with mock.patch.object(live_capture, "observe", return_value=0) as observer:
            result = live_capture.main(
                [
                    "observe",
                    "--run-id",
                    "flr0401-0001",
                    "--evidence-root",
                    "/evidence",
                    "--run-dir",
                    "/evidence/flr0401-0001/qemu",
                    "--qmp",
                    "/evidence/flr0401-0001/qemu/qmp.sock",
                    "--launch-mode",
                    "direct",
                ]
            )

        self.assertEqual(0, result)
        self.assertEqual("direct", observer.call_args.args[0].launch_mode)

    def test_observe_passes_the_selected_mode_into_guest_command_builder(self):
        with tempfile.TemporaryDirectory() as evidence_root:
            run_dir = Path(evidence_root) / "flr0401-0001" / "qemu"
            args = SimpleNamespace(
                run_id="flr0401-0001",
                launch_mode="direct",
                evidence_root=Path(evidence_root),
                run_dir=run_dir,
                qmp=run_dir / "qmp.sock",
            )
            with mock.patch.object(
                live_capture, "guest_commands", wraps=guest_commands
            ) as command_builder:
                with self.assertRaises(FileNotFoundError):
                    live_capture.observe(args)

        command_builder.assert_called_once_with(
            "flr0401-0001", launch_mode="direct"
        )

    def test_direct_observer_prepares_and_cleans_the_run_scoped_gdb_script(self):
        run_id = "flr0401-0002"
        with tempfile.TemporaryDirectory() as evidence_root:
            run_dir = Path(evidence_root) / run_id / "qemu"
            run_dir.mkdir(parents=True)
            qmp = run_dir / "qmp.sock"
            commands = guest_commands(run_id, launch_mode="direct")
            args = SimpleNamespace(
                run_id=run_id,
                launch_mode="direct",
                evidence_root=Path(evidence_root),
                run_dir=run_dir,
                qmp=qmp,
                serial_port=5555,
                timeout_seconds=30.0,
            )
            serial_calls = []
            responses = {
                "preflight": "FLR0399_GUEST_PREFLIGHT=PASS\n",
                "launch": "FLR0399_LAUNCH=PASS\n",
                "present-stack-script": "FLR0401_GDB_SCRIPT=READY sha256=test\n",
                "ready-001": f"FLR0399_STATE=TIMEOUT LOG_PATH={commands.log_path}\n",
                "collect": "FLR0399_EVIDENCE_COLLECT=PASS\n",
                "stop": "FLR0399_APP_STOP=NOT_LAUNCHED\n",
                "present-stack-cleanup": "FLR0401_GDB_SCRIPT=CLEANED\n",
            }

            def serial_exec(*, label, command, **_kwargs):
                serial_calls.append((label, command))
                return responses[label]

            with mock.patch.object(Path, "is_socket", return_value=True):
                with mock.patch.object(live_capture, "_serial_exec", side_effect=serial_exec):
                    with mock.patch.object(live_capture, "_capture_qmp"):
                        with mock.patch.object(live_capture, "verify_postflight", return_value=()):
                            with mock.patch.object(
                                live_capture.subprocess,
                                "run",
                                return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                            ):
                                with redirect_stdout(io.StringIO()):
                                    result = live_capture.observe(args)
        labels = [label for label, _command in serial_calls]
        self.assertEqual(1, result)
        self.assertLess(labels.index("launch"), labels.index("present-stack-script"))
        self.assertLess(labels.index("present-stack-script"), labels.index("ready-001"))
        self.assertLess(labels.index("stop"), labels.index("present-stack-cleanup"))
        self.assertIn(commands.prepare_present_stack, [command for _, command in serial_calls])
        self.assertIn(commands.cleanup_present_stack, [command for _, command in serial_calls])

    def test_direct_observer_never_cleans_a_script_when_preflight_rejects_it(self):
        run_id = "flr0401-0003"
        with tempfile.TemporaryDirectory() as evidence_root:
            run_dir = Path(evidence_root) / run_id / "qemu"
            run_dir.mkdir(parents=True)
            args = SimpleNamespace(
                run_id=run_id,
                launch_mode="direct",
                evidence_root=Path(evidence_root),
                run_dir=run_dir,
                qmp=run_dir / "qmp.sock",
                serial_port=5555,
                timeout_seconds=30.0,
            )
            serial_calls = []

            def serial_exec(*, label, **_kwargs):
                serial_calls.append(label)
                if label == "preflight":
                    return "FLR0399_GUEST_PREFLIGHT=FAIL existing-script\n"
                if label == "collect":
                    return "FLR0399_EVIDENCE_COLLECT=PASS\n"
                if label == "stop":
                    return "FLR0399_APP_STOP=NOT_LAUNCHED\n"
                if label == "present-stack-cleanup":
                    return "FLR0401_GDB_SCRIPT=CLEANED\n"
                raise AssertionError(f"unexpected serial command: {label}")

            with mock.patch.object(Path, "is_socket", return_value=True):
                with mock.patch.object(live_capture, "_serial_exec", side_effect=serial_exec):
                    with mock.patch.object(live_capture, "_capture_qmp"):
                        with mock.patch.object(live_capture, "verify_postflight", return_value=()):
                            with mock.patch.object(
                                live_capture.subprocess,
                                "run",
                                return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                            ):
                                with redirect_stdout(io.StringIO()):
                                    result = live_capture.observe(args)

        self.assertEqual(1, result)
        self.assertEqual(["preflight", "collect", "stop"], serial_calls)
        self.assertNotIn("present-stack-script", serial_calls)
        self.assertNotIn("present-stack-cleanup", serial_calls)

    def test_unconfirmed_guest_gdb_completion_skips_guest_serial_and_quits_owned_qemu(self):
        run_id = "flr0401-0004"
        with tempfile.TemporaryDirectory() as evidence_root:
            run_dir = Path(evidence_root) / run_id / "qemu"
            run_dir.mkdir(parents=True)
            commands = guest_commands(run_id, launch_mode="direct")
            args = SimpleNamespace(
                run_id=run_id,
                launch_mode="direct",
                evidence_root=Path(evidence_root),
                run_dir=run_dir,
                qmp=run_dir / "qmp.sock",
                serial_port=5555,
                timeout_seconds=120.0,
            )
            live = (
                f"FLR0399_STATE=LIVE PID=694 UID=1001 START=23470 "
                f"LOG_PATH={commands.log_path}\n"
            )
            ready = (
                f"FLR0399_STATE=READY PID=694 UID=1001 START=23470 READY=1 "
                f"PRESENT_BEGIN=1 PRESENT_RETURN=0 SUN=1 LOG_PATH={commands.log_path}\n"
            )
            serial_calls = []

            def serial_exec(*, label, **_kwargs):
                serial_calls.append(label)
                if label == "preflight":
                    return "FLR0399_GUEST_PREFLIGHT=PASS\n"
                if label == "launch":
                    return "FLR0399_LAUNCH=PASS\n"
                if label == "present-stack-script":
                    return "FLR0401_GDB_SCRIPT=READY sha256=fixture\n"
                if label == "ready-001":
                    return ready
                if label in {
                    "identity-after-ready",
                    "identity-before-present-stack",
                    "identity-after-present-still",
                }:
                    return live
                if label == "present-stack":
                    raise TimeoutError("serial GDB completion marker unavailable")
                raise AssertionError(f"guest serial command continued after GDB uncertainty: {label}")

            with mock.patch.object(Path, "is_socket", return_value=True):
                with mock.patch.object(live_capture, "_serial_exec", side_effect=serial_exec):
                    with mock.patch.object(live_capture, "_capture_qmp"):
                        with mock.patch.object(live_capture, "verify_postflight", return_value=()):
                            with mock.patch.object(
                                live_capture.subprocess,
                                "run",
                                return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                            ) as qmp_quit:
                                with redirect_stdout(io.StringIO()):
                                    result = live_capture.observe(args)
            safety_log = (run_dir / "FLR-0399-guest-serial-safety.log").read_text()

        self.assertEqual(1, result)
        self.assertEqual(
            [
                "preflight",
                "launch",
                "present-stack-script",
                "ready-001",
                "identity-after-ready",
                "identity-before-present-stack",
                "identity-after-present-still",
                "present-stack",
            ],
            serial_calls,
        )
        self.assertEqual(1, qmp_quit.call_count)
        self.assertIn("GDB_COMPLETION_UNCONFIRMED", safety_log)

    def test_present_matched_marker_is_confirmed_and_guest_evidence_is_collected(self):
        run_id = "flr0401-0005"
        with tempfile.TemporaryDirectory() as evidence_root:
            run_dir = Path(evidence_root) / run_id / "qemu"
            run_dir.mkdir(parents=True)
            commands = guest_commands(run_id, launch_mode="direct")
            args = SimpleNamespace(
                run_id=run_id,
                launch_mode="direct",
                evidence_root=Path(evidence_root),
                run_dir=run_dir,
                qmp=run_dir / "qmp.sock",
                serial_port=5555,
                timeout_seconds=120.0,
            )
            live = (
                f"FLR0399_STATE=LIVE PID=694 UID=1001 START=23470 "
                f"LOG_PATH={commands.log_path}\n"
            )
            ready = (
                f"FLR0399_STATE=READY PID=694 UID=1001 START=23470 READY=1 "
                f"PRESENT_BEGIN=1 PRESENT_RETURN=0 SUN=1 LOG_PATH={commands.log_path}\n"
            )
            presented = (
                f"FLR0399_STATE=PRESENT PID=694 UID=1001 START=23470 READY=1 "
                f"PRESENT_BEGIN=1 PRESENT_RETURN=1 SUN=1 LOG_PATH={commands.log_path}\n"
            )
            serial_calls = []

            def serial_exec(*, label, command, **_kwargs):
                serial_calls.append((label, command))
                if label == "preflight":
                    return "FLR0399_GUEST_PREFLIGHT=PASS\n"
                if label == "launch":
                    return "FLR0399_LAUNCH=PASS\n"
                if label == "present-stack-script":
                    return "FLR0401_GDB_SCRIPT=READY sha256=fixture\n"
                if label == "ready-001":
                    return ready
                if label in {
                    "identity-after-ready",
                    "identity-before-present-stack",
                    "identity-after-present-still",
                    "identity-after-present-stack",
                    "identity-after-present",
                }:
                    return live
                if label == "present-stack":
                    return "FLR0401_GDB_CAPTURE_RESULT=PRESENT_MATCHED\n"
                if label == "present-001":
                    return presented
                if label == "collect":
                    return "FLR0399_EVIDENCE_COLLECT=PASS\n"
                if label == "stop":
                    return "FLR0399_APP_STOP=REQUESTED\n"
                if label == "present-stack-cleanup":
                    return "FLR0401_GDB_SCRIPT=CLEANED\n"
                raise AssertionError(f"unexpected serial command: {label}")

            with mock.patch.object(Path, "is_socket", return_value=True):
                with mock.patch.object(live_capture, "_serial_exec", side_effect=serial_exec):
                    with mock.patch.object(live_capture, "_capture_qmp"):
                        with mock.patch.object(live_capture, "verify_postflight", return_value=()):
                            with mock.patch.object(
                                live_capture.subprocess,
                                "run",
                                return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                            ) as qmp_quit:
                                with redirect_stdout(io.StringIO()):
                                    result = live_capture.observe(args)

        labels = [label for label, _command in serial_calls]
        self.assertEqual(0, result)
        self.assertIn("identity-after-present-stack", labels)
        self.assertLess(labels.index("present-stack"), labels.index("collect"))
        self.assertIn("collect", labels)
        self.assertIn("stop", labels)
        self.assertIn("present-stack-cleanup", labels)
        gdb_command = dict(serial_calls)["present-stack"]
        self.assertNotIn(live_capture.PRESENT_STACK_TIMEOUT_TOKEN, gdb_command)
        self.assertEqual(1, qmp_quit.call_count)

    def test_guest_command_builder_rejects_unknown_launch_mode(self):
        with self.assertRaisesRegex(ValueError, "launch mode must be gdb-run or direct"):
            guest_commands("flr0401-0001", launch_mode="gdbserver")

    def test_exact_image_qemu_start_helper_parses_as_bash(self):
        start_helper = Path(__file__).parents[1] / "work/commands/FLR-0399-qemu-start.sh"
        result = subprocess.run(
            ["bash", "-n", str(start_helper)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_qemu_start_helper_requires_explicit_build_roles(self):
        start_helper = Path(__file__).parents[1] / "work/commands/FLR-0399-qemu-start.sh"
        environment = os.environ.copy()
        for name in ("BUILD_DIR", "BUILD_TMPDIR", "BUILD_EVIDENCE"):
            environment.pop(name, None)
        environment["FLR0399_RUN_ID"] = "flr0401-0001"

        result = subprocess.run(
            ["bash", str(start_helper), "preflight"],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("BUILD_DIR-role-required", result.stderr)

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

    def test_state_parser_preserves_present_counters_for_live_gate_samples(self):
        sample = parse_state_output(
            "FLR0399_STATE=READY PID=694 UID=1001 START=23470 "
            "READY=1 PRESENT_BEGIN=3 PRESENT_RETURN=2 SUN=1 "
            "LOG_PATH=/run/user/1001/flr0401-0001-gdb.log\n",
            stage="ready",
        )

        self.assertEqual(1, sample.ready_count)
        self.assertEqual(3, sample.present_begin)
        self.assertEqual(2, sample.present_return)
        self.assertEqual(1, sample.sun_count)

    def test_state_parser_rejects_missing_duplicate_and_malformed_counters(self):
        valid = (
            "FLR0399_STATE=READY PID=694 UID=1001 START=23470 READY=1 "
            "PRESENT_BEGIN=3 PRESENT_RETURN=2 SUN=1 "
            "LOG_PATH=/run/user/1001/flr0401-0001-gdb.log\n"
        )
        malformed = {
            "missing-present-begin": valid.replace("PRESENT_BEGIN=3 ", ""),
            "duplicate-ready": valid.replace("READY=1 ", "READY=1 READY=2 "),
            "negative-sun": valid.replace("SUN=1", "SUN=-1"),
            "nonnumeric-present-return": valid.replace(
                "PRESENT_RETURN=2", "PRESENT_RETURN=two"
            ),
        }
        for label, marker in malformed.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    parse_state_output(marker, stage="ready")

    def test_waiting_marker_remains_a_pollable_state(self):
        for stage in ("ready", "present"):
            sample = parse_state_output(
                "FLR0399_STATE=WAITING PID=694 UID=1001 START=23470 "
                "READY=0 PRESENT_BEGIN=0 PRESENT_RETURN=0 SUN=0 "
                "LOG_PATH=/run/user/1001/flr0400-0001-gdb.log\n",
                stage=stage,
            )
            self.assertEqual("WAITING", sample.state)

        with self.assertRaises(ValueError):
            parse_state_output(
                "FLR0399_STATE=WAITING LOG_PATH=/run/user/1001/a.log\n",
                stage="ready",
            )

    def test_repeated_state_reads_get_unique_serial_evidence_labels(self):
        self.assertEqual("ready-001", state_poll_label("ready", 1))
        self.assertEqual("ready-002", state_poll_label("ready", 2))
        self.assertEqual("present-001", state_poll_label("present", 1))
        self.assertEqual("present-002", state_poll_label("present", 2))
        self.assertNotEqual(
            state_poll_label("present", 1), state_poll_label("present", 2)
        )
        with self.assertRaises(ValueError):
            state_poll_label("ready", 0)

    def test_state_reader_labels_repeated_present_waiting_snapshots_uniquely(self):
        log_path = "/run/user/1001/flr0400-0001-gdb.log"
        identity = "PID=694 UID=1001 START=23470"
        outputs = iter(
            [
                f"FLR0399_STATE=WAITING {identity} READY=0 PRESENT_BEGIN=0 "
                f"PRESENT_RETURN=0 SUN=0 LOG_PATH={log_path}\n",
                f"FLR0399_STATE=PRESENT {identity} READY=1 PRESENT_BEGIN=1 "
                f"PRESENT_RETURN=1 SUN=1 LOG_PATH={log_path}\n",
            ]
        )
        calls = []

        def serial(label, command, timeout_seconds):
            calls.append((label, command, timeout_seconds))
            return next(outputs)

        reader = make_state_reader(guest_commands("flr0400-0001"), serial)
        first = reader("present", 30)
        second = reader("present", 30)

        self.assertEqual(["WAITING", "PRESENT"], [first.state, second.state])
        self.assertEqual(["present-001", "present-002"], [call[0] for call in calls])
        self.assertEqual([15.0, 15.0], [call[2] for call in calls])

    def test_state_reader_routes_stack_identity_brackets_to_the_identity_command(self):
        commands = guest_commands("flr0401-0001", launch_mode="direct")
        log_path = commands.log_path
        identity_output = (
            f"FLR0399_STATE=LIVE PID=694 UID=1001 START=23470 "
            f"LOG_PATH={log_path}\n"
        )
        calls = []

        def serial(label, command, timeout_seconds):
            calls.append((label, command, timeout_seconds))
            return identity_output

        reader = make_state_reader(commands, serial)
        stages = (
            "identity-before-present-stack",
            "identity-after-present-still",
            "identity-after-present-stack",
        )
        samples = [reader(stage, 30) for stage in stages]

        self.assertTrue(all(sample.state == "LIVE" for sample in samples))
        self.assertEqual(list(stages), [call[0] for call in calls])
        self.assertTrue(all(call[1] == commands.identity for call in calls))
        self.assertEqual([15.0, 15.0, 15.0], [call[2] for call in calls])

    def test_first_live_frame_gets_one_video_and_later_frames_stay_stills(self):
        capture = make_frame_capture(
            Path("/evidence/flr0400-0001/qemu"),
            Path("/evidence/flr0400-0001/qemu/qmp-0400.sock"),
            "flr0400-0001",
        )
        identity = Identity(694, 1001, 23470)

        with mock.patch.object(live_capture, "_capture_qmp") as qmp_capture:
            capture("WAITING", identity, 90)
            capture("READY", identity, 80)
            capture("PRESENT", identity, 70)

        self.assertEqual(
            [True, False, False],
            [call.kwargs["video"] for call in qmp_capture.call_args_list],
        )
        self.assertEqual(
            [
                "flr0400-0001-waiting",
                "flr0400-0001-ready",
                "flr0400-0001-present",
            ],
            [call.args[2] for call in qmp_capture.call_args_list],
        )

    def test_guest_state_command_is_one_snapshot_not_a_poll_loop(self):
        commands = guest_commands("flr0400-0001")

        for command in (commands.ready, commands.present):
            with self.subTest(command=command):
                self.assertNotIn("sleep ", command)
                self.assertNotIn("seq 1", command)
                self.assertNotIn("for n in", command)
                self.assertNotIn("while ", command)

    def test_fresh_0400_run_uses_its_own_evidence_directory(self):
        commands = guest_commands("flr0400-0001")

        self.assertEqual(
            "/run/user/1001/flr0400-0001-gdb.log", commands.log_path
        )
        with tempfile.TemporaryDirectory() as evidence_root:
            expected = expected_run_dir(Path(evidence_root), "flr0400-0001")
            self.assertEqual(
                Path(evidence_root).resolve() / "flr0400-0001" / "qemu",
                expected,
            )

    def test_guest_command_builder_rejects_non_ticket_run_ids(self):
        for run_id in ("flr0396-0001", "flr0399-0", "../flr0399-0001", ""):
            with self.subTest(run_id=run_id):
                with self.assertRaises(ValueError):
                    guest_commands(run_id)


if __name__ == "__main__":
    unittest.main()
