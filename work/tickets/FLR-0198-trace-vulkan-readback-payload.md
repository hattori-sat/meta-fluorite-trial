# FLR-0198 — trace Vulkan readback payload at driver completion

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Mini authoritative build + QEMU runtime roles
- Created: 2026-09-16
- Predecessor: [FLR-0194](FLR-0194-readback-direct-fixture-swapchain.md)
- Working log: `work/logs/2026-09-16-flr0198.md`

## Work unit

Measure the bytes produced by the already-proven Vulkan readback at the driver
completion boundary, before deferred `scheduleDestroy` ownership prevents the
application callback from emitting its result. Keep the diagnostic gated by
`FLUORITE_NATIVE_SWAPCHAIN_READBACK` and do not change rendering behavior.

## Facts

- The FLR-0194 image built successfully at receiver revision
  `2dfaee6ae21a...`; rootfs SHA256 is
  `bde3cc8a063e2c9ad734c0611fbede0964f8615c7570fae96b95e5bd234ea0f3`.
- QMP post-launch frame SHA256 is
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- The 3D candidate region `[300,250,620,400]` is uniformly black: 0 changed
  pixels, 0 chromatic pixels, luma range `[0,0]`, 248000 black pixels.
- The HUD region is present: 116 changed pixels and luma range `[0,255]`.
- Runtime reaches `FLUORITE_NATIVE_SWAPCHAIN_READBACK_REQUEST`, Vulkan queue
  submit result 0, fence wait result 0, map result 0, reshape success, work
  complete, and cleanup end.
- `FLUORITE_NATIVE_SWAPCHAIN_READBACK_RESULT` is absent even after a delayed
  sample while `flutter-auto` remains alive.
- Static source shows Vulkan `readCompleteFunc` calls `scheduleDestroy` with the
  completed descriptor; the descriptor callback is therefore deferred beyond
  the observed single frame.
- QMP teardown passed with `residual_targets=0` and `residual_qmp=0`.

## Hypotheses

1. **Leading:** the readback payload is available at Vulkan driver completion,
   but the application callback is deferred by `scheduleDestroy` until a later
   driver cycle.
2. **Alternative:** the payload is empty/black at the driver boundary; direct
   driver statistics will show zero bytes or zero nonzero pixels.

## Success criteria

- [x] Modify the existing Mac Devtool `filament-vk` source workspace only, with
  a fixture-gated payload statistic at driver completion.
- [x] Generate the official filament-vk patch through Devtool, commit the
  layer, bundle it to the fixed Mini receiver, and pass do_patch/do_compile.
- [x] Build one fixed image and run one QMP-only QEMU session with bounded
  driver payload statistics and paired pre/post frames.
- [x] Decide native-content versus compositor visibility from the direct
  payload result, then tear down QEMU through QMP with zero residuals.

## Plan / Do / Check / Act

### Plan

Instrument the `readCompleteFunc` path immediately before deferred descriptor
destruction. Count nonzero bytes/pixels and record a bounded byte sum and max
byte, guarded by the existing readback environment variable.

### Do

The source commit is `608c1c4`. The official generated patch is registered in
the Filament recipe and has SHA256
`fd5a461664e95463b9f618d5a301ee5c16c399307de6ce89efc672fdeb9e9bf9`.
Mac do_patch, Mini do_patch/do_compile, full image build, QMP capture, and
QMP teardown passed. The 74 pre-existing deleted zero-byte tracked files were
restored from HEAD and are not part of the diagnostic patch.

### Check

The driver-completion marker reports
`bytes=4096000 nonzero_bytes=478864 checksum=1693330037`, while the QMP
3D candidate `[300,250,620,400]` remains uniformly black. The HUD remains
visible. This proves a non-zero total driver payload, but not non-zero payload
inside the 3D candidate ROI because the current statistic is total-buffer only.
QEMU was torn down through QMP with zero residuals.

### Act

The total payload is non-zero while QMP remains black, so FLR-0199 owns the
next ROI and native-surface/compositor split. No production rendering change
is justified yet.

## Result classification

- Facts: official Devtool patch generation, Mac/Mini gates, image build, QMP
  capture, driver completion, and teardown all passed.
- Inference: the first missing visible-pixel boundary is after the driver
  completion statistic, or the non-zero bytes are outside the 3D candidate.
- UNKNOWN: the driver statistic does not yet identify the 3D ROI; native child
  surface geometry, scale/viewport, alpha/opaque region, and compositor
  stacking are not yet correlated with this frame.
