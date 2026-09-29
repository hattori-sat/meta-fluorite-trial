# FLR-0021 — homescreen and image activation evidence

## Facts

- The active `ivi-homescreen` recipe is version 2.0 and declares a Vulkan
  loader dependency.
- Its effective package options include `backend-wayland-vulkan` and
  `egl-transparency`; its source also carries a Wayland/Vulkan patch.
- In the normal r2 candidate configuration, `bitbake -e ivi-homescreen` fails
  before task execution because `vulkan-loader` is skipped when `vulkan` is
  absent from `DISTRO_FEATURES`.
- A temporary `bitbake -R` append for `vulkan` allows the homescreen metadata to
  resolve. This was an observation-only override and was not persisted.
- Under that temporary override, the effective `agl-ivi-image-flutter`
  metadata contains no `packagegroup-fluorite-demo`, `ivi-homescreen`,
  `agl-shell-activator`, or `window-management-client-grpc` in the image
  install token set.

## Inferences

- Vulkan initialization evidence alone does not establish that the selected
  image contains a homescreen or the Fluorite demo to render.
- The question “3D is not displayable” must be split: the current candidate
  has an earlier packaging/activation possibility where the expected producer
  or homescreen consumer is absent from the image metadata.
- The homescreen's declared Vulkan/transparent Wayland contract is compatible
  with the FLR-0019 presentation boundary, but does not prove runtime attach,
  commit, or screen pixels.

## UNKNOWN

- The authoritative production image/packagegroup that should contain the
  Fluorite demo and homescreen.
- Whether the current target rootfs was produced from this candidate image
  configuration or from a different historical image.
- Runtime service readiness, child-surface commits, and screen-pixel evidence.
