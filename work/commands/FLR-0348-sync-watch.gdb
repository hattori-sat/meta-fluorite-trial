set pagination off
set confirm off
set print thread-events off
python
import gdb

def find_waiter():
    for thread in gdb.selected_inferior().threads():
        if thread.name != "FEngine::loop":
            continue
        thread.switch()
        try:
            stack = gdb.execute("bt 8", to_string=True)
        except gdb.error:
            continue
        if "lvp_pipe_sync_wait_locked" in stack:
            return thread, stack
    return None, ""

def select_wait_frame(thread):
    thread.switch()
    frame = gdb.selected_frame()
    while frame is not None:
        if "lvp_pipe_sync_wait_locked" in (frame.name() or ""):
            frame.select()
            return frame
        frame = frame.older()
    return None

gdb.set_convenience_variable("flr0348_ready", gdb.Value(0))
fence_value_expression = None
thread, stack = find_waiter()
if thread is None:
    print("FLR0348_WATCH_SETUP_FAIL=waiter-not-found")
else:
    frame = select_wait_frame(thread)
    if frame is None:
        print("FLR0348_WATCH_SETUP_FAIL=wait-frame-not-found")
    else:
        try:
            sync = gdb.parse_and_eval("sync")
            sync_address = int(sync)
            signal_address = int(gdb.parse_and_eval("&sync->signaled"))
            fence_address = int(gdb.parse_and_eval("&sync->fence"))
            fence_value_expression = "*(void **)0x%x" % fence_address
            print("FLR0348_WAIT_TID=%s" % thread.ptid[1])
            print("FLR0348_SYNC_PTR=0x%x" % sync_address)
            print("FLR0348_SIGNAL_FIELD_ADDR=0x%x" % signal_address)
            print("FLR0348_SIGNAL_FIELD_OFFSET=%d" % (signal_address - sync_address))
            print("FLR0348_SIGNAL_INITIAL=%s" % gdb.parse_and_eval("sync->signaled"))
            print("FLR0348_FENCE_FIELD_ADDR=0x%x" % fence_address)
            print("FLR0348_FENCE_FIELD_OFFSET=%d" % (fence_address - sync_address))
            print("FLR0348_FENCE_INITIAL=%s" % gdb.parse_and_eval(fence_value_expression))
            print(stack)
        except gdb.error as error:
            detail = str(error).replace("\n", " ")[:240]
            print("FLR0348_WATCH_SETUP_FAIL=%s" % type(error).__name__)
            print("FLR0348_WATCH_SETUP_DETAIL=%s" % detail)
        else:
            signal_armed = False
            fence_armed = False
            try:
                result = gdb.execute("watch -l sync->signaled", to_string=True)
                signal_armed = True
                if result:
                    print(result.rstrip())
                print("FLR0348_SIGNAL_WATCH_ARMED=1")
            except gdb.error as error:
                detail = str(error).replace("\n", " ")[:240]
                print("FLR0348_SIGNAL_WATCH_SETUP_FAIL=%s" % type(error).__name__)
                print("FLR0348_SIGNAL_WATCH_SETUP_DETAIL=%s" % detail)
            try:
                result = gdb.execute(
                    "watch -l " + fence_value_expression, to_string=True
                )
                fence_armed = True
                if result:
                    print(result.rstrip())
                print("FLR0348_FENCE_WATCH_ARMED=1")
            except gdb.error as error:
                detail = str(error).replace("\n", " ")[:240]
                print("FLR0348_FENCE_WATCH_SETUP_FAIL=%s" % type(error).__name__)
                print("FLR0348_FENCE_WATCH_SETUP_DETAIL=%s" % detail)
            if signal_armed and fence_armed:
                gdb.set_convenience_variable("flr0348_ready", gdb.Value(1))
                print("FLR0348_WATCHPOINTS_ARMED=1")
                # Keep the established FLR-0346 arm-poll compatible.
                print("FLR0344_WATCHPOINTS_ARMED=1")
end
if $flr0348_ready
continue
python
writer = gdb.selected_thread()
if writer is None:
    print("FLR0348_WRITER_TID=unknown")
else:
    print("FLR0348_WRITER_TID=%s" % writer.ptid[1])
end
bt 12
python
thread, stack = find_waiter()
if thread is None:
    print("FLR0348_POST_STOP_WAITER=not-found")
else:
    frame = select_wait_frame(thread)
    if frame is None:
        print("FLR0348_POST_STOP_WAITER=frame-not-found")
    elif fence_value_expression is None:
        print("FLR0348_POST_STOP_READ_FAIL=fence-address-unavailable")
    else:
        try:
            print("FLR0348_POST_STOP_TID=%s" % thread.ptid[1])
            print("FLR0348_SIGNAL_AFTER=%s" % gdb.parse_and_eval("sync->signaled"))
            print("FLR0348_FENCE_AFTER=%s" % gdb.parse_and_eval(fence_value_expression))
            print(stack)
        except gdb.error as error:
            detail = str(error).replace("\n", " ")[:240]
            print("FLR0348_POST_STOP_READ_FAIL=%s" % type(error).__name__)
            print("FLR0348_POST_STOP_READ_DETAIL=%s" % detail)
end
end
detach
