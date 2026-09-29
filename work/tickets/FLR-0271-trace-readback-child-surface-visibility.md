# FLR-0271 — trace readback child-surface visibility in composed output

- Status: Done
- Priority: High
- Owner: readback child-surface visibility / compositor import
- Created: 2026-09-24
- Predecessor: [FLR-0270](FLR-0270-separate-readback-shm-pool.md)

## Objective

Identify the first boundary after a readback SHM buffer is populated and
accepted by Wayland but is absent from the QMP-composed framebuffer. The
diagnostic must distinguish surface ownership/stacking from buffer import or
QMP capture omission before changing product code.

## Facts inherited from FLR-0270

- The same image's SHM-only control displays 2D plus a self-made 3D cube.
- The separate-pool readback run initially keeps the full QMP frame stable and
  2D-visible for ten frames, but a later same-image run produces five
  consecutive full-black frames. The previous whole-frame blackout remains
  time-dependent and unresolved.
- Readback source pixels are `100800/100800` nonzero and chromatic for both
  slots. `wl_surface@43` receives attach, `360x280` damage, and commit, and
  both buffers receive release. No protocol error is recorded.
- The QMP ROI `(460,260,360,280)` remains `0/100800` changed and chromatic in
  all ten frames.

## Hypotheses and alternatives

1. The readback surface is accepted by the client protocol but is not in the
   compositor's visible surface tree or effective stacking order.
2. The surface is in the tree, but the compositor rejects or fails to import
   the SHM buffer contents without emitting a protocol error.
3. QMP's framebuffer capture omits that child surface even though the target
   display presents it; this must be tested against an independent target
   observation before changing code.

## Verification plan

- Reuse the exact FLR-0270 image and one QEMU instance.
- Capture bounded Wayland creation/parent/position/stacking and buffer import
  evidence, including the first creation of the readback surface, not only
  its later commits.
- Compare the readback child against the known-good SHM-only control in the
  same image and QMP profile.
- Require a first-divergence decision and QMP-only evidence. A log marker or
  source-side chromatic counter is not sufficient for visible 3D.

## Scope boundary

No production scene, camera, light, Flutter route, native Vulkan WSI, or patch
until one of the three hypotheses is evidenced. If a source change becomes
necessary, use the established Mac Podman Devtool source commit → official
patch generation → layer commit → Mini bundle flow.

## Visual evidence

The predecessor's QMP evidence is inherited only as a baseline. This ticket
requires a new QMP capture for its own acceptance gate. Run
`$EVIDENCE_ROOT/FLR-0271/0290-surface-create` captured five consecutive
full-black frames after the surface was created and readback was published;
all five had SHA prefix `d4e96a65fd4f` and `0/1024000` changed pixels.

## Closure — Run 0293 control evidence

The continuous pure-fixture control at
`$EVIDENCE_ROOT/FLR-0271/0293-native-fixture-crash-window` captured actual
QMP pixels for the self-made native cube and the 2D HUD in the same frame.
The native ROI had `100800/100800` changed pixels, `24178` chromatic pixels,
and edge bounds `[545,335,190,175]`; the HUD ROI had `2845` chromatic pixels.
The full-frame SHA for the first visible frame was
`c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`.

This falsifies QMP capture omission for the tested profile. The readback
child-surface/import boundary remains unresolved and is intentionally not
claimed as fixed here. One earlier fixture run crashed in llvmpipe while the
continuous run kept the visible frame; runtime stability remains a separate
unknown. FLR-0252 completed the production baseline and FLR-0272 now owns the
next production runtime boundary.
