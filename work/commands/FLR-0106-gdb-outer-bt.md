# FLR-0106 bounded outer-caller GDB capture

This command reuses the FLR-0104 debug image and observes the production
Example Demo. It sets one pending breakpoint at
`llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)`, records one PC/register
sample and a bounded 16-frame backtrace, disables the breakpoint, detaches,
and exits. It does not run guest `addr2line`, a full all-thread backtrace, or
an unbounded log transfer while the application is live.

The guest loopback endpoint is used so no host address is recorded. The
temporary GDB command file exists only inside the guest `/tmp` during this
run.

```sh
printf '%s\n' 'set pagination off' 'set confirm off' 'set breakpoint pending on' 'set debug-file-directory /usr/lib/.debug' 'target remote localhost:23458' 'break llvm::CmpInst::isOrdered' 'commands 1' 'silent' 'printf "FLR0106_GDB_BREAKPOINT_HIT pc=%p\\n", $pc' 'x/i $pc' 'printf "FLR0106_REGS rip=%p rsp=%p rdi=%p rsi=%p rdx=%p rcx=%p\\n", $rip, $rsp, $rdi, $rsi, $rdx, $rcx' 'bt 16' 'disable 1' 'detach' 'quit' 'end' 'continue' > /tmp/flr0106-outer-bt.gdb; rm -f /tmp/flr0106-gdbserver.log /tmp/flr0106-gdb-client.log /tmp/flr0106-gdbserver.pid /tmp/flr0106-gdb-client.pid; su - agl-driver -c 'env FLUORITE_SCENE_PASS_TRACE=1 FLUORITE_PRESENT_TRACE=1 FLUORITE_DRIVER_LIFECYCLE_TRACE=1 nohup /usr/bin/gdbserver --once localhost:23458 /usr/bin/flutter-auto -b /usr/share/flutter/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/3.38.3/release >/tmp/flr0106-gdbserver.log 2>&1 & echo $! >/tmp/flr0106-gdbserver.pid'; nohup sh -c 'sleep 2; /usr/bin/gdb --batch --nx --nh -x /tmp/flr0106-outer-bt.gdb >/tmp/flr0106-gdb-client.log 2>&1' >/dev/null 2>&1 & echo $! >/tmp/flr0106-gdb-client.pid; echo gdbserver_pid=$(cat /tmp/flr0106-gdbserver.pid) gdb_client_pid=$(cat /tmp/flr0106-gdb-client.pid)
```
