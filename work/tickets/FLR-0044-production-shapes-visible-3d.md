# FLR-0044 — make production shapes reach visible 3D pixels

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament scene/resource + Flutter/Wayland + target-validation roles
- Depends on: [FLR-0043](FLR-0043-production-scene-visible-3d.md)
- Working log: `work/logs/2026-09-07-flr0043.md`

## Problem

FLR-0043 proved that the production Scene can display a self-made native cube
when the existing production shape setup is skipped. With shape setup enabled,
the released Example Demo remains HUD-only even though production shapes report
`renderable=true`. The remaining task is to make an actual production shape or
GLB visible, not to keep the diagnostic cube as a product workaround.

## Success measure

- Identify the first shape/resource operation that differs between the visible
  shape-skipped control and the shape-enabled production path.
- Display at least one actual production asset as QMP-captured 3D pixels with
  the production shape path enabled.
- Correlate the result with native render/present markers and retain a QMP-only
  screenshot plus pixel analysis.
- Keep source changes on the Mac persistent Devtool source, generate patches by
  the official Yocto Devtool/patch API, commit them under `meta-fluorite-trial`,
  transfer by Git bundle, and build on the fixed Mini PC receiver/build/TMPDIR.
- Use one QEMU instance at a time and close it through QMP before the next case.

## Plan / PDCA

### Plan

- Reuse the FLR-0043 rootfs/profile as a control and compare shape-enabled and
  shape-skipped production runs before editing source.
- Inspect `ShapeSystem`, shape-to-renderable creation, entity ownership,
  material/vertex-buffer readiness, camera bounds, and downstream scene add
  operations in the runtime log and source.
- Select one smallest divergent operation, edit it through the persistent Mac
  Devtool source, and validate the generated patch with authoritative
  `do_patch` before a full image rebuild.

### Facts

- Shape-skipped production Scene: self-made native cube is visible in QMP.
- Shape-enabled production runs: all 37 shapes reported `renderable=true`, but
  the QMP candidate region remained HUD-only.
- `QUEUE_PRESENT result=0` and `COMMIT_DONE` are present in the shape-skipped
  run, so global Vulkan present and QMP capture are not the current blocker.

## Completed result

- The exact historical shape-only condition was replayed on the new
  `20260907130705` rootfs: `FLR0026_NATIVE_SKIP_MODEL_LOAD=1`,
  `FLR0026_NATIVE_SKIP_ENVIRONMENT=1`, and
  `FLR0027_NATIVE_SKIP_LIGHTS=1`. No force-render or sync-trace diagnostic
  variable was added.
- The QMP-only screenshot
  `work/evidence/flr0044/shape-only-past-flags-current/shape-only-past-flags.png`
  shows multiple production shapes and wireframes on the QEMU framebuffer.
  Region `[200,100,400,250]` changed `37588/100000` pixels with bounding box
  `[200,100,400,250]`; the source PPM SHA-256 is
  `adfaa6d873dfee169c44299939f375a483c463be701f221c9bd717ec9eed5352`.
- Runtime evidence records `FLR0027_NATIVE_SKIP_LIGHTS enabled=true`, 37
  `FLR0026_SHAPE_READY ... renderable=true` entries, camera application,
  `FLR0026_FRAME_BEGIN`, successful queue present, present-boundary completion,
  and commit completion. QMP shutdown returned `host-qmp-quit`.

This proves that the released Example Demo's production shape path can reach
visible 3D pixels on the current image. The earlier black result used different
model/environment and extra force/sync controls, so those conditions remain a
separate full-scene question.

### Hypotheses

1. A production shape is added to ECS but not to the same Filament Scene or
   render list as the diagnostic cube.
2. Shape resource/material readiness or an entity/component error prevents the
   production renderable from contributing visible pixels.
3. Production camera/framing places the asset outside the visible volume even
   though the shape is reported renderable.

### UNKNOWN

- Which production shape is the smallest visible candidate.
- Whether the `Entity(164): Light not found` runtime error is causal or an
  unrelated application-side request.
- Whether the released GLB contains valid camera/material/mesh data for this
  target profile.

## First gate

Run the same QMP-only production case with `FLR0027_NATIVE_SKIP_SHAPES` unset,
then compare shape/resource/entity markers against the FLR-0043 screenshot.
Do not call the diagnostic cube a production success.
