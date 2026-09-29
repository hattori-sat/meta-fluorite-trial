# FLR-0124 — restore a reproducible native 3D control through Devtool

- Status: Waiting
- Priority: High
- Owner: Mac persistent Devtool source + canonical layer + Mini authoritative build roles
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0123](FLR-0123-compare-native-and-dart-fixture-entry-paths.md), [FLR-0114](FLR-0114-reconcile-flutter-auto-patch-stack-baseline.md)
- Working log: `work/logs/2026-09-13-flr0124.md`
- Plan: `docs/superpowers/plans/2026-09-13-flr0124-restore-native-control.md`

## Work unit

Restore a minimal, self-made native 3D control in the current effective
`flutter-auto` source using the official Yocto Devtool workflow. The control
must be present in the current Mini image before it is used to compare the
Dart Example Demo cube. This ticket owns source provenance reconciliation,
Devtool-generated patch creation, canonical layer registration, Mini build,
and one QMP-only native-control validation.

## Problem

FLR-0042 proved a C++ native cube through a historical source/patch stack.
FLR-0121/0122 now test a Dart-created cube, but the current Mini effective
source no longer contains the historical native-control implementation. The
old environment variables therefore cannot reproduce the control and must not
be used as a fake runtime comparison.

## Success measure

- The Mac persistent Devtool source is based on the exact current Mini
  effective native source, with the prior patch context imported through the
  documented baseline procedure.
- A minimal native-control change is edited in the Devtool source, committed
  there, and exported unchanged by `devtool finish --mode patch`.
- The unchanged patch is registered under `meta-fluorite-trial`, committed,
  bundled, and built on the fixed Mini build/TMPDIR.
- One official QEMU run proves the control setup marker, native frame/commit/
  present sequence, and nonzero 3D pixels in the fixed central QMP region.
- No claim is made about the Dart fixture or production Sequoia scene until
  this control passes.

## Facts

- FLR-0123 source preflight found no native minimal-geometry/pure-fixture
  implementation in the current Mini effective `flutter-auto` source.
- The current Dart fixture reaches shape readiness and queue submit but has a
  uniform-black central QMP region.
- FLR-0042's positive cube was produced by a different C++ native entry path.
- The persistent Mac Devtool native source and Mini effective source are
  currently different snapshots; source identity must be fixed before editing.
- Fixed build, TMPDIR, one persistent Podman container, canonical layer, Mini
  receiver, QEMU profile, and QMP capture contract are reused.
- The exact Mini effective `view_target.cc`, `view_target.h`, and
  `scene_text_deserializer.cc` were imported into the Devtool source baseline;
  source baseline commit is `69dcb931ce0747ef66d6f4e971f728d11db3b3fa`.
- The native-control source was committed in Devtool source commits
  `5b1579439c2628661dece2ad7cc635a1f6f3cfb9`,
  `107e792eac92b09304d30545f26ea391c3589a5b`, and
  `116e9bb1c82e3dfa6299e80ed495608cde611957`.
- Official Devtool `update-recipe --mode patch` generated three patches. Their
  canonical filenames and SHA-256 values are:
  `0233-diag-add-native-control-fields-devtool.patch`
  (`2d06dad02e7cc2df398ec612353890a32fbf1ff9e614cd25f0f0e4861f8c1d00`),
  `0234-diag-add-native-minimal-geometry-control-devtool.patch`
  (`cbc58ba2eec5af2694019fd5583f6f7b1f2d875daa899feb528e5c23b0a26651`), and
  `0235-diag-isolate-native-fixture-setup-devtool.patch`
  (`b8c946cf876006799ba9a973cb121e811ab75a71a8634db4bf89006c61d62613`).
- Mac `flutter-auto:do_patch` completed successfully: 104 tasks attempted,
  100 reused, and the target patch task succeeded.
- Mini `flutter-auto:do_patch`, `do_compile`, and the full
  `agl-ivi-image-flutter` build all completed successfully. The resulting
  native-control rootfs SHA-256 is
  `447f0cdadde58f774210b2b9cb5a2fd2bfe17a87399c25e9180f971ac4d6c495`.
- The only QEMU run used the fixed harness and one `agl-driver` flutter-auto
  process. `FLUORITE_NATIVE_PURE_FIXTURE` was observed, but no
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY_*` marker, `ViewTarget` entry marker, or
  `InitializeFilamentInternals` marker was observed.
- QMP early and late captures were both 1280x800 and uniform black in the
  fixed region `[300,250,620,400]`: `changed_pixels=0`,
  `chromatic_pixels=0`, and `luma_range=[0,0]`. Both captures have PPM SHA-256
  `f8328a0e292f11342c6b8b741b77e15a640473de2ae6a0ddfffebea538f483f8`.
- The source and deployed binary contain the native-control marker strings,
  so the observed absence is a runtime-entry failure, not evidence that the
  patch was omitted. No coredump was found, and negotiated QMP quit reported
  zero residual targets and sockets.

## Inferences

- A native control cannot be validated by launch variables alone when its
  handler is absent from the image.
- Rebuilding the control first is the smallest way to distinguish a shared
  image/native display regression from a Dart scene integration failure.
- A source-provenance mismatch creates integration risk greater than the
  native control itself, so provenance is the first gate.

## Hypotheses / UNKNOWN

1. Restoring the native control on the current effective source will reproduce
   visible cube pixels and present markers.
2. If it does not, the shared native frame/present path has regressed and the
   Dart path remains out of scope.
3. UNKNOWN whether the historical patch applies cleanly to the current source;
   the official Devtool baseline and patch result must establish this.

## 4W1H stratification (Why excluded)

| Dimension | Observation | Evidence target |
| --- | --- | --- |
| What | Native control implementation is absent from the current image | source scan and binary strings |
| Where | Mac Devtool source, canonical layer patch, Mini effective source | hashes and Devtool finish output |
| When | Before any native/Dart pixel comparison | ticket sequence |
| Who | Devtool source role, layer integration role, Mini build/runtime roles | working log |
| How | Import exact baseline → edit via Devtool → finish patch → bundle/build/QMP | patch hash and runtime evidence |

## PDCA

### Plan

1. Confirm the fixed Podman Devtool container and current canonical branch;
   do not create another container, volume, TMPDIR, or build tree.
2. Record the current Mini native source identity and patch order, then align
   the persistent Mac Devtool local-Git baseline with that effective source.
3. Make only the native-control source edit through the persistent Devtool
   source, commit it there, and generate the patch using official Devtool.
4. Copy the generated patch unchanged into the canonical layer, register it,
   run the Mac recipe gate, commit locally, and send one complete-history
   bundle to the fixed Mini receiver.
5. Run Mini progressive/full-image gates and one official QMP-only native
   control. Stop through negotiated QMP and classify pixels before opening the
   Dart comparison ticket.

### Do

- Imported the three exact Mini effective native source files into the
  persistent Devtool source workspace and committed the baseline.
- Added the neutral native-control environment gates in Devtool source:
  `FLUORITE_NATIVE_PURE_FIXTURE` and
  `FLUORITE_NATIVE_MINIMAL_GEOMETRY`.
- Committed the source changes through the bounded source-Git wrapper and
  generated the three patches through official Devtool.
- Copied the generated patches unchanged into the canonical layer and
  registered them after the existing current-source plugin patch stack.
- No Mini build or QEMU action has started yet.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Devtool/source identity | Mac baseline equals Mini effective native source | PASS | source baseline commit and hashes | PASS |
| Devtool patch | source commit and unchanged official finish patch | PASS | generated patch hashes | PASS |
| Canonical/Mini build | layer commit, bundle, do_patch, compile, image pass | Mac do_patch PASS; Mini not run | build evidence | OPEN |
| Native control entry | setup marker and ViewTarget initialization are observed | FAIL | runtime status and entry output | FAIL |
| Native control pixels | fixed central QMP region has nonzero geometry | FAIL | QMP PPM/analysis | FAIL |
| Teardown/privacy | QMP quit, zero residuals, no private metadata | PASS | qmp-quit.txt and harness output | PASS |

### Act

- Keep the Dart fixture and production scene out of scope. Split the missing
  PlatformView/ViewTarget entry path into FLR-0125.

## Evidence locations

- `$EVIDENCE_ROOT/flr0113-authoritative/flr0124-native-control/qemu`
- Working log: `work/logs/2026-09-13-flr0124.md`

## Unknowns

- Whether the old positive cube depended on additional source changes that are
  also absent from the current layer.
- Whether the restored control and Dart fixture share the same ViewTarget and
  Wayland child surface.
- Whether the PlatformView registration callback, ECS message queue, or
  ViewTarget creation request is the first missing runtime boundary.

## PDCA checker

- Status: PASS WITH FAILURE HANDOFF
- Checked by: FLR-0124 bounded Devtool/build/QMP loop
- Findings: source identity, generated patch, build, and teardown passed; the
  native-control runtime entry and pixel criteria failed and were split into
  FLR-0125.
