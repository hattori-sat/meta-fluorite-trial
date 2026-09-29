# FLR-0305 — probe a self-made light in the production default Scene

- Status: Done
- Priority: High
- Owner: production default Scene lighting/material evaluation role
- Created: 2026-09-25
- Predecessor: [FLR-0304](FLR-0304-probe-production-camera-culling-visibility.md)
- Working log: `work/logs/2026-09-25-flr0305.md`

## Objective

Determine whether the production Sequoia renderables become visible or
chromatic when one known-good self-made light is added to the same default
Scene that owns the production model. The existing lit native fixture is a
positive control, but its diagnostic Scene path is not sufficient evidence for
production Sequoia.

## Scope

- Add one opt-in light only to the production default Scene.
- Keep the proven direct app launch, app id, bundle, camera, viewport, HUD,
  frame recovery, and QMP capture contract unchanged.
- Do not alter materials, model transforms, culling, surface blend, or
  Wayland composition in this ticket.
- Use one normal profile and one self-made-light profile at most.

## Success criteria

1. The light entity creation and default-Scene attachment are logged.
2. The same QMP-only frame contains the HUD and a changed native ROI, or the
   light contribution is explicitly falsified.
3. Any red-tail/color result is recorded as evidence, not inferred from logs.
4. One QEMU at a time and clean QMP teardown are proven.

## Facts and hypotheses

- FLR-0286 proves a self-made LIT Filament fixture can produce colored native
  pixels with the HUD in the same image.
- FLR-0283/0284 restored existing production indirect/direct-light paths, but
  the current Sequoia native ROI remained black.
- FLR-0304 proves camera/frustum/culling is not the first missing contract.

Hypotheses:

1. The production default Scene may lack a usable light for the Sequoia
   material evaluation path.
2. A self-made light may change nothing, which would move the boundary to
   production material/base-color/texture evaluation.

UNKNOWN: whether the historical red tail came from a production light,
emissive/material data, or a different asset/camera condition.

## Plan / PDCA

- Plan: inspect `LightSystem` ownership and default Scene APIs; add one
  opt-in light with explicit color, intensity, and direction.
- Do: use the Mac persistent Devtool source, official generated patch, fixed
  Mini bundle/build, and QMP-only normal/light A/B.
- Check: compare native/HUD ROIs and bounded light/material markers.
- Act: if light changes the native ROI, narrow to light placement/intensity;
  otherwise open the smallest material/emissive/texture boundary.

## Runtime result

- Canonical commit: `d3c1197`; fixed Mini receiver tip:
  `d3c1197bae93e4b90c56f780b0af54c4886663d6`.
- Bundle SHA-256:
  `b051a2883e8307f64b67b6418ca9ff9b9e28a2880449bc1720837c721ab07af3`.
- Mini `do_patch`, `flutter-auto do_compile`, and full
  `bitbake agl-ivi-image-flutter` all passed.
- Rootfs SHA-256:
  `eb93884eaf55429a7095a3f5d709eca9f48a5d1fa073450259e1543ac622230e`.
- The light profile logged `FLR0305_PRODUCTION_SCENE_LIGHT_SETUP_DONE
  entity=72 scene=default type=SUN intensity=110000 direction=(0.7,-1,-0.8)`
  and reached the same default Scene draw and Vulkan present markers as the
  baseline.
- Baseline QMP frame:
  `/mnt/yocto/evidence/flr0305-0001/normal/normal.ppm`, SHA-256
  `e6f0e98514821de062f284bf5d65b288a696e51869f53ad43a5a919d2341a524`.
  Native ROI was `0/144000` changed/chromatic; HUD ROI was `2845` chromatic.
- Self-made-light QMP frame:
  `/mnt/yocto/evidence/flr0305-0001/light/light.ppm`, SHA-256
  `1988e6cfc7ac9e94930bb521ba7e36729e004b94b5793642f3dab1467cdaa03c`.
  Native ROI remained `0/144000` changed/chromatic; HUD ROI remained `2845`
  chromatic. The final frame of each eight-frame video had the same SHA as
  its profile frame.
- Both QMP teardowns passed; residual QEMU and flutter-auto checks passed.

## Classification

The self-made light reached the production default Scene but did not change
the Sequoia output. Lighting absence alone is therefore falsified as the first
missing contract. The next boundary is production material/output evaluation,
including alpha, base-color/texture parameters, and whether the production
Renderable actually emits fragments into the target.
