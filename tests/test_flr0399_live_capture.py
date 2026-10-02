import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
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

        self.assertEqual("PRESENT_DEADLINE_EXPIRED", result.status)
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
            with self.assertRaises(ValueError):
                expected_run_dir(Path(evidence_root), "../flr0399-0001")

    def test_generated_commands_parse_as_bash_and_posix_sh(self):
        for run_id in ("flr0399-0001", "flr0400-0001"):
            commands = guest_commands(run_id)
            for shell in ("bash", "sh"):
                for name, command in commands.__dict__.items():
                    if not isinstance(command, str) or name.endswith("_path"):
                        continue
                    with self.subTest(run_id=run_id, shell=shell, command=name):
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

    def test_qemu_start_helper_requires_explicit_build_roles(self):
        start_helper = Path(__file__).parents[1] / "work/commands/FLR-0399-qemu-start.sh"
        environment = os.environ.copy()
        for name in ("BUILD_DIR", "BUILD_TMPDIR", "BUILD_EVIDENCE"):
            environment.pop(name, None)
        environment["FLR0399_RUN_ID"] = "flr0400-0001"

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
                f"FLR0399_STATE=WAITING {identity} LOG_PATH={log_path}\n",
                f"FLR0399_STATE=PRESENT {identity} LOG_PATH={log_path}\n",
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
