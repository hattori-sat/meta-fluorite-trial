from __future__ import annotations

import contextlib
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
GDB_SCRIPT = REPO_ROOT / "work/commands/FLR-0348-sync-watch.gdb"
RUNNER = REPO_ROOT / "work/commands/FLR-0344-run-sync-watch.sh"
QEMU_START = REPO_ROOT / "work/commands/FLR-0344-qemu-start.sh"
PREFLIGHT_COMMAND = REPO_ROOT / "work/commands/FLR-0344-preflight.cmd"
GDB_LAUNCH_COMMAND = REPO_ROOT / "work/commands/FLR-0344-launch-gdb.cmd"
SIGNAL_ARMED = "FLR0348_SIGNAL_WATCH_ARMED=1"
FENCE_ARMED = "FLR0348_FENCE_WATCH_ARMED=1"
ALL_ARMED = "FLR0348_WATCHPOINTS_ARMED=1"


class _GdbError(Exception):
    pass


class _Value:
    def __init__(self, value: int | str) -> None:
        self.value = value

    def __int__(self) -> int:
        return int(self.value)

    def __str__(self) -> str:
        return str(self.value)


class _Frame:
    def name(self) -> str:
        return "lvp_pipe_sync_wait_locked"

    def older(self) -> None:
        return None

    def select(self) -> None:
        return None


class _Thread:
    name = "FEngine::loop"
    ptid = (1, 123, 0)

    def switch(self) -> None:
        return None


class _Inferior:
    def threads(self) -> list[_Thread]:
        return [_Thread()]


class _Gdb(types.ModuleType):
    error = _GdbError

    def __init__(self, fail_watch: str | None = None) -> None:
        super().__init__("gdb")
        self.fail_watch = fail_watch
        self.commands: list[str] = []
        self.convenience: dict[str, _Value] = {}
        self.watchpoint_id = 0

    def selected_inferior(self) -> _Inferior:
        return _Inferior()

    def selected_frame(self) -> _Frame:
        return _Frame()

    def Value(self, value: int | str) -> _Value:
        return _Value(value)

    def parse_and_eval(self, expression: str) -> _Value:
        values = {
            "sync": 0x1000,
            "&sync->signaled": 0x1010,
            "&sync->fence": 0x1018,
            "sync->signaled": 0,
            "sync->fence": 0,
        }
        if expression.startswith("*(void **)0x"):
            return _Value(0)
        return _Value(values[expression])

    def execute(self, command: str, to_string: bool = False) -> str:
        self.commands.append(command)
        if (
            command.startswith("watch ")
            and self.fail_watch is not None
            and self.fail_watch in command
        ):
            raise _GdbError("synthetic watchpoint rejection")
        if command.startswith("watch "):
            self.watchpoint_id += 1
            return f"Hardware watchpoint {self.watchpoint_id}: {command}\n"
        return "#0 lvp_pipe_sync_wait_locked\n" if command == "bt 8" else ""

    def set_convenience_variable(self, name: str, value: _Value) -> None:
        self.convenience[name] = value


def _execute_setup(script: str, gdb: _Gdb) -> str:
    lines = script.splitlines()
    start = lines.index("python") + 1
    end = lines.index("end", start)
    output = io.StringIO()
    with patch.dict(sys.modules, {"gdb": gdb}), contextlib.redirect_stdout(output):
        exec(compile("\n".join(lines[start:end]), "gdb-setup", "exec"), {})
    return output.getvalue()


class SyncWatchContractTest(unittest.TestCase):
    def test_both_wait_release_predicates_arm_before_the_combined_marker(self) -> None:
        script = GDB_SCRIPT.read_text(encoding="utf-8")
        gdb = _Gdb()

        output = _execute_setup(script, gdb)
        watch_commands = [command for command in gdb.commands if command.startswith("watch ")]

        self.assertIn("watch -l sync->signaled", watch_commands)
        self.assertIn("watch -l *(void **)0x1018", watch_commands)
        self.assertNotIn("pipe_fence_handle", script)
        self.assertIn(SIGNAL_ARMED, output)
        self.assertIn(FENCE_ARMED, output)
        self.assertIn(ALL_ARMED, output)
        self.assertLess(output.index(SIGNAL_ARMED), output.index(ALL_ARMED))
        self.assertLess(output.index(FENCE_ARMED), output.index(ALL_ARMED))
        self.assertLess(output.index(ALL_ARMED), output.index("FLR0344_WATCHPOINTS_ARMED=1"))
        self.assertIn("Hardware watchpoint 1:", output)
        self.assertIn("Hardware watchpoint 2:", output)
        self.assertEqual(1, int(gdb.convenience["flr0348_ready"]))

    def test_a_rejected_fence_watch_preserves_signal_result_but_never_arms_all(self) -> None:
        script = GDB_SCRIPT.read_text(encoding="utf-8")
        gdb = _Gdb(fail_watch="*(void **)0x1018")

        output = _execute_setup(script, gdb)

        self.assertIn("watch -l sync->signaled", gdb.commands)
        self.assertIn("watch -l *(void **)0x1018", gdb.commands)
        self.assertIn(SIGNAL_ARMED, output)
        self.assertIn("FLR0348_FENCE_WATCH_SETUP_FAIL=", output)
        self.assertNotIn(ALL_ARMED, output)
        self.assertEqual(0, int(gdb.convenience["flr0348_ready"]))

    def test_a_rejected_signal_watch_never_arms_all(self) -> None:
        script = GDB_SCRIPT.read_text(encoding="utf-8")
        gdb = _Gdb(fail_watch="sync->signaled")

        output = _execute_setup(script, gdb)

        self.assertIn("FLR0348_SIGNAL_WATCH_SETUP_FAIL=", output)
        self.assertIn("watch -l *(void **)0x1018", gdb.commands)
        self.assertIn(FENCE_ARMED, output)
        self.assertNotIn(ALL_ARMED, output)
        self.assertEqual(0, int(gdb.convenience["flr0348_ready"]))

    def test_runner_routes_0348_to_unique_qmp_and_dedicated_gdb_script(self) -> None:
        runner = RUNNER.read_text(encoding="utf-8")
        qemu_start = QEMU_START.read_text(encoding="utf-8")

        self.assertIn("flr0348-[0-9][0-9][0-9][0-9]", runner)
        self.assertIn("flr0347-*|flr0348-*", runner)
        self.assertIn("qmp-0348.sock", runner)
        self.assertIn("gdb_script_file=FLR-0348-sync-watch.gdb", runner)
        self.assertIn("qmp-0348.sock", qemu_start)
        self.assertIn("flr0348-[0-9][0-9][0-9][0-9]", qemu_start)
        self.assertIn("qmp-0344.sock", runner)
        self.assertIn("qmp-0347.sock", runner)
        self.assertIn('if grep -Fq "$arm_wait_pass_marker"', runner)
        self.assertIn('echo FLR0344_GDB_WATCH_WINDOW=SKIPPED arm-failed', runner)

    def test_shared_guest_slot_requires_fresh_log_and_hash_verified_script(self) -> None:
        runner = RUNNER.read_text(encoding="utf-8")
        preflight = PREFLIGHT_COMMAND.read_text(encoding="utf-8")
        gdb_launch = GDB_LAUNCH_COMMAND.read_text(encoding="utf-8")

        self.assertIn("[ ! -e /run/user/1001/flr0344-gdb-watch.log ]", preflight)
        self.assertIn("[ ! -e /run/user/1001/flr0344-gdb-watch.pid ]", preflight)
        self.assertIn("[ -e \"$gdb_log\" ]", gdb_launch)
        self.assertIn("[ -e \"$gdb_pidfile\" ]", gdb_launch)
        self.assertIn('sha256sum "$run_dir/$gdb_script_file"', runner)
        self.assertIn("sha256sum /run/user/1001/flr0344-sync-watch.gdb", runner)


if __name__ == "__main__":
    unittest.main()
