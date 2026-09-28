# FLR-0064 — non-blocking production target-content probe

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan roles
- Created: 2026-09-10
- Depends on: [FLR-0062](FLR-0062-production-shaded-output-target-boundary.md)
- Working log: `work/logs/2026-09-10-flr0064.md`

## Work unit

Replace the blocking queue-idle observation introduced by FLR-0062 with one
bounded diagnostic that can classify the production 1280x800 target as
non-zero, zero, or unavailable without changing lighting, materials, or
composition behavior.

## Problem

The authoritative FLR-0062 run reached the production target draw and queue
submit, then stopped at `TARGET_PROBE_QUEUE_IDLE_BEGIN`. QMP showed a black
candidate region, but the diagnostic itself did not complete, so the result
cannot distinguish a black shaded target from a diagnostic-side stall.

## Success measure

- [x] Edit only the persistent Mac Devtool source and generate the patch by
  official Devtool into `meta-fluorite-trial`.
- [x] Deliver one bundle to the fixed Mini receiver and pass metadata,
  recipe-scoped `do_patch`, compile, and full-image gates in the existing
  build/TMPDIR.
- [x] Run exactly one reusable QEMU with explicit guest launch and QMP-only
  capture; obtain a completed target-content result or an explicitly bounded
  timeout classification.
- [x] Preserve raw runtime log, QMP frames, pixel analysis, gdb or
  syscall evidence when needed, hashes, and exact cleanup evidence.
- [x] Do not change light count, material values, stacking, route behavior, or
  product defaults in this ticket.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0062's corrected app patch cleanup and full image passed on the fixed
  Mini build.
- The 0175 run had one `flutter-auto`, one compositor, successful draw/submit
  markers, and no SIGSEGV, but no target pixel result.
- The prior cube-plus-HUD result was a self-made native-above-parent A/B, and
  the prior Sequoia result was model-only; combined full-shaded production
  2D+3D remains unproven.

### Hypotheses

1. The target is non-zero and the previous blocking diagnostic obscured that
   fact. Prediction: a bounded observation reports non-zero target pixels.
2. The target is zero before composition because the production shaded path is
   incomplete. Prediction: a completed observation reports zero pixels while
   draw/submit remains successful.
3. The target cannot be sampled safely in this runtime path. Prediction: the
   bounded diagnostic reports timeout/unavailable without blocking the frame
   loop or hiding the teardown boundary.

## Evidence — authoritative Mini/QEMU run (2026-09-10)

### Facts

- The persistent Mac Devtool source commit was `c6767205434a36d6d6954a5728ac7083a55419ed`.
  Official `devtool finish --mode patch` generated the registered 0176 patch;
  the generated and registered patch SHA-256 is
  `b95416383a8cf365f205febe853a97993526be468329e6724614037c245ecffd`.
- Exact byte-identical patch duplicates are zero. The earlier redundant app
  patches 0025/0026 were removed in `49089ba`; 0176 is a follow-up replacement
  for the blocking 0175 diagnostic boundary, not a duplicate implementation.
- One bundle moved the canonical receiver from `49089ba` to `19806a2`.
  Bundle SHA-256 was
  `a4c58d39a4239bcf5f62ee0e381525f6cc54390d8524cddb3df9807aa0349faf`.
- Mini gates passed in the existing build and TMPDIR: `filament-vk:do_patch`
  104/104, `filament-vk:do_compile` 1965/1965, and
  `agl-ivi-image-flutter` 11748/11748. The full-image rootfs, kernel, and
  qemuboot SHA-256 values are respectively
  `a6382c77e943645ec8b35bb266056a581d1e17cbfad1d8c586d5c329a9c2a794`,
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and
  `b6c983c3b6ef4a08bdb5bb16e3da96f8dcd99811dfb4022b6db2d78e44de272a`.
- Exactly one QEMU was started through the short-path harness under
  `$QEMU_EVIDENCE_ROOT/flr0064/p1`. The guest had one `flutter-auto` process.
  The QMP-only capture was 1280x800 and contained 12 identical frames. The
  final PPM SHA-256 was
  `049ad4a1084d8bb0cb8c10c06ee354e80e6ec52a1a368958aae5029f664771ab`.
- The central 3D candidate region `[300,80,620,360]` was `0/223200` pixels
  different from black. Its region SHA-256 was
  `30ff759070d06040ddbba9915df4ce1a62754df3bfee0a150ea81edac42a1ff2`.
  The full frame changed 24847 pixels, the top HUD region changed 6272, and
  the bottom control region changed 15252, confirming the 2D HUD/control path
  was visible in the same QMP frame.
- The runtime reached `TARGET_DRAW2` 24 times and queue-submit success twice.
  The non-blocking observation completed with
  `FLR0026_VK_READBACK_FENCE_WAIT result=2`,
  `FLR0026_VK_READBACK_FENCE_TIMEOUT`, and
  `FLR0026_TARGET_PROBE_RESULT ... nonzero_pixels=0 total_pixels=1024000
  half_word_sum=0`. Runtime-log SHA-256 was
  `826ce017fc193ce33bd6a6de43868234b80d0245a3850ef2cb38bcbe07a2b93c`.
- QMP negotiated quit was accepted and cleanup reported zero residual target
  processes and zero residual QMP socket.

### Inferences

- The previous 0175 diagnostic-side stop is resolved as a classification
  problem: the probe now completes with a bounded timeout and a zero-content
  result. The target itself was zero in this run; the result is not merely an
  artifact of waiting forever at `QUEUE_IDLE_BEGIN`.
- This is not evidence of a regression from the latest diagnostic patch. The
  patch changes only the environment-gated target observation; it does not
  change lights, materials, render stacking, route behavior, or product
  defaults. Full-production shaded black output was already recorded in the
  preceding light/surface/draw-boundary tickets.
- The earlier simultaneous 2D+3D frame was a diagnostic A/B with production
  shapes/lights suppressed (wireframe/red-lamp content). It is not a same-input
  baseline for the current full-shaded production scene. Therefore the current
  evidence does not support “2D+3D regressed from a previously successful full
  shaded state.”

### UNKNOWN

- Actual production target contents before swapchain composition.
- Whether the remaining full-shaded failure is resource/material, target
  handoff, parent alpha, or a later composition boundary.

## PDCA

### Plan

- Inspect the existing 0175 Devtool source and choose the smallest
  non-blocking/timeout-bounded observation.
- Generate the patch on Mac through the persistent Devtool workspace; do not
  hand-edit a generated patch or use the Mac `EXTERNALSRC` context as the
  authoritative `do_patch` result.
- Bundle once, apply/build on Mini, then run one QMP capture and one cleanup.

### Do / Check / Act

- Do: record all commands and bounded outputs in the working log.
- Check: classify target-nonzero, target-zero, or unavailable; do not infer
  light failure from a missing diagnostic result.
- Act: if target-nonzero, open a separate composition ticket; if target-zero,
  open a separate production shading/resource ticket; if unavailable, narrow
  the runtime synchronization boundary before changing rendering behavior.

### Act result

- Target classification is **zero**, so this ticket is Waiting and hands off to
  [FLR-0065](FLR-0065-production-target-zero-resource-boundary.md). Do not add
  a lighting or composition fix to this ticket.
