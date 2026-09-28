# FLR-0072 — reproduce p9 trace-visible condition

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan roles
- Created: 2026-09-11
- Depends on: [FLR-0071](FLR-0071-separate-trace-timing-side-effect.md)
- Working log: `work/logs/2026-09-11-flr0072.md`

## Work unit

Reproduce or falsify the earlier FLR-0070 p9 result in which the native light
state trace coincided with visible 3D pixels. FLR-0071 repeated the same
profile on the new `a94f877` image and stayed black in all three conditions.
This ticket first compares image identity, patch stack, exact app launch,
compositor owner, QEMU profile, and capture timing. It does not introduce a
product fix or treat a diagnostic side effect as one.

## Success criteria

- Reuse the fixed Mini build/TMPDIR, one QEMU at a time, and the existing QMP
  evidence root; do not create duplicate containers, volumes, build trees, or
  TMPDIRs.
- Identify the exact p9 rootfs and compare its recipe/patch identity with the
  current `a94f877` rootfs, without changing source or deleting caches.
- Replay p9 and p3 with explicit, recorded `agl-driver` environment, bundle,
  compositor owner, wait interval, and QMP frame timing.
- Retain QMP-only frames, runtime logs, hashes, process state, and clean QMP
  teardown for every independently valid condition.
- If the positive cannot be reproduced, record UNKNOWN at the first missing
  identity or runtime condition and split the next smallest discriminator.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0070 p9 used the prior fixed image and reported
  `native_entity=5 light_component=true instance_valid=true
  scene_has_entity=true scene_light_count=1`, with final 3D region
  `5510/223200`.
- FLR-0071 p1/p2/p3 used rootfs SHA-256
  `0d8df09ac176eaf4c301fb6761ee2a50843f4d27ae49c602eed63dababb08a4f`.
  Trace-disabled, 10ms delay-only, and native-state-trace conditions all had
  five QMP frames with 3D region `0/223200`.
- FLR-0071 p3 reproduced valid native light state but not visible pixels.
- FLR-0071 p4 repeated the native-state-trace condition on the same rootfs and
  also produced five QMP frames with 3D region `0/223200`; final frame SHA-256
  was `60488daf59c1ca9183e14754b614bccbe5d44c172f6734e2e4df1d44cc2d7c22`.
- p4 runtime log SHA-256 was
  `cd9f5b9e860a20b27ee79c43fc058652848d59343bcb0718adcbb899961399bf` and
  again contained valid native light state. Its HUD region changed
  `929/100000` pixels.
- p4 used the same QEMU profile and explicit launch as p3, including
  `XDG_RUNTIME_DIR=/run/user/1001`, `WAYLAND_DISPLAY=wayland-0`, the installed
  Example Demo bundle, and `FLR0026_NATIVE_LIGHT_OPERATION_TRACE=1`.

### Hypotheses

1. The p9 positive depends on an image/patch-stack difference not captured by
   the short p9 identity record.
2. The p9 positive depends on compositor ownership, app start ordering, or
   capture timing that was not preserved as an explicit input.
3. The p9 result was nondeterministic and will not reproduce under an exact
   repeated profile.

### UNKNOWN

- Exact p9 rootfs SHA-256 and full runtime input list.
- Whether the p9 compositor owner and app lifecycle exactly match FLR-0071.
- The downstream operation that can produce 3D pixels after valid light state.

## Plan / Do / Check / Act

### Plan

- Read FLR-0070/p9 evidence metadata and Mini artifact history.
- Replay the oldest missing identity first; stop before any source mutation if
  the p9 rootfs or launch contract cannot be recovered.

### Do

- Read the p9 evidence directory. Its `runqemu` command records the same
  QEMU profile, but references the old rootfs
  `.../agl-ivi-image-flutter-qemux86-64.rootfs-20260910195718.ext4`, which is
  no longer present in the fixed Mini deploy directory. The p9 record has no
  rootfs SHA-256 or complete environment capture.
- Repeated the p3 native-state-trace condition as p4 on the current rootfs.
  The first start attempt stopped at an artifact SHA check before QEMU start;
  a subsequent preflight and start passed after the same expected SHA was
  revalidated. No QEMU was left by the failed attempt.
- Captured five QMP frames, copied the guest runtime log, analyzed the 3D and
  HUD regions, and stopped the recorded app PID before official QMP teardown.
### Check

- p4's five frames were all 1280x800 and all had 3D region `0/223200` with
  region SHA-256
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
- p4 teardown passed with absent QMP socket and zero residual target
  processes. The positive p9 result was not reproduced twice on the current
  rootfs.
- The p9 result remains UNKNOWN with respect to exact image and complete
  runtime identity. This ticket does not claim a product regression or fix.

### Act

- Close FLR-0072. Split the direct image-stack comparison into FLR-0073:
  compare the 0206-free commit `a0ddaf3` with the current `a94f877` under the
  same fixed Mini build/TMPDIR and QMP trace profile.
