# FLR-0300 — A/B production culling for Sequoia model-only visibility

- Status: Waiting
- Priority: High
- Owner: production Sequoia culling/frustum visibility role
- Created: 2026-09-25
- Predecessor: [FLR-0299](FLR-0299-compare-sequoia-asset-selection.md)
- Working log: `work/logs/2026-09-25-flr0300.md`

## Objective

Enable the existing opt-in `FLR0285_NATIVE_DISABLE_CULLING=1` control under the
current Sequoia model-only/default-camera/frame-recovery profile. Determine
whether renderable culling is the first boundary that removes all visible
vehicle pixels.

## Acceptance gate

One fixed-image QEMU run must retain:

1. exact launch identity plus only the culling-disable control;
2. model/load/scene-add, culling count, draw, and present markers;
3. QMP-only frame/video evidence with native ROI and full-frame review;
4. comparison against FLR-0299 and the historical model-only silhouette;
5. clean QMP teardown with zero residual targets.

## Constraints

- No source edit, generated patch, recipe change, image rebuild, or new
  container.
- Reuse the fixed Mini receiver, build, TMPDIR, rootfs, and one-QEMU harness.
- Keep lights, camera, model selector, frame recovery, HUD, and surface
  ownership unchanged.

## Ranked hypotheses

1. If culling is the cause, disabling it will produce native Sequoia pixels
   without changing model selection or lighting.
2. If culling is not the cause, the frame will remain HUD-only and the boundary
   moves to transform/material/target output.
3. If pixels appear outside the candidate ROI, the next analysis must use
   full-frame bounds before changing camera or source.

## UNKNOWN

- Whether current renderable instances have valid bounds/transform at draw
  time.
- Whether the existing culling switch applies to the production default scene
  as well as the diagnostic scene.

## Plan / PDCA

- Plan: replay FLR-0299 with only `FLR0285_NATIVE_DISABLE_CULLING=1`.
- Do: collect bounded culling/model/frame markers and QMP frame/video.
- Check: compare native/full-frame pixels and selected runtime state.
- Act: open a transform/material/target ticket or a camera ticket only after
  this control is classified.

## Visual evidence

Evidence root: `/mnt/yocto/evidence/flr0300-0001`.

- QMP frame: `production-culling-model-only.ppm`, SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- QMP video: `production-culling-model-only-video/` (12 frames).
- Runtime log: `production-culling-model-only-runtime.log`, SHA-256
  `bfb1edc6e9e31f89c83e7a3158f27c002eb5df1c98531d1bf2d8464b49fd53ff`.
- Native ROI: `0/144000` changed and `0/144000` chromatic; full frame is HUD
  only.
- QMP teardown: PASS with zero residual QEMU, runqemu, flutter-auto, and QMP
  socket targets.

## Result

- The culling control did not reach the production path: its diagnostic marker
  was absent and the frame SHA was unchanged.
- Runtime materials/bounds are present, so the next unit must inspect primary
  model transform and production scene ownership. No source or generated patch
  was created.
