# FLR-0262 — split native readback from QMP composition

- Status: Done
- Priority: High
- Owner: Filament native swapchain readback / Wayland-QEMU composition boundary
- Created: 2026-09-24
- Predecessor: [FLR-0261](FLR-0261-trace-current-production-scene-stages.md)

## Objective

Use the existing environment-gated native swapchain readback to determine
whether production 3D pixels are already present after Filament rendering or
are lost only at the Wayland/QEMU composition boundary.

## Facts

- FLR-0261 recorded positive production model selection, asset load, Scene
  insertion, entity setup, Draw submit/end, active default Scene, and Vulkan
  queue-present markers.
- The paired QMP frame was stable across ten captures and remained effectively
  black/grayscale in ROI `[200,100,400,250]`: `22893/100000` changed pixels,
  `chromatic=0`, `max_chroma=4`, with `77107` black and `22893` white pixels.
- The current image already contains the `FLUORITE_NATIVE_SWAPCHAIN_READBACK`
  diagnostic and the existing Mini artifact is sufficient; no source patch is
  required for this observation.

## Hypotheses

1. Native readback is zero: the first failing boundary remains inside Vulkan
   pixel generation, attachment contents, or readback semantics.
2. Native readback is nonzero while QMP remains black: the first failing
   boundary is Wayland child-surface or QEMU composition.
3. Readback is null/incomplete: the readback contract itself is not yet a
   valid discriminator and needs a separate bounded diagnostic.

## Scope boundary

One no-input QEMU run using the existing verified image. Enable only the
existing readback and scene-stage markers. Do not change camera, material,
lighting, composition, source, or product behavior.

## Success criteria

- One QMP-only runtime records the existing scene-stage markers and the native
  readback request/result.
- Ten QMP frames are captured and paired with bounded pixel statistics.
- QEMU is quit through QMP and residual process/socket checks pass.
- The first-zero boundary is classified from the paired readback and QMP
  evidence, with the remaining 3D-shape/color proof explicitly split out.

## Verification plan

1. Reuse the fixed Mini receiver, build, TMPDIR, and image from FLR-0261.
2. Start exactly one QEMU through `qemu-runtime-harness.sh`.
3. Launch the production Fluorite example with
   `FLUORITE_NATIVE_SWAPCHAIN_READBACK=1` and the bounded scene-stage traces.
4. Capture readback logs and ten QMP frames without input.
5. Quit through QMP, verify no residual QEMU/flutter-auto process, and record
   hashes and paths.

## Result

- The same Mini image ran one bounded QEMU observation with no input.
- Readback completed twice: `nonzero_pixels=1024000/1024000`,
  `byte_sum=723049563`, `max_byte=255`, `buffer_null=false`.
- The paired QMP capture completed ten frames. All ten had SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- QMP ROI `[200,100,400,250]` was completely black:
  `changed_pixels=0`, `chromatic_pixels=0`, `max_chroma=0`,
  `luma_range=[0,0]`.
- QMP quit and cleanup passed with `residual_targets=0 residual_qmp=0`.

## Boundary decision

- The result supports native-content-to-composition loss: native readback has
  nonzero content while the paired QMP 3D candidate is black.
- This does not yet prove that the native nonzero buffer contains the intended
  production car geometry/color, because the existing callback reports whole
  image nonzero statistics rather than a 3D ROI/chroma breakdown.
- FLR-0263 owns the next no-source-change check using the existing
  `FLUORITE_NATIVE_READBACK_TO_SHM=1` path to test whether native readback can
  reach the visible Wayland surface.

## Evidence

- Mini runtime directory:
  `/mnt/yocto/flourite-receivers/flr0023-835a04e/evidence/FLR-0262/0280-runtime`
- Combined serial log: `readback-serial.log`
- Delayed callback log: `readback-log-slice.log`
- QMP frames: `qmp-frames/frame-00000.ppm` through `frame-00009.ppm`
