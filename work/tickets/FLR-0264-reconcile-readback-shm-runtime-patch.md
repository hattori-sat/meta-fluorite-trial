# FLR-0264 — reconcile published SHM surface with QMP pixels

- Status: Done
- Priority: High
- Owner: Wayland child-surface position/stacking / QMP capture boundary
- Created: 2026-09-24
- Predecessor: [FLR-0263](FLR-0263-verify-native-readback-visible-surface.md)

## Objective

Explain why the verified readback-to-SHM path publishes a child surface while
the paired QMP framebuffer remains completely black.

## Facts

- `flutter-auto_2.0.bbappend` lists
  `0270-diag-publish-native-readback-through-visible-shm-devtool.patch`.
- FLR-0263 enabled `FLUORITE_NATIVE_READBACK_TO_SHM=1`.
- The runtime emitted native readback results and
  `FLUORITE_NATIVE_READBACK_SHM_PUBLISHED=2` with zero skipped publications.
- QMP remained completely black across the full 1280×800 frame in the paired
  capture.
- The live Wayland trace in evidence `0283-runtime` showed the readback child
  surface on the expected parent and geometry: `wl_subsurface@33` was created
  for `wl_surface@35` under `wl_surface@14`, positioned at `(460,260)`, and
  placed above `wl_surface@39`.
- The same trace showed `wl_surface@35.attach(wl_buffer@37)`, damage of
  `360×280`, and commit twice, immediately around two
  `FLUORITE_NATIVE_READBACK_SHM_PUBLISHED` records. Each publication reported
  `100800/100800` nonzero and chromatic pixels with a positive flush result.
- Ten QMP frames captured while the relaunch was active showed the 2D surface
  (`538854/1024000` changed pixels, geometry indicator present), while the
  readback target ROI `(460,260,360,280)` stayed black in all frames.
- A same-image SHM-only control in `0284-shm-control` showed the existing
  self-made cube in all ten QMP frames: target ROI `100800/100800` changed,
  `24178` chromatic pixels, and visible three-face geometry. Frame SHA-256 was
  `90c2635cf8ed1e93eb159dbd38eb00c66a3041d5b481ce18361a33840d3359c3`.

## Hypotheses

1. The SHM child surface is committed but positioned outside the QMP-visible
   area or behind an opaque surface.
2. The child surface is attached to a different parent/stack than the QMP
   framebuffer being captured.
3. QMP capture timing or the QEMU display path omits the committed child
   surface even though Wayland accepted the flush.
4. The readback bridge republishes the existing SHM buffer without proving its
   Wayland buffer lifecycle/ownership, so the control buffer is visible but the
   readback update is not accepted or imported as a new compositor buffer.

## Scope boundary

Read-only source, patch, build-workdir, and runtime evidence comparison. Do
not change the recipe or product code until one hypothesis is evidenced.

## Check

- Parent, position, stacking, attach, damage, commit, and flush: PASS.
- Live-QMP correlation: PASS; 2D remains visible and the readback ROI remains
  black across ten frames.
- SHM compositor control: PASS in the same image and QEMU profile.
- QMP-only evidence limitation: FALSIFIED. The remaining failure is specific
  to the readback update path, not a global SHM or QMP display failure.

## Act

Close this boundary ticket. FLR-0266 owns the next narrow unit: prove the
readback SHM buffer lifecycle and callback ownership, then make the smallest
official Devtool-generated change that publishes a fresh or released buffer.
No product patch is inferred from this ticket alone.

## UNKNOWN

- Whether the first failing detail is reusing a busy `wl_buffer`, missing
  `wl_buffer.release` handling, or calling the Wayland client from the
  readback callback's thread.
- Whether the current callback's pixel format/alpha is independently accepted
  by the compositor; the source-side counters prove content but not import.
