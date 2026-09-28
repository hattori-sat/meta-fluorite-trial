# FLR-0193 — trace post-create native draw content

- Status: Waiting — direct swapchain readback is a separate next unit in
  [FLR-0194](FLR-0194-readback-direct-fixture-swapchain.md)
- Priority: High
- Owner: Mini QEMU runtime + Mac source analysis roles
- Created: 2026-09-15
- Predecessor: [FLR-0192](FLR-0192-defer-viewtarget-create-until-ecs-init.md)
- Working log: `work/logs/2026-09-15-flr0193.md`

## Work unit

Determine why the self-made native fixture remains black after ViewTarget
creation now succeeds. This is a runtime/source diagnosis unit; do not change
the production scene or lighting contract until the first zero boundary is
identified.

## Facts inherited from FLR-0192

- QMP shows the 2D HUD, but fixed 3D region `[300,250,620,400]` is uniform
  black (`0/248000` changed pixels).
- Runtime reaches ViewTarget creation and start with `count=1`.
- Vulkan queue submit and present return `0`; Wayland surface commit is also
  observed.
- Reuse the same fixed Mini image, build/TMPDIR, receiver, and QMP profile.
  Do not create another receiver, build directory, TMPDIR, or QEMU process.

## Hypotheses

1. **Native draw content is black — leading.** The fixture renderable reaches
   the frame path, but clear/material/viewport or shader output produces no
   non-black pixels.
2. **Valid native pixels are hidden downstream — secondary.** The surface is
   presented, but stacking, alpha, or target selection hides it from QMP.

## Initial evidence

- Static source inspection shows the fixture creates a native scene, vertex and
  index buffers, an unlit material instance, a renderable entity, and adds that
  entity to the native scene. The runtime contract reports
  `has_renderable=true`, `primitives=1`, `bound_material=true`, and
  `vertex_count=8 index_count=36`.
- The native fixture sets a `1280x800` viewport, switches the minimal-geometry
  view to opaque blend mode, applies a 60-degree vertical projection, and
  applies `lookAt((0,0,5),(0,0,0),(0,1,0))`.
- The bounded runtime marker chain is
  `DRAW_FRAME_BEGIN` → `BEGIN_FRAME_TRUE` → `RENDER_RETURN` → `END_FRAME`.
  The same run reports Vulkan queue-present result `0` and a Wayland commit.
- QMP remains the negative result: HUD `[200,100,400,250]` has 116 changed
  pixels while the fixed 3D region `[300,250,620,400]` has `0/248000`.

## FLR-0193 bounded runtime evidence

- Reused the fixed FLR-0192 image and QEMU run directory. The QMP-only
  after-launch frame is `frame-flr0193-after-probe.ppm`, SHA-256
  `b133eeb9e9e1fe49188d717d3649a3aba3ebaf006643eafafd1b215605c05147`.
- Target region `[300,250,620,400]` is uniformly black: `0/248000` changed
  pixels, luma `[0,0]`, chromatic pixels `0`.
- HUD region `[200,100,400,250]` remains present: 116 changed pixels and
  geometry indicator present.
- Runtime reports `FLR0026_TARGET_RENDER_PASS_BEGIN swapchain=true
  extent=1280x800`, `FLR0026_TARGET_DRAW2 swapchain=true index_count=36`,
  Vulkan queue-present `result=0`, and `FLR0026_COMMIT_DONE`.
- The existing `FLR0026_TARGET_PROBE` did not emit a result because its
  current condition intentionally requires `!rt->isSwapChain()` and an
  intermediate `R16G16B16A16_SFLOAT` target. This fixture renders directly
  into the swapchain (`color_format=44`).
- Evidence log SHA-256: `serial-flr0193-probe.log`
  `7f271a514753d4c33d41bf70ef2625fb2f07df36f3e7de39d11e877982f6740c`.

## Boundary decision

- **Fact:** ViewTarget creation, native geometry setup, Filament render-pass
  admission, `draw2`, submit, present, and Wayland commit all occur.
- **Fact:** QMP still shows no non-black pixels in the fixed 3D region.
- **UNKNOWN:** Whether the direct swapchain image contains non-zero native
  pixels before presentation. The existing probe cannot answer this branch.
- **Decision:** Waiting. FLR-0194 adds a fixture-gated public
  `Renderer::readPixels` diagnostic inside the valid beginFrame/render/endFrame
  window; it does not change production scene, lighting, or compositor policy.

## Success criteria

- [x] Record static source ownership for ViewTarget, DrawFrame, RenderPass,
  swapchain target, and Wayland commit in the current Devtool source and
  bounded runtime evidence.
- [x] Capture one bounded runtime slice with the first missing marker
  identified: direct swapchain content after `draw2` remains UNKNOWN.
- [x] Compare the available target trace with QMP pixels without reading the
  full raw log into the working context; direct swapchain readback remains
  UNKNOWN and is split into FLR-0194.
- [x] Decide the next action: a minimal fixture-only readback diagnostic, not a
  compositor visibility change.
- [x] Preserve QMP-only evidence and clean teardown (`qmp=PASS`,
  `residual_targets=0`, `residual_qmp=0`).

## Plan / Do / Check / Act

### Plan

Start with source and existing marker contracts, then run one explicit fixture
capture using the FLR-0192 image. Select the smallest diagnostic seam that
distinguishes draw-content black from downstream hiding.

### Do

Static and runtime boundary collection completed. No source patch or build was
started for this ticket.

### Check

The direct target trace proves draw admission and present, but the existing
intermediate-target probe was inapplicable. The QMP 3D region is still uniformly
black, while the HUD is non-black.

### Act

Create FLR-0194 for fixture-gated direct swapchain readback. If its readback is
non-zero while QMP remains black, create a separate surface/compositor ticket;
if it is zero, continue with native pipeline/content analysis.
