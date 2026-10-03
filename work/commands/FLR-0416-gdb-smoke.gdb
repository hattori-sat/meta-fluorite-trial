set pagination off
set confirm off
python
import gdb
import sys
sys.path.insert(0, "/run/user/1001/flr0421-0001")
import flr0416_gdb_observer
import flr0416_gdb_callback
assert hasattr(gdb, "BP_HARDWARE_BREAKPOINT")
assert issubclass(flr0416_gdb_callback.FirstHitBreakpoint, gdb.Breakpoint)
print("FLR0416_GDB_PYTHON_API=PASS")
end
quit
