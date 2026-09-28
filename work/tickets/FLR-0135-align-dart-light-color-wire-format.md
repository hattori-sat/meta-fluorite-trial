# FLR-0135 — align the Dart Light color wire format

- Status: Done
- Priority: High
- Owner: Mac Devtool/source + Mini build/runtime roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0134](FLR-0134-instrument-viewtarget-frame-boundary.md), [FLR-0116](FLR-0116-flutter-auto-material-variant-crash.md)
- Working log: `work/logs/2026-09-13-flr0135.md`

## Work unit

Align the Dart `Light.toJson()` color field with the native
`Light::Light` deserializer, then determine whether the corrected Light input
changes the normal Fluorite Example Demo's black 3D result. This is one API
correction and one QMP visual validation unit. It must not change camera,
material, ViewTarget, compositor, fence, or QEMU behavior.

## Problem

FLR-0134 classified the current failure downstream of ViewTarget frame
admission and render reachability. The normal Dart fixture reaches a 36-index
Cube draw and Vulkan present but its fixed QMP 3D region is uniformly black;
the same QEMU native fixture displays blue geometry.

The exact source contract now shows a mismatch:

- Before this ticket, Dart `Light.toJson()` sent `color?.storage64`, a
  four-element numeric RGBA array; the committed source now sends `color.toHex()`.
- Native `Light::Light` decodes `color` into `std::string m_szColor`, and
  `LightSystem` passes that string to `colorOf()`.

Before this ticket, the native path consequently could not consume the
explicit Dart color and used its default color-temperature fallback. This was
a real API mismatch; the corrected runtime result shows it was not the sole
cause of the black 3D output.

## Success criteria (preconditions complete; runtime gates open)

- [x] Record the exact Dart/native type contract and compare at least the
  chosen string direction with the current native semantics.
- [x] Edit only the persistent Mac Devtool-managed source; do not edit
  `tmp/work` or hand-author the patch body.
- [x] Generate the official Yocto Devtool patch and register it unchanged under
  `meta-fluorite-trial`, and commit the canonical layer.
- [x] Transfer one complete-history bundle to the fixed Mini authoritative
  receiver and pass progressive `do_patch`, `do_compile`, and full-image
  gates.
- [x] Run one normal Dart QEMU process with the fixed image and existing
  diagnostics. Capture QMP-only screenshot/video, target markers, and bounded
  runtime errors.
- [x] Classify the result as Light-contract contribution, unchanged
  Material/scene content, or composition/target UNKNOWN.
- [x] Negotiate QMP quit and verify zero residual QEMU, `flutter-auto`, and
  QMP socket artifacts.

## Facts

- FLR-0134's normal run reached `shape_ready=1`, `camera_applied=1`, repeated
  `beginFrame=true`/`render`/`endFrame`, a target `index_count=36` draw, and
  Vulkan present while the fixed 3D QMP region stayed black.
- The native positive control in the same QEMU showed a blue geometry region,
  so the shared QMP/Vulkan/Wayland path can display 3D.
- Dart `Light.toJson()` currently serializes color using `Float64List
  storage64`.
- Native `Light::Light` currently reads `color` as a string and
  `LightSystem::vBuildLight()` calls `colorOf()` only when that string is
  non-empty; otherwise it uses `colorTemperature`.
- Material COLOR already has a separate established string-wire fix in
  FLR-0116/patch `0052`; this ticket must not conflate the two contracts.
- Mini effective configuration registered patch `0056` in `SRC_URI` and used
  the fixed build/TMPDIR; the receiver revision was the canonical tip
  `2df2e64edb3c7f06366959e456b61a621ab6562c`.
- Mini `do_patch`, `do_compile`, and full `agl-ivi-image-flutter` all passed;
  the full image attempted 11,898 tasks and all succeeded.
- The normal QMP run used the newly built image and showed the expected 2D
  HUD/controls, but the fixed 3D region was uniform black: 0 changed pixels,
  0 edge pixels, 0 chromatic pixels, and luma `[0,0]`.
- The same run still reached `application=1`, `shape_ready=1`,
  `camera_applied=1`, `begin_true=32`, `render_return=31`, `end_frame=31`,
  `target_draw2=5`, `vk_present=3`, and `errors=0`.

## Inferences

- Changing only Dart Light color serialization is the smallest direct way to
  make the sender and receiver agree without broadening the native parser.
- For the current white fixture light, the visual delta may be zero because
  native fallback color temperature is also near white. A no-change result is
  useful: it rejects Light color as the sole cause and preserves the next
  Material/scene-content investigation.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: Light color mismatch changes the effective normal scene output | corrected string reaches native color path and QMP pixels change toward visible Cube | REJECTED: corrected run remained black with the same target draw/present sequence |
| H2: fallback color is visually equivalent for the white fixture | API correction leaves QMP black | SUPPORTED for this white fixture: no visual delta |
| H3: the remaining fault is lit Material/scene content or target composition | Light correction does not change black fixed region; native control remains positive | SUPPORTED as the next boundary; exact owner remains UNKNOWN |

UNKNOWN: native runtime still does not emit an explicit Light input type/value
marker. Source and build evidence prove the corrected wire format is applied;
the unchanged QMP result proves only that Light color is not the sole cause.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | Dart `Light.color` wire type and native Light parser |
| Where | Dart `Light.toJson()` → EncodableMap → `Light::Light` → `LightSystem` |
| When | Scene deserialization before Shape render |
| Who | Dart scene package and native filament_view Light roles |
| How | One Devtool source edit, official patch, one Mini build, one QMP A/B |

## PDCA

### Plan

1. Recheck the exact current source/API and the fixed Devtool workspace.
2. Change only `Light.toJson().color` to the already-supported native string
   representation.
3. Generate/register/commit the official patch and hand off one bundle.
4. Run the normal Dart fixture once, capture QMP-only evidence, and compare
   the fixed central region with FLR-0134.
5. Keep or reject the Light hypothesis and split the next independent ticket.

### Do

- Reconnected the existing source with persistent Devtool `modify --no-extract`.
- Edited only `Light.toJson().color` and committed the Devtool source change
  as `8ed3a4598039a617a176e2b6e1f7d5996e0c758a`.
- Generated the official patch
  `0056-filament_scene-align-dart-light-color-wire-format-devtool.patch`;
  its SHA-256 is
  `440ad7faa2ca8ba12c7c71b7738754178b33725913b62a5669f3c51e9ae7fba4`.
- Registered the untouched patch in the canonical Example Demo recipe.
- Mac fixed-container `do_patch` passed: 104 attempted tasks, all succeeded;
  the only warning was forced-task taint.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| API mapping | Dart and native color types are recorded | numeric RGBA vs native string | PASS |
| Source edit | only Light color serialization changes | one line in `light.dart` | PASS |
| Official patch | generated by Devtool and unchanged in layer | SHA matches generated artifact | PASS |
| Mini build | progressive gates pass | `do_patch`, `do_compile`, full image all passed | PASS |
| Runtime | Light correction is correlated with target markers and QMP pixels | target/present remained active; fixed 3D region stayed black | H1 REJECTED |
| Teardown | zero residual target processes and QMP socket | QMP quit accepted; host counts zero; socket absent | PASS |

### Act

- Light-only correction is retained as a valid API fix, but H1 is rejected: it
  did not restore normal Dart 3D pixels. The next independent boundary is the
  ViewTarget opaque/translucent composition contract; it is opened as FLR-0136.

## Visual evidence

- Mini evidence root: `$EVIDENCE_ROOT/flr0135-light-color/qemu`.
- QMP screenshot: `qmp-normal.ppm`, 1280x800, SHA-256
  `5108934c9fa230eafcc1b2030cd6f5a59ed44c24dba6edef750ac67e95d23244`.
  Fixed region `[300,250,620,400]`: 0 changed, 0 edge, 0 chromatic pixels,
  luma `[0,0]`; the visible content is the 2D HUD/controls only.
- QMP video evidence: 12 raw QMP frames at 1 fps, stored under the same
  Mini run directory; Mac-converted MP4 SHA-256 is
  `f45cc1effab120e126d15b45cbdae55059aa3d683ef1b95ab8fbce9ab80eb0e5`.
- Runtime counts: `application=1 shape_ready=1 camera_applied=1
  begin_true=32 render_return=31 end_frame=31 target_draw2=5 vk_present=3
  errors=0`.
- QMP teardown: negotiated quit accepted; `qemu=0 runqemu=0
  flutter-auto=0 socket=absent`.

## PDCA checker

- Status: PASS (Light API correction validated; normal-Dart 3D remains a
  product failure and is split to FLR-0136)
- Checked by: Mac Devtool + Mac `do_patch` + Mini authoritative BitBake +
  one-QEMU QMP loop
- Findings: the exact sender/receiver type mismatch was corrected, but the
  same draw/present path and uniformly black fixed region remained. Light is
  not the sole cause; ViewTarget composition and scene/material ownership stay
  UNKNOWN.
