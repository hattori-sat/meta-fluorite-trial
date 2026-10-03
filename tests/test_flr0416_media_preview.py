import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from unittest import mock
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts/export_flr0416_media_preview.py"
SPEC = importlib.util.spec_from_file_location("flr0416_media_preview", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FLR0416MediaPreviewTests(unittest.TestCase):
    def _controller_final(self, **overrides):
        identity = {
            "guest_boot_id": "boot-abc",
            "process": {"pid": 300, "uid": 1001, "start_token": "400"},
            "gdb_process": {"pid": 301, "uid": 1001, "start_token": "401"},
        }
        record = {
            "event": "FLR0416_CONTROLLER_FINAL",
            "run_id": MODULE.RUN_ID,
            "image": "FLR-0410-0001",
            "status": "DIAGNOSTIC_CAPTURE_PASS",
            "product_acceptance": "NOT_CLAIMED",
            "qemu_build": "NOT_RUN",
            "stages": {"load_ready": {"identity": identity}},
            "teardown_verified": True,
            "teardown_errors": [],
            "qemu_process_gone": True,
            "postflight_verified": True,
            "qmp_quit_status": "PASS",
            "qmp_socket_absent": True,
            "completed_host_wall_ns": 123456789,
            "qemu_host_identity": {"pid": 200, "start_token": "300"},
            "errors": [],
            "teardown_warnings": [],
        }
        record.update(overrides)
        return record

    def _archive(self, files):
        manifest = {
            "event": "FLR0416_MEDIA_EXPORT",
            "run_id": MODULE.RUN_ID,
            "files": {
                name: {"size": len(content), "sha256": hashlib.sha256(content).hexdigest()}
                for name, content in files.items()
            },
        }
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w") as archive:
            for name, content in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
            content = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
            info = tarfile.TarInfo(MODULE.EXPORT_MANIFEST)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
        return output.getvalue()

    def _capture_records(self, stage):
        still = MODULE.RUN_ID + "-qmp-" + stage + "-still.ppm"
        names = [still] + [
            MODULE.RUN_ID + "-qmp-" + stage + "-frame-%04d.ppm" % index
            for index in range(MODULE.FRAME_COUNT)
        ]
        files = {}
        records = []
        for index, name in enumerate(names):
            content = ("frame-%s" % index).encode()
            files[name] = content
            start = 1_000_000_000 + index * 250_000_000
            records.append(
                {
                    "event": "QMP_CAPTURE",
                    "name": name,
                    "status": "PASS",
                    "format": "P6-PPM",
                    "width": 1280,
                    "height": 800,
                    "size": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "host_wall_ns": [start, start + 100],
                    "host_monotonic_ns": [start, start + 100],
                }
            )
        capture = {
            "event": "QMP_CAPTURE_SET",
            "run_id": MODULE.RUN_ID,
            "stage": stage,
            "still_and_frames": records,
            "video_status": "PENDING_MAC_PREVIEW",
        }
        report_name = MODULE.RUN_ID + "-qmp-" + stage + "-capture.json"
        report_bytes = json.dumps(capture).encode()
        files[report_name] = report_bytes
        hashes = {record["name"]: record["sha256"] for record in records}
        hashes[report_name] = hashlib.sha256(report_bytes).hexdigest()
        process = {"pid": 300, "uid": 1001, "start_token": "400"}
        gdb_process = {"pid": 301, "uid": 1001, "start_token": "401"}

        def sample(guest_monotonic_ns):
            return {
                "event": "GUEST_RUNTIME_SNAPSHOT",
                "run_id": MODULE.RUN_ID,
                "stage": stage,
                "guest_boot_id": "boot-abc",
                "process": process,
                "gdb_process": gdb_process,
                "guest_wall_ns": guest_monotonic_ns + 100,
                "guest_monotonic_ns": guest_monotonic_ns,
                "process_observation": {
                    "state": "LIVE",
                    "matches": True,
                    "actual": {
                        **process,
                        "comm": "flutter-auto",
                        "state": "T" if stage == "hit" else "S",
                    },
                },
                "gdb_observation": {
                    "state": "LIVE",
                    "matches": True,
                    "actual": {**gdb_process, "comm": "gdb", "state": "S"},
                },
                "present": {"begin": 5, "return": 4, "success": 4},
                "kernel": {"baseline": 0, "current": 0, "delta": 0},
            }

        identity = {
            "guest_boot_id": "boot-abc",
            "process": process,
            "gdb_process": gdb_process,
        }
        bracket = MODULE.capture.build_bracket(
            stage,
            identity,
            sample(1),
            sample(2),
            900_000_000,
            4_000_000_000,
            hashes,
            900_000_000,
            4_000_000_000,
        )
        files[MODULE.RUN_ID + "-" + stage + "-bracket.json"] = bracket
        return files

    def test_export_allowlist_contains_only_qmp_screen_media_and_metadata(self):
        names = MODULE.allowed_media_names()
        self.assertIn(MODULE.CONTROLLER_FINAL, names)
        self.assertNotIn("FLR0416-controller-result.json", names)
        self.assertIn("flr0421-0001-qmp-hit-frame-0007.ppm", names)
        self.assertIn("flr0421-0001-qmp-post-frame-0000.ppm", names)
        self.assertFalse(any("rootfs" in name or "kernel" in name or "log" in name for name in names))
        self.assertEqual(8, sum("qmp-hit-frame-" in name for name in names))

    def test_media_archive_hash_manifest_is_verified_and_unexpected_files_fail(self):
        frame = "flr0421-0001-qmp-hit-frame-0000.ppm"
        payloads, manifest = MODULE.validate_media_archive(self._archive({frame: b"ppm"}))
        self.assertEqual(b"ppm", payloads[frame])
        self.assertEqual(hashlib.sha256(b"ppm").hexdigest(), manifest["files"][frame]["sha256"])
        with self.assertRaisesRegex(ValueError, "unsafe or unexpected"):
            MODULE.validate_media_archive(self._archive({"unrelated.txt": b"not screen media"}))

    def test_capture_set_requires_all_exact_frames_hashes_timing_and_bracket(self):
        files = self._capture_records("hit")
        with mock.patch.object(MODULE, "parse_p6_ppm", return_value=(1280, 800)):
            records = MODULE.validate_capture_set(files, "hit")
            bracket = MODULE.validate_bracket_record(
                files, "hit", records, self._controller_final()
            )
        self.assertEqual(9, len(records))
        self.assertIsNotNone(bracket)
        last = "flr0421-0001-qmp-hit-frame-0007.ppm"
        files[last] = b"changed"
        with mock.patch.object(MODULE, "parse_p6_ppm", return_value=(1280, 800)):
            with self.assertRaisesRegex(ValueError, "metadata/hash mismatch"):
                MODULE.validate_capture_set(files, "hit")

    def test_post_bracket_round_trip_uses_the_shared_running_state_contract(self):
        files = self._capture_records("post")
        bracket_name = MODULE.RUN_ID + "-post-bracket.json"
        bracket = json.loads(files[bracket_name])
        with mock.patch.object(MODULE, "parse_p6_ppm", return_value=(1280, 800)):
            records = MODULE.validate_capture_set(files, "post")
            self.assertIsNotNone(
                MODULE.validate_bracket_record(
                    files, "post", records, self._controller_final()
                )
            )

        bracket["guest_before"]["process_observation"]["actual"]["state"] = "T"
        files[bracket_name] = json.dumps(bracket).encode()
        with mock.patch.object(MODULE, "parse_p6_ppm", return_value=(1280, 800)):
            records = MODULE.validate_capture_set(files, "post")
            with self.assertRaisesRegex(ValueError, "post-release.*stopped"):
                MODULE.validate_bracket_record(
                    files, "post", records, self._controller_final()
                )

    def test_incomplete_bracket_keeps_preview_visible_but_correlation_unknown(self):
        files = self._capture_records("hit")
        bracket_name = MODULE.RUN_ID + "-hit-bracket.json"
        bracket = json.loads(files[bracket_name])
        bracket.pop("verified")
        files[bracket_name] = json.dumps(bracket).encode()
        with (
            mock.patch.object(MODULE, "parse_p6_ppm", return_value=(1280, 800)),
            mock.patch.object(MODULE, "encode_png", return_value=b"png-preview"),
            mock.patch.object(MODULE, "encode_mp4", return_value=b"mp4-preview"),
        ):
            outputs, stages = MODULE.build_previews(
                files, "ffmpeg", final_record=self._controller_final()
            )
        self.assertIn("FLR-0416-hit.mp4", outputs)
        self.assertEqual("UNVERIFIED_BRACKET", stages["hit"]["video_status"])
        self.assertEqual("UNKNOWN", stages["hit"]["correlation_status"])
        self.assertFalse(stages["hit"]["bracket_verified"])

    def test_bracket_requires_final_identity_and_capture_report_hash_match(self):
        files = self._capture_records("hit")
        final = self._controller_final(
            stages={
                "load_ready": {
                    "identity": {
                        "guest_boot_id": "boot-abc",
                        "process": {"pid": 999, "uid": 1001, "start_token": "400"},
                        "gdb_process": {"pid": 301, "uid": 1001, "start_token": "401"},
                    }
                }
            }
        )
        with mock.patch.object(MODULE, "parse_p6_ppm", return_value=(1280, 800)):
            records = MODULE.validate_capture_set(files, "hit")
            with self.assertRaisesRegex(ValueError, "load-ready baseline"):
                MODULE.validate_bracket_record(files, "hit", records, final)

            capture_name = MODULE.RUN_ID + "-qmp-hit-capture.json"
            files[capture_name] += b" "
            records = MODULE.validate_capture_set(files, "hit")
            with self.assertRaisesRegex(ValueError, "report hash mismatch"):
                MODULE.validate_bracket_record(
                    files, "hit", records, self._controller_final()
                )

    def test_controller_final_requires_verified_teardown_but_preserves_capture_failure(self):
        failure = self._controller_final(
            status="DIAGNOSTIC_CAPTURE_FAIL",
            errors=["target-boundary-unavailable"],
        )
        record = MODULE.validate_controller_final(
            {MODULE.CONTROLLER_FINAL: json.dumps(failure).encode()}
        )
        self.assertEqual("DIAGNOSTIC_CAPTURE_FAIL", record["status"])
        for override in (
            {"teardown_verified": False},
            {"qemu_process_gone": False},
            {"postflight_verified": False},
            {"qmp_socket_absent": False},
            {"teardown_errors": ["postflight=FAIL"]},
        ):
            with self.subTest(override=override):
                invalid = self._controller_final(**override)
                with self.assertRaisesRegex(ValueError, "clean exact teardown"):
                    MODULE.validate_controller_final(
                        {MODULE.CONTROLLER_FINAL: json.dumps(invalid).encode()}
                    )

    def test_remote_archive_program_streams_only_exact_allowlisted_media(self):
        frame = "flr0421-0001-qmp-hit-frame-0000.ppm"
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / frame).write_bytes(b"verified frame")
            (Path(directory) / MODULE.CONTROLLER_FINAL).write_text(
                json.dumps(self._controller_final()), encoding="utf-8"
            )
            (Path(directory) / "unrelated.log").write_text("must not transfer", encoding="utf-8")
            names = json.dumps(sorted(MODULE.allowed_media_names()))
            result = subprocess.run(
                [sys.executable, "-c", MODULE.remote_archive_program(), directory, names],
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr.decode(errors="replace"))
            payloads, _ = MODULE.validate_media_archive(result.stdout)
            self.assertEqual({frame, MODULE.CONTROLLER_FINAL}, set(payloads))
            denied = subprocess.run(
                [sys.executable, "-c", MODULE.remote_archive_program(), directory, '["unrelated.log"]'],
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertNotEqual(0, denied.returncode)

            invalid_final = self._controller_final(teardown_verified=False)
            (Path(directory) / MODULE.CONTROLLER_FINAL).write_text(
                json.dumps(invalid_final), encoding="utf-8"
            )
            rejected = subprocess.run(
                [sys.executable, "-c", MODULE.remote_archive_program(), directory, names],
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn(b"completed teardown", rejected.stderr)

    def test_preview_labels_playback_rate_as_nominal_not_realtime(self):
        files = self._capture_records("hit")
        report = json.loads(files["flr0421-0001-qmp-hit-capture.json"])
        still = report["still_and_frames"][0]
        files[still["name"] + ".capture.json"] = json.dumps(still).encode()
        with (
            mock.patch.object(MODULE, "parse_p6_ppm", return_value=(1280, 800)),
            mock.patch.object(MODULE, "encode_png", return_value=b"png-preview"),
            mock.patch.object(MODULE, "encode_mp4", return_value=b"mp4-preview"),
        ):
            outputs, stages = MODULE.build_previews(
                files, "ffmpeg", final_record=self._controller_final()
            )
        self.assertEqual("PASS", stages["hit"]["video_status"])
        self.assertFalse(stages["hit"]["real_time_video"])
        self.assertEqual(4, stages["hit"]["nominal_playback_fps"])
        self.assertEqual([250.0] * 7, stages["hit"]["capture_interval_ms"])
        self.assertIn("FLR-0416-hit.mp4", outputs)

    def test_incomplete_capture_cannot_become_mp4(self):
        with self.assertRaisesRegex(ValueError, "exactly eight"):
            MODULE.encode_mp4("ffmpeg", [b"P6"] * 7, runner=lambda *args, **kwargs: None)

    def test_local_ffmpeg_creates_playable_format_png_and_fragmented_mp4(self):
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            self.skipTest("local Mac FFmpeg is not installed")
        row = bytes((40, 120, 220)) * 16
        ppm = b"P6\n16 16\n255\n" + row * 16
        with tempfile.TemporaryDirectory() as directory:
            png = MODULE.encode_png(ffmpeg, ppm)
            mp4 = MODULE.encode_mp4(ffmpeg, [ppm] * 8)
            self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertIn(b"ftyp", mp4[:64])
            preview = Path(directory) / "preview.mp4"
            preview.write_bytes(mp4)
            probe = shutil.which("ffprobe")
            if probe:
                result = subprocess.run(
                    [probe, "-v", "error", "-show_entries", "format=format_name", "-of", "default=nw=1:nk=1", str(preview)],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("mp4", result.stdout)


if __name__ == "__main__":
    unittest.main()
