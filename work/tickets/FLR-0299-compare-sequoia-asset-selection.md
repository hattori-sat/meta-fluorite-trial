# FLR-0299 — compare Sequoia asset selection for model-only visibility

- Status: Waiting
- Priority: High
- Owner: production model selection/asset visibility role
- Created: 2026-09-25
- Predecessor: [FLR-0298](FLR-0298-replay-default-camera-sequoia.md)
- Working log: `work/logs/2026-09-25-flr0299.md`

## Objective

Change only the model-match selector from `sequoia_ngp` to the existing
`sequoia` selector under the current model-only/default-camera/frame-recovery
profile. Record the exact selected asset and determine whether the historical
vehicle silhouette belongs to a different asset.

## Acceptance gate

One fixed-image QEMU run must retain:

1. exact launch identity and the one selector change;
2. model selected/load plan, scene add, draw, and present markers;
3. QMP-only frame/video evidence with native ROI and full-frame visual review;
4. comparison against FLR-0298 and historical FLR-0285-0026f;
5. clean QMP teardown with zero residual targets.

## Constraints

- No source edit, generated patch, recipe change, image rebuild, or new
  container.
- Reuse the fixed Mini receiver, build, TMPDIR, rootfs, and one-QEMU harness.
- Keep environment, indirect light, explicit lights, camera, frame recovery,
  HUD, and surface ownership unchanged.

## Ranked hypotheses

1. If the historical silhouette belongs to `sequoia.glb`, changing the match
  selector will restore native geometry under the same model-only controls.
2. If the selected asset changes but remains black, the remaining boundary is
  asset transform/material/resource or target handoff.
3. If the selector resolves to the same asset, the historical positive differs
  elsewhere and must be recovered from its launch identity.

## UNKNOWN

- Exact historical model selector and selected asset for FLR-0285-0026f.
- Whether the current `sequoia` match is unique or selects multiple assets.

## Plan / PDCA

- Plan: replay FLR-0298 with only `FLR0026_NATIVE_MODEL_MATCH=sequoia`.
- Do: capture bounded markers and QMP frame/video.
- Check: compare selected asset identity and pixel evidence.
- Act: open a transform/material/target ticket or recover the historical
  launch profile; do not patch from a selector correlation alone.

## Visual evidence

Evidence root: `/mnt/yocto/evidence/flr0299-0001`.

- QMP frame: `sequoia-asset-selector-model-only.ppm`, SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- QMP video: `sequoia-asset-selector-model-only-video/` (12 frames).
- Runtime log: `sequoia-asset-selector-model-only-runtime.log`, SHA-256
  `8cabbd566f836cb3f0083ed11a75ee212260eca2102731c5de2b6154b60509b5`.
- Selected asset: `assets/models/sequoia_ngp.glb` for both selector profiles.
- Native ROI: `0/144000` changed and `0/144000` chromatic; HUD-only frame.
- QMP teardown: PASS with zero residual QEMU, runqemu, flutter-auto, and QMP
  socket targets.

## Result

- The selector A/B is negative and the asset spelling is not causal.
- The next diagnostic is the existing culling-disable control. No source or
  generated patch was created.
