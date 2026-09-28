# FLR-0105 bounded LLVM-entry breakpoint

This command observes the production Example Demo on the fixed debug image.
It sets one pending breakpoint at
`llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)`, records one PC/register/
short-backtrace sample, disables the breakpoint, detaches, and exits. It does
not run guest `addr2line`, full all-thread backtraces, or an unbounded log
transfer while the application is live.

The serial command file creates the temporary GDB command file inside the
guest, starts one `gdbserver`, and starts one batch GDB client. The guest
loopback endpoint is intentionally used so no host address is recorded.

```sh
printf '%s\n' 'set pagination off' 'set confirm off' 'set breakpoint pending on' 'set debug-file-directory /usr/lib/.debug' 'target remote localhost:23457' 'break llvm::CmpInst::isOrdered' 'commands 1' 'silent' 'printf "FLR0105_GDB_BREAKPOINT_HIT pc=%p\\n", $pc' 'x/i $pc' 'printf "FLR0105_REGS rip=%p rsp=%p rdi=%p rsi=%p rdx=%p rcx=%p\\n", $rip, $rsp, $rdi, $rsi, $rdx, $rcx' 'bt 8' 'disable 1' 'detach' 'quit' 'end' 'continue' > /tmp/flr0105-breakpoint.gdb; rm -f /tmp/flr0105-gdbserver.log /tmp/flr0105-gdb-client.log /tmp/flr0105-gdbserver.pid /tmp/flr0105-gdb-client.pid; su - agl-driver -c 'env FLUORITE_SCENE_PASS_TRACE=1 FLUORITE_PRESENT_TRACE=1 FLUORITE_DRIVER_LIFECYCLE_TRACE=1 nohup /usr/bin/gdbserver --once localhost:23457 /usr/bin/flutter-auto -b /usr/share/flutter/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/3.38.3/release >/tmp/flr0105-gdbserver.log 2>&1 & echo $! >/tmp/flr0105-gdbserver.pid'; nohup sh -c 'sleep 2; /usr/bin/gdb --batch --nx --nh -x /tmp/flr0105-breakpoint.gdb >/tmp/flr0105-gdb-client.log 2>&1' >/dev/null 2>&1 & echo $! >/tmp/flr0105-gdb-client.pid; echo gdbserver_pid=$(cat /tmp/flr0105-gdbserver.pid) gdb_client_pid=$(cat /tmp/flr0105-gdb-client.pid)
```

After a bounded wait, use focused extraction only:

```sh
cat /tmp/flr0105-gdbserver.pid /tmp/flr0105-gdb-client.pid 2>/dev/null || true
ps -o pid,ppid,stat,rss,etime,comm,args -p <server-pid>,<client-pid>,<app-pid>
grep -nE 'FLR0105_GDB_BREAKPOINT_HIT|Program received|SIG(SEGV|BUS|ABRT)|No symbol|Breakpoint|FEngine::loop' /tmp/flr0105-gdb-client.log /tmp/flr0105-gdbserver.log 2>/dev/null | tail -80
```
