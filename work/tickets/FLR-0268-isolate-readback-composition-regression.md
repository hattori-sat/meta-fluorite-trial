# FLR-0268 — isolate readback-mode composition regression

- Status: Done
- Priority: High
- Owner: readback SHM mode / Flutter parent composition
- Created: 2026-09-24
- Predecessor: [FLR-0267](FLR-0267-fix-readback-shm-buffer-release.md)

## Objective

Determine why the FLR-0267 image produced a fully black QMP frame while the
FLR-0266 image retained the 2D HUD. Separate a regression caused by the
readback-mode implementation from a QMP timing/startup artifact before making
another source change.

## Facts

- FLR-0266 known-good QMP frame: `538854/1024000` changed pixels, full-frame
  SHA `2149fccddf4ce9a725333e416f6b4ba1e0f2bf83976ac4d9daa82361c8d02046`.
- FLR-0267 release/fresh-buffer QMP frames: ten identical full-black frames,
  full-frame SHA `d4e96a65fd4f8e97bc1d762fc90cf259bc2efb53a3125a72502fdae0f09395c`.
- FLR-0267 source logs prove two readback publishes and two `wl_buffer.release`
  events, so release starvation is not the remaining explanation.
- FLR-0267 source-side readback pixels were chromatic, but QMP did not show
  them or the 2D HUD.

## Hypotheses

1. The new readback-mode pool/buffer setup changes the visible SHM surface or
   damages the compositor state, causing the whole QMP frame to go black.
2. The frame capture happened before Flutter's parent surface became visible,
   and the full-black result is a startup/timing artifact.

## Verification plan

- On the same FLR-0267 image, run the SHM-only control
  `FLUORITE_NATIVE_VISIBLE_SHM_CUBE=1` without
  `FLUORITE_NATIVE_READBACK_TO_SHM`; retain QMP-only ten-frame evidence.
- Run the native/readback environment with a delayed capture after the release
  events, using the same image and one QEMU process.
- Compare full-frame and ROI hashes against FLR-0266 and record whether the
  2D HUD is restored before considering a source edit.

## Scope boundary

Do not change production scene, camera, light, native WSI, or Flutter route
code until the readback-mode versus timing boundary is proven.

## Runtime result

- The same FLR-0267 image was used for the SHM-only control.
- Ten QMP frames were captured; all shared SHA-256
  `90c2635cf8ed1e93eb159dbd38eb00c66a3041d5b481ce18361a33840d3359c3`.
- Full frame: `699050/1024000` changed pixels, `24178` chromatic pixels.
- Central ROI `(460,260,360,280)`: `100800/100800` changed pixels,
  `24178` chromatic pixels, geometry bounding box present.
- QMP quit and cleanup passed with no residual QEMU process.

## Conclusion

The SHM-only control proves that this image still renders simultaneous 2D and
self-made 3D. The readback-enabled run remains full black even after publish
and release events, so startup timing is not sufficient to explain the result.
The remaining boundary is the readback-mode Wayland protocol/composition path;
FLR-0269 owns that trace.
