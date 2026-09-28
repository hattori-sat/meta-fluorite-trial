# FLR-0142 — flush Wayland child surface after Filament present

- Status: Done
- Priority: High
- Owner: Fluorite ViewTarget / Wayland surface role
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0140](FLR-0140-reconcile-2d-hud-with-recovered-dart-3d.md)
- Working log: `work/logs/2026-09-13-flr0142.md`

## Work unit

Test one source-owned composition variable: flush the Wayland display after
the Filament child surface commit in `ViewTarget::OnFrame`. Keep the FLR0139
image, Dart Cube payload, camera, transparent swapchain, launch guard, QMP
region, and capture timing profile unchanged.

## Why this is the next variable

- FLR-0140's same-run evidence shows an early Flutter HUD frame followed by a
  late Cube-only frame while native render/present markers continued.
- The effective Mini source calls `wl_surface_commit(obj->surface_)` but does
  not call `wl_display_flush` at that boundary.
- A historical Devtool-generated flush patch exists in the layer but is not
  registered in the current `flutter-auto` recipe and targets an older source
  context. It must not be activated by copying it blindly.

## Success criteria

- Mac Devtool generates a fresh patch against the current effective source;
  the generated patch is copied unchanged into `meta-fluorite-trial` and
  registered after the existing `flutter-auto` patch stack.
- The fixed Mini receiver applies the patch, completes `do_patch`,
  `do_compile`, and the full image build without creating a second build/TMPDIR
  tree.
- One normal-Dart QEMU run produces QMP-only early/late evidence and proves
  either a stable combined HUD+Cube frame or a falsified flush hypothesis,
  with exact logs and hashes recorded.
- All QEMU processes are torn down through QMP and no residual target/QMP
  process remains.

## Hypotheses / UNKNOWN

- H1: the missing display flush delays child-surface state propagation and
  creates the observed parent-only then child-only final-frame sequence.
- H2: flush is not causal; the child buffer's alpha/composite contract or
  compositor stacking still hides the parent HUD.

UNKNOWN: the compositor's exact buffer alpha and the timestamped relation
between Filament present, Wayland commit, display flush, and the first QMP frame.

## Scope boundary

Do not change Dart payloads, scene transition behavior, camera API, material,
clear color, swapchain blend mode, or compositor policy in this ticket. If
flush is falsified, open a separate alpha/composite ticket.

## Iteration 1 result

### Facts

- The official Devtool-generated patch was applied to the Mini image and the
  fixed image build completed: `do_patch`, `do_compile`, and full image all
  passed.
- One QEMU run used the discovered Example Demo bundle as `agl-driver`.
  The process count was one, the runtime reached repeated Vulkan submit and
  `FLR0026_VK_QUEUE_PRESENT result=0` markers, and no coredump was reported.
- QMP prelaunch was uniform black in `[300,250,620,400]`. Post-launch QMP
  showed the black Cube on a white frame: `changed_pixels=217400`, edge
  bounding box `[525,302,232,202]`, `chromatic_pixels=0`, luma `[1,255]`,
  and `geometry_indicator=present`.
- The post-launch PPM SHA-256 is
  `481442329d0e5517eeeed016b3fd18f8b94294bb0f503c082479cfc40edee0c4`.
  The 12 QMP video frames all have the same PPM SHA. The Mac-preview MP4
  SHA-256 is `37ca108cdb5e017375fceadc5387f9712bbd109cf529dc9753b16b888f4ad84f`.
- QMP teardown negotiated `quit` and reported zero residual target processes
  and zero residual QMP sockets.

### Inferences

- The flush patch does not restore the 2D HUD in the final frame: the result
  matches FLR-0139's late Cube-only frame. H1 is falsified for this image.
- The 3D renderer and child surface are not absent. The remaining owner is
  the parent/child alpha or stacking/activation contract, while the separate
  Dart/native scene and camera API mismatch remains open in FLR-0141.

### Decision

- Close FLR-0142 as a falsified one-variable flush probe. Do not retain the
  flush patch as a product fix; its generated patch and build evidence remain
  in the repository for provenance and comparison.
