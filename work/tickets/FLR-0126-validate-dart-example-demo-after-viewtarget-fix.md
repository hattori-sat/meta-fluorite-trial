# FLR-0126 — validate the Dart Example Demo after the ViewTarget fix

- Status: Waiting
- Priority: High
- Owner: Mini runtime and QMP evidence roles, with Mac Devtool source role if a new patch is justified
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0125](FLR-0125-trace-viewtarget-entry-path.md)
- Working log: `work/logs/2026-09-13-flr0126.md`
- Plan: `docs/superpowers/plans/2026-09-13-flr0126-validate-dart-example-demo.md`

## Work unit

Run the normal Flutter Example Demo without the native-fixture environment
variables on the FLR-0125 image. Determine whether the same deferred
ViewTarget delivery restores the Dart-created blue-cube path, and distinguish
shared native rendering from a Dart scene/payload problem. This ticket does
not claim production Sequoia rendering or scene-transition/input success.

## Problem

FLR-0125 proved that the restored native fixture reaches ViewTarget creation,
native geometry, present, and visible QMP pixels. FLR-0121 previously showed
the Dart Example Demo path reaching shape/submit while its fixed central QMP
region remained black. The native-control result is not evidence that the Dart
entry path is correct.

## Success criteria

- Use the existing Mini artifact, fixed build/TMPDIR, receiver, QEMU harness,
  and QMP-only evidence contract; create no second build or TMPDIR.
- Launch exactly one `agl-driver` Example Demo process without
  `FLUORITE_NATIVE_PURE_FIXTURE` or `FLUORITE_NATIVE_MINIMAL_GEOMETRY`.
- Record application identity, camera/shape/present markers, coredump state,
  and any channel errors in the same run.
- Capture early and late QMP framebuffer images and analyze
  `[300,250,620,400]`; accept Dart 3D only from nonzero visual pixels.
- End through negotiated QMP `quit` and prove zero residual QEMU targets and
  QMP sockets.
- Do not edit source or generate a new patch unless this runtime evidence
  identifies a source-controlled Dart defect.

## Facts

- FLR-0125 canonical commit `f0406dae` and Mini image rootfs
  `5d4dc1763574ffd7d4005b2002eb2cb8977a9d95c96aaeacde4f60df6be55811` contain
  the ordered ViewTarget delivery fix.
- The native fixture on that image produced `111758` changed/chromatic pixels
  in the fixed region and reached native geometry/present markers.
- FLR-0121's Dart path removed camera API errors but its QMP region remained
  uniform black.
- The Dart and native fixture paths must be compared with separate environment
  identities; a native-fixture environment variable is not a Dart test.
- The normal Dart run completed without the native-fixture environment
  variables. One `agl-driver` `flutter-auto` process stayed alive and
  `coredumpctl` reported no coredumps.
- The bounded runtime output reached
  `FLR0026_SHAPE_READY guid=4 entity=5 renderable=true`,
  `flutter: Camera 8 enabled`, `FLUORITE_VK_SUBMIT_RETURN result=0`, and
  `FLUORITE_VK_PRESENT_ENTER index=0 headless=false`.
- QMP-only early and late captures both measured
  `changed_pixels=0`, `edge_pixels=0`, `chromatic_pixels=0`, and luma range
  `[0,0]` in `[300,250,620,400]`. The region SHA-256 was
  `17c129be2f336bd881ef6947d9ee957d4b699e7cadd115f919a60e57e413bc25` and
  the full-frame SHA-256 was
  `f8328a0e292f11342c6b8b741b77e15a640473de2ae6a0ddfffebea538f483f8`.
- All eight QMP video frames were stable at the same full-frame SHA-256.
- Teardown used negotiated QMP `quit`; the recorded QEMU, QMP socket, and
  associated runtime targets were zero after cleanup.

## Inferences

- If the normal Dart run becomes QMP-positive, the shared ViewTarget/native
  present path is repaired and the remaining production issue is scene-specific.
- If it remains black while the native control stays positive, the next scope
  is Dart PlatformView creation parameters, scene deserialization, camera
  payload, or Dart-side timing—not Wayland composition by default.
- A single unchanged QMP frame cannot distinguish a surface-placement issue
  from missing Dart geometry; marker order and fixed-region pixels are both
  required.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Test | Result |
| --- | --- | --- | --- |
| H1: ordered ViewTarget delivery fixes the Dart fixture too | normal Dart run reaches native 3D pixels | one no-native-fixture QEMU run | FALSIFIED: shared present markers passed but QMP remained black |
| H2: Dart payload/scene remains independent failure | native markers may run but Dart shape/camera or pixels remain absent | compare bounded markers and QMP region | LEADING: Shape/Camera/submit/present exist, but pixels are absent; exact resource boundary is UNKNOWN |
| H3: shared surface/compositor still hides only Dart output | submit/present succeeds but fixed region remains black | compare native control and Dart QMP captures | NOT EXCLUDED: native control uses a diagnostic opaque/unlit path, while Dart uses the normal translucent/lit path |

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | Dart Example Demo 3D visibility after native entry fix | QMP pixels and runtime markers |
| Where | Dart PlatformView payload, native deserializer, ViewTarget, present target | source/log boundary |
| When | first startup frame and late steady state | early/late QMP and monotonic log |
| Who | Dart app, flutter-auto, ECS/ViewTarget runtime roles | one-process status |
| How | normal bundle launch with native fixture controls removed | exact launch command |

## PDCA

### Plan

1. Reuse the FLR-0125 image and fixed Mini/QEMU evidence infrastructure.
2. Run the normal Example Demo with native fixture controls absent; collect
   only the bounded runtime markers needed for classification.
3. Capture early/late QMP images and, if positive, a short QMP frame sample.
4. Split any newly identified Dart or production boundary into a new ticket
   before editing or changing the build.

### Do

- Created after FLR-0125 proved the native fixture path and cleanly shut down.
- Reused the FLR-0125 image, fixed build/TMPDIR, Mini receiver, and QEMU
  harness.
- Launched the normal Example Demo with the native-fixture environment
  variables absent.
- Collected bounded process, coredump, Shape/Camera/submit/present markers,
  early/late QMP captures, eight QMP video frames, and negotiated teardown.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| One active ticket | FLR-0126 only during this run | FLR-0126 gate complete; follow-up split to FLR-0127 | PASS |
| Normal Dart launch | no native fixture variables | one process launched with the normal Example Demo bundle | PASS |
| Runtime health | one process, no coredump | one `flutter-auto`; no coredump | PASS |
| Dart QMP pixels | fixed region nonzero | zero changed/chromatic pixels, uniform black | FAIL |
| QMP teardown | negotiated quit, zero residuals | QMP quit accepted; residual targets and sockets zero | PASS |

### Act

- The normal Dart gate is decided as negative and this ticket is closed as
  `Waiting`; it does not claim production Sequoia rendering.
- FLR-0127 owns the next bounded source/runtime boundary. It must compare the
  Dart resource path with the positive native control before any compositor or
  lighting change is proposed.

## Evidence locations

- `$EVIDENCE_ROOT/flr0113-authoritative/flr0126-dart-example/qemu`
- Working log: `work/logs/2026-09-13-flr0126.md`

## Visual evidence

- Run ID: `flr0126-dart-example` on the FLR-0125 image; QMP-only artifacts are
  under `$EVIDENCE_ROOT/flr0113-authoritative/flr0126-dart-example/qemu`.
- `dart-qmp-early.ppm` and `dart-qmp-late.ppm` both show the 2D HUD while the
  central 3D region is uniformly black. The fixed-region analysis is recorded
  in `dart-qmp-early-analysis.json` and `dart-qmp-late-analysis.json`.
- `qmp-video.json` and `qmp-video-frame-sha256.txt` retain the eight-frame
  stability check; no frame contains nonzero 3D-region pixels.

## PDCA checker

- Status: PASS (evidence completeness; visual acceptance is FAIL)
- Checked by: runtime/QMP evidence role
- Findings: The shared entry and present boundary are proven for the Dart
  run, but the requested Dart 3D pixels are not present. Follow-up FLR-0127
  is required.
