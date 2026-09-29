# FLR-0023 — full-scene clean-branch reference

This repository-safe summary preserves the full-scene result used by the
FLR-0023 comparison. It is derived from the probe-free clean-branch QEMU
runtime record and contains no machine-specific paths or connection details.

## Artifact and condition

- Rootfs SHA-256:
  `e218933d1c666566596094375ed6996a3d23b4e871137fa3bb57b296bd055cfc`
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- QEMU: qemux86-64, q35, 2048 MiB, 12 vCPU, TCG, virtio-vga, snapshot disk
- Vulkan device: Mesa llvmpipe 24.0.7 / LLVM 18.1.8

## Observed boundaries

- AGL boot, compositor, Wayland session, Vulkan, Filament initialization, and
  swapchain creation: PASS.
- The dynamic 2D overlay changed, and the Scenes menu displayed Playground,
  Radar, Settings, Planetarium, and Trainset: PASS.
- The 3D region remained black at startup. After Playground selection, the
  runtime entered a long processing state, later showed `FPS: 0`, and became
  all white while QEMU remained alive: 3D scene acceptance FAIL.

## Interpretation

The full-scene reference proves that the startup 2D/menu path can be active
without proving visible 3D presentation. It is a comparison reference, not a
claim that the released full scene is healthy.
