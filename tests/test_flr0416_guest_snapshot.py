import importlib.util
from types import SimpleNamespace
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "work/commands/flr0416_guest_snapshot.py"
SPEC = importlib.util.spec_from_file_location("flr0416_guest_snapshot", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FLR0416GuestSnapshotTests(unittest.TestCase):
    def test_kernel_journal_uses_cursor_to_return_only_new_records(self):
        observed = {}

        def runner(command, **kwargs):
            observed.setdefault("calls", []).append((command, kwargs))
            if any(arg.startswith("--cursor=") for arg in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout="anchor record\n-- cursor: opaque=cursor-0\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=0,
                stdout="new kernel record\n-- cursor: opaque=cursor-1\n",
                stderr="",
            )

        text, cursor, observation = MODULE._run_journal(
            after_cursor="opaque=cursor-0", runner=runner
        )

        self.assertEqual("new kernel record", text)
        self.assertEqual("opaque=cursor-1", cursor)
        self.assertEqual("NEW_ENTRIES", observation)
        self.assertIn(
            "--after-cursor=opaque=cursor-0", observed["calls"][1][0]
        )
        self.assertIn("--cursor=opaque=cursor-0", observed["calls"][0][0])
        self.assertIn("--lines=+1", observed["calls"][0][0])
        self.assertEqual(3, len(observed["calls"]))
        self.assertTrue(all(call[1]["timeout"] <= 10 for call in observed["calls"]))

    def test_kernel_journal_requires_a_returned_cursor(self):
        result = SimpleNamespace(returncode=0, stdout="kernel record\n", stderr="")

        with self.assertRaisesRegex(MODULE.SnapshotError, "cursor is missing"):
            MODULE._run_journal(runner=lambda *args, **kwargs: result)

    def test_kernel_journal_accepts_empty_after_exact_verified_cursor(self):
        def runner(command, **kwargs):
            if any(arg.startswith("--cursor=") for arg in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout="anchor record\n-- cursor: opaque=valid-anchor\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=0, stdout="-- No entries --\n", stderr=""
            )

        text, cursor, observation = MODULE._run_journal(
            after_cursor="opaque=valid-anchor", runner=runner
        )
        self.assertEqual("", text)
        self.assertEqual("opaque=valid-anchor", cursor)
        self.assertEqual("NO_NEW_ENTRIES", observation)

    def test_kernel_journal_does_not_accept_empty_output_without_valid_anchor(self):
        result = SimpleNamespace(returncode=0, stdout="-- No entries --\n", stderr="")
        with self.assertRaisesRegex(MODULE.SnapshotError, "cursor is missing"):
            MODULE._run_journal(runner=lambda *args, **kwargs: result)

    def test_kernel_journal_rejects_seek_that_resolves_to_nearest_cursor(self):
        def runner(command, **kwargs):
            if any(arg.startswith("--cursor=") for arg in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout="nearest record\n-- cursor: opaque=nearest\n",
                    stderr="",
                )
            self.fail("must not query after an unresolved cursor")

        with self.assertRaisesRegex(MODULE.SnapshotError, "different entry"):
            MODULE._run_journal(after_cursor="opaque=missing", runner=runner)

    def test_kernel_journal_rejects_anchor_rotated_during_incremental_read(self):
        calls = 0

        def runner(command, **kwargs):
            nonlocal calls
            calls += 1
            if any(arg.startswith("--cursor=") for arg in command):
                cursor = "opaque=old" if calls == 1 else "opaque=nearest"
                return SimpleNamespace(
                    returncode=0,
                    stdout="record\n-- cursor: " + cursor + "\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=0, stdout="-- No entries --\n", stderr=""
            )

        with self.assertRaisesRegex(MODULE.SnapshotError, "different entry"):
            MODULE._run_journal(after_cursor="opaque=old", runner=runner)
        self.assertEqual(3, calls)

    def test_kernel_journal_rejects_empty_marker_with_cursor(self):
        def runner(command, **kwargs):
            if any(arg.startswith("--cursor=") for arg in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout="anchor record\n-- cursor: opaque=old\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=0,
                stdout="-- No entries --\n-- cursor: opaque=next\n",
                stderr="",
            )

        with self.assertRaisesRegex(MODULE.SnapshotError, "conflicts"):
            MODULE._run_journal(after_cursor="opaque=old", runner=runner)

    def test_present_counts_distinguish_begin_return_and_success(self):
        counts = MODULE.parse_present_counts(
            "FLR0026_VK_QUEUE_PRESENT_BEGIN a\n"
            "FLR0026_VK_QUEUE_PRESENT result=0\n"
            "FLR0026_VK_QUEUE_PRESENT_BEGIN b\n"
            "FLR0026_VK_QUEUE_PRESENT result=-4\n"
        )

        self.assertEqual({"begin": 2, "return": 2, "success": 1}, counts)

    def test_kernel_fault_summary_counts_only_fault_boundaries(self):
        count, matches = MODULE.parse_kernel_faults(
            "normal boot\nBUG: unable to handle page fault\n"
            "RIP: 0033:0x123\nKilled process 7\n"
        )

        self.assertEqual(2, count)
        self.assertIn("BUG: unable to handle page fault", matches)
        self.assertIn("Killed process 7", matches)
        self.assertNotIn("normal boot", matches)

    def test_proc_identity_uses_starttime_after_parenthesized_comm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "321").mkdir()
            (root / "321" / "comm").write_text("flutter-auto\n", encoding="utf-8")
            (root / "321" / "status").write_text("Name:\tflutter-auto\nUid:\t1001\t1001\t1001\t1001\n", encoding="utf-8")
            fields = ["S"] + ["0"] * 18 + ["98765"]
            (root / "321" / "stat").write_text("321 (flutter (engine)) " + " ".join(fields), encoding="utf-8")

            identity = MODULE.proc_identity(root, 321)

        self.assertEqual(321, identity["pid"])
        self.assertEqual(1001, identity["uid"])
        self.assertEqual("98765", identity["start_token"])
        self.assertEqual("flutter-auto", identity["comm"])
        self.assertEqual("S", identity["state"])

    def test_proc_identity_fails_closed_when_status_is_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "322").mkdir()
            (root / "322" / "comm").write_text("gdb\n", encoding="utf-8")
            (root / "322" / "status").write_text("Name:\tgdb\n", encoding="utf-8")
            (root / "322" / "stat").write_text("322 (gdb) S " + "0 " * 19 + "1", encoding="utf-8")

            with self.assertRaisesRegex(MODULE.SnapshotError, "UID"):
                MODULE.proc_identity(root, 322)

    def test_zombie_identity_is_not_reported_as_live(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "323").mkdir()
            (root / "323" / "comm").write_text("flutter-auto\n", encoding="utf-8")
            (root / "323" / "status").write_text(
                "Name:\tflutter-auto\nUid:\t1001\t1001\t1001\t1001\n",
                encoding="utf-8",
            )
            fields = ["Z"] + ["0"] * 18 + ["98766"]
            (root / "323" / "stat").write_text(
                "323 (flutter-auto) " + " ".join(fields), encoding="utf-8"
            )
            expected = {"pid": 323, "uid": 1001, "start_token": "98766"}

            observed = MODULE._process_observation(root, expected, "flutter-auto", False)

        self.assertEqual("ZOMBIE", observed["state"])
        self.assertFalse(observed["matches"])


if __name__ == "__main__":
    unittest.main()
