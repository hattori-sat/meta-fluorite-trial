# FLR-0020 — explicit Flutter launch boundary evidence

## Identity

- Diagnostic rootfs SHA-256:
  `fd5eac3d4aff37541d697caf99509b99d7fe37dbcd7e0b6985d8c0d68b0d5edb`.
- Fixed kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QEMU profile: q35, TCG multi-thread, `-cpu max`, 2048 MiB, 12 vCPU,
  virtio-vga, snapshot rootfs, Wayland graphical session.
- This rootfs predates the FLR-0023 Devtool-generated fixture; the result is
  not a fixture acceptance result.

## Facts

- The guest booted the supplied kernel and mounted the snapshot rootfs on
  `/dev/vda`; the guest reported 12 CPUs.
- AGL systemd reached the graphical target, started `applaunchd`, created the
  UID 1001 runtime directory, and started the AGL compositor.
- Before explicit launch, no `flutter-auto` application process was running.
  The image did contain `/usr/bin/flutter-auto`, `/usr/bin/homescreen`, the
  Flutter engine, and the Fluorite demo release bundle.
- An explicit launch as the registered `agl-driver` role with
  `WAYLAND_DISPLAY=wayland-0` and the demo release bundle produced:
  - Application Id `fluorite`;
  - 1280x720 fullscreen view;
  - Vulkan instance extensions `VK_KHR_surface` and
    `VK_KHR_wayland_surface`;
  - a Vulkan device/driver line with API 1.3; and
  - Flutter AOT loading of `libapp.so`.
- The Dart payload then threw `Null check operator used on a null value` at
  `TrainsetSceneView.cameras`, called by `poGetScenesCameras` from
  `_MyAppState.poGetFilamentScene`.
- The bounded launch was stopped after 30 seconds; no fixture/native entity,
  Filament frame, child Wayland attach/commit, or screen-pixel acceptance was
  claimed from this run.

## Inferences

- For this exact diagnostic artifact, the first observed divergence is in Dart
  scene construction after Vulkan initialization and before native 3D scene
  creation. This supports the user's “the thing to display was not created”
  line of investigation.
- The image has a producer binary and bundle, but it does not auto-launch the
  producer in this session; explicit launcher action is part of the capability
  contract.
- The exception is not evidence against Vulkan or the Wayland compositor. It
  is a separate payload/source contract failure that must be removed before a
  WSI/child-surface verdict is attributable.

## Hypotheses

1. The old diagnostic payload's camera access is malformed for the pinned
   native/Dart contract. Prediction: the FLR-0023 minimal fixture avoids
   `poGetScenesCameras` and reaches native scene creation.
2. If the fixture also fails after AOT load, the next boundary is the native
   platform-view/bootstrap or WSI path rather than missing Dart geometry.

## UNKNOWN

- Whether the Devtool-generated FLR-0023 fixture compiles into a payload and
  removes this camera exception.
- Whether a fixture-created entity reaches Filament frame completion and child
  Wayland commit.
- Whether the homescreen is the intended launcher/consumer for this image; the
  current image metadata did not include the expected homescreen package token.
