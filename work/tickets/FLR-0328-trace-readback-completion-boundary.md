# FLR-0328 — trace native readback completion boundary

- Status: Done
- Priority: High
- Owner: Filament Vulkan readback queue / fence / callback roles
- Created: 2026-09-25
- Predecessor: [FLR-0326](FLR-0326-probe-production-fragment-target-boundary.md)
- Working log: `work/logs/2026-09-25-flr0328.md`

## Objective

Identify the first missing event after `VulkanDriver::readPixels()` records
the readback commands and before `FLUORITE_NATIVE_SWAPCHAIN_READBACK_DRIVER_RESULT`
or the application callback. Preserve the fixed-color production probe and
the same QMP/HUD acceptance contract. Do not change Light, camera, Scene
ownership, Wayland stacking, or production material behavior.

## Success criteria

- Static source inspection identifies the exact `mReadPixels.run()` completion,
  fence, command-queue, and `readCompleteFunc` seams in the active patch stack.
- If a source probe is required, it is edited in the persistent Mac Devtool
  workspace, committed in the source Git, and materialized through official
  Devtool flow; no generated patch is hand-edited.
- The canonical layer is committed and handed to Mini by one Git bundle.
- Mini `do_patch`, component compile, full image, and one QMP-first runtime
  pass with matching image identity.
- One bounded run records the first of: readback submission, fence completion,
  callback entry, payload bytes/ROI, or an explicit failure/timeout.
- The full QMP frame is saved before ROI analysis; teardown leaves zero target
  processes and zero QMP sockets.

## Facts / hypotheses / UNKNOWN

### Facts

- FLR-0326 reaches `FLR0026_VK_READBACK_DRIVER_ENTER`,
  `...COMMANDS_RECORDED`, and `...EXIT`.
- The fixed UNLIT replacement, Scene add, begin-frame, draw submit, and HUD
  are positive, while QMP native ROI remains `0/144000`.
- The active recipe registers the historical 0260 payload and 0261 ROI
  diagnostics, but their completion markers were absent in the bounded run.
- Static source mapping shows `VulkanReadPixels::run()` submits a separate
  readback command with a fence, posts `waitFenceFunc` to `TaskHandler`, and
  invokes `readCompleteFunc` only from `cleanPbdFunc` after fence completion.
- The fixed Mini image reached `FLR0026_VK_READBACK_QUEUE_SUBMIT result=0`,
  `FLR0026_VK_READBACK_TASK_POSTED`, and
  `FLR0026_VK_READBACK_FENCE_WAIT_BEGIN`; no fence result, map, reshape,
  work-complete, cleanup, driver result, or application callback marker
  appeared in the bounded interval.
- QMP full-frame evidence was captured before analysis. The native ROI
  `(440,220,400,360)` was uniform black (`0/144000` chromatic, luma
  `[0,0]`), while the HUD ROI was positive (`2845` chromatic).

### Hypotheses

1. The readback command is recorded but its completion callback is deferred or
   not drained by the driver queue. A queue/fence completion marker will be
   absent or delayed while the app remains alive.
2. The readback submission reaches the GPU but the fence/command completion
   path is not observed by the current frame loop. A bounded fence/result probe
   will distinguish this from callback scheduling.
3. The active image contains an older effective Filament patch stack than the
   layer metadata suggests. Effective source identity and one marker probe will
   falsify this before deeper runtime interpretation.

### UNKNOWN

- Whether any nonzero fragment payload exists at the native target before the
  missing completion event.
- Whether the historical FLR-0198 completion result is reproducible on the
  current source/image pair.
- Whether the Vulkan fence eventually signals, times out only under a bounded
  wait, or remains blocked because the submitted readback command cannot
  complete on the current llvmpipe image.

## Plan / PDCA

1. Read the active Filament source and patch order; map `readPixels()` through
   `mReadPixels.run`, queue execution, fence wait, callback, and destruction.
2. Compare the current image's effective marker set with FLR-0198 without
   starting a second QEMU or changing the production scene.
3. Add at most one bounded completion probe through Mac Devtool if static
   evidence leaves the first missing seam unresolved.
4. Transfer one layer commit by bundle, build progressively on Mini, and run
   one fixed-color QMP test with full-frame evidence.

## Result

- Static source inspection and one bounded runtime observation met the ticket
  gate without a source patch or a Light/camera/compositor change.
- The first missing event is after `FLR0026_VK_READBACK_FENCE_WAIT_BEGIN`
  and before `FLR0026_VK_READBACK_FENCE_WAIT result=...`. This falsifies the
  earlier narrower interpretation that only the deferred application callback
  was missing; the fence completion boundary must be tested first.
- QMP full-frame PPM:
  `/mnt/yocto/evidence/flr0328-0001/qemu/qmp-0328-readback-full.ppm`,
  SHA-256
  `b487abce3d0fc5d56b28777617ead2fae27e8c1bd7efd975dab05210736a9a85`.
- Bounded serial output:
  `/mnt/yocto/evidence/flr0328-0001/qemu/serial-0328-readback-completion.output`,
  SHA-256
  `40a216e8ab9fb0c49a5a17b88b75b039b47da4d7c0e290f007ce39790e1a5a7a`.
- QEMU teardown passed with `residual_targets=0` and `residual_qmp=0`.
- The attached colored Sequoia image remains valid static
  `HeadLights_Emission` texture evidence (SHA-256
  `3f74e0bbddf6938c09fc394687ce1c558b2139ad2fbdf7ee172872bcfb438c6a`),
  while FLR-0070 remains the independent historical QMP proof of a combined
  HUD and colored Sequoia frame.

The next ticket is FLR-0329, which will use the existing image and one
environment-only bounded fence timeout observation to distinguish a blocked
fence from a merely deferred callback.

## Stop conditions

- Do not add a Light, camera, texture, compositor, or route workaround while
  this completion boundary is unresolved.
- Do not treat the static `HeadLights_Emission` texture or a nonzero total
  readback statistic as proof of visible QMP 3D pixels.
