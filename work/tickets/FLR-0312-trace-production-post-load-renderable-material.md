# FLR-0312 — trace production post-load renderable and material setup

- Status: Done
- Priority: High
- Owner: production async resource completion / Scene attachment / renderable-material roles
- Created: 2026-09-25
- Predecessor: [FLR-0311](FLR-0311-compare-production-gltf-material-fault-with-lit-fixture.md)
- Working log: `work/logs/2026-09-25-flr0312.md`

## Objective

Determine whether the production `sequoia_ngp.glb` reaches asynchronous load
completion, Scene attachment, Filament renderable creation, and material
binding before the black native ROI and FEngine fault. Reuse existing
opt-in diagnostics; do not create a source patch unless the evidence shows a
missing or incorrect operation.

## Success criteria

- One Mini-authoritative QEMU run using the existing FLR-0311 image and one
  `flutter-auto` process.
- Guest log captured before teardown with bounded counts for
  `FLR0026_MODEL_STAGE_*`, `FLR0280_MODEL_RENDERABLE`,
  `FLR0280_MODEL_MATERIAL`, Vulkan present, and kernel fault/OOM markers.
- QMP-only screenshot and eight-frame video with native and HUD ROI analysis.
- Exact rootfs/image identity, QMP hashes, runtime-log hash, and cleanup
  result recorded.
- Decide whether the first missing boundary is post-load Scene/renderable/
  material setup or the later camera/target/renderer path.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0311 proved `createAsset()` and `asyncBeginLoad()` complete for the
  selected Sequoia asset, but both zero and normal light runs have no vehicle
  pixels.
- The current image already contains opt-in stage markers controlled by
  `FLR0026_MODEL_STAGE_TRACE` and renderable/material markers controlled by
  `FLR0280_MODEL_CONTENT_TRACE`.
- FLR-0286 proves the same QEMU/Wayland/QMP stack can display colored native
  Filament geometry plus HUD when the direct LIT fixture is used.

### Hypotheses

1. Async resource completion or `addModelToScene()` does not reach the
   production model, leaving no renderables in the visible Scene.
2. Renderables and materials are valid, but camera/frustum/target ownership
   hides them after the post-load stage.
3. The FEngine/libLLVM fault occurs after valid model setup and is downstream
   of the actual 3D geometry.

### UNKNOWN

- Whether `MODEL_STAGE_COMPLETE` and `FLR0280_MODEL_MATERIAL` are emitted in
  the current normal-light runtime.
- Whether the vehicle is geometrically present outside the fixed native ROI.

## Plan / PDCA

### Plan

Run one marker-only A/B with normal light and the two existing diagnostic
environment variables. Keep the image, camera, selector, QEMU memory, and
QMP regions unchanged from FLR-0311.

### Do

The first run used the obsolete `FLR0026_MODEL_STAGE_TRACE` name; that
diagnostic was absent from the effective source and the mistake is retained
in the log. After static source inspection, the same run was repeated with
the effective `FLR0026_SCENE_STAGE_TRACE` name. No source or image change was
made.

### Check

Classify the first absent marker, then compare it with the QMP pixel result.
Do not infer visibility from a valid pointer or present result alone.

### Act

Open a separate source-change ticket only if the first missing operation is
identified and a minimal behavior change is justified.

## 2026-09-25 corrected runtime result

### Facts

- The corrected run reused the verified FLR-0311 rootfs, normal SUN light,
  one selected `sequoia_ngp.glb`, 4096 MiB QEMU, and QMP-only capture.
- Post-load markers reached the complete production path:
  `FLR0026_SCENE_STAGE_ASSET_LOADED=1`, `ADD_BEGIN=1`, `ENTITY_SET=1`,
  `SCENE_ADD_DONE=1`, and `ADD_COMPLETE=1`.
- `FLR0280_MODEL_RENDERABLE` occurred 12 times and
  `FLR0280_MODEL_MATERIAL` occurred 21 times. The trace includes the body
  `PaintColor`, `HeadLights`, `Chrome`, and other valid `base_lit_*` materials;
  color/depth write state is enabled for the opaque materials.
- Vulkan `QUEUE_PRESENT` occurred 3 times, followed by the known
  FEngine/libLLVM page fault. No OOM marker and no coredump entry were found.
- QMP screenshot and all eight video frames had SHA-256
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
- Native ROI `(440,220,400,360)` remained uniform black: `0/144000` changed,
  `0` chromatic, luma range `[1,6]`. HUD ROI was uniform white in this late
  capture (`12800/12800` changed, `0` chromatic).
- Runtime log SHA-256:
  `e3a7fbc4676e1c576675e4970b01cea6ccb348d1a52b65cdbcd20428f97bedbd`.
- QMP quit and cleanup passed with zero residual QEMU/flutter-auto targets and
  zero QMP sockets.

### Inference

- The production Sequoia has valid asset, Scene, renderable, and material
  state before the black QMP ROI. The first missing boundary is therefore not
  GLTF loading or material creation.
- Camera/frustum/culling, render-target ownership, or the downstream renderer
  fault remains unresolved. A valid material pointer and present result are
  not sufficient evidence of visible pixels.

### Act

- FLR-0312 is complete as the post-load boundary check.
- FLR-0313 owns the marker-only camera, transform, culling, and target
  visibility check. It must preserve the same QMP ROI and historical
  FLR-0070/FLR-0286 acceptance references.
