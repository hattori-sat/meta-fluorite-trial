set pagination off
set height 0
set width 0
set confirm off
set non-stop off
handle SIGINT stop print nopass
set breakpoint always-inserted on
python
import gdb
import sys
sys.path.insert(0, "/run/user/1001/flr0418-0001")
import flr0416_gdb_callback as flr0416
assert hasattr(gdb, "BP_HARDWARE_BREAKPOINT")
end
catch load libLLVM\.so\.18\.1
commands 1
silent
python
try:
    flr0416.arm_target_breakpoint()
except (Exception, KeyboardInterrupt) as error:
    flr0416.abort_run("arm", error)
end
disable 1
end
run
python
try:
    flr0416.record_load_stop_and_wait()
except (Exception, KeyboardInterrupt) as error:
    flr0416.abort_run("load_stop", error)
end
continue
python
try:
    flr0416.capture_first_stop_and_wait()
except (Exception, KeyboardInterrupt) as error:
    flr0416.abort_run("first_stop", error)
end
continue
python
try:
    flr0416.capture_after_continue()
except (Exception, KeyboardInterrupt) as error:
    flr0416.record_failure("after_continue", error)
end
quit
