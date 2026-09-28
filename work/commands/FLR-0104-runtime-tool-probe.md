# FLR-0104 guest runtime tool probe

Use this as the single-line command passed to the existing bounded
`qemu-runtime-harness.sh serial-exec` operation. It keeps the observation
small: command paths, GDB target configuration, LLVM symbolizer version,
coredump inventory, core pattern, and core limit.

```sh
for c in gdb gdbserver coredumpctl llvm-symbolizer strace perf eu-stack addr2line readelf; do printf '%s=' "$c"; command -v "$c"; done; echo GDB_CONFIG; gdb --configuration | sed -n '1,8p'; echo LLVM_SYMBOLIZER; llvm-symbolizer --version; echo COREDUMP_LIST; coredumpctl list --no-pager; echo CORE_PATTERN; cat /proc/sys/kernel/core_pattern; echo CORE_LIMIT; ulimit -c
```

The `--boot` option is intentionally omitted because this image's
`coredumpctl` does not support it.
