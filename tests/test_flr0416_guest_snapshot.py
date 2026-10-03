import importlib.util
import contextlib
import io
import json
from types import SimpleNamespace
from pathlib import Path
import sys
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

        result = MODULE._run_journal(after_cursor="opaque=cursor-0", runner=runner)

        self.assertEqual(0, result.fault_count)
        self.assertEqual("opaque=cursor-1", result.cursor)
        self.assertEqual("NEW_ENTRIES", result.observation)
        self.assertFalse(result.diagnostics["query"]["cursor_equal_anchor"])
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

        result = MODULE._run_journal(after_cursor="opaque=valid-anchor", runner=runner)
        self.assertEqual("opaque=valid-anchor", result.cursor)
        self.assertEqual("NO_NEW_ENTRIES", result.observation)
        self.assertEqual(
            "NO_NEW_ENTRIES_NO_CURSOR",
            result.diagnostics["query"]["classification"],
        )

    def test_kernel_journal_does_not_accept_empty_output_without_valid_anchor(self):
        result = SimpleNamespace(returncode=0, stdout="-- No entries --\n", stderr="")
        with self.assertRaisesRegex(MODULE.SnapshotError, "not exact"):
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

        with self.assertRaisesRegex(MODULE.SnapshotError, "resolve exactly"):
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

        with self.assertRaisesRegex(MODULE.SnapshotError, "resolve exactly"):
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

        with self.assertRaisesRegex(MODULE.SnapshotError, "did not equal"):
            MODULE._run_journal(after_cursor="opaque=old", runner=runner)

    def test_kernel_journal_accepts_empty_marker_with_exact_anchor_cursor(self):
        def runner(command, **kwargs):
            if any(arg.startswith("--cursor=") for arg in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout="anchor record\n-- cursor: opaque=old\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=0,
                stdout="-- No entries --\n-- cursor: opaque=old\n",
                stderr="",
            )

        result = MODULE._run_journal(after_cursor="opaque=old", runner=runner)

        self.assertEqual("opaque=old", result.cursor)
        self.assertEqual("NO_NEW_ENTRIES", result.observation)
        self.assertTrue(result.diagnostics["query"]["cursor_equal_anchor"])
        self.assertTrue(result.diagnostics["anchor_before"]["exact_anchor"])
        self.assertTrue(result.diagnostics["anchor_after"]["exact_anchor"])

    def test_kernel_journal_rejects_empty_marker_with_extra_output(self):
        def runner(command, **kwargs):
            if any(arg.startswith("--cursor=") for arg in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout="anchor record\n-- cursor: opaque=old\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=0,
                stdout="-- No entries --\nunexpected line\n-- cursor: opaque=old\n",
                stderr="",
            )

        with self.assertRaisesRegex(MODULE.SnapshotError, "not exact"):
            MODULE._run_journal(after_cursor="opaque=old", runner=runner)

    def test_kernel_journal_rejects_duplicate_cursor_in_empty_response(self):
        def runner(command, **kwargs):
            if any(arg.startswith("--cursor=") for arg in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout="anchor record\n-- cursor: opaque=old\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "-- No entries --\n"
                    "-- cursor: opaque=old\n"
                    "-- cursor: opaque=old\n"
                ),
                stderr="",
            )

        with self.assertRaisesRegex(MODULE.SnapshotError, "did not equal") as caught:
            MODULE._run_journal(after_cursor="opaque=old", runner=runner)
        marker = MODULE._failure_marker(caught.exception)
        self.assertNotIn("opaque=old", marker)

    def test_kernel_journal_rejects_query_stderr_and_nonzero_status(self):
        def runner(command, **kwargs):
            if any(arg.startswith("--cursor=") for arg in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout="anchor record\n-- cursor: opaque=old\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=3,
                stdout="-- No entries --\n-- cursor: opaque=old\n",
                stderr="private stderr detail\n",
            )

        with self.assertRaisesRegex(MODULE.SnapshotError, "returned an error") as caught:
            MODULE._run_journal(after_cursor="opaque=old", runner=runner)
        marker = MODULE._failure_marker(caught.exception)
        self.assertNotIn("private stderr detail", marker)
        self.assertNotIn("opaque=old", marker)

    def test_failure_marker_and_emitted_baseline_do_not_expose_cursor(self):
        cursor = "opaque=secret"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            MODULE._emit({"event": "KERNEL_BASELINE", "journal_cursor": cursor})
        encoded = output.getvalue().strip().split("=", 1)[1]
        public = json.loads(MODULE.base64.b64decode(encoded).decode("utf-8"))
        self.assertNotIn(cursor, json.dumps(public))
        self.assertEqual(
            MODULE.hashlib.sha256(cursor.encode("ascii")).hexdigest(),
            public["journal_cursor_sha256"],
        )

    def test_journalctl_version_is_reduced_to_numeric_systemd_version(self):
        result = MODULE._journalctl_version(
            runner=lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout="systemd 255 (255.4-1)\nPAM\n",
                stderr="",
            )
        )
        self.assertEqual("systemd-255", result)

    def test_bounded_collector_drains_both_pipes_concurrently(self):
        code = (
            "import os\n"
            "for _ in range(80):\n"
            " os.write(1, b'x'*1023 + b'\\n')\n"
            " os.write(2, b'y'*1023 + b'\\n')\n"
        )
        result = MODULE._collect_bounded_command(
            [sys.executable, "-c", code],
            timeout=5,
            max_output_bytes=256 * 1024,
            max_line_bytes=4096,
        )

        self.assertTrue(result.complete)
        self.assertTrue(result.reaped)
        self.assertEqual(80 * 1024, result.stdout_bytes)
        self.assertEqual(80 * 1024, result.stderr_bytes)
        self.assertFalse(result.stderr_empty)

    def test_bounded_collector_stops_and_reaps_on_total_byte_limit(self):
        code = "import os\nwhile True: os.write(1, b'x'*4095 + b'\\n')\n"
        result = MODULE._collect_bounded_command(
            [sys.executable, "-c", code],
            timeout=5,
            max_output_bytes=4096,
            max_line_bytes=8192,
        )

        self.assertTrue(result.oversized)
        self.assertTrue(result.truncated)
        self.assertFalse(result.complete)
        self.assertTrue(result.reaped)
        self.assertLessEqual(result.total_bytes_seen, 4097)

    def test_bounded_collector_stops_and_reaps_on_line_state_limit(self):
        code = "import os\nos.write(1, b'x'*100 + b'\\n')\n"
        result = MODULE._collect_bounded_command(
            [sys.executable, "-c", code],
            timeout=5,
            max_output_bytes=1024,
            max_line_bytes=32,
        )

        self.assertTrue(result.line_overflow)
        self.assertTrue(result.truncated)
        self.assertFalse(result.complete)
        self.assertTrue(result.reaped)

    def test_bounded_collector_times_out_and_reaps(self):
        result = MODULE._collect_bounded_command(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=0.1,
            max_output_bytes=1024,
            max_line_bytes=128,
        )

        self.assertTrue(result.timed_out)
        self.assertTrue(result.truncated)
        self.assertFalse(result.complete)
        self.assertTrue(result.reaped)

    def test_cursor_diagnostics_never_contain_raw_cursor_or_kernel_line(self):
        def runner(command, **kwargs):
            if any(arg.startswith("--cursor=") for arg in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout="private kernel detail\n-- cursor: opaque=secret\n",
                    stderr="",
                )
            return SimpleNamespace(
                returncode=0,
                stdout="-- No entries --\n-- cursor: opaque=secret\n",
                stderr="",
            )

        result = MODULE._run_journal(after_cursor="opaque=secret", runner=runner)
        serialized = json.dumps(result.diagnostics, sort_keys=True)

        self.assertEqual("NO_NEW_ENTRIES", result.observation)
        self.assertIn('"cursor_equal_anchor": true', serialized)
        self.assertNotIn("opaque=secret", serialized)
        self.assertNotIn("private kernel detail", serialized)

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
        self.assertEqual(["KERNEL_FAULT", "MEMORY"], [item["category"] for item in matches])
        self.assertTrue(all("line_sha256" in item for item in matches))
        self.assertNotIn("BUG: unable to handle page fault", json.dumps(matches))
        self.assertNotIn("Killed process 7", json.dumps(matches))

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
