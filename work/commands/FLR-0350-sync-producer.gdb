set pagination off
set confirm off
set print thread-events off
set breakpoint pending on
set follow-exec-mode same
set follow-fork-mode parent
set detach-on-fork on

python
import gdb
import os
import stat
import time

RUN_DIR = "/run/user/1001"
ROOT_DIR = "/run/flr0350"
GATE_PATH = RUN_DIR + "/flr0350-go.fifo"
RUN_ID_FILE = ROOT_DIR + "/run.id"
IDENTITY_FILE = ROOT_DIR + "/fifo.identity"
ATTACH_AUTH_FILE = ROOT_DIR + "/attach.auth"
GO_RECORD_FILE = ROOT_DIR + "/go.record"
GO_WAIT_SECONDS = 30
TARGET_PID_FILE = RUN_DIR + "/flr0350-flutter.pid"
START_FILE = RUN_DIR + "/flr0350-wrapper.start"
ARMED_FILE = RUN_DIR + "/flr0350-gdb-armed"
EXEC_FILE = RUN_DIR + "/flr0350-exec-result"
SYMBOL_FILE = RUN_DIR + "/flr0350-symbols-ready"
WAIT_FILE = RUN_DIR + "/flr0350-matched-wait"
EXPECTED_BUILD_ID = "18eb7b64f7fcae9a4b5ef5bbe1fe58a65944a403"
MAX_EVENTS = 16000
MAX_HISTORY_PER_OBJECT = 512
REQUIRED_SYMBOLS = (
    "lvp_queue_submit",
    "lvp_pipe_sync_init",
    "lvp_pipe_sync_finish",
    "lvp_pipe_sync_signal",
    "lvp_pipe_sync_signal_with_fence",
    "lvp_pipe_sync_reset",
    "lvp_pipe_sync_move",
    "lvp_pipe_sync_wait",
)

with open(TARGET_PID_FILE, "r") as stream:
    TARGET_PID = int(stream.read().strip())
with open(START_FILE, "r") as stream:
    TARGET_START = stream.read().strip()
GDB_PID = os.getpid()
inferior = gdb.selected_inferior()
if inferior.pid != TARGET_PID:
    raise gdb.GdbError("FLR0350 attach PID does not match recorded wrapper")

gdb.set_convenience_variable("flr0350_exec_ok", gdb.Value(0))
gdb.set_convenience_variable("flr0350_symbols_ok", gdb.Value(0))
gdb.set_convenience_variable("flr0350_trace_truncated", gdb.Value(0))
trace_breakpoints = {}
history_by_sync = {}
generation_by_sync = {}
alive_by_sync = {}
truncated_syncs = set()
event_count = 0
event_sequence = 0
trace_truncated = False
matched_sync = None
matched_wait_seen = False
watchpoints_armed = False
coverage_gaps = []
queue_submit_count = 0

def emit(line):
    print(line, flush=True)

def guest_uptime():
    try:
        with open("/proc/uptime", "r") as stream:
            return stream.read().split()[0]
    except Exception:
        return "unknown"

def write_once(path, contents):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(contents + "\n")
        stream.flush()
        os.fsync(stream.fileno())

def read_one_line(path):
    with open(path, "r") as stream:
        contents = stream.read()
    if not contents.endswith("\n") or contents.count("\n") != 1:
        raise RuntimeError("not-one-line")
    return contents[:-1]

def root_record(path, expected_fields):
    root = os.lstat(ROOT_DIR)
    if not stat.S_ISDIR(root.st_mode) or root.st_uid != 0 or stat.S_IMODE(root.st_mode) != 0o700:
        raise RuntimeError("root-dir-owner-mode")
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600:
        raise RuntimeError("root-record-owner-mode")
    fields = read_one_line(path).split()
    if len(fields) != expected_fields:
        raise RuntimeError("root-record-field-count")
    return fields

def proc_snapshot(pid):
    with open("/proc/%d/stat" % pid, "r") as stream:
        raw = stream.read()
    boundary = raw.rfind(") ")
    if boundary < 0:
        raise RuntimeError("proc-stat-malformed")
    fields = raw[boundary + 2:].split()
    if len(fields) < 20:
        raise RuntimeError("proc-stat-short")
    state = fields[0]
    start = fields[19]
    uid = None
    tracer = None
    with open("/proc/%d/status" % pid, "r") as stream:
        for line in stream:
            if line.startswith("Uid:"):
                uid = int(line.split()[1])
            elif line.startswith("TracerPid:"):
                tracer = int(line.split()[1])
    with open("/proc/%d/comm" % pid, "r") as stream:
        comm = stream.read().strip()
    if uid is None or tracer is None:
        raise RuntimeError("proc-status-incomplete")
    return state, start, uid, tracer, comm

def stopped_gate_identity():
    if gdb.selected_inferior().pid != TARGET_PID or os.getuid() != 0:
        raise RuntimeError("inferior-or-gdb-identity")
    run_id = read_one_line(RUN_ID_FILE)
    if (len(run_id) != 12 or not run_id.startswith("flr") or
            run_id[3:7].isdigit() is False or run_id[8:12].isdigit() is False or run_id[7] != "-"):
        raise RuntimeError("run-id-format")
    identity = root_record(IDENTITY_FILE, 7)
    if identity[0] != "1" or identity[1] != run_id:
        raise RuntimeError("run-identity-record")
    pid = int(identity[2])
    start_expected = identity[3]
    uid_expected = int(identity[4])
    dev_expected = int(identity[5])
    ino_expected = int(identity[6])
    if pid != TARGET_PID or start_expected != TARGET_START or uid_expected != 1001:
        raise RuntimeError("recorded-target-identity")
    state, start, uid, tracer, comm = proc_snapshot(pid)
    if state not in ("t", "T") or start != start_expected or uid != uid_expected:
        raise RuntimeError("target-not-stopped-or-changed")
    if tracer != GDB_PID or comm != "sh":
        raise RuntimeError("target-tracer-or-comm")
    gate_lstat = os.lstat(GATE_PATH)
    gate_stat = os.stat(GATE_PATH)
    if stat.S_ISLNK(gate_lstat.st_mode) or not stat.S_ISFIFO(gate_stat.st_mode):
        raise RuntimeError("named-gate-type")
    expected_pair = (dev_expected, ino_expected)
    gate_pair = (gate_stat.st_dev, gate_stat.st_ino)
    if gate_pair != expected_pair:
        raise RuntimeError("named-gate-identity")
    for fd in (0, 3):
        descriptor = os.stat("/proc/%d/fd/%d" % (pid, fd))
        if (descriptor.st_dev, descriptor.st_ino) != expected_pair:
            raise RuntimeError("target-fd-%d-identity" % fd)
    gdb_state, gdb_start, gdb_uid, _, gdb_comm = proc_snapshot(GDB_PID)
    if gdb_uid != 0 or gdb_comm != "gdb" or not gdb_start:
        raise RuntimeError("gdb-process-identity")
    return run_id, pid, start, uid, dev_expected, ino_expected, gdb_start

def create_stopped_attach_authorization():
    try:
        run_id, pid, start, uid, dev, ino, gdb_start = stopped_gate_identity()
        content = "1 %s %d %s %d %d %d %d %s" % (
            run_id, pid, start, uid, dev, ino, GDB_PID, gdb_start)
        write_once(ATTACH_AUTH_FILE, content)
        emit("FLR0350_ATTACH_AUTH=PASS pid=%d start=%s gdb_pid=%d gdb_start=%s state=stopped fifo=%d:%d" % (
            pid, start, GDB_PID, gdb_start, dev, ino))
    except Exception as error:
        emit("FLR0350_ATTACH_AUTH=FAIL reason=%s" % str(error).replace("\n", " ")[:120])
        raise gdb.GdbError("FLR0350 stopped attach authorization failed")

def target_lifecycle_state():
    try:
        with open("/proc/%d/stat" % TARGET_PID, "r") as stream:
            raw = stream.read()
        boundary = raw.rfind(") ")
        if boundary < 0:
            return "unknown"
        fields = raw[boundary + 2:].split()
        if len(fields) < 20:
            return "unknown"
        if fields[19] != TARGET_START:
            return "reused"
        return fields[0]
    except OSError:
        return "gone"

def terminate_stopped_inferior(reason):
    try:
        if gdb.selected_inferior().pid != TARGET_PID:
            raise RuntimeError("selected-inferior-mismatch")
        try:
            gdb.execute("kill", to_string=True)
        except Exception:
            try:
                state, start, uid, tracer, _ = proc_snapshot(TARGET_PID)
                if start != TARGET_START or uid != 1001 or tracer != GDB_PID:
                    raise RuntimeError("fallback-target-identity-mismatch")
                os.kill(TARGET_PID, 9)
            except Exception:
                emit("FLR0350_TARGET_ABORT=FAIL reason=%s" % reason)
                while target_lifecycle_state() not in ("gone", "reused", "Z", "X", "x"):
                    time.sleep(0.2)
                emit("FLR0350_TARGET_ABORT=PASS reason=%s target_terminated=1" % reason)
                return
        deadline = time.time() + 2
        while time.time() < deadline:
            if target_lifecycle_state() in ("gone", "reused", "Z", "X", "x"):
                emit("FLR0350_TARGET_ABORT=PASS reason=%s target_terminated=1" % reason)
                return
            time.sleep(0.05)
        emit("FLR0350_TARGET_ABORT=FAIL reason=%s target_still_live=1" % reason)
        while target_lifecycle_state() not in ("gone", "reused", "Z", "X", "x"):
            time.sleep(0.2)
        emit("FLR0350_TARGET_ABORT=PASS reason=%s target_terminated=1" % reason)
    except Exception as error:
        emit("FLR0350_TARGET_ABORT=FAIL reason=%s error=%s" % (
            reason, type(error).__name__))
        while target_lifecycle_state() not in ("gone", "reused", "Z", "X", "x"):
            time.sleep(0.2)
        emit("FLR0350_TARGET_ABORT=PASS reason=%s target_terminated=1" % reason)

def wait_for_go_record():
    deadline = time.time() + GO_WAIT_SECONDS
    while time.time() < deadline:
        try:
            run_id, pid, start, uid, dev, ino, gdb_start = stopped_gate_identity()
            if os.path.lexists(GO_RECORD_FILE):
                record = root_record(GO_RECORD_FILE, 12)
                expected = ["1", run_id, str(pid), start, str(uid), str(dev), str(ino),
                            str(GDB_PID), gdb_start, str(dev), str(ino), "11"]
                if record != expected:
                    raise RuntimeError("go-record-mismatch")
                emit("FLR0350_GO_RECORD=PASS pid=%d gdb_pid=%d fifo=%d:%d bytes=11 target_stopped=1" % (
                    pid, GDB_PID, dev, ino))
                return
        except Exception as error:
            emit("FLR0350_GO_WAIT=FAIL reason=%s" % str(error).replace("\n", " ")[:120])
            terminate_stopped_inferior("go-identity-invalid")
            raise gdb.GdbError("FLR0350 target identity changed before GO")
        time.sleep(0.05)
    emit("FLR0350_GO_WAIT=FAIL reason=record-timeout seconds=%d" % GO_WAIT_SECONDS)
    terminate_stopped_inferior("go-record-timeout")
    raise gdb.GdbError("FLR0350 GO record timeout; inferior terminated before detach")

def current_target_identity():
    try:
        with open("/proc/%d/stat" % TARGET_PID, "r") as stream:
            fields = stream.read().split()
        with open("/proc/%d/comm" % TARGET_PID, "r") as stream:
            comm = stream.read().strip()
        exe = os.readlink("/proc/%d/exe" % TARGET_PID)
        return fields[21], comm, exe
    except Exception:
        return None, None, None

def sync_pointer_arguments(frame):
    result = []
    block = frame.block()
    visited = set()
    while block is not None:
        for symbol in block:
            if not symbol.is_argument or symbol.name in visited:
                continue
            visited.add(symbol.name)
            try:
                value = symbol.value(frame)
                value_type = value.type.strip_typedefs()
                if value_type.code != gdb.TYPE_CODE_PTR or int(value) == 0:
                    continue
                target_type = value_type.target().strip_typedefs()
                field_names = set(field.name for field in target_type.fields() if field.name)
                if "signaled" in field_names and "fence" in field_names:
                    result.append((symbol.name, int(value)))
            except Exception:
                continue
        block = block.superblock
    return result

def selected_tid():
    try:
        thread = gdb.selected_thread()
        return str(thread.ptid[1]) if thread else "unknown"
    except Exception:
        return "unknown"

def sync_fields(address):
    try:
        sync_type = gdb.lookup_type("struct lvp_pipe_sync").pointer()
        sync = gdb.Value(address).cast(sync_type).dereference()
        signaled = bool(int(sync["signaled"]))
        fence = int(sync["fence"])
        return "signaled=%s fence=0x%x" % (str(signaled).lower(), fence)
    except Exception as error:
        return "fields=unavailable:%s" % type(error).__name__

def record_event(function, phase, argument, address, extra="", read_fields=True):
    global event_count, event_sequence, trace_truncated
    event_sequence += 1
    if event_count >= MAX_EVENTS:
        if not trace_truncated:
            trace_truncated = True
            gdb.set_convenience_variable("flr0350_trace_truncated", gdb.Value(1))
            emit("FLR0350_TRACE_COVERAGE=TRUNCATED limit=%d" % MAX_EVENTS)
        return
    event_count += 1
    generation = generation_by_sync.get(address, 0)
    live = alive_by_sync.get(address, "unknown")
    fields = sync_fields(address) if read_fields else "fields=not-read"
    line = (
        "FLR0350_SYNC_EVENT seq=%d uptime=%s tid=%s function=%s phase=%s "
        "argument=%s sync=0x%x generation=%d live=%s %s%s"
        % (event_sequence, guest_uptime(), selected_tid(), function, phase,
           argument, address, generation, live, fields,
           (" " + extra) if extra else "")
    )
    object_history = history_by_sync.setdefault(address, [])
    if len(object_history) < MAX_HISTORY_PER_OBJECT:
        object_history.append(line)
    else:
        truncated_syncs.add(address)
    if matched_sync == address:
        emit(line)

def argument_summary(frame):
    parts = []
    block = frame.block()
    visited = set()
    while block is not None:
        for symbol in block:
            if not symbol.is_argument or symbol.name in visited:
                continue
            visited.add(symbol.name)
            if symbol.name not in ("fence", "signaled", "initial_signaled", "wait_flags"):
                continue
            try:
                parts.append("%s=%s" % (symbol.name, str(symbol.value(frame))))
            except Exception:
                parts.append("%s=unavailable" % symbol.name)
        block = block.superblock
    return " ".join(parts)

def log_history(address):
    records = history_by_sync.get(address, [])
    emit("FLR0350_MATCHED_HISTORY_BEGIN sync=0x%x events=%d" % (address, len(records)))
    for line in records:
        emit(line)
    if address in truncated_syncs or trace_truncated:
        emit("FLR0350_MATCHED_HISTORY_COVERAGE=UNKNOWN sync=0x%x" % address)
    else:
        emit("FLR0350_MATCHED_HISTORY_COVERAGE=COMPLETE_TO_WAIT sync=0x%x" % address)
    emit("FLR0350_MATCHED_HISTORY_END sync=0x%x" % address)

def attach_exec_gate():
    try:
        pid = gdb.selected_inferior().pid
        start, comm, exe = current_target_identity()
        ok = pid == TARGET_PID and start == TARGET_START and comm == "flutter-auto" and exe == "/usr/bin/flutter-auto"
        text = "FLR0350_SAME_PID_EXEC=%s pid=%s start=%s comm=%s exe=%s" % (
            "PASS" if ok else "FAIL", pid, start, comm, exe)
        emit(text)
        write_once(EXEC_FILE, text)
        gdb.set_convenience_variable("flr0350_exec_ok", gdb.Value(1 if ok else 0))
    except Exception as error:
        emit("FLR0350_SAME_PID_EXEC=FAIL error=%s" % type(error).__name__)
        gdb.set_convenience_variable("flr0350_exec_ok", gdb.Value(0))

def library_symbol_gate():
    try:
        lavapipe_objects = [obj for obj in gdb.objfiles()
                            if obj.filename and os.path.basename(obj.filename) == "libvulkan_lvp.so"]
        runtime_objects = [obj for obj in lavapipe_objects if getattr(obj, "owner", None) is None]
        if len(runtime_objects) != 1:
            raise RuntimeError("lavapipe-objfile-count=%d" % len(runtime_objects))
        runtime_object = runtime_objects[0]
        runtime_build_id = (runtime_object.build_id or "").lower()
        if runtime_build_id != EXPECTED_BUILD_ID:
            raise RuntimeError("runtime-build-id-mismatch")
        mismatched_debug_objects = [obj for obj in lavapipe_objects
                                    if getattr(obj, "owner", None) is runtime_object
                                    and (obj.build_id or "").lower() != EXPECTED_BUILD_ID]
        if mismatched_debug_objects:
            raise RuntimeError("separate-debug-build-id-mismatch")
        unresolved = []
        for name in REQUIRED_SYMBOLS:
            breakpoint = trace_breakpoints[name]
            if breakpoint.pending or not breakpoint.locations:
                unresolved.append(name)
        line_info = gdb.execute("info line lvp_pipe_sync_wait", to_string=True)
        if "lvp_pipe_sync.c" not in line_info:
            raise RuntimeError("wait-source-line-unavailable")
        if unresolved:
            raise RuntimeError("unresolved=" + ",".join(unresolved))
        summary = (
            "FLR0350_SYMBOL_GATE=PASS pid=%d build_id=%s resolved=%d/%d line=%s"
            % (gdb.selected_inferior().pid, runtime_build_id, len(REQUIRED_SYMBOLS),
               len(REQUIRED_SYMBOLS), line_info.strip().replace("\n", " ")[:160])
        )
        emit(summary)
        write_once(SYMBOL_FILE, summary)
        gdb.set_convenience_variable("flr0350_symbols_ok", gdb.Value(1))
    except Exception as error:
        summary = "FLR0350_SYMBOL_GATE=FAIL pid=%s reason=%s" % (
            gdb.selected_inferior().pid, str(error).replace("\n", " ")[:180])
        emit(summary)
        try:
            write_once(SYMBOL_FILE, summary)
        except Exception:
            pass
        gdb.set_convenience_variable("flr0350_symbols_ok", gdb.Value(0))

def fork_event(kind):
    try:
        emit("FLR0350_%s_EVENT parent_pid=%d uptime=%s" % (
            kind, gdb.selected_inferior().pid, guest_uptime()))
    except Exception as error:
        emit("FLR0350_%s_EVENT=UNKNOWN error=%s" % (kind, type(error).__name__))

def arm_wait_watchpoints(frame):
    global watchpoints_armed
    before = set(bp.number for bp in (gdb.breakpoints() or ()))
    try:
        signal_address = int(gdb.parse_and_eval("&sync->signaled"))
        fence_address = int(gdb.parse_and_eval("&sync->fence"))
        signal_result = gdb.execute("watch -l sync->signaled", to_string=True)
        fence_expression = "*(void **)0x%x" % fence_address
        fence_result = gdb.execute("watch -l " + fence_expression, to_string=True)
        created = [bp for bp in (gdb.breakpoints() or ()) if bp.number not in before]
        if len(created) != 2 or "Hardware watchpoint" not in signal_result or "Hardware watchpoint" not in fence_result:
            raise RuntimeError("two-hardware-watchpoints-not-confirmed")
        for bp, field, address in zip(created, ("signaled", "fence"), (signal_address, fence_address)):
            event_command = (
                'emit("FLR0350_SYNC_WRITE field=%s sync=0x%x uptime=" + guest_uptime())'
                % (field, matched_sync)
            )
            bp.commands = "silent\npython\n%s\nend\nbt 8\ncontinue" % event_command
        watchpoints_armed = True
        emit("FLR0350_WAIT_WATCHPOINTS=PASS sync=0x%x signaled=0x%x fence=0x%x" % (
            matched_sync, signal_address, fence_address))
        return True
    except Exception as error:
        emit("FLR0350_WAIT_WATCHPOINTS=FAIL sync=0x%x reason=%s" % (
            matched_sync, str(error).replace("\n", " ")[:160]))
        coverage_gaps.append("wait-field-watchpoints")
        return False

def matched_wait(frame, sync_args, stack):
    global matched_sync, matched_wait_seen
    if matched_wait_seen or "wsi_common_queue_present" not in stack:
        return
    if len(sync_args) != 1:
        coverage_gaps.append("present-wait-sync-argument-count")
        emit("FLR0350_MATCHED_WAIT=UNKNOWN sync_arg_count=%d" % len(sync_args))
        return
    argument, address = sync_args[0]
    matched_sync = address
    matched_wait_seen = True
    fields = sync_fields(address)
    tid = selected_tid()
    log_history(address)
    init_seen = any("function=lvp_pipe_sync_init " in item for item in history_by_sync.get(address, ()))
    lifetime = (
        "PASS" if init_seen and alive_by_sync.get(address) == "live"
        and address not in truncated_syncs and not trace_truncated
        else "UNKNOWN"
    )
    emit("FLR0350_MATCHED_WAIT_BEGIN pid=%d tid=%s uptime=%s argument=%s sync=0x%x generation=%d %s lifetime=%s"
         % (TARGET_PID, tid, guest_uptime(), argument, address,
            generation_by_sync.get(address, 0), fields, lifetime))
    emit(stack.rstrip())
    watchpoints_ready = arm_wait_watchpoints(frame)
    marker = (
        "FLR0350_MATCHED_WAIT=1 target_pid=%d tid=%s sync_ptr=0x%x uptime=%s "
        "lifetime=%s watchpoints=%s"
        % (TARGET_PID, tid, address, guest_uptime(), lifetime,
           "PASS" if watchpoints_ready else "FAIL")
    )
    try:
        write_once(WAIT_FILE, marker)
    except Exception as error:
        coverage_gaps.append("matched-wait-marker")
        emit("FLR0350_MATCHED_WAIT_MARKER=FAIL error=%s" % type(error).__name__)

class SyncTraceBreakpoint(gdb.Breakpoint):
    def __init__(self, name):
        self.trace_name = name
        super(SyncTraceBreakpoint, self).__init__(name, internal=True)

    def stop(self):
        global queue_submit_count
        frame = gdb.newest_frame()
        if self.trace_name == "lvp_queue_submit":
            queue_submit_count += 1
            if queue_submit_count <= 256:
                emit("FLR0350_QUEUE_SUBMIT seq=%d uptime=%s tid=%s" % (
                    queue_submit_count, guest_uptime(), selected_tid()))
            elif queue_submit_count == 257:
                emit("FLR0350_QUEUE_SUBMIT_COVERAGE=TRUNCATED limit=256")
                coverage_gaps.append("queue-submit-events-truncated")
            return False
        try:
            sync_args = sync_pointer_arguments(frame)
            extra = argument_summary(frame)
            if not sync_args:
                coverage_gaps.append(self.trace_name + "-sync-arg")
                emit("FLR0350_SYNC_ARGUMENT=UNKNOWN function=%s" % self.trace_name)
                return False
            for argument, address in sync_args:
                if self.trace_name == "lvp_pipe_sync_init":
                    generation_by_sync[address] = generation_by_sync.get(address, 0) + 1
                    alive_by_sync[address] = "live"
                elif self.trace_name == "lvp_pipe_sync_finish":
                    alive_by_sync[address] = "finishing"
                elif self.trace_name == "lvp_pipe_sync_move":
                    alive_by_sync[address] = "moving"
                record_event(self.trace_name, "entry", argument, address, extra,
                             read_fields=self.trace_name != "lvp_pipe_sync_init")
            if self.trace_name == "lvp_pipe_sync_wait":
                stack = gdb.execute("bt 16", to_string=True)
                matched_wait(frame, sync_args, stack)
            if self.trace_name in (
                "lvp_pipe_sync_init", "lvp_pipe_sync_finish", "lvp_pipe_sync_signal",
                "lvp_pipe_sync_signal_with_fence", "lvp_pipe_sync_reset",
                "lvp_pipe_sync_move",
            ):
                TraceReturnBreakpoint(frame, self.trace_name, sync_args, extra)
            return False
        except Exception as error:
            coverage_gaps.append(self.trace_name + "-handler")
            emit("FLR0350_SYNC_HANDLER=FAIL function=%s error=%s" % (
                self.trace_name, type(error).__name__))
            return False

class TraceReturnBreakpoint(gdb.FinishBreakpoint):
    def __init__(self, frame, name, sync_args, entry_extra):
        super(TraceReturnBreakpoint, self).__init__(frame, internal=True)
        self.trace_name = name
        self.sync_args = sync_args
        self.entry_extra = entry_extra

    def stop(self):
        for argument, address in self.sync_args:
            if self.trace_name == "lvp_pipe_sync_finish":
                alive_by_sync[address] = "finished"
            elif self.trace_name == "lvp_pipe_sync_move":
                alive_by_sync[address] = "moved"
            record_event(self.trace_name, "return", argument, address, self.entry_extra)
        return False

    def out_of_scope(self):
        coverage_gaps.append(self.trace_name + "-out-of-scope")
        emit("FLR0350_SYNC_RETURN=UNKNOWN function=%s" % self.trace_name)

for symbol_name in REQUIRED_SYMBOLS:
    trace_breakpoints[symbol_name] = SyncTraceBreakpoint(symbol_name)

def create_preexec_marker():
    pid = gdb.selected_inferior().pid
    start, comm, exe = current_target_identity()
    if pid != TARGET_PID or start != TARGET_START or comm != "sh":
        raise gdb.GdbError("FLR0350 pre-exec target identity mismatch")
    content = "FLR0350_EXEC_GATE=PASS target_pid=%d gdb_pid=%d" % (pid, GDB_PID)
    write_once(ARMED_FILE, content)
    emit("FLR0350_GDB_ARMED=PASS target_pid=%d gdb_pid=%d comm=%s exe=%s" % (
        pid, GDB_PID, comm, exe))

end

catch exec
commands
silent
python
attach_exec_gate()
end
if $flr0350_exec_ok
continue
else
kill
end
end

catch fork
commands
silent
python
fork_event("FORK")
end
continue
end

catch vfork
commands
silent
python
fork_event("VFORK")
end
continue
end

catch load libvulkan_lvp.so
commands
silent
python
library_symbol_gate()
end
if $flr0350_symbols_ok
continue
else
kill
end
end

python
create_preexec_marker()
create_stopped_attach_authorization()
wait_for_go_record()
end

continue
python
emit("FLR0350_GDB_CONTINUE_RETURN uptime=%s matched_wait=%s watchpoints=%s truncated=%s gaps=%d" % (
    guest_uptime(), str(matched_wait_seen), str(watchpoints_armed),
    str(trace_truncated), len(coverage_gaps)))
for gap in coverage_gaps[:32]:
    emit("FLR0350_COVERAGE_GAP=%s" % gap)
if len(coverage_gaps) > 32:
    emit("FLR0350_COVERAGE_GAPS_TRUNCATED count=%d" % len(coverage_gaps))
end
detach
