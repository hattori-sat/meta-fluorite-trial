# FLR-0103 guest GDB production launch

This is the single-line command passed to the bounded guest
`qemu-runtime-harness.sh serial-exec` operation. It runs the production
Example Demo under `gdbserver`, then connects the guest GDB in batch mode.

```sh
rm -f /tmp/flr0103-gdbserver.log /tmp/flr0103-gdb-client.log /tmp/flr0103-gdbserver.pid /tmp/flr0103-gdb-client.pid; su - agl-driver -c 'env FLUORITE_SCENE_PASS_TRACE=1 FLUORITE_PRESENT_TRACE=1 FLUORITE_DRIVER_LIFECYCLE_TRACE=1 nohup /usr/bin/gdbserver --once localhost:23456 /usr/bin/flutter-auto -b /usr/share/flutter/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/3.38.3/release >/tmp/flr0103-gdbserver.log 2>&1 & echo $! >/tmp/flr0103-gdbserver.pid'; nohup sh -c 'sleep 2; /usr/bin/gdb --batch --nx --nh -ex "set pagination off" -ex "set confirm off" -ex "target remote localhost:23456" -ex "continue" -ex "info program" -ex "thread apply all bt full" -ex "info sharedlibrary" -ex "detach" -ex "quit"' >/tmp/flr0103-gdb-client.log 2>&1 & echo $! >/tmp/flr0103-gdb-client.pid; echo gdbserver_pid=$(cat /tmp/flr0103-gdbserver.pid) gdb_client_pid=$(cat /tmp/flr0103-gdb-client.pid)
```

The command uses only the existing installed Example Demo and neutral
diagnostic markers; it does not change rendering or synchronization behavior.
