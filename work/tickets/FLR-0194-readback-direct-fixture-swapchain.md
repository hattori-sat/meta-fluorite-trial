# FLR-0194 — read back direct fixture swapchain pixels

- Status: Waiting — driver-completion payload tracing is tracked in
  [FLR-0198](FLR-0198-trace-vulkan-readback-payload.md)
- Priority: High
- Owner: Mac Devtool source + Mini authoritative build + QEMU runtime roles
- Created: 2026-09-15
- Predecessor: [FLR-0193](FLR-0193-trace-post-create-native-draw-content.md)
- Working log: `work/logs/2026-09-15-flr0193.md`

## Work unit

Measure the native pixels of the direct opaque fixture swapchain in the valid
Filament frame window. The diagnostic must be fixture-gated, use the public
`Renderer::readPixels` contract after `render()` and before `endFrame()`, and
not change production scene, lighting, alpha, or compositor behavior.

## Facts inherited

- FLR-0193 proved `draw2(index_count=36)` reaches a 1280×800 swapchain and
  Vulkan present returns `0`, but QMP's fixed 3D region remains uniformly black.
- The existing target probe only handles a non-swapchain floating-point
  intermediate target and therefore did not emit a result for this run.
- The public Filament contract permits swapchain `readPixels()` only between
  `beginFrame()` and `endFrame()`; `ViewTarget::DrawFrame` has that window.

## Hypotheses

1. **Native swapchain pixels are zero — leading.** The draw is admitted and
   submitted, but the fixture pipeline produces black/empty output.
2. **Native swapchain pixels are non-zero — secondary.** QMP black is then a
   downstream surface/Wayland/compositor visibility problem.

## Success criteria

- [ ] Add a fixture-gated readback diagnostic through Mac Devtool source,
  regenerate the official recipe patch without hand-editing its body, and
  commit the layer change locally.
- [ ] Mini `do_patch`, component compile, and image gates pass using the fixed
  build/TMPDIR and one bundle transfer.
- [ ] QMP-only evidence includes a pre/post frame and the bounded runtime
  readback result with non-zero-pixel count and hash.
- [ ] Compare readback and QMP results, choose native-content or compositor
  visibility as the next independently ticketed boundary, and tear QEMU down
  through QMP with zero residual targets.

## Plan / Do / Check / Act

### Plan

Edit only the existing Mac Devtool source workspace. Call public
`Renderer::readPixels` after native fixture `render()` and before `endFrame()`
when `FLUORITE_NATIVE_SWAPCHAIN_READBACK` is set. Log bounded pixel statistics
from the callback, then use the established Mac→bundle→Mini→QEMU flow.

### Do

Ticket opened after FLR-0193 established the direct-swapchain boundary. The
Mac Devtool source edit was committed as `d62ba72a9`. The deterministic helper
correction is committed as `b93dcfb`; the official generated patch was
registered and committed as `7c63e9e`. The patch SHA256 is
`e48ddabed0153b535677ea77bf339a45e9e06b66ddc55261a89d3dc8a33169db`.

### Check

Mac generation, bundle handoff, Mini do_patch, Mini do_compile, and full image
build passed after the callback API and complete-patch-history corrections. The
QMP frame shows the HUD and a uniformly black 3D candidate region. Vulkan
readback reaches queue submit, fence wait, map, reshape, work complete, and
cleanup, but the application callback result is not emitted; FLR-0198 owns the
driver-completion payload boundary.

### Act

If readback is non-zero and QMP is black, open a compositor/surface ticket. If
readback is zero, continue with native pipeline/content diagnosis.
