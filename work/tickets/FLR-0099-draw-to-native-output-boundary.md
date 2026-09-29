# FLR-0099 — isolate the recovered draw-to-native-output boundary

- Status: Done
- Priority: High
- Owner: Fluorite runtime evidence / draw-target and native-output boundary
- Created: 2026-09-12
- Depends on: [FLR-0098](FLR-0098-current-image-frame-skip-ab.md)
- Working log: `work/logs/2026-09-12-flr0099.md`

## Work unit

Determine why the current production image remains native-black after the
existing frame-skip control recovers `beginFrame`, `endFrame`, draw-target
setup, and renderer commit enqueue. Compare the positive fixture and the
recovered production path at the boundary between effective draw commands,
the swapchain/native target, and the visible native surface.

This ticket is evidence-first. It must not assume that a successful
`TARGET_DRAW2`, submit, or present marker implies visible pixels.

The current work uses only the canonical repository, fixed Mini receiver,
fixed build/TMPDIR, and neutral ticket/evidence names. Historical `FLR0026`
markers in the existing image are read-only instrumentation; no new directory,
receiver, TMPDIR, control, or marker under that namespace may be created.

## Success criteria

- Static inspection maps `TARGET_DRAW2` target identity, active render target,
  frame/render list, and native-surface handoff to the actual source seams and
  patch order.
- One bounded recovered-production run and one fixture comparison reuse the
  fixed image, one QEMU at a time, one QMP socket, and QMP-only visual evidence.
- The first divergence among effective native draw, swapchain target, queue
  submit/present, and visible native surface is identified, or the exact gap
  is recorded as `UNKNOWN`.
- The result distinguishes a draw-content problem from a surface/composition
  problem. No source patch is proposed from a marker alone.
- QMP teardown, residual checks, selected logs, hashes, and failed invocation
  evidence are recorded.

## Out of scope

- No source patch or image rebuild until the first missing boundary is proven.
- No synchronization, present, Wayland, alpha, light, or material fix by
  assumption.
- No second concurrent QEMU, new TMPDIR, new receiver, cache deletion, or
  global kill.

## Facts

- FLR-0098 normal production control has no effective draw-target marker after
  repeated frame-start timeouts.
- FLR-0098 recovered production has `FRAME_BEGIN started=true`, 25
  `TARGET_DRAW2` records, renderer commit enqueue, and successful pipeline
  creation, but native region `0/223200`.
- The fixture reaches native draw/submit/present and changes `41750/223200`
  native pixels under the same fixed image.
- The recovered production selected output includes offscreen targets and a
  `swapchain=true` `1280x800` target, but does not yet prove that the production
  scene content affects the visible native candidate region.
- In the paired FLR-0099 run, the fixture produced 20 `TARGET_DRAW2` records
  for the visible `swapchain=true`, `1280x800`, `index_count=36` target and
  reached `FLUORITE_VK_QUEUE_PRESENT_RETURN result=0`, outer present return,
  and present completion. Its late native region changed `41,750/223,200`
  pixels.
- In the same paired run, production produced 25 `TARGET_DRAW2` records,
  including offscreen `1024x1024` targets and a final visible
  `swapchain=true`, `1280x800`, `index_count=3` target. It reached
  `FLUORITE_VK_QUEUE_PRESENT_ENTER wait=true`, but no queue-present return,
  outer present return, or present-done marker appeared. Its late native
  region remained `0/223,200`, while the HUD region changed `984/100,000`
  pixels.

## Inferences

- The next useful cut is target/content identity, not another fence/present
  timing change.
- A draw-target marker with a valid extent can still represent a fullscreen,
  offscreen, or non-production-content operation; target identity and content
  correlation are required.
- The production native-black result is downstream of the first visible
  target draw record in this run: the queue-present call does not return while
  the positive fixture returns through the same boundary.

## Hypotheses

1. Production draw commands target an offscreen or non-visible render target.
   Prediction: draw markers are present, but swapchain/native target identity
   or visible-surface commit differs from the fixture.
2. Production reaches the visible swapchain but renders no effective scene
   primitives. Prediction: swapchain draw exists, but render-list/content
   markers differ before submit.
3. Production native content is submitted but the visible surface handoff is
   stale or hidden by composition. Prediction: target/content/submit/present
   markers match, but native QMP pixels remain zero.
4. The bounded marker set is insufficient. Prediction: fixture and production
   marker sequences cannot be distinguished despite different pixels; a
   small neutral Devtool observation patch becomes a separate ticket.

## UNKNOWN

- Which `TARGET_DRAW2` records correspond to the production scene versus
  internal/offscreen work.
- Whether the recovered production path reaches a native surface commit after
  the visible swapchain draw.
- Whether target/content identity alone explains the zero native region.
- Which production submission, semaphore wait, or software-Vulkan operation
  owns the non-returning `vkQueuePresentKHR` call. The current markers identify
  the boundary but not the blocked thread or kernel wait.

## Plan / Do / Check / Act

### Plan

1. Inspect `TARGET_DRAW2`, render-list, frame, and surface-handoff source hooks
   and effective patch order.
2. Reuse the current ready condition for one production run and compare it with
   the fixture at the same post-pipeline markers.
3. Correlate target identity/content with QMP native pixels and classify the
   first divergence.
4. Open a separate Mac Devtool source-change ticket only if a controllable
   seam is proven.

### Do

1. Inspected the effective Toyota and Filament patch order. `TARGET_DRAW2`
   is emitted from `VulkanDriver::draw2`; outer present markers surround
   `VulkanSwapChain::present`; queue-present markers surround
   `VulkanPlatformSurfaceSwapChain::present` and the `vkQueuePresentKHR` call.
2. Reused the fixed authoritative image, build/TMPDIR, fixed receiver, and
   one short QMP run alias. The fixture and recovered production cases used
   the same image, QMP regions, bounded waits, and neutral lifecycle,
   submit/present, fence, and pipeline-input controls. The only case-specific
   functional difference was the fixture control versus the existing
   unlinked-fence-ready production recovery condition.
3. Captured QMP before/early/late frames and six-frame QMP videos for both
   cases, extracted selected guest markers, and recorded the single
   `flutter-auto`/compositor process state.
4. Stopped each QEMU through negotiated QMP `quit`; both cases passed the
   residual target and socket checks.

### Check

- Both cases passed preflight, start, guest-ready, serial launch/extraction,
  QMP capture, QMP video, and QMP teardown.
- Fixture: the late native candidate region `[300,80,620,360]` changed
  `41,750/223,200` pixels with bounding box `[501,278,278,162]`. The ordered
  trace reached visible swapchain draw, queue-present return `result=0`,
  outer present return, and present completion. Its six QMP video frames were
  not byte-identical, consistent with an active rendered fixture.
- Production: the late native candidate region stayed `0/223,200`; the HUD
  changed `984/100,000` pixels with bounding box `[200,113,29,66]`. The trace
  reached valid scene/resource state, frame begin/end, offscreen draws, a
  visible swapchain target draw, and submit, but stopped at the queue-present
  call. Its six QMP video frames were byte-identical, matching a stable
  HUD-only output.
- The first observed divergence is therefore `vkQueuePresentKHR` return:
  fixture returns `0`; recovered production has enter but no return. This
  distinguishes the current boundary from a purely missing draw-target
  record. It does not yet identify the blocked wait owner or prove the final
  3D root cause.
- Full artifact paths, hashes, marker counts, and pixel statistics are in the
  evidence manifest.

### Act

Close this evidence unit as Done. Do not treat `TARGET_DRAW2`, submit, or
present-enter alone as visible-pixel proof. Split the blocked present-return
execution analysis into FLR-0100; use runtime backtraces and syscall timing
before proposing a source patch.

## Visual evidence

The QMP-only before/early/late frames and six-frame videos for both cases are
listed with hashes and pixel-region analysis in the evidence manifest.
Not started.
