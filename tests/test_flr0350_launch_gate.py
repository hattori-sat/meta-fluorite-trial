#!/usr/bin/env python3
"""Regression tests for the production FLR-0350 launch-gate predicate."""

from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
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
        "version": "2",
        "run_id": "flr0362-0001",
        "identity_record": "PASS",
        "identity_pid": "708",
        "identity_start": "10001",
        "identity_uid": "1001",
        "identity_dev": "17",
        "identity_ino": "88",
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
                accepted = validate_gate_output(
                    render(observation(arg1=actual_fd)), expected_run_id="flr0362-0001"
                )
                self.assertEqual(accepted["arg1"], actual_fd)

    def test_run_id_and_persisted_identity_must_match_expected_observation(self) -> None:
        with self.assertRaises(GateObservationError):
            validate_gate_output(
                render(observation()), expected_run_id="flr0362-0002"
            )
        for changes in (
            {"identity_record": "FAIL"},
            {"identity_pid": "709"},
            {"identity_start": "10002"},
            {"identity_uid": "0"},
            {"identity_dev": "18"},
            {"identity_ino": "89"},
            {"run_id": "flr0359-0001"},
        ):
            with self.subTest(changes=changes), self.assertRaises(
                GateObservationError
            ):
                validate_gate_output(
                    render(observation(**changes)), expected_run_id="flr0362-0001"
                )

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
            {"version": "1"},
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
    def _release_gate_fixture(
        self, root: Path, *, fault: str | None = None
    ) -> tuple[dict[str, str], Path, Path, int, tuple[str, str, str, str]]:
        user_dir = root / "user"
        root_dir = root / "root-owned"
        proc_root = root / "proc"
        fake_bin = root / "bin"
        for directory in (user_dir, root_dir, proc_root, fake_bin):
            directory.mkdir(mode=0o700)
        target_pid = "730001"
        gdb_pid = str(os.getpid())
        target_start = "1234567"
        gdb_start = "7654321"
        run_id = "flr0362-0001"
        gate = user_dir / "flr0350-go.fifo"
        decoy = user_dir / "other.fifo"
        os.mkfifo(gate, 0o600)
        os.mkfifo(decoy, 0o600)
        os.chmod(gate, 0o600)
        os.chmod(decoy, 0o600)
        gate_stat = os.stat(gate)

        def proc_stat(pid: str, state: str, start: str) -> str:
            return f"{pid} (fixture) " + " ".join(
                [state, *("0" for _ in range(18)), start]
            ) + "\n"

        target = proc_root / target_pid
        gdb = proc_root / gdb_pid
        for entry in (target, gdb):
            (entry / "fd").mkdir(parents=True)
        (target / "stat").write_text(proc_stat(target_pid, "t", target_start))
        (target / "comm").write_text("sh\n")
        (target / "status").write_text(
            f"Uid:\t1001\t1001\t1001\t1001\nTracerPid:\t{gdb_pid}\n"
        )
        (target / "fd" / "0").symlink_to(gate)
        (target / "fd" / "3").symlink_to(gate)
        (gdb / "stat").write_text(proc_stat(gdb_pid, "S", gdb_start))
        (gdb / "comm").write_text("gdb\n")
        (gdb / "status").write_text("Uid:\t0\t0\t0\t0\nTracerPid:\t0\n")

        (root_dir / "run.id").write_text(run_id + "\n")
        (root_dir / "fifo.identity").write_text(
            f"1 {run_id} {target_pid} {target_start} 1001 "
            f"{gate_stat.st_dev} {gate_stat.st_ino}\n"
        )
        (root_dir / "attach.auth").write_text(
            f"1 {run_id} {target_pid} {target_start} 1001 "
            f"{gate_stat.st_dev} {gate_stat.st_ino} {gdb_pid} {gdb_start}\n"
        )
        for record in root_dir.iterdir():
            record.chmod(0o600)

        (user_dir / "flr0350-flutter.pid").write_text(target_pid + "\n")
        (user_dir / "flr0350-wrapper.start").write_text(target_start + "\n")
        (user_dir / "flr0350-gdb.pid").write_text(gdb_pid + "\n")
        (user_dir / "flr0350-gdb.start").write_text(gdb_start + "\n")
        (user_dir / "flr0350-gdb-armed").write_text(
            f"FLR0350_GDB_ARMED=PASS target_pid={target_pid} gdb_pid={gdb_pid}\n"
        )

        fake_stat = fake_bin / "stat"
        fake_stat.write_text(
            "#!/bin/sh\n"
            "fmt=; target=; want_fmt=0\n"
            "for arg do\n"
            "  if [ \"$want_fmt\" = 1 ]; then fmt=$arg; want_fmt=0; continue; fi\n"
            "  case $arg in -L) ;; -c) want_fmt=1 ;; *) target=$arg ;; esac\n"
            "done\n"
            "result=$(python3 -c 'import os,sys; s=os.stat(sys.argv[2]); f=sys.argv[1]; m=oct(s.st_mode & 0o777)[2:]; "
            "print((\"0:%s\" % m) if f == \"%u:%a\" else (\"%s:%s\" % (s.st_dev,s.st_ino)))' \"$fmt\" \"$target\")\n"
            "printf '%s\\n' \"$result\"\n"
            "if [ \"${FLR0350_TEST_MUTATE_POST_OPEN:-0}\" = 1 ] && [ \"$fmt\" = '%d:%i' ] && "
            "[ \"$target\" = \"$FLR0350_WRITER_FD_PATH\" ]; then\n"
            "  n=$(cat \"$FLR0350_TEST_STAT_COUNT\" 2>/dev/null || echo 0); n=$((n + 1)); printf '%s\\n' \"$n\" >\"$FLR0350_TEST_STAT_COUNT\"\n"
            "  if [ \"$n\" -eq 2 ]; then cp \"$FLR0350_TEST_MUTATED_STAT\" \"$FLR0350_PROC_ROOT/$FLR0350_TEST_TARGET_PID/stat\"; fi\n"
            "fi\n"
        )
        fake_stat.chmod(0o755)
        fake_id = fake_bin / "id"
        fake_id.write_text("#!/bin/sh\nprintf '%s\\n' 1001\n")
        fake_id.chmod(0o755)

        common = ROOT / "work/commands/FLR-0350-gate-common.sh"
        release_text = (ROOT / "work/commands/FLR-0350-release-go.sh").read_text()
        source_line = ". /run/user/1001/FLR-0350-gate-common.sh || exit 80"
        release_text = release_text.replace(
            source_line, f'. "{common}" || exit 80', 1
        )
        if fault == "postwrite-record":
            needle = 'if ! flr0350_write_once "$FLR0350_ROOT_DIR/go.record" "$go_record"; then'
            release_text = release_text.replace(
                needle,
                'flr0350_write_once "$FLR0350_ROOT_DIR/go.record" "1 corrupt" || true\n    ' + needle,
                1,
            )
        release = root / "release-go.sh"
        release.write_text(release_text)

        if fault == "state":
            (target / "stat").write_text(proc_stat(target_pid, "S", target_start))
        elif fault in ("postopen-state", "postopen-start"):
            changed_state = "S" if fault == "postopen-state" else "t"
            changed_start = target_start if fault == "postopen-state" else target_start + "1"
            (root / "mutated-stat").write_text(
                proc_stat(target_pid, changed_state, changed_start)
            )
        elif fault == "fd0":
            (target / "fd" / "0").unlink()
            (target / "fd" / "0").symlink_to(decoy)
        elif fault == "fifo-swap":
            gate.unlink()
            os.mkfifo(gate, 0o600)
            os.chmod(gate, 0o600)
        elif fault == "missing-auth":
            (root_dir / "attach.auth").unlink()

        read_fd = os.open(gate, os.O_RDWR | os.O_NONBLOCK)
        env = os.environ.copy()
        env.update(
            FLR0350_USER_DIR=str(user_dir),
            FLR0350_ROOT_DIR=str(root_dir),
            FLR0350_PROC_ROOT=str(proc_root),
            FLR0350_WRITER_FD_PATH=str(gate if fault != "writer-fd" else decoy),
            PATH=f"{fake_bin}:{env['PATH']}",
        )
        if fault in ("postopen-state", "postopen-start"):
            env.update(
                FLR0350_TEST_MUTATE_POST_OPEN="1",
                FLR0350_TEST_STAT_COUNT=str(root / "stat-count"),
                FLR0350_TEST_MUTATED_STAT=str(root / "mutated-stat"),
                FLR0350_TEST_TARGET_PID=target_pid,
            )
        args = (target_pid, target_start, gdb_pid, gdb_start)
        return env, release, gate, read_fd, args

    def _run_inner_go(
        self, env: dict[str, str], release: Path, args: tuple[str, str, str, str]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/sh", str(release), "--write-go", *args],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def _read_fifo_now(self, descriptor: int) -> bytes:
        try:
            return os.read(descriptor, 64)
        except BlockingIOError:
            return b""

    def test_release_helper_writes_exact_go_for_run_bound_stopped_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            env, release, _, read_fd, args = self._release_gate_fixture(Path(temp))
            try:
                result = self._run_inner_go(env, release, args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("FLR0350_GO_WRITE=PASS", result.stdout)
                self.assertIn("FLR0350_GO_RECORD=PASS", result.stdout)
                self.assertEqual(self._read_fifo_now(read_fd), b"FLR0350_GO\n")
            finally:
                os.close(read_fd)

    def test_release_helper_prewrite_identity_faults_send_zero_bytes(self) -> None:
        for fault in (
            "state", "fd0", "writer-fd", "fifo-swap", "missing-auth",
            "postopen-state", "postopen-start",
        ):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                env, release, _, read_fd, args = self._release_gate_fixture(
                    Path(temp), fault=fault
                )
                try:
                    result = self._run_inner_go(env, release, args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self._read_fifo_now(read_fd), b"")
                    self.assertNotIn("FLR0350_GO_WRITE=PASS", result.stdout)
                finally:
                    os.close(read_fd)

    def test_release_helper_postwrite_record_failure_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            env, release, _, read_fd, args = self._release_gate_fixture(
                Path(temp), fault="postwrite-record"
            )
            try:
                result = self._run_inner_go(env, release, args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("FLR0350_GO_WRITE=PASS", result.stdout)
                self.assertIn(
                    "FLR0350_GO_RECORD=FAIL reason=publication-after-write",
                    result.stdout,
                )
                self.assertEqual(self._read_fifo_now(read_fd), b"FLR0350_GO\n")
            finally:
                os.close(read_fd)

    def test_outer_release_rechecks_fifo_swapped_after_its_precheck(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            env, release, gate, old_read_fd, _ = self._release_gate_fixture(Path(temp))
            fake_timeout = Path(env["PATH"].split(":", 1)[0]) / "timeout"
            fake_timeout.write_text(
                "#!/bin/sh\n"
                "shift\n"
                "if [ \"$1\" = /bin/sh ] && [ \"$3\" = --write-go ]; then\n"
                "  unlink \"$FLR0350_USER_DIR/flr0350-go.fifo\"\n"
                "  mkfifo \"$FLR0350_USER_DIR/flr0350-go.fifo\"\n"
                "  chmod 600 \"$FLR0350_USER_DIR/flr0350-go.fifo\"\n"
                "fi\n"
                "exec \"$@\"\n"
            )
            fake_timeout.chmod(0o755)
            try:
                result = subprocess.run(
                    ["/bin/sh", str(release)],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("FLR0350_GO=FAIL reason=writer-command", result.stdout)
                os.close(old_read_fd)
                old_read_fd = -1
                replacement_fd = os.open(gate, os.O_RDWR | os.O_NONBLOCK)
                try:
                    self.assertEqual(self._read_fifo_now(replacement_fd), b"")
                finally:
                    os.close(replacement_fd)
            finally:
                if old_read_fd >= 0:
                    os.close(old_read_fd)

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

    def test_attach_preflight_reports_each_existing_predicate(self) -> None:
        attach = (
            ROOT / "work/commands/FLR-0350-attach-pre-submit.sh"
        ).read_text()
        fields = (
            "pid_present",
            "recorded_start_present",
            "start_match",
            "comm_match",
            "uid_match",
            "running_state",
            "tracer_clear",
            "syscall_read",
            "syscall_fd0",
            "gate_fifo",
            "gate_owner_mode",
            "root_identity_loaded",
            "root_identity_process",
            "root_identity_fifo",
            "fd0_same_gate",
            "fd3_same_gate",
            "fd3_path_match",
            "script_readable",
            "armed_clear",
            "auth_clear",
            "go_clear",
            "gdb_pid_clear",
            "gdb_start_clear",
            "log_clear",
        )
        self.assertTrue(
            "FLR0350_GDB_ATTACH_PREFLIGHT" in attach,
            "guest attach command lacks the bounded preflight marker",
        )
        self.assertTrue(
            'values="$values $name=PASS"' in attach and
            'values="$values $name=FAIL"' in attach,
            "preflight marker does not serialize individual PASS/FAIL values",
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertTrue(
                    f"check {field} " in attach,
                    f"preflight marker omits predicate {field}",
                )
        for field in (
            "fd0_same_gate",
            "fd3_same_gate",
            "syscall_nr",
            "syscall_fd",
        ):
            with self.subTest(diagnostic=field):
                self.assertTrue(
                    f"{field}=" in attach,
                    f"preflight marker omits diagnostic {field}",
                )

    def test_attach_failure_stays_before_gdb_and_release_go(self) -> None:
        attach = (
            ROOT / "work/commands/FLR-0350-attach-pre-submit.sh"
        ).read_text()
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        failure = attach.index('if [ -n "$failed" ]; then')
        failure_marker = attach.index(
            'echo "FLR0350_GDB_ATTACH=FAIL precondition failed=$failed"', failure
        )
        gdb = attach.index("exec /usr/bin/gdb", failure)
        self.assertLess(failure, failure_marker)
        self.assertLess(failure_marker, gdb)

        attach_call = runner.index(
            "guest_run attach-gdb FLR-0350-attach-pre-submit.cmd"
        )
        attach_pass = runner.index(
            "grep -F 'FLR0350_GDB_ATTACH=PASS'", attach_call
        )
        release_go = runner.index(
            "guest_run release-go FLR-0350-release-go.cmd", attach_call
        )
        self.assertLess(attach_call, attach_pass)
        self.assertLess(attach_pass, release_go)

    def test_attach_preflight_evaluates_failures_and_keeps_fd0_diagnostic_only(
        self,
    ) -> None:
        attach = (ROOT / "work/commands/FLR-0350-attach-pre-submit.sh").read_text()
        common = (ROOT / "work/commands/FLR-0350-gate-common.sh").read_text()
        preflight = "pidfile=" + attach.split("pidfile=", 1)[1].split(
            '\nif [ -n "$failed" ]; then', 1
        )[0]

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = root / "run"
            proc_root = root / "proc"
            root_dir = root / "root-owned"
            fake_bin = root / "bin"
            run_dir.mkdir()
            root_dir.mkdir(mode=0o700)
            fake_bin.mkdir()
            pid = "4242"
            proc = proc_root / pid
            (proc / "fd").mkdir(parents=True)

            gate = run_dir / "flr0350-go.fifo"
            decoy = run_dir / "other.fifo"
            os.mkfifo(gate)
            os.mkfifo(decoy)
            os.chmod(gate, 0o600)
            (root_dir / "run.id").write_text("flr0362-0001\n")
            gate_stat = os.stat(gate)
            (root_dir / "fifo.identity").write_text(
                f"1 flr0362-0001 {pid} 424242 1001 {gate_stat.st_dev} {gate_stat.st_ino}\n"
            )
            for record in root_dir.iterdir():
                record.chmod(0o600)
            (run_dir / "flr0350-flutter.pid").write_text(f"{pid}\n")
            (run_dir / "flr0350-wrapper.start").write_text("424242\n")
            (run_dir / "flr0350-sync-producer.gdb").write_text("# test script\n")
            (proc / "stat").write_text(
                f"{pid} (wrapper) "
                + " ".join(["S", *(["0"] * 18), "424242"])
                + "\n"
            )
            (proc / "comm").write_text("sh\n")
            (proc / "status").write_text(
                "Uid:\t1001\t1001\t1001\t1001\nTracerPid:\t0\n"
            )
            syscall_file = proc / "syscall"
            syscall_file.write_text("0 0x0 0 0\n")
            (proc / "fd" / "0").symlink_to(gate)
            (proc / "fd" / "3").symlink_to(gate)

            fake_id = fake_bin / "id"
            fake_id.write_text("#!/bin/sh\nprintf '%s\\n' 1001\n")
            fake_id.chmod(0o755)
            fake_stat = fake_bin / "stat"
            fake_stat.write_text(
                "#!/bin/sh\n"
                "fmt=; target=; want_fmt=0\n"
                "for arg do\n"
                "  if [ \"$want_fmt\" = 1 ]; then fmt=$arg; want_fmt=0; continue; fi\n"
                "  case $arg in -L) ;; -c) want_fmt=1 ;; *) target=$arg ;; esac\n"
                "done\n"
                "exec python3 -c 'import os,sys; s=os.stat(sys.argv[2]); f=sys.argv[1]; mode=oct(s.st_mode & 0o777)[2:]; "
                "print((\"0:%s\" % mode) if f == \"%u:%a\" else "
                "(\"%s:%s:1001:600\" % (s.st_dev,s.st_ino)) if f == \"%d:%i:%u:%a\" else "
                "(\"%s:%s\" % (s.st_dev,s.st_ino)))' \"$fmt\" \"$target\"\n"
            )
            fake_stat.chmod(0o755)

            command = (
                f"FLR0350_USER_DIR={run_dir} FLR0350_ROOT_DIR={root_dir} "
                f"FLR0350_PROC_ROOT={proc_root}; {common}\n{preflight} "
                "\nif [ -n \"$failed\" ]; then echo TEST_GDB_FAIL; "
                "else echo TEST_GDB_BRANCH; fi"
            )
            env = os.environ.copy()
            env.update(
                PATH=f"{fake_bin}:{env['PATH']}",
                PROC_ROOT=str(proc_root),
            )

            def run_preflight() -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["sh", "-c", command],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )

            passed = run_preflight()
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertIn("syscall_read=PASS", passed.stdout)
            self.assertIn("syscall_fd0=PASS", passed.stdout)
            self.assertIn("fd0_same_gate=PASS", passed.stdout)
            self.assertIn("fd3_same_gate=PASS", passed.stdout)
            self.assertIn("syscall_nr=0 syscall_fd=0x0", passed.stdout)
            self.assertIn("TEST_GDB_BRANCH", passed.stdout)
            for field in (
                "pid_present",
                "recorded_start_present",
                "start_match",
                "comm_match",
                "uid_match",
                "syscall_fd0",
                "root_identity_loaded",
                "root_identity_process",
                "root_identity_fifo",
                "fd3_path_match",
                "script_readable",
                "armed_clear",
                "auth_clear",
                "go_clear",
                "gdb_pid_clear",
                "gdb_start_clear",
                "log_clear",
            ):
                with self.subTest(predicate=field):
                    self.assertIn(f"{field}=PASS", passed.stdout)

            syscall_file.write_text("0 0x3 0 0\n")
            failed = run_preflight()
            self.assertEqual(failed.returncode, 0, failed.stderr)
            self.assertIn("syscall_read=PASS", failed.stdout)
            self.assertIn("syscall_fd0=FAIL", failed.stdout)
            self.assertIn(
                "TEST_GDB_FAIL", failed.stdout
            )
            self.assertNotIn("TEST_GDB_BRANCH", failed.stdout)

            syscall_file.write_text("0 0x0 0 0\n")
            (proc / "fd" / "0").unlink()
            (proc / "fd" / "0").symlink_to(decoy)
            diagnostic_only = run_preflight()
            self.assertEqual(diagnostic_only.returncode, 0, diagnostic_only.stderr)
            self.assertIn("fd0_same_gate=FAIL", diagnostic_only.stdout)
            self.assertIn("fd3_same_gate=PASS", diagnostic_only.stdout)
            self.assertIn("TEST_GDB_FAIL", diagnostic_only.stdout)
            self.assertNotIn("TEST_GDB_BRANCH", diagnostic_only.stdout)

    def test_postwrite_record_failure_terminates_inferior_before_gdb_error(self) -> None:
        release = (ROOT / "work/commands/FLR-0350-release-go.sh").read_text()
        gdb = (ROOT / "work/commands/FLR-0350-sync-producer.gdb").read_text()
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        write = release.index("printf '%s\\n' FLR0350_GO >&3")
        record = release.index('flr0350_write_once "$FLR0350_ROOT_DIR/go.record"')
        self.assertLess(write, record)
        self.assertIn("FLR0350_GO_RECORD=FAIL reason=publication-after-write", release)

        wait = gdb.index("def wait_for_go_record():")
        wait_end = gdb.index("def current_target_identity():", wait)
        wait_body = gdb[wait:wait_end]
        self.assertIn("terminate_stopped_inferior", wait_body)
        self.assertIn("gdb.execute(\"kill\"", gdb)
        self.assertIn("os.kill(TARGET_PID, 9)", gdb)
        self.assertIn("FLR0350_TARGET_ABORT=PASS", gdb)
        self.assertLess(
            wait_body.index("terminate_stopped_inferior"),
            wait_body.index("raise gdb.GdbError"),
        )
        self.assertIn("FLR0350_GO_RECORD=PASS", runner)
        self.assertIn("FLR0350_EXEC=PASS", runner)

    def test_cleanup_kills_unreleased_target_before_interrupting_gdb(self) -> None:
        interrupt = (ROOT / "work/commands/FLR-0350-interrupt-gdb.sh").read_text()
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        target_abort = interrupt.index('kill -KILL "$pid"')
        gdb_interrupt = interrupt.index('kill -INT "$gpid"')
        self.assertLess(target_abort, gdb_interrupt)
        self.assertIn("FLR0350_UNRECORDED_TARGET_ABORT=PASS", interrupt)
        self.assertIn("flr0350_go_record_matches", interrupt)
        self.assertIn("FLR0350_UNRECORDED_TARGET_ABORT=FAIL", runner)

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

    def test_runner_initializes_identity_only_after_preflight_before_launch(self) -> None:
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        preflight = runner.rindex("guest_run preflight FLR-0350-preflight.cmd")
        helper_preflight = runner.rindex(
            "guest_run helper-preflight FLR-0350-preflight-helper-collision.cmd"
        )
        self.assertTrue(
            "guest_run init-run-identity" in runner,
            "runner has no run-identity initialization stage",
        )
        initialize = runner.rindex("guest_run init-run-identity")
        launch = runner.rindex(
            "guest_run launch FLR-0350-launch-paused-production.cmd"
        )
        self.assertLess(preflight, helper_preflight)
        self.assertLess(helper_preflight, initialize)
        self.assertLess(initialize, launch)
        self.assertIn("--render-identity-init", runner)

    def test_helper_transfer_rejects_stale_payloads_and_never_overwrites(self) -> None:
        preflight = (
            ROOT / "work/commands/FLR-0350-preflight-helper-collision.cmd"
        ).read_bytes()
        self.assertEqual(len(preflight.splitlines()), 1)
        self.assertLessEqual(len(preflight.rstrip(b"\n")), 4096)
        text = preflight.decode()
        self.assertIn("FLR-0350-*.sh", text)
        self.assertIn("FLR-0350-*.sh.gz", text)
        self.assertIn("FLR-0350-*.sh.tmp", text)
        self.assertIn("FLR0350_HELPER_COLLISION=$f", text)
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        self.assertIn("test ! -e '$guest_path' && test ! -L '$guest_path'", runner)
        self.assertIn("test ! -e '$guest_path.tmp' && test ! -L '$guest_path.tmp'", runner)
        self.assertIn("test ! -e /run/user/1001/flr0350-sync-producer.gdb.tmp", runner)

    def test_long_guest_decisions_use_committed_helpers_behind_small_adapters(self) -> None:
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        expected_helpers = (
            "FLR-0350-gate-common.sh",
            "FLR-0350-attach-pre-submit.sh",
            "FLR-0350-release-go.sh",
            "FLR-0350-stop-recorded-app.sh",
            "FLR-0350-interrupt-gdb.sh",
        )
        for name in expected_helpers:
            with self.subTest(helper=name):
                self.assertTrue(name in runner, f"runner does not stage {name}")
                adapter = (ROOT / "work/commands" / name).with_suffix(".cmd")
                if name != "FLR-0350-gate-common.sh":
                    data = adapter.read_bytes()
                    self.assertEqual(len(data.splitlines()), 1)
                    self.assertLessEqual(len(data.rstrip(b"\n")), 4096)
        self.assertTrue(
            'git -C "$repo_root" show "HEAD:work/commands/$file"' in runner,
            "runner does not compare helper source to committed HEAD",
        )

    def test_identity_init_command_is_run_bound_collision_safe_and_bounded(self) -> None:
        output = io.StringIO()
        errors = io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            result = main(["--render-identity-init", "flr0362-0001"])
        self.assertEqual(result, 0)
        command = output.getvalue().strip()
        self.assertEqual(len(command.splitlines()), 1)
        self.assertLessEqual(len(command.encode()), 4096)
        self.assertIn("/run/flr0350", command)
        self.assertIn('[ -e "$d" ] || [ -L "$d" ]', command)
        self.assertIn("set -C", command)
        self.assertIn("flr0362-0001", command)
        rejected = io.StringIO()
        rejected_err = io.StringIO()
        with redirect_stdout(rejected), redirect_stderr(rejected_err):
            result = main(["--render-identity-init", "flr0350-0001"])
        self.assertNotEqual(result, 0)

    def test_identity_init_command_creates_once_and_rejects_dangling_symlink(self) -> None:
        generated = io.StringIO()
        with redirect_stdout(generated):
            self.assertEqual(main(["--render-identity-init", "flr0362-0001"]), 0)
        command = generated.getvalue().strip()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = root / "flr0350"
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_stat = fake_bin / "stat"
            fake_stat.write_text(
                "#!/bin/sh\n"
                "python3 -c 'import os,sys; s=os.stat(sys.argv[1]); "
                "print(\"0:%o\" % (s.st_mode & 0o777))' \"$3\"\n",
                encoding="utf-8",
            )
            fake_stat.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            local_command = command.replace("/run/flr0350", str(run_dir))
            created = subprocess.run(
                ["sh", "-c", local_command], env=env,
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(created.returncode, 0)
            self.assertIn("FLR0350_RUN_ID_INIT=PASS", created.stdout)
            self.assertEqual((run_dir / "run.id").read_text(), "flr0362-0001\n")

            collision = subprocess.run(
                ["sh", "-c", local_command], env=env,
                capture_output=True, text=True, check=False,
            )
            self.assertIn("FLR0350_RUN_ID_INIT=FAIL reason=collision", collision.stdout)
            self.assertEqual((run_dir / "run.id").read_text(), "flr0362-0001\n")

            (run_dir / "run.id").unlink()
            run_dir.rmdir()
            run_dir.symlink_to(root / "missing-target")
            dangling = subprocess.run(
                ["sh", "-c", local_command], env=env,
                capture_output=True, text=True, check=False,
            )
            self.assertIn("FLR0350_RUN_ID_INIT=FAIL reason=collision", dangling.stdout)

    def test_all_fixed_guest_commands_are_staged_before_qemu_start(self) -> None:
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        fixed_calls = set(re.findall(
            r"(?m)^\s*guest_run\s+\S+\s+(FLR-0350-[\w.-]+\.cmd)\s*$",
            runner,
        ))
        inventory = re.search(
            r"(?ms)^runtime_command_files=\(\n(.*?)^\)", runner
        )
        self.assertIsNotNone(inventory, "runner has no static command inventory")
        staged = set(re.findall(
            r"(?m)^\s*(FLR-0350-[\w.-]+\.cmd)\s*$", inventory.group(1)
        ))
        self.assertTrue(fixed_calls, "no fixed guest_run commands were found")
        self.assertEqual(fixed_calls - staged, set())
        self.assertIn("FLR-0350-observe-fifo-read-gate.cmd", staged)
        stage_loop = runner.rfind(
            'for file in "${runtime_command_files[@]}"; do',
            0,
            runner.rindex('FLR0350_RUN_ID="$run_id" bash "$start_script" start'),
        )
        self.assertNotEqual(stage_loop, -1)
        copy_parent = runner.index(
            'cp -- "$repo_root/work/commands/$file" "$parent/$file"'
        )
        start = runner.rindex(
            'FLR0350_RUN_ID="$run_id" bash "$start_script" start'
        )
        self.assertLess(copy_parent, start)

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
        stop = (ROOT / "work/commands/FLR-0350-stop-recorded-app.sh").read_text()
        self.assertNotIn("pkill", stop)
        self.assertNotIn("killall", stop)
        guarded_start = '[ "$start" = "$expected" ]'
        guarded_uid = '[ "$uid" = "$(id -u agl-driver)" ]'
        identity_gate = 'flr0350_identity_matches_process "$pid" "$expected" "$uid"'
        self.assertIn(guarded_start, stop)
        self.assertIn(guarded_uid, stop)
        self.assertIn(identity_gate, stop)
        self.assertLess(stop.index(guarded_start), stop.index('kill -TERM "$pid"'))
        self.assertLess(stop.index(guarded_uid), stop.index('kill -TERM "$pid"'))
        self.assertLess(stop.index(identity_gate), stop.index('kill -TERM "$pid"'))
        self.assertIn('if [ "$state" = Z ] || [ "$state" = X ] || [ "$state" = x ]; then', stop)
        self.assertIn("candidate_state=$(flr0350_proc_state \"$candidate\")", stop)


class StarterRunIdPropagationTests(unittest.TestCase):
    def test_runner_passes_the_same_run_id_to_preflight_and_start(self) -> None:
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        preflight = 'FLR0350_RUN_ID="$run_id" bash "$start_script" preflight'
        start = 'FLR0350_RUN_ID="$run_id" bash "$start_script" start'
        evidence_create = 'mkdir -- "$parent"'
        self.assertTrue(preflight in runner, "runner omits the ID-bearing preflight")
        self.assertTrue(start in runner, "runner omits the ID-bearing start")
        self.assertLess(runner.rindex(preflight), runner.rindex(evidence_create))
        self.assertGreater(runner.rindex(start), runner.rindex(evidence_create))

    def test_starter_requires_shared_fresh_id_validation_without_old_default(self) -> None:
        starter = (ROOT / "work/commands/FLR-0350-qemu-start.sh").read_text()
        self.assertFalse(
            "${FLR0350_RUN_ID:-flr0350-0001}" in starter,
            "starter retains the consumed-ID fallback",
        )
        self.assertTrue("${FLR0350_RUN_ID:?" in starter, "starter does not require an ID")
        self.assertTrue(
            "scripts/flr0350_launch_gate.py" in starter,
            "starter does not use the shared run-ID validator",
        )
        self.assertTrue('--check-run-id "$run_id"' in starter, "starter does not validate the ID")
        self.assertTrue("preflight)" in starter, "starter has no preflight mode")
        self.assertTrue("start)" in starter, "starter has no start mode")

    def test_starter_preflight_rejects_missing_or_consumed_ids_before_target_access(self) -> None:
        starter = ROOT / "work/commands/FLR-0350-qemu-start.sh"
        env = os.environ.copy()
        env.pop("FLR0350_RUN_ID", None)
        missing = subprocess.run(
            ["bash", str(starter), "preflight"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("FLR0350_RUN_ID-is-required", missing.stderr)

        env["FLR0350_RUN_ID"] = "flr0350-0001"
        consumed = subprocess.run(
            ["bash", str(starter), "preflight"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(consumed.returncode, 0)
        self.assertIn("invalid-or-consumed-run-id", consumed.stderr)

    def test_starter_preflight_is_non_mutating_and_start_repeats_runtime_guards(self) -> None:
        starter = (ROOT / "work/commands/FLR-0350-qemu-start.sh").read_text()
        preflight_exit = starter.rindex('if [ "$mode" = preflight ]; then')
        start_mutation = starter.index('mkdir -- "$run_dir"')
        qemu_start = starter.index('"$harness" start')
        self.assertLess(preflight_exit, start_mutation)
        self.assertLess(start_mutation, qemu_start)
        self.assertIn("residual-runtime-process", starter)
        self.assertIn("check_port_free \"$port\"", starter)
        self.assertIn("kernel-sha256", starter)
        self.assertIn("rootfs-sha256", starter)

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
                result = main(
                    ["--validate", "flr0362-0001", str(launch_path), str(gate_path)]
                )
        self.assertEqual(result, 0)
        self.assertIn("FLR0350_FIFO_READ_GATE=PASS", output.getvalue())

    def test_run_id_cli_rejects_consumed_identifier(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(["--check-run-id", "flr0350-0001"])
        self.assertEqual(result, 2)
        self.assertIn("FLR0350_RUN_ID=REJECTED", output.getvalue())


class RuntimeHelperProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        self.starter = (ROOT / "work/commands/FLR-0350-qemu-start.sh").read_text()

    def test_runner_stages_current_helper_before_start_and_uses_that_copy(self) -> None:
        source = 'harness_source=$repo_root/scripts/qemu-runtime-harness.sh'
        staged = 'cp -- "$harness_source" "$parent/qemu-runtime-harness.sh"'
        selected = 'harness=$parent/qemu-runtime-harness.sh'
        start = 'FLR0350_RUN_ID="$run_id" bash "$start_script" start'
        runtime = self.runner.split("run_id=$1\n", 1)[1]

        self.assertTrue(source in self.runner, "runner does not source the current repository helper")
        self.assertTrue(staged in runtime, "runner does not stage the helper into the run parent")
        self.assertTrue(selected in runtime, "runner does not select the staged run helper")
        self.assertLess(runtime.index(staged), runtime.index(selected))
        self.assertLess(runtime.index(selected), runtime.rindex(start))
        self.assertTrue(
            'git -C "$repo_root" show "HEAD:scripts/qemu-runtime-harness.sh"' in runtime,
            "runner does not compare source bytes with committed HEAD",
        )
        self.assertTrue('[ -x "$harness_source" ]' in runtime,
                        "runner does not reject a non-executable source helper")
        self.assertTrue('sha256sum "$harness"' in self.runner, "runner does not calculate staged helper SHA")
        self.assertTrue("FLR0350_RUNTIME_HELPER=PASS" in self.runner, "runner omits helper provenance marker")
        self.assertFalse("harness=$prior_run_dir/qemu-runtime-harness.sh" in self.runner.splitlines(),
                         "runner still selects the prior-run helper")

    def test_starter_validates_and_uses_the_same_run_scoped_helper(self) -> None:
        source = 'harness_source=$repo_root/scripts/qemu-runtime-harness.sh'
        staged = 'harness=$new_run_parent/qemu-runtime-harness.sh'
        self.assertTrue(source in self.starter, "starter does not source the current repository helper")
        self.assertTrue(staged in self.starter, "starter does not select the run-scoped helper")
        self.assertTrue('cmp -s "$harness_source" "$harness"' in self.starter,
                        "starter does not compare staged bytes with source")
        self.assertTrue(
            'git -C "$repo_root" show "HEAD:scripts/qemu-runtime-harness.sh"' in self.starter,
            "starter does not compare source bytes with committed HEAD",
        )
        self.assertTrue('[ -x "$harness" ]' in self.starter,
                        "starter does not reject a non-executable run helper")
        self.assertLess(
            self.starter.index('cmp -s "$harness_source" "$harness"'),
            self.starter.index('"$harness" preflight'),
            "starter invokes the helper before validating staged bytes",
        )
        self.assertTrue("runtime-helper-source-mismatch" in self.starter,
                        "starter has no fail-closed source mismatch reason")
        self.assertTrue('"$harness" preflight' in self.starter and '"$harness" start' in self.starter,
                        "starter does not invoke the validated helper for both operations")
        self.assertFalse("harness=$prior_run_dir/qemu-runtime-harness.sh" in self.starter.splitlines(),
                         "starter still selects the prior-run helper")
        self.assertFalse(
            "339472336f14387fd1b72c3d702e510de19ff710c5c203441733a7a59d79aa6d" in self.starter,
            "starter still pins the old runtime helper SHA",
        )

    def test_pixel_capture_helper_remains_pinned_to_historical_evidence(self) -> None:
        capture_identity = "992c0428cc85dc61ebdea1e49dc544eed528a961f06faf9dd7fe7de30795ec24"
        self.assertIn("capture=$prior_run_dir/qemu-pixel-capture.py", self.runner)
        self.assertIn("capture=$prior_run_dir/qemu-pixel-capture.py", self.starter)
        self.assertIn(capture_identity, self.starter)


if __name__ == "__main__":
    unittest.main()
