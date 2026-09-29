# FLR-0102 evidence — production scene draw seam (2026-09-12)

## Outcome

The Devtool-generated scene-pass probe was built and exercised on the fixed
Mini image. The self-made fixture produced visible native 3D pixels, while the
production Example Demo remained native-black. Production scene command
execution completed before the already-known queue-present fault boundary.
This is a diagnostic success, not a production 3D success.

## Identity

- Layer commit: `c309ca2ac83809c7b28be59ed0ab105542c38c26`
- Bundle SHA-256: `85e2015268b9fab7ced8a7be34353caf0de63f058f3fa0141781ee1dcb8072c8`
- Mini receiver: `$RECEIVER`, exact layer tip above
- Image: `agl-ivi-image-flutter`, `MACHINE=qemux86-64`, `DISTRO=poky-agl`
- Kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Rootfs SHA-256: `ba360b950bd591def03c31b4447d4aebec735a15ed27d0b58403b2eb4f07dd5f`
- qemuboot SHA-256: `6a291cb941489b69cb39a22689591c9ddbd1d5dedaeb6dfb66428873e8af23fe`
- Raw evidence root: `$RECEIVER/evidence/flr0102-scene-draw-seam/`

## Build gates

- Mac Podman status and mount/reuse contract: PASS
- Official Devtool `finish --mode patch`: PASS
- Mac `filament-vk do_patch`: PASS
- Mini `filament-vk do_patch`: PASS, 104/104 tasks
- Mini `filament-vk do_compile`: PASS, 1965/1965 tasks
- Mini `agl-ivi-image-flutter`: PASS, 11748/11748 tasks
- Warnings were existing forced-task taint and static-archive buildpath QA;
  no 0187 compile or patch error occurred.

## Runtime contract

- One QEMU, fixed `$QEMU_RUN` alias, snapshot rootfs, QMP-first harness.
- QEMU preflight/start and guest-ready: PASS.
- Guest BUNDLE: installed Example Demo release with `app_id=fluorite`.
- The first host-side read mistakenly inspected Mini host paths instead of the
  guest. It was excluded from the verdict. Subsequent guest state and logs
  were obtained only through serial-exec and retained in the evidence root.
- The first kernel query used unsupported BusyBox `dmesg -T`; it was excluded.
  The BusyBox-compatible retry succeeded.
- QMP capabilities negotiation, `quit`, and residual checks: PASS.
  No QEMU/runqemu/flutter-auto target or QMP socket remained.

## Control — self-made fixture

Launch variables were `FLUORITE_NATIVE_PURE_FIXTURE=1`,
`FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`, and `FLUORITE_SCENE_PASS_TRACE=1`, with
the guest BUNDLE launched as `agl-driver` using the registered Wayland user.

- QMP late PPM: `control-late.ppm`
- PPM SHA-256: `833d60726dbd8b8fc443f27ff0769e18eca1dbdac5e69b96de5d6a28a73050b6`
- Native region `[300,80,620,360]`: `41750/223200`, bbox `[501,278,278,162]`
- HUD region `[200,100,400,250]`: `6201/100000`
- QMP video frames: `control-frames/`, 6 frames, 6 unique SHA-256 values
- Scene markers: `FLUORITE_SCENE_PASS_EXECUTE_BEGIN/END` observed
- Queue-present return marker: observed with result `0`
- Verdict: visible native fixture 3D PASS

## Production — Example Demo

The production BUNDLE was launched after the fixture PID was stopped and a
guest-side process guard confirmed no existing flutter-auto. Only
`FLUORITE_SCENE_PASS_TRACE=1` and the existing lifecycle trace were enabled.

- QMP late PPM: `production-late.ppm`
- PPM SHA-256: `9d23fb4b1bb2de7e321dcc2d30ab14160da203e322a5f0168eb30c3c3f40e141`
- Native region `[300,80,620,360]`: `0/223200`
- HUD region `[200,100,400,250]`: `1214/100000`, bbox `[200,113,29,66]`
- QMP video frames: `production-frames/`, 6 frames, 6 unique SHA-256 values
- Scene pass markers: BEGIN/END observed, including production command counts
  `0`, `1`, and `552`
- Engine markers: execute enter, queue wait enter, and execute-after-wait
  `count=168` observed
- Present boundary: submit and `QUEUE_PRESENT_BEGIN` observed; no retained
  queue-present return was observed
- Kernel: page fault/Oops in `FEngine::loop`, with RIP
  `0x7f53d399d541` and CR2 `0x6d5d3750`
- Verdict: 2D HUD PASS; production native 3D FAIL/not observed

## Decision

The scene draw/command-recording seam is not the first missing operation:
production reaches and completes it, while the fixture completes the same
instrumented seam and produces native pixels. Keep 0187 as diagnostic history;
do not present it as a fix. Continue with a separate ticket for the common
post-scene Vulkan/LLVM present boundary.
