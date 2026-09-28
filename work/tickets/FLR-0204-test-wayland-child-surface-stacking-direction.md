# FLR-0204 — test Wayland child-surface stacking direction

- Status: Done
- Priority: High
- Owner: Mac source/runtime analysis + Mini authoritative build + QEMU runtime roles
- Created: 2026-09-19
- Predecessor: [FLR-0203](FLR-0203-isolate-wayland-child-surface-after-opaque-ab.md)
- Working log: `work/logs/2026-09-19-flr0204.md`

## Work unit

Determine whether the native Filament child surface is hidden by an invalid or
ineffective Wayland stacking relationship. Keep the current `place_above`
behavior as control and test only a gated `place_below` alternative.

## Facts

- FLR-0203 produced non-zero native driver ROI but zero QMP central and wide
  3D ROI.
- The commit/flush probe did not change the QMP frame; `wl_display_flush`
  returned 8 in the runtime log.
- Current `view_target.cc` uses `wl_subsurface_place_above(subsurface_,
  parent_surface_)` during setup.
- Historical working evidence FLR-0142 and other active plugin surfaces use a
  `place_below` path; exact equivalence to the current pure fixture is UNKNOWN.

## Inferences

- The first remaining source-owned composition discriminator is stacking
  direction, not Vulkan draw or swapchain opacity.
- A gated A/B keeps the control image and avoids making an unproven permanent
  compositor change.

## Hypotheses

1. H1: `place_above(subsurface_, parent_surface_)` is rejected, ignored, or
   produces a compositor ordering that hides the native child; `place_below`
   with the current HUD transparency exposes the native pixels.
2. H2: stacking direction is not causal; both paths remain QMP-black while the
   driver ROI stays non-zero, so the next boundary is compositor import,
   buffer-release, or Flutter parent-surface state.

## Success criteria

- [x] Record the control and alternative source operations before editing.
- [x] Generate the alternative only through the fixed Mac Podman Devtool and
  official `update-recipe` output.
- [x] Pass canonical registration, Mini `do_patch`, `do_compile`, full image,
  one QEMU runtime, QMP screen capture, and clean teardown.
- [x] Classify the central ROI from QMP; do not claim 3D success from driver
  readback alone.

## Plan / Do / Check / Act

### Plan

1. Compare current `place_above` with the historical and active `place_below`
   implementations.
2. Add an environment-gated `place_below` switch only if the comparison
   supports it.
3. Reuse the fixed source container, fixed Mini receiver/build/TMPDIR, and one
   QMP-only runtime loop.

### Do

The gated `place_below` source change was generated through the fixed Mac
Podman Devtool as official patch `0266` and registered once. Mini `do_patch`,
`do_compile`, full image, one QEMU run, QMP capture, and teardown passed.

### Check

The runtime marker was `FLUORITE_NATIVE_WAYLAND_STACKING below=true`. Driver
readback remained `nonzero_rgb=111758`, but QMP central
`[300,250,620,400]` and wide `[180,180,920,560]` ROIs were both zero. The
final frame SHA was identical to the control: `b133eeb9...c05147`.

### Act

The stacking alternative did not change QMP. Retain the official patch as
provenance, do not enable it by default, and continue with FLR-0205 for direct
client protocol and compositor import/release observation.

## UNKNOWN

- Whether the compositor accepts the current parent surface as the `sibling`
  argument to `place_above`.
- Whether the Flutter parent surface is opaque over the native child region.
- Whether `place_below` is sufficient without an explicit parent commit.
