# FLR-0260 — diagnose black production render content after PlatformView return

- Status: Done (diagnostic A/B complete; FLR-0261 owns current-source scene-stage tracing)
- Priority: High
- Owner: Fluorite Filament scene/render-target content
- Created: 2026-09-21
- Predecessor: [FLR-0259](FLR-0259-trace-platform-view-create-block.md)

## Objective

Determine why the now-composited Fluorite PlatformView surface contains a
black render result even though production shapes are created and Vulkan
present succeeds.

## Facts

- FLR-0259 repair makes the PlatformView handler return and Flutter receives
  `onPlatformViewCreated`.
- QMP shows a white 2D surface and a black trapezoidal PlatformView surface,
  so the PlatformView geometry/placement is no longer completely absent.
- The runtime log reports many `FLR0026_SHAPE_READY ... renderable=true` lines
  and successful Vulkan queue-present markers.
- The production ROI still has zero chromatic pixels.
- Historical FLR-0049 evidence proves that the Sequoia GLB can produce QMP
  pixels under a no-readback runtime with environment/lighting/shape skip
  controls; this is not a blanket GLB failure.
- The current `flutter-auto_2.0.bbappend` registers `0181`, `0183`, and
  `0184`, but not the historical `0179`, `0180`, or `0187` controls. The old
  patches fail `git apply --check` against the current Devtool source, so they
  cannot be re-registered unchanged.
- A runtime-only route attempt on the repaired image used
  `FLUORITE_NATIVE_EMPTY_INPUT_REGION=1`. The QMP initial, move-x, move-y,
  down, and up frames were byte-identical with SHA-256
  `14b1c905bead455d72134d2906a33a32c62e7df43c811f7aff25da4fa99b6cf8`.
  The frame was already in the known white-parent/black-native state, so this
  run does not establish a Planetarium transition.
- The first route-launch attempt failed as an observation attempt because the
  harness was given the literal prompt `root@.*# ` instead of the guest's
  exact `root@qemux86-64:~# ` prompt. The corrected attempt passed
  `serial-exec`; both the failed command and corrected evidence remain under
  `evidence/FLR-0260/route-empty-input/` on the fixed Mini receiver.
- The corrected bounded log has `FLR0236_SCENE_ACTIVATION=0`,
  `FLR0026_MODEL_SELECTED=60`, `FLR0026_VK_QUEUE_PRESENT=4`,
  `FLUORITE_VIEWTARGET_BEGIN_FRAME_TRUE=4`, and
  `FLUORITE_VIEWTARGET_BEGIN_FRAME_FALSE=1152`. No route transition marker was
  observed in this image.
- The current-source diagnostic stage-isolation A/B was built on Mini and ran
  with no readback, Sequoia match, and model limit 2. Ten QMP frames were
  byte-identical (SHA
  `fcc12e263ff0b1271466210f6b2ebe5c31ec093b0641354dc7f9ccebb8878c19`). In
  ROI `[200,100,400,250]`, `chromatic_pixels=0` and `max_chroma=0`; the image
  contained a black upper area and a white lower surface, with no Sequoia or
  red-light pixels.
- The same bounded log reported `FLR0026_MODEL_SELECTED=2`,
  `FLR0026_VK_QUEUE_PRESENT=8`, and four true frame-boundary events. The
  scene-add marker is unavailable in the current recipe, and explicit skip
  branch markers were absent, so branch execution is UNKNOWN.
- The app and QEMU were stopped cleanly: scoped PID stop followed by QMP
  `quit`, with zero residual targets and zero residual QMP sockets.

## Conclusion

The current-source reintroduction of the historical stage-isolation controls
did not reproduce production Sequoia pixels. Model selection and Vulkan
Present were positive, but QMP still had zero chromatic pixels. This ticket's
diagnostic A/B is complete; the first scene-stage zero remains UNKNOWN because
the current recipe lacks a Scene-add marker. [FLR-0261](FLR-0261-trace-current-production-scene-stages.md)
owns the next bounded trace.

## Hypotheses

1. Production models and renderables exist, but the active camera/light/material
   contract produces black output.
2. The active Filament view/viewport or render target contains only the clear
   value while present succeeds.
3. The PlatformView surface is composed correctly, but the production scene is
   not the scene actually bound to the presented ViewTarget.
4. The current source lost the historical stage-isolation controls during the
   patch-stack reconciliation; without them, the old successful Sequoia
   condition cannot be reproduced. Prediction: a current-source diagnostic
   rebase of those controls will allow a valid no-readback A/B, without
   changing the default path.

## Scope boundary

Use bounded frame-contract, scene/camera/light/material, render-target, and
QMP evidence. Do not change multiple scene variables at once. Any repair must
be a separate ticket after the first zero boundary is identified.

## Success criteria

- Identify the first boundary where production render content becomes black.
- Distinguish internal Filament content from Wayland/QMP composition.
- Preserve the fixed Mac Devtool → canonical layer → Mini bundle/build → QMP
  loop for any required source change.

## Verification plan

1. Run the current fixed image with the existing frame-contract trace enabled.
2. Correlate scene, camera, viewport, material/light, draw, present, and QMP
   evidence using one bounded run.
3. Split the smallest repair into its own ticket only after classification.
4. Use the current-source Devtool diagnostic patch to reproduce the historical
   Sequoia condition, then compare no-readback QMP pixels and bounded model /
   present markers. Do not treat a diagnostic skip as the production fix.
5. Because the stage-isolation A/B still has zero chromatic production pixels,
   add current-source scene-stage markers around model load, scene add, draw
   submission, and ViewTarget binding through Devtool, then repeat one bounded
   no-input QMP run. Keep composition/stacking tests separate from scene
   content tests.

## UNKNOWN

- Whether the active production camera sees the loaded renderables.
- Whether the production material/light path writes non-black color.
- Whether the black surface is a clear value or a rendered black scene.
- Whether the requested stage-skip branches executed in the current binary;
  explicit branch markers were not present in the bounded log slice.
- The first current-source scene-stage boundary after model selection; the
  current `MODEL_STAGE_SCENE_ADD_DONE` marker is not registered.
