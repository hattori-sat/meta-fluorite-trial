# FLR-0211 — reconcile visible SHM geometry and native WSI RGB

- Status: Done — geometry fixed; clipping discriminator falsified
- Priority: High
- Owner: Wayland subsurface geometry + native Vulkan WSI roles
- Created: 2026-09-20
- Predecessor: [FLR-0209](FLR-0209-visible-shm-cube-fallback.md)

## Goal

Use the FLR-0209 visible cube as the control while independently correcting
the child-surface position and restoring RGB pixels in the native Vulkan
surface. The final proof must remain QMP-only and must show a real Fluorite
native object together with the 2D HUD.

## Facts

- The SHM fallback is visible and stable in QMP: the observed child is
  `[0,0,360,280]` with three colored cube faces.
- The runtime log reports the requested child position as `left=460 top=260`,
  so the requested position and the QMP position disagree.
- The bounded `WAYLAND_DEBUG=client` trace shows the SHM child surface being
  created and committed, but its protocol request is
  `wl_subsurface@31.set_position(0, 0)`. The requested `(460,260)` was not
  sent on the wire.
- The source expression used `left_ + left_` and `top_ + top_`, reusing the
  member coordinates instead of the locally computed centered coordinates.
  This is the confirmed cause of the SHM geometry mismatch.
- After the 0268 patch, QMP observed the colored cube at `[460,260,360,280]`:
  all `100800` pixels changed, with `24178` chromatic pixels and edge box
  `[545,335,190,175]`.
- In the same QMP frame, the `Scenes` HUD region `[1120,0,160,80]` remained
  visible with `2976` changed pixels. The old cube region `[0,0,360,280]`
  had no chromatic pixels.
- Twelve QMP frames were byte-stable with frame SHA
  `830fd73a5eb8ca51798dc037add59fcb37c9e3b5c3082f4d515c487fa0ab0cf4`.
- The existing native Vulkan path reaches begin/render/end and present, but
  previous bounded gdb evidence found zero or alpha-only RGB in its live
  `memfd:mesa-shared` mappings.

## Hypotheses

1. **Confirmed false:** the child-surface position was not a compositor-relative
   geometry problem; the client sent `(0,0)` because of a source typo.
2. The native Vulkan WSI import path is still producing zero-RGB transfer
   buffers independently of SHM composition.
3. **Falsified by the Queue-Idle A/B:** the native render submission has not
   completed before present, so `vkQueuePresentKHR` hands off an incomplete
   image.

## Next action

Use the repaired `devtool-flr0213-baseline` as the parent for the first native
WSI source child edit. Follow the standard sequence: edit source, `git add .`,
`git commit`, official `devtool update-recipe`/`finish`, copy the untouched
patch into the canonical layer, then bundle to the Mini and run QMP proof.

## Plan / Do / Check / Act

### Plan

1. Reuse the already-built FLR-0209 image without a source change.
2. Capture bounded `WAYLAND_DEBUG=client` protocol evidence for the requested
   child position and commit order.
3. Compare the protocol request with the QMP pixel location before choosing a
   minimal Devtool patch.

### Do

- Completed the no-source-change protocol probe using the exact FLR-0209 image.
- Edited the fixed Devtool source by one line and committed it as
  `2c9d32cf6f66ebf88527d75e9c12789ab694a449`, with parent baseline
  `606018f75ce5e83d5c2225d87a018a61db2789b3`.
- Re-registered `fluorite-plugins` with the component-scoped Devtool flow and
  generated the official patch from that parent/source pair.
- Registered the byte-identical generated patch as `0268` in the existing
  `flutter-auto_2.0.bbappend`; generated patch SHA-256 is
  `1ca4b7e07eb6e1eb5bc8aa03e4644474c23942bf5c7f27bff3b04204b612bec8`.
- Recorded the failed 0-patch attempt: registering the already-committed
  source with `modify --no-extract` made that commit the initial revision, so
  `finish` correctly had no delta. The component-scoped re-registration fixed
  the baseline relationship without hand-authoring a patch.

### Check

- No-source-change QMP evidence is retained under the FLR-0211 geometry probe;
  the old image still shows the cube at `(0,0)`.
- The protocol trace is the authoritative proof of the old behavior: the
  client sent `set_position(0, 0)`.
- Mini `do_patch` passed, `flutter-auto:do_compile` passed all 2,686 attempted
  tasks, and the full image passed all 11,758 attempted tasks.
- Corrected-image QMP validation passed. The post-launch PPM SHA is
  `830fd73a5eb8ca51798dc037add59fcb37c9e3b5c3082f4d515c487fa0ab0cf4`.
- QMP teardown passed with zero residual `qemu-system-x86_64`, `runqemu`, and
  `flutter-auto` processes. The initial long-socket-path failure also left no
  residual QEMU process.
- Native WSI probe without a source change was run under the Mini evidence
  directory `evidence/FLR-0211/p`. Filament's direct swapchain probe reported
  `nonzero_pixels=111758`, `chromatic_pixels=111758`, and
  `byte_sum=71301604` before present. The paired QMP native region still
  contained only the visible SHM cube, and the HUD stayed visible.
- Queue-Idle A/B was run under `evidence/FLR-0211/i-queue-idle` with only
  `FLR0026_PRESENT_QUEUE_IDLE=1` added. The native probe remained
  `nonzero_rgb=111758`; QMP remained byte-identical at
  `830fd73a5eb8ca51798dc037add59fcb37c9e3b5c3082f4d515c487fa0ab0cf4`.
  The runtime logged `QUEUE_WAIT_IDLE result=0` followed by
  `QUEUE_PRESENT_RETURN result=0`, so queue completion was not the missing
  boundary. The A/B screenshot and selected runtime log hashes are recorded
  in the working log.
- A first A/B invocation failed before QEMU because its destination evidence
  directory was not created; the corrected invocation then stopped before
  QEMU on an incorrect expected rootfs hash. The actual fixed rootfs hash was
  re-read, the run was retried, and the final QMP teardown left zero target
  processes and no socket.
- Present-layout A/B under `evidence/FLR-0211/j-skip-layout` added only
  `FLR0026_SKIP_PRESENT_LAYOUT=1`. The direct native probe remained
  `nonzero_rgb=111758`, and the QMP frame remained byte-identical with the
  same SHM cube/HUD metrics. This falsifies the present-layout transition as
  the first missing boundary.
- Opaque-alpha A/B under `evidence/FLR-0211/k-opaque` added only
  `FLUORITE_NATIVE_OPAQUE_SWAPCHAIN=1`. Runtime selected
  `transparent=false ... selected=0x1`, but the direct native probe and QMP
  frame were unchanged. This falsifies the premultiplied-alpha contract as
  the sole cause.
- Native-only A/B under `evidence/FLR-0211/m-no-shm` omitted the SHM cube
  entirely. QMP still showed the HUD but the native ROI was uniformly black:
  `changed_pixels=0`, `chromatic_pixels=0`. This falsifies SHM-cube
  occlusion as the cause. The native surface itself remains the unresolved
  Wayland/WSI boundary.

### Act

- Keep the native Vulkan RGB path as the remaining boundary. Use the visible
  SHM cube and `Scenes` HUD as controls while tracing whether RGB is lost
  before or after native WSI import.

## Baseline handoff

- FLR-0213 restored a complete active Filament Devtool source baseline at
  `2990e692ea88b47c3dda61780a4ec08dd33cf7ec`.
- The fixed workspace append records that same `initial_rev`, and the official
  no-source-change `update-recipe` gate passed with zero generated patches.
- The old broken source branch remains only as an audit archive. Do not use it
  as the parent of a new WSI edit.
- The first native WSI child edit uses the repaired baseline and changes
  `VkSwapchainCreateInfoKHR.clipped` from `VK_TRUE` to `VK_FALSE` for a
  bounded Wayland-subsurface discriminator. Source commit is
  `1fd22efd9acd0b80c7bd2c670cf17e25fd796b8a`.
- Official Devtool update/finish produced exactly one untouched patch. It is
  registered in the canonical layer as `0269` with SHA-256
  `6392a5dbdde06d2cd6d38a8701ae543d30a68bdf753e8b4ad43fc2e4ba3f4805`.

## Iteration 7 — Mini/QMP clipping discriminator

### Facts

- The canonical commit `df50895` was transferred by the fixed Git bundle
  handoff. The receiver matched the tip; bundle SHA-256 was
  `4b7d893b390f229e05c04bb2fac23182201a5a2d6d455b097cf42c1762db76b2`.
- Mini `filament-vk` `do_patch` passed after the receiver update.
- Mini `flutter-auto:do_compile` passed all `2686/2686` tasks.
- Mini `agl-ivi-image-flutter` passed all `11758/11758` tasks. The tested
  rootfs SHA-256 is
  `c307730a9bd11b357290dcac617b8f634adc8554724432b2f649c15870d63f29`.
- The QEMU run reused the existing FLR-0211 `q` evidence directory, one QMP
  socket, and the installed Example Demo bundle as `agl-driver`.
- The QMP frame SHA-256 was
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
  Eight consecutive QMP frames had that same SHA; the frame-list SHA-256 is
  `153cefda7f52a7fc0227d9c7ab189f4d4d550f651c6096cd13a8d296d1c2a4d8`.

### Check

| ROI | QMP result | Meaning |
| --- | --- | --- |
| Native candidate `[300,250,620,400]` | `changed=0/248000`, chromatic `0` | native 3D is absent from the final framebuffer |
| SHM cube `[460,260,360,280]` | `changed=0/100800` | no colored 3D control was present in the final frame |
| HUD/Scenes `[1120,0,160,80]` | `changed=2976`, chromatic `2801` | 2D composition and app liveness are present |
| Old cube region `[0,0,360,280]` | grayscale HUD only | no hidden colored 3D object was found there |

The QMP screenshot is a black central 3D region with the `Fluorite Game
Engine` HUD and `Scenes` button. Direct native readback remained positive
before present (`nonzero_rgb=111758` in the same ROI), so changing
`VkSwapchainCreateInfoKHR.clipped` from `VK_TRUE` to `VK_FALSE` did not change
the native-to-QMP result.

### Act

- The clipping hypothesis is **falsified** and patch `0269` is no longer
  active in the recipe. Its historical Devtool-generated file remains in Git
  for provenance, following the existing obsolete-patch policy.
- QMP teardown passed; final Mini checks showed zero residual QEMU, runqemu,
  or flutter-auto processes and no QMP socket.
- The next independent work unit is
  [FLR-0214](FLR-0214-trace-wayland-wsi-buffer-transfer.md), which owns the
  post-present Wayland WSI buffer transfer/import boundary.

## UNKNOWN

- Whether the native WSI buffer is zero before import or loses RGB at import.
- Whether moving the SHM control to `(460,260)` will expose any additional
  native-surface occlusion or stacking issue.
- Whether the native `wl_shm` buffer contains RGB immediately after the
  Vulkan present call; the current direct swapchain probe does not yet sample
  that buffer in the successful Queue-Idle run.
- Whether the native surface is being imported by the compositor with the
  expected buffer contents despite the successful Vulkan present return.

The remaining UNKNOWN is whether RGB is lost while the Vulkan WSI buffer is
exported/imported by Mesa/Wayland or while the compositor imports the native
surface. The next ticket must identify that owner before creating another
source patch.
