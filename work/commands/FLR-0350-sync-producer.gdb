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

RUN_DIR = "/run/user/1001"
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
