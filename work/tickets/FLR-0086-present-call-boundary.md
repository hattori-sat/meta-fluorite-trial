# FLR-0086 — isolate the present-call completion boundary

- Status: Done
- Priority: High
- Owner: Filament Vulkan WSI + Wayland compositor boundary
- Created: 2026-09-11
- Depends on: [FLR-0084](FLR-0084-driver-thread-lifecycle.md)
- Working log: `work/logs/2026-09-11-flr0086.md`

## Work unit

Identify why the current image reaches Vulkan submit and
`VK_QUEUE_PRESENT_BEGIN` but does not reach present-boundary completion or
show native 3D pixels. Use a minimal official Mac Devtool patch and the fixed
Mini build/QEMU loop. This unit is diagnostic first; no production behavior
change is accepted without a QMP pixel improvement and a matching runtime
explanation.

## Success criteria

- Map the effective `VulkanSwapChain::present()` and platform swapchain path
  before editing.
- Compare the finished-drawing semaphore/llvmpipe wait hypothesis with the
  Wayland buffer-release/compositor hypothesis using runtime evidence.
- Edit the persistent Mac Devtool source and generate the official patch;
  register only the generated patch in `meta-fluorite-trial`.
- Reuse the fixed Mini receiver, build, TMPDIR, Podman container, and one-QEMU
  contract. Verify `do_patch`, component compile, and the full image before
  runtime.
- Capture QMP-only frames and prove either recognizable 3D pixels or the first
  remaining missing boundary. Preserve GDB/log evidence and clean QMP teardown.
- Use only new `FLUORITE_*` controls in this ticket. Historical `FLR0026_*`
  controls and paths are read-only provenance, not new experiment inputs.

## Facts

- FLR-0084 proved driver loop entry, driver creation, barrier release, queue
  wait entry/return, shape creation, frame begin/end, and two queue submits.
- The current run emitted one `VK_QUEUE_PRESENT_BEGIN` and no present-boundary
  completion marker.
- QMP showed a healthy 2D HUD and metrics but `0/223200` changed pixels in
  the native candidate region.
- A root GDB snapshot showed live engine/Vulkan activity waiting in
  llvmpipe/Vulkan condition-variable frames; the exact wait site is UNKNOWN.

## Inferences

- The first observed boundary is later than driver-thread startup and earlier
  than an accepted visible native frame.
- 2D Flutter composition and input are not the first failure for this run.

## Hypotheses

1. The finished-drawing semaphore or llvmpipe work does not complete before
   `vkQueuePresentKHR`. Prediction: a neutral before/after trace shows no
   return, and the thread remains in Vulkan/llvmpipe wait frames.
2. `vkQueuePresentKHR` returns, but Wayland buffer release or child-surface
   commit does not complete. Prediction: the call-return marker appears while
   Wayland commit/release markers or native pixels remain absent.
3. The present call completes and the output is only hidden by composition.
   Prediction: both call-return and boundary-complete markers appear while the
   QMP native candidate remains zero. This is lower priority because the
   current run lacks call-return evidence.

## UNKNOWN

- Exact semaphore handle/state and the symbolized llvmpipe operation holding
  the first present call.
- Whether a diagnostic-only wait/submit change can produce a visible fixture
  without altering the product contract.
- Whether the same boundary affects the production Sequoia scene and route
  transitions; that comparison remains separate until the fixture control is
  restored.

## Plan / Do / Check / Act

### Plan

Read the effective patched source and existing Yocto recipe order, then create
one opt-in neutral present trace through the persistent Mac Devtool source.
Hand off the generated patch via the fixed bundle flow, run progressive Mini
gates, and perform one explicit Example Demo launch with QMP evidence.

### Do

- Read-only runtime evidence and GDB state were collected in the preceding
  FLR-0084 run.
- The Mini post-`do_patch` source for the two present files was imported into
  the persistent Mac Devtool source as baseline commit `1a7512970` on branch
  `fluorite-present-boundary-baseline`. This is an import of existing recipe
  patches, not a new behavior change.
- Devtool source commits `a5fb01ef8` and `a32ed6409` added only the opt-in
  `FLUORITE_PRESENT_TRACE` markers around the upper present call and the
  `vkQueuePresentKHR` call.
- Official `devtool finish --mode patch` generated the two patches. The final
  recipe move failed because the original `/workspace/agl` layer is
  read-only; the generated patch files remained intact in the Devtool
  workspace and were copied without body changes into the project layer.
- Registered patches:
  `0182-diag-trace-Vulkan-present-call-boundary-devtool.patch` (SHA-256
  `ce3c8425091606d50471a88960c4f9df771e786b6bb966cd1ba487aa298808ab`) and
  `0183-diag-trace-Vulkan-queue-present-return-devtool.patch` (SHA-256
  `49db2b78d3f25b208a207989ff9a94eab334d23845a6cd8f8509575ffc750a98`).
- The Mac workspace recipe parsed successfully, but its bounded
  `recipe-task filament-vk do_patch` gate failed because the temporary
  split-component `externalsrc` recipe has no `do_patch` task. This is not
  evidence against the generated patch; authoritative `do_patch` remains the
  fixed Mini gate.

### Check

Source and layer checks pass. The fixed Mini `do_patch`, Filament compile, and
full image gates all passed before the runtime run. The Mac `do_patch` result
is recorded as a workspace-recipe limitation, not as a product/runtime
verdict.

The single QEMU run used the fixed harness revision
`e69f1364552dfe677fbc3c7050043e7172f6e761`. One `flutter-auto` process was
proven. The QMP-only early and late frames were 1280x800; the late frame
SHA-256 is
`16ccbabf47c6f5de8b47230e339bd090091a8923cfa377c105ec853fc2e97241`.
The native candidate `[300,80,620,360]` remained `0/223200` in both frames;
the HUD region `[200,100,400,250]` changed `1294/100000` early and
`1214/100000` late. Visual inspection shows the 2D HUD, CPU/GPU/Script
metrics, Scenes button, and lower controls, with a black native 3D area. A
16-frame QMP-only sequence was also retained.

The new marker counts were:

| Marker | Count |
| --- | ---: |
| `FLUORITE_VK_PRESENT_ENTER` | 1 |
| `FLUORITE_VK_PRESENT_FLUSH_DONE` | 1 |
| `FLUORITE_VK_PRESENT_CALL_BEGIN` | 1 |
| `FLUORITE_VK_QUEUE_PRESENT_ENTER` | 1 |
| `FLUORITE_VK_QUEUE_PRESENT_RETURN` | 0 |
| `FLUORITE_VK_PRESENT_CALL_RETURN` | 0 |
| `FLUORITE_VK_PRESENT_DONE` | 0 |

This identifies the first remaining boundary as the synchronous
`vkQueuePresentKHR` wait path after the queue-present entry. The Wayland
release/composition hypotheses are not reached in this run, so no product
fix is accepted here. QMP quit and cleanup passed with zero host target
processes and no QMP socket.

### Act

Split the next independent diagnostic into FLR-0088: identify the wait owner
and semaphore relationship inside `vkQueuePresentKHR` before changing
production present/semaphore behavior.
