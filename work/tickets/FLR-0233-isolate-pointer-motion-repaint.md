# FLR-0233 — isolate pointer-motion repaint

- Status: Done
- Priority: High
- Owner: Wayland pointer motion and Flutter parent-surface roles
- Created: 2026-09-20
- Predecessor: FLR-0232

## Objective

Determine whether `Display::pointer_handle_motion` delivery is the trigger for
the persistent uniform-white Flutter HUD while native 3D pixels remain visible.

## Facts

- FLR-0232 found no white transition in no-input, move-x-only, or move-y-only
  controls.
- The combined `x → 4s hold → y` run produced `wl_pointer.enter` followed by
  `wl_pointer.motion`; the HUD became white at `move-y` and stayed white.
- The native ROI stayed at `24178` chromatic pixels through the transition.
- Static source inspection shows `pointer_handle_motion` maps the event to
  `kHover` or `kMove` and calls `Engine::CoalesceMouseEvent`.

## Hypotheses

| Rank | Hypothesis | Prediction | Discriminator |
| --- | --- | --- | --- |
| 1 | Flutter pointer-motion delivery triggers the parent repaint/import | gating only motion preserves HUD after the combined QMP sequence | official Devtool motion-only A/B |
| 2 | Wayland parent damage/import is independent of Flutter motion delivery | motion gate does not change the white transition | same QMP sequence and fixed ROI hashes |
| 3 | Native ordering changes on motion while native content remains valid | native ROI or selected attach/order markers change | native ROI and bounded Wayland markers |

## Plan / Do / Check / Act

### Plan

1. Use the existing matching Devtool baseline and create one environment-gated
   motion-only source change.
2. Generate the patch through official Devtool update-recipe/finish flow;
   never hand-edit the generated patch.
3. Run Mini `do_patch`, `do_compile`, image build, then the same combined QMP
   sequence with output-enter metrics skip held constant.

### Success criteria

- The motion-gate marker proves only pointer-motion delivery was changed.
- Native 3D remains at `24178` chromatic pixels.
- HUD state after `move-y` distinguishes the two hypotheses.
- QMP evidence, selected pointer/Wayland logs, and clean teardown are retained.

## Scope boundary

Do not change route selection, Dart scene widgets, Filament light/material/
camera code, native geometry, or compositor configuration in this ticket.

## Evidence

- Predecessor: [FLR-0232](FLR-0232-isolate-input-independent-parent-repaint.md)
- Working log: [2026-09-20-flr0233.md](../logs/2026-09-20-flr0233.md)

## Runtime Check

- Image rootfs SHA-256:
  `56b1080d6040ee9c47ecad58fc36c56b173ad21bb337c806257cbd8a3b1606b4`.
- Image kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- Control evidence: `$EVIDENCE_ROOT/FLR-0233/qemu-motion-control-ready/`.
- Motion-skip evidence: `$EVIDENCE_ROOT/FLR-0233/qemu-motion-skip-ready/`.
- Both runs used the same combined `x → 4s hold → y` QMP sequence and the
  same output-enter metrics skip. Only
  `FLUORITE_DISABLE_POINTER_MOTION_EVENT=1` differed.
- Control: native ROI stayed `chromatic_pixels=24178`, while HUD became
  `chromatic_pixels=0`, `luma=[255,255]` at `move-y` and stayed white.
- Motion-skip: native ROI stayed `24178` and HUD stayed `chromatic_pixels=2801`
  through all frames. The marker was
  `FLUORITE_DISABLE_POINTER_MOTION_EVENT enabled=true
  operation=skip_pointer_motion`.
- Control and motion-skip QMP teardown and residual checks both passed.

## Conclusion

The pointer-motion delivery path is the confirmed trigger boundary. The
motion-only gate is diagnostic and must not be treated as the product fix,
because it removes pointer motion. The next unit is
[FLR-0234](FLR-0234-repair-pointer-motion-parent-repaint.md).
