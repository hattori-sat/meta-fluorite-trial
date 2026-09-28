# FLR-0136 — isolate the ViewTarget opacity contract

- Status: Done
- Priority: High
- Owner: Mini runtime role with Mac evidence role
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0135](FLR-0135-align-dart-light-color-wire-format.md), [FLR-0134](FLR-0134-instrument-viewtarget-frame-boundary.md)
- Working log: `work/logs/2026-09-13-flr0136.md`

## Work unit

Run the normal Dart Example Demo from the FLR-0135 image once with the
existing native ViewTarget forced to opaque. This is a runtime-only A/B:
there is no source or layer patch in this ticket. The result will distinguish
transparent ViewTarget composition from a scene/material/target-content fault.

## Problem

FLR-0135 corrected the confirmed Dart/native Light color type mismatch, but
the normal Dart run remained black in the fixed 3D region. The same run still
had a ready Shape, applied Camera, repeated ViewTarget render/end, a 36-index
target draw, and Vulkan present.

The effective native source explicitly selects
`View::BlendMode::OPAQUE` when `FLUORITE_NATIVE_FORCE_OPAQUE` is set and
`View::BlendMode::TRANSLUCENT` otherwise. The previous native positive
control used this opaque setting together with a native geometry fixture.
Whether opaque alone restores the normal Dart-created Cube is UNKNOWN.

## Success criteria

- [x] Record the exact effective opacity hook and distinguish it from the
  native-geometry fixture switch.
- [x] Reuse the fixed FLR-0135 image, build, TMPDIR, and one QEMU run; make no
  source/layer change.
- [x] Run the normal Dart Example Demo with only
  `FLUORITE_NATIVE_FORCE_OPAQUE=1` added to the existing diagnostics.
- [x] Capture QMP-only screenshot/video and fixed-region statistics; retain
  bounded application/shape/camera/frame/target/present/error evidence.
- [x] Classify the result as opacity-related or unchanged scene/material/
  target-content failure.
- [x] Negotiate QMP quit and verify zero residual QEMU, `runqemu`,
  `flutter-auto`, and QMP socket artifacts.

## Facts

- FLR-0135 normal Dart QMP screenshot was 1280x800 with fixed region
  `[300,250,620,400]`, 0 changed/edge/chromatic pixels, and luma
  `[0,0]`; the visible content was the 2D HUD and controls.
- FLR-0135 normal runtime counts were
  `application=1 shape_ready=1 camera_applied=1 begin_true=32
  render_return=31 end_frame=31 target_draw2=5 vk_present=3 errors=0`.
- The effective native source reads `FLUORITE_NATIVE_FORCE_OPAQUE` in
  `ViewTarget::setupView()` and selects OPAQUE versus TRANSLUCENT.
- `FLUORITE_NATIVE_MINIMAL_GEOMETRY=1` is a separate native fixture switch
  and must not be used in this A/B.
- The opaque-only run emitted `FLUORITE_NATIVE_FORCE_OPAQUE enabled=true` and
  did not emit the native-geometry fixture marker.
- Its QMP screenshot was 1280x800, SHA-256
  `879b0c4cbad5d4424b308ac3ab035e91034fa1fbe4c5a645f77e721b531cd258`.
  The fixed 3D region had 0 changed, edge, or chromatic pixels and luma
  `[0,0]`; the region hash matched the FLR-0135 normal run.
- Its runtime counts were `application=1 shape_ready=1 camera_applied=1
  begin_true=32 render_return=31 end_frame=31 target_draw2=4 vk_present=3
  errors=0`.

## Inferences

- Opaque-only is the smallest runtime experiment for the remaining
  composition hypothesis because it leaves Dart scene payload and target
  setup unchanged.
- A non-black fixed region with opaque-only would implicate the default
  translucent ViewTarget contract; a black region would reject opacity as the
  sole cause.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: translucent ViewTarget suppresses the normal Dart 3D result | opaque-only normal run produces a stable Cube region | opaque-only run remains uniformly black |
| H2: opacity is not the root cause | opaque-only run has the same black fixed region and draw/present boundary | opaque-only run produces visible geometry |
| H3: remaining fault is lit material, scene content, or target composition | opaque-only does not change pixels; next ticket selects one of those boundaries | opacity-only change restores 3D |

UNKNOWN: the native runtime does not expose a separate per-frame blend-mode
marker beyond the startup opacity marker; source evidence plus the controlled
QMP A/B is sufficient for this ticket.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | Normal Dart ViewTarget opacity selection |
| Where | `ViewTarget::setupView()` → Filament View blend mode → QMP target |
| When | View setup before the normal Dart frame loop |
| Who | Mini runtime role; Mac evidence role |
| How | One environment-only A/B, one QMP screenshot/video, one teardown |

## PDCA

### Plan

1. Confirm the effective opacity hook and the existing FLR-0135 artifact.
2. Start one QEMU from the same fixed image with only the opaque variable added.
3. Run the normal Dart application, capture QMP visual and bounded markers.
4. Reject or support opacity, close this ticket, and open the next boundary.

### Do

- Reused the FLR-0135 image, fixed build/TMPDIR, and one QMP-first QEMU run;
  no source or layer patch was made.
- Added only `FLUORITE_NATIVE_FORCE_OPAQUE=1` to the existing normal Dart
  launch. The native geometry fixture switch was absent.
- Captured QMP screenshot/video and bounded runtime markers. The opaque
  startup marker was observed.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Opacity API mapping | exact OPAQUE/TRANSLUCENT hook recorded | `FLUORITE_NATIVE_FORCE_OPAQUE` selects OPAQUE; unset selects TRANSLUCENT | PASS |
| Runtime A/B | only opaque variable differs from FLR-0135 | normal Dart only; native geometry fixture disabled | PASS |
| Visual evidence | fixed region and QMP screenshot/video recorded | fixed region remained uniformly black; QMP screenshot/video captured | H2 SUPPORTED |
| Boundary evidence | application/shape/camera/frame/target/present/errors recorded | application/shape/camera/frame/target/present reached; errors=0 | PASS |
| Teardown | zero residual target processes and QMP socket | QMP quit accepted; qemu/runqemu/flutter-auto=0; socket absent | PASS |

### Act

- H1 is rejected and H2 is supported: opaque-only did not change the fixed
  3D region or the normal draw/present boundary. The next ticket isolates the
  lit Material path of the self-made Dart Cube.

## Visual evidence

- Mini evidence root: `$EVIDENCE_ROOT/flr0136-viewtarget-opacity/qemu`.
- QMP screenshot: `qmp-opaque.ppm`, 1280x800, SHA-256
  `879b0c4cbad5d4424b308ac3ab035e91034fa1fbe4c5a645f77e721b531cd258`.
  Fixed region `[300,250,620,400]` had 0 changed, edge, or chromatic pixels
  and luma `[0,0]`; region hash was
  `17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25`.
- QMP video contains 12 raw frames at 1 fps under the same Mini run; the Mac
  converted MP4 SHA-256 is
  `d43f91400b8d05a1c8ea918e6b94b138a79ff03762273689d54596ec9099e8ab`.
- Opaque startup marker was present, native geometry fixture marker was
  absent, and runtime counts included `begin_true=32 render_return=31
  end_frame=31 target_draw2=4 vk_present=3 errors=0`.
- QMP quit was negotiated and accepted; residual check was
  `qemu=0 runqemu=0 flutter-auto=0 socket=absent`.

## PDCA checker

- Status: PASS (opacity-only hypothesis classified; normal-Dart 3D remains a
  product failure and is split to FLR-0137)
- Checked by: Mini QMP-first runtime harness + Mac visual inspection
- Findings: the opaque startup marker was present, but fixed-region pixels
  and the normal draw/present boundary were unchanged. Translucent ViewTarget
  is not the sole cause; the lit Material/scene-content boundary is next.
