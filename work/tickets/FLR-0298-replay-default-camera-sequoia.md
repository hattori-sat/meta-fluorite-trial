# FLR-0298 — replay default-camera Sequoia model-only condition

- Status: Waiting
- Priority: High
- Owner: production Sequoia camera/framing runtime role
- Created: 2026-09-25
- Predecessor: [FLR-0297](FLR-0297-reproduce-current-model-only-control.md)
- Working log: `work/logs/2026-09-25-flr0298.md`

## Objective

Replay the FLR-0285-0026f model-only condition on the current fixed rootfs,
removing only the explicit wide-camera override from FLR-0297. Keep the same
Sequoia selection, environment/indirect/direct-light skips, frame recovery,
QMP capture, and HUD path. Determine whether the vehicle silhouette returns and
where it lies in the 1280x800 frame.

## Acceptance gate

One fixed-image QEMU run must retain:

1. the exact FLR-0297 environment with no `FLR0285_NATIVE_PRODUCTION_CAMERA`;
2. model/load/scene-add, frame, draw, and present markers;
3. QMP-only frame/video evidence and both the historical candidate ROI and a
   full-frame vehicle-bound analysis;
4. comparison against FLR-0297 and FLR-0285-0026f;
5. clean QMP teardown with zero residual targets.

## Constraints

- No source edit, generated patch, recipe change, image rebuild, or new
  container.
- Reuse the fixed Mini receiver, build, TMPDIR, rootfs, and one-QEMU harness.
- Do not add light, material, surface, SHM, or compositor changes to this A/B.

## Ranked hypotheses

1. If the wide camera is the immediate cause, removing it will restore a
   recognizable but possibly clipped Sequoia silhouette.
2. If both cameras remain black, the first divergence is before or at model
   visibility/material/target output, not camera framing alone.
3. If default camera restores geometry but not color, camera is separated from
   the later light/material boundary.

## UNKNOWN

- Exact default camera transform in the current image.
- Whether the historical clipped silhouette is inside the native surface or
  merely outside the earlier ROI.

## Plan / PDCA

- Plan: run the existing model-only profile with only the wide-camera variable
  removed.
- Do: collect bounded markers, QMP frame/video, and full-frame pixel bounds.
- Check: compare native ROI, full-frame bounds, and HUD against FLR-0297.
- Act: if geometry returns, open the smallest camera framing or one-light
  ticket; otherwise open a model visibility/material boundary ticket.

## Visual evidence

Evidence root: `/mnt/yocto/evidence/flr0298-0001`.

- QMP frame: `sequoia-default-camera-model-only.ppm`, SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- QMP video: `sequoia-default-camera-model-only-video/` (12 frames).
- Runtime log: `sequoia-default-camera-model-only-runtime.log`, SHA-256
  `96ba48b3c80afe244c808f7d70ed8fbd0773e48dfb2cb13613ed2853dcaba081`.
- Native ROI: `0/144000` changed and `0/144000` chromatic; HUD ROI `2893`
  chromatic. Full-frame visual inspection shows HUD only.
- QMP teardown: PASS with zero residual QEMU, runqemu, flutter-auto, and QMP
  socket targets.

## Result

- The default-camera replay did not restore the vehicle and produced the same
  frame hash as FLR-0297. Camera override alone is not causal.
- The historical clipped-silhouette record is not identical to this run's
  effective asset selection; the next task compares model identity.
