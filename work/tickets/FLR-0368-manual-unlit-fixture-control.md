# FLR-0368 — isolate the lit-fixture failure with a manual UNLIT control

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / direct guest SSH / manual Flutter launch / QMP evidence roles
- Created: 2026-09-30
- Predecessor: [FLR-0367 lit-fixture replay](FLR-0367-replay-manual-known-good-fixture-on-current-image.md)
- Historical positive control: [FLR-0251 HUD + native cube](FLR-0251-restore-known-good-2d-3d-display.md)
- Current image: rootfs SHA-256 `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`
- Run ID: `flr0368-0001` (one fresh attempt)
- Branch: `feature-flr-0368-unlit-fixture-control` (local continuation of the unmerged runtime feature lineage; no push)
- Working log: [FLR-0368 working log](../logs/2026-09-30-flr0368.md)

## Objective

Using the exact current rootfs and FLR-0367's direct manual Flutter command,
remove only `FLUORITE_NATIVE_FIXTURE_LIGHT`. Determine whether the same
self-made geometry appears as UNLIT in a QMP frame together with the Flutter
HUD. This separates an LIT/material/light-specific failure from a shared
geometry-to-visible-target failure. Do not edit launch scripts, source, recipe,
or image in this experiment.

## Facts and hypotheses

### Facts

- FLR-0367 manually launched the current Example Demo and reached fixture
  geometry/material/light/camera setup, 1,040 draw/render/present returns, and a
  visible HUD; its native ROI remained black.
- FLR-0286 previously rendered the LIT fixture and HUD together, but on an older
  rootfs. FLR-0251 also proves simultaneous HUD and self-made native geometry.
- This run's exact current-image result is UNKNOWN until QMP capture.

### Hypotheses

1. **UNLIT pixels return:** geometry and visible-target paths work; the LIT
   material or explicit light branch is the narrower failing boundary.
2. **UNLIT remains black:** fixture creation metadata and present success do
   not produce visible native pixels; investigate the shared geometry,
   rasterization, or target handoff boundary.
3. **Only HUD changes or the app faults before the bounded frame gate:**
   capture the first failed marker and classify the result without inferring a
   3D render from QEMU boot or process liveness.

## Scope and success criteria

- One fresh QEMU run on the pinned current image, using the existing Mini
  receiver/build/TMPDIR and 6144 MiB profile.
- Connect to the guest over strict SSH and manually launch exactly one
  `agl-driver` `/usr/bin/flutter-auto` process from the same Example Demo
  bundle as FLR-0367.
- Keep all FLR-0367 rendering/runtime inputs fixed except remove
  `FLUORITE_NATIVE_FIXTURE_LIGHT=1`; retain the pure fixture, minimal geometry,
  local camera, and force-render setting. Do not introduce an app launcher.
- After the geometry/camera markers, observe at most 8 successful present
  completions or a 45-second deadline, then capture a full 1280x800 QMP still
  and a short bounded QMP sequence. Do not wait for minutes after the result is
  stable.
- Report HUD ROI `(1120,0,160,80)` and native ROI `(440,220,400,360)` separately;
  visually inspect the whole screenshot and record image/log hashes. A positive
  UNLIT result requires visible, identifiable geometry in the native ROI and
  the HUD in the same QMP frame; report changed, edge, and chromatic pixels
  separately so visible grayscale geometry is not misclassified as black.
- Stop only the recorded app and QEMU run, then independently verify exact
  process/socket/port cleanup.

## Impact

- **Build-time / packaging:** none; reuse the current image.
- **Runtime:** one bounded manual app run with the fixture light opt-in unset.
- **Integration risk:** low; no persistent source, recipe, image, or launcher
  changes. A fixture result does not by itself prove production Sequoia.

## Plan / Do / Check / Act

### Plan

- Reuse the exact pinned rootfs, QEMU profile, guest SSH route, bundle, and
  manual launch contract established in FLR-0367.
- Change only the fixture-light opt-in among runtime behavior variables.
- Capture once after setup and a small bounded set of completed presents; stop
  early on the first decisive QMP result.

### Do

- Pending one fresh QEMU run, after verifying canonical repository, free run
  slot, image identity, and one-active-ticket state.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Current image / guest preflight | Exact pinned image, bundle, Wayland, no stale app | Pending | PENDING |
| Manual UNLIT fixture launch | One app; `shading=unlit`, geometry and local camera markers | Pending | PENDING |
| Bounded draw/present | Up to 8 successful returns or exact first divergence by 45 seconds | Pending | PENDING |
| HUD + native QMP pixels | Separate fixed HUD/native ROI metrics and full-frame visual review | Pending | PENDING |
| Evidence | Full QMP still, short sequence, selected markers, hashes | Pending | PENDING |
| Teardown | Exact app/QEMU/socket/ports absent | Pending | PENDING |

### Act

- If UNLIT geometry is visible with HUD, open a separate LIT/light follow-up
  ticket using this as its same-image positive control.
- If UNLIT is black while setup/draw/present succeed, open a target/raster
  boundary ticket; do not modify the launcher or lighting code.
- If the guest/app/present gate fails first, open a new task for that exact
  boundary and retain the failure evidence.

## Evidence

- FLR-0367 current-image LIT screenshot/video and measurements.
- FLR-0251 historical same-frame HUD + native cube measurements.
- Current run evidence: `$EVIDENCE_ROOT/flr0368-0001/qemu` (pending).

## UNKNOWN

- Whether the current image can show this fixture without its explicit SUN/LIT
  branch.
- Whether a visible UNLIT fixture would identify the root cause of production
  Sequoia's black native ROI; that remains a separate verification boundary.
