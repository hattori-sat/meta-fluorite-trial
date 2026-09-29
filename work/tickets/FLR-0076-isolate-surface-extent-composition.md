# FLR-0076 — isolate surface extent and parent composition

- Status: Done (surface extent not primary; full-scene shaded boundary split)
- Priority: High
- Owner: Mini QEMU runtime + Wayland composition diagnosis roles
- Created: 2026-09-11
- Depends on: [FLR-0075](FLR-0075-restore-production-default-indirect-light.md), [FLR-0067](FLR-0067-reintroduce-production-scene-stages.md)
- Working log: `work/logs/2026-09-11-flr0076.md`

## Work unit

Explain why the current fixed image logs a Flutter view of `1280x720` but
creates a native Wayland/Vulkan surface of `1280x800`, while historical p6
logged `1280x720` for both. Determine whether the native child covers the
Flutter parent HUD, whether the QEMU/compositor launch timing selects the
larger extent, or whether a separate rendering target issue remains. Start
with runtime-only controls and one fixed image; do not create a source patch
until the first differing operation is identified.

## Success criteria

- Reuse the fixed receiver, build directory, TMPDIR, QEMU evidence root, and
  one QMP-owned QEMU at a time.
- Reproduce the current surface markers and QMP black/bottom-controls frame
  with the exact artifact identity from FLR-0075.
- Run the smallest orthogonal surface/composition controls, including a
  native-scene-content suppression control and a compositor-ready relaunch,
  without changing the image or indirect-light source.
- For every control, retain effective surface extent, selected scene markers,
  QMP-only frames/video, HUD/3D region analysis, runtime log hash, and clean
  QMP teardown.
- Identify the first boundary that changes between the controls, or record
  UNKNOWN with the missing evidence. Do not call a thin line or a pixel count
  a visible 3D object.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0075's restored layer commit and Mini image gates passed.
- Current runtime reports app size `1280x720` and native surface extent
  `1280x800`.
- Current QMP frame shows black content with a horizontal boundary and lower
  Flutter buttons; visible 3D and HUD criteria are not met.
- Historical p6's QMP frame has HUD and lower controls, but its recorded
  `4905/223200` pixel count is not by itself visual 3D proof.

### Ranked hypotheses

1. The native child surface is 80 pixels taller than the Flutter parent and
   covers the parent content. Prediction: suppressing native scene content
   restores the HUD without changing the image or Flutter view size.
2. Compositor/output readiness or launch timing determines the native extent.
   Prediction: a compositor-ready relaunch produces `1280x720` and restores
   parent composition.
3. Surface extent is correctable, but the Filament target remains black.
   Prediction: parent HUD returns while the central 3D region remains zero.

### UNKNOWN

- Whether the extent originates in Wayland configure, Flutter embedder window
  negotiation, QEMU display profile, or a later native surface patch.
- Whether the p6 central pixel count represented meaningful 3D content.

## Plan / Do / Check / Act

### Plan

- Start from the exact FLR-0075 rootfs and one QMP run directory.
- Run one control at a time, saving the requested/effective environment and
  surface markers before interpreting pixels.
- Use QMP-only evidence and stop through negotiated QMP quit after each run.
- Generate a Mac Devtool patch only if runtime evidence identifies a source
  operation whose change is justified; Mini remains authoritative for build and
  runtime validation.

### Do

- Ran the exact FLR-0075 rootfs with one QEMU owner and QMP-only capture.
- The pure self-made native fixture rendered a bright cube together with the
  Fluorite 2D HUD. Final candidate-region result was `41750/223200` with
  bounding box `[501,278,278,162]`; HUD result was `6291/100000` with
  bounding box `[200,113,400,237]`.
- The production Sequoia model-only control rendered a recognizable car model
  in the native surface. Final candidate-region result was `140034/223200`.
  The native surface masked the parent HUD in this frame, so it is recorded as
  model-only 3D evidence, not combined composition acceptance.
- After each run, the app was stopped, QMP `quit` was accepted, the QMP socket
  was absent, and no QEMU/runqemu/flutter-auto process remained.
- Confirmed the seven inactive old Mini `flr0026-tmp*` work directories were
  not referenced by a process and removed them. The fixed TMPDIR, shared
  caches, bundle receiver, and QMP evidence were preserved.

### Check

- The surface-extent-only hypothesis is not supported as the primary cause.
  The same current image can show a native cube plus 2D HUD and can show the
  production Sequoia model alone despite the `1280x800` native versus
  `1280x720` Flutter extent mismatch.
- The general native render/present/QMP path is therefore positive. The full
  production shaded scene remains negative after DEFAULT restoration.
- The historical FLR-0070 p9 combined frame is not a stable regression
  baseline: later same-image trace/timing repetitions remained black.
- Current-image evidence hashes: pure-fixture selected runtime
  `a5b1369ce6eac9ff089305f2f9a8430cc9a7afd4a6ccd310add0c9f3c98e0239`;
  model-only selected runtime
  `ea120462d6744bd071f83c9281592d89f187e269021e71bfda73bbcfc413d2bf`.

### Act

- Close FLR-0076 at the surface/composition boundary and continue in the new
  independent FLR-0077 ticket for the first full-production shaded operation.
- Keep Mac Devtool as the source-edit and official patch-generation location.
  Keep Mini as the authoritative `do_patch`, BitBake, image, QEMU, and QMP
  location; do not use a Mini-side hand-edited patch as a substitute.
