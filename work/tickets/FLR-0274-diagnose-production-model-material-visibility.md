# FLR-0274 — diagnose production model/material visibility

- Status: Done
- Priority: High
- Owner: production scene asset / material / lighting runtime roles
- Depends on: [FLR-0273](FLR-0273-isolate-post-activation-render-surface-visibility.md)
- Working log: `work/logs/2026-09-24-flr0274.md`

## Problem

The shared fixture path displays colored native 3D pixels, but the production
Fluorite scene remains grayscale/zero-chroma after camera activation. The
production content path must be separated into model presence, material
parameters, lighting contribution, and camera framing before changing source.
The first production discriminator identified a camera-selection defect in
the Flutter route wiring.

## Facts

- Camera activation and effective camera transform are already proven by
  FLR-0272.
- The fixture and production controls use the same verified rootfs and QMP
  capture profile.
- Fixture stable ROI has `chromatic_pixels=35`; production Run 0303 has
  `chromatic_pixels=0`.
- Production runtime reaches Scene insertion, draw submit/end, and Vulkan
  present.
- Run `flr0274-0001` loaded five production assets, added one secondary model
  to Scene, and reached `QUEUE_PRESENT`, but its QMP ROI was the same black
  native trapezoid with `chromatic_pixels=0`.
- The effective camera in that run was `(-720,-80,680)` with viewport
  `(0,0,1280,800)`. `PlanetariumSceneView` uses that origin, while the
  production models and the self-made fixture are near `(0,0,0)`.
- The startup `build()` mounted `PlanetariumSceneView` unconditionally, while
  the Scenes button selected empty scene `5`; the existing `_sceneViewNotifier`
  was not used by the startup Stack.
- `flr0274-0002` (skip default indirect light) and `flr0274-0003` (skip
  environment/lights/shapes) did not recover colored pixels. The latter
  changed composition to uniform gray, so it is not accepted as a model
  visibility result.
- The official `0091` patch was committed as canonical revision `4137e70` and
  consumed by the fixed Mini receiver. Mini `do_patch`, app compile, and
  `agl-ivi-image-flutter` image generation all passed.
- The new image rootfs SHA-256 is
  `2f4b454befb5c21931010e060baaadc6fe8b3d8755eb5e52e4cc7e86a21f5e16`.
- FLR-0274 QMP run `flr0274-0004` used that image and reached the patched
  effective camera `camera_pos=(5,0,-5)`, but startup and settled frames both
  remained `chromatic_pixels=0`, `max_chroma=4`. QMP teardown passed.

## Hypotheses

1. ~~Production model/material data is present but resolves to grayscale or
   unlit output.~~ Lower priority: asset load and Scene insertion are positive,
   while the camera mismatch is directly evidenced.
2. ~~Production assets are geometrically present but outside the intended
   camera/light framing because the startup route activates Planetarium's
   distant camera.~~ The `0091` fix changed the effective camera to the local
   Playground camera without restoring colored pixels.
3. Production geometry/material or native scene attachment still suppresses
   visible color after camera selection. UNKNOWN whether the first remaining
   boundary is model transform, material parameters, or native view state.

## Success criteria

- Reproduce the production control with bounded logs and QMP evidence.
- Add the smallest runtime discriminator that distinguishes model/material,
  lighting, and framing without changing the shared surface contract.
- Apply the minimal route/camera patch through the official Mac Devtool flow,
  then verify it authoritatively on Mini.
- Preserve QMP screenshot/video evidence and clean QEMU teardown.

## Non-goals

- Do not redesign Wayland/QMP composition while the fixture control remains
  positive.
- Do not declare 3D complete from draw/present markers alone.
- Do not use a new build directory or duplicate container/TMPDIR.

## Verification plan

1. Inspect existing production asset/material/light markers and effective
   camera values. (Done.)
2. Run production controls with the same fixed image and ROI analyzer. (Done.)
3. Compare the first differing content boundary against FLR-0273 fixture data.
   (Camera framing selected as the first actionable boundary.)
4. Generate `0091` through the canonical Devtool flow, commit the layer
   change, bundle it to the Mini receiver, and rebuild there. (Done.)
5. Run one authoritative QMP startup and one bounded input attempt. (Done;
   startup remains zero-chroma and route transition was not observed.)

## Result

`0091` corrected the startup camera selection from the distant Planetarium
camera to the local Playground camera, and the change was proven in the
authoritative runtime log. It did not produce colored production pixels. The
remaining production model/material/native attachment discriminator is moved
to FLR-0275; this ticket is closed with its evidence preserved.

## Evidence

- Canonical commit: `4137e70b067241e3eed37f6f19e6203b84842746`
- Mini evidence: `/mnt/yocto/evidence/flr0274-0004`
- QMP startup/settled ROI: `chromatic_pixels=0`, `max_chroma=4`
- QMP teardown: PASS, zero residual targets and zero QMP socket

## Next ticket

- FLR-0275 owns production payload and native scene attachment isolation with
  the corrected local camera retained.
