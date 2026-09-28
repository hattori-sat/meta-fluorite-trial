# FLR-0306 — probe production material and fragment output

- Status: Waiting
- Priority: High
- Owner: production Sequoia material/fragment output role
- Created: 2026-09-25
- Predecessor: [FLR-0305](FLR-0305-probe-production-default-scene-light.md)
- Working log: `work/logs/2026-09-25-flr0306.md`

## Objective

Find the first material/output boundary that keeps valid production Sequoia
Renderable instances completely black even after camera, culling, Scene
attachment, draw/present, and a default-Scene self-made light are proven.

## Scope

- Keep the proven direct app launch, `fluorite` app id, camera, default Scene,
  self-made light, frame recovery, and QMP ROI contract.
- Inspect and log only bounded material properties: blending/alpha mode,
  color/depth write, double-sided state, primitive/material presence, and
  texture/base-color parameter availability where the target API permits.
- Use one opt-in material probe or one minimal A/B at a time.
- Do not change Wayland composition, surface blend, camera, culling, or model
  transforms in this ticket.

## Success criteria

1. The selected Sequoia material/output state is observed with bounded logs.
2. A QMP-only baseline/light/material comparison proves whether native pixels
   remain absent or become visible/chromatic.
3. The first missing contract is classified as material/fragment output or
   moved to a narrower target/draw boundary.
4. QMP teardown and residual-process checks pass.

## Facts and hypotheses

- FLR-0304: camera/frustum/culling A/B did not change native ROI.
- FLR-0305: a self-made SUN in the production default Scene did not change
  native ROI; the generic light path is positive only for the self-made fixture.
- Existing traces prove Sequoia materials are present with color/depth write
  enabled, but do not prove alpha mode, texture/base-color availability, or
  fragment emission.

Hypotheses:

1. Production glTF material alpha/texture state may discard or output black
   fragments under the current target contract.
2. Material state may be valid while the production draw path emits no visible
   fragments; a bounded material override or fragment-output probe is needed.

UNKNOWN: whether the historical red-tail pixels were emissive/base-color data,
a different model instance, or a different render target condition.

## Historical baseline correction

The earlier summary that combined HUD plus Sequoia had never been observed was
incorrect. The repository contains two distinct positive references:

- FLR-0070 p9 observed the Flutter HUD and Sequoia pixels in the same QMP
  frame under the one-light operation-trace profile: `5510/223200` native
  candidate pixels and `3961/100000` HUD pixels, frame SHA-256
  `3bc9fc3442750f1331f1baf43f55ec212f02b59a8c191712b461edea8254dd06`.
- FLR-0049 observed the production Sequoia silhouette and red tail-light
  pixels, but its native surface covered the HUD in that profile. FLR-0251
  and FLR-0286 separately prove simultaneous HUD plus self-made native 3D,
  including an opt-in LIT/SUN fixture.

Therefore the current target is not generic 2D/3D composition. It is to
reproduce the historical combined Sequoia/color condition and then identify
why the current default production material path remains zero-pixel. Camera,
culling, and light presence are already negative first-cause candidates;
material/fragment output remains the active boundary.

## Plan / PDCA

- Plan: inspect exact target Filament material APIs and current bounded trace.
- Do: add only the smallest opt-in observation/override through the persistent
  Mac Devtool source and official patch flow.
- Check: compare native/HUD ROIs and selected material markers.
- Act: keep only the next smallest boundary; do not reopen camera/light work.

## Result and visual evidence

The bounded material probe completed on the authoritative FLR-0306 image.
The light-enabled profile is retained under the fixed Mini evidence role
`$EVIDENCE_ROOT/flr0306-0001/normal/` (the directory name is historical; the
profile included `FLR0305_PRODUCTION_SCENE_LIGHT=1`). Its QMP frame
`normal.ppm` has SHA-256
`d36a446dd14130f6530a6249eb50dc5b56b1cb59878f7f3e19b530a5822b28e1` and its
bounded video is in `normal/video/`.

Observed in that profile:

- native ROI `(440,220,400,360)`: `0/144000` changed and `0/144000`
  chromatic pixels;
- HUD ROI `(1120,0,160,80)`: `2845` chromatic pixels;
- `FLR0305_PRODUCTION_SCENE_LIGHT_SETUP_DONE`: 1;
- `FLR0280_MODEL_MATERIAL`: 1410 records;
- `FLR0306_MODEL_PARAMETER`: 22560 bounded parameter records;
- `FLR0026_SCENE_STAGE_DRAW_SUBMIT`: 15 and `FLUORITE_VK_PRESENT_DONE`: 1;
- runtime log SHA-256
  `3c8bb29790ebc6656e55bf642a1c751443a1bf05ee9189f2a6fb768ca25e33b9`.

The observed material example was `base_lit_opaque` with transparency 0,
color/depth write enabled, double-sided false, alpha-to-coverage false,
mask threshold 0.4, and 40 parameters including `baseColorIndex` and
`emissiveIndex`. This moves the first unresolved boundary after material
metadata and Scene draw setup; it does not prove fragment emission.

A no-light profile was also captured in the same QEMU. Its settled frame
`baseline/settled.ppm` has SHA-256
`8a093164334d964ddc38a7b05f6c53feed8e59fe21a76917f6565bcf7b854336`, with
the same native `0/144000` and HUD `2845` result. It remained in asynchronous
asset loading before material markers appeared, so the no-light material
comparison is `UNKNOWN`, not a claim of a completed A/B.

QMP quit and cleanup passed; the final precise check found zero residual
QEMU/runqemu/flutter-auto processes and no QMP socket.

## Decision / Act

- Camera, culling, Scene attachment, and light presence remain falsified as
  first causes for this black result.
- The material metadata probe is complete; no production material override
  was promoted.
- FLR-0307 owns the next one-variable fragment-output versus target-handoff
  discriminator.
