#!/usr/bin/env python3
"""Fetch only FLR-0416 QMP screen media and make local PNG/MP4 previews."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import flr0416_live_capture as capture  # noqa: E402
from flr0416_live_capture import parse_p6_ppm  # noqa: E402

RUN_ID = "flr0416-0001"
EXPORT_MANIFEST = ".flr0416-media-export.json"
CONTROLLER_FINAL = "FLR0416-controller-final.json"
MAX_MEMBER_BYTES = 4_000_000
MAX_ARCHIVE_BYTES = 100_000_000
FRAME_COUNT = 8
PLAYBACK_FPS = 4


def allowed_media_names():
    names = {CONTROLLER_FINAL}
    for stage in ("pre-launch", "load", "hit", "post"):
        still = RUN_ID + "-qmp-" + stage + "-still.ppm"
        names.add(still)
        names.add(still + ".capture.json")
        if stage != "pre-launch":
            names.add(RUN_ID + "-" + stage + "-bracket.json")
        if stage in ("load", "hit", "post"):
            names.add(RUN_ID + "-qmp-" + stage + "-capture.json")
        if stage in ("hit", "post"):
            names.update(
                RUN_ID + "-qmp-" + stage + "-frame-%04d.ppm" % index
                for index in range(FRAME_COUNT)
            )
    return frozenset(names)


def remote_archive_program():
    return r'''import hashlib, io, json, os, stat, sys, tarfile
root = os.path.realpath(sys.argv[1])
names = json.loads(sys.argv[2])
controller_final = "FLR0416-controller-final.json"
expected = {controller_final}
for stage in ("pre-launch", "load", "hit", "post"):
    still = "flr0416-0001-qmp-" + stage + "-still.ppm"
    expected.add(still)
    expected.add(still + ".capture.json")
    if stage != "pre-launch":
        expected.add("flr0416-0001-" + stage + "-bracket.json")
    if stage in ("load", "hit", "post"):
        expected.add("flr0416-0001-qmp-" + stage + "-capture.json")
    if stage in ("hit", "post"):
        expected.update(
            "flr0416-0001-qmp-" + stage + "-frame-%04d.ppm" % index
            for index in range(8)
        )
if not isinstance(names, list) or len(names) != len(set(names)) or set(names) != expected:
    raise SystemExit("requested media names do not match the fixed allowlist")
try:
    final_path = os.path.join(root, controller_final)
    final_info = os.lstat(final_path)
    if not stat.S_ISREG(final_info.st_mode) or final_info.st_size > 4000000:
        raise SystemExit("controller final record has an unexpected type or size")
    with open(final_path, "rb") as source:
        final = json.loads(source.read(4000001).decode("utf-8"))
except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
    raise SystemExit("controller final record is missing or invalid") from error
if (
    not isinstance(final, dict)
    or final.get("event") != "FLR0416_CONTROLLER_FINAL"
    or final.get("run_id") != "flr0416-0001"
    or final.get("image") != "FLR-0410-0001"
    or final.get("status") not in (
        "DIAGNOSTIC_CAPTURE_PASS",
        "DIAGNOSTIC_CAPTURE_FAIL",
        "DIAGNOSTIC_CAPTURE_INCOMPLETE",
        "LOAD_STAGE_ABORT_REQUESTED",
        "HIT_STAGE_ABORT_REQUESTED",
    )
    or final.get("product_acceptance") != "NOT_CLAIMED"
    or final.get("teardown_verified") is not True
    or final.get("teardown_errors") != []
    or final.get("qemu_process_gone") is not True
    or final.get("postflight_verified") is not True
    or final.get("qmp_quit_status") not in (
        "PASS",
        "ALREADY_EXITED",
        "FAILED_BUT_GONE",
        "EXITED_DURING_TEARDOWN",
    )
    or final.get("qmp_socket_absent") is not True
    or type(final.get("completed_host_wall_ns")) is not int
    or final.get("completed_host_wall_ns") <= 0
    or not isinstance(final.get("qemu_host_identity"), dict)
    or type(final["qemu_host_identity"].get("pid")) is not int
    or final["qemu_host_identity"]["pid"] <= 1
    or not isinstance(final["qemu_host_identity"].get("start_token"), str)
    or not final["qemu_host_identity"]["start_token"].isdigit()
    or not isinstance(final.get("stages"), dict)
    or final.get("qemu_build") != "NOT_RUN"
    or not isinstance(final.get("errors"), list)
    or any(not isinstance(error, str) for error in final["errors"])
):
    raise SystemExit("QMP media export requires identity-matched completed teardown")
manifest = {}
with tarfile.open(fileobj=sys.stdout.buffer, mode="w|") as archive:
    for name in names:
        if not isinstance(name, str) or "/" in name or name in ("", ".", ".."):
            raise SystemExit("invalid allowlisted name")
        path = os.path.join(root, name)
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_size > 4000000:
            raise SystemExit("unexpected media-file type or size")
        with open(path, "rb") as source:
            content = source.read(4000001)
        if len(content) != info.st_size or len(content) > 4000000:
            raise SystemExit("media file changed or exceeded size bound")
        manifest[name] = {"size": len(content), "sha256": hashlib.sha256(content).hexdigest()}
        member = tarfile.TarInfo(name)
        member.size = len(content)
        member.mode = 0o600
        archive.addfile(member, io.BytesIO(content))
    content = json.dumps({"event":"FLR0416_MEDIA_EXPORT", "run_id":"flr0416-0001", "files":manifest}, sort_keys=True, separators=(",", ":")).encode()
    member = tarfile.TarInfo(".flr0416-media-export.json")
    member.size = len(content)
    member.mode = 0o600
    archive.addfile(member, io.BytesIO(content))
'''


def remote_run_directory(evidence_root):
    if not isinstance(evidence_root, str) or not evidence_root.startswith("/"):
        raise ValueError("BUILD_EVIDENCE must be an absolute role path")
    if "\n" in evidence_root or "\0" in evidence_root:
        raise ValueError("BUILD_EVIDENCE contains an invalid character")
    return evidence_root.rstrip("/") + "/" + RUN_ID + "/qemu"


def fetch_media_archive(host, evidence_root, runner=subprocess.run):
    if not isinstance(host, str) or re.fullmatch(r"[A-Za-z0-9_.-]+", host) is None:
        raise ValueError("BUILD_HOST must be a configured SSH role or host")
    run_dir = remote_run_directory(evidence_root)
    names = sorted(allowed_media_names())
    remote_command = "python3 - " + shlex.quote(run_dir) + " " + shlex.quote(
        json.dumps(names, separators=(",", ":"))
    )
    result = runner(
        ["ssh", "-T", "-o", "BatchMode=yes", host, remote_command],
        input=remote_archive_program().encode("utf-8"),
        check=False,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace")[-1000:]
        raise RuntimeError("Mini media export failed: " + detail.strip())
    if len(result.stdout) > MAX_ARCHIVE_BYTES:
        raise RuntimeError("Mini media export exceeded the archive size bound")
    return result.stdout


def validate_media_archive(archive_bytes):
    if not isinstance(archive_bytes, bytes) or len(archive_bytes) > MAX_ARCHIVE_BYTES:
        raise ValueError("media archive is invalid or too large")
    allowed = allowed_media_names()
    payloads = {}
    total = 0
    try:
        archive = tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*")
    except (tarfile.TarError, OSError) as error:
        raise ValueError("media archive cannot be opened") from error
    with archive:
        for member in archive:
            if member.name == EXPORT_MANIFEST:
                if EXPORT_MANIFEST in payloads or not member.isfile():
                    raise ValueError("media export manifest is invalid")
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError("media export manifest is unreadable")
                payloads[EXPORT_MANIFEST] = stream.read(64_001)
                if len(payloads[EXPORT_MANIFEST]) > 64_000:
                    raise ValueError("media export manifest is too large")
                continue
            if (
                member.name not in allowed
                or member.name in payloads
                or not member.isfile()
                or member.size < 0
                or member.size > MAX_MEMBER_BYTES
            ):
                raise ValueError("media archive contains an unsafe or unexpected member")
            total += member.size
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("media archive members exceed the total size bound")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("media archive member is unreadable")
            content = stream.read(MAX_MEMBER_BYTES + 1)
            if len(content) != member.size:
                raise ValueError("media archive member size is inconsistent")
            payloads[member.name] = content
    raw_manifest = payloads.pop(EXPORT_MANIFEST, None)
    if raw_manifest is None:
        raise ValueError("media export manifest is missing")
    try:
        manifest = json.loads(raw_manifest.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("media export manifest is invalid JSON") from error
    if (
        not isinstance(manifest, dict)
        or manifest.get("event") != "FLR0416_MEDIA_EXPORT"
        or manifest.get("run_id") != RUN_ID
        or not isinstance(manifest.get("files"), dict)
        or set(manifest["files"]) != set(payloads)
    ):
        raise ValueError("media export manifest does not match its members")
    for name, content in payloads.items():
        record = manifest["files"].get(name)
        if (
            not isinstance(record, dict)
            or record.get("size") != len(content)
            or record.get("sha256") != hashlib.sha256(content).hexdigest()
        ):
            raise ValueError("media member hash/size mismatch: " + name)
    return payloads, manifest


def _json_record(payloads, name, required=True):
    content = payloads.get(name)
    if content is None:
        if required:
            raise ValueError("required media metadata is missing: " + name)
        return None
    try:
        record = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("media metadata is invalid JSON: " + name) from error
    if not isinstance(record, dict):
        raise ValueError("media metadata is not an object: " + name)
    return record


def _validate_ppm(payloads, name, record):
    content = payloads.get(name)
    if content is None:
        raise ValueError("captured screen frame is missing: " + name)
    if (
        not isinstance(record, dict)
        or record.get("event") != "QMP_CAPTURE"
        or record.get("name") != name
        or record.get("status") != "PASS"
        or record.get("format") != "P6-PPM"
        or record.get("width") != 1280
        or record.get("height") != 800
        or record.get("size") != len(content)
        or record.get("sha256") != hashlib.sha256(content).hexdigest()
    ):
        raise ValueError("screen frame metadata/hash mismatch: " + name)
    width, height = parse_p6_ppm(content)
    if width != 1280 or height != 800:
        raise ValueError("screen frame is not full-screen 1280x800: " + name)
    for key in ("host_wall_ns", "host_monotonic_ns"):
        interval = record.get(key)
        if (
            not isinstance(interval, list)
            or len(interval) != 2
            or any(not isinstance(value, int) or value < 0 for value in interval)
            or interval[1] < interval[0]
        ):
            raise ValueError("screen frame capture interval is invalid: " + name)
    return record


def validate_capture_set(payloads, stage):
    if stage not in ("hit", "post"):
        raise ValueError("video capture stage must be hit or post")
    report_name = RUN_ID + "-qmp-" + stage + "-capture.json"
    report = _json_record(payloads, report_name)
    still = RUN_ID + "-qmp-" + stage + "-still.ppm"
    expected_names = [still] + [
        RUN_ID + "-qmp-" + stage + "-frame-%04d.ppm" % index
        for index in range(FRAME_COUNT)
    ]
    if (
        report.get("event") != "QMP_CAPTURE_SET"
        or report.get("run_id") != RUN_ID
        or report.get("stage") != stage
        or report.get("video_status") != "PENDING_MAC_PREVIEW"
        or not isinstance(report.get("still_and_frames"), list)
        or [item.get("name") if isinstance(item, dict) else None for item in report["still_and_frames"]]
        != expected_names
    ):
        raise ValueError("capture set does not describe the complete expected frame sequence")
    records = [
        _validate_ppm(payloads, name, record)
        for name, record in zip(expected_names, report["still_and_frames"])
    ]
    return records


def validate_bracket_record(payloads, stage, records, final_record):
    bracket_name = RUN_ID + "-" + stage + "-bracket.json"
    bracket = _json_record(payloads, bracket_name)
    if (
        bracket.get("event") != "QMP_CAPTURE_BRACKET"
        or bracket.get("run_id") != RUN_ID
        or bracket.get("stage") != stage
        or bracket.get("verified") is not True
        or bracket.get("clock_origins_comparable") is not False
        or "error" in bracket
    ):
        raise ValueError("capture bracket is absent or not explicitly verified")
    identity = {
        "guest_boot_id": bracket.get("guest_boot_id"),
        "process": bracket.get("process"),
        "gdb_process": bracket.get("gdb_process"),
    }
    if not isinstance(identity["guest_boot_id"], str) or not identity["guest_boot_id"]:
        raise ValueError("capture bracket guest identity is missing")
    for key in ("process", "gdb_process"):
        process = identity[key]
        if (
            not isinstance(process, dict)
            or process.get("uid") != 1001
            or not isinstance(process.get("pid"), int)
            or process["pid"] <= 0
            or re.fullmatch(r"[0-9]+", str(process.get("start_token", ""))) is None
        ):
            raise ValueError("capture bracket process identity is invalid")
    stages = final_record.get("stages") if isinstance(final_record, dict) else None
    load_ready = stages.get("load_ready") if isinstance(stages, dict) else None
    load_identity = load_ready.get("identity") if isinstance(load_ready, dict) else None
    if (
        not isinstance(load_identity, dict)
        or any(load_identity.get(key) != value for key, value in identity.items())
    ):
        raise ValueError("capture bracket identity has no matching load-ready baseline")
    host_intervals = {}
    for key in ("host_request_monotonic_ns", "host_request_wall_ns"):
        interval = bracket.get(key)
        if (
            not isinstance(interval, list)
            or len(interval) != 2
            or any(not isinstance(value, int) or value < 0 for value in interval)
            or interval[1] < interval[0]
        ):
            raise ValueError("capture bracket host interval is invalid")
        host_intervals[key] = interval
    hashes = bracket.get("capture_sha256")
    if not isinstance(hashes, dict):
        raise ValueError("capture bracket frame hashes are missing")
    report_name = RUN_ID + "-qmp-" + stage + "-capture.json"
    report_bytes = payloads.get(report_name)
    if report_bytes is None or hashes.get(report_name) != hashlib.sha256(report_bytes).hexdigest():
        raise ValueError("capture bracket report hash mismatch")
    for record in records:
        if hashes.get(record["name"]) != record["sha256"]:
            raise ValueError("capture bracket frame hash mismatch")
        for record_key, bracket_key in (
            ("host_monotonic_ns", "host_request_monotonic_ns"),
            ("host_wall_ns", "host_request_wall_ns"),
        ):
            interval = record[record_key]
            outer = host_intervals[bracket_key]
            if interval[0] < outer[0] or interval[1] > outer[1]:
                raise ValueError("capture frame time falls outside the verified bracket")
    capture.validate_bracket_samples(
        stage,
        identity,
        bracket.get("guest_before"),
        bracket.get("guest_after"),
    )
    return bracket


def encode_png(ffmpeg, ppm_bytes, *, runner=subprocess.run):
    command = [
        ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "image2pipe",
        "-vcodec",
        "ppm",
        "-i",
        "-",
        "-frames:v",
        "1",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "pipe:1",
    ]
    result = runner(command, input=ppm_bytes, capture_output=True, timeout=45, check=False)
    if result.returncode != 0 or not result.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Mac FFmpeg failed to create a PNG preview")
    return result.stdout


def encode_mp4(ffmpeg, frame_bytes, *, runner=subprocess.run):
    if len(frame_bytes) != FRAME_COUNT:
        raise ValueError("MP4 preview requires exactly eight verified frames")
    command = [
        ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "image2pipe",
        "-vcodec",
        "ppm",
        "-framerate",
        str(PLAYBACK_FPS),
        "-i",
        "-",
        "-frames:v",
        str(FRAME_COUNT),
        "-an",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+frag_keyframe+empty_moov",
        "-f",
        "mp4",
        "pipe:1",
    ]
    result = runner(
        command,
        input=b"".join(frame_bytes),
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0 or b"ftyp" not in result.stdout[:64]:
        raise RuntimeError("Mac FFmpeg failed to create an MP4 preview")
    return result.stdout


def validate_controller_final(payloads):
    record = _json_record(payloads, CONTROLLER_FINAL)
    try:
        valid = (
            record.get("event") == "FLR0416_CONTROLLER_FINAL"
            and record.get("run_id") == RUN_ID
            and record.get("image") == "FLR-0410-0001"
            and record.get("status") in (
                "DIAGNOSTIC_CAPTURE_PASS",
                "DIAGNOSTIC_CAPTURE_FAIL",
                "DIAGNOSTIC_CAPTURE_INCOMPLETE",
                "LOAD_STAGE_ABORT_REQUESTED",
                "HIT_STAGE_ABORT_REQUESTED",
            )
            and record.get("product_acceptance") == "NOT_CLAIMED"
            and record.get("qemu_build") == "NOT_RUN"
            and record.get("teardown_verified") is True
            and record.get("teardown_errors") == []
            and record.get("qemu_process_gone") is True
            and record.get("postflight_verified") is True
            and record.get("qmp_quit_status") in (
                "PASS",
                "ALREADY_EXITED",
                "FAILED_BUT_GONE",
                "EXITED_DURING_TEARDOWN",
            )
            and record.get("qmp_socket_absent") is True
            and type(record.get("completed_host_wall_ns")) is int
            and record["completed_host_wall_ns"] > 0
            and isinstance(record.get("qemu_host_identity"), dict)
            and type(record["qemu_host_identity"].get("pid")) is int
            and record["qemu_host_identity"]["pid"] > 1
            and isinstance(record["qemu_host_identity"].get("start_token"), str)
            and record["qemu_host_identity"]["start_token"].isdigit()
            and isinstance(record.get("stages"), dict)
            and record.get("qemu_build") == "NOT_RUN"
            and isinstance(record.get("errors"), list)
            and all(isinstance(error, str) for error in record["errors"])
            and isinstance(record.get("teardown_warnings"), list)
            and all(isinstance(error, str) for error in record["teardown_warnings"])
        )
    except AttributeError:
        valid = False
    if not valid:
        raise ValueError("controller final record does not prove clean exact teardown")
    return record


def build_previews(payloads, ffmpeg, *, final_record=None, runner=subprocess.run):
    outputs = {}
    stage_summaries = {}
    for stage in ("pre-launch", "load", "hit", "post"):
        still_name = RUN_ID + "-qmp-" + stage + "-still.ppm"
        metadata_name = still_name + ".capture.json"
        metadata = _json_record(payloads, metadata_name, required=False)
        stage_summary = {"still_status": "MISSING", "video_status": "NOT_REQUESTED"}
        if still_name in payloads and metadata is not None:
            record = _validate_ppm(payloads, still_name, metadata)
            png_name = "FLR-0416-" + stage + ".png"
            outputs[png_name] = encode_png(ffmpeg, payloads[still_name], runner=runner)
            stage_summary["still_status"] = "PASS"
            stage_summary["still_sha256"] = hashlib.sha256(outputs[png_name]).hexdigest()
            stage_summary["source_still_sha256"] = record["sha256"]
        if stage in ("hit", "post"):
            try:
                records = validate_capture_set(payloads, stage)
            except ValueError as error:
                stage_summary["video_status"] = "INCOMPLETE"
                stage_summary["video_reason"] = str(error)
            else:
                try:
                    validate_bracket_record(payloads, stage, records, final_record)
                except ValueError as error:
                    bracket_verified = False
                    bracket_reason = str(error)
                else:
                    bracket_verified = True
                    bracket_reason = None
                video_name = "FLR-0416-" + stage + ".mp4"
                frame_names = [record["name"] for record in records[1:]]
                frame_payloads = [payloads[name] for name in frame_names]
                outputs[video_name] = encode_mp4(ffmpeg, frame_payloads, runner=runner)
                midpoints = [
                    (record["host_monotonic_ns"][0] + record["host_monotonic_ns"][1]) // 2
                    for record in records[1:]
                ]
                intervals_ms = [
                    round((right - left) / 1_000_000, 3)
                    for left, right in zip(midpoints, midpoints[1:])
                ]
                stage_summary.update(
                    {
                        "video_status": "PASS" if bracket_verified else "UNVERIFIED_BRACKET",
                        "correlation_status": "VERIFIED" if bracket_verified else "UNKNOWN",
                        "video_sha256": hashlib.sha256(outputs[video_name]).hexdigest(),
                        "capture_interval_ms": intervals_ms,
                        "nominal_playback_fps": PLAYBACK_FPS,
                        "real_time_video": False,
                        "source_frame_sha256": [record["sha256"] for record in records[1:]],
                        "bracket_verified": bracket_verified,
                        "bracket_reason": bracket_reason,
                    }
                )
        stage_summaries[stage] = stage_summary
    if not outputs:
        raise ValueError("no verified QMP screen media is available for preview")
    return outputs, stage_summaries


def write_previews(
    outputs,
    stage_summaries,
    output_dir,
    diagnostic_status,
    *,
    teardown_verified,
    source_media_manifest,
):
    target = Path(output_dir)
    if not target.is_absolute() or target.exists() or target.is_symlink():
        raise ValueError("preview output must be an unused absolute directory")
    if not target.parent.is_dir():
        raise ValueError("preview output parent must already exist")
    target.mkdir(mode=0o700)
    created = {}
    for name, content in outputs.items():
        if Path(name).name != name:
            raise ValueError("preview filename is invalid")
        path = target / name
        with path.open("xb") as destination:
            destination.write(content)
        created[name] = hashlib.sha256(content).hexdigest()
    for stage, summary in stage_summaries.items():
        if summary["still_status"] == "MISSING" and summary["video_status"] in ("NOT_REQUESTED", "INCOMPLETE"):
            continue
        sidecar = {
            "event": "FLR0416_LOCAL_MEDIA_PREVIEW",
            "run_id": RUN_ID,
            "stage": stage,
            "diagnostic_status": diagnostic_status,
            "teardown_verified": teardown_verified,
            **summary,
            "outputs": {name: digest for name, digest in created.items() if "-" + stage in name},
            "raw_ppm_retained_on_mini": True,
            "playback_is_real_time": False,
        }
        name = "FLR-0416-" + stage + ".preview.json"
        with (target / name).open("xb") as destination:
            destination.write(json.dumps(sidecar, sort_keys=True, separators=(",", ":")).encode())
    index = {
        "event": "FLR0416_LOCAL_MEDIA_PREVIEW_INDEX",
        "run_id": RUN_ID,
        "diagnostic_status": diagnostic_status,
        "teardown_verified": teardown_verified,
        "stages": stage_summaries,
        "outputs": created,
        "source_media_manifest": source_media_manifest,
        "raw_ppm_retained_on_mini": True,
        "playback_is_real_time": False,
    }
    with (target / "FLR-0416-preview-index.json").open("xb") as destination:
        destination.write(json.dumps(index, sort_keys=True, separators=(",", ":")).encode())
    return target


def export_previews(host, evidence_root, output_dir, *, ffmpeg=None, runner=subprocess.run):
    executable = ffmpeg or shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("Mac FFmpeg is unavailable")
    archive_bytes = fetch_media_archive(host, evidence_root, runner=runner)
    payloads, manifest = validate_media_archive(archive_bytes)
    final = validate_controller_final(payloads)
    outputs, summaries = build_previews(
        payloads, executable, final_record=final, runner=runner
    )
    return write_previews(
        outputs,
        summaries,
        output_dir,
        final["status"],
        teardown_verified=final["teardown_verified"],
        source_media_manifest=manifest["files"],
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("BUILD_HOST"))
    parser.add_argument("--evidence-root", default=os.environ.get("BUILD_EVIDENCE"))
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    if not args.host or not args.evidence_root:
        parser.error("--host/BUILD_HOST and --evidence-root/BUILD_EVIDENCE are required")
    try:
        output = export_previews(args.host, args.evidence_root, args.output_dir)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print("FLR0416_MEDIA_PREVIEW=FAIL reason=" + str(error), file=sys.stderr)
        return 1
    print("FLR0416_MEDIA_PREVIEW=PASS output=" + str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
