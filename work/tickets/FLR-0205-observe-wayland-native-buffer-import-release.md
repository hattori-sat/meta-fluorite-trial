# FLR-0205 — observe Wayland native buffer import and release

- Status: Done
- Priority: High
- Owner: Runtime protocol/compositor analysis + QEMU evidence roles
- Created: 2026-09-19
- Predecessor: [FLR-0204](FLR-0204-test-wayland-child-surface-stacking-direction.md)
- Working log: `work/logs/2026-09-19-flr0205.md`

## Work unit

Observe the Wayland client protocol and compositor journal around the native
Filament surface without changing source. The goal is to identify whether the
non-zero native driver buffer is attached/presented, imported by the compositor,
released, and included in the parent frame.

## Facts

- FLR-0203 commit/flush did not change QMP and logged `wl_display_flush=8`.
- FLR-0204 `place_below` did not change QMP; control and alternative frame SHA
  were identical.
- Both runs reported non-zero native driver ROI and successful Vulkan queue
  present.
- QMP remains the acceptance evidence; driver readback alone is not 3D
  visibility.

## Inferences

- The next efficient observation is protocol/compositor state, not another
  render-source patch.
- `WAYLAND_DEBUG=client` can prove client-side attach/commit/feedback traffic;
  the guest compositor journal can reveal protocol errors or buffer import
  failures.

## Hypotheses

1. H1: the client sends no valid buffer attach/commit for the native child, or
   the WSI buffer is released before compositor import.
2. H2: the compositor imports and composites the child, but the Flutter parent
   frame or surface role prevents the pixels from reaching QMP.

## Success criteria

- [x] Run exactly one QEMU session from the existing FLR-0204 image without a
  source or layer change.
- [x] Save bounded client protocol evidence and compositor journal evidence.
- [x] Capture QMP screen/video and classify central and wide 3D ROIs.
- [x] Stop the app and QMP-quit with zero residual targets.

## Plan / Do / Check / Act

### Plan

1. Reuse the fixed image and runqemu harness.
2. Launch one fixture with `WAYLAND_DEBUG=client` and no stacking override.
3. Filter only native surface, buffer, callback, error, and compositor lines.

### Do

One runtime used `WAYLAND_DEBUG=client` and the existing FLR-0204 image. The
client log proves native `wl_surface@39` attaches `wl_buffer@58`, damages the
full surface, requests a frame callback, and commits. The AGL compositor
journal has no matching protocol/import error.

### Check

QMP final SHA is `b133eeb9...c05147`; central `[300,250,620,400]` and wide
`[180,180,920,560]` ROIs both have zero changed pixels. The client journal,
compositor journal, PPM, and three video frames are retained under the fixed
receiver evidence directory. Teardown reports zero residual targets and QMP.

### Act

Client-side protocol and Vulkan present are positive, while QMP remains black
and compositor logs are silent. The next boundary is split to FLR-0206, which
observes the contents of the `wl_shm` buffer itself.

## UNKNOWN

- Whether the Vulkan Wayland WSI emits protocol traffic through the same
  connection visible to `WAYLAND_DEBUG=client`.
- Whether the guest compositor exposes import/release diagnostics in its
  journal at the current log level.
