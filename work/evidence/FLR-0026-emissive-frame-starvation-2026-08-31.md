# FLR-0026 — emissive fixture frame-starvation boundary — 2026-08-31

## Outcome

The self-created emissive Cube still produces no visible 3D pixels in the
QMP-only QEMU framebuffer. The 2D Flutter overlay is reproducible. Native
markers now localize the active failure more narrowly: Filament acquires and
ends only the first two frames, then `beginFrame` returns false continuously.

## Facts

- Project revision under test: `be081b4d9402b6c23c53604d050d0585367206fc`.
- The fixture uses the packaged lit material with a blue emissive color; the
  source change was generated through the persistent Mac Devtool workspace and
  imported unchanged as project patch `0021`.
- The fixed mini-PC receiver built the target demo task and the full
  `agl-ivi-image-flutter` image successfully. The resulting rootfs SHA-256 is
  `b6c0d5c608c227e60b3daea15f349e59c84285d737b1bd813be56598b0f89821`.
- The QEMU-only PPM at the stable post-launch point is stored under the role
  locator `$QEMU_ARTIFACT_ROOT/flr0023-qemu-unlit/run/emissive-tcp3-after30.ppm`.
  Its SHA-256 is
  `355f151ef464a1ad63c2939a72e4c640cba78a1ed039415d0f8ef81e1070bcc8`.
- QMP analysis against black reports:
  - full `720x400`: `changed_pixels=7274`,
    `changed_ratio=0.025256944444444443`, bounding box `[4,7,692,193]`;
  - candidate 3D region `[200,100,400,250]`: `changed_pixels=0`.
- The PPM visibly contains `Fluorite Game Engine`, FPS, Frametime, CPU, GPU,
  Script, graph, Scenes, and the bottom controls. The central candidate 3D
  region is black.
- The guest log reports one fixture renderable and a camera aimed at the
  origin:

  ```text
  FLR0026_SHAPE_READY ... renderable=true
  FLR0026_CAMERA_APPLIED head=(0,0,-5) target=(0,0,0) dolly=(5,0,0)
  ```

- Frame lifecycle counts from the same run are `FLR0026_FRAME_END=2` and the
  first frame markers are:

  ```text
  FLR0026_FRAME_BEGIN seq=1 started=true
  FLR0026_FRAME_BEGIN seq=2 started=true
  FLR0026_FRAME_BEGIN seq=3 started=false
  FLR0026_FRAME_BEGIN seq=10 started=false
  ```

  Later markers remain `started=false` while the Flutter overlay continues to
  update.
- The AGL compositor watchdog stopped the first TCP-serial boot's compositor.
  Restarting `agl-compositor.service` before launching `flutter-auto` restored
  the known 2D overlay; this is an environment/startup condition, not a 3D
  success.
- Existing project patch
  `0058-filament-view-explicit-subsurface-commit-devtool.patch` was generated
  through Devtool in an earlier iteration and is currently not registered in
  `flutter-auto_2.0.bbappend`. The next local change registers that unchanged
  patch for the transparent composition path.

## Inferences

- The camera and native renderable boundaries are crossed, but no stable
  Filament render/present sequence exists after the first two frame attempts.
- The zero central pixels cannot yet distinguish a missing Wayland commit from
  a Vulkan swapchain image-release problem, but it is earlier than a reliable
  10-second visible-3D acceptance.
- The 2D baseline is not regressed: it is present after compositor recovery,
  with non-zero CPU/GPU/Script overlay values.

## Hypotheses

1. The missing explicit child-surface commit prevents the compositor or WSI
   path from releasing acquired swapchain images, causing later `beginFrame`
   calls to return false. Re-registering `0058` predicts continued frame
   acquisition and a non-zero native pixel candidate.
2. If `0058` does not change the `started=false` sequence, the next boundary is
   Vulkan WSI/swapchain image release or compositor protocol behavior rather
   than Dart scene data, camera placement, or material loading.
3. A separate production-route issue may remain after the fixture path is
   fixed; Planetarium is not accepted until its own QMP pixel evidence exists.

## UNKNOWN

- Whether the first two successful frames contain Cube pixels.
- Whether the explicit commit patch changes swapchain image availability.
- Whether production Planetarium can be selected reliably through QMP input and
  produce visible 3D pixels.

