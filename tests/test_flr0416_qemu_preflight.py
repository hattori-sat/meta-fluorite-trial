import importlib.util
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch


HELPER = Path(__file__).parents[1] / "work/commands/flr0416_qemu_preflight.py"
STARTER = Path(__file__).parents[1] / "work/commands/FLR-0416-qemu-start.sh"
SPEC = importlib.util.spec_from_file_location("flr0416_qemu_preflight", HELPER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FLR0416QemuPreflightTests(unittest.TestCase):
    def _proc_fixture(self, directory, processes=(), mount_options="rw"):
        root = Path(directory) / "proc"
        root.mkdir()
        mountinfo = Path(directory) / "mountinfo"
        mountinfo.write_text(
            "25 20 0:22 / /proc rw,nosuid,nodev,noexec - proc proc "
            + mount_options
            + "\n",
            encoding="utf-8",
        )
        for pid, uid, comm, argv in processes:
            process = root / str(pid)
            process.mkdir()
            (process / "comm").write_text(comm + "\n", encoding="utf-8")
            (process / "cmdline").write_bytes(b"\0".join(
                value.encode() for value in argv
            ) + b"\0")
            (process / "status").write_text(
                "Name:\t"
                + comm
                + "\nState:\tR (running)\nUid:\t"
                + "\t".join([str(uid)] * 4)
                + "\n",
                encoding="utf-8",
            )
        return root, mountinfo

    def test_process_scan_reports_other_uid_zombie_owner_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            root, mountinfo = self._proc_fixture(
                directory,
                [(701, 1001, "qemu-system-x86", ["/usr/bin/qemu-system-x86_64", "-S"])],
            )
            status = root / "701" / "status"
            status.write_text(
                status.read_text(encoding="utf-8").replace(
                    "State:\tR (running)", "State:\tZ (zombie)"
                ),
                encoding="utf-8",
            )

            result = MODULE.scan_processes(str(root), str(mountinfo))

            self.assertEqual(1, result["scanned"])
            self.assertEqual(
                [{"pid": 701, "uid": 1001, "kind": ["qemu"], "state": "Z"}],
                result["owners"],
            )

    def test_process_scan_blocks_devtool_and_bitbake_server_owners(self):
        with tempfile.TemporaryDirectory() as directory:
            root, mountinfo = self._proc_fixture(
                directory,
                [
                    (702, 1000, "devtool", ["devtool", "status"]),
                    (703, 1000, "bitbake-server", ["bitbake-server"]),
                ],
            )
            result = MODULE.scan_processes(str(root), str(mountinfo))

        self.assertEqual(
            [
                {"pid": 702, "uid": 1000, "kind": ["devtool"], "state": "R"},
                {"pid": 703, "uid": 1000, "kind": ["bitbake"], "state": "R"},
            ],
            result["owners"],
        )

    def test_process_scan_rejects_hidepid_that_can_hide_other_uids(self):
        with tempfile.TemporaryDirectory() as directory:
            root, mountinfo = self._proc_fixture(
                directory, mount_options="rw,hidepid=2"
            )

            with self.assertRaisesRegex(MODULE.PreflightError, "proc-visibility"):
                MODULE.scan_processes(str(root), str(mountinfo))

    def test_process_scan_fails_closed_when_enumeration_or_mount_visibility_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root, mountinfo = self._proc_fixture(directory)
            missing_proc = Path(directory) / "missing-proc"
            with self.assertRaisesRegex(MODULE.PreflightError, "proc-enumeration-failed"):
                MODULE.scan_processes(str(missing_proc), str(mountinfo))
            with self.assertRaisesRegex(MODULE.PreflightError, "proc-visibility"):
                MODULE.scan_processes(str(root), str(Path(directory) / "missing-mountinfo"))

    def test_process_scan_rejects_unresolved_live_entry_instead_of_skipping_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root, mountinfo = self._proc_fixture(
                directory, [(704, 1004, "ordinary", ["ordinary"]) ]
            )
            cmdline = str(root / "704" / "cmdline")
            real_open = open

            def incomplete_cmdline(path, *args, **kwargs):
                if str(path) == cmdline:
                    raise FileNotFoundError("fixture missing live cmdline")
                return real_open(path, *args, **kwargs)

            with patch("builtins.open", side_effect=incomplete_cmdline):
                with self.assertRaisesRegex(MODULE.PreflightError, "proc-entry-incomplete"):
                    MODULE.scan_processes(str(root), str(mountinfo))

    def test_process_scan_fails_closed_when_a_live_proc_entry_is_unreadable(self):
        with tempfile.TemporaryDirectory() as directory:
            root, mountinfo = self._proc_fixture(
                directory, [(702, 1002, "ordinary", ["ordinary"]) ]
            )
            cmdline = str(root / "702" / "cmdline")
            real_open = open

            def deny_cmdline(path, *args, **kwargs):
                if str(path) == cmdline:
                    raise PermissionError("fixture permission denial")
                return real_open(path, *args, **kwargs)

            with patch("builtins.open", side_effect=deny_cmdline):
                with self.assertRaisesRegex(MODULE.PreflightError, "proc-entry-unreadable"):
                    MODULE.scan_processes(str(root), str(mountinfo))

    def test_process_scan_ignores_only_an_entry_that_vanished_during_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root, mountinfo = self._proc_fixture(
                directory, [(703, 1003, "ordinary", ["ordinary"]) ]
            )
            process = root / "703"
            real_open = open
            denied = False

            def vanish_during_read(path, *args, **kwargs):
                nonlocal denied
                if str(path) == str(process / "cmdline") and not denied:
                    denied = True
                    for child in process.iterdir():
                        child.unlink()
                    process.rmdir()
                    raise FileNotFoundError("fixture process exit")
                return real_open(path, *args, **kwargs)

            with patch("builtins.open", side_effect=vanish_during_read):
                result = MODULE.scan_processes(str(root), str(mountinfo))

            self.assertEqual(1, result["scanned"])
            self.assertEqual(1, result["disappeared"])
            self.assertEqual([], result["owners"])

    def test_port_queries_are_targeted_and_fail_closed_on_command_errors(self):
        calls = []

        def free_ss(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, "", "")

        MODULE.check_ports_free([10943, 10944], runner=free_ss)
        self.assertEqual(
            [
                ["ss", "-H", "-ltn", "( sport = :10943 )"],
                ["ss", "-H", "-ltn", "( sport = :10944 )"],
            ],
            calls,
        )

        def busy_ss(args, **kwargs):
            return subprocess.CompletedProcess(args, 0, "LISTEN 0 5 *:10943 *:*\n", "")

        with self.assertRaisesRegex(MODULE.PreflightError, "port-in-use:10943"):
            MODULE.check_ports_free([10943], runner=busy_ss)

        def broken_ss(args, **kwargs):
            return subprocess.CompletedProcess(args, 2, "", "ss fixture failure")

        with self.assertRaisesRegex(MODULE.PreflightError, "port-inspection-failed"):
            MODULE.check_ports_free([10943], runner=broken_ss)

        def warning_ss(args, **kwargs):
            return subprocess.CompletedProcess(args, 0, "", "ss fixture warning")

        with self.assertRaisesRegex(MODULE.PreflightError, "port-inspection-failed"):
            MODULE.check_ports_free([10943], runner=warning_ss)

    def test_port_queries_reject_invalid_ports(self):
        with self.assertRaisesRegex(MODULE.PreflightError, "port-list-invalid"):
            MODULE.check_ports_free([0], runner=lambda *args, **kwargs: None)

    def test_port_queries_fail_closed_when_ss_is_missing(self):
        def missing_ss(args, **kwargs):
            raise FileNotFoundError("ss")

        with self.assertRaisesRegex(MODULE.PreflightError, "port-inspection-failed"):
            MODULE.check_ports_free([10943], runner=missing_ss)

    def test_start_script_uses_testable_gate_and_does_not_suppress_ss_errors(self):
        source = STARTER.read_text(encoding="utf-8")
        self.assertIn("flr0416_qemu_preflight.py", source)
        self.assertIn("preflight|prepare|start|capture|postflight", source)
        self.assertIn('exec python3 "$repo_root/scripts/flr0416_live_capture.py"', source)
        self.assertIn("work/commands/flr0416_guest_snapshot.py", source)
        self.assertIn("FLR0416-staged-files.sha256", source)
        self.assertIn("ffmpeg-unavailable-for-required-video", source)
        self.assertIn('"$serial_port"', source)
        self.assertIn('"$ssh_port"', source)
        self.assertIn('"$telnet_port"', source)
        self.assertNotIn("owner_result=$(python3", source)
        self.assertNotIn('ss -H -ltn "( sport = :$port )" 2>/dev/null', source)


if __name__ == "__main__":
    unittest.main()
