# FLR-0237 — fix Planetarium route composition and visible scene ownership

- Status: Done
- Priority: High
- Owner: Flutter surface-composition and native scene-activation roles
- Created: 2026-09-20
- Predecessor: FLR-0236

## Objective

After the verified Scenes-to-Planetarium callback, preserve the 2D HUD and
produce a post-transition native frame whose identity is distinguishable from
the diagnostic fixture cube. This ticket isolates composition and scene
ownership; it does not change the Devtool handoff protocol.

## Facts

- FLR-0236 proves the tap reaches `_setScene(3)` and emits the bounded
  Planetarium activation marker.
- The FLR-0236 initial frame had HUD chromatic pixels `2845` and native ROI
  chromatic pixels `24178`.
- After activation, the HUD region became uniform white (`0` chromatic
  pixels), while the native ROI remained `24178`.
- `StatefulSceneView` is inserted above the native `_filamentViewWidget` in a
  Flutter `Stack` when `_sceneView != null`.
- The Planetarium payload uses Planetarium shapes and cameras, while the
  current scene-shape path also appends the diagnostic fixture cube.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Activated route surface paints an opaque default background | Making only the route surface transparent preserves the HUD and exposes the next native result | may reveal that scene ownership is still unchanged |
| 2 | Flutter state changes but native scene creation remains on the fixture | Transparent composition leaves the same native ROI after activation | requires a separate native scene-creation change |
| 3 | Planetarium geometry is active but outside the target camera | Transparent composition changes neither ROI identity nor coverage | needs bounded camera/shape telemetry before geometry edits |

Candidate 1 is the smallest falsifiable change because the white HUD is the
first observed post-activation boundary and FLR-0235 already established the
pre-activation surface baseline.

## Success criteria

- Mac Devtool source history is based on the FLR-0236 source commit.
- The generated patch is produced by the official split-component procedure
  and registered in `meta-fluorite-trial` without hand-editing its body.
- Mini patch, compile, and image gates pass for the exact bundle tip.
- QMP initial frame retains HUD `2845` and native ROI `24178`.
- QMP tap emits the Planetarium marker, keeps the HUD non-white, and records
  whether the native ROI changed from the fixture baseline.
- QMP quit and residual process/socket cleanup pass.

## Evidence

- Predecessor: [FLR-0236](FLR-0236-activate-planetarium-scene.md)
- Working log: [2026-09-20-flr0237.md](../logs/2026-09-20-flr0237.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0237/`

### Completed evidence

- Source commit `589b97abea736c2728c53dcafacbd638e5de57c5` was converted by
  the official Devtool split-component flow. The generated patch and
  canonical patch are byte-identical with SHA-256
  `d4cf08c9e116a5b4e6446ddda159063baa6bae1a42dbcc468b7e27053c174d3b`.
- Canonical layer commit: `81cdc102cc416a370e82d838d65230b47eb4f190`.
  Bundle handoff SHA-256:
  `25ef0d6089c5c6088ec2840e3e0ad161692d5e8a5b8fc97c1b1e6c9b880b507a`.
- Mini `do_patch` passed; compile passed with `1674/1674` successful tasks;
  image passed with `11758/11758` successful tasks.
- Runtime rootfs SHA-256 was
  `0aa6ccbb1f1a5c995b3beaa39afa3b2f0a094a51d978467a89cb112c3f06d51e`.
  The qemuboot SHA-256 was
  `dbc148b92a0efd3b5281b10df92cda4d6aa6361151ad9255406c9d574530c15b` and
  the kernel SHA-256 was
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QMP initial/move frames showed HUD `2845` and native ROI `24178`. The `up`
  frame showed HUD `0`, luma `[255,255]`, while native ROI remained `24178`.
  Representative PPM hashes are
  `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01` and
  `83b474a377d3b8edb59a542f79cd2446961c0daef0fe44b734be22d15349f1fb`.
- The callback marker, pointer button events, Flutter surface attach, and raw
  guest log are retained under `$EVIDENCE_ROOT/FLR-0237/`. QMP quit, app stop,
  and residual process/socket checks passed.

### Verdict

The full-surface Planetarium gesture layer is not the sole cause of the white
post-tap frame: the A/B replaced its build output with `SizedBox.shrink()`
while keeping the route state lifecycle, and the same HUD-white/native-fixture
result remained. This ticket closes that composition discriminator. FLR-0238
owns the split between route-state mounting and a plain `setState` rebuild.

## UNKNOWN

- The exact widget or route layer that paints the post-tap white surface.
- Whether scene id `3` triggers native scene replacement or only Flutter view
  replacement.
- Whether the Planetarium geometry is inside the target camera after the
  composition boundary is repaired.
