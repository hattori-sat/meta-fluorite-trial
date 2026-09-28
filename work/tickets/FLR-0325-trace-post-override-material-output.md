# FLR-0325 — trace post-override material output

- Status: Done
- Priority: High
- Owner: persistent Devtool source Git / Filament material output / Mini runtime roles
- Created: 2026-09-25
- Predecessor: [FLR-0324](FLR-0324-fix-paintcolor-string-comparison.md)
- Working log: `work/logs/2026-09-25-flr0325.md`

## Objective

Identify the first divergence after the corrected PaintColor
`setParameter("baseColorFactor", ...)` call and before visible Sequoia pixels.
Use diagnostics only: do not change Light, camera, Scene ownership, surface
composition, or production output behavior in this ticket.

## Success criteria

- Trace the post-override material-instance state and the renderable/material
  binding used for the submitted Scene draw.
- Mini `do_patch`, component compile, and full image pass through the standard
  Mac Devtool → bundle → Mini flow.
- One QMP-first runtime records the full frame, fixed native/HUD ROIs, and the
  bounded post-override log slice.
- Determine whether the parameter is readable after the setter, whether the
  same MaterialInstance is bound to the renderable, or mark the first unknown
  boundary explicitly.
- Teardown the single QEMU cleanly and create a separate fix ticket if needed.

## Facts

- FLR-0324 fixed the `const char*` pointer comparison. Runtime now reports
  `material_match=true` and emits the baseColor override marker.
- The same run still has native ROI `0/144000` chromatic while HUD ROI is
  `2845` chromatic. BeginFrame, Scene add, draw submit, and present are positive.
- The GLB contains the colored tail-light texture/material data; the supplied
  square image is static resource evidence, not a runtime frame.
- The post-override trace reports `value=(1,0,1,1)`,
  `same_instance=true`, and bound instance `PaintColor` for the production
  PaintColor primitive. This falsifies setter loss and instance mismatch at
  this boundary.
- The QMP frame contains the 2D HUD and Scenes control, but native ROI
  `(440,220,400,360)` is uniform black (`0/144000` chromatic pixels); HUD ROI
  remains positive (`2845` chromatic pixels). The frame is saved under the
  FLR-0325 evidence directory and was visually inspected.

## Hypotheses

| hypothesis | prediction | falsifier |
| --- | --- | --- |
| setter state is not retained/read by the instance | post-setter readback differs or is unavailable | readback matches `(1,0,1,1)` |
| setter state is retained but a different instance is rendered | bound-instance identity/name differs from the traced instance | same instance is bound |
| state and binding are valid but fragment output remains black | all post-override checks pass while QMP native ROI is zero | native ROI becomes chromatic |

## Plan / PDCA

1. Add only bounded post-override state/binding diagnostics in the persistent
   Devtool source and commit them.
2. Generate/register the official patch and run Mini progressive gates.
3. Capture/display the QMP full frame before ROI analysis; inspect only the
   tagged post-override slice.
4. Close this ticket at the first proven divergence and open the smallest
   possible production fix ticket.

## Result

The first missing boundary is after a valid post-override MaterialInstance is
bound and before visible native pixels. The remaining candidates are the
production material/fragment output path and the fragment-to-native-target
handoff. This ticket does not claim that Light or the static texture is the
root cause.

## UNKNOWN

- Whether the production fragment path emits a nonzero color for the valid
  PaintColor state.
- Whether the emitted fragment reaches the native target attachment.

## Evidence

- QMP full frame: `$EVIDENCE_ROOT/flr0325-0001/qmp-full.ppm`
- QMP late frame: `$EVIDENCE_ROOT/flr0325-0001/qmp-late.ppm`
- Runtime slice: `$EVIDENCE_ROOT/flr0325-0001/serial-post-override.output`
- Full/late QMP SHA-256: `dd6a7da72d21abe4d8b6bf91c7c637eb0dc75c63dafe5f2e0cfefe4caaacd6b2`

## Act

FLR-0326 owns a single opt-in fragment-output versus target-handoff
discriminator. Do not infer a Light failure from this result.
