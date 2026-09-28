# FLR-0279 — isolate production opaque surface composition

- Status: Done
- Priority: High
- Owner: production View blend mode / Flutter-Wayland surface composition
- Depends on: [FLR-0278](FLR-0278-isolate-production-grayscale-render-content.md)
- Working log: `work/logs/2026-09-24-flr0279.md`

## Problem

The same authoritative image renders the self-made fixture with chromatic QMP
pixels, but the production model path produces a black or uniform white/gray
surface. The current production frame callback can also fault later in
`CallEvent`, so content and composition must be tested with that callback
disabled.

## Facts

- QEMU has already been proven healthy at 4096 MiB with no guest OOM record.
- `FLUORITE_NATIVE_FORCE_OPAQUE` is an existing runtime switch in
  `ViewTarget::setupView`; without it the production view is translucent.
- `FLR0026_SKIP_FRAME_EVENT` is an existing runtime switch that avoids the
  delayed `CallEvent` path.
- The same image and QMP capture path must be reused; no compositor or image
  change is allowed in this discriminator.

## Result

The opaque-surface hypothesis is falsified for this case. The runtime log
proves `FLUORITE_NATIVE_FORCE_OPAQUE enabled=true` and
`blend=0`, but the late QMP ROI has zero chromatic pixels and the same PPM
identity as the existing frame-event-skip production baseline. The process
remained alive with no coredump, and serial stop/QMP teardown passed.

## Hypothesis

The production view's translucent blend/surface contract is causing the
uniform white/gray result or hiding production pixels. If so, forcing the
native view opaque while skipping the known callback fault should change the
QMP ROI from the current black/white baseline. **Falsified:** opaque mode was
effective but did not change the ROI.

## Success criteria

- Run one bounded production case in one 4096 MiB QEMU.
- Capture initial and ten late QMP screenshots plus a bounded log slice.
- Require a live-process check and clean serial-stop/QMP teardown.
- Classify the result as supported, falsified, or UNKNOWN; do not call a gray
  or uniform frame successful 3D.

## Verification plan

1. Reuse the existing authoritative image and fixed Mini receiver.
2. Launch one model with skybox, indirect light, and lights skipped, plus
   `FLR0026_SKIP_FRAME_EVENT=1` and `FLUORITE_NATIVE_FORCE_OPAQUE=1`.
3. Compare QMP chromatic/edge metrics and the bounded production markers with
   FLR-0277/0278 evidence.
4. If opaque changes pixels, open a separate fix ticket; otherwise move to the
   next first-difference boundary without patching this discriminator.

## Evidence

- Mini run: `/mnt/yocto/evidence/flr0279-0001`
- QMP late frame: `opaque-video/frame-00009.ppm`
- PPM SHA-256: `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`
- ROI: `[200,100,400,250]`, changed `116`, edge `294`, chromatic `0`, max
  chroma `0`
- QEMU: 4096 MiB; app live during capture; no coredump; serial stop and QMP
  cleanup PASS

The next independent unit is
[FLR-0280](FLR-0280-trace-production-model-content-binding.md).
