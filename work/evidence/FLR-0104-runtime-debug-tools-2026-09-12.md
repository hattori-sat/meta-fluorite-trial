# FLR-0104 evidence — reproducible runtime debug tools (2026-09-12)

## Outcome

The project-owned diagnostic packagegroup was built into a new exact
`agl-ivi-image-flutter` image on the fixed Mini PC build. The guest contains
GDB, gdbserver, coredumpctl, LLVM symbolizer, syscall/profiling tools, and
targeted Flutter/Filament/Mesa/Clang debug packages. One QMP-first QEMU boot
verified the tools and coredump configuration, captured a QMP-only frame, and
teardown left no residual target or QMP socket.

This ticket establishes diagnostic readiness only. It does not claim that the
production Fluorite 3D fault is fixed.

## Baseline facts

- The prior exact rootfs already contained `gdb`, `gdbserver`, `coredumpctl`,
  `strace`, `perf`, and `eu-stack` through AGL image features/packagegroups.
- The prior exact rootfs did not contain `/usr/bin/llvm-symbolizer`.
- Mini pkgdata maps `/usr/bin/llvm-symbolizer` to the `clang` package.
- The current AGL image metadata contained `tools-debug`, `tools-profile`, and
  `packagegroup-agl-core-devel`, but those inputs were not a project-owned
  complete contract.
- An earlier inventory claimed the ordinary tools were absent. The exact-path
  recheck disproved that claim; it is recorded as an observation error.

## Implementation

The layer now contains `packagegroup-fluorite-runtime-debug`, included by
`conf/include/fluorite-common.inc`. Its explicit runtime dependencies are:

```text
gdb gdbserver strace perf elfutils binutils systemd clang
clang-dbg mesa-dbg flutter-auto-dbg flutter-engine-dbg filament-vk-dbg
```

The packagegroup is project-owned and does not enable global `dbg-pkgs`; the
debug-symbol selection is limited to the runtime graphics stack under test.
This is a Yocto image/packagegroup integration change, not an upstream source
change, so no artificial Devtool source patch was generated.

Focused packagegroup tests and the full repository verification passed.

## Build identity

- Layer commit: `14af6776e2c4c10748e360734c19732dd56ff271`.
- Bundle SHA-256:
  `ba71ce0b05cb129a494d9b752d8406354d83555d00c33e5011d416d30d12ad24`.
- Receiver: `$BUILD_RECEIVER`, exact tip matches the layer commit.
- Build role: `$BUILD_DIR`; TMPDIR role: `$BUILD_TMPDIR`.
- Target: `qemux86-64`; image: `agl-ivi-image-flutter`.
- Full build: `11758/11758` tasks succeeded. BitBake reported 16 warnings,
  including existing forced-task taint warnings; no task failed.
- Exact rootfs:
  `$BUILD_TMPDIR/deploy/images/qemux86-64/agl-ivi-image-flutter-qemux86-64.rootfs-20260912011117.ext4`
- Rootfs size: `6787766272` bytes.
- Rootfs SHA-256:
  `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`.
- Manifest SHA-256:
  `27c611211c8950aae40ac970ab798cf5c481aae924c617e89c20614def5dfbc2`.
- Qemuboot SHA-256:
  `ba6711550d96677f66e99f3a06af308a61c1e58a7b776f7489b42c8cc470136d`.
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.

## Manifest evidence

The new manifest contains these requested package entries:

```text
binutils corei7_64 2.42
clang corei7_64 18.1.8
clang-dbg corei7_64 18.1.8
elfutils corei7_64 0.191
filament-vk-dbg corei7_64 1.65.4
flutter-auto-dbg corei7_64 2.0
flutter-engine-dbg corei7_64 3.38.3
gdb corei7_64 14.2
gdbserver corei7_64 14.2
mesa-dbg corei7_64 24.0.7
perf qemux86_64 6.6.111
strace corei7_64 6.7
systemd corei7_64 255.21
```

## Rootfs path evidence

`debugfs` inspection of the exact new rootfs reports these paths present:

```text
/usr/bin/gdb
/usr/bin/gdbserver
/usr/bin/coredumpctl
/usr/bin/llvm-symbolizer
/usr/bin/strace
/usr/bin/perf
/usr/bin/eu-stack
/usr/bin/addr2line
/usr/bin/readelf
/usr/lib/.debug/libvulkan_lvp.so
/usr/share/flutter/3.38.3/release/lib/.debug/libflutter_engine.so
/usr/bin/.debug/flutter-auto
```

## Guest runtime evidence

Probe definition: [FLR-0104 guest runtime tool probe](../commands/FLR-0104-runtime-tool-probe.md).

The corrected serial probe passed with `command_status=0` and resolved:

```text
gdb=/usr/bin/gdb
gdbserver=/usr/bin/gdbserver
coredumpctl=/usr/bin/coredumpctl
llvm-symbolizer=/usr/bin/llvm-symbolizer
strace=/usr/bin/strace
perf=/usr/bin/perf
eu-stack=/usr/bin/eu-stack
addr2line=/usr/bin/addr2line
readelf=/usr/bin/readelf
```

Additional output:

- GDB target: `x86_64-agl-linux`.
- LLVM symbolizer: version `18.1.8`, optimized build.
- `coredumpctl list --no-pager`: no coredumps found in this tool-only boot.
- `core_pattern`: `|/usr/lib/systemd/systemd-coredump %P %u %g %s %t %c %h %d`.
- `ulimit -c`: `unlimited`.

## QMP evidence

- QEMU preflight/start/guest-ready: PASS.
- QMP-only frame: `$RECEIVER/evidence/flr0104-runtime-debug-tools/qmp-tools-late.ppm`.
- Frame SHA-256:
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- QMP `quit`: accepted.
- Residual target processes: `0`.
- Residual QMP sockets: `0`.

## Failed observations retained

1. The first focused test matched `dbg-pkgs` in a comment. The comment was
   revised and the focused test passed.
2. The first `make verify` stopped at the project-layer file-count/hash lock.
   The authorized baseline lock was updated for the new layer file and the
   full verification passed.
3. The first artifact inventory assumed an unavailable manifest symlink. The
   timestamp-matched manifest was then checked explicitly.
4. The first guest probe used unsupported `coredumpctl list --boot`. The
   corrected `list --no-pager` probe passed.

## Classification

| Gate | Result |
| --- | --- |
| Project-owned packagegroup in effective `IMAGE_INSTALL` | PASS |
| Full Mini image build | PASS |
| GDB/gdbserver | PASS |
| coredumpctl/systemd-coredump configuration | PASS |
| LLVM symbolizer | PASS |
| strace/perf/elfutils/binutils | PASS |
| Flutter/Mesa/Filament targeted debug files | PASS |
| QMP-only frame | PASS |
| QMP teardown / residual check | PASS |
| Production 3D fix | NOT IN SCOPE; FLR-0103 remains UNKNOWN |
