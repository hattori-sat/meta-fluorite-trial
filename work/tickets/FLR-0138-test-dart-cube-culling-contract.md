# FLR-0138 — test the self-made Dart Cube culling contract

- Status: Waiting
- Priority: High
- Owner: Mac Devtool/source + Mini build/runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0137](FLR-0137-test-dart-cube-unlit-material-path.md), [FLR-0136](FLR-0136-isolate-viewtarget-opacity-contract.md)
- Working log: `work/logs/2026-09-13-flr0138.md`

## Work unit

Keep the FLR0137 unlit material selection and all camera, geometry, frame,
ViewTarget, compositor, and QEMU inputs unchanged. Change only the self-made
Dart Cube's culling setting from the Dart Shape default to disabled, then run
the full Mac Devtool → canonical layer → Mini bundle → BitBake → QMP loop.

## Problem

FLR0137 changed the self-made Dart Cube from the lit helper to the existing
unlit helper. The normal Dart run still produced a uniformly black 3D region
despite Shape/Camera readiness, a 36-index target draw, Vulkan submit/present,
and zero runtime errors.

The visible native control fixture in the same ViewTarget path explicitly uses
`.culling(false)`. Dart `Shape.cullingEnabled` defaults to `true`, and native
`BaseShape::vBuildRenderable()` forwards that value to Filament. This is the
next source-owned difference to falsify; it is not yet proven to be the root
cause because the current Cube winding and camera direction also need to be
considered.

## Success criteria

- [x] Record Dart culling default, native forwarding, native visible-fixture
  setting, and Cube winding/camera relation.
- [x] Edit only the persistent Mac Devtool-managed source; do not edit
  `tmp/work` or hand-author the patch body.
- [x] Generate the official Yocto Devtool patch, register it unchanged under
  `meta-fluorite-trial`, and commit the canonical layer.
- [x] Transfer one bundle to the fixed Mini receiver and pass `do_patch`,
  `do_compile`, and full-image gates.
- [x] Run one normal Dart QEMU process with unlit material and culling
  disabled; capture QMP-only screenshot/video, fixed-region statistics, and
  bounded runtime markers.
- [x] Classify whether culling controls the missing self-made 3D pixels.
- [x] Negotiate QMP quit and verify zero residual QEMU, `runqemu`,
  `flutter-auto`, and QMP socket artifacts.

## Facts

- FLR0137 unlit A/B used the same Cube, camera, ViewTarget, and target path as
  the prior lit run. Its fixed QMP region was uniformly black across the
  screenshot and 12 captured frames.
- Dart `Shape` serializes `cullingEnabled`; its constructor default is `true`.
- Native `BaseShape::vBuildRenderable()` passes
  `renderable->IsCullingOfObjectEnabled()` to Filament's `.culling(...)`.
- The visible native control fixture in `ViewTarget::setupNativeMinimalGeometry`
  passes `.culling(false)`.
- The Dart Cube uses the native Cube's single-sided six-face index buffer and
  a non-identity rotation, with the fixture camera at `(5, 0, 0)` looking at
  the origin.
- FLR0137 proved that changing only the material asset path from lit to unlit
  does not restore visible pixels; Shape/Camera/draw/present remain active.
- Devtool source branch `devtool-flr0138-effective-culling` has context
  baseline commit `7c2a101849ff7aaabbf5176a0dc39e5cf4e53e92` and culling source
  commit `3e03936bab4bfc9a334a2c0a1699464f5bf13494`.
- Official Devtool generated
  `0001-test-compare-self-made-Cube-with-culling-disabled.patch`. The copied
  canonical patch `0058-filament_scene-compare-self-made-cube-culling-devtool.patch`
  is byte-identical; SHA-256 is
  `865524c0a3d19afc9e43945c958bdbcb8ede50d4d3b21a63435bae0b49b84480`.
- The first generated patch applied with fuzz 2 because the preceding `0057`
  patch changes the nearby comment context. It was discarded. The source was
  rebranched from the unlit commit, aligned to the post-`0057` context, and the
  official patch was regenerated; the subsequent Mac gate passed without
  patch-fuzz QA failure.
- `unlitUV.filamat` requires `baseMap`; its fragment shader samples the
  texture, multiplies RGB by sampled alpha, and then applies `baseColor`.
- `poGetUnlitMaterial(Colors.blue)` supplies only `baseColor`. Native
  `MaterialDefinitions` does not synthesize a default texture for `baseMap`.
- FLR0138's fixed QMP region `[300,250,620,400]` remained uniformly black:
  `changed_pixels=0`, `edge_pixels=0`, `chromatic_pixels=0`, and
  `luma_range=[0,0]`. Region SHA-256:
  `17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25`.
- FLR0138 runtime counts were
  `application=1 shape_ready=1 camera_applied=1 view_begin=31 begin_true=31
  begin_false=0 render_return=30 end_frame=30 fence_ready=29 skip_zero=29
  target_pass=8 target_draw=0 target_draw2=8 vk_submit=1 vk_present=0
  present=0 errors=0`.
- The bounded FLR0138 marker window contained offscreen `1024x1024` Cube
  draws and a non-swapchain `1280x800` draw, but no swapchain target/present
  marker.

## Inferences

- Culling was a valid source-side comparison, but the selected unlit material
  has an unsatisfied `baseMap` input, so the result cannot isolate culling.
- The absent swapchain/present marker further prevents a strong visual culling
  conclusion.
- The next smallest source-owned correction is to bind an existing opaque
  texture through `poGetUnlitTexturedMaterial` while keeping culling disabled.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: Dart culling state removes the Cube | culling-disabled produces a stable blue Cube in the fixed region | culling-disabled remains black after valid material input and swapchain boundary |
| H2: the unlit material's unbound `baseMap` suppresses the Cube | binding an opaque `baseMap` produces geometry | textured unlit material remains black with valid target/present markers |
| H3: another geometry/camera/target contract owns the black result | valid textured material remains black | textured material produces visible geometry |

UNKNOWN: no runtime marker currently reports Filament's per-entity culling
state, effective sampler binding, or post-transform clip result.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | Self-made Dart Cube culling enabled versus disabled |
| Where | Dart Shape JSON → CommonRenderable → BaseShape RenderableManager builder |
| When | Shape creation before the normal ViewTarget frame loop |
| Who | Dart fixture/shape role and native BaseShape renderable role |
| How | One Devtool source edit, official patch, one Mini image, one QMP run |

## PDCA

### Plan

1. Reconfirm culling defaults, Cube winding, and the native visible control.
2. Change only the fixture's culling setting in persistent Devtool source and
   generate an official patch.
3. Build the exact layer on the Mini and run one unlit normal-Dart QEMU.
4. Use QMP pixels and target markers to decide whether culling owns the black
   output, then split the next falsifiable boundary.

### Do

- Reused the existing Mac Podman machine, fixed container, state bind, and
  Devtool-managed source. Existing source branch `devtool-flr0138-dart-culling`
  was preserved; the effective-context branch was created from the FLR0137
  unlit commit.
- Committed a context-only source baseline, then committed the culling A/B
  through the Devtool source Git wrapper. The source diff in the A/B commit is
  only `cullingEnabled: false`.
- Reconnected the source with official `modify --no-extract`, aligned the
  Devtool `initial_rev` to the context baseline, and ran official
  `update-recipe --mode patch --append --no-remove --force-patch-refresh`.
- Copied the generated patch unchanged into the canonical layer as `0058` and
  registered it after `0057` and before `0175`.
- The first metadata retry used a nonexistent abbreviated-SHA expansion and
  failed before patch generation; the actual SHA was read and corrected. This
  failed command did not change the canonical layer.
- One bundle reached the fixed Mini receiver; Mini `do_patch` (104/104),
  `do_compile` (2590/2590), and full image (11898/11898) passed.
- One normal-Dart QEMU run captured QMP screenshot/video and showed a black
  fixed 3D region. QMP quit and residual cleanup passed.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| API mapping | Dart default, native forwarding, and native fixture setting are recorded | recorded in Facts and Problem | PASS |
| Source edit | only fixture culling selection changes | Devtool source commit `3e03936`; one A/B source file | PASS |
| Official patch | generated by Devtool and unchanged in layer | generated/canonical SHA `865524c0...b84480`; Mac gate no fuzz | PASS |
| Mini build | progressive gates pass | 104/104, 2590/2590, 11898/11898 | PASS |
| Runtime | culling-disabled result correlates with QMP and target markers | QMP black; no swapchain/present marker in window | INCONCLUSIVE |
| Teardown | zero residual target processes and QMP socket | QMP quit accepted; residual targets/sockets zero | PASS |

### Act

- The culling patch passed the authoritative Mini build/runtime loop, but the
  visual result is confounded by the unbound `baseMap` and incomplete
  swapchain observation.
- FLR0139 owns the next material-input correction; do not reuse this ticket or
  infer a culling fix from the black QMP result.

## Visual evidence

- QMP evidence is stored under `$EVIDENCE_ROOT/flr0138-dart-culling/qemu`.
  The local inspection copies are `qmp-culling.png`, `qmp-culling.ppm`, and
  `qmp-culling-runtime.mp4`; raw artifacts remain outside Git.

## PDCA checker

- Status: PASS_WITH_OPEN_BOUNDARY
- Checked by: Mac source / Mini build / QMP runtime roles
- Findings: official patch, Mini build, QMP capture, and teardown passed.
  Culling is not isolated because the unlit shader input contract is
  incomplete and the bounded runtime did not reach swapchain Present.
