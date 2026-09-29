# FLR-0225 — diagnose post-input white surface and route composition

- Status: Done
- Priority: High
- Owner: Flutter route, native surface composition, and runtime evidence role
- Created: 2026-09-20
- Predecessor: FLR-0224

## Objective

Identify why the accepted QMP click, after the native surface input region is
cleared, changes the final QMP frame to a uniform-white HUD area without a
Scenes route marker. Determine whether the first divergence is Flutter route
rendering, a surface-stack replacement, or an application transition that is
not instrumented.

## Success criteria

- Reuse the exact FLR-0224 image and input-region patch baseline.
- Capture one bounded QMP run with initial and post-click frames, hashes, and
  fixed ROI summaries.
- Correlate the post-click white frame with bounded Flutter/native/Wayland
  evidence and identify the first missing or changed event.
- Produce a new ticket for the next independently verified source boundary;
  no source patch is justified by this diagnostic unit alone.
- Teardown is clean and all evidence is recorded in this ticket's working log.

## Scope boundary

- Do not treat the diagnostic SHM cube as production-scene 3D success.
- Do not modify camera/material/scene data until the post-input surface owner
  is identified.
- Do not hand-edit generated patches or reuse FLR-0224 as an evergreen ticket.

## Plan / Do / Check / Act

### Plan

1. Read FLR-0224 evidence and verify the exact rootfs/layer/patch identity.
2. Compare at least two boundaries: Flutter route rendering versus
   compositor/surface stacking.
3. Use bounded logs and QMP ROI evidence to locate the first divergence.
4. Apply only the smallest source or runtime diagnostic change implicated by
   evidence, using the fixed Mac Devtool workspace and Mini bundle/build loop.

### Do

- Reused the exact FLR-0224 image and `FLUORITE_NATIVE_EMPTY_INPUT_REGION=1`.
- Captured separate initial, pointer-move, button-down, and button-up QMP
  frames. The white transition first appeared on the pointer move into the
  Scenes control area, before button down/up.
- Ran a neutral pointer-move control. Its three frames retained the initial
  frame hash.
- Correlated bounded runtime evidence with the QMP frames and inspected the
  effective application source.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| FLR-0224 baseline identity | exact image and layer revision | inherited rootfs/kernel/qemuboot and patch identity | PASS |
| First white-frame divergence | event boundary identified | Flutter-parent repaint after target-area pointer motion | PASS |
| QMP visual evidence | frame hashes and ROI summaries | native cube ROI unchanged; HUD ROI becomes uniform white | PASS |
| Native reattach discriminator | no native surface reattach after motion | no native attach/commit observed | PASS |
| Neutral control | non-target move leaves frame unchanged | all frames match initial hash | PASS |
| Teardown | no residual QEMU/app/QMP socket | QMP and cleanup passed for both runs | PASS |

### Act

Close this unit after the first divergence is evidenced. FLR-0226 owns the
minimal Flutter-parent transparent-composition/hover correction. Camera,
material, and production-scene changes remain out of scope until the parent
surface stays transparent through pointer entry.

## Facts

- FLR-0224 proved `FLUORITE_NATIVE_EMPTY_INPUT_REGION enabled=true`.
- After the QMP click, pointer enter changed to the Flutter parent surface.
- The post-click HUD ROI became uniform white and no Scenes route marker was
  observed.
- FLR-0224 QMP evidence is retained at `$EVIDENCE_ROOT/FLR-0224/qemu-input-region/`.
- The stepwise frame hashes were initial/x-only
  `830fd73a5eb8ca51798dc037add59fcb37c9e3b5c3082f4d515c487fa0ab0cf4` and
  y-move/down/up `83b474a377d3b8edb59a542f79cd2446961c0daef0fe44b734be22d15349f1fb`.
- The native cube ROI stayed at 24178 chromatic pixels while the HUD ROI
  became uniform white. The neutral-move control retained the initial hash.
- Focused logs show Flutter-parent repaint/commit activity after pointer
  motion, but no native surface reattach. The effective source places route
  activation on the Scenes button `onPressed` callback, not pointer hover.

## Hypotheses

1. Flutter accepted the click but replaced the HUD with a white route surface
   before the route marker or scene content was rendered.
2. The click caused a surface-stack or native/Flutter composition change, so
   the white frame is an occluding surface rather than a Flutter route result.

## UNKNOWN

- Whether the white frame is caused by the Flutter parent clear/alpha contract
  or by the `MenuAnchor` hover repaint layer.
- Whether the Scenes action callback executes after the parent remains
  transparent.

## Evidence

- Predecessor ticket: [FLR-0224](FLR-0224-clear-native-input-coverage-for-flutter-route.md)
- Next ticket: [FLR-0226](FLR-0226-fix-flutter-parent-hover-composition.md)
- Evidence root: `$EVIDENCE_ROOT/FLR-0225/`
