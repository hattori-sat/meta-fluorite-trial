# FLR-0026 — 0054 camera-origin boundary

## Outcome

The self-created Cube reaches a native renderable and the Flutter 2D overlay is
visible in a QMP-only 720x400 screenshot. The Cube itself is not visible yet.
The marker evidence identifies the fixture camera as an origin-state candidate.

## Facts

- Project revision: `b09af44`.
- Devtool source commit: `41fe401`.
- Devtool baseline import commit: `a5a5acf`.
- Generated patch: `0054-filament-view-shape-camera-state-markers.patch`.
- Generated patch SHA-256:
  `b120884f9940da181292530e5477ae40b0dca4f02edf4b76aa36136665116b37`.
- Mini-PC receiver: isolated `$BUILD_HOST` receiver at detached `b09af44`.
- Build results: `do_patch` 104/104 succeeded; `do_compile` 2592/2592
  succeeded; full image 11748/11748 succeeded.
- Artifact SHA-256 values:
  - rootfs: `90ea826ac395cb27ba4355921179c01b4560b4b5cd7170fa099e2f6ce6134cbf`
  - kernel: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
  - qemuboot:
    `2e3bab8f942bdabe9131a54ef204e8f8376e666ecc5242a43caa173708085cf2`
- QMP screenshot: `/private/tmp/flr0026-qemu-b09af44/run/after-flutter-run-30s.ppm`.
- QMP screenshot SHA-256:
  `ded9bd9324d1bb86aeb53cfd6627ccfcce72fdee5f74ad87c136283dbe500087`.
- QMP screenshot analysis against black, full 720x400 region:
  `changed_pixels=24908`, `changed_ratio=0.08648611111111111`,
  `bounding_box=[0,7,696,393]`.
- The screenshot visibly shows `Fluorite Game Engine`, `FPS: 20 / 60`,
  nonzero `CPU`, `GPU`, and `Script`, a graph, `Scenes`, and the bottom
  shape/collider/quality controls. The central 3D area remains black.
- Native markers from the same run:

  ```text
  FLR0026_SHAPE_READY guid=4 entity=6 renderable=true
  FLR0026_WAYLAND_SURFACE_CREATED surface=true subsurface=true parent=true
  FLR0026_CAMERA_APPLIED head=(0,0,0) targetPresent=true target=(0,0,0) dolly=(0,0,0)
  Native is ready. Proceeding...
  vkCreateSwapchain: 720x400, 44, 0, swapchain-size=5, identity-transform=true, depth=126, protected=false
  ```

- The first QEMU attempt hit host block `io-status=nospace`; it was ended by
  QMP `quit`. The final run was also ended by QMP `quit`, followed by a
  zero-result `qemu-system-x86_64` process check.

## Inferences

- Payload delivery, native entity creation, renderable creation, Wayland
  surface creation, and swapchain creation are all demonstrated.
- `renderable=true` rules out the narrow hypothesis that the Cube never became
  a renderable.
- The origin camera marker is compatible with the black 3D region. The Dart
  `orbitDistance`/legacy `flightStartPosition` values are not reflected in the
  native `dollyOffset` observed here.

## Hypotheses

1. A fixture camera with serialized `dollyOffset=(5,0,0)` will produce a
   non-origin native head and expose the Cube to the camera.
2. If that marker changes without 3D pixels, inspect Filament draw/present and
   child-surface geometry next.

## UNKNOWN

- Visible 3D pixels after changing the camera.
- Reliable QMP activation of the Scenes route in this run.
- Planetarium and other production-scene 3D pixels.
- Whether the prepared Dart effective-source baseline can be re-registered by
  devtool after Docker Desktop recovers.

## Prepared next source baseline

- Fixed upstream SRCREV: `2626d1757f18e438f4095e38e413eb40eab40b6d`.
- Effective Dart source baseline commit: `2b5b019`.
- Baseline includes the recipe's existing Dart patches in their registered
  order. It is separate from the active project layer and has no new camera
  change yet.
- The next source-only change is limited to serializing an explicit
  `dollyOffset` for the self-created fixture camera. It must be registered and
  finished through Mac Docker devtool before entering `meta-fluorite-trial`.

## Stored evidence

- `/private/tmp/flr0026-qemu-b09af44/run/after-flutter-run-30s.ppm`
- `/private/tmp/flr0026-qemu-b09af44/run/after-flutter-run-30s.png`
