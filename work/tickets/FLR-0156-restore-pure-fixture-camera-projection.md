# FLR-0156 — restore pure-fixture camera projection

- Status: Waiting
- Blocked by: FLR-0158 patch-stack baseline reconciliation
- Priority: High
- Owner: Fluorite ViewTarget camera + native fixture lifecycle
- Created: 2026-09-14
- Updated: 2026-09-15
- Depends on: [FLR-0155](FLR-0155-trace-native-vertex-upload-and-clip-contract.md)
- Process prerequisite: [FLR-0157](FLR-0157-determinize-devtool-runtime-loop.md)
- Working log: `work/logs/2026-09-14-flr0156.md`

## Work unit

Repair the pure native fixture's camera initialization so it preserves the
explicit local look-at while applying the camera's normal projection and other
configuration first. Validate the repair through the existing Mac Devtool →
canonical layer → Git bundle → Mini BitBake → one-QEMU QMP loop.

## Problem

FLR-0155 proved that the fixture reaches valid geometry, exact vertex/index
uploads, Vulkan binding, indexed draw, present, and Wayland commit, but the
3D QMP candidate is uniformly black. The pure-fixture camera branch calls
`setCameraLookat()` and returns before `CameraManager::updateCamera()` applies
the deserialized projection. Filament's unset projection is identity; with
the fixture eye at `(0,0,5)` and cube vertices at z `[-1,1]`, all view-space z
values are `[-6,-4]` and are clipped. This is a source-owned camera contract
defect, not an unresolved generic QEMU or buffer-upload issue.

## Success criteria

- [x] Edit the persistent Mac Devtool-managed Fluorite source and generate the
  implementation patch with official Yocto Devtool.
- [x] Register the generated patch unchanged under
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/` and commit it
  locally with the ticket evidence updates.
- [ ] Pass Mac `do_patch`, Mini `do_patch`, `do_compile`, and the fixed full
  `agl-ivi-image-flutter` build using the existing container, build directory,
  and TMPDIR.
- [ ] Run one QEMU with the fixed profile and QMP-only evidence. The fixed 3D
  region must become non-black and chromatic while the 2D HUD remains present.
- [ ] Record the camera-configuration marker, screenshot/video hashes, pixel
  statistics, and clean QMP teardown with zero residual targets.
- [ ] If this repair does not change the predicted QMP boundary, keep the
  patch as diagnostic history and split the next source owner into a new
  ticket; do not silently broaden this work unit.

## Facts

- FLR-0155 runtime evidence records `bytes=96 checksum=3361464197` for the
  fixture vertex upload and `bytes=72 checksum=101010765` for its index upload.
- FLR-0155 records non-null Vulkan handles matching the draw-time vertex and
  index handles, indexed draw count 36, queue-present result 0, and Wayland
  child-surface commits.
- FLR-0155 QMP-only evidence is uniformly black in `[300,250,620,400]` while
  the 2D HUD is non-black.
- The native fixture source's local-camera branch returns immediately after
  `setCameraLookat()`. The normal path below it calls `updateCamera()`, which
  applies exposure, projection, lens projection, shift, scaling, and camera
  manipulator configuration.
- The Dart camera contract provides a default perspective projection of 60
  degrees vertical FOV. Filament's default `mat4` constructor is identity.

## Inferences

- The current first-zero boundary is before fragment output: the fixture's
  camera projection is identity rather than the perspective contract supplied
  by the camera payload.
- Applying normal camera configuration before overriding only the local
  look-at is the smallest behavior-preserving repair.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: the pure fixture skips required projection initialization | after `updateCamera()` runs, the same cube produces nonzero chromatic pixels in the fixed QMP region | the camera marker and configuration are positive but QMP remains uniformly black |
| H2: projection repair is insufficient and the loss is in attachment/readback | source/runtime camera contract becomes positive but QMP and a paired target observation remain zero | QMP 3D pixels become nonzero after the camera-only repair |
| H3: the chosen repair changes normal camera behavior outside the fixture | non-fixture launch or source/API comparison changes unexpectedly | only the environment-gated pure fixture uses the local look-at override |

Current UNKNOWN: whether the rebuilt image will produce visible pixels after
the camera configuration repair. It must be proven by QMP, not inferred from
the log marker alone.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | Apply camera configuration, then use the fixture-local look-at |
| Where | Fluorite `ViewTarget::vSetupCameraManagerWithDeserializedCamera` |
| When | During camera setup before the first native fixture draw |
| Who | Fluorite ViewTarget camera role, Mac Devtool role, Mini build role, QEMU/QMP runtime role |
| How | One minimal Devtool patch and one fixed-image QMP run |

## PDCA

### Plan

1. Preserve the exact FLR-0155 geometry, material, Vulkan, Wayland, QEMU, and
   evidence profile.
2. Compare two repairs: call the existing `updateCamera()` and override only
   look-at, or directly set a hardcoded projection. Prefer the existing API
   path because it preserves payload-defined projection/lens behavior.
3. Edit only the persistent Devtool source, generate the official patch,
   register it unchanged, run the fixed build gates, and validate QMP pixels.

### Do

- Ticket created after FLR-0155 classified the first missing boundary.
- The source edit and official Devtool-generated patch are prepared, but Mini
  build/runtime validation is paused until FLR-0157 makes recipe resolution,
  finish output selection, and bounded log extraction fail-closed and
  reproducible.
- FLR-0157 is now committed as `b6f7e3c`; the fixed handoff helper and bounded
  runtime evidence loop are available for this ticket.
- The bundle handoff reached receiver tip `8149bcd1d35545c7978e8b77cf605386f1966775`,
  but Mini `do_patch` stopped before the camera patch at the older `0002`
  patch. The current source has moved the camera file, so patch-stack baseline
  reconciliation is split to FLR-0158 rather than changing this camera patch.
- The fixed bundle handoff passed with bundle SHA-256
  `c54ce3f4e31ff425a0d6bad9ace5e0d6056c8258c961bbffd7a727dd20b1e920` and
  receiver tip `8149bcd1d35545c7978e8b77cf605386f1966775`. The existing Mini
  build and TMPDIR were selected by receiver-layer match; no duplicate state
  path was created.

### Check

- Static source/API expectation: pending implementation.
- Build and runtime pixel evidence: pending.

### Act

- Pending the first repaired-image QMP result.

## Evidence

- [FLR-0155 boundary evidence](FLR-0155-trace-native-vertex-upload-and-clip-contract.md)
- Raw FLR-0155 runtime evidence: `$RECEIVER/evidence/flr0155/qemu-diagnostic-20260914/`
