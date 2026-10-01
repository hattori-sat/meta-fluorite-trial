# FLR-0398 — verify production Sequoia and Flutter HUD composition

- Status: Inbox
- Priority: High
- Created: 2026-10-01
- Owner: Mini QEMU / guest Flutter / Wayland composition / QMP evidence roles
- Predecessor: [FLR-0396](FLR-0396-match-working-lit-material-on-sequoia.md)
- Historical controls: [FLR-0049](FLR-0049-production-model-render-boundary.md), [FLR-0286](FLR-0286-reproduce-known-good-combined-sequoia-hud.md)
- Reference image: [user-provided historical composition frame](../evidence/FLR-0398-user-provided-composition-reference.jpg)

## Objective

After FLR-0396 independently proves colored production-Sequoia pixels in a
native-only visual-isolation frame, prove that the same exact candidate image
can display recognizable Sequoia 3D and the real Flutter HUD in one live QMP
frame. This is a composition gate, not a material-parity or original-PBR gate.

## Facts and evidence boundary

- FLR-0286 proves that a self-created lit Filament fixture and the Flutter HUD
  can appear in one QMP frame. It does not prove production Sequoia composition.
- FLR-0049 Iteration 23 proves production Sequoia geometry and red lamps in a
  QMP frame where the native surface was above the Flutter parent. The HUD was
  masked, so that run does not prove composition.
- The user-provided 1280x800 frame is retained at
  `work/evidence/FLR-0398-user-provided-composition-reference.jpg`, SHA-256
  `df30ba433b979f631c552328c0db29ef95a8a6dfefe795e3d5976ddd4b4cd3d3`. It
  visibly shows the Flutter HUD/Scenes control and red vehicle-like pixels in
  one frame; its QEMU run, image identity, and launch profile are unavailable.
  Treat it as a historical visual reference, not the acceptance artifact.
- The supplied frame shows `Shapes: On` and `Colliders: Off`. The large white
  wireframe-like lines are likely the Example Demo's Shape visualization, not
  collider outlines. Their exact implementation/source is UNKNOWN. Do not
  count those lines as Sequoia pixels or accept a frame where they obscure
  whether the car itself is visible.

## Hypotheses

1. **Composition succeeds:** the existing above-parent native-surface path and
   transparent-buffer contract allow one QMP frame to contain recognizable
   Sequoia geometry and the CPU/GPU/FPS HUD.
2. **Native output exists but is occluded:** FLR-0396's native-only pass
   remains positive, while the HUD-visible layout hides the Sequoia pixels.
3. **The apparent historical positive depended on debug geometry or a distinct
   image/profile:** the new exact-image run does not reproduce recognizable
   Sequoia plus HUD, or only Shape visualization is visible.

## 4W1H and problem point

| Dimension | Scope |
| --- | --- |
| What | Same-frame recognizable production Sequoia pixels and Flutter CPU/GPU/FPS HUD |
| Where | Exact image accepted by FLR-0396; Example Demo; Filament native surface and Flutter/Wayland composition |
| When | One controlled QMP run after the predecessor gate passes |
| Who | Mini image/runtime, guest Flutter, compositor, and QMP evidence roles |
| How | Reuse the exact Sequoia material, camera, light, model selector, image, and registered default-above-parent surface order; verify the transparent composition state and turn off Shape visualization using its observable UI control |

**Problem point:** historical proof exists for the two paths separately and a
user-supplied same-frame visual candidate exists, but no attributable,
repeatable current-image Sequoia+HUD QMP run is established.

## Scope and exclusions

- Do not start until FLR-0396 has a valid colored-Sequoia native-only result and
  its exact image hashes/profile are recorded.
- Reuse that exact image and diagnostic Sequoia material. Keep model, camera,
  light, render scale, Flutter app identity, and existing native-above-parent
  stacking fixed. Verify the existing transparent-buffer composition state;
  do not use the historical below-parent mode, which hid native 3D under HUD.
- Verify and disable Shape visualization and Colliders through an existing,
  observable control before judging vehicle pixels. Do not invent flags or
  infer effective state from an intended command.
- Do not edit source, patch, recipe, texture, camera, or lighting here. If
  evidence points to a source defect, create a separate ticket after this
  composition gate is classified.
- This diagnostic-blue Sequoia composition does not prove restoration of the
  original PBR material/texture appearance or the final production-light path.

## Success criteria

1. One QMP-only 1280x800 full-frame still and short video are captured while
   the same Flutter process identity is live before and after capture.
2. The full frame visibly contains recognizable production Sequoia geometry
   and the real Flutter HUD/CPU/GPU/FPS/Scenes pixels at the same time; a
   fixture, isolated tail-light fragment, Shape wireframe, log marker, or
   separate-run image pair does not pass.
3. Fixed Sequoia, HUD, and Shape-overlay ROIs, full-frame hashes, image/run
   identity, present/fault counters, and a complete visual inspection are
   recorded. Compare the result with both FLR-0396's native-only evidence and
   this ticket's user-provided historical reference without treating either as
   current-run proof.
4. Exact app/QEMU teardown passes with no residual QEMU, runqemu, Flutter,
   QMP-socket, or forwarded-port process/state.

## Visual evidence

- Historical user reference: [1280x800 composition photo](../evidence/FLR-0398-user-provided-composition-reference.jpg), SHA-256 `df30ba433b979f631c552328c0db29ef95a8a6dfefe795e3d5976ddd4b4cd3d3`; run identity UNKNOWN.
- Current FLR-0398 QMP still/video, exact image and run identity, pixel ROIs, hashes, and teardown: pending until FLR-0396 passes.
- White-line classification: likely Shape visualization because the UI says `Shapes: On`, with `Colliders: Off`; exact source and whether any lines belong to Sequoia remain UNKNOWN until the overlay is disabled and compared.
