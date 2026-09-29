# FLR-0130 — align the deserialized scene-camera handoff with ViewTarget

- Status: Waiting
- Priority: High
- Owner: Mac source and Mini runtime/QMP evidence roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0129](FLR-0129-compare-dart-opaque-translucent-surface.md), [FLR-0126](FLR-0126-validate-dart-example-demo-after-viewtarget-fix.md)
- Working log: `work/logs/2026-09-13-flr0130.md`
- Plan: `docs/superpowers/plans/2026-09-13-flr0130-restore-deserialized-camera-handoff.md`

## Work unit

Restore the API handoff from the Dart `scene.camera` payload to the native
Filament ViewTarget camera. This ticket changes one native message-routing
boundary only, then verifies whether the self-made Dart cube becomes visible
with the normal lit material. It does not change material, blend mode,
lighting, scene contents, compositor stacking, or production Sequoia behavior.

## Problem

The Dart recipe puts the fixture camera into `scene.camera`. The native
deserializer constructs a `Camera` and sends it with
`ECSMessageType::SetCameraFromDeserializedLoad`. The initial diagnosis used a
different API generation and incorrectly called the receiver missing. In the
actual Mini source (`SRCREV_plugins=451aa46e2c7b14fbb306383eebaad45d0457caa`),
the receiver already exists. The real source contradiction was that
`CameraManager` first creates a default Filament camera, while
`vSetCameraFromSerializedData()` skipped every ViewTarget that already had a
primary camera. The existing
`ViewTarget::vSetupCameraManagerWithDeserializedCamera()` method is the intended
replacement path, so this ticket removes that skip. The runtime now proves the
camera message is received and the handoff method is called, but the fixed 3D
region remains black.

## Success criteria

- Confirm the current API generation, existing handler, default-primary
  creation, and intended replacement ownership from the current Devtool source.
- Change only the native default-primary guard; use
  `std::unique_ptr<Camera>` ownership exactly once and keep the ViewTarget
  selection explicit.
- Generate the patch through the fixed Mac Devtool workflow, register the
  untouched generated patch in `meta-fluorite-trial`, and commit the layer.
- Bundle the commit to the fixed Mini receiver and pass progressive BitBake
  gates in the existing build/TMPDIR.
- Run one normal lit Dart Example Demo in one QEMU, record the camera-handoff
  marker, bounded Shape/submit/present markers, coredump state, and QMP-only
  early/late/video evidence.
- Accept success only if the fixed region contains nonuniform geometry-bearing
  pixels; a clear-color or HUD-only change is not sufficient.
- End via negotiated QMP `quit` and prove zero residual QEMU targets/sockets.

## Facts

- FLR-0125 is the positive native control: a self-made native cube reached
  visible QMP pixels through the same Filament/Wayland path.
- FLR-0126 and FLR-0129 both show the normal Dart path alive with a visible 2D
  HUD, `FLR0026_SHAPE_READY`, Vulkan submit/present activity, and a black fixed
  3D region.
- FLR-0129 additionally confirmed `FLUORITE_NATIVE_FORCE_OPAQUE` at runtime,
  but forcing the ViewTarget opaque did not change the 3D region.
- Static inspection of the actual Mini source found the sender in
  `SceneTextDeserializer::vRunPostSetupLoad()` and an existing
  `vRegisterMessageHandler(SetCameraFromDeserializedLoad)` in
  `ViewTargetSystem`.
- `ViewTarget::setupView()` attaches the common Filament Scene and creates a
  `CameraManager`; `CameraManager::setDefaultFilamentCamera()` immediately
  installs a default Filament camera on the View.
- Before this ticket, `vSetCameraFromSerializedData()` skipped replacement when
  a primary camera already existed. The existing ViewTarget API then updated
  the Filament camera and replaced the plugin primary camera.
- The normal Dart run reached `FLR0026_SHAPE_READY ... renderable=true`, camera
  `RECEIVED/APPLIED`, Vulkan submit return `0`, and present, while the QMP 3D
  region `[300,250,620,400]` remained uniform black in both early and late
  captures. The full frame contained only HUD/controls as geometry indicators.

## Inferences

- The missing-handler hypothesis is falsified for the actual API generation.
- The default-primary guard was a real API handoff defect and the minimal
  correction is valid, but it is not sufficient to produce visible Dart 3D
  pixels.
- The next boundary must distinguish “Renderable exists but no Filament draw
  is emitted” from “draw is emitted but the ViewTarget/Wayland output is not
  visible”; this is a separate ticket and must not be mixed into this one.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Result |
| --- | --- | --- |
| H1: deserialized camera message is silently dropped | actual Mini source has no receiver | FALSIFIED — existing receiver ran |
| H2: replacing the default primary camera makes the lit Dart fixture visible | handoff marker plus nonuniform QMP geometry | FALSIFIED — handoff ran but the fixed region stayed black |
| H3: Shape/Material/Camera reaches setup but no geometry draw is emitted | target trace has no Shape draw or shows invalid draw inputs | OPEN — FLR-0131 |
| H4: valid geometry is drawn but ViewTarget/Wayland composition hides it | target trace has Shape draw and QMP remains black | OPEN — FLR-0131 |

## 4W1H (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | Dart `scene.camera` to native ViewTarget camera | source path and runtime marker |
| Where | `SceneTextDeserializer` → ECS message → `ViewTargetSystem` → `ViewTarget` | current source and official patch |
| When | post-deserialization before steady-state frame | monotonic log order |
| Who | Dart scene serializer, ECS router, ViewTarget system, CameraManager | one runtime process |
| How | one missing-handler fix; lit material and blend mode held constant | QMP fixed region |

## PDCA

### Plan

1. Verify the current API generation, sender, existing receiver, default
   primary camera, and pointer ownership.
2. Remove only the default-primary skip through current-source Mac Devtool and
   generate the official patch.
3. Register the patch in the canonical layer, bundle it to Mini, and pass
   `do_patch`, `do_compile`, and full-image gates.
4. Run one normal lit Dart QEMU test with QMP-only evidence and clean teardown.

### Do

- Mac Devtool source commit `7ff7887c5c6b3e58d412e32cfd960f6772e786a8`
  generated the official patch. Canonical commit `5385417` preserves the patch
  byte-for-byte and registers it as `0239`.
- Mini bundle handoff from canonical commit `5385417` passed with bundle SHA
  `bab9dcadcedf74cd160c541f907cb2c7bf3f94243f0838e4cd92a4e7f24fd418`.
- Mini `do_patch`, `do_compile`, and full `agl-ivi-image-flutter` passed.
- One QMP-only run proved `RECEIVED`, `APPLIED`, Shape `renderable=true`, submit
  return `0`, and present activity, but early/late fixed-region geometry was
  absent. Eight QMP video frames were captured. Negotiated QMP quit and zero
  residuals passed.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Current-source contract | sender, dispatcher, receiver ownership mapped | sender and dead receiver path found; handler missing | PASS for diagnosis |
| Official Devtool patch | current source, untouched generated patch | canonical `0239`, byte identity PASS | PASS |
| Mini patch/compile/image | fixed build/TMPDIR succeeds | `do_patch`, `do_compile`, full image PASS | PASS |
| Normal lit Dart QMP | nonuniform geometry in `[300,250,620,400]` | uniform black, early and late | FAIL |
| Teardown | negotiated quit, zero residuals | QMP quit and residual check PASS | PASS |

### Act

- Retain the API fix as a proven camera-handoff correction, but leave this
  ticket `Waiting` because its visual success criterion failed.
- Continue with FLR-0131, which uses existing Filament target tracing to locate
  the first missing boundary without changing material, light, camera, or
  compositor variables.

## Visual evidence

- QMP artifacts: `$EVIDENCE_ROOT/flr0113-authoritative/flr0130-deserialized-camera/qemu/`
  (run ID `flr0130-deserialized-camera`). The fixed region analysis is uniform
  black with `region_sha256=17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25`.

## PDCA checker

- Status: PASS for build/handoff/teardown evidence; FAIL for visual acceptance
- Checked by: FLR-0131 handoff
- Findings: camera handoff is proven at the native marker boundary, but no
  visible Dart 3D pixels were produced. The ticket is Waiting, not Done.
