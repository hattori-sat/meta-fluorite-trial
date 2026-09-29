# FLR-0232 — isolate input-independent parent repaint

- Status: Done
- Priority: High
- Owner: Wayland parent-surface damage/import and Flutter frame roles
- Created: 2026-09-20
- Predecessor: FLR-0231

## Objective

Identify why the Flutter parent/HUD becomes uniform white after the QMP input
sequence even when the Flutter button-up event is suppressed, while the native
3D ROI remains visible.

## Facts

- FLR-0231 emitted the button-up suppression marker, but control and
  button-up-skip `up.ppm` files were byte-identical.
- Both runs retained `24178` chromatic pixels in the native ROI and had zero
  chromatic pixels in the HUD ROI at `up`.
- The output-enter metrics skip still preserves the HUD through `move-y`.
- QMP teardown passed for both runs with no residual QEMU target or QMP socket.

## Hypotheses

| Rank | Hypothesis | Prediction | Discriminator |
| --- | --- | --- | --- |
| 1 | A pointer-motion/region-entry path causes parent-surface damage/import independent of button-up | isolated `move-y` reproduces white while isolated `move-x` does not; native ROI stays unchanged | single-event QMP A/B with repeated post-event frames |
| 2 | A parent-surface or Flutter frame path changes after a delayed input-related update | input run stays white while no-input control stays chromatic, with selected frame markers at the transition | compare no-input, move-x-only, and move-y-only runs |
| 3 | Native surface ordering/occlusion changes while the native buffer remains valid | native Wayland attach/damage/order markers change at the transition, or native ROI changes | compare only selected parent/native surface protocol markers and fixed ROIs |

## Plan / Do / Check / Act

### Plan

1. Keep the known output-enter metrics skip enabled so FLR-0229 remains
   controlled.
2. Do not add a source patch initially; first capture five QMP frames after
   `move-y`, `down`, and `up` using the same single-QEMU harness.
3. Compare the fixed HUD and native ROIs, then inspect only the bounded
   parent/native Wayland and Flutter frame markers needed to distinguish the
   hypotheses.

### Success criteria

- The first white transition is identified as persistent repaint, transient
  capture timing, or native ordering/import.
- Native 3D visibility is measured independently from HUD state.
- Evidence contains QMP PPM hashes, ROI metrics, selected logs, and clean
  teardown.
- No route, lighting, camera, geometry, or production-scene change is mixed
  into this unit.

## Evidence

- Predecessor: [FLR-0231](FLR-0231-isolate-button-release-repaint.md)
- Working log: [2026-09-20-flr0232.md](../logs/2026-09-20-flr0232.md)

## Runtime Check

- Evidence: `$EVIDENCE_ROOT/FLR-0232/qemu-parent-repaint-repeat-ready/`.
- The run used the latest image and kept
  `FLUORITE_DISABLE_OUTPUT_ENTER_METRICS=1` enabled. No source behavior patch
  was added for this unit.
- QMP collected 25 PPM frames: initial, each transition frame, and five
  post-transition frames at 0.5-second intervals.
- Initial and all `move-x` post-frames had HUD
  `chromatic_pixels=2801` and native `chromatic_pixels=24178`.
- `move-y` and all five `post-move-y-*` frames had HUD
  `chromatic_pixels=0`, `luma=[255,255]`, and native
  `chromatic_pixels=24178`. The same uniform-white result continued through
  `down`, `up`, and all their post-frames.
- `move-y.ppm` and `post-move-y-04.ppm` share SHA-256
  `83b474a377d3b8edb59a542f79cd2446961c0daef0fe44b734be22d15349f1fb`.
- The output-enter skip marker was emitted; app stop, QMP quit, and cleanup
  passed with zero residual QMP socket.

### No-input control

- Valid control evidence:
  `$EVIDENCE_ROOT/FLR-0232/qemu-no-input-ready-r2/`.
- Twenty-five frames were captured at 0.5-second intervals with no QMP input
  event. Every frame had HUD `chromatic_pixels=2801` and native
  `chromatic_pixels=24178`; the first and last PPM share SHA-256
  `830fd73a5eb8ca51798dc037add59fcb37c9e3b5c3082f4d515c487fa0ab0cf4`.
- The first no-input attempt is explicitly invalid:
  `$EVIDENCE_ROOT/FLR-0232/qemu-no-input-ready/` stopped at frame 23 because
  the original script did not wait for QMP file creation, and an outer
  `set -u` runner incorrectly printed PASS. QMP cleanup still passed. The
  script now has a bounded two-second file wait, and the valid rerun used
  `set -eu`.

## Current Conclusion

The white transition is persistent once it occurs, not a one-frame QMP timing
artifact. It does not occur during the no-input time-only control, so a
pure-time explanation is falsified. It occurs at `move-y` in the repeated
input run, before button-up, while the native 3D ROI remains unchanged. The
next discriminator is isolated pointer motion/region entry versus the parent
frame or Wayland damage/import path.

## Closeout

- No-input and single-axis controls stayed chromatic in the HUD. The combined
  `x → 4s hold → y` run alone produced the persistent white HUD.
- The selected Wayland log for the combined run contains
  `wl_pointer@65.enter(... 1189.96093750, 0.00000000)` followed by
  `wl_pointer@65.motion(... 1189.96093750, 39.99218750)`.
- The combined pixel-analysis SHA-256 is
  `80abb75b37c993b98c5b42edad304cf355b9cc156e508ffed27c7e8ec8153c0f`.
- The move-x-only and move-y-only analysis SHA-256 values are
  `43c3751c42915d616deda8ece40947dcb92269d13537a119f10bf1ff6565edab`
  and `24e6b88afd757d86c974734784b8c3200dd7bea14882684f2088a1aa1c86af09`.
- The exact owner is now narrowed to the pointer-motion/Flutter parent path;
  the next source A/B is [FLR-0233](FLR-0233-isolate-pointer-motion-repaint.md).
