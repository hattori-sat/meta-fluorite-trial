# FLR-0083 — locate the current-image command-stream execution boundary

- Status: Done
- Priority: High
- Owner: Filament command-stream + Vulkan runtime roles
- Created: 2026-09-11
- Depends on: [FLR-0081](FLR-0081-current-image-minimal-geometry.md), [FLR-0042](FLR-0042-trace-render-frame-present-boundary.md)
- Working log: `work/logs/2026-09-11-flr0083.md`

## Work unit

Use the p16 current-image evidence to map the exact operation between
`FRenderer::endFrame()` enqueue, `CommandStream::execute()`, Vulkan driver
commit, and `vkQueuePresentKHR`. Compare the current 0208 patched source with
the historical visible-cube path before making any source change.

This is a source/runtime diagnosis unit. It must not turn the ready-fence,
force-render, or command trace switches into product behavior.

## Success criteria

- Identify the command-stream worker/dispatcher ownership and the expected
  execution path for `commit`, `createFenceR`, and `endFrame`.
- Explain why p16 has enqueue and frame markers but zero command-execution,
  queue-present, and commit-done markers even though those marker strings are
  in the binary.
- Compare at least two plausible boundaries: worker/dispatcher starvation and
  trace coverage/path mismatch.
- Select one minimal next observation or Devtool-generated source patch only
  after the static source evidence supports it.
- Do not claim a 3D fix until a QMP-visible current-image object is captured.

## Facts

- p15 and p16 use current 0208, skip production model/environment setup, and
  enable the known minimal eight-vertex geometry.
- p16 reaches `FRAME_BEGIN started=true` and repeated renderer/fence enqueue,
  but QMP candidate and HUD regions are both zero.
- The current binary contains command-execution, commit, and present marker
  strings, while p16 emits none of the execution/present markers.
- Historical FLR-0042 proves the older self-made cube path reached queue
  present, present boundary, commit, and QMP-visible pixels.
- The static Filament path is `FEngine::flush()` →
  `CommandBufferQueue::flush()` → driver-thread `FEngine::execute()` →
  `waitForCommands()` → `DriverApi::execute()` →
  `CommandStream::execute()` → command dispatch. Vulkan `commit()` then calls
  the swapchain `present()` path, whose command buffer submission calls
  `vkQueueSubmit` before `vkQueuePresentKHR`.
- The current layer registers the existing 0157/0158/0159 diagnostic patches.
  0158 provides queue flush/wait/engine-execute markers, while p16 enabled only
  the named command-execution trace and did not enable
  `FLR0026_COMMAND_QUEUE_TRACE`.
- The persistent Mac Devtool source tree is on the historical
  `devtool-baseline-flr0062` branch at `c67672054`; it is useful for read-only
  baseline context but is not the effective 0208 source. The effective current
  source must be reasoned from the registered layer patch order or refreshed
  through the official Devtool workflow before editing.
- p17 enabled only the existing `FLR0026_COMMAND_QUEUE_TRACE` in addition to
  p16's flags. It emitted 62 queue-flush markers but zero queue-wait,
  engine-execute, engine-execute-buffer, command-execute, queue-present, and
  commit-done markers.
- p17's QMP five-frame set was again byte-identical to p16, with native
  candidate `0/223200` and HUD `0/100000`. The queue/engine marker strings
  were present in the guest binary.

## Hypotheses

1. The command-stream worker is not draining the enqueued commands in the
   current image. Prediction: worker/dispatcher state or thread handoff stops
   before `CommandBase::execute`.
2. Commands execute through a dispatcher path not covered by the named trace.
   Prediction: the all-command trace or dispatcher ownership differs from the
   expected `CommandStream` path.
3. The current QMP surface is black despite successful present. Prediction:
   queue/present markers would still appear; p16 currently does not support
   this hypothesis.

## UNKNOWN

- The exact current command-stream owner/thread state and first blocked call.
- Whether a source change is needed or whether an existing runtime launch
  contract leaves the renderer worker unstarted.
- Whether the historical visible-cube image and current 0208 image use the
  same Filament worker configuration.

## Plan / Do / Check / Act

### Plan

Read the effective patch order and source around `CommandStream`, dispatcher
startup, `FRenderer::endFrame`, `VulkanDriver::commit`, and present. Compare
these with FLR-0042 and p16 markers. Keep the next runtime run bounded and
QMP-only.

### Do

Static source map completed in the existing Devtool source container. No source
file or layer patch was changed. The next bounded runtime observation is p17:
reuse the current image and add only `FLR0026_COMMAND_QUEUE_TRACE=1`.

### Check

- H1 is supported at the first observed boundary: producer-side
  `CommandBufferQueue::flush()` runs, but the driver-thread consumer does not
  produce even the `waitForCommands()` return marker.
- H2 is not supported as the primary explanation: the queue and engine trace
  strings are present in the binary, and the queue flush marker is emitted.
- H3 is falsified for p17: there is no queue/present marker from which a black
  successful-present result could be inferred.
- The current failure is therefore below Vulkan present and before
  `FEngine::execute()` consumes the queue. This remains a diagnosis, not a
  product fix.

### Act

Close this boundary unit and create FLR-0084 for a minimal driver-thread
lifecycle/queue-wait diagnostic. Refresh the Devtool source through the
official workflow before editing; keep the existing container, receiver,
build, TMPDIR, and QEMU harness.

## Visual evidence

- p17 evidence directory: `$QEMU_EVIDENCE_ROOT/flr0083/p17`.
- Five QMP frames shared SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`;
  native candidate `0/223200`; HUD `0/100000`.
- `runtime-markers-output.log` SHA-256:
  `57721df1ccd424a274cf506ced3afd97ea54d36ad3823cd2efb9482c8ff51c00`.
- `pixel-analysis.log` SHA-256:
  `810d2925f264e985e42e0528996ee9845aee609d1cf1cd364e0cb8217479663e`.
- `binary-queue-markers-output.log` SHA-256:
  `d237dbab95904c8c0fbc8033ede695aeb97aafc0e528a3d01db7b785c77f4fe7`.
- QMP quit accepted, cleanup reported residual process/socket counts of zero,
  and the final socket/process check was empty.
