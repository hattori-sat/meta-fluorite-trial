from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_COMMAND = REPO_ROOT / "work/commands/FLR-0344-wait-armed.cmd"
FIXED_COMMAND = REPO_ROOT / "work/commands/FLR-0346-wait-armed.cmd"
FIXED_HELPER = REPO_ROOT / "work/commands/FLR-0346-arm-poll.sh"
ARMED_MARKER = "FLR0344_WATCHPOINTS_ARMED=1"


class ArmPollEmptyLogTest(unittest.TestCase):
    def test_empty_log_is_waited_on_and_absent_state_is_specific(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flr0346-arm-poll-") as temp_name:
            temp_root = Path(temp_name)
            pid_file = temp_root / "gdb.pid"
            gdb_log = temp_root / "gdb.log"
            proc_root = temp_root / "proc"
            fake_bin = temp_root / "bin"

            pid_file.write_text("99999999\n", encoding="utf-8")
            gdb_log.touch()
            legacy = LEGACY_COMMAND.read_text(encoding="utf-8")
            legacy = legacy.replace(
                "gdb_pidfile=/run/user/1001/flr0344-gdb-watch.pid",
                f"gdb_pidfile={shlex.quote(str(pid_file))}",
                1,
            ).replace(
                "gdb_log=/run/user/1001/flr0344-gdb-watch.log",
                f"gdb_log={shlex.quote(str(gdb_log))}",
                1,
            )
            legacy_result = subprocess.run(
                ["sh", "-c", legacy], capture_output=True, text=True, timeout=2
            )
            self.assertIn("FLR0344_ARM_WAIT=FAIL missing-gdb-state", legacy_result.stdout)

            def run_fixed() -> subprocess.CompletedProcess[str]:
                command = FIXED_COMMAND.read_text(encoding="utf-8")
                replacements = (
                    ("/run/user/1001/flr0346-arm-poll.sh", str(FIXED_HELPER)),
                    ("/run/user/1001/flr0344-gdb-watch.pid", str(pid_file)),
                    ("/run/user/1001/flr0344-gdb-watch.log", str(gdb_log)),
                    ("/proc", str(proc_root)),
                )
                for original, replacement in replacements:
                    self.assertIn(original, command)
                    command = command.replace(
                        original, shlex.quote(replacement), 1
                    )
                self.assertIn(" 88 0.25", command)
                command = command.replace(" 88 0.25", " 40 0.05", 1)
                return subprocess.run(
                    ["sh", "-c", command],
                    capture_output=True,
                    text=True,
                    env={
                        **os.environ,
                        "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
                    },
                    timeout=4,
                )

            pid_file.unlink()
            missing_pid = run_fixed()
            missing_pid_output = missing_pid.stdout + missing_pid.stderr
            self.assertEqual(
                2,
                missing_pid.returncode,
                f"unexpected missing-PID result: {missing_pid_output}",
            )
            self.assertIn(
                "FLR0346_ARM_WAIT=FAIL missing-pidfile", missing_pid_output
            )

            fake_bin.mkdir()
            fake_ps = fake_bin / "ps"
            fake_ps.write_text("#!/bin/sh\nprintf 'S\\n'\n", encoding="utf-8")
            fake_ps.chmod(0o755)
            test_pid = 4242
            pid_file.write_text(f"{test_pid}\n", encoding="utf-8")
            proc_comm = proc_root / str(test_pid) / "comm"
            proc_comm.parent.mkdir(parents=True)
            proc_comm.write_text("gdb\n", encoding="utf-8")

            gdb_log.unlink()
            missing_log = run_fixed()
            missing_log_output = missing_log.stdout + missing_log.stderr
            self.assertEqual(
                2, missing_log.returncode, missing_log_output
            )
            self.assertIn("FLR0346_ARM_WAIT=FAIL missing-logfile", missing_log_output)

            gdb_log.touch()
            writer = threading.Timer(
                0.15,
                lambda: gdb_log.write_text(ARMED_MARKER + "\n", encoding="utf-8"),
            )
            writer.start()
            armed = run_fixed()
            writer.join(timeout=1)
            self.assertEqual(0, armed.returncode, armed.stdout + armed.stderr)
            self.assertIn("FLR0346_ARM_WAIT=PASS armed=1", armed.stdout)


if __name__ == "__main__":
    unittest.main()
