# FLR-0231 — isolate button-release repaint

- Status: Done
- Priority: High
- Owner: Flutter pointer button and parent-surface composition roles
- Created: 2026-09-20
- Predecessor: FLR-0229

## Objective

Identify the repaint path that still changes the Flutter parent/HUD surface to
uniform white on QMP `up` after the output-enter `SetPixelRatio` resend has
been skipped.

## Facts

- FLR-0229 proved that skipping only output-enter `SetPixelRatio` preserves the
  HUD through `move-y` while the diagnostic 3D ROI remains unchanged.
- The same metrics-skip run still changed the HUD to uniform white on the
  button-release `up` event.
- The initial metrics-skip frame contains both the 2D HUD and diagnostic 3D
  (`chromatic_pixels=2801` in the HUD ROI and `24178` in the native ROI).

## Hypotheses

| Rank | Hypothesis | Prediction | Discriminator |
| --- | --- | --- | --- |
| 1 | Flutter button-up event causes a separate full parent repaint/import | skipping only button-up delivery preserves HUD after `down → up` | one input-path A/B with output-enter metrics skip held constant |
| 2 | Wayland parent damage/import occurs independently of Flutter button-up | button-up gating does not change the white transition | same QMP sequence and ROI hashes |
| 3 | Native surface receives or changes ordering on release | native attach/order or native ROI changes at `up` | selected protocol log and native ROI; currently low probability |

## Plan / Do / Check / Act

### Plan

1. Keep `FLUORITE_DISABLE_OUTPUT_ENTER_METRICS=1` enabled so the already
   classified output-enter path does not confound this unit.
2. Trace the existing `pointer_handle_button` → Flutter event path before
   adding a source gate.
3. Add one environment-gated A/B only if static/runtime evidence identifies a
   single button-release boundary; use the same official Devtool baseline,
   source commit, update-recipe, finish, Mini build, and QMP workflow.

### Success criteria

- The branch marker proves whether only button-up delivery was gated.
- The native diagnostic 3D ROI remains unchanged.
- The HUD either remains non-white after `up` or the hypothesis is falsified;
  ambiguous capture timing is rejected.
- QMP-only evidence and clean teardown are retained.

## Scope boundary

Do not change route selection, Dart scene widgets, Filament light/material/
camera code, native geometry, or compositor configuration in this ticket.

## Evidence

- Predecessor: [FLR-0229](FLR-0229-isolate-output-enter-pixel-ratio-repaint.md)
- Working log: [2026-09-20-flr0231.md](../logs/2026-09-20-flr0231.md)

## Runtime Check

- Latest image identity: rootfs SHA-256
  `fe213800ee5a2226364b9b980847cfbbd1b60b09e66f834fc0a7b2d6d45a4e78`;
  kernel SHA-256
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- Control evidence: `$EVIDENCE_ROOT/FLR-0231/qemu-button-up-control-ready/`.
- Button-up-skip evidence:
  `$EVIDENCE_ROOT/FLR-0231/qemu-button-up-skip-ready/`.
- Both runs used the same QMP sequence and the same output-enter metrics skip
  boundary; only `FLUORITE_DISABLE_BUTTON_UP_EVENT=1` differed.
- Control marker: `up` produced HUD `chromatic_pixels=0`, `luma=[255,255]`;
  native ROI remained `chromatic_pixels=24178`.
- Button-up-skip marker was emitted as
  `FLUORITE_DISABLE_BUTTON_UP_EVENT enabled=true operation=skip_pointer_up`,
  but its `up.ppm` SHA-256 was the same as control
  (`83b474a377d3b8edb59a542f79cd2446961c0daef0fe44b734be22d15349f1fb`),
  with the same HUD/native ROI metrics.
- Both runs ended with `qmp=PASS`, `cleanup=PASS residual_targets=0
  residual_qmp=0`, and app stop status `PASS`.

## Conclusion

The button-up delivery hypothesis is falsified. Suppressing the Flutter
button-up event does not prevent the white parent/HUD transition, and does not
change the native 3D pixels. The next independent unit is
[FLR-0232](FLR-0232-isolate-input-independent-parent-repaint.md).
