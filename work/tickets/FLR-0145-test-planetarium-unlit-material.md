# FLR-0145 — test Planetarium unlit material API contract

- Status: Done
- Priority: High
- Owner: Mac Devtool/source + Mini build/runtime + Dart/Native material roles
- Created: 2026-09-14
- Updated: 2026-09-14
- Depends on: [FLR-0144](FLR-0144-isolate-planetarium-light-native-fault.md), [FLR-0139](FLR-0139-bind-dart-unlit-base-map.md)
- Working log: `work/logs/2026-09-14-flr0145.md`

## Work unit

Keep the FLR-0144 Planetarium camera, shape list, scene light list, direct-light
runtime, ViewTarget, compositor, build/TMPDIR, and QEMU profile unchanged.
Change only the visible Planetarium planet material construction from the lit
helper to the existing unlit helper that satisfies the packaged shader's
`baseMap` input. Use the official Mac Devtool → canonical layer → Mini bundle →
BitBake → QMP loop.

## Problem

FLR-0144 separated light entity setup from direct contribution: disabling
contribution kept the faceted Planetarium sphere and present returns stable, but
the material remained black; enabling contribution correlated with an
FEngine/libLLVM-family fault. Static inspection shows that the visible planets
currently use `lit.filamat`, while the packaged `unlitUV.filamat` is a separate
unlit shader whose declared `baseMap` input must be bound.

The color-only `poGetUnlitMaterial` helper supplies only `baseColor` and is
therefore not a valid API match for `unlitUV.filamat`. FLR-0139 already proved
that binding `floor_basecolor.png` through `poGetUnlitTexturedMaterial` is the
minimal accepted unlit contract for the self-made Dart fixture.

## Facts

- `PlanetariumSceneView.getSceneShapes()` creates ten visible planets and
  currently calls `poGetLitMaterial(planetColors[name]!)` for each.
- `poGetUnlitTexturedMaterial()` loads the packaged
  `assets/materials/texture/floor_basecolor.png`, binds it as `baseMap`, and
  applies the supplied `baseColor`.
- `unlitUV.mat` declares `shadingModel: unlit`, requires `uv0`, samples
  `baseMap`, premultiplies sampled alpha, and multiplies by `baseColor`.
- Native `MaterialDefinitions` loads texture parameters before applying only
  parameters advertised by the material package. No native default texture is
  synthesized for a missing `baseMap`.
- FLR-0144 direct-contribution-disabled evidence is the fixed runtime control:
  geometry/present are stable but the candidate region is chroma `0`.
- The persistent Devtool source branch is `devtool-flr0145-unlit-planetarium`;
  source commit `b001c94` changes only the planet-generation loop's material
  call. Devtool `finish --force-patch-refresh` generated the official patch
  with SHA-256
  `89f8cef3e8a13ed4d41f22f7532a3bdba0413c5c4bb864b504009804e1d25332`.
- The unchanged generated patch is registered as
  `0063-filament_scene-use-unlit-planetarium-material-devtool.patch` after
  0062. Mac fixed-container `do_patch` passed 104 tasks, with 100 reused and
  all successful.

- Canonical commit `d701a7b` was handed off by bundle to the fixed Mini
  receiver. Mini `do_patch`, target compile, and full image build passed using
  the existing build/TMPDIR.
- The normal-Dart QEMU run used one `flutter-auto`, reached Planetarium
  `SHAPE_READY` markers and Vulkan submit, then stopped before the queue-present
  return. QMP native candidate `[300,250,620,400]` was `0/248000`, luma
  `[0,0]`, chroma `0`.
- The direct-light-disabled A/B used the same image and returned repeatedly
  from queue-present, but its QMP native candidate remained `0/248000`.
- The material API change did not restore colored Planetarium pixels. No
  material/texture load error was observed; the repeated `uvOffset` and
  `uvScale` messages remain absent-parameter diagnostics, not a proven cause.
- A current-image native fixture reached
  `FLUORITE_NATIVE_PURE_FIXTURE_SETUP_DONE`,
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_READY vertices=8 indices=36`, and repeated
  queue-present returns, but its QMP native candidate was black. Static API
  tracing shows that this comparison is invalid after the camera fix: the
  fixture cube is at the origin, while the deserialized Planetarium camera is
  `eye=(-640,0,680)` looking at `target=(-720,0,680)`. FLR-0147 owns this
  camera-frame correction.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | Planetarium visible planets: lit material versus baseMap-satisfied unlit material |
| Where | Dart helper → Material JSON → Native MaterialDefinitions → Filament MaterialInstance |
| When | Planet shape creation before the stable scene pass/present loop |
| Who | Dart material role, Native material/texture role, Filament backend/runtime role |
| How | One Devtool source edit, official patch, one Mini image, one QMP run with direct light enabled |

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: the lit shader/direct-light consumer is the first source-owned fault | baseMap-satisfied unlit planets produce chromatic QMP pixels and avoid the FEngine fault | unlit run faults at the same boundary |
| H2: material API is not the owner | unlit planets remain black or transparent despite valid texture/present markers | stable chromatic planet pixels |
| H3: the packaged unlit path itself is invalid for Sphere | texture load/material application reports an error or geometry disappears | stable unlit geometry with nonzero color |

## Success criteria

- [x] Record the Dart helper, `unlitUV` shader inputs, texture asset, and Native
  parameter mapping.
- [x] Edit only the persistent Mac Devtool source and generate the patch with
  Yocto-standard Devtool; do not hand-author the generated patch body.
- [x] Copy the unchanged generated patch into `meta-fluorite-trial`, register
  it after patch 0062, and commit the canonical layer.
- [x] Pass Mac fixed-container `do_patch`, then transfer one bundle to the
  fixed Mini receiver and pass Mini `do_patch`, target `do_compile`, and full
  image build using the fixed TMPDIR.
- [x] Run exactly one normal-Dart QEMU with direct light enabled; capture QMP
  screenshot/video, fixed-region pixel statistics, runtime markers, and fault
  evidence if present.
- [x] Negotiate QMP quit and verify zero residual QEMU, runqemu,
  `flutter-auto`, and QMP socket artifacts.
- [x] Classify whether actual colored Planetarium pixels are restored. Do not
  claim success from runtime markers alone.

## Scope

### In scope

- Visible Planetarium planet material helper selection and its declared
  `baseMap` API contract.
- One fixed image/runtime comparison against FLR-0144.

### Out of scope

- Camera or shape geometry changes.
- Light position, light contribution, or Native light builder changes.
- HUD alpha/stacking, scene transition, and production GLB path.

## PDCA

### Plan

1. Confirm the current Devtool source branch and exact material/texture API
   relationship.
2. Replace only the planet-generation loop's material call (instantiated for
   the ten visible planets) with
   `poGetUnlitTexturedMaterial("assets/materials/texture/floor_basecolor.png", color: planetColors[name]!)`.
3. Generate and register the official Devtool patch, then pass Mac and Mini
   build gates.
4. Run one QMP-first runtime with direct contribution enabled and classify
   chromatic pixels, present, and fault evidence.

### Do

- FLR-0146 first restored the missing standard workspace-layer metadata in the
  existing Podman container; the repeated `modify --no-extract` then passed.
- The Devtool source branch `devtool-flr0145-unlit-planetarium` was created
  from `9ae43aa`. Only `planetarium_scene.dart` changed, and source commit
  `b001c94` was created through the bounded source-Git wrapper.
- Official `finish --force-patch-refresh` generated the patch recorded above;
  the patch was copied unchanged and registered after 0062. Mac `do_patch`
  passed 104/104 tasks.
- Mini bundle, authoritative build, QMP runtime, and teardown are pending.

### Check

- Require source diff, patch SHA, Mac/Mini build counts, rootfs SHA, QMP
  region metrics, runtime/fault boundary, and teardown counts.

### Act

- The patch is retained as the correct Dart→Native material API alignment, but
  it is not a 3D display fix. The normal run still faults at direct-light
  contribution and the stable direct-light-disabled run is still black.
- The current pure-fixture black result is not promoted to a global render
  failure because its cube/camera coordinate frames do not match after the
  camera contract fix. FLR-0147 owns that positive-control repair.

## PDCA checker

- Status: PASS
- Checked by: bounded QMP/runtime evidence review
- Findings: build, bundle, normal runtime, direct-light-disabled A/B, QMP
  capture, video capture, and teardown are recorded; colored Planetarium
  pixels were not restored, so the next camera-frame ticket is required.
