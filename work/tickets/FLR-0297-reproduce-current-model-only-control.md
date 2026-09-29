# FLR-0297 — reproduce current-image Sequoia model-only control

- Status: Waiting
- Priority: High
- Owner: production Sequoia camera/culling/material baseline
- Created: 2026-09-25
- Predecessor: [FLR-0296](FLR-0296-production-sequoia-after-frame-recovery.md)
- Working log: `work/logs/2026-09-25-flr0297.md`

## Objective

Reproduce the historical current-image model-only control using the exact
production Sequoia model and wide camera, while disabling environment,
indirect light, and explicit lights and keeping the FLR-0295 frame-recovery
diagnostic control. Establish whether the current image can still show the
vehicle geometry with HUD before reintroducing lighting.

## Acceptance gate

One fixed-image QEMU run must retain:

1. the exact model-only environment and the single frame-recovery control;
2. model selection/load/scene-add, camera, draw, and present markers;
3. QMP-only frame/video evidence with native/HUD ROI analysis;
4. comparison against the known historical model-only positive and FLR-0296;
5. clean QMP teardown with zero residual targets.

## Constraints

- No source edit, generated patch, recipe change, image rebuild, or new
  container.
- Reuse the fixed Mini receiver, build, TMPDIR, rootfs, and one-QEMU harness.
- Do not mix the diagnostic scene, SHM cube, opaque surface, readback, or new
  camera values into this control.

## Ranked hypotheses

1. If the current image still has the known model-only path, disabling the
   production environment/lights will restore recognizable Sequoia pixels.
2. If model-only remains black, the remaining issue is camera/culling,
   model-transform, material resource, or target handoff before lighting.
3. If model-only is visible but adding one light later removes it, the light or
   shaded-material boundary remains causal.

## UNKNOWN

- Whether the older model-only positive used exactly the same current rootfs
  and camera profile.
- Whether the red tail-light material is inside the selected model view.

## Plan / PDCA

- Plan: replay the existing model-only command profile with only the fence-ready
  control carried forward.
- Do: collect bounded runtime markers and QMP evidence.
- Check: compare native/HUD pixels to FLR-0296 and the historical model-only
  result.
- Act: if positive, open the next one-light reintroduction ticket; if black,
  open a camera/culling/material boundary ticket.

## Visual evidence

Evidence root: `/mnt/yocto/evidence/flr0297-0001`.

- QMP frame: `sequoia-model-only-frame-recovery.ppm`, SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- QMP video: `sequoia-model-only-frame-recovery-video/` (12 frames).
- Runtime log: `sequoia-model-only-frame-recovery-runtime.log`, SHA-256
  `e23ecdaaad6dd4f78ac9d37551c5fb3d0e63a39431ed56c400f9ab96e285b561`.
- Observed: HUD ROI `2893` chromatic; native ROI `0/144000` changed and
  `0/144000` chromatic under the explicit wide camera.
- QMP teardown: PASS with zero residual QEMU, runqemu, flutter-auto, and QMP
  socket targets.

## Result

- The model-only acceptance gate failed under the wide camera, even though
  model loading, scene add, draw, present, and HUD succeeded.
- The historical default-camera/no-light silhouette is the next discriminating
  control. No source or generated patch is justified yet.
