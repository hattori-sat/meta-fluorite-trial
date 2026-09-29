# FLR-0139 — bind the Dart unlit material base map

- Status: Done
- Priority: High
- Owner: Mac Devtool/source + Mini build/runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0138](FLR-0138-test-dart-cube-culling-contract.md), [FLR-0137](FLR-0137-test-dart-cube-unlit-material-path.md)
- Working log: `work/logs/2026-09-13-flr0139.md`

## Work unit

Keep the FLR0138 self-made Dart Cube, camera, `cullingEnabled: false`, Light,
ViewTarget, compositor, build, and QEMU inputs unchanged. Change only the
fixture material construction from the color-only unlit helper to the existing
textured unlit helper, binding the packaged opaque `floor_basecolor.png` as
`baseMap` while retaining blue `baseColor`.

## Problem

The current Dart fixture selects `unlitUV.filamat`. Its shader requires
`baseMap`, multiplies sampled alpha into the output, and then applies
`baseColor`. The Dart `poGetUnlitMaterial` helper supplies only `baseColor`,
while native MaterialDefinitions does not synthesize or bind a texture. The
FLR0137 and FLR0138 black results therefore do not prove that material choice
or culling is irrelevant.

## Success criteria

- [x] Record the Dart helper, packaged material shader, texture asset, and
  native parameter mapping.
- [x] Edit only the persistent Mac Devtool-managed source and commit the source
  change through its Git wrapper.
- [x] Generate the official Yocto Devtool patch and register it unchanged under
  `meta-fluorite-trial`.
- [x] Pass Mac recipe `do_patch` without patch-fuzz QA errors.
- [x] Transfer one bundle to the fixed Mini receiver and pass Mini
  `do_patch`, `do_compile`, and full-image gates.
- [x] Run exactly one normal-Dart QEMU with a capture window long enough to
  observe a swapchain target/present marker; capture QMP-only screenshot/video,
  fixed-region statistics, and bounded runtime markers.
- [x] Classify whether binding `baseMap` restores self-made 3D pixels.
- [x] Negotiate QMP quit and verify zero residual QEMU, `runqemu`,
  `flutter-auto`, and QMP socket artifacts.

## Facts

- The fixture currently uses `poGetUnlitMaterial(Colors.blue)` and
  `cullingEnabled: false`.
- `unlitUV.filamat` is compiled from `unlitUV.mat`, which declares `baseMap`
  and `baseColor`, requires `uv0`, and computes `baseColor` from a sampled
  texture multiplied by the supplied color.
- `poGetUnlitTexturedMaterial` already binds `baseMap` through
  `Texture.asset`, sets the color parameter, and is used elsewhere in the
  Example Demo.
- `floor_basecolor.png` is a packaged `1024x1024` RGB PNG with no alpha
  channel; it is an opaque texture candidate for the shader's `tex.a` path.
- Native MaterialDefinitions accepts the Dart `baseMap` texture parameter and
  loads it before applying the material instance parameters.
- FLR0138 had a black fixed QMP region and no swapchain/present marker in its
  bounded capture interval, so it cannot classify culling independently.
- The persistent Mac Devtool source commit is `450511d`, based on the
  3e03936 culling baseline.
- Standard split-component registration (`component-add` at 3e03936, then
  source checkout at 450511d) generated the official patch
  `0001-diag-bind-Dart-unlit-base-map.patch` with SHA-256
  `f1796ad72241f3f29160179a6fa673783843fa80fc0c50c257d53d2242b26232`.
- The unchanged generated patch is registered in the layer as
  `0059-filament_scene-bind-dart-unlit-base-map-devtool.patch`, immediately
  after 0058.
- Mac Podman `do_patch` passed after the fixed mount/xattr gate.
- Mini `do_patch`, `do_compile`, and the full `agl-ivi-image-flutter` image
  all succeeded. The first wrapper exit code 1 was only an artifact-selector
  glob error for the timestamped qemuboot filename; the corrected selector
  found all three inputs.
- The single normal-Dart QEMU passed preflight, start, guest-ready, serial
  synchronization, launch, boundary, counts, target markers, QMP capture,
  and QMP video. Runtime counts included `application=1`,
  `shape_ready=1`, `camera_applied=1`, `target_pass=201`,
  `target_draw=25`, `target_draw2=235`, `vk_submit=52`,
  `vk_present=128`, `present=0`, and `errors=0`.
- Runtime target markers included a swapchain render pass and
  `FLUORITE_VK_PRESENT_CALL_RETURN result=0`.

## Inferences

- Binding `baseMap` is the smallest source-side correction that makes the
  selected Filament material's declared inputs satisfiable.
- A geometry-bearing, chromatic QMP region after the swapchain/present marker
  would validate the Dart Material API path and provide a meaningful culling
  baseline for a later ticket.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: unbound `baseMap` makes the unlit output transparent/black | textured unlit helper produces nonzero chromatic cube pixels | valid texture load plus swapchain/present remains black |
| H2: texture loading or asset packaging fails | runtime logs show a bounded asset/material failure and QMP remains black | texture loads without error |
| H3: the first owner is camera/geometry/target rather than material input | valid textured material remains black with target/present active | textured material produces visible geometry |

- H1: PASS — the final image and runtime produced a non-uniform Cube region
  after the baseMap binding.
- H2: NOT SUPPORTED — no bounded asset/material error appeared, and the
  textured path produced geometry. Detailed release asset logs remain limited.
- H3: FALSIFIED for this material-input trial — camera/geometry/target reached
  swapchain and present while the Cube was visible.

UNKNOWN: why the 2D HUD seen in FLR0138 is absent from the full FLR0139 QMP
frame. That composition boundary is separated into FLR-0140.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | Unlit material with no `baseMap` versus the same material with `baseMap` |
| Where | Dart helper → Material JSON → native MaterialDefinitions → Filament MaterialInstance |
| When | Shape material creation before the normal ViewTarget frame loop |
| Who | Dart material helper and native material/texture loader roles |
| How | One Devtool source edit, official patch, one Mini image, one QMP run |

## PDCA

### Plan

1. Verify the material and texture contracts from source and package assets.
2. Change only the fixture helper call through the persistent Mac Devtool
   source and generate the official patch.
3. Run Mac recipe validation, then hand off one canonical bundle to Mini.
4. Run progressive Mini BitBake gates and one normal-Dart QMP runtime with a
   bounded wait for swapchain Present.
5. Use QMP pixels plus runtime markers to classify the material-input boundary.

### Do

- Ticket created after FLR0138 showed that culling was confounded by the
  unbound unlit `baseMap` and an incomplete swapchain observation window.
- The Mac Devtool source was edited and committed as `450511d`; the standard
  split-component registration generated the official patch, which was copied
  unchanged as 0059. Mac `do_patch` and canonical `make verify` passed.
- One bundle at canonical commit `6034796` reached the fixed Mini receiver;
  Mini patch, compile, and full image gates passed.
- One normal-Dart QEMU produced the QMP-only screenshot/video and the fixed
  region analysis: `changed_pixels=217400`, `edge_pixels=1230`,
  `chromatic_pixels=0`, `luma_range=[1,255]`, and
  `geometry_indicator=present`. The edge bounding box was
  `[525,302,232,202]`.
- Mac copies of the QMP evidence are under
  `$LOCAL_QMP_EVIDENCE_ROOT/flr0139-dart-unlit-base-map/`; screenshot SHA-256
  is `d34cdf3d4db64e50a3fbe307a3a40039e506fba684e4bc4839bf7f3ab9302f38`
  and video SHA-256 is
  `457b706c55bde61bd7788673e69f0941b5a7e56dccd4fe41005bee67c92681f1`.
- QMP capabilities negotiation and quit passed; residual QEMU, runqemu,
  flutter-auto, and QMP socket counts were all zero.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| API mapping | helper, shader, texture, and native mapping recorded | recorded in ticket | PASS |
| Source edit | only the fixture material helper changes | 450511d; one source file | PASS |
| Official patch | generated by Devtool and copied unchanged | 0059; SHA recorded above | PASS |
| Mac recipe gate | patch applies without fuzz QA error | Podman `do_patch` passed | PASS |
| Mini build | progressive gates pass | `do_patch`, `do_compile`, full image passed | PASS |
| Runtime | valid target/present boundary and QMP classification | QMP geometry indicator present | PASS |
| Teardown | negotiated QMP quit and zero residuals | all target/socket counts zero | PASS |

### Act

- Close FLR0139 as the material-input A/B is classified. Keep the missing 2D
  HUD composition boundary in separate FLR-0140 and do not modify this ticket's
  0059 patch while investigating it.

## Visual evidence

- QMP-only screenshot: `qmp-base-map.png` (geometry indicator present; SHA
  recorded above).
- QMP-only video: `qmp-base-map-runtime.mp4` (12 frames; SHA recorded above).
- Raw evidence is stored under
  `$EVIDENCE_ROOT/flr0139-dart-unlit-base-map/qemu`; screenshots/videos remain
  outside Git.

## PDCA checker

- Status: PASS
- Checked by: Fluorite integration role
- Findings: API contract, official patch provenance, Mac gate, Mini image,
  single QEMU QMP evidence, and teardown all satisfy the ticket scope. The
  2D HUD/composition observation is explicitly split to FLR-0140.
