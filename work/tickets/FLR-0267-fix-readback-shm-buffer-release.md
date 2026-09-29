# FLR-0267 — fix readback SHM buffer release ownership

- Status: Done
- Priority: High
- Owner: readback SHM buffer lifecycle / compositor import
- Created: 2026-09-24
- Predecessor: [FLR-0266](FLR-0266-fix-readback-shm-buffer-lifecycle.md)

## Objective

Make the native readback pixels visible through the existing SHM child surface
by fixing buffer ownership in the opt-in diagnostic bridge. Do not alter the
production scene, native WSI selection, or the known-good SHM control.

## Facts

- The same-image SHM control displays the self-made cube.
- The readback callback produces chromatic pixels and runs on the same thread
  as SHM setup/publish.
- The bridge reuses one `wl_buffer` for the initial control commit and the
  subsequent readback commits without an observed release event.
- QMP shows 2D but a black readback ROI in ten live frames.

## Hypotheses and options

1. Leading: reattaching a buffer before a compositor release causes the
   readback update to be ignored. Add explicit `wl_buffer.release` tracking and
   publish only with a released buffer, or allocate a fresh retained buffer.
2. Alternative: the buffer is released but the SHM pixel/alpha contract is
   rejected. Falsify this with a fresh-buffer control carrying the same bytes.

Choose the smallest opt-in change that preserves the buffer until release and
does not introduce a second source tree, volume, TMPDIR, or runtime process.

## Success criteria

- Source change is made in the persistent Mac Podman Devtool source, committed
  before official `finish-source`, and registered as an untouched generated
  patch in `meta-fluorite-trial`.
- Mini `do_patch`, `do_compile`, and full image build pass.
- QMP shows the readback ROI with nonzero chromatic pixels in a live ten-frame
  capture, while the 2D HUD remains visible.
- SHM-only control and native-only negative control remain recorded.
- QMP quit and residual-process cleanup pass.

## Scope boundary

No changes to model selection, camera/light setup, production scene routing,
native Vulkan WSI, or input routing belong in this ticket.

## Devtool provenance

- Persistent source baseline: `4832585059aed211966d71f95caf02229a2bb61c`.
- Source commit: `27099cff7f35ff32b32a0b22236f329bd4283688`.
- Official generated patch: `0281-flr0267-fix-readback-shm-buffer-release-devtool.patch`.
- Generated/canonical SHA-256:
  `c4cff0de9ca78cafb802b2f4f94a5b104757e0f0d751274f7ceeed19736818f9`.
- The source was re-registered as `fluorite-plugins` before
  `update-recipe --force-patch-refresh`; no patch body was hand-edited.

## Runtime result

- Mini `do_patch`: PASS.
- `flutter-auto do_compile`: PASS, 2686 attempted tasks, all succeeded.
- Full `agl-ivi-image-flutter` build: PASS, 11758 attempted tasks, all
  succeeded.
- Rootfs SHA-256:
  `4ed8648bf199d1e8d33098e3267776c19465b241516f44a231cbb4ab728b2fc7`.
- QMP run directory: `$BUILD_RECEIVER/evidence/FLR-0267/0286-readback-release`.
- The first attempt was stopped by QMP quit after its serial output was not
  persisted; the second attempt used `serial-exec` and saved bounded launch,
  delayed-slice, and stop logs.
- The delayed log proved two distinct readback buffers (`slot=0`, `slot=1`)
  and two Wayland release events (`slot=0`, `slot=1`), with source-side
  `100800/100800` chromatic pixels for both publishes.
- Ten QMP frames had identical full-frame SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf259bc2efb53a3125a72502fdae0f09395c`.
  The full frame was `0/1024000` changed and the readback ROI
  `(460,260,360,280)` was `0/100800` changed and `0` chromatic in every
  frame.
- The previous FLR-0266 known-good 2D frame had `538854/1024000` changed
  pixels and SHA-256
  `2149fccddf4ce9a725333e416f6b4ba1e0f2bf83976ac4d9daa82361c8d02046`.
- QMP quit and residual cleanup: PASS, `residual_targets=0 residual_qmp=0`.

## Conclusion

The release/fresh-buffer hypothesis is falsified as a sufficient fix. Buffer
ownership now behaves correctly at the protocol level, but the FLR-0267 image
also produced a fully black QMP frame, unlike the FLR-0266 2D baseline. The
readback-mode change may have introduced a separate whole-surface composition
regression; this is split to FLR-0268. No production WSI or scene conclusion
is claimed from this ticket.
