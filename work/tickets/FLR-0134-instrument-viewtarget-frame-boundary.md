# FLR-0134 — instrument the ViewTarget frame boundary

- Status: Done
- Priority: High
- Owner: Mac Devtool/source role with Mini build/runtime role
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0133](FLR-0133-isolate-unlinked-frame-fence.md), [FLR-0125](FLR-0125-trace-viewtarget-entry-path.md)
- Working log: `work/logs/2026-09-13-flr0134.md`

## Work unit

Make the C++ API boundary inside `ViewTarget::DrawFrame()` observable: the
`Renderer::beginFrame()` return value, the `render(fview_)` call, and the
matching `endFrame()` call. Use one diagnostic patch generated through Mac
Devtool, register it in the canonical `meta-fluorite-trial` layer, build on the
fixed Mini receiver, and validate with one QMP-only QEMU run.

This ticket is diagnostic only. It does not change camera selection, Shape
geometry, material, lighting, Fence behavior, Wayland stacking, or the
diagnostic Fence override's product behavior.

## Problem

FLR-0132 reached Shape readiness and camera application but its fixed 3D QMP
region was black. FLR-0133 showed that treating an unlinked Fence as ready
changes the frame-skip status but still leaves the fixed region black. The
source contains the `beginFrame` → `render(fview_)` relation, but the runtime
does not currently expose whether the ViewTarget call admitted a frame or
whether its Filament View was actually rendered.

## Success criteria

- Inspect the exact Mini-effective and Mac Devtool source/API signatures before
  editing; do not guess a replacement API.
- Generate an untouched official Devtool patch containing only bounded
  ViewTarget frame-boundary markers and register it in the layer with the
  correct nested `patchdir`.
- Pass canonical privacy/link/size/whitespace checks and the Mini progressive
  `do_patch`, `do_compile`, and full-image gates.
- In one QEMU run, record one-process launch, camera/Shape markers, explicit
  ViewTarget `beginFrame`/`render`/`endFrame` ordering, Vulkan target markers,
  and QMP-only pixels. Use the Fence-ready variable only as an explicitly
  labelled diagnostic condition if needed to admit a frame.
- Classify the first missing API boundary as one of: ViewTarget frame admission,
  ViewTarget render call, Filament view/scene/render-list state, Vulkan target
  draw, or presentation/composition.
- End with negotiated QMP quit, zero residual target processes, and no QMP
  socket. If a product correction is justified, open a separate implementation
  ticket before changing behavior.

## Facts

- FLR-0133's control reported repeated frame skips from an unlinked Fence.
- FLR-0133's diagnostic ready condition changed the frame status to admitted,
  but its fixed 3D QMP region remained uniformly black.
- `ViewTarget::DrawFrame()` calls `beginFrame(fswapChain_, ...)`, then calls
  `render(fview_)` and `endFrame()` only inside the true branch.
- Vulkan target markers are present in the current Filament source, but the
  bounded FLR-0132/0133 runtime extracts did not show a target-draw boundary.
- A native fixture has a historical QMP-positive control under FLR-0125, so
  QMP capture and the shared native Filament path are not globally broken.

## Inferences

- The next high-value measurement is the ViewTarget call boundary, because it
  separates a renderer admission problem from a missing/invalid Filament View
  or render-list problem without changing scene content.
- A `beginFrame=true` marker alone is insufficient; the `render(fview_)` and
  target-draw markers must be correlated with QMP pixels.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Experiment | Result |
| --- | --- | --- | --- |
| H1: ViewTarget still receives `beginFrame=false` in the clean Dart path | explicit marker reports false before any render marker | Devtool diagnostic markers with normal launch | REJECTED: repeated `beginFrame=true` after the diagnostic fence admission condition |
| H2: ViewTarget admits a frame but `render(fview_)` is not reached | begin true, no render/end marker | same run | REJECTED: repeated `render` and `endFrame` markers |
| H3: ViewTarget renders but its Filament View/scene/render-list produces no Vulkan draw | render/end markers present, target draw absent or zero QMP region | same run with target trace | REJECTED for “no draw”; normal Dart produced `index_count=36` target draws |
| H4: Vulkan target draw/present occurs but pixels remain black | target draw/present markers present, QMP remains black | same run and fixed-region analysis | SUPPORTED as the observed output boundary; exact scene/material/light cause is split to FLR-0135 |

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | ViewTarget C++ frame API contract and Filament View render reachability |
| Where | `ViewTarget::DrawFrame` → `Renderer::beginFrame/render/endFrame` → Vulkan target |
| When | after camera/Shape setup and before QMP pixel presentation |
| Who | ViewTarget, Filament renderer, Vulkan driver, Mini runtime roles |
| How | Devtool diagnostic markers, one Mini build, one QMP-only run |

## PDCA

### Plan

1. Inspect the exact current source and Devtool state; record the function
   signatures and existing marker convention.
2. Edit only the persistent Mac Devtool source and generate the official
   untouched patch.
3. Register/commit/bundle the layer and pass the fixed Mini build gates.
4. Run one QEMU with the conditional process guard, bounded runtime extraction,
   QMP screenshot/video evidence, and negotiated teardown.
5. Open a separate implementation ticket only if the boundary evidence proves
   a product behavior change is needed.

### Do

- Inspected the exact Mini-effective Dart and native APIs before changing
  source. The Mac Devtool-generated diagnostic patch was registered after the
  existing `flutter-auto` patch stack so its context remained valid.
- The canonical layer commit `71688934b3fe6d8d8b2afdf983c41725ed8dccd9`
  contains the unchanged official patch
  `0001-diag-trace-effective-ViewTarget-frame-boundary.patch` with SHA-256
  `9e248d02854d38e3d2e9a185b1710d1e8349351d994511db9c345111738d68a3`.
- Mini progressive gates passed: `do_patch`, `do_compile`, and the full
  `agl-ivi-image-flutter` image. The full image summary reported 11,898
  attempted tasks with all tasks successful.
- One QEMU run used the fixed qemuboot/image. The normal Dart launch and the
  native diagnostic fixture were run sequentially in that same QEMU, with one
  process at a time and QMP-only captures.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Source/API mapping | exact current signatures are recorded | Dart SceneView→native deserializer, ShapeSystem, MaterialDefinitions, CameraManager, and ViewTarget were inspected | PASS |
| Devtool patch | official patch, no hand-edited hunk | official generated patch registered after the existing stack | PASS |
| Mini build | `do_patch`, `do_compile`, full image | all three gates passed | PASS |
| ViewTarget boundary | begin/render/end ordering is visible | `beginFrame=true` → `render` → `endFrame` repeated | PASS |
| 3D visual gate | target draw/present and non-black QMP region | target draw/present passed, normal fixed region remained black; native fixture was blue | CLASSIFIED / PRODUCT FAIL |
| Teardown | negotiated quit and zero residuals | QMP quit accepted, residual targets/socket were zero | PASS |

### Act

- Mark this diagnostic unit Done and open FLR-0135 for the first concrete API
  correction: Dart `Light.toJson().color` currently emits an RGBA numeric
  array while native `Light::Light` reads an ARGB string. Do not mix that
  correction into this diagnostic patch.
- Keep the diagnostic fence-ready environment variable explicitly labelled;
  it admitted the frame but did not produce the missing normal-Dart pixels.

## Visual evidence

- Mini evidence root: `$EVIDENCE_ROOT/flr0113-authoritative/flr0134-viewtarget-frame`.
- Normal QMP screenshot: `qemu/qmp-after.ppm`, SHA-256
  `8612db713f9953926f36ea4c2fe31bc9193ba86818bc324b57719297c9dd3e23`.
  Fixed region `[300,250,620,400]` was black: 0 changed pixels, 0 edge
  pixels, 0 chroma, luma `[0,0]`.
- Native control screenshot: `qemu/qmp-native.ppm`, SHA-256
  `8ec56bf19f35fe54998d1b06431ea5aad7d8c11f0b180569dc94b1f0b702bf03`.
  The same fixed region contained a blue geometry bounding box
  `[484,250,312,266]` with 82,992 changed pixels.
- Normal runtime counts included `shape_ready=1`, `camera_applied=1`,
  `begin_true=32`, `target_draw2=5`, `vk_submit=2`, and `vk_present=3` in the
  bounded sample. The native control produced a visibly blue fixed region and
  eight distinct QMP video frames.
- The QEMU was ended by negotiated QMP quit; cleanup reported zero residual
  targets and zero QMP sockets.

## PDCA checker

- Status: PASS (diagnostic classification complete; normal-Dart 3D gate is
  intentionally not claimed as fixed)
- Checked by: Mac Devtool + Mini authoritative BitBake + one-QEMU QMP loop
- Findings: ViewTarget frame admission/render/end and Vulkan target/present
  are present. The remaining failure is downstream of the frame API and is
  now split into the Dart/native scene-content contract ticket FLR-0135.
