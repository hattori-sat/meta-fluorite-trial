# FLR-0070 — trace explicit-light operation

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan roles
- Created: 2026-09-11
- Depends on: [FLR-0069](FLR-0069-compare-alternate-single-light.md)
- Working log: `work/logs/2026-09-11-flr0070.md`

## Work unit

Enable the existing opt-in `FLR0026_NATIVE_LIGHT_OPERATION_TRACE` on the
fixed runtime image. Capture the native light state immediately after
`BuildLightAndAddToScene` for one explicit light while holding all other
conditions constant. This is a runtime-only observation ticket; no source
edit, new patch, or new image is justified before the trace is inspected.

## Success criteria

- Reuse the fixed Mini build/TMPDIR, one QEMU, one compositor owner, one short
  evidence directory, and QMP-only capture.
- Keep `DEFAULT` indirect light, skybox skip/clear, Sequoia model selection,
  `FLR0026_NATIVE_LIGHT_LIMIT=1`, backend, camera, and app launch constant.
- Record the selected GUID/type, post-operation native entity/component/
  instance/scene state, QMP pixel count/bounding box, frame hash, selected
  runtime markers, and exact cleanup.
- Decide whether light registration itself reports a valid native state. Do
  not infer target correctness from state validity alone.

## Facts / inferences / hypotheses / UNKNOWN

### Facts

- FLR-0068 and FLR-0069 showed that two different single POINT lights each
  reproduce the black model target while scene add, camera, submit, and
  present markers remain positive.
- Patch 0192 already provides the opt-in operation trace and reports state
  after `BuildLightAndAddToScene`; its default is unchanged when the variable
  is absent.
- On the fixed candidate rootfs, p9 used `DEFAULT` indirect light, skipped
  GUID 126, selected only `guid=128`, limited the setup to one light, and
  enabled only `FLR0026_NATIVE_LIGHT_OPERATION_TRACE` compared with p8.
- The p9 marker immediately after `BuildLightAndAddToScene` was
  `native_entity=5 light_component=true instance_valid=true
  scene_has_entity=true scene_light_count=1 position=(74.5,1.2,67.15)`.
- The five QMP-only frames in p9 contained 3D pixels in all captures. The
  final frame changed `5510/223200` pixels in the candidate region, with
  bounding box `[300,80,620,320]`; the HUD region changed `3961/100000`.
- The p9 frame SHA-256 is
  `3bc9fc3442750f1331f1baf43f55ec212f02b59a8c191712b461edea8254dd06` and
  the copied runtime log SHA-256 is
  `86fe6f8cc244a53892b21cc318c919c8fb9c714957af9956527c2d6c1c8e44e9`.
- QMP teardown accepted `quit`; the final state recorded no QEMU process and
  no QMP socket.

### Hypotheses

- H1: post-operation native light state is invalid or absent, identifying a
  registration failure before shaded drawing.
- H2: post-operation native state is valid and present in the Scene, moving the
  boundary downstream to material/pipeline, target, or composition.
- H3: the trace itself changes timing or output; compare only markers and QMP
  evidence under the same one-light profile.

### UNKNOWN

- Whether a valid native light state is sufficient for shaded model pixels.
- The exact operation after native registration that is affected by the trace,
  including whether a native getter causes synchronization or only changes
  scheduling.
- Whether the production path is visible without any diagnostic side effect.

## Plan / Do / Check / Act

### Plan

- Run one single-light profile with `FLR0026_NATIVE_LIGHT_OPERATION_TRACE=1`.
- Use the existing candidate rootfs and no source-dependent build step.

### Do

- Ran the fixed Mini/QEMU p9 profile with one recorded QEMU owner and QMP-only
  framebuffer capture.

### Check

- H1 is falsified: the native entity, light component, instance, and Scene
  registration all reported valid state.
- H2 is supported for registration: native light setup reached a valid state,
  and the same run reached model scene-add, submit, present, and visible QMP
  pixels.
- H3 is supported as a runtime-effect observation: p8 was black under the same
  one-light profile without the operation trace, while p9 was visible with the
  trace. This does not make the trace a product fix.

## Visual evidence

- Evidence ID: `FLR-0070-p9`
- Run: fixed candidate rootfs; image SHA-256
  `c8ee1fc3e4e0a467ed642a939120788040fd1dc96bd71f6cc72ebc92d60f37d1`.
- Stimulus: launch `flutter-auto`, keep the Sequoia model/camera and
  composition profile fixed, select only POINT light GUID 128, and enable the
  native light operation trace.
- QMP screenshot: `$EVIDENCE_ROOT/flr0070/p9/light-skip126-limit1-optrace/frames/frame-00004.ppm`.
- Observed: 2D HUD and the Sequoia 3D model are simultaneously visible. The
  QMP candidate region is non-black in all five captures.
- Pixel evidence: final frame changed `5510/223200` candidate pixels and
  `3961/100000` HUD pixels; frame SHA-256 is recorded above.
- Teardown: `qmp=PASS`, accepted `quit`, residual QEMU process/socket count is
  zero in `final-state.txt`.

### Act

- Close this runtime-only gate. The next independent unit is FLR-0071, which
  separates the trace's native-state query from a pure timing-only diagnostic.
- Mac remains the only source-edit and patch-generation location. Mini remains
  authoritative for `do_patch`, BitBake, image production, QEMU, and QMP
  validation.
