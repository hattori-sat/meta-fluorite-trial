# FLR-0217 — trace native readback payload identity and timing

- Status: Done
- Priority: High
- Owner: Filament Vulkan readback / swapchain-buffer identity role
- Created: 2026-09-20
- Predecessor: [FLR-0216](FLR-0216-diagnostic-readback-visible-shm-bridge.md)

## Work unit

Determine why the native readback callback is uniform 255 while the native-only
QMP surface is black and earlier mapping evidence was RGB-positive. Correlate
the readback request, swapchain image index, mapped buffer identity, queue
completion, and QMP frame without changing composition behavior first.

## Success criteria

- Reuse the fixed Podman/Devtool state, Mini receiver/build/TMPDIR, and one
  QEMU harness run.
- Produce bounded evidence that ties one readback payload to one swapchain image
  and one `vkQueuePresentKHR` index.
- Distinguish placeholder/cleared readback from real rendered content.
- Preserve native-only, SHM-control, and QMP evidence separately.
- Only then create the smallest source patch, if required, using source commit →
  official `devtool update-recipe` → layer registration → bundle → Mini gates.

## Facts inherited from FLR-0216

- Self-made SHM cube and 2D HUD are visible in QMP.
- Native-only QMP ROI is black.
- The readback-to-SHM bridge changes QMP but transfers a uniform white payload.
- The current Devtool/layer/bundle/build flow is passing deterministically.

## Facts

- Existing runtime tracing identified the readback target as
  `target_handle=236 swapchain=true extent=1280x800 region=0,0 1280x800`.
- The target color image/view used format `44` and layout `9`; readback source
  image/view identity was logged and the readback queue submit, fence wait,
  memory map, reshape, and cleanup all returned success.
- The preceding native present logged `swapchain=0x... index=0 result=0`.
  The pointer values are retained only in the Mini evidence log; this ticket
  records the role-level identity rather than host-specific addresses.
- The driver readback payload was `4096000` bytes, all bytes non-zero, with all
  `248000` native-ROI pixels RGB-positive and alpha `255`.
- The paired QMP frame SHA-256 was
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`;
  native ROI was uniformly black and HUD was visible.

## Hypotheses

1. Readback is performed on a cleared or placeholder image before the rendered
   image reaches the presented WSI buffer.
2. Readback payload and present use different swapchain image identities.
3. The driver mapping evidence and callback evidence occur at different timing
   points and need an explicit fence/image-index correlation.

## Plan / Do / Check / Act

### Plan

Add observation only: correlate image index and bounded payload statistics with
queue submit/present and QMP. Do not modify composition until correlation is
complete.

### Do

- Reused the fixed FLR-0216 image, receiver, build, TMPDIR, and QMP harness.
- Enabled existing target/readback/synchronization trace flags only.
- Captured one native-only run, bounded marker output, and one QMP frame.
- Stopped the recorded guest PID and quit QEMU through QMP.

### Check

- PASS: readback target is a real swapchain render target and all asynchronous
  readback stages report success.
- PASS: the preceding present reports success.
- PASS: payload statistics and QMP evidence are retained together.
- PASS: teardown left zero QEMU/runqemu/flutter-auto processes and no QMP
  socket.
- INCOMPLETE: the exact swapchain image index used by `readPixels` is not
  directly correlated with the present index. The target handle and image
  pointer are not sufficient to prove image identity across frames.

### Act

Close this correlation unit and open FLR-0218 for direct swapchain image-index
identity tracing. No source patch was created in FLR-0217.

## UNKNOWN

- Exact swapchain image represented by the callback payload.
- Whether `renderer->readPixels` is synchronized with the same image index that
  `vkQueuePresentKHR` reports.
