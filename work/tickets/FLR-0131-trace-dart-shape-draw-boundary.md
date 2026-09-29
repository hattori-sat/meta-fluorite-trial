# FLR-0131 — trace the Dart Shape draw boundary

- Status: Waiting
- Priority: High
- Owner: Mini runtime/QMP evidence role
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0130](FLR-0130-restore-deserialized-camera-handoff.md), [FLR-0125](FLR-0125-trace-viewtarget-entry-path.md)
- Working log: `work/logs/2026-09-13-flr0131.md`

## Work unit

Use the already-built FLR-0130 image and the existing compiled Vulkan target
trace for one normal lit Dart Example Demo run. Determine whether the Dart
Shape reaches a Filament `draw()` call and whether that draw targets the
ViewTarget swapchain. This ticket does not change source, material, camera,
lighting, blend mode, compositor order, or QEMU settings.

## Problem

FLR-0130 proves the Dart camera message is received and the replacement path is
called. The Shape is reported as `renderable=true`, and Vulkan submit/present
return successfully, but QMP shows a uniform-black fixed 3D region. `Shape
READY` is not sufficient evidence that a renderable was actually visited by the
Filament renderer.

## Success criteria

- Reuse the fixed Mini build/TMPDIR, one QEMU, one `flutter-auto`, and one
  negotiated QMP teardown.
- Capture bounded runtime markers and existing Vulkan target/pipeline trace.
- Classify the first missing boundary as one of:
  - no Shape Draw emitted;
  - Draw emitted with invalid or unexpected target/input;
  - valid Draw emitted to the ViewTarget but absent from QMP pixels.
- Preserve QMP-only early/late screenshots, bounded video frames, logs,
  artifact identity, hashes, and zero-residual evidence.
- Do not create a source patch until the classification selects the next
  single boundary.

## Facts

- FLR-0125 is the positive native control: a self-made native cube produced
  visible pixels through the same Filament/Wayland path.
- FLR-0130's current-source API correction produces
  `FLUORITE_DESERIALIZED_CAMERA_RECEIVED` and
  `FLUORITE_DESERIALIZED_CAMERA_APPLIED`.
- FLR-0130 also produces `FLR0026_SHAPE_READY ... renderable=true`, Vulkan
  submit return `0`, and present activity, while the fixed region remains
  uniform black.
- Existing compiled diagnostics include target render-pass, target draw,
  readback-source, and effective pipeline-input markers, selected by runtime
  environment variables.
- The QEMU preflight, start, guest-ready check, QMP captures, and QMP video
  completed, but the runtime launch procedure was not a valid single-process
  experiment. The first generated command contained `test "" = 0` because the
  host shell expanded the guest process-count substitution while writing the
  command file. The corrected command still used `test ...; su ...` rather than
  stopping on a failed test, so it could start `flutter-auto` after the guard
  failed.
- The saved guest log contains `agl_shell extension already in use by other
  shell client.` followed by repeated `FLR0026_FRAME_SKIP_STATUS status=1` and
  `FLR0026_FRAME_FENCE_WAIT_LINKED linked=false`. No target draw marker from
  this run is therefore usable as an application rendering result.
- The fixed QMP region `[300,250,620,400]` was uniform black with region hash
  `17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25`.
  QMP teardown was nevertheless clean: negotiated quit accepted and zero
  residual targets/QMP sockets.

## Inferences

- The QEMU framebuffer and teardown path are operational, but this run cannot
  distinguish Shape/Material/Camera setup from draw submission because the
  Wayland shell-client precondition was violated.
- The first generated command and the semicolon-based guard are a procedure
  defect that can create the same double-start collision this experiment was
  intended to detect. The next run must preflight, inspect, and execute one
  conditional launch command only.
- Static API inspection also found a separate source-level candidate for the
  next ticket: Dart serializes custom mode `INERTIA_AND_GESTURES`; native marks
  only `eCustomCameraMode_`, then passes uninitialized `mode_` to
  `CameraManipulator::Builder::build()` from `updateCameraManipulator()`.
  This is not proven as the visual root cause yet.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Result |
| --- | --- | --- |
| H1: `Shape READY` is reached but no geometry Draw is emitted | no target Draw marker for the Dart renderable | UNKNOWN; run invalid due shell-client collision |
| H2: geometry Draw is emitted to an unexpected/invalid target or with invalid pipeline inputs | Draw/RenderPass target or pipeline trace differs from the expected ViewTarget path | UNKNOWN; run invalid due shell-client collision |
| H3: valid geometry Draw reaches the ViewTarget swapchain but QMP remains black | target Draw and swapchain RenderPass are present, fixed region is still uniform black | UNKNOWN; run invalid due shell-client collision |
| H4: the fixed QMP region is not the ViewTarget surface | Draw/readback viewport/extent is present elsewhere in the frame | UNKNOWN; run invalid due shell-client collision |
| H5: the launch guard allowed two app starts and caused the shell collision | a clean conditional guard removes `agl_shell` collision and frame skips | Supported as a procedure finding; clean rerun pending |

## 4W1H (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | Dart Shape to Filament Draw to QMP pixels | target/pipeline trace and QMP |
| Where | shared Filament Scene → ViewTarget View → swapchain | target image/extent/format markers |
| When | after Shape setup and camera handoff, during steady frames | ordered serial timestamps |
| Who | ShapeSystem, MaterialSystem, CameraManager, Filament renderer | one `flutter-auto` |
| How | runtime trace only; no source or input change | one controlled QEMU |

## PDCA

### Plan

1. Reuse the FLR-0130 artifact identity and fixed QEMU runbook.
2. Enable only existing target/pipeline diagnostics and launch the normal lit
   Dart fixture once.
3. Capture QMP early/late/video and bounded logs.
4. Quit via negotiated QMP, verify zero residuals, classify the boundary, and
   open a separate source-change ticket only if evidence requires it.

### Do

- Ran one QEMU instance using the FLR-0130 image with the existing target and
  pipeline diagnostics. QMP early/late captures and an 8-frame video were
  saved under `$EVIDENCE_ROOT/flr0131-dart-shape-draw/qemu`.
- The first launch command was malformed by host-side command substitution. A
  corrected command was inspected and executed, but its semicolon-separated
  guard did not prevent a second launch after a failed process-count test.
- The guest showed the `agl_shell` collision and repeated frame skips; no
  source, image, or layer mutation was made.
- QEMU was terminated through the recorded QMP socket; cleanup reported zero
  residual targets and zero residual QMP sockets.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| One-process runtime | one `flutter-auto` | launch collision invalidated the experiment | UNKNOWN |
| Target Draw trace | Dart geometry Draw is classified | no usable target trace | UNKNOWN |
| QMP visual gate | fixed region is geometry-bearing or explained | uniform black; not attributable to a valid run | UNKNOWN |
| Teardown | negotiated quit, zero residuals | negotiated quit accepted; zero residuals | PASS |

### Act

- Mark this run Waiting as an invalid diagnostic execution, not as evidence
  that the Dart renderer has no Draw path.
- Create FLR-0132 for the independently testable camera API contract and use a
  single conditional launch command in its clean runtime gate.
- Do not add a workaround patch before the camera payload/manipulator contract
  and the clean Shape-to-Draw boundary are both rechecked.

## Visual evidence

- Run: `$EVIDENCE_ROOT/flr0131-dart-shape-draw/qemu`
- QMP late screenshot: `qmp-late.ppm`, SHA-256
  `f8328a0e292f11342c6b8b741b77e15a640473de2ae6a0ddfffebea538f483f8`.
- Fixed region `[300,250,620,400]`: uniform black, 0 changed/edge/chromatic
  pixels, luma `[0,0]`.
- The full-frame classification includes HUD-like pixels, but the late capture
  was compared to another capture of the same frame; it is not a valid motion
  delta. The visual result is retained as evidence of this invalid run only.

## PDCA checker

- Status: UNKNOWN (runtime gate invalidated by launch collision)
- Checked by: runtime evidence role
- Findings: QMP teardown passed; the application draw boundary was not
  classifiable because the single-process/Wayland shell precondition failed.
