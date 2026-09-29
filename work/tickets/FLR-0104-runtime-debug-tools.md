# FLR-0104 — add reproducible runtime debug tools

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Yocto image + target-validation roles
- Created: 2026-09-12
- Depends on: [FLR-0103](FLR-0103-trace-post-scene-vulkan-present-boundary.md)
- Working log: `work/logs/2026-09-12-flr0104.md`

## Problem

The production Fluorite path reaches the post-scene Vulkan present boundary and
reports an `FEngine::loop` page fault. The existing image already contains
most ordinary debug tools through AGL image features, but it does not contain
`llvm-symbolizer`, and the project layer does not explicitly own the complete
runtime diagnostic set. This prevents a reproducible guest-side symbol/core
diagnosis.

## Work unit

Add a project-owned Yocto packagegroup to the shared Fluorite validation image,
build it on the fixed Mini PC build, and verify the requested tools and
targeted graphics/runtime debug symbols inside one new exact image. This ticket
does not change rendering, present, synchronization, light, camera, or
compositor behavior.

## Success criteria

- `meta-fluorite-trial` explicitly includes a runtime-debug packagegroup in the
  shared image include.
- The image contains `gdb`, `gdbserver`, `coredumpctl`, `llvm-symbolizer`,
  `strace`, `perf`, `eu-stack`, `addr2line`, and `readelf`.
- Targeted debug packages for LLVM/Clang, Mesa/llvmpipe, Flutter, and the
  Filament runtime are present without enabling global `dbg-pkgs`.
- Mini metadata, packagegroup resolution, and full image build pass using the
  existing receiver/build/TMPDIR/cache roles.
- One QEMU guest-side tool probe and QMP teardown pass with no residual target
  or QMP socket. Any production fault remains a separate UNKNOWN/diagnostic
  result.

## Facts

- The exact current rootfs recheck found `/usr/bin/gdb`, `/usr/bin/gdbserver`,
  `/usr/bin/coredumpctl`, `/usr/bin/strace`, `/usr/bin/perf`, and
  `/usr/bin/eu-stack` present.
- The same rootfs did not contain `/usr/bin/llvm-symbolizer`.
- The current effective image metadata already contains AGL `tools-debug`,
  `tools-profile`, and `packagegroup-agl-core-devel`; those inputs explain the
  ordinary tools but do not make the project-owned contract explicit.
- Yocto pkgdata maps `/usr/bin/llvm-symbolizer` to the `clang` package.
- The locked build metadata provides `clang-dbg`, `mesa-dbg`,
  `flutter-auto-dbg`, `flutter-engine-dbg`, and `filament-vk-dbg` packages.
- The previous inventory statement that all of `gdb`, `gdbserver`,
  `coredumpctl`, `strace`, `perf`, and `eu-stack` were absent is rejected by
  this exact-path recheck; it was an observation error, not a source change.

## Inferences

- Adding only another AGL image feature would not close the measured gap,
  because the current image already resolves the relevant features while
  lacking `llvm-symbolizer`.
- A project packagegroup is the smallest reproducible integration point: it
  makes the tool contract visible in `meta-fluorite-trial` while avoiding a
  global debug-symbol expansion.
- The debug symbols are diagnostic inputs; their presence does not prove that
  the production 3D path or the coredump producer is fixed.

## Hypotheses

1. Explicitly installing `clang` will provide `llvm-symbolizer`, allowing the
   current `libLLVM.so.18.1` boundary to be symbolized in the guest workflow.
2. Targeted Mesa/Flutter/Filament debug packages will make a future GDB/core
   capture more useful without the storage cost of `dbg-pkgs` for every image
   package.
3. The missing tool set is an image reproducibility gap, not the cause of the
   existing production native-black/present-boundary fault.

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | ordinary tools mostly present; LLVM symbolizer absent | rootfs exact-path probe, pkgdata |
| Where | shared image include and runtime rootfs | BitBake `IMAGE_INSTALL`, guest command paths |
| When | current post-FLR-0103 fault diagnosis | exact image/tool probe timestamp |
| Who | Yocto image, runtime diagnosis, target-validation roles | working log |
| How | project packagegroup → BitBake image → one QEMU guest | bundle/build/QMP evidence |

## PDCA

### Plan

1. Confirm the current tool set and provider ownership against the locked Mini
   metadata.
2. Add a project-owned packagegroup with runtime tools and targeted debug
   symbols; keep rendering semantics unchanged.
3. Bundle the layer commit, build the exact image on Mini, and verify guest
   tool paths plus coredump configuration.
4. Hand the resulting evidence to the paused FLR-0103 present-boundary
   diagnosis.

### Do

- Canonical repository check passed.
- The residual QEMU from the interrupted FLR-0103 maps run was closed through
  QMP with `quit=accepted` and `residual_targets=0 residual_qmp=0`.
- Mini metadata resolved the project-owned packagegroup and its explicit
  dependencies.
- The packagegroup was added to `fluorite-common.inc`, and the focused test
  plus full repository verification passed.
- The exact layer commit was transferred to the fixed Mini receiver through
  the existing bundle helper.
- The full image build completed all `11758/11758` tasks using the existing
  build/TMPDIR/cache roles.
- One QEMU booted the new image; the guest tool probe and QMP-only capture
  completed, then QMP teardown left no residual target or socket.

### Check

The baseline tool check was partial: ordinary debugger/syscall/coredump tools
were present, but `llvm-symbolizer` was absent. The new image contains all
requested command paths and targeted debug packages; the guest probe confirms
`llvm-symbolizer 18.1.8`, `core_pattern` routed to systemd-coredump, and an
unlimited core limit. The exact artifact, manifest, QMP frame, and teardown
results are recorded in the evidence index.

### Act

The tooling unit is complete. Resume FLR-0103 with the new guest-side GDB,
coredumpctl, LLVM symbolizer, and targeted graphics debug symbols; this ticket
does not claim that production 3D is fixed.

## UNKNOWN

- Whether the targeted debug packages contain usable symbols for every loaded
  binary in the final stripped image.
- Whether systemd-coredump persists a usable `flutter-auto` core during the
  next production reproduction.
- Whether a symbolized backtrace will identify the producer of the existing
  LLVM fault or only improve the evidence quality.

## Check result

- Packagegroup/provider metadata: PASS.
- Full image: PASS, `11758/11758` tasks; 16 warnings were reported by BitBake,
  including existing forced-task taint warnings, with no failed task.
- New rootfs: `$BUILD_TMPDIR/deploy/images/qemux86-64/agl-ivi-image-flutter-qemux86-64.rootfs-20260912011117.ext4`, size `6787766272`, SHA-256 `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`.
- New manifest: SHA-256 `27c611211c8950aae40ac970ab798cf5c481aae924c617e89c20614def5dfbc2`.
- New qemuboot: SHA-256 `ba6711550d96677f66e99f3a06af308a61c1e58a7b776f7489b42c8cc470136d`.
- Guest command paths: PASS for GDB, gdbserver, coredumpctl,
  llvm-symbolizer, strace, perf, eu-stack, addr2line, and readelf.
- Guest coredump readiness: PASS for systemd-coredump `core_pattern` and
  `ulimit -c unlimited`; no coredump was expected in the tool-only boot.
- QMP-only frame: `$RECEIVER/evidence/flr0104-runtime-debug-tools/qmp-tools-late.ppm`, SHA-256 `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- QMP teardown: PASS with `residual_targets=0 residual_qmp=0`.

## Failed observations retained

- The first focused Python test failed because its negative assertion matched
  the phrase in a comment; the comment was corrected and the test passed.
- The first full repository verification failed only because the authorized
  baseline lock still had the previous layer file count and tree hashes; the
  lock was updated for the new project layer file and `make verify` passed.
- The first artifact inventory assumed a non-existent manifest symlink and
  did not produce a valid manifest hash; the timestamp-matched manifest was
  then checked explicitly and passed.
- The first guest probe used unsupported `coredumpctl list --boot`; the failure
  was retained, the command was changed to `coredumpctl list --no-pager`, and
  the corrected probe passed.

## Evidence

- Baseline and subsequent build/runtime results: `work/evidence/FLR-0104-runtime-debug-tools-2026-09-12.md`.
