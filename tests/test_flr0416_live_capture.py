import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from unittest import mock
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts/flr0416_live_capture.py"
SPEC = importlib.util.spec_from_file_location("flr0416_live_capture", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)


class FLR0416LiveCaptureTests(unittest.TestCase):
    def setUp(self):
        SPEC.loader.exec_module(MODULE)
        self.identity = {
            "guest_boot_id": "boot-abc",
            "process": {"pid": 300, "uid": 1001, "start_token": "400"},
            "gdb_process": {"pid": 301, "uid": 1001, "start_token": "401"},
        }

    def _guest_files(self, stage):
        prefix = "flr0416-0001-"
        armed = {
            "guest_boot_id": self.identity["guest_boot_id"],
            "process": self.identity["process"],
            "gdb_process": self.identity["gdb_process"],
        }
        files = {prefix + "armed.json": json.dumps(armed).encode()}
        if stage == "load":
            ready = {
                "event": "LOAD_READY",
                "target": armed,
            }
            files[prefix + "load-ready.json"] = json.dumps(ready).encode()
        else:
            files[prefix + "hit-begin"] = b"HIT_BEGIN\n"
            hit = {
                "event": "HIT_RECORD",
                "guest_boot_id": self.identity["guest_boot_id"],
                "process": self.identity["process"],
                "gdb_process": self.identity["gdb_process"],
            }
            ready = {"event": "HIT_READY", "target": armed, "hit": hit}
            files[prefix + "hit-record.json"] = json.dumps(hit).encode()
            files[prefix + "hit-ready.json"] = json.dumps(ready).encode()
        return files

    def _mini_files(self, stage):
        prefix = "flr0416-0001-"
        if stage == "load":
            names = [prefix + "load-bracket.json", prefix + "qmp-load-still.ppm"]
        else:
            names = [prefix + "hit-bracket.json", prefix + "qmp-hit-still.ppm"]
            names += [prefix + "qmp-hit-frame-%04d.ppm" % i for i in range(8)]
        return {name: ("media:" + name).encode() for name in names}

    def test_payload_chunks_and_shell_commands_stay_inside_serial_contract(self):
        payload = bytes(range(256)) * 41

        chunks = MODULE.payload_chunks(payload, max_chars=3000)
        commands = MODULE.payload_shell_commands(
            "/run/user/1001/flr0416-0001/payload.bin", payload
        )

        encoded = "".join(chunks)
        self.assertEqual(payload, MODULE.base64.b64decode(encoded, validate=True))
        self.assertTrue(commands)
        self.assertTrue(all("\n" not in command and len(command) <= 4096 for command in commands))
        for command in commands:
            syntax = subprocess.run(
                ["/bin/bash", "-n", "-c", command],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, syntax.returncode, syntax.stderr)
        self.assertIn("set -C", commands[0])
        self.assertNotIn("/run/user/1001/flr0416-0001/payload.bin", " ".join(commands[:-1]))
        self.assertIn("os.link(tmp,dst)", commands[-1])
        self.assertIn("/run/user/1001/flr0416-0001/payload.bin", commands[-1])
        with self.assertRaisesRegex(ValueError, "empty guest payload"):
            MODULE.payload_shell_commands(
                "/run/user/1001/flr0416-0001/empty.bin", b""
            )

    def test_guest_setup_builds_only_bounded_one_line_serial_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "qemu"
            run_dir.mkdir()
            repo_root = Path(__file__).parents[1]
            controller = MODULE.CaptureController(
                run_dir, run_dir / "qmp.sock", repo_root=repo_root
            )
            observed = []

            def serial(label, command, timeout=40):
                observed.append((label, command))
                if label == "guest-preflight":
                    return "FLR0416_GUEST_PREFLIGHT=PASS"
                if label == "guest-run-dir":
                    return "FLR0416_GUEST_DIR=READY"
                if label.startswith("upload-"):
                    source_label, index_text = label[len("upload-"):].rsplit("-", 1)
                    content = (repo_root / "work/commands" / source_label).read_bytes()
                    total = len(
                        MODULE.payload_shell_commands(
                            MODULE.GUEST_DIR + "/" + source_label, content
                        )
                    )
                    return "FLR0416_PAYLOAD=PASS index=%d total=%d" % (int(index_text), total)
                if label.startswith("verify-"):
                    name = label[len("verify-"):]
                    content = (repo_root / "work/commands" / name).read_bytes()
                    return "FLR0416_GUEST_FILE_HASH=PASS name=%s sha256=%s" % (
                        name,
                        MODULE.sha256_bytes(content),
                    )
                if label == "gdb-api-smoke":
                    return "FLR0416_GDB_SMOKE=PASS app=NOT_STARTED hwbp=NOT_ATTEMPTED"
                if label == "kernel-baseline":
                    payload = MODULE.canonical_json({"event": "KERNEL_BASELINE"}).encode()
                    return "FLR0416_GUEST_SNAPSHOT=" + MODULE.base64.b64encode(payload).decode()
                self.fail("unexpected serial command label: " + label)

            with mock.patch.object(controller, "_serial", side_effect=serial):
                controller._guest_setup()

            self.assertGreater(len(observed), 10)
            self.assertTrue(
                all("\n" not in command and len(command) <= MODULE.SERIAL_COMMAND_LIMIT for _, command in observed)
            )

    def test_guest_file_decoder_requires_one_exact_named_payload(self):
        content = b'{"event":"LOAD_READY"}\n'
        import base64
        output = "noise\nFLR0416_FILE=flr0416-0001-load-ready.json:" + base64.b64encode(content).decode()

        self.assertEqual(
            content,
            MODULE.decode_guest_file(output, "flr0416-0001-load-ready.json"),
        )
        with self.assertRaisesRegex(ValueError, "exactly one"):
            MODULE.decode_guest_file(output + "\n" + output.splitlines()[-1], "flr0416-0001-load-ready.json")
        with self.assertRaisesRegex(ValueError, "base64"):
            MODULE.decode_guest_file("FLR0416_FILE=x:%%%", "x")

    def test_load_manifest_requires_exact_guest_and_qmp_artifacts(self):
        guest = self._guest_files("load")
        mini = self._mini_files("load")

        manifest_text = MODULE.build_manifest("load", self.identity, guest, mini)
        manifest = json.loads(manifest_text)

        self.assertEqual("EVIDENCE_MANIFEST", manifest["event"])
        self.assertEqual(self.identity["process"], manifest["process"])
        self.assertEqual("guest", manifest["files"]["flr0416-0001-load-ready.json"]["source"])
        self.assertEqual(
            hashlib.sha256(mini["flr0416-0001-qmp-load-still.ppm"]).hexdigest(),
            manifest["files"]["flr0416-0001-qmp-load-still.ppm"]["sha256"],
        )
        del mini["flr0416-0001-qmp-load-still.ppm"]
        with self.assertRaisesRegex(ValueError, "required Mini"):
            MODULE.build_manifest("load", self.identity, guest, mini)

    def test_hit_manifest_requires_all_eight_qmp_frames_and_matching_identity(self):
        guest = self._guest_files("hit")
        mini = self._mini_files("hit")
        del mini["flr0416-0001-qmp-hit-frame-0007.ppm"]

        with self.assertRaisesRegex(ValueError, "required Mini"):
            MODULE.build_manifest("hit", self.identity, guest, mini)

        mini = self._mini_files("hit")
        changed = dict(self.identity)
        changed["process"] = {**self.identity["process"], "start_token": "999"}
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            MODULE.build_manifest("hit", changed, guest, mini)

    def test_release_ack_is_digest_bound_and_identity_bound(self):
        manifest = MODULE.build_manifest(
            "load", self.identity, self._guest_files("load"), self._mini_files("load")
        )

        release = json.loads(
            MODULE.build_release("load", self.identity, manifest).decode("utf-8")
        )

        self.assertEqual("CONTROLLER_ACK", release["event"])
        self.assertTrue(release["acknowledged"])
        self.assertEqual(
            hashlib.sha256(manifest).hexdigest(), release["manifest_sha256"]
        )
        self.assertEqual(
            "/run/user/1001/flr0416-0001-load-manifest.json",
            release["manifest_path"],
        )

        acceptance = {
            "event": "GUEST_RELEASE_ACCEPTED",
            "run_id": MODULE.RUN_ID,
            "stage": "load",
            **self.identity,
            "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "release_sha256": hashlib.sha256(
                MODULE.build_release("load", self.identity, manifest)
            ).hexdigest(),
        }
        release_bytes = MODULE.build_release("load", self.identity, manifest)
        self.assertTrue(
            MODULE.validate_release_acceptance(
                json.dumps(acceptance).encode(), "load", self.identity, manifest, release_bytes
            )
        )
        acceptance["release_sha256"] = "0" * 64
        self.assertFalse(
            MODULE.validate_release_acceptance(
                json.dumps(acceptance).encode(), "load", self.identity, manifest, release_bytes
            )
        )

    def test_release_publishes_the_already_saved_manifest_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "qemu"
            run_dir.mkdir()
            repo_root = root / "repo"
            repo_root.mkdir()
            manifest = MODULE.build_manifest(
                "load", self.identity, self._guest_files("load"), self._mini_files("load")
            )
            manifest_path = run_dir / "flr0416-0001-load-manifest.json"
            manifest_path.write_bytes(manifest)
            controller = MODULE.CaptureController(
                run_dir, run_dir / "qmp.sock", repo_root=repo_root
            )
            controller.identity = self.identity

            def serial_marker(label, *args):
                index = int(label.rsplit("-", 1)[1])
                return "FLR0416_PAYLOAD=PASS index=%d total=2" % index

            with mock.patch.object(
                controller,
                "_serial",
                side_effect=serial_marker,
            ):
                controller._publish_release("load", manifest)

            self.assertEqual(manifest, manifest_path.read_bytes())
            release = json.loads(
                (run_dir / "flr0416-0001-load-release.json").read_text(encoding="utf-8")
            )
            self.assertEqual(hashlib.sha256(manifest).hexdigest(), release["manifest_sha256"])

    def test_load_ready_requires_disabled_catchpoint_and_all_threads_stopped(self):
        target = {
            "guest_boot_id": self.identity["guest_boot_id"],
            "process": self.identity["process"],
            "gdb_process": self.identity["gdb_process"],
        }
        ready = {
            "event": "LOAD_READY",
            "stop_boundary": "catch-load-libLLVM",
            "target": target,
            "load_catchpoint_disabled": True,
            "all_app_threads_stopped": True,
            "thread_states": [{"stopped": True}],
        }
        payload = json.dumps(ready).encode()
        self.assertTrue(MODULE.validate_stage_ready("load", payload, self.identity))
        ready["thread_states"] = [{"stopped": False}]
        self.assertFalse(MODULE.validate_stage_ready("load", json.dumps(ready).encode(), self.identity))

    def test_hit_ready_requires_exact_hardware_pc_caller_and_release_eligibility(self):
        target = {
            "guest_boot_id": self.identity["guest_boot_id"],
            "process": self.identity["process"],
            "gdb_process": self.identity["gdb_process"],
        }
        hit = {
            "event": "HIT_RECORD",
            "guest_boot_id": self.identity["guest_boot_id"],
            "process": self.identity["process"],
            "gdb_process": self.identity["gdb_process"],
            "target_pc_match": True,
            "identity_match": True,
            "errors": {},
            "pc": 0x1234,
            "pc_mapping": "r-xp libLLVM",
            "caller_resume_pc": 0x5678,
            "caller_mapping": "r-xp libflutter",
        }
        ready = {
            "event": "HIT_READY",
            "stop_boundary": "temporary-hardware-breakpoint",
            "target": target,
            "breakpoint": {"type": "hardware", "address": "0x1234"},
            "hit": hit,
            "release_eligible": True,
            "release_blockers": [],
            "all_app_threads_stopped": True,
            "thread_states": [{"stopped": True}],
        }
        payload = json.dumps(ready).encode()
        self.assertTrue(MODULE.validate_stage_ready("hit", payload, self.identity))
        ready["breakpoint"]["address"] = "0x9999"
        self.assertFalse(MODULE.validate_stage_ready("hit", json.dumps(ready).encode(), self.identity))

    def test_bracket_rejects_reversed_host_interval_and_identity_change(self):
        sample = {
            "guest_boot_id": "boot-abc",
            "guest_wall_ns": 100,
            "guest_monotonic_ns": 200,
            "process": self.identity["process"],
            "gdb_process": self.identity["gdb_process"],
            "present": {"begin": 2, "return": 1, "success": 1},
            "kernel": {"baseline": 0, "current": 0, "delta": 0},
            "process_observation": {
                "state": "LIVE",
                "matches": True,
                "actual": {
                    **self.identity["process"],
                    "comm": "flutter-auto",
                    "state": "T",
                },
            },
            "gdb_observation": {
                "state": "LIVE",
                "matches": True,
                "actual": {
                    **self.identity["gdb_process"],
                    "comm": "gdb",
                    "state": "S",
                },
            },
        }
        hashes = {"flr0416-0001-qmp-load-still.ppm": "a" * 64}
        record = MODULE.build_bracket(
            "load", self.identity, sample, sample, 10, 20, hashes, 100, 200
        )
        self.assertEqual("QMP_CAPTURE_BRACKET", json.loads(record)["event"])
        with self.assertRaisesRegex(ValueError, "host interval"):
            MODULE.build_bracket("load", self.identity, sample, sample, 20, 10, hashes, 100, 200)
        changed = {**sample, "guest_boot_id": "other"}
        with self.assertRaisesRegex(ValueError, "identity changed"):
            MODULE.build_bracket("load", self.identity, sample, changed, 10, 20, hashes, 100, 200)

    def test_bracket_rejects_dead_identity_or_incomplete_capture_set(self):
        sample = {
            "guest_boot_id": self.identity["guest_boot_id"],
            "guest_wall_ns": 100,
            "guest_monotonic_ns": 200,
            "process": self.identity["process"],
            "gdb_process": self.identity["gdb_process"],
            "present": {"begin": 2, "return": 1, "success": 1},
            "kernel": {"baseline": 0, "current": 0, "delta": 0},
            "process_observation": {
                "state": "LIVE",
                "matches": True,
                "actual": {**self.identity["process"], "comm": "flutter-auto", "state": "T"},
            },
            "gdb_observation": {
                "state": "LIVE",
                "matches": True,
                "actual": {**self.identity["gdb_process"], "comm": "gdb", "state": "S"},
            },
        }
        args = ("load", self.identity, sample, sample, 10, 20)
        with self.assertRaisesRegex(ValueError, "required complete QMP frame set"):
            MODULE.build_bracket(*args, {}, 100, 200)
        stopped_dead = {**sample, "process_observation": {"state": "EXITED", "matches": False}}
        with self.assertRaisesRegex(ValueError, "matching live process"):
            MODULE.build_bracket(
                "load",
                self.identity,
                sample,
                stopped_dead,
                10,
                20,
                {"flr0416-0001-qmp-load-still.ppm": "a" * 64},
                100,
                200,
            )

    def test_ppm_validator_requires_complete_p6_rgb_raster(self):
        raster = bytes((0, 10, 32, 255, 1, 2))
        ppm = b"P6\n# QMP test\n2 1\n255\n" + raster

        self.assertEqual((2, 1), MODULE.parse_p6_ppm(ppm, 2, 1))
        with self.assertRaisesRegex(ValueError, "dimensions"):
            MODULE.parse_p6_ppm(ppm)
        with self.assertRaisesRegex(ValueError, "raster length"):
            MODULE.parse_p6_ppm(ppm[:-1], 2, 1)
        with self.assertRaisesRegex(ValueError, "raster length"):
            MODULE.parse_p6_ppm(ppm + b"x", 2, 1)
        with self.assertRaisesRegex(ValueError, "P6"):
            MODULE.parse_p6_ppm(b"P3\n2 1\n255\n" + raster, 2, 1)

    def test_gdb_interrupt_source_is_syntax_checked_pidfd_and_identity_bound(self):
        source = MODULE.gdb_interrupt_python_source()
        compile(source, "FLR0416-gdb-interrupt.py", "exec")
        command = MODULE.interrupt_gdb_command(
            self.identity["gdb_process"],
            self.identity["process"],
            expected_gdb=self.identity["gdb_process"],
        )
        self.assertIn("pidfd_open", source)
        self.assertIn("pidfd_send_signal", source)
        self.assertIn("TracerPid:", source)
        self.assertLessEqual(len(command), MODULE.SERIAL_COMMAND_LIMIT)
        self.assertNotIn("\n", command)
        self.assertNotIn("kill -INT", command)
        self.assertIn("base64.b64decode", command)
        self.assertTrue(command.endswith(" 301 401 300 400"))
        argv = MODULE.shlex.split(command.split("; ", 1)[1])
        self.assertEqual(["python3", "-c"], argv[:2])
        encoded = argv[2].split("base64.b64decode('", 1)[1][:-3]
        self.assertEqual(source.encode("utf-8"), MODULE.base64.b64decode(encoded))
        self.assertEqual(["301", "401", "300", "400"], argv[3:])
        wrong = {**self.identity["gdb_process"], "start_token": "999"}
        with self.assertRaisesRegex(ValueError, "identity"):
            MODULE.interrupt_gdb_command(
                wrong,
                self.identity["process"],
                expected_gdb=self.identity["gdb_process"],
            )

    def test_diagnostic_capture_status_requires_every_observation_boundary(self):
        evidence = {
            "load_ready_valid": True,
            "load_bracket_verified": True,
            "hit_ready_valid": True,
            "hit_bracket_verified": True,
            "post_bracket_verified": True,
            "post_pixel_analysis": {"status": "PASS", "changed_pixels": 0},
            "present_success_delta": 1,
            "kernel_fault_delta": 0,
            "after_continue_event": "AFTER_CONTINUE_STOP_OR_EXIT",
        }
        self.assertTrue(MODULE.diagnostic_capture_evidence_complete(**evidence))
        for key, invalid in (
            ("post_bracket_verified", False),
            ("post_pixel_analysis", {"status": "UNKNOWN"}),
            ("present_success_delta", None),
            ("present_success_delta", 0),
            ("kernel_fault_delta", None),
        ):
            with self.subTest(key=key):
                candidate = {**evidence, key: invalid}
                self.assertFalse(MODULE.diagnostic_capture_evidence_complete(**candidate))

    def test_post_frame_analysis_requires_valid_pixels_and_exact_final_frame_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "qemu"
            run_dir.mkdir()
            controller = MODULE.CaptureController(
                run_dir, run_dir / "qmp.sock", repo_root=root
            )
            first = run_dir / "flr0416-0001-qmp-post-frame-0000.ppm"
            last = run_dir / "flr0416-0001-qmp-post-frame-0007.ppm"
            first.write_bytes(b"reference-frame")
            last.write_bytes(b"sample-frame")
            response = {
                "width": 1280,
                "height": 800,
                "comparison": "reference",
                "changed_pixels": 0,
                "changed_ratio": 0.0,
                "ppm_sha256": hashlib.sha256(last.read_bytes()).hexdigest(),
            }
            completed = subprocess.CompletedProcess([], 0, json.dumps(response), "")
            with mock.patch.object(MODULE.subprocess, "run", return_value=completed):
                result = controller._analyze_post_frames({first.name: first.read_bytes(), last.name: last.read_bytes()})
            self.assertEqual("PASS", result["status"])
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), result["reference_frame_sha256"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "qemu"
            run_dir.mkdir()
            controller = MODULE.CaptureController(
                run_dir, run_dir / "qmp.sock", repo_root=root
            )
            first = run_dir / "flr0416-0001-qmp-post-frame-0000.ppm"
            last = run_dir / "flr0416-0001-qmp-post-frame-0007.ppm"
            first.write_bytes(b"reference-frame")
            last.write_bytes(b"sample-frame")
            response = {
                "width": 1280,
                "height": 800,
                "comparison": "reference",
                "changed_pixels": 1,
                "changed_ratio": 0.0,
                "ppm_sha256": "0" * 64,
            }
            completed = subprocess.CompletedProcess([], 0, json.dumps(response), "")
            with mock.patch.object(MODULE.subprocess, "run", return_value=completed):
                result = controller._analyze_post_frames({first.name: first.read_bytes(), last.name: last.read_bytes()})
            self.assertEqual("UNKNOWN", result["status"])

    def test_teardown_error_cannot_leave_diagnostic_success_verdict(self):
        status, code = MODULE.final_capture_status(
            "DIAGNOSTIC_CAPTURE_PASS", ["qmp-quit=FAIL"], True
        )
        self.assertEqual("DIAGNOSTIC_CAPTURE_INCOMPLETE", status)
        self.assertEqual(1, code)
        status, code = MODULE.final_capture_status(
            "DIAGNOSTIC_CAPTURE_PASS", [], False
        )
        self.assertEqual("DIAGNOSTIC_CAPTURE_INCOMPLETE", status)
        self.assertEqual(1, code)

    def test_main_executes_controller_with_explicit_roles(self):
        observed = {}

        class DummyController:
            def __init__(self, run_dir, qmp, **kwargs):
                observed.update(run_dir=run_dir, qmp=qmp, **kwargs)

            def run(self):
                return 17

        with mock.patch.object(MODULE, "CaptureController", DummyController):
            result = MODULE.main(
                [
                    "--run-dir", "/evidence/flr0416-0001/qemu",
                    "--qmp", "/evidence/flr0416-0001/qemu/qmp-0416.sock",
                    "--repo-root", "/repo",
                    "--marker-timeout-seconds", "90",
                    "--post-release-seconds", "11",
                ]
            )

        self.assertEqual(17, result)
        self.assertEqual(90, observed["marker_timeout_seconds"])
        self.assertEqual(11, observed["post_release_seconds"])

    def test_ack_collection_deadline_caps_blocking_operations(self):
        controller = MODULE.CaptureController.__new__(MODULE.CaptureController)
        controller.marker_timeout_seconds = MODULE.ACK_COLLECTION_SECONDS
        controller._ack_deadline = MODULE.time.monotonic() + 2
        controller._abort_deadline = None
        self.assertLessEqual(controller._bounded_timeout(40), 2)

        controller._ack_deadline = MODULE.time.monotonic() - 1
        with self.assertRaisesRegex(TimeoutError, "deadline expired"):
            controller._bounded_timeout(40)
        self.assertEqual(
            25,
            controller._bounded_timeout(25, respect_deadline=False),
        )

    def test_abort_publication_has_one_bounded_grace_window(self):
        controller = MODULE.CaptureController.__new__(MODULE.CaptureController)
        controller._ack_deadline = None
        controller._abort_deadline = None
        controller._begin_abort_window()
        self.assertLessEqual(
            controller._bounded_timeout(40, respect_deadline=False),
            MODULE.ABORT_GRACE_SECONDS,
        )
        self.assertLessEqual(
            controller._bounded_timeout(40), MODULE.ABORT_GRACE_SECONDS
        )
        controller._abort_deadline = MODULE.time.monotonic() - 1
        with self.assertRaisesRegex(TimeoutError, "abort publication deadline"):
            controller._bounded_timeout(25, respect_deadline=False)
        controller._end_abort_window()

    def test_stage_failure_publishes_abort_if_identity_is_known(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            repo_root = Path(__file__).parents[1]
            controller = MODULE.CaptureController(
                run_dir, run_dir / "qmp.sock", repo_root=repo_root
            )
            controller.identity = self.identity

            for stage, method_name in (
                ("load", "_run_load_stage"),
                ("hit", "_run_hit_stage"),
            ):
                with self.subTest(stage=stage):
                    result = {"stages": {}}
                    with mock.patch.object(
                        controller,
                        "_wait_marker",
                        side_effect=RuntimeError("stage collection failed"),
                    ), mock.patch.object(
                        controller,
                        "_publish_abort",
                        side_effect=lambda abort_stage, reason: self.assertEqual(
                            (stage, "controller_stage_error"),
                            (abort_stage, reason),
                        ),
                    ) as publish_abort:
                        with self.assertRaisesRegex(
                            RuntimeError, "stage collection failed"
                        ):
                            getattr(controller, method_name)(result)
                    publish_abort.assert_called_once()
                    self.assertIsNone(controller._ack_deadline)
                    self.assertIsNone(controller._abort_deadline)
                    self.assertEqual(
                        {
                            "publication": "PUBLISHED",
                            "guest_acceptance": "UNKNOWN",
                        },
                        result["stages"][stage + "_failure_abort"],
                    )

    def test_release_ack_failure_is_recorded_as_unknown_before_exact_teardown(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            repo_root = Path(__file__).parents[1]
            controller = MODULE.CaptureController(
                run_dir, run_dir / "qmp.sock", repo_root=repo_root
            )
            controller.identity = self.identity
            result = {"stages": {}}
            with mock.patch.object(controller, "_wait_marker"), mock.patch.object(
                controller, "_load_identity", return_value=b"armed"
            ), mock.patch.object(
                controller, "_fetch_guest", return_value=b"load-ready"
            ), mock.patch.object(
                MODULE, "validate_stage_ready", return_value=True
            ), mock.patch.object(
                controller, "_capture_stage", return_value=({}, True, {}, {})
            ), mock.patch.object(
                MODULE, "build_manifest", return_value=b"manifest"
            ), mock.patch.object(
                controller, "_save_once"
            ), mock.patch.object(
                controller, "_publish_release", return_value=b"release"
            ), mock.patch.object(
                controller,
                "_wait_release_acceptance",
                side_effect=RuntimeError("acceptance fetch failed"),
            ), mock.patch.object(controller, "_publish_abort") as publish_abort:
                with self.assertRaisesRegex(
                    RuntimeError, "acceptance fetch failed"
                ):
                    controller._run_load_stage(result)

            load = result["stages"]["load"]
            self.assertEqual("PUBLISHED", load["release_publication"])
            self.assertEqual("UNKNOWN", load["guest_release_acceptance"])
            self.assertEqual(
                "UNKNOWN_IF_RELEASE_PUBLISHED",
                load["inferior_held_after_error"],
            )
            self.assertEqual(
                {
                    "publication": "PUBLISHED",
                    "guest_acceptance": "UNKNOWN",
                },
                result["stages"]["load_failure_abort"],
            )
            publish_abort.assert_called_once_with(
                "load", "controller_stage_error"
            )
            self.assertNotIn("hit", controller._prepared_ack_deadlines)

    def test_ack_window_is_one_shot_and_resets(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            repo_root = Path(__file__).parents[1]
            controller = MODULE.CaptureController(
                run_dir,
                run_dir / "qmp.sock",
                repo_root=repo_root,
                marker_timeout_seconds=30,
            )
            controller._begin_ack_window("load")
            first_deadline = controller._ack_deadline
            with self.assertRaisesRegex(RuntimeError, "already active"):
                controller._begin_ack_window("load")
            controller._end_ack_window()
            self.assertIsNone(controller._ack_deadline)
            controller._begin_ack_window("load")
            self.assertGreater(controller._ack_deadline, first_deadline)
            controller._end_ack_window()

    def test_hit_window_is_anchored_before_load_release_and_carried_forward(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            controller = MODULE.CaptureController(
                run_dir,
                run_dir / "qmp.sock",
                repo_root=Path(__file__).parents[1],
                marker_timeout_seconds=30,
            )
            controller._begin_ack_window("load")
            controller._prepare_ack_window("hit")
            hit_deadline = controller._prepared_ack_deadlines["hit"]
            controller._end_ack_window()
            adopted = controller._begin_ack_window("hit")
            self.assertEqual(hit_deadline, adopted)
            controller._end_ack_window()

        source = SCRIPT.read_text(encoding="utf-8")
        self.assertLess(source.index('self._begin_ack_window("load")'), source.index("self._launch_gdb()"))
        self.assertLess(source.index('self._prepare_ack_window("hit")'), source.index('self._publish_release("load", load_manifest)'))


if __name__ == "__main__":
    unittest.main()
