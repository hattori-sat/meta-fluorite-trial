# FLR-0129 — compare the Dart fixture opaque and translucent ViewTarget paths

- Status: Waiting
- Priority: High
- Owner: Mac source and Mini runtime/QMP evidence roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0127](FLR-0127-isolate-dart-fixture-black-region.md), [FLR-0125](FLR-0125-trace-viewtarget-entry-path.md)
- Working log: `work/logs/2026-09-13-flr0129.md`
- Plan: `docs/superpowers/plans/2026-09-13-flr0129-compare-dart-opaque-translucent-surface.md`

## Work unit

Determine whether the Dart fixture's missing 3D pixels are caused by the
normal transparent/translucent ViewTarget contract. Restore the normal Dart
fixture's original lit material and change only the ViewTarget blend condition
through a current-source Mac Devtool patch. This ticket does not claim a
production Sequoia fix or scene-transition/input success.

## Problem

FLR-0126 showed the normal lit Dart fixture with a black 3D region while the
2D HUD remained visible. FLR-0127 changed only the Dart material to unlit and
produced a stable full-white frame with no cube, edges, chroma, or HUD. The
first observable change is real but its owner is UNKNOWN: material/resource
output and surface composition remain confounded.

## Success criteria

- Reuse the fixed Mac Podman Devtool state, canonical layer, Mini receiver,
  build/TMPDIR, and QMP evidence contract; create no second state, build, or
  QEMU instance.
- Generate the ViewTarget blend probe from the current effective source with
  Mac Devtool and register the untouched generated patch in
  `meta-fluorite-trial`.
- Restore the Dart fixture to `poGetLitMaterial`; the only runtime variable is
  an explicit opaque ViewTarget condition versus the normal translucent one.
- Run the resulting image once in exactly one QEMU, record the bounded
  Shape/Camera/submit/present markers and coredump state, and capture QMP-only
  early/late frames plus the fixed region `[300,250,620,400]`.
- Accept visible 3D only when the QMP region contains geometry indicators and
  nonzero pixels attributable to the fixture, not from a uniform clear color.
- End through negotiated QMP `quit` and prove zero residual QEMU targets and
  sockets.

## Facts

- FLR-0125 is the positive native control: its self-made native geometry
  reached visible QMP pixels through an opaque diagnostic View and unlit
  material.
- FLR-0126 is the normal lit Dart negative control: Shape/Camera/submit/present
  markers passed, the HUD was visible, and the central 3D region was uniform
  black.
- FLR-0127 is the unlit Dart A/B: the full frame became stable uniform white,
  but no geometry or HUD was visible. It is not a 3D success.
- The current ViewTarget source creates a transparent swapchain and sets the
  normal View blend mode to `TRANSLUCENT`; the native diagnostic path sets
  `OPAQUE` only when it replaces the scene.
- A historical opaque probe exists in the repository, but this ticket must
  regenerate the patch against the current Devtool source rather than copy a
  historical patch by hand.

## Inferences

- A lit Dart run with only ViewTarget forced opaque is the cleanest next test:
  it removes the material variable introduced by FLR-0127.
- If opaque produces a geometry-bearing QMP region, the transparent/translucent
  composition path is implicated. If it remains uniform or black, surface
  blend mode alone is not sufficient and the material/resource or camera path
  remains open.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Result |
| --- | --- | --- |
| H1: translucent ViewTarget hides valid lit Dart output | lit + forced opaque yields visible fixture geometry | OPEN |
| H2: the unlit package changes the whole-surface state independently of blend mode | lit + forced opaque remains non-geometric, or differs only in clear color | OPEN |
| H3: camera/transform remains the first Dart-specific defect | neither blend condition yields geometry and bounded transform evidence is invalid | OPEN |

## 4W1H (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | lit Dart fixture under opaque/translucent ViewTarget | QMP region and markers |
| Where | ViewTarget blend/swapchain boundary | current source patch and runtime markers |
| When | first and steady-state frames | early/late QMP |
| Who | Dart app, flutter-auto, ViewTarget runtime roles | one-process status |
| How | same image/build/QEMU profile; one blend variable | exact launch command |

## PDCA

### Plan

1. Register the current effective ViewTarget source in the fixed Mac Devtool
   state and create a clean source baseline.
2. Add only an environment-controlled opaque ViewTarget probe and commit the
   source through Devtool; generate the official patch with `finish`.
3. Restore the Dart fixture's lit-material source in the same image and append
   the untouched ViewTarget patch to the canonical recipe.
4. Bundle the canonical layer commit to Mini, run progressive BitBake gates,
   and execute one QMP-only runtime comparison.

### Do

- The current-source ViewTarget workspace was imported into the fixed Mac
  Devtool state. The source edit changed only the existing normal
  `TRANSLUCENT` assignment to an environment-controlled branch and was
  committed in the source workspace before official `finish`.
- Official Devtool `finish` generated the untouched patch
  `0237-diag-add-opaque-ViewTarget-probe-devtool.patch` with SHA-256
  `0575d4185875d4743d1c1378164e7d5a6463a0420594a04d1c81b9ea91d3822f`.
  The canonical layer commit is `7da9bb6`.
- The normal Dart fixture was restored to `poGetLitMaterial` by removing the
  FLR-0127 recipe registration; the FLR-0127 patch file remains in history.
- The fixed bundle handoff advanced the Mini receiver to
  `7da9bb6c0bb21c4fff975b77bc8e6315c3517df8`.
- Mini `flutter-auto` `do_patch`, `do_compile`, and
  `agl-ivi-image-flutter` all passed in the fixed build/TMPDIR. The resulting
  rootfs is recorded in the artifact identity under the fixed evidence root.
- One QEMU was started after preflight. The launch used the lit Dart fixture
  and `FLUORITE_NATIVE_FORCE_OPAQUE=1`; the one-process guard passed. The
  runtime log contained `FLR0026_SHAPE_READY` and
  `FLUORITE_NATIVE_FORCE_OPAQUE enabled=true`; no coredump was found.
- The QMP-only pre-launch region `[300,250,620,400]` was uniform black. The
  early and late region remained uniform black, and all eight QMP video frames
  had the same region SHA-256. The full frame did contain the 2D HUD and
  controls, so the result is not a total application-surface failure.
- A first video command used an unsupported `--region` option and failed after
  the QMP screenshots; the corrected direct QMP capture command then succeeded
  and created eight frames. No second QEMU was started.
- Negotiated QMP `quit` was accepted and cleanup reported zero residual QEMU
  targets and zero QMP sockets.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Fixed Devtool/container | one reusable state and rootful Podman bind | PASS | PASS |
| Current-source official patch | generated by Devtool, not hand-written | patch `0237`, SHA recorded | PASS |
| Mini patch/compile/image | same fixed build/TMPDIR succeeds | all three gates passed | PASS |
| Lit Dart opaque QMP | geometry-bearing visible pixels or falsifying evidence | 2D HUD present; 3D region uniform black | FAIL for 3D acceptance |
| Teardown | negotiated quit, zero residuals | QMP quit accepted; targets/sockets `0/0` | PASS |

### Act

- H1 is not supported: forcing the normal lit Dart ViewTarget opaque did not
  change the black 3D region. Keep this ticket as a waiting diagnostic
  boundary and split the next camera/transform or material-instance
  instrumentation test into a new ticket; do not stack unrelated changes here.

## Visual evidence

- Raw QMP artifacts are under
  `$EVIDENCE_ROOT/flr0129-opaque-surface/qemu/`:
  `qmp-before.ppm`, `qmp-early.ppm`, `qmp-late.ppm`, `video-frames/`, and the
  corresponding analysis/log files.
- The 3D-region analysis for `qmp-early.ppm` and `qmp-late.ppm` was:
  `changed_pixels=0`, `edge_pixels=0`, `chromatic_pixels=0`,
  `luma_range=[0,0]`, `geometry_indicator=absent-or-undetectable`.
  The full-frame analysis was `geometry-indicators-present` because it
  included the 2D HUD and controls.
- The late QMP screenshot visually shows the HUD and controls while the
  central 3D surface remains black. The screenshot was only copied to a Mac
  temporary path for inspection; the receiver evidence is authoritative.

## PDCA checker

- Status: PASS_WITH_OPEN_3D_GATE
- Checked by: Mac source / Mini build / QMP runtime evidence roles
- Findings: The opaque/translucent boundary is isolated as a falsified
  sufficient cause. The actual Dart 3D pixel owner is UNKNOWN; the next test
  must instrument camera/transform, render-list/material instance, or target
  attachment independently.
