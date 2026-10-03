import importlib.util
import ast
import hashlib
import json
import tempfile
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "work/commands/flr0416_gdb_observer.py"
CALLBACK = Path(__file__).parents[1] / "work/commands/flr0416_gdb_callback.py"
GDB_SCRIPT = Path(__file__).parents[1] / "work/commands/FLR-0416-prearm-libllvm.gdb"
SMOKE_GDB_SCRIPT = Path(__file__).parents[1] / "work/commands/FLR-0416-gdb-smoke.gdb"
SPEC = importlib.util.spec_from_file_location("flr0416_gdb_observer", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FLR0416GdbObserverTests(unittest.TestCase):
    def _write_release_fixture(self, directory, stage):
        root = Path(directory) / "flr0417-0001"
        expected = {
            "guest_boot_id": "boot-id-1",
            "process": {"pid": 1001, "uid": 1001, "start_token": "101"},
            "gdb_process": {"pid": 1002, "uid": 1001, "start_token": "102"},
        }
        names = ["flr0417-0001-armed.json"]
        if stage == "load":
            names.append("flr0417-0001-load-ready.json")
            records = {
                "flr0417-0001-load-ready.json": {
                    "event": "LOAD_READY",
                    "stop_boundary": "catch-load-libLLVM",
                    "load_catchpoint_disabled": True,
                    "all_app_threads_stopped": True,
                    "thread_states": [{"stopped": True}],
                    "target": expected,
                }
            }
        else:
            names.extend(
                [
                    "flr0417-0001-hit-begin",
                    "flr0417-0001-hit-record.json",
                    "flr0417-0001-hit-ready.json",
                ]
            )
            hit = {
                "event": "HIT_RECORD",
                "run_id": "flr0417-0001",
                "guest_boot_id": expected["guest_boot_id"],
                "process": expected["process"],
                "gdb_process": expected["gdb_process"],
                "errors": {},
                "target_pc_match": True,
                "identity_match": True,
                "pc": 0x1234,
                "pc_mapping": "r-xp libLLVM",
                "caller_resume_pc": 0x5678,
                "caller_mapping": "r-xp libflutter",
            }
            hit_target = {
                **expected,
                "library": {
                    "address": hit["pc"],
                    "mapping": hit["pc_mapping"],
                },
            }
            records = {
                "flr0417-0001-hit-record.json": hit,
                "flr0417-0001-hit-ready.json": {
                    "event": "HIT_READY",
                    "run_id": "flr0417-0001",
                    "stop_boundary": "temporary-hardware-breakpoint",
                    "target": hit_target,
                    "breakpoint": {"type": "hardware", "address": "0x1234"},
                    "release_eligible": True,
                    "release_blockers": [],
                    "all_app_threads_stopped": True,
                    "thread_states": [{"stopped": True}],
                    "hit": hit,
                },
            }

        files = {}
        for name in names:
            evidence = Path(directory) / name
            if name in records:
                content = MODULE.encode_hit_record(records[name]).encode("utf-8")
            elif name.endswith("-hit-begin"):
                content = b"HIT_BEGIN\n"
            else:
                content = (name + "\n").encode("utf-8")
            evidence.write_bytes(content)
            files[name] = {
                "source": "guest",
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        mini_names = (
            [
                "flr0417-0001-load-bracket.json",
                "flr0417-0001-qmp-load-still.ppm",
            ]
            if stage == "load"
            else [
                "flr0417-0001-hit-bracket.json",
                "flr0417-0001-qmp-hit-still.ppm",
                *[
                    "flr0417-0001-qmp-hit-frame-%04d.ppm" % index
                    for index in range(8)
                ],
            ]
        )
        for name in mini_names:
            files[name] = {
                "source": "mini",
                "sha256": hashlib.sha256(name.encode("utf-8")).hexdigest(),
            }

        manifest_path = Path(str(root) + "-" + stage + "-manifest.json")
        manifest = {
            "event": "EVIDENCE_MANIFEST",
            "run_id": "flr0417-0001",
            "stage": stage,
            **expected,
            "controller_acknowledged": True,
            "files": files,
        }
        manifest_text = MODULE.encode_hit_record(manifest)
        manifest_path.write_text(manifest_text, encoding="utf-8")
        manifest_hash = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
        release = {
            "event": "CONTROLLER_ACK",
            "run_id": "flr0417-0001",
            "stage": stage,
            **expected,
            "manifest_path": str(manifest_path),
            "manifest_sha256": manifest_hash,
            "acknowledged": True,
        }
        Path(str(root) + "-" + stage + "-release.json").write_text(
            MODULE.encode_hit_record(release), encoding="utf-8"
        )
        return root, expected

    def test_mapping_for_address_returns_exact_executable_mapping(self):
        expected = (
            "7fffefb00000-7fffefc00000 r-xp 00000000 08:02 123 "
            "/usr/lib/libLLVM.so.18.1"
        )
        maps = (
            "555555554000-555555556000 r--p 00000000 08:02 456 /usr/bin/flutter-auto\n"
            + expected
            + "\n"
        )

        self.assertEqual(
            expected,
            MODULE.mapping_for_address(maps, 0x7FFFEFB4D541),
        )

    def test_mapping_for_address_rejects_missing_executable_mapping(self):
        maps = "7fffefb00000-7fffefc00000 r--p 00000000 08:02 123 /usr/lib/libLLVM.so.18.1\n"

        with self.assertRaisesRegex(ValueError, "found 0"):
            MODULE.mapping_for_address(maps, 0x7FFFEFB4D541)

    def test_mapping_for_address_rejects_ambiguous_executable_mapping(self):
        maps = (
            "7fffefb00000-7fffefc00000 r-xp 00000000 08:02 123 /usr/lib/first.so\n"
            "7fffefb40000-7fffefc50000 r-xp 00004000 08:02 123 /usr/lib/second.so\n"
        )

        with self.assertRaisesRegex(ValueError, "found 2"):
            MODULE.mapping_for_address(maps, 0x7FFFEFB4D541)

    def test_encode_hit_record_is_sorted_compact_json_with_one_newline(self):
        fields = {"event": "HIT", "pc": "0x42", "boot_id": "boot-1"}

        encoded = MODULE.encode_hit_record(fields)

        self.assertEqual(
            '{"boot_id":"boot-1","event":"HIT","pc":"0x42"}\n',
            encoded,
        )
        self.assertEqual(encoded, MODULE.encode_hit_record(dict(reversed(list(fields.items())))))

    def test_encode_hit_record_escapes_embedded_newlines(self):
        encoded = MODULE.encode_hit_record({"value": "first\nsecond"})

        self.assertEqual('{"value":"first\\nsecond"}\n', encoded)

    def test_hit_identity_requires_exact_debugger_and_inferior(self):
        expected = {
            "guest_boot_id": "boot-1",
            "process": {"pid": 11, "uid": 1001, "start_token": "21"},
            "gdb_process": {"pid": 12, "uid": 1001, "start_token": "22"},
        }
        self.assertTrue(MODULE.target_identity_matches(expected, expected))
        changed_gdb = {
            **expected,
            "gdb_process": {"pid": 12, "uid": 1001, "start_token": "23"},
        }
        self.assertFalse(MODULE.target_identity_matches(changed_gdb, expected))

    def test_create_once_persists_record_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hit-begin"

            MODULE.create_once(path, "HIT_BEGIN\n")

            self.assertEqual("HIT_BEGIN\n", path.read_text(encoding="utf-8"))
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            with self.assertRaises(FileExistsError):
                MODULE.create_once(path, "overwritten\n")
            self.assertEqual("HIT_BEGIN\n", path.read_text(encoding="utf-8"))

    def test_publish_once_exposes_only_complete_record_and_rejects_overwrite(self):
        import os
        from unittest import mock

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ready.json"
            expected = '{"event":"READY"}\n'
            original_link = os.link
            publications = []

            def inspect_then_link(source, destination):
                self.assertFalse(path.exists())
                self.assertEqual(expected.encode(), Path(source).read_bytes())
                publications.append((source, destination))
                return original_link(source, destination)

            with mock.patch.object(os, "link", side_effect=inspect_then_link):
                MODULE.publish_once(path, expected)

            self.assertEqual(1, len(publications))
            self.assertEqual(expected, path.read_text(encoding="utf-8"))
            self.assertFalse(list(Path(directory).glob(".flr0416-publish-*")))
            with self.assertRaises(FileExistsError):
                MODULE.publish_once(path, "replacement\n")
            self.assertEqual(expected, path.read_text(encoding="utf-8"))

    def test_gdb_python_blocks_are_valid_python(self):
        compile(CALLBACK.read_text(encoding="utf-8"), str(CALLBACK), "exec")
        for path in (GDB_SCRIPT, SMOKE_GDB_SCRIPT):
            with self.subTest(script=path.name):
                source = path.read_text(encoding="utf-8")
                in_block = False
                block = []
                block_count = 0

                for line in source.splitlines():
                    if line == "python":
                        self.assertFalse(in_block, "nested GDB python block")
                        in_block = True
                        block = []
                    elif line == "end" and in_block:
                        compile("\n".join(block), str(path), "exec")
                        block_count += 1
                        in_block = False
                    elif in_block:
                        block.append(line)

                self.assertFalse(in_block, "unterminated GDB python block")
                self.assertGreater(block_count, 0)

    def test_breakpoint_stop_writes_marker_first_and_never_runs_gdb_commands(self):
        tree = ast.parse(CALLBACK.read_text(encoding="utf-8"))
        breakpoint_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "FirstHitBreakpoint"
        )
        stop = next(node for node in breakpoint_class.body if node.name == "stop")
        first = stop.body[0]
        first_call = first.body[0].value
        self.assertIsInstance(first, ast.Try)
        self.assertEqual("create_once", first_call.func.attr)
        self.assertFalse(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute"
                for node in ast.walk(stop)
            )
        )
        self.assertIsInstance(stop.body[-1], ast.Return)
        self.assertIs(stop.body[-1].value.value, True)

    def test_consumed_json_uses_atomic_publication_and_guest_deadline_is_bounded(self):
        callback_source = CALLBACK.read_text(encoding="utf-8")
        self.assertIn(
            "observer.publish_once(path, observer.encode_hit_record(fields))",
            callback_source,
        )
        self.assertIn("ACK_COLLECTION_SECONDS = 540", callback_source)
        self.assertIn("ACK_ABORT_GRACE_SECONDS = 60", callback_source)
        self.assertIn('wait_for_release("load", ACK_COLLECTION_SECONDS)', callback_source)
        self.assertIn('wait_for_release("hit", ACK_COLLECTION_SECONDS)', callback_source)
        self.assertIn("ACK_COLLECTION_SECONDS = 540", Path(__file__).parents[1].joinpath("scripts/flr0416_live_capture.py").read_text(encoding="utf-8"))
        host_source = Path(__file__).parents[1].joinpath(
            "scripts/flr0416_live_capture.py"
        ).read_text(encoding="utf-8")
        self.assertIn("ACK_COLLECTION_SECONDS = 540", host_source)
        self.assertIn(" 1800s ", host_source)

    def test_load_command_list_does_not_wait_or_continue(self):
        lines = GDB_SCRIPT.read_text(encoding="utf-8").splitlines()
        start = lines.index("commands 1")
        end = lines.index("end", start + 1)
        command_list = lines[start + 1 : end]

        self.assertNotIn("continue", command_list)
        self.assertFalse(any("wait_for_release" in line for line in command_list))
        self.assertIn("handle SIGINT stop print nopass", lines)

    def test_controller_release_checks_manifest_digest_and_guest_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root, expected = self._write_release_fixture(directory, "hit")

            self.assertTrue(
                MODULE.validate_controller_release(str(root), "hit", expected)
            )
            (Path(directory) / "flr0417-0001-hit-record.json").write_text(
                "tampered\n", encoding="utf-8"
            )
            self.assertFalse(
                MODULE.validate_controller_release(str(root), "hit", expected)
            )

    def test_controller_release_rejects_manifest_without_all_hit_qmp_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            root, expected = self._write_release_fixture(directory, "hit")
            manifest_path = Path(str(root) + "-hit-manifest.json")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            del manifest["files"]["flr0417-0001-qmp-hit-frame-0007.ppm"]
            manifest_text = MODULE.encode_hit_record(manifest)
            manifest_path.write_text(manifest_text, encoding="utf-8")

            release_path = Path(str(root) + "-hit-release.json")
            release = json.loads(release_path.read_text(encoding="utf-8"))
            release["manifest_sha256"] = hashlib.sha256(
                manifest_text.encode("utf-8")
            ).hexdigest()
            release_path.write_text(
                MODULE.encode_hit_record(release), encoding="utf-8"
            )

            self.assertFalse(
                MODULE.validate_controller_release(str(root), "hit", expected)
            )

    def test_controller_release_rejects_mismatched_gdb_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root, expected = self._write_release_fixture(directory, "load")
            release_path = Path(str(root) + "-load-release.json")
            release = json.loads(release_path.read_text(encoding="utf-8"))
            release["gdb_process"]["start_token"] = "wrong"
            release_path.write_text(
                MODULE.encode_hit_record(release), encoding="utf-8"
            )

            self.assertFalse(
                MODULE.validate_controller_release(str(root), "load", expected)
            )

    def test_controller_abort_requires_exact_run_and_process_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root, expected = self._write_release_fixture(directory, "hit")
            abort = {
                "event": "CONTROLLER_ABORT",
                "run_id": "flr0417-0001",
                "stage": "hit",
                **expected,
                "reason": "caller_mapping_unknown",
            }
            abort_path = Path(str(root) + "-hit-abort.json")
            MODULE.create_once(abort_path, MODULE.encode_hit_record(abort))

            self.assertTrue(
                MODULE.validate_controller_abort(str(root), "hit", expected)
            )
            expected["gdb_process"]["start_token"] = "stale"
            self.assertFalse(
                MODULE.validate_controller_abort(str(root), "hit", expected)
            )


if __name__ == "__main__":
    unittest.main()
