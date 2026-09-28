# FLR-0304 — probe production camera, frustum, and culling visibility

- Status: Done
- Priority: High
- Owner: production ViewTarget camera/renderable visibility role
- Created: 2026-09-25
- Predecessor: [FLR-0302](FLR-0302-probe-production-world-transform.md)
- Working log: `work/logs/2026-09-25-flr0304.md`

## Objective

Determine why production Sequoia has valid scene attachment, world transforms,
materials, layer, draw, and present markers but produces no native pixels. The
next boundary is the effective camera/frustum and production renderable
culling state.

## Scope

- One opt-in diagnostic observation or one-variable A/B at a time.
- Keep lighting, blend mode, Wayland surface, and target composition unchanged.
- Log the effective camera position/target/projection and production culling
  state for the selected Sequoia renderables.
- Do not call the diagnostic-only Scene path as evidence for production.

## Success criteria

1. The exact production camera/frustum and culling state are observed or
   explicitly classified as UNKNOWN.
2. A QMP-only frame compares native ROI and HUD ROI under one fixed image.
3. The result either proves camera/culling visibility or moves the first
   missing boundary to lighting/material evaluation.
4. QMP teardown leaves no residual runtime process.

## Hypotheses

1. The default camera/frustum may not cover the Sequoia local bounds despite
   valid world transforms.
2. Production renderables may be culled by a state not affected by the
   existing diagnostic-only `FLR0285_NATIVE_DISABLE_CULLING` switch.
3. If camera and culling are proven visible, the remaining boundary is the
   light/material evaluation path; the self-made Lit fixture remains the
   generic positive control.

## UNKNOWN

- Whether the historical FLR-0070 visible run used the same camera/culling
  contract.
- The exact production light/material evaluation boundary remains UNKNOWN.

## Static/API evidence

- The target Filament `Camera` API provides `getProjectionMatrix()`,
  `getCullingProjectionMatrix()`, `getViewMatrix()`, and `getPosition()`.
- The target Filament `RenderableManager` API provides `setCulling()` but no
  culling-state getter. The default state therefore cannot be claimed from a
  log-only observation.
- The production path adds renderables through `ModelSystem::setupRenderable`;
  the existing `FLR0285_NATIVE_DISABLE_CULLING` switch is confined to the
  diagnostic Scene path and does not affect production renderables.
- The probe consequently records the effective camera matrices and offers an
  explicit production-only culling-disable A/B. Lighting and composition are
  unchanged.

## Plan / PDCA

- Plan: inspect camera setup and Filament culling APIs in the persistent
  Devtool source; no source edit until the observation marker is specified.
- Do: create one opt-in probe, commit via Devtool, regenerate patch, build and
  run one QEMU profile. The source commit is `9b2f144313f166c4dd8a88b5475e228dd280c906`;
  the canonical patch is `0299-flr0304-probe-production-camera-culling-devtool.patch`.
- Check: compare native ROI, HUD ROI, camera/culling markers, and historical
  evidence.
- Act: camera/culling passed; FLR-0305 owns the separate production-light
  boundary.

## Runtime result

- Canonical commit: `e1fb232`; fixed Mini receiver tip:
  `e1fb232342a655c6839c808e227e008c0b4ab525`.
- Bundle SHA-256:
  `0a88faf57a6e4cdb2ac7d08c7a8f5caf629d542e75d75d4cefb11f554b34440d`.
- `do_patch`, `flutter-auto do_compile`, and full
  `bitbake agl-ivi-image-flutter` passed.
- Rootfs SHA-256:
  `5ef230c6e3a887114c4f1273e265428ec5844f0cba1d97c4082ce64933d1f7cb`.
- Normal direct-launch profile recorded effective camera position `(5,0,-5)`;
  viewport `(0,0,1280,800)`; projection and culling-projection matrices were
  logged; draw, frame, and present markers passed. Native ROI was
  `0/144000` changed and chromatic; HUD ROI was `2845` chromatic pixels.
- Normal QMP frame:
  `/mnt/yocto/evidence/flr0304-0001/normal/direct.ppm`, SHA-256
  `6249bdf657c09f688fbdf02b8894158b43f69b2d982d5a64180b0677996cd60e`.
  The final frame of the eight-frame video had the same SHA.
- Culling-disabled profile applied
  `FLR0304_PRODUCTION_CULLING_OVERRIDE` to 108 renderables and reached the
  same camera/draw/present markers. Native ROI remained `0/144000`; HUD ROI
  remained `2845` chromatic pixels.
- Culling-disabled QMP frame:
  `/mnt/yocto/evidence/flr0304-0001/culling/culling.ppm`, SHA-256
  `4216a9275a1e7d6020415b351f0c732fbedd3e60ba60d511ae685694fb1aa513`.
  The final frame of its eight-frame video had the same SHA.
- Both profiles ended with QMP quit accepted and zero residual QEMU,
  runqemu, or flutter-auto processes.

## Classification

- The effective production camera is now observed, and disabling production
  frustum culling does not change the visible result.
- Camera/frustum/culling is not the first missing contract for this fixed
  Sequoia run. This does not prove that lighting is the root cause, but it
  makes a controlled production-light/material A/B the next smallest test.
