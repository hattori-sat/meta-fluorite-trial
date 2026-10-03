"""Pure helpers shared by the FLR-0416 GDB observer and host tests."""

import json
import hashlib
import os
import re
import tempfile


def mapping_for_address(maps_text, address):
    """Return the sole executable /proc/PID/maps line containing address."""
    if not isinstance(address, int) or isinstance(address, bool) or address < 0:
        raise ValueError("address must be a non-negative integer")

    matches = []
    for line in maps_text.splitlines():
        fields = line.split(None, 5)
        if len(fields) < 5 or "x" not in fields[1]:
            continue

        bounds = fields[0].split("-", 1)
        if len(bounds) != 2:
            continue
        try:
            start, end = (int(bound, 16) for bound in bounds)
        except ValueError:
            continue
        if start <= address < end:
            matches.append(line)

    if len(matches) != 1:
        raise ValueError(
            "expected one executable mapping for address, found %d" % len(matches)
        )
    return matches[0]


def encode_hit_record(fields):
    """Encode one canonical, single-line JSON record for the hit evidence."""
    return json.dumps(
        fields,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ) + "\n"


def target_identity_matches(actual, expected):
    """Require the guest boot, inferior, and debugger to match the armed run."""
    if not isinstance(actual, dict) or not isinstance(expected, dict):
        return False
    return all(
        actual.get(key) == expected.get(key)
        for key in ("guest_boot_id", "process", "gdb_process")
    )


def create_once(path, text):
    """Create and fsync a private evidence file without replacing any path."""
    if not isinstance(text, str):
        raise TypeError("record must be text")

    path = os.fspath(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        stream = os.fdopen(descriptor, "wb")
        descriptor = -1
        with stream:
            stream.write(text.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())

        parent = os.path.dirname(path) or "."
        directory_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def publish_once(path, text):
    """Publish one complete durable record atomically without replacement."""
    if not isinstance(text, str):
        raise TypeError("record must be text")

    path = os.fspath(path)
    parent = os.path.dirname(path) or "."
    descriptor, temporary_path = tempfile.mkstemp(
        prefix=".flr0416-publish-", dir=parent
    )
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(text.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())

        # Same-directory hard-link publication is atomic and fails if the
        # final name already exists; readers never observe partial JSON.
        os.link(temporary_path, path)
        directory_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        else:
            directory_descriptor = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)


def validate_controller_release(root, stage, expected_process):
    """Validate the explicit ACK, its manifest digest, identities and guest files."""
    if stage not in ("load", "hit"):
        return False

    release_path = root + "-" + stage + "-release.json"
    manifest_path = root + "-" + stage + "-manifest.json"
    expected_digest = re.compile(r"[0-9a-f]{64}")
    try:
        if (
            os.path.islink(release_path)
            or os.path.islink(manifest_path)
            or not os.path.isfile(release_path)
            or not os.path.isfile(manifest_path)
        ):
            return False
        with open(release_path, "r", encoding="utf-8") as stream:
            release = json.load(stream)
        with open(manifest_path, "r", encoding="utf-8") as stream:
            manifest = json.load(stream)

        manifest_hash = release.get("manifest_sha256", "")
        if not expected_digest.fullmatch(manifest_hash):
            return False
        actual_hash = hashlib.sha256()
        with open(manifest_path, "rb") as stream:
            for block in iter(lambda: stream.read(65536), b""):
                actual_hash.update(block)
        if actual_hash.hexdigest() != manifest_hash:
            return False

        expected_identity = {
            "guest_boot_id": expected_process["guest_boot_id"],
            "process": expected_process["process"],
            "gdb_process": expected_process["gdb_process"],
        }
        for record in (release, manifest):
            if any(record.get(key) != value for key, value in expected_identity.items()):
                return False

        if not (
            release.get("event") == "CONTROLLER_ACK"
            and release.get("run_id") == "flr0418-0001"
            and release.get("stage") == stage
            and release.get("manifest_path") == manifest_path
            and release.get("acknowledged") is True
            and manifest.get("event") == "EVIDENCE_MANIFEST"
            and manifest.get("run_id") == "flr0418-0001"
            and manifest.get("stage") == stage
            and manifest.get("controller_acknowledged") is True
        ):
            return False

        files = manifest.get("files")
        if not isinstance(files, dict):
            return False
        base = os.path.basename(root)
        required = {base + "-armed.json"}
        if stage == "load":
            required.add(base + "-load-ready.json")
            required_mini = {
                base + "-load-bracket.json",
                base + "-qmp-load-still.ppm",
            }
        else:
            required.update(
                {
                    base + "-hit-begin",
                    base + "-hit-record.json",
                    base + "-hit-ready.json",
                }
            )
            required_mini = {
                base + "-hit-bracket.json",
                base + "-qmp-hit-still.ppm",
            }
            required_mini.update(
                base + "-qmp-hit-frame-%04d.ppm" % index
                for index in range(8)
            )

        verified_guest = set()
        verified_mini = set()
        for name, metadata in files.items():
            if not isinstance(name, str) or not isinstance(metadata, dict):
                return False
            if not expected_digest.fullmatch(metadata.get("sha256", "")):
                return False
            if os.path.basename(name) != name:
                return False
            source = metadata.get("source")
            if source == "mini":
                verified_mini.add(name)
                continue
            if source != "guest":
                return False
            if not name.startswith(base + "-"):
                return False
            guest_path = os.path.join(os.path.dirname(root), name)
            if os.path.islink(guest_path) or not os.path.isfile(guest_path):
                return False
            digest = hashlib.sha256()
            with open(guest_path, "rb") as stream:
                for block in iter(lambda: stream.read(65536), b""):
                    digest.update(block)
            if digest.hexdigest() != metadata["sha256"]:
                return False
            verified_guest.add(name)
        if not required.issubset(verified_guest) or not required_mini.issubset(verified_mini):
            return False

        base_path = os.path.dirname(root)
        if stage == "load":
            with open(os.path.join(base_path, base + "-load-ready.json"), "r", encoding="utf-8") as stream:
                ready = json.load(stream)
            target = ready.get("target", {})
            return bool(
                ready.get("event") == "LOAD_READY"
                and ready.get("stop_boundary") == "catch-load-libLLVM"
                and ready.get("load_catchpoint_disabled") is True
                and ready.get("all_app_threads_stopped") is True
                and isinstance(ready.get("thread_states"), list)
                and bool(ready["thread_states"])
                and all(state.get("stopped") is True for state in ready.get("thread_states", []))
                and target.get("guest_boot_id") == expected_process["guest_boot_id"]
                and target.get("process") == expected_process["process"]
                and target.get("gdb_process") == expected_process["gdb_process"]
            )

        with open(os.path.join(base_path, base + "-hit-record.json"), "r", encoding="utf-8") as stream:
            hit = json.load(stream)
        with open(os.path.join(base_path, base + "-hit-ready.json"), "r", encoding="utf-8") as stream:
            ready = json.load(stream)
        target = ready.get("target", {})
        breakpoint = ready.get("breakpoint", {})
        return bool(
            hit.get("event") == "HIT_RECORD"
            and hit.get("run_id") == "flr0418-0001"
            and hit.get("guest_boot_id") == expected_process["guest_boot_id"]
            and hit.get("process") == expected_process["process"]
            and hit.get("gdb_process") == expected_process["gdb_process"]
            and hit.get("errors") == {}
            and hit.get("target_pc_match") is True
            and hit.get("identity_match") is True
            and isinstance(hit.get("pc"), int)
            and hit.get("pc_mapping") != "UNKNOWN"
            and isinstance(hit.get("caller_resume_pc"), int)
            and hit.get("caller_mapping") != "UNKNOWN"
            and ready.get("event") == "HIT_READY"
            and ready.get("stop_boundary") == "temporary-hardware-breakpoint"
            and ready.get("run_id") == "flr0418-0001"
            and ready.get("release_eligible") is True
            and ready.get("release_blockers") == []
            and ready.get("all_app_threads_stopped") is True
            and isinstance(ready.get("thread_states"), list)
            and bool(ready["thread_states"])
            and all(state.get("stopped") is True for state in ready.get("thread_states", []))
            and target.get("guest_boot_id") == expected_process["guest_boot_id"]
            and target.get("process") == expected_process["process"]
            and target.get("gdb_process") == expected_process["gdb_process"]
            and target.get("library", {}).get("address") == hit.get("pc")
            and target.get("library", {}).get("mapping") == hit.get("pc_mapping")
            and breakpoint.get("type") == "hardware"
            and int(breakpoint.get("address", "0"), 16) == hit.get("pc")
            and ready.get("hit") == hit
        )
    except (Exception, KeyboardInterrupt):
        return False


def validate_controller_abort(root, stage, expected_process):
    """Accept only an identity-matched controller abort; it can never resume."""
    if stage not in ("load", "hit"):
        return False
    path = root + "-" + stage + "-abort.json"
    try:
        if os.path.islink(path) or not os.path.isfile(path):
            return False
        with open(path, "r", encoding="utf-8") as stream:
            abort = json.load(stream)
        return bool(
            abort.get("event") == "CONTROLLER_ABORT"
            and abort.get("run_id") == "flr0418-0001"
            and abort.get("stage") == stage
            and abort.get("guest_boot_id") == expected_process["guest_boot_id"]
            and abort.get("process") == expected_process["process"]
            and abort.get("gdb_process") == expected_process["gdb_process"]
            and isinstance(abort.get("reason"), str)
            and 0 < len(abort["reason"]) <= 256
        )
    except (Exception, KeyboardInterrupt):
        return False
