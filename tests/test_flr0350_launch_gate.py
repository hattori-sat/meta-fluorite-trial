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

    def test_attach_preflight_reports_each_existing_predicate(self) -> None:
        attach = (
            ROOT / "work/commands/FLR-0350-attach-pre-submit.cmd"
        ).read_text()
        fields = (
            "pid_present",
            "expected_start_present",
            "start_match",
            "comm_match",
            "uid_match",
            "fd3_path_match",
            "syscall_read",
            "syscall_fd3",
            "script_readable",
            "armed_clear",
            "gdb_pid_clear",
            "gdb_start_clear",
            "log_clear",
        )
        self.assertTrue(
            "FLR0350_GDB_ATTACH_PREFLIGHT" in attach,
            "guest attach command lacks the bounded preflight marker",
        )
        self.assertTrue(
            'v="$v $n=PASS"' in attach and 'v="$v $n=FAIL"' in attach,
            "preflight marker does not serialize individual PASS/FAIL values",
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertTrue(
                    f"c {field} " in attach,
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
            ROOT / "work/commands/FLR-0350-attach-pre-submit.cmd"
        ).read_text()
        runner = (ROOT / "work/commands/FLR-0350-run-sync-producer.sh").read_text()
        failure = attach.index('if [ -n "$b" ]; then')
        failure_marker = attach.index(
            'echo "FLR0350_GDB_ATTACH=FAIL precondition failed=$b"', failure
        )
        alternate = attach.index("; else /bin/sh -c", failure)
        gdb = attach.index("exec /usr/bin/gdb", alternate)
        self.assertLess(failure, failure_marker)
        self.assertLess(failure_marker, alternate)
        self.assertLess(alternate, gdb)

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
        attach = (
            ROOT / "work/commands/FLR-0350-attach-pre-submit.cmd"
        ).read_text()
        preflight = attach.split(" else /bin/sh -c", 1)[0]

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = root / "run"
            proc_root = root / "proc"
            fake_bin = root / "bin"
            run_dir.mkdir()
            fake_bin.mkdir()
            pid = "4242"
            proc = proc_root / pid
            (proc / "fd").mkdir(parents=True)

            gate = run_dir / "flr0350-go.fifo"
            decoy = run_dir / "other.fifo"
            os.mkfifo(gate)
            os.mkfifo(decoy)
            (run_dir / "flr0350-flutter.pid").write_text(f"{pid}\n")
            (run_dir / "flr0350-wrapper.start").write_text("424242\n")
            (run_dir / "flr0350-sync-producer.gdb").write_text("# test script\n")
            (proc / "stat").write_text(
                f"{pid} (wrapper) "
                + " ".join(["S", *(["0"] * 18), "424242"])
                + "\n"
            )
            (proc / "comm").write_text("sh\n")
            (proc / "status").write_text("Uid:\t1001\t1001\t1001\t1001\n")
            syscall_file = proc / "syscall"
            syscall_file.write_text("0 0x3 0 0\n")
            (proc / "fd" / "0").symlink_to(gate)
            (proc / "fd" / "3").symlink_to(gate)

            fake_id = fake_bin / "id"
            fake_id.write_text("#!/bin/sh\nprintf '%s\\n' 1001\n")
            fake_id.chmod(0o755)
            fake_stat = fake_bin / "stat"
            fake_stat.write_text(
                "#!/bin/sh\n"
                "for p do last=$p; done\n"
                "exec python3 -c 'import os,sys; s=os.stat(sys.argv[1]); "
                "print(\"%s:%s\" % (s.st_dev, s.st_ino))' \"$last\"\n"
            )
            fake_stat.chmod(0o755)

            command = preflight.replace("/run/user/1001", str(run_dir)).replace(
                "/proc/$pid", "$PROC_ROOT/$pid"
            ) + " else echo TEST_GDB_BRANCH; fi"
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
            self.assertIn("fd0_same_gate=PASS", passed.stdout)
            self.assertIn("fd3_same_gate=PASS", passed.stdout)
            self.assertIn("syscall_nr=0 syscall_fd=0x3", passed.stdout)
            self.assertIn("TEST_GDB_BRANCH", passed.stdout)
            for field in (
                "pid_present",
                "expected_start_present",
                "start_match",
                "comm_match",
                "uid_match",
                "fd3_path_match",
                "syscall_read",
                "syscall_fd3",
                "script_readable",
                "armed_clear",
                "gdb_pid_clear",
                "gdb_start_clear",
                "log_clear",
            ):
                with self.subTest(predicate=field):
                    self.assertIn(f"{field}=PASS", passed.stdout)

            syscall_file.write_text("0 0x0 0 0\n")
            failed = run_preflight()
            self.assertEqual(failed.returncode, 0, failed.stderr)
            self.assertIn("syscall_read=PASS", failed.stdout)
            self.assertIn("syscall_fd3=FAIL", failed.stdout)
            self.assertIn(
                "FLR0350_GDB_ATTACH=FAIL precondition failed=syscall_fd3",
                failed.stdout,
            )
            self.assertNotIn("TEST_GDB_BRANCH", failed.stdout)

            syscall_file.write_text("0 0x3 0 0\n")
            (proc / "fd" / "0").unlink()
            (proc / "fd" / "0").symlink_to(decoy)
            diagnostic_only = run_preflight()
            self.assertEqual(diagnostic_only.returncode, 0, diagnostic_only.stderr)
            self.assertIn("fd0_same_gate=FAIL", diagnostic_only.stdout)
            self.assertIn("fd3_same_gate=PASS", diagnostic_only.stdout)
            self.assertIn("TEST_GDB_BRANCH", diagnostic_only.stdout)
            self.assertNotIn("FLR0350_GDB_ATTACH=FAIL", diagnostic_only.stdout)

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
        stop = (ROOT / "work/commands/FLR-0350-stop-recorded-app.cmd").read_text()
        self.assertNotIn("pkill", stop)
        self.assertNotIn("killall", stop)
        guarded_signal = (
            '[ "$start" = "$expected" ] && '
            '[ "$uid" = "$(id -u agl-driver)" ]'
        )
        self.assertIn(guarded_signal, stop)
        self.assertLess(stop.index(guarded_signal), stop.index('kill -TERM "$pid"'))


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
                result = main(["--validate", str(launch_path), str(gate_path)])
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
