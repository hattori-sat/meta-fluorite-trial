"""GDB 14.2 callback for FLR-0416's first libLLVM target hit."""

import gdb
import hashlib
import json
import os
import re
import struct
import time

import flr0416_gdb_observer as observer


RUN_ID = "flr0416-0001"
ROOT = "/run/user/1001/" + RUN_ID
LIBRARY = "/usr/lib/libLLVM.so.18.1"
BUILD_ID = "359c1108040bc6bc1af64bb639d0b25385858051"
TARGET_VMA = 0xB1D541
TARGET_UID = 1001
ACK_COLLECTION_SECONDS = 540
ACK_ABORT_GRACE_SECONDS = 60
TARGET = None
BREAKPOINT = None


def _file_text(path):
    with open(path, "r", encoding="utf-8") as stream:
        return stream.read()


def _proc_identity(pid):
    status = _file_text("/proc/%d/status" % pid)
    match = re.search(r"^Uid:\s+(\d+)", status, re.MULTILINE)
    if match is None:
        raise RuntimeError("process_uid_unavailable")
    stat_tail = _file_text("/proc/%d/stat" % pid).rsplit(")", 1)[1].split()
    if len(stat_tail) <= 19:
        raise RuntimeError("process_start_token_unavailable")
    return {
        "pid": int(pid),
        "uid": int(match.group(1)),
        "start_token": stat_tail[19],
    }


def _guest_clocks():
    return {
        "wall_ns": time.time_ns(),
        "monotonic_ns": time.monotonic_ns(),
    }


def _elf_target(path, expected_build_id, vma, pid):
    with open(path, "rb") as stream:
        header = stream.read(64)
        if header[:6] != b"\x7fELF\x02\x01":
            raise RuntimeError("unexpected_elf_class_or_encoding")
        phoff = struct.unpack_from("<Q", header, 32)[0]
        phentsize, phnum = struct.unpack_from("<HH", header, 54)
        if phentsize < 56:
            raise RuntimeError("short_elf_program_header")

        executable_segments = []
        build_id = ""
        for index in range(phnum):
            stream.seek(phoff + index * phentsize)
            entry = stream.read(phentsize)
            kind, flags, offset, vaddr, _, file_size, mem_size, _ = (
                struct.unpack_from("<IIQQQQQQ", entry)
            )
            if kind == 1 and flags & 1 and vaddr <= vma < vaddr + mem_size:
                executable_segments.append((offset, vaddr, mem_size))
            if kind == 4:
                stream.seek(offset)
                notes = stream.read(file_size)
                cursor = 0
                while cursor + 12 <= len(notes):
                    name_size, desc_size, note_type = struct.unpack_from(
                        "<III", notes, cursor
                    )
                    cursor += 12
                    name = notes[cursor : cursor + name_size].rstrip(b"\0")
                    cursor = (cursor + name_size + 3) & ~3
                    desc = notes[cursor : cursor + desc_size]
                    cursor = (cursor + desc_size + 3) & ~3
                    if name == b"GNU" and note_type == 3:
                        build_id = desc.hex()

    if build_id != expected_build_id or len(executable_segments) != 1:
        raise RuntimeError("ELF_Build_ID_or_PT_LOAD_mismatch")

    page_size = os.sysconf("SC_PAGE_SIZE")
    file_offset, segment_vaddr, _ = executable_segments[0]
    candidates = []
    maps_text = _file_text("/proc/%d/maps" % pid)
    for line in maps_text.splitlines():
        fields = line.split(None, 5)
        if len(fields) < 6 or fields[5] != path or "x" not in fields[1]:
            continue
        try:
            map_start, map_end = (int(value, 16) for value in fields[0].split("-", 1))
            map_offset = int(fields[2], 16)
        except ValueError:
            continue
        file_page = file_offset - file_offset % page_size
        virtual_page = segment_vaddr - segment_vaddr % page_size
        bias = map_start - virtual_page - (map_offset - file_page)
        address = bias + vma
        expected_file_offset = file_offset + vma - segment_vaddr
        actual_file_offset = map_offset + address - map_start
        if map_start <= address < map_end and actual_file_offset == expected_file_offset:
            candidates.append((address, bias, line, expected_file_offset))

    if len(candidates) != 1:
        raise RuntimeError("unique_executable_load_mapping_not_proven")
    return {
        "build_id": build_id,
        "vma": "0x%x" % vma,
        "load_bias": "0x%x" % candidates[0][1],
        "address": candidates[0][0],
        "mapping": candidates[0][2],
        "segment_file_offset": file_offset,
        "segment_vaddr": segment_vaddr,
        "segment_mem_size": executable_segments[0][2],
    }


def _encode_write(path, fields):
    observer.publish_once(path, observer.encode_hit_record(fields))


def record_failure(phase, error):
    try:
        _encode_write(
            ROOT + "-observer-error",
            {
                "run_id": RUN_ID,
                "phase": phase,
                "error_type": type(error).__name__,
            },
        )
    except (Exception, KeyboardInterrupt):
        pass


def _safe_field(fields, errors, name, getter):
    try:
        fields[name] = getter()
    except (Exception, KeyboardInterrupt) as error:
        fields[name] = "UNKNOWN"
        errors[name] = type(error).__name__


class FirstHitBreakpoint(gdb.Breakpoint):
    def __init__(self, address, expected_process):
        self.hit_begin_path = ROOT + "-hit-begin"
        self.hit_record_path = ROOT + "-hit-record.json"
        self.address = address
        self.expected_process = expected_process
        super(FirstHitBreakpoint, self).__init__(
            "*0x%x" % address,
            type=gdb.BP_HARDWARE_BREAKPOINT,
            temporary=True,
        )

    def stop(self):
        try:
            observer.create_once(self.hit_begin_path, "HIT_BEGIN\n")
        except (Exception, KeyboardInterrupt) as error:
            record_failure("hit_begin", error)
            return True

        try:
            self._write_hit_record()
        except (Exception, KeyboardInterrupt) as error:
            record_failure("hit_record", error)
        return True

    def _write_hit_record(self):
        fields = {
            "event": "HIT_RECORD",
            "run_id": RUN_ID,
            "expected_process": self.expected_process,
            "errors": {},
        }
        errors = fields["errors"]
        _safe_field(fields, errors, "guest_boot_id", lambda: _file_text(
            "/proc/sys/kernel/random/boot_id"
        ).strip())
        _safe_field(fields, errors, "process", lambda: _proc_identity(
            int(gdb.selected_inferior().pid)
        ))
        _safe_field(fields, errors, "gdb_process", lambda: _proc_identity(os.getpid()))
        _safe_field(fields, errors, "guest_clocks", _guest_clocks)
        _safe_field(fields, errors, "lwp", lambda: int(gdb.selected_thread().ptid[1]))
        _safe_field(fields, errors, "pc", lambda: int(gdb.parse_and_eval("$pc")))
        _safe_field(fields, errors, "caller_resume_pc", lambda: int(
            gdb.selected_frame().older().pc()
        ))

        process_record = fields.get("process")
        pid = process_record.get("pid") if isinstance(process_record, dict) else None
        pc = fields.get("pc")
        if isinstance(pid, int) and isinstance(pc, int):
            _safe_field(fields, errors, "pc_mapping", lambda: observer.mapping_for_address(
                _file_text("/proc/%d/maps" % pid), pc
            ))
        else:
            fields["pc_mapping"] = "UNKNOWN"
            errors["pc_mapping"] = "required_identity_or_pc_unknown"

        caller_pc = fields.get("caller_resume_pc")
        if isinstance(pid, int) and isinstance(caller_pc, int):
            _safe_field(fields, errors, "caller_mapping", lambda: observer.mapping_for_address(
                _file_text("/proc/%d/maps" % pid), caller_pc
            ))
        else:
            fields["caller_mapping"] = "UNKNOWN"
            errors["caller_mapping"] = "required_identity_or_caller_unknown"

        fields["target_pc_match"] = fields.get("pc") == self.address
        fields["identity_match"] = observer.target_identity_matches(
            fields, self.expected_process
        )
        try:
            _encode_write(self.hit_record_path, fields)
        except (Exception, KeyboardInterrupt) as error:
            record_failure("hit_record", error)


def arm_target_breakpoint():
    global TARGET, BREAKPOINT
    inferior = gdb.selected_inferior()
    pid = int(inferior.pid)
    process = _proc_identity(pid)
    if process["uid"] != TARGET_UID:
        raise RuntimeError("inferior_uid_mismatch")
    boot_id = _file_text("/proc/sys/kernel/random/boot_id").strip()
    library = _elf_target(LIBRARY, BUILD_ID, TARGET_VMA, pid)
    clocks = _guest_clocks()
    gdb_process = _proc_identity(os.getpid())
    if gdb_process["uid"] != TARGET_UID:
        raise RuntimeError("gdb_uid_mismatch")
    TARGET = {
        "run_id": RUN_ID,
        "guest_boot_id": boot_id,
        "process": process,
        "gdb_process": gdb_process,
        "library": library,
        "guest_clocks": clocks,
    }

    BREAKPOINT = FirstHitBreakpoint(library["address"], TARGET)
    if BREAKPOINT.type != gdb.BP_HARDWARE_BREAKPOINT:
        raise RuntimeError("hardware_breakpoint_type_mismatch")
    details = gdb.execute(
        "info breakpoints %d" % BREAKPOINT.number,
        to_string=True,
    )
    if not re.search(r"\bhw breakpoint\b", details, re.IGNORECASE):
        raise RuntimeError("hardware_breakpoint_insertion_unconfirmed")
    address_pattern = r"\b0x0*%x\b" % library["address"]
    if re.search(address_pattern, details, re.IGNORECASE) is None:
        raise RuntimeError("hardware_breakpoint_address_not_listed")

    TARGET["breakpoint"] = {
        "number": int(BREAKPOINT.number),
        "type": "hardware",
        "address": "0x%x" % library["address"],
        "info": details,
    }
    _encode_write(ROOT + "-armed.json", TARGET)
    gdb.write("FLR0416_HWB_ARMED address=0x%x\n" % library["address"])


def _valid_release(expected_process, stage):
    return observer.validate_controller_release(ROOT, stage, expected_process)


def wait_for_release(stage, timeout_seconds):
    path = ROOT + "-" + stage + "-release.json"
    abort_path = ROOT + "-" + stage + "-abort.json"
    deadline = time.monotonic() + timeout_seconds + ACK_ABORT_GRACE_SECONDS
    while time.monotonic() < deadline:
        if os.path.exists(abort_path):
            if observer.validate_controller_abort(ROOT, stage, TARGET):
                _encode_write(
                    ROOT + "-" + stage + "-abort-accepted.json",
                    {"event": "CONTROLLER_ABORT_ACCEPTED", "run_id": RUN_ID, "stage": stage},
                )
            return False
        if os.path.exists(path):
            if not _valid_release(TARGET, stage):
                return False
            with open(path, "rb") as stream:
                release_bytes = stream.read()
            with open(ROOT + "-" + stage + "-manifest.json", "rb") as stream:
                manifest_bytes = stream.read()
            _encode_write(
                ROOT + "-" + stage + "-release-accepted.json",
                {
                    "event": "GUEST_RELEASE_ACCEPTED",
                    "run_id": RUN_ID,
                    "stage": stage,
                    "guest_boot_id": TARGET["guest_boot_id"],
                    "process": TARGET["process"],
                    "gdb_process": TARGET["gdb_process"],
                    "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                    "release_sha256": hashlib.sha256(release_bytes).hexdigest(),
                },
            )
            return True
        time.sleep(0.1)
    _encode_write(
        ROOT + "-" + stage + "-release-timeout.json",
        {"event": "RELEASE_TIMEOUT", "run_id": RUN_ID, "stage": stage},
    )
    return False


def _require_live_identity():
    if not isinstance(TARGET, dict):
        raise RuntimeError("target_identity_unavailable")
    if _file_text("/proc/sys/kernel/random/boot_id").strip() != TARGET["guest_boot_id"]:
        raise RuntimeError("guest_boot_id_changed")
    pid = TARGET["process"]["pid"]
    if _proc_identity(pid) != TARGET["process"]:
        raise RuntimeError("inferior_identity_changed")
    if _proc_identity(os.getpid()) != TARGET["gdb_process"]:
        raise RuntimeError("gdb_identity_changed")
    inferior = gdb.selected_inferior()
    if int(inferior.pid) != pid:
        raise RuntimeError("selected_inferior_changed")
    return inferior


def _thread_stop_states(inferior):
    if bool(gdb.parameter("non-stop")):
        raise RuntimeError("gdb_not_in_all_stop_mode")
    threads = inferior.threads()
    if not threads:
        raise RuntimeError("no_inferior_threads")
    states = []
    for thread in threads:
        if not thread.is_valid():
            raise RuntimeError("invalid_inferior_thread")
        stopped = bool(thread.is_stopped())
        states.append({"ptid": list(thread.ptid), "stopped": stopped})
        if not stopped:
            raise RuntimeError("inferior_thread_not_stopped")
    return states


def record_load_stop_and_wait():
    inferior = _require_live_identity()
    thread_states = _thread_stop_states(inferior)
    program = gdb.execute("info program", to_string=True)
    threads = gdb.execute("info threads", to_string=True)
    catchpoints = [bp for bp in (gdb.breakpoints() or ()) if bp.number == 1]
    if len(catchpoints) != 1 or catchpoints[0].enabled:
        raise RuntimeError("library_load_catchpoint_not_disabled")
    record = {
        "event": "LOAD_READY",
        "run_id": RUN_ID,
        "stop_boundary": "catch-load-libLLVM",
        "target": TARGET,
        "load_catchpoint_disabled": True,
        "all_app_threads_stopped": True,
        "thread_states": thread_states,
        "info_program": program,
        "info_threads": threads,
        "guest_clocks": _guest_clocks(),
    }
    _encode_write(ROOT + "-load-ready.json", record)
    if not wait_for_release("load", ACK_COLLECTION_SECONDS):
        raise RuntimeError("load_release_missing_or_invalid")


def capture_first_stop_and_wait():
    marker = _file_text(ROOT + "-hit-begin")
    if marker != "HIT_BEGIN\n":
        raise RuntimeError("first_hit_marker_or_record_missing")
    if os.path.exists(ROOT + "-observer-error"):
        raise RuntimeError("observer_error_record_present")
    with open(ROOT + "-hit-record.json", "r", encoding="utf-8") as stream:
        hit = json.load(stream)
    required_hit_fields = {
        "guest_boot_id",
        "process",
        "gdb_process",
        "guest_clocks",
        "lwp",
        "pc",
        "pc_mapping",
    }
    if (
        hit.get("event") != "HIT_RECORD"
        or hit.get("run_id") != RUN_ID
        or required_hit_fields.intersection(hit.get("errors", {}))
        or hit.get("target_pc_match") is not True
        or hit.get("identity_match") is not True
        or hit.get("guest_boot_id") != TARGET["guest_boot_id"]
        or hit.get("process") != TARGET["process"]
        or hit.get("gdb_process") != TARGET["gdb_process"]
        or hit.get("pc") != TARGET["library"]["address"]
        or hit.get("pc_mapping") != TARGET["library"]["mapping"]
    ):
        raise RuntimeError("hit_record_identity_or_target_mismatch")
    inferior = _require_live_identity()
    thread_states = _thread_stop_states(inferior)
    program = gdb.execute("info program", to_string=True)
    threads = gdb.execute("info threads", to_string=True)
    release_blockers = []
    if not isinstance(hit.get("caller_resume_pc"), int):
        release_blockers.append("caller_resume_pc_unknown")
    if hit.get("caller_mapping") == "UNKNOWN":
        release_blockers.append("caller_mapping_unknown")
    _encode_write(
        ROOT + "-hit-ready.json",
        {
            "event": "HIT_READY",
            "run_id": RUN_ID,
            "stop_boundary": "temporary-hardware-breakpoint",
            "target": TARGET,
            "breakpoint": TARGET["breakpoint"],
            "hit": hit,
            "release_eligible": not release_blockers,
            "release_blockers": release_blockers,
            "all_app_threads_stopped": True,
            "thread_states": thread_states,
            "info_program": program,
            "info_threads": threads,
            "guest_clocks": _guest_clocks(),
        },
    )
    if not wait_for_release("hit", ACK_COLLECTION_SECONDS):
        raise RuntimeError("hit_release_missing_invalid_or_controller_aborted")


def abort_run(phase, error):
    record_failure(phase, error)
    try:
        gdb.execute("kill")
    except (Exception, KeyboardInterrupt):
        pass
    gdb.execute("quit")


def capture_after_continue():
    errors = {}
    fields = {
        "event": "AFTER_CONTINUE_STOP_OR_EXIT",
        "run_id": RUN_ID,
        "expected_target": TARGET,
        "errors": errors,
        "guest_clocks": "UNKNOWN",
        "process_observation": "UNKNOWN",
        "gdb_observation": "UNKNOWN",
        "inferior_pid": "UNKNOWN",
        "thread_states": "UNKNOWN",
        "info_program": "UNKNOWN",
        "info_threads": "UNKNOWN",
        "stop_classification": "UNKNOWN",
    }
    _safe_field(fields, errors, "guest_clocks", _guest_clocks)
    try:
        boot_id = _file_text("/proc/sys/kernel/random/boot_id").strip()
        fields["guest_boot_id"] = boot_id
        if TARGET is not None and boot_id != TARGET.get("guest_boot_id"):
            errors["guest_boot_id"] = "identity_mismatch"
    except (Exception, KeyboardInterrupt) as error:
        fields["guest_boot_id"] = "UNKNOWN"
        errors["guest_boot_id"] = type(error).__name__

    if isinstance(TARGET, dict):
        pid = TARGET.get("process", {}).get("pid")
        try:
            actual = _proc_identity(int(pid))
            comm = _file_text("/proc/%d/comm" % int(pid)).strip()
            stat_fields = _file_text("/proc/%d/stat" % int(pid)).rsplit(")", 1)[1].split()
            state = stat_fields[0]
            fields["process_observation"] = {
                "actual": {**actual, "comm": comm, "state": state},
                "matches": (
                    actual == TARGET["process"]
                    and comm == "flutter-auto"
                    and state not in ("Z", "X")
                ),
                "state": "ZOMBIE" if state == "Z" else "DEAD" if state == "X" else "LIVE",
            }
        except (Exception, KeyboardInterrupt) as error:
            if pid is not None and not os.path.exists("/proc/%s" % pid):
                fields["process_observation"] = {"state": "EXITED", "matches": False}
            else:
                fields["process_observation"] = {
                    "state": "UNKNOWN",
                    "matches": False,
                }
                errors["process_observation"] = type(error).__name__

        try:
            gdb_actual = _proc_identity(os.getpid())
            fields["gdb_observation"] = {
                "actual": gdb_actual,
                "matches": gdb_actual == TARGET["gdb_process"],
            }
        except (Exception, KeyboardInterrupt) as error:
            errors["gdb_observation"] = type(error).__name__

    inferior = None
    try:
        inferior = gdb.selected_inferior()
        fields["inferior_pid"] = int(inferior.pid)
    except (Exception, KeyboardInterrupt) as error:
        errors["inferior_pid"] = type(error).__name__
    try:
        fields["info_program"] = gdb.execute("info program", to_string=True)
    except (Exception, KeyboardInterrupt) as error:
        errors["info_program"] = "UNKNOWN:%s" % type(error).__name__
    try:
        fields["info_threads"] = gdb.execute("info threads", to_string=True)
    except (Exception, KeyboardInterrupt) as error:
        fields["info_threads"] = "UNKNOWN:%s" % type(error).__name__
    if inferior is not None:
        try:
            fields["thread_states"] = _thread_stop_states(inferior)
        except (Exception, KeyboardInterrupt) as error:
            fields["thread_states"] = "UNKNOWN"
            errors["thread_states"] = type(error).__name__

    process_observation = fields.get("process_observation")
    if isinstance(process_observation, dict) and process_observation.get("state") in ("EXITED", "DEAD"):
        fields["stop_classification"] = "inferior_exited"
    elif isinstance(process_observation, dict) and process_observation.get("matches"):
        states = fields.get("thread_states")
        if isinstance(states, list) and states and all(item.get("stopped") for item in states):
            fields["stop_classification"] = "inferior_live_all_threads_stopped"
        else:
            fields["stop_classification"] = "inferior_live_stop_state_unknown"
    else:
        fields["stop_classification"] = "inferior_identity_or_liveness_unknown"
    try:
        _encode_write(ROOT + "-after-continue.json", fields)
    except (Exception, KeyboardInterrupt) as error:
        record_failure("after_continue_write", error)
