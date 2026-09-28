# Plan: FLR-0130 — align the deserialized scene-camera handoff with ViewTarget

## Goal

Prove or falsify the current-source API contract between Dart `scene.camera` and
the native ViewTarget CameraManager, then verify the smallest default-primary
replacement fix with the normal lit Dart fixture.

## Constraints

- Use the fixed Mac Podman Devtool state/container and current source.
- Keep the canonical `meta-fluorite-trial` layer as the source of truth.
- Reuse the fixed Mini receiver, build, TMPDIR, and QMP evidence root.
- Do not change material, ViewTarget blend mode, scene content, lighting,
  compositor order, or QEMU settings in this ticket.
- Use exactly one QEMU and QMP-only framebuffer evidence.

## Steps

1. Record the actual API-generation sender, existing message handler, default
   primary-camera creation, receiver method, and unique-pointer ownership.
2. Edit only the default-primary guard in
   `ViewTargetSystem::vSetCameraFromSerializedData()` in the Mac Devtool source
   workspace, preserving the existing receiver and ownership path.
3. Commit the source through the Devtool source wrapper and run official
   `finish` into the fixed finish layer.
4. Register the untouched generated patch in the canonical recipe, commit,
   bundle to Mini, and pass progressive BitBake gates.
5. Start one QEMU after preflight, launch the normal lit Dart fixture, capture
   bounded camera/shape/submit/present markers and QMP early/late/video
   evidence, then quit through QMP.
6. Update the ticket and working log, classify the camera hypothesis, and split
   the next boundary into a new ticket before further source changes.

## Acceptance

- The patch is current-source and Devtool-generated, with its SHA-256 recorded.
- Runtime evidence shows that the deserialized camera message is received and
  the native CameraManager handoff is called, but the fixed QMP region does not
  become geometry-bearing.
- The next independent boundary is FLR-0131: existing Vulkan target tracing
  will distinguish no-Draw from Draw-but-hidden without another source change.
- Build identity, logs, screenshots/video, analysis, and zero-residual teardown
  are recorded before the ticket is marked Waiting or Done.
