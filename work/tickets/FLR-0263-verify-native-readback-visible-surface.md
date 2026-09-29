# FLR-0263 — verify native readback reaches the visible surface

- Status: Done
- Priority: High
- Owner: native readback publication / Wayland visible-surface boundary
- Created: 2026-09-24
- Predecessor: [FLR-0262](FLR-0262-split-native-readback-from-qmp-composition.md)

## Objective

Use the existing `FLUORITE_NATIVE_READBACK_TO_SHM=1` runtime diagnostic to
determine whether the native readback buffer can be published into the visible
Wayland surface and appear in QMP.

## Facts

- FLR-0262 observed nonzero native readback for the full 1280×800 buffer while
  the paired QMP 3D ROI was completely black.
- The current source already has an environment-gated readback-to-SHM path.
- No source modification is justified before this A/B observation.

## Hypotheses

1. QMP becomes non-black when readback is published to SHM: the native draw is
   valid and the normal swapchain/Wayland handoff is stale or miswired.
2. QMP remains black: the readback buffer does not contain the intended 3D
   content, or the SHM publication path is also not visible.
3. QMP shows a shifted/scaled/non-production image: coordinate or format
   conversion is the remaining contract mismatch.

## Scope boundary

One no-input QEMU run with the existing verified image. Add only the existing
`FLUORITE_NATIVE_READBACK_TO_SHM=1` environment variable; do not patch source,
camera, material, lighting, or compositor behavior.

## Success criteria

- Ten QMP frames are captured and analyzed for non-black/chromatic content.
- Readback result and SHM publication markers are recorded.
- QMP quit and residual cleanup pass.
- The next source owner is selected from the A/B result.

## Result

- The same verified image ran one no-input QEMU with
  `FLUORITE_NATIVE_SWAPCHAIN_READBACK=1` and
  `FLUORITE_NATIVE_READBACK_TO_SHM=1`.
- Readback requests and results occurred. The SHM bridge published twice and
  skipped zero times. The initial extraction missed the published marker
  because its regular expression was too narrow; the corrected log shows
  `FLUORITE_NATIVE_READBACK_SHM_PUBLISHED=2` and
  `FLUORITE_NATIVE_READBACK_SHM_PUBLISH_SKIPPED=0`.
- Ten QMP frames were identical with SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- QMP ROI `[200,100,400,250]` remained completely black with zero chromatic
  pixels and luma `[0,0]`.
- QMP quit and cleanup passed with `residual_targets=0 residual_qmp=0`.

## Boundary decision

The A/B reached the expected SHM publication path twice, but the paired QMP
frame remained completely black. This supports a surface stacking, visible
surface identity, or QMP capture/compositor boundary problem. The earlier
patch-stack mismatch inference was withdrawn after correcting the log filter.
No product code change is justified by this observation alone.
