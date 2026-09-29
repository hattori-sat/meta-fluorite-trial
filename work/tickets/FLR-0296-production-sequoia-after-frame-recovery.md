# FLR-0296 — replay production Sequoia after frame-loop recovery

- Status: Waiting
- Priority: High
- Owner: production Sequoia content + material/light/composition roles
- Created: 2026-09-25
- Predecessor: [FLR-0295](FLR-0295-ab-unlinked-fence-ready.md)
- Working log: `work/logs/2026-09-25-flr0296.md`

## Objective

Replay the known production Sequoia runtime profile while keeping the
diagnostic frame-loop control from FLR-0295. Determine whether production
Sequoia produces recognizable geometry or colored/light pixels once
`beginFrame` is no longer suppressed. This is a runtime classification unit;
the fence control is not a product fix.

## Acceptance gate

One fixed-image QEMU run must retain:

1. the exact production launch environment plus only
   `FLR0026_TREAT_UNLINKED_FENCE_READY=1` as the added diagnostic control;
2. model selection/scene-add, draw, submit, and present markers;
3. QMP-only frame/video evidence with native and HUD ROI analysis;
4. a comparison to FLR-0287 production control and FLR-0295 diagnostic
   recovery;
5. clean QMP teardown with zero residual targets.

## Constraints

- No source edit, generated patch, recipe change, image rebuild, or new
  container.
- Reuse the fixed Mini receiver, build, TMPDIR, rootfs, and one-QEMU harness.
- Do not change the production camera, model selection, lights, surface
  ownership, or swapchain except for the one recorded fence control.

## Ranked hypotheses

1. If the frame-loop boundary was the only blocker, production Sequoia will
   show recognizable geometry and/or colored light pixels under the recovered
   loop.
2. If production remains black while the fixture control is known positive,
   the remaining boundary is production content/material/light/target state.
3. If the HUD/native composition changes independently, the remaining issue is
   surface ownership or composition rather than light creation.

## UNKNOWN

- Whether the production profile has a stable model/material path with the
  frame-loop control enabled.
- Whether the vehicle's red tail-light observation belongs to the current
  camera view or only the historical FLR-0049 profile.

## Plan / PDCA

- Plan: use the recorded FLR-0287 production Sequoia launch and add only the
  FLR-0295 fence-readiness control.
- Do: collect bounded runtime markers and QMP evidence.
- Check: compare pixels and first missing stage against the fixture and
  diagnostic profiles.
- Act: open a source-boundary ticket only after the production divergence is
  identified.

## Visual evidence

Evidence root: `/mnt/yocto/evidence/flr0296-0001`.

- QMP frame: `production-sequoia-frame-recovery.ppm`, SHA-256
  `42c2c2c7b11604af7d18d5e79df7ba831b070fc0fc4f060f9a16d03c7b5c1d5b`.
- QMP video: `production-sequoia-frame-recovery-video/` (12 frames).
- Runtime log: `production-sequoia-frame-recovery-runtime.log`, SHA-256
  `ab7a049b130b8e8e3c131c9318e041824feedbd8d5cfe229f16c6b12d49cba2f`.
- Observed: HUD ROI has `2893` chromatic pixels; native ROI has `0` changed
  and `0` chromatic pixels.
- QMP teardown: PASS with zero residual QEMU, runqemu, flutter-auto, and QMP
  socket targets.

## Result

- Frame recovery is confirmed but insufficient for production Sequoia pixels.
- `scene_default=true` is expected for the production path and is not the
  first divergence; diagnostic-only scene switching is opt-in.
- The next gate is a current-image model-only control before any light or
  source change.
