# FLR-0218 — trace swapchain image-index identity across readback and present

- Status: Done
- Priority: High
- Owner: Filament Vulkan swapchain identity role
- Created: 2026-09-20
- Predecessor: [FLR-0217](FLR-0217-trace-native-readback-payload-identity.md)

## Work unit

Expose the exact swapchain image identity used by the native readback and
correlate it with `vkQueuePresentKHR` image index, buffer attach, and QMP frame.
Keep the change observation-only until the mismatch is explained.

## Success criteria

- Reuse the fixed Podman/Devtool state, Mini receiver/build/TMPDIR, and one
  QEMU run.
- Produce bounded logs that name readback image identity and present image
  index for the same frame sequence.
- Decide whether the all-255 payload is a different image, a clear/placeholder,
  or a compositor-side mismatch.
- If source instrumentation is required, use source commit → official Devtool
  patch generation → layer commit → bundle → Mini gates.

## Facts inherited from FLR-0217

- Readback returns success on a swapchain target but payload is uniformly 255.
- Native-only QMP remains black while 2D HUD is visible.
- The current layer patch and build handoff flow is deterministic and passing.

## Facts

- The saved FLR-0218 correlation log SHA-256 is
  `da521ba5be52e94fc0903d5c3fa44460f1a9102d65edc5c082b599a7d57a74ec`.
- Runtime acquisition logged `swapchain-acquire index=0`, followed by
  `present index=0 result=0` on the same swapchain handle.
- Readback targeted `target_handle=236 swapchain=true extent=1280x800`, with
  source image/view and format/layout recorded; queue submit, fence wait,
  map, reshape, and cleanup all succeeded.
- The paired QMP frame SHA-256 is
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`;
  native ROI is uniformly black and HUD is visible.
- The current source statically binds the render target color attachment from
  `VulkanSwapChain::getCurrentColor()`, which reads `mCurrentSwapIndex`, but
  the readback marker does not print that index directly.
- The canonical layer already contains the prior source commit
  `1fd22efd9acd0b80c7bd2c670cf17e25fd796b8a` as patch `0269`; the Devtool
  workspace initially still advertised the older baseline
  `2990e692ea88b47c3dda61780a4ec08dd33cf7ec`.
- With the old baseline, official `update-recipe` regenerated the prior
  clipping patch as well as the new observation patch. With baseline `1fd22...`,
  official `update-recipe` generated only the two-file child patch from
  `f71d3a4b87f5b6122fe06d2e220cf045530752b3`.
- The generated patch was copied unchanged to canonical as
  `0270-diag-trace-current-swapchain-image-identity-devtool.patch`, SHA-256
  `0277b1a4ecfa9c762b5a45dff6da9853dac4cc7c074047b8c8683c7db2851c9f`, and
  registered once in the existing `filament-vk` bbappend.
- The first Mini compile failed at `VulkanSwapChain.cpp:117:55` because the
  observation used nonexistent `VulkanTexture::getImage()`; the pinned API is
  `getVkImage()`.
- The correction was source commit
  `9de434cc5f9a1a83afdeafb4e7ea73d2a0066e71` based on `f71d3a4...`.
  Re-registering official Devtool from `f71d3a4...` and running
  `update-recipe` generated only the one-line child patch
  `0271-diag-use-vulkan-image-accessor-devtool.patch`, SHA-256
  `742c0bd69b453dbcfcdfd7fd00850ce3ed15323d2240ae9703d14fe68d35c932`.
- Official `finish-source` selected exactly the `9de434c...` patch and the
  canonical bbappend registration passed. The generated patch was not edited.
- Bundle handoff of canonical commit `dbf2b2f26f678fd6acf2c87b0eafd71b2b0b697a`
  passed with SHA-256
  `dca6b39296e888839cf33b16cae013e1aa7a8d51d1e887b9eee4387dbc0634fb`.
- Mini patch gate passed at receiver tip `dbf2b2f26f678fd6acf2c87b0eafd71b2b0b697a`:
  `workdir-reset=PASS mode=recipe-clean`, `do_patch=PASS`.
- Mini compile rerun passed for `filament-vk-1.65.4-r0`; summary is at
  `/mnt/yocto/flourite-receivers/flr0023-835a04e/evidence/FLR-0218/filament-vk-do-compile-rerun.summary`
  and output SHA-256 is
  `d9eadd4d96bb0afdfea58427c4e6a646d405b9e18aaeb18a2e2dbd99ecd4536e`.
- Full `agl-ivi-image-flutter` build passed: 11,758 tasks attempted, 11,722
  reused, all tasks succeeded; output SHA-256 is
  `c4d9ac18ca0d682301906dbb98ca14aa7db187ad556b25e676d66ffb446b33ae`.
- The corrected runtime marker reported
  `FLUORITE_SWAPCHAIN_CURRENT_COLOR index=0 image=0x7f1ec04558b0` and both
  `FLR0026_TARGET_DRAW` and `FLR0026_TARGET_READBACK_SOURCE` reported the
  same `color_image=0x7f1ec04558b0`.
- Driver readback reported `bytes=4096000 nonzero_bytes=4096000`, and its
  native ROI reported `pixels=248000 nonzero_rgb=248000 nonzero_alpha=248000`
  with alpha min/max 255.
- QMP-only evidence: the native ROI `[300,250,620,400]` was uniformly black
  (`changed_pixels=0`, `chromatic_pixels=0`, luma `[0,0]`) while the HUD ROI
  remained visible (`changed_pixels=2976`, `chromatic_pixels=2801`). Eight
  frames at 0.25-second intervals had the same frame SHA-256
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- QEMU start, guest readiness, QMP quit, and residual cleanup all passed. The
  QMP screenshot is retained at
  `$EVIDENCE_ROOT/FLR-0218/q/flr0218-latest.ppm`.

## Hypotheses

1. Readback and present use different swapchain images.
2. Readback observes a cleared/placeholder image before presentation.
3. The compositor displays a different surface/image than the traced target.

The direct image identity observation falsified hypothesis 1 for this run.
Hypothesis 2 is inconsistent with the RGB-positive driver ROI. Hypothesis 3
remains the active boundary and is transferred to FLR-0219.

## Plan / Do / Check / Act

### Plan

Inspect current Filament Vulkan swapchain/readback source and add only the
smallest image-index/handle observation if existing markers are insufficient.

### Do

- Reused the fixed artifact, build, receiver, TMPDIR, and QEMU harness.
- Ran one native-only app with existing acquire/present/target/readback trace
  flags.
- Copied the bounded guest correlation log to the Mini evidence directory
  before teardown.
- Captured one QMP frame and performed exact guest/QMP teardown.
- Reused the fixed Podman container and source mount; no new machine,
  container, named volume, source tree, or TMPDIR was created.
- Committed the observation-only source change in the Devtool source Git
  before running official `update-recipe`.
- Re-registered the component from the latest canonical patch baseline
  `1fd22...`, generated the child patch from `f71d3a4...`, and completed the
  unchanged patch handoff into `meta-fluorite-trial`.

### Check

- PASS: acquire index and present index both equal `0`, with present result `0`.
- PASS: readback source is a swapchain target and all asynchronous stages
  succeed.
- PASS: QMP still shows 2D HUD and black native ROI; eight-frame capture is
  stable.
- PASS: current-color, draw, and readback all use the same swapchain image
  handle, while the driver ROI is RGB-positive.
- PASS: saved correlation log and QMP frame hashes are recorded.
- PASS: the direct current-color marker exposes the image index and handle, and
  it matches the draw/readback image handle.
- PASS: old-baseline regeneration was reproduced and the latest-baseline
  child-patch result was verified by source commit and patch SHA.
- FAIL then PASS: the first Mini compile caught the wrong accessor; the
  correction passed official Devtool generation as a one-line child patch.
- PASS: bundle handoff, Mini `do_patch`, and Mini `do_compile` passed for the
  corrected patch.

### Act

Close FLR-0218 as a completed image-identity diagnostic. FLR-0219 owns the
next boundary: why an RGB-positive native image remains absent from the final
QMP composition while the 2D HUD is visible. No composition or payload fix is
added to this ticket.

## Devtool baseline decision

The next Devtool operation must start from the latest effective source commit
recorded by the prior canonical patch, not from the original upstream/import
commit. This run proved the rule: stale baseline `2990e692...` regenerated an
old patch; `1fd22...` produced only the `f71d3a4...` child; and `f71d3a4...`
produced only the `9de434c...` one-line child. The deterministic unit is
`modify at baseline → source Git commit → update-recipe → finish → canonical
registration → next baseline lock`.

## UNKNOWN

- Whether the compositor imports the RGB-positive native buffer into the
  visible parent frame or selects another buffer/surface.
- Whether the final QMP/scanout path differs from the surface observed by the
  runtime trace.
