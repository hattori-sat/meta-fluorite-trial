# FLR-0137 — test the self-made Dart Cube unlit material path

- Status: Done
- Priority: High
- Owner: Mac Devtool/source + Mini build/runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0136](FLR-0136-isolate-viewtarget-opacity-contract.md), [FLR-0135](FLR-0135-align-dart-light-color-wire-format.md)
- Working log: `work/logs/2026-09-13-flr0137.md`

## Work unit

Change only the self-made Dart Cube fixture from the lit material helper to
the existing unlit material helper, then run the full Mac Devtool → canonical
layer → Mini bundle → BitBake → QMP loop. Geometry, camera, Light, ViewTarget
opacity, compositor, fence diagnostics, and QEMU profile stay unchanged.

## Problem

FLR-0135 aligned the Light color wire format and FLR-0136 proved that forcing
the normal ViewTarget opaque does not restore 3D. The normal path still
reaches a 36-index Cube draw and Vulkan Present while the fixed QMP 3D region
is uniformly black.

The Dart fixture already has two material helpers. The current fixture uses
`poGetLitMaterial(Colors.blue, emissiveColor: Colors.blue,
emissiveIntensity: 1.0)`; the existing alternate helper is
`poGetUnlitMaterial(Colors.blue)`. Native `MaterialDefinitions` consumes
`assetPath` and typed parameters, but the current runtime has no material
parameter marker. This A/B selects whether the lit material/shader contract
is the first source-owned visual divergence.

## Success criteria

- [x] Record the exact Dart fixture material helper and native material input
  contract.
- [x] Edit only the persistent Mac Devtool-managed source; do not edit
  `tmp/work` or hand-author the patch body.
- [x] Generate the official Yocto Devtool patch, register it unchanged under
  `meta-fluorite-trial`, and commit the canonical layer.
- [x] Transfer one bundle to the fixed Mini receiver and pass `do_patch`,
  `do_compile`, and full-image gates.
- [x] Run one normal Dart QEMU process with the unlit fixture and capture
  QMP-only screenshot/video, fixed-region statistics, and bounded runtime
  markers.
- [x] Classify whether unlit material restores visible self-made 3D.
- [x] Negotiate QMP quit and verify zero residual QEMU, `runqemu`,
  `flutter-auto`, and QMP socket artifacts.

## Facts

- FLR-0136 opaque-only normal Dart remained uniformly black in the fixed 3D
  region while application, Shape, Camera, frame, target, and Present markers
  remained active.
- `poGetMinimal3dFixtureShapes()` creates one self-made Cube at the origin
  with the existing fixture camera and blue material.
- The current fixture material is the lit Filament asset with blue base color,
  blue emissive color, emissive intensity 1.0, roughness, metallic, and
  reflectance parameters.
- The existing unlit helper supplies the same blue color through the unlit
  material asset. No model or external scene asset is introduced.
- Native `MaterialDefinitions` reads material `assetPath`, `url`, and typed
  `parameters`; native COLOR input is a string after FLR-0116.
- The persistent Devtool source branch is `devtool-flr0137-unlit-material` at
  source commit `afc8390` (`test: compare Dart fixture with unlit material`).
- Yocto Devtool generated
  `0001-diag-compare-Dart-fixture-with-unlit-material.patch`; its SHA-256 is
  `85bf6bd689c8d034bb89d4cf8da5d8bcb3c7ba7809d662204b389e8ef5aa6e88`.
- The unchanged generated patch is registered as
  `0057-filament_scene-compare-self-made-cube-unlit-material-devtool.patch`.
- Mac fixed-container recipe `do_patch` passed: 104 tasks attempted, 103
  reused, all tasks succeeded.
- Mini fixed build passed recipe `do_patch` (104 tasks), recipe `do_compile`
  (2590 tasks), and full image (11898 tasks). The resulting image was tested
  with one normal Dart QEMU process.
- QMP captured a 1280x800 screenshot and 12 frames. The fixed region
  `[300,250,620,400]` had `changed_pixels=0`, `edge_pixels=0`,
  `chromatic_pixels=0`, `luma_range=[0,0]`, and the background region SHA
  `17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25`.
- Runtime counts were `application=1 shape_ready=1 camera_applied=1
  view_begin=50 begin_true=49 begin_false=0 render_return=49 end_frame=49
  fence_ready=48 skip_zero=48 target_pass=153 target_draw=19 target_draw2=77
  vk_submit=38 vk_present=93 present=0 errors=0`. Target logs include a
  36-index non-swapchain draw and 1280x800 render pass/present.
- QMP teardown was negotiated and accepted; residual state was
  `qemu=0 runqemu=0 flutter-auto=0 socket=absent`.

## Inferences

- Unlit-only is the smallest content/API experiment because it changes one
  material selection while keeping the Cube vertex/index data and render
  boundary fixed.
- A visible unlit Cube would prove the normal Dart scene can produce 3D
  pixels and isolate the remaining defect to the lit material path or its
  parameter contract.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: lit material/shader input suppresses the self-made Cube | unlit-only produces a stable blue Cube in the fixed region | unlit-only remains black with the same target draw/present boundary |
| H2: material selection is not the root cause | unlit-only remains black | unlit-only produces visible geometry |
| H3: unlit visibility proves geometry/composition and leaves a lit-material API defect | unlit-only is visible while the current lit fixture is black | lit and unlit are both black |

UNKNOWN: the current native logs do not expose the effective material asset and
parameter map per entity; the QMP A/B plus source contract will classify the
boundary.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | Self-made Dart Cube lit versus unlit material path |
| Where | Dart material helper → SceneView shapes → MaterialDefinitions → Filament material |
| When | Shape setup before the normal ViewTarget frame loop |
| Who | Dart fixture/material role and native material deserializer role |
| How | One Devtool source edit, official patch, one Mini image, one QMP A/B |

## PDCA

### Plan

1. Reconfirm the two helper contracts and persistent Devtool source.
2. Change only the fixture material helper and generate an official patch.
3. Build the exact layer on the Mini and run one unlit normal-Dart QEMU.
4. Use QMP pixels and target markers to decide whether lit material owns the
   black output, then split the next ticket.

### Do

- The Devtool source branch was created from the prior Light-alignment source
  branch. Only the self-made Cube material selection changed from
  `poGetLitMaterial(Colors.blue, emissiveColor: Colors.blue,
  emissiveIntensity: 1.0)` to `poGetUnlitMaterial(Colors.blue)`.
- The first `finish` attempt failed because the prior Devtool `finish` had
  reset the recipe registration (`No recipe named ... in your workspace`).
  Re-running `modify --no-extract` against the same persistent source restored
  the registration, and the official `finish` then generated the patch.
- The generated patch was copied unchanged into the canonical layer and
  registered after patch `0056` and before the existing `0175` entry.
- Mini `do_patch`, `do_compile`, and full image all passed on the fixed
  receiver/build/TMPDIR. The resulting normal-Dart QEMU run passed preflight,
  start, guest-ready, serial launch, QMP capture/video, and negotiated
  teardown.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| API mapping | Dart lit/unlit helper and native material input are recorded | recorded in Facts | PASS |
| Source edit | only fixture material selection changes | Devtool source commit `afc8390`; one source file | PASS |
| Official patch | generated by Devtool and unchanged in layer | generated SHA matches registered layer patch | PASS |
| Mac recipe gate | canonical recipe applies the patch | 104/104 tasks succeeded | PASS |
| Mini build | progressive gates pass | 104/104, 2590/2590, 11898/11898 succeeded | PASS |
| Runtime | unlit fixture result is correlated with QMP and target markers | uniformly black fixed region; draw/present active | PASS (negative) |
| Teardown | zero residual target processes and QMP socket | `qemu=0 runqemu=0 flutter-auto=0 socket=absent` | PASS |

### Act

- H1 (lit material/shader alone suppresses the Cube) is rejected: unlit was
  also black with the same active draw/present boundary.
- H2 is supported for this run: material selection is not the first observed
  owner of the black pixels.
- The next boundary is the Dart/native culling contract and is tracked in
  FLR-0138; this ticket is not reused.

## Visual evidence

- Evidence is stored under `$EVIDENCE_ROOT/flr0137-unlit-material/qemu` on the
  Mini PC. The QMP screenshot is `qmp-unlit.ppm`; the 12-frame capture is under
  `qmp-unlit-frames/`. Raw runtime logs and images remain outside Git.

## PDCA checker

- Status: PASS
- Checked by: Fluorite integration role
- Findings: the unlit A/B is a valid negative classification. It does not
  restore 3D pixels, but it proves the app reaches the normal Shape/Camera /
  render / submit / present boundary without runtime errors or residual
  processes. The next ticket compares render-state differences with the
  visible native control fixture.
