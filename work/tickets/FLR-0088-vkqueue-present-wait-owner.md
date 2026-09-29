# FLR-0088 — identify the vkQueuePresentKHR wait owner

- Status: Done
- Priority: High
- Owner: Filament Vulkan queue-present / llvmpipe WSI boundary
- Created: 2026-09-11
- Depends on: [FLR-0086](FLR-0086-present-call-boundary.md)
- Working log: `work/logs/2026-09-11-flr0088.md`

## Work unit

Identify which semaphore, queue submission, or llvmpipe/WSI wait prevents
`vkQueuePresentKHR` from returning. This unit is evidence-only first. Do not
change production present behavior until the blocked operation and its
expected signal source are proven.

## Success criteria

- Map the effective `vkQueueSubmit` signal semaphore to the
  `vkQueuePresentKHR` wait semaphore in the post-`do_patch` source.
- Capture one bounded live GDB backtrace and, if available, a narrow syscall
  trace while the process is inside the present wait.
- Distinguish an unsignaled application semaphore from a llvmpipe/WSI internal
  condition wait and from a Wayland-after-present issue.
- Keep the fixed Mac Devtool → patch → bundle → Mini build contract ready for
  the smallest subsequent diagnostic patch, but do not create that patch until
  the evidence selects the seam.
- End QEMU through QMP and preserve a QMP-only screenshot plus the bounded
  runtime log.

## Facts

- FLR-0086 reached `FLUORITE_VK_QUEUE_PRESENT_ENTER` and never reached its
  return marker.
- The same run displayed the 2D HUD while the native 3D candidate remained
  `0/223200` pixels.
- The current image uses llvmpipe Vulkan on qemux86-64.
- The corrected Devtool patch was applied by the authoritative Mini gates:
  metadata, `do_patch`, `do_compile`, and the full
  `agl-ivi-image-flutter` image build all passed.
- In the corrected runtime, `vkQueueSubmit` returned `result=0` with signal
  semaphore `0x7f3048025840`, and both `FLUORITE_VK_PRESENT_CALL_BEGIN` and
  `FLUORITE_VK_QUEUE_PRESENT_ENTER` used that same semaphore handle.
- The QMP screenshot showed the 2D HUD and controls, but the native 3D region
  remained unchanged: `changed_pixels=0`, `changed_ratio=0.0`.
- Sixteen QMP video frames were captured; all had the same SHA-256, so the
  black native region was stable during the bounded sample.

## Inferences

- The next useful observation is the blocked thread's symbolized stack and the
  handle relationship immediately before `vkQueuePresentKHR`, not another
  blind compositor or light patch.
- The wait owner is the application-created completed-drawing semaphore passed
  through submit and present; a wrong-semaphore mapping is not supported by
  this run.
- The same-handle/result-success evidence does not prove that the semaphore
  was signaled at the point of present, nor does it prove that native 3D
  commands reached the display surface.

## Hypotheses

1. The finished-drawing semaphore submitted before present is never signaled.
2. llvmpipe blocks while converting the Vulkan present to a WSI operation.
3. The call returns but the new trace is not at the true return boundary.

The corrected run weakens the handle-mismatch form of hypothesis 1, but does
not distinguish semaphore completion from a later llvmpipe/WSI wait.

## UNKNOWN

- The semaphore's signaled state and the first blocking symbol.
- Whether a fixture-only scene can reach the same wait with fewer resources.
- Whether the native command stream produced any pixels before the present
  wait.

## Plan / Do / Check / Act

### Plan

Read the effective patched source and runtime logs, then run one bounded
debugger/syscall observation on the fixed image before editing source.

### Do

Static source mapping is complete. `VulkanCommandBuffer::submit()` signals
the semaphore returned by `CommandBufferPool::flush()`, and
`VulkanSwapChain::present()` passes that same completed-drawing semaphore to
the platform swapchain. `VulkanPlatformSurfaceSwapChain::present()` places it
in `VkPresentInfoKHR.pWaitSemaphores` before `vkQueuePresentKHR`.

A bounded GDB sample was captured on the fixed image. The process contained
`FEngine::loop` and llvmpipe worker threads in condition-variable waits; the
guest also emitted a kernel page-fault/Oops around `FEngine::loop`. The exact
relationship between that Oops and the process lifetime is UNKNOWN, so this
is retained as evidence rather than treated as the root cause.

The first source edit was found in a stale Devtool attic copy and was rejected
as patch input. The active source was then committed through the persistent
Mac Devtool Git as `16e8c5db`, re-registered from baseline `28b98a4f`, and
processed with official `devtool update-recipe --mode patch --append
--no-remove --force-patch-refresh`. The generated patch is registered as
`0184-diag-trace-submit-present-semaphore-ownership-devtool.patch`.

That first candidate was rejected by the authoritative Mini `do_patch`: it
repeated the existing `0182/0183` present-boundary changes. The source was
rebased onto effective baseline `65d9b9e` and re-edited through the active
Devtool source. The corrected Devtool source commit is `b88d603322`; it adds
only submit signal markers and the present wait-handle field.

### Check

Canonical guard and `git diff --check` pass. The first candidate was rejected
by Mini `do_patch` because it repeated existing present-boundary hunks. The
corrected generated patch is byte-identical to the layer copy with SHA-256
`5ef6c01e85464faf760d16cc9654091614a0b79297c2a75e0bc47c7b9b81ed29`.

The corrected bundle reached the fixed receiver at tip `224c5aa9`; Mini
metadata, `do_patch`, `do_compile`, and the full image gate passed. The first
QEMU attempt used an unsupported VMDK input and was stopped by QMP; it is
recorded as a runqemu input-selection failure, not a product result. The
second attempt used the generated ext4 rootfs and passed preflight, start,
guest-ready, and serial-login.

The corrected QMP screenshot is stored under the fixed evidence root as
`qmp-corrected/qmp-present-trace-corrected.ppm`, SHA-256
`06eed30c8975456fd9d7620ab40fa8a4234a6df540e912241607bbcb434746af`.
Its native region analysis is `changed_pixels=0`; the HUD analysis is
`changed_pixels=1232`. The video sample contains 16 frames with identical
SHA-256. Runtime markers counted two submit begin/return pairs, one present
call, one queue-present entry, and zero queue-present return markers.
QMP teardown reported `cleanup=PASS residual_targets=0 residual_qmp=0`.

### Act

This evidence boundary is closed. Do not change present behavior in this
ticket. The unresolved semaphore-completion/llvmpipe/3D-command question is
split into [FLR-0089](FLR-0089-semaphore-completion-and-native-pixels.md).
