# FLR-0091 — isolate first unfinished Vulkan command

- Status: Done
- Priority: High
- Owner: Filament command stream / llvmpipe execution boundary
- Created: 2026-09-12
- Depends on: [FLR-0090](FLR-0090-fence-completion-boundary.md)
- Working log: `work/logs/2026-09-12-flr0091.md`

## Work unit

Determine which submitted command, render pass, shader/resource operation, or
scene stage prevents llvmpipe from signaling the Vulkan fence. Compare the
self-made fixture and production scene only after the common command boundary
is measured. Do not skip synchronization or change present behavior as a
diagnostic shortcut.

## Success criteria

- Capture a bounded command-stream or driver trace that identifies the first
  unfinished operation before fence signaling.
- Correlate the operation with the existing submit/fence markers and QMP
  native/HUD pixel regions.
- Classify whether the failure is common to the fixture and production scene,
  or specific to scene content/resources.
- Preserve the QMP screenshot/video, selected runtime/GDB/journal evidence,
  hashes, and QMP teardown.
- If a source change is required, create a separate patch ticket after the
  operation boundary is proven.

## Facts

- FLR-0090 found `FEngine::loop` and llvmpipe workers waiting inside
  `libvulkan_lvp.so` while the submit fence remained `VK_NOT_READY`.
- The 2D HUD presents, but the native 3D region remains black.
- The valid production command-trace run completed QEMU startup, guest
  readiness, serial launch/dump, QMP PPM capture plus 20 frame captures, QMP
  quit, and residual-process cleanup. The native region was `0/223200` and
  the HUD region was `116/100000`, with HUD bounding box `[200,113,29,66]`.
- Production command execution recorded 1,415 command-begin markers and 1,414
  command-done markers. The only unfinished command was `bindPipeline`; the
  preceding `beginRenderPass`, `scissor`, and both `bindDescriptorSet`
  operations completed.
- The production pipeline-substep run recorded eight `bindPipeline` begins.
  Earlier pipeline instances completed, but the last instance ended after
  `GRAPHICS_PIPELINE_CREATE_BEGIN` without
  `GRAPHICS_PIPELINE_CREATE_DONE`, `PIPELINE_CACHE_ENTRY_DONE`, or
  `PIPELINE_CMD_BIND_DONE`. Static source inspection maps this boundary to
  `vkCreateGraphicsPipelines` in `VulkanPipelineCache::createPipeline`.
- The valid self-made fixture run completed repeated submit/present activity,
  captured 20 QMP frames, and produced native pixels (`41750/223200`, bounding
  box `[501,278,278,162]`) together with HUD pixels (`6246/100000`). Its
  command trace had 2,770 begins and 2,769 dones; the sole trailing unmatched
  operation was `commit` during capture shutdown, after the fixture had already
  rendered and presented visible frames.
- The evidence runs were executed with the fixed Mini PC QEMU contract and
  were terminated through QMP; both reported zero residual QEMU/QMP targets.

## Inferences

- The first scene-specific divergence is inside graphics-pipeline creation,
  before pipeline binding, draw, submit completion, and present. The fixture
  reaches the same command path successfully, so the failure is not a generic
  Vulkan fence/present failure.
- The production black native region is consistent with the pipeline-creation
  stall preventing the production render pass from reaching a visible draw.
- The fixture's trailing `commit` mismatch is a capture-shutdown artifact,
  not evidence that the fixture is broken.

## Hypotheses

1. The production scene reaches a shader, descriptor-layout, render-pass, or
   other graphics-pipeline combination that makes llvmpipe block inside
   `vkCreateGraphicsPipelines`.
2. A production resource lifetime or pipeline-cache key is invalid, while the
   self-made fixture uses a smaller valid combination.
3. The trace boundary is an instrumentation or timeout artifact rather than
   a real driver stall. This is currently less likely because the production
   QMP native region remains zero and the fixture completes the same path, but
   it is not yet disproved by a backtrace.

## UNKNOWN

- The exact production pipeline inputs that trigger the stall.
- Whether the blocked llvmpipe worker has a stable backtrace and whether it is
  in shader compilation, pipeline validation, or resource access.
- Whether guest journal/syscall evidence shows a fault during the wait.

## Plan / Do / Check / Act

### Plan

Reuse the current image and fixed QEMU flow. Use the smallest existing
command/resource trace or a bounded GDB/syscall observation, then compare one
fixture and one production launch only if the common boundary requires it.

### Do

Reused the fixed image and ran one valid production command trace, one valid
self-made fixture trace, and one production pipeline-substep trace. An earlier
production collection with a wrong log path and the first fixture collection
with a shell quoting error were classified as invalid collection attempts;
neither was used for a product conclusion. The valid runs were closed through
QMP and retained under the FLR-0091 evidence set on the Mini PC.

### Check

PASS: production first unfinished command is `bindPipeline`, with the
substep boundary at `vkCreateGraphicsPipelines`; fixture completes the
pipeline, submits, presents, and produces QMP native pixels. QMP screenshot,
frame sequence, serial dump, hashes, and teardown evidence are retained in:

- `$RECEIVER/evidence/flr0091-af24ec3/qemu-command-trace-r2/`
- `$RECEIVER/evidence/flr0091-af24ec3/qemu-command-trace-fixture/`
- `$RECEIVER/evidence/flr0091-af24ec3/qemu-pipeline-trace/`

Representative hashes are recorded in each run's `*-sha256.txt`. The exact
current-image rootfs/kernel/qemuboot identities remain those fixed by FLR-0090.

### Act

Open FLR-0093 for production graphics-pipeline input/backtrace isolation.
Generate a source patch only after that boundary is explained; use Mac
Devtool, build authoritatively on Mini, and verify QMP pixels.
