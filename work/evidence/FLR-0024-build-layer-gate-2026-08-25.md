# FLR-0024 — r2 authoritative recipe-gate evidence

## Facts

- The mini PC materialized a separate AGL build directory from the pinned
  `aglsetup.sh` flow for `qemux86-64`, with `agl-demo`, `agl-devel`, and
  `agl-flutter` features.
- The imported clean worktree is revision
  `e36baf0b9cfabc4a7bd2927d3cc569b2fc8c209b` for the recipe gate; the later r3
  documentation handoff is revision `65fe1f54d9d8e6c245a59a8841f53ea55425bb0d`.
- `bitbake-layers show-layers` resolved the AGL layers, project
  `meta-fluorite-trial` at priority 90, and the external Vulkan layer.
- The target demo recipe parsed with 3337 recipes and zero errors.
- `bitbake -e` resolved
  `0016-filament_scene-minimal-3d-fixture-devtool.patch` in the active
  `SRC_URI`, the project layer in `FILESPATH`, and did not resolve the raw
  comparison patch.
- The target demo recipe `do_patch` completed successfully. BitBake attempted
  104 tasks and all succeeded; the post-task source contained the fixture
  calls and `flr0023_fixture_cube`.
- The generated candidate configuration's effective `DISTRO_FEATURES` did not
  contain `vulkan`.
- A temporary `bitbake -R` configuration containing only
  `DISTRO_FEATURES:append = " vulkan"` made `bitbake -e` resolve the feature.
  The extra configuration was not persisted in the build directory or source.

## Inferences

- The Devtool-generated patch is proven through parse, effective metadata, and
  recipe `do_patch`; the present gate is not a patch registration failure.
- Vulkan package/layer presence and a temporary feature override do not prove
  that the production candidate image selects Vulkan or presents pixels.
- The missing default feature activation is a separate build-configuration
  problem and must be fixed or explicitly configured before a Vulkan runtime
  claim is attributable.

## Hypotheses

1. If the production candidate is rebuilt with the project common include
   active, the effective feature and package graph will include Vulkan without
   changing the fixture source.
2. If the runtime remains black after that configuration gate is corrected,
   the remaining boundary is downstream of Dart/source creation: native ECS,
   frame completion, WSI, or Wayland child-surface composition.

## UNKNOWN

- The fixture recipe `do_compile` has not passed; an earlier bounded compile
  attempt spent its budget in native/compiler dependencies before reaching the
  target recipe.
- No current target image built from r2/r3 has been booted, so native entity,
  frame, child-surface, and screen-pixel acceptance remain unproven.
- The exact production homescreen configuration that consumes this candidate
  remains a runtime integration gate.
