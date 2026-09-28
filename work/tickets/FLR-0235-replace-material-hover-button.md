# FLR-0235 — replace Material hover button with static clickable surface

- Status: Done
- Priority: High
- Owner: Flutter Scenes control and parent-surface composition roles
- Created: 2026-09-20
- Predecessor: FLR-0234

## Objective

Keep pointer motion and Scenes activation available while replacing the
stateful Material `FilledButton` hover path with a static clickable surface.
Prove that the combined QMP motion sequence keeps both the 2D HUD and native
3D visible.

## Facts

- FLR-0233 proved pointer-motion delivery is upstream of the white transition.
- FLR-0234 proved that setting `FilledButton.overlayColor` transparent does
  not fix the transition; it caused a uniform-white full frame in the tested
  image.
- The initial frame before motion still contains HUD `2801` and native
  `24178` chromatic pixels.
- The native Vulkan present path returns `0` and continues committing native
  buffers during the white transition.
- FLR-0235 Mini `do_patch`, `do_compile`, and full image gates passed.
- QMP initial, move-x, move-y, and five post-motion frames all retained HUD
  `2845` chromatic pixels and native ROI `24178` chromatic pixels.
- QMP visual inspection confirmed simultaneous 2D HUD, Scenes control, and
  colored native cube. The pointer-motion sequence did not reproduce the
  FLR-0234 uniform-white transition.
- QMP quit, application stop, residual process, and residual socket checks
  passed.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Replace `FilledButton` with a static decorated clickable surface | motion remains delivered and no Material hover repaint occurs | visual/semantics parity must be checked |
| 2 | Remove the Scenes control entirely | frame remains stable | loses activation and is not product-compatible |
| 3 | Change embedder pointer phase or suppress motion | frame remains stable | breaks pointer semantics; diagnostic only |

Candidate 1 is selected because it preserves the control's visual role and
tap boundary without changing native 3D, camera, light, or route logic.

## Plan / Do / Check / Act

### Plan

1. Register the current effective app source at the FLR-0234 source commit
   through official Devtool.
2. Replace only the `FilledButton` implementation with a static decorated
   clickable surface and commit the source change.
3. Generate the patch through official Devtool, bundle it to Mini, run
   `do_patch`, `do_compile`, full image, and one QMP combined-motion run.

### Success criteria

- Pointer motion is still delivered.
- Initial, `move-y`, and all post-motion QMP frames have a non-white HUD ROI.
- Native ROI remains at least `24178` chromatic pixels.
- No route, camera, light, material, or native geometry changes are included.
- QMP quit, process cleanup, and residual socket checks pass.

## Evidence

- Predecessor: [FLR-0234](FLR-0234-repair-pointer-motion-parent-repaint.md)
- Working log: [2026-09-20-flr0235.md](../logs/2026-09-20-flr0235.md)

## Conclusion

FLR-0235 is complete. The static clickable-surface patch keeps the 2D HUD and
native 3D cube visible together through the tested pointer-motion sequence.
This does not yet prove route activation or the lighting/camera behavior of a
different production scene; those require a new ticket.
