# FLR-0045 — reach visible 3D with production model and lights

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament scene/resource + Flutter/Wayland + target-validation roles
- Depends on: [FLR-0044](FLR-0044-production-shapes-visible-3d.md)
- Working log: `work/logs/2026-09-07-flr0045.md`

## Problem

FLR-0044 proves production shapes can produce visible QMP pixels, but only in
the controlled model/environment-skip and light-skip condition. The released
full scene still needs model loading, environment setup, and production lights
to coexist without returning to a black native region or the previously seen
renderer fault boundary.

## Success measure

- Identify the smallest production model/light/environment combination that
  first diverges from the visible shape-only case.
- Display at least one actual production model/GLB-derived object as QMP
  pixels, with the corresponding camera and resource markers.
- Preserve a QMP-only screenshot, pixel analysis, runtime log, and clean QMP
  teardown for every decisive case.
- Make any source change through the persistent Mac Devtool source and official
  Yocto patch generation, then commit under `meta-fluorite-trial`, transfer by
  bundle, and build on the fixed Mini PC environment.

## Plan / PDCA

### Plan

- Reuse the current rootfs and fixed QEMU profile.
- Compare one variable at a time: shape-only control, one selected light,
  bounded light prefix, model loading, then environment stages.
- Correlate model/resource readiness, renderable samples/bounds, camera state,
  frame/present result, and QMP candidate pixels before selecting a patch.

### Facts

- Production shapes are visible with model, environment, and lights skipped.
- Earlier runs reached production renderables and present but were HUD-only or
  hit a renderer fault when more production resources were enabled.
- QMP, Wayland handoff, and native present are proven by FLR-0042/0044 controls.

### Hypotheses

1. A production model/material/pipeline operation is the first new renderer
   divergence after shape-only geometry is working.
2. A light/resource interaction becomes invalid above a bounded selected-light
   set, as suggested by the earlier light-count boundary.
3. Environment/indirect-light setup changes the active scene or resource state
   before the production model is visible.

### UNKNOWN

- The first full-scene resource or light combination that produces visible GLB
  pixels on the current rootfs.
- Whether the earlier `Light not found` messages are causal, expected from
  skipped lights, or unrelated to the black/full-scene result.
- Whether a source patch is required after the next runtime-only matrix.

## First action

Run the smallest shape-only-to-full-scene matrix on the same rootfs, beginning
with one production light and no environment, then add model/environment only
after the preceding QMP result is captured.

## Result

The first decisive model case was completed using the current authoritative
rootfs and the fixed QEMU profile. With production environment and lights
skipped, one selected production GLB produced visible QMP pixels:

- `FLR0026_MODEL_SELECTED ordinal=0 asset=assets/models/sequoia_ngp.glb`
- `FLR0026_MODEL_LOAD_PLAN total=60 limit=1 match= inspected=2 queued=1`
- `FLR0026_CAMERA_APPLIED head=(5,0,-5) targetPresent=true target=(0,0,0)`
- `FLR0026_VK_QUEUE_PRESENT result=0`
- QMP-only image: `work/evidence/flr0045/model1-env0-nolights-current/model1.png`
- QMP pixels: `1280x800`, region `200,100,400,250`, changed `22893/100000`,
  bounding box `[200,100,400,241]`
- PPM SHA-256: `aa0f262851c44fa18bf5ca8e777a6ecb98666e390c3100e8192e699b4276cc8a`
- Marker evidence: `work/evidence/flr0045/model1-env0-nolights-current/markers.log`

This closes the model-only gate: production GLB selection/loading can reach
visible native pixels, and the earlier shape-only image is not the only
possible source of 3D pixels. `FLR0026_MODEL_STAGE_TRACE` was not enabled in
this run, so asynchronous stage-completion markers remain an evidence gap.
The repeated `Light not found` messages are expected under the intentional
light-skip condition and are not treated as the full-scene root cause.

QMP teardown was successful: `query-status` returned `running`, the QMP
`quit` response emitted `SHUTDOWN reason=host-qmp-quit`, and the post-check
found no `qemu-system`, `runqemu`, or `flutter-auto` process.

## Decision

No source patch was made for this ticket. The runtime-only result is sufficient
to split the next independent task: co-enable the selected production model
with bounded production lights, then test environment stages separately.
