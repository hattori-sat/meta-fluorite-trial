# FLR-0149 — trace Filament draw-to-target contract

- Status: Done
- Priority: High
- Owner: Filament Vulkan render-target + Wayland/QMP runtime roles
- Created: 2026-09-14
- Updated: 2026-09-14
- Depends on: [FLR-0148](FLR-0148-reconcile-effective-viewtarget-api-contract.md), [FLR-0062](FLR-0062-production-shaded-output-target-boundary.md)
- Working log: `work/logs/2026-09-14-flr0149.md`

## Work unit

Use the existing registered Filament diagnostics to map the native fixture
from a valid Renderable through `VulkanDriver::draw2`, render-pass execution,
the effective color target, and the Wayland/QMP display. This is a diagnostic
unit only: no rendering behavior is changed until the first failing boundary
is observed.

## Success criteria

- [x] One fixed-image runtime run enables only the existing draw/target and
  render-pass diagnostics; no second build directory, TMPDIR, container, or
  QEMU is created.
- [x] Runtime evidence explicitly records whether the native Renderable emits
  `draw2`, which target/extent/format receives it, and whether the render-pass
  execution seam returns.
- [x] QMP-only evidence is paired with the exact image identity and the native
  candidate-region result.
- [x] The first failing boundary is classified among draw admission, target
  contents/attachment, render-pass execution, or Wayland/QMP handoff.
- [x] QMP teardown leaves zero target processes and zero QMP sockets.

## Facts

- FLR-0148/commit `d3e077d` proved the active native diagnostic Scene,
  camera `(0,0,5)`, viewport `1280x800`, opaque View, parent/child surfaces,
  Renderable component, one primitive, bound material, vertex count 8, and
  index count 36.
- The same fixed-image runtime reached `beginFrame`, `render`, `endFrame`,
  queue-present, and child-surface commit, but its QMP native region
  `[300,250,620,400]` was uniform black: `0/248000`, no edge/chroma pixels,
  luma `[0,0]`.
- The current recipe already registers the environment-gated diagnostics
  `0172` (`draw2` target identity), `0173`/`0174`/`0175`/`0176` (target
  content/readback boundary), and `0187` (render-pass execute seam). The
  previous FLR-0148 command did not enable these switches, so their absence
  from that log is not evidence that draw2 or the target probe did not run.
- The authoritative 0244 image is paired with rootfs SHA-256
  `c2cb06be2c70bbd3c0c611f653b4fef5cf6e90fdc393982814bfd84f6f61bd18` and
  kernel SHA-256
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.

## Inferences

- The first unmeasured boundary is now below the valid Renderable contract
  and above the top-level QMP framebuffer. Enabling existing diagnostics is
  lower risk and more discriminating than another ViewTarget or camera patch.
- The existing target probe may not read the native swapchain because its
  filter accepts only a non-swapchain `1280x800` floating-point target; draw2
  and render-pass records are therefore required even when readback is absent.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: the valid native Renderable is never admitted to `draw2` | no fixture `draw2` record, or index/instance counts are absent/zero | one or more fixture `draw2` records with valid counts |
| H2: draw2 executes but targets an empty/invalid color attachment | draw2 exists but target identity/format/layout is absent, invalid, or target content remains zero before composition | target content/readback is nonzero or the target is a valid swapchain attachment |
| H3: target/render-pass output is valid but is lost after Filament | render-pass and target evidence is positive while QMP candidate remains black | target evidence is zero or render-pass seam does not complete |

## UNKNOWN

- Whether the native fixture reaches `VulkanDriver::draw2` on the current
  image.
- Whether the current native swapchain color image contains nonzero pixels
  before Wayland composition.
- Whether the existing non-swapchain target probe applies to this fixture.

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | self-made native 3D fixture draw and target contents |
| Where | Filament RenderPass/Vulkan target, native swapchain, Wayland child, QMP framebuffer |
| When | one bounded steady-state runtime window after fixture setup |
| Who | Filament Vulkan render-target, Wayland surface, and QMP evidence roles |
| How | existing environment-gated traces, one fixed-image QEMU, QMP-only capture |

## PDCA

### Plan

1. Reuse the completed 0244 image, fixed build/TMPDIR, receiver, and QEMU
   evidence directory.
2. Enable only the existing `draw2`, target, and render-pass trace switches
   in one root-console launch.
3. Capture one QMP-only screenshot and extract only decisive markers and
   hashes.
4. Select the next source change only if the first failing boundary is
   proven; generate it through Mac Devtool and validate it on Mini.

### Do

Ticket opened after FLR-0148 proved that Scene/View/Camera/Renderable/
Material/Buffer contracts are valid while native QMP pixels remain absent.
No source patch or second build has been made for this ticket.

### Check

Pending one bounded draw-to-target runtime observation.

### Act

Run the existing diagnostics on the fixed 0244 image. Preserve the QMP
screen, serial output, hashes, and negotiated teardown under the existing
receiver evidence root.

## Evidence

- Runtime evidence: `$RECEIVER/evidence/flr0149/qemu/`.
- Fixed image identity: recorded above and revalidated by the harness before
  QEMU start.

## Result — existing draw-to-target diagnostics (2026-09-14)

### Facts

- The fixed-image preflight, QEMU start, guest readiness, synchronized
  serial-exec, QMP-only capture, and negotiated teardown all passed. No second
  QEMU, build directory, TMPDIR, or container was created.
- The runtime emitted the native fixture draw as
  `FLR0026_TARGET_DRAW2 swapchain=true extent=1280x800 index_offset=0
  index_count=36 instances=1`, with a non-null color image and image view,
  color format `44`, and layout `9`.
- The render-pass execution seam returned for the fixture:
  `FLUORITE_SCENE_PASS_EXECUTE_BEGIN commands=1` followed by
  `FLUORITE_SCENE_PASS_EXECUTE_END commands=1`.
- Wayland child-surface creation, parent-relative placement, position, and
  commit were present, and queue-present returned `result=0`.
- QMP captured 1280x800, but `[300,250,620,400]` remained uniform black:
  `0/248000` changed pixels, zero edge/chroma pixels, luma `[0,0]`.
  The screenshot SHA-256 is
  `6c47f670b15233e360c878584a9cc8df8c93131d7b42d010fe8cc171a463895a`;
  the serial evidence SHA-256 is
  `ea1a6ca1e008736aaf4677d6f8a454c5e5406631a08aa975f27b6168b78941ef`.

### Inferences

- H1 is rejected: the valid native Renderable emitted a native `draw2` with
  the expected 36 indices and one instance.
- The target identity and format are valid at draw admission, so H2 is
  narrowed: target allocation is not missing, but target pixel contents are
  still unproven. The existing target-content probe intentionally excludes
  this swapchain target.
- H3 remains the active boundary: the next observation must read the native
  swapchain image before the Wayland/QMP handoff. A present return alone does
  not prove that the image contains geometry.

### Check / Act

- **Check:** draw admission and render-pass execution are PASS; native QMP
  pixels are FAIL; target pixel contents are UNKNOWN; teardown is PASS.
- **Act:** continue in FLR-0150 with a one-shot swapchain-image readback
  diagnostic generated through Mac Devtool. Do not alter camera, Scene,
  Renderable, present, or Wayland behavior until the readback result is known.

## PDCA checker

- Status: PASS
- Checked by: fixed Mini runqemu/QMP harness and bounded pixel analyzer
- Findings: the selected draw-to-target relationship is proven through
  RenderPass execution, while the first unmeasured boundary is swapchain image
  content before Wayland/QMP.
