# FLR-0093 — isolate production graphics-pipeline creation

- Status: Done
- Priority: High
- Owner: Filament Vulkan pipeline cache / llvmpipe runtime
- Created: 2026-09-12
- Depends on: [FLR-0091](FLR-0091-isolate-first-unfinished-command.md)
- Working log: `work/logs/2026-09-12-flr0093.md`

## Work unit

Explain why the production scene stops inside `vkCreateGraphicsPipelines`
while the self-made fixture completes the same pipeline path and produces
native QMP pixels. Identify the effective shader, descriptor-layout,
render-pass, raster, and resource inputs at the first blocking instance before
changing source behavior.

## Success criteria

- Reproduce the production-only pipeline-create boundary on the fixed image
  with one bounded QEMU run.
- Collect a runtime backtrace or equivalent driver evidence for the blocked
  worker, plus the smallest useful journal/syscall evidence.
- Compare the blocking production pipeline inputs with one fixture pipeline
  that completes.
- Select one falsifiable next cut, or identify the exact source operation that
  needs a patch, without changing present or fence semantics as a shortcut.
- Preserve QMP screenshot/frame evidence, hashes, runtime evidence, and clean
  QMP teardown.

## Facts

- FLR-0091 identified `bindPipeline` as the first unfinished command in
  production.
- The production pipeline trace has a final
  `GRAPHICS_PIPELINE_CREATE_BEGIN` without a completion marker.
- The self-made fixture reaches visible native pixels and completes its
  pipeline path on the same fixed image.
- The bounded production trace `$RECEIVER/evidence/flr0091-af24ec3/qemu-pipeline-trace`
  kept the native candidate region at `0/223200` while the HUD remained
  visible at `116/100000`; QMP teardown and artifact hashing passed.
- The follow-up GDB run `$RECEIVER/evidence/flr0093-qemu-gdb-pipeline`
  attached once to the single QEMU-launched process. It observed 39 threads;
  llvmpipe workers and the Filament engine were waiting in futex/condition
  paths, with no captured signal or fault.
- In that longer trace, the production `vkCreateGraphicsPipelines` calls
  eventually returned `result=0`. The same bounded sequence then recorded
  submit `result=0`, fence status `result=1` (`VK_NOT_READY`), and
  `QUEUE_PRESENT_BEGIN` without a return. The native region stayed at
  `0/223200`, while the HUD region was `1284/100000`; QMP teardown passed.
- Static source mapping places the create boundary in
  `VulkanPipelineCache::createPipeline()`, at
  `vkCreateGraphicsPipelines`, using shader modules, render pass, layout,
  topology, vertex inputs, raster state, and sample count.
- Mac Yocto Devtool generated the diagnostic patch from source commit
  `27f57649c`; the canonical copy is
  `layers/meta-fluorite-trial/recipes-graphics/filament/files/0186-diag-trace-effective-Vulkan-pipeline-inputs-devtool.patch`
  with SHA-256 `f49877d34ee60619fd7e01d6f655d848f00b70e9903c65d6d24f5c5745a6b12d`.
- Mini `do_patch`, `do_compile`, and `agl-ivi-image-flutter` all passed on the
  same fixed build/TMPDIR. The image artifact hashes and task counts are in
  `work/evidence/FLR-0093-pipeline-input-qemu-2026-09-12.md`.
- The new QMP-only production run captured 20 frames plus a final frame. The
  native candidate was `0/223200`; the HUD was `1236/100000` with bbox
  `[200,113,29,66]`. Exactly one `agl-driver` `flutter-auto` was observed,
  and QMP teardown left no target process or socket.
- Six neutral pipeline-input records and six `result=0` create results were
  observed. The slowest create took `21509378` microseconds; later frame
  attempts remained `started=false`.
- The first post-run bundle attempt was refused because raw QMP evidence in
  the fixed receiver was untracked. This exposed a handoff contract defect,
  not a build or runtime defect. The handoff now ignores only the bounded
  receiver-root `evidence/` payload directory; other receiver changes still
  block synchronization, and the evidence was preserved.

## Inferences

- The next useful layer is the effective pipeline inputs and blocked worker,
  not Wayland alpha, surface placement, or present-mode changes.
- The first bounded trace was a timing boundary, not proof of a permanent
  pipeline-create deadlock. The current persistent divergence is later:
  fence completion/present return after successful submit.
- The long create duration is evidence of expensive production work under
  llvmpipe, but it does not by itself explain the missing native pixels or
  prove a deadlock.

## Hypotheses

1. Full-production shader/resource work is sufficiently expensive in llvmpipe
   to create timing or resource pressure before the frame can present.
2. A production descriptor layout, render-pass/sample configuration, or
   resource lifetime leaves work pending and prevents fence completion.
3. The apparent create boundary is an instrumentation timing artifact; the
   successful results support this for the permanent-stall interpretation,
   while the later synchronization boundary remains real.

## UNKNOWN

- Which effective pipeline input differs between the successful fixture and
  the full production scene in a way that explains the pending work.
- The exact llvmpipe worker function below the captured futex wait; the run
  showed no fault, but symbols were insufficient to name the operation.
- Whether the diagnostic input trace changes the native QMP result; no product
  behavior change has been attempted.
- The exact llvmpipe operation that leaves the later fence incomplete remains
  UNKNOWN; this ticket does not change synchronization behavior.

## Plan / Do / Check / Act

### Plan

Use the existing fixed Mini/QEMU flow and the smallest current diagnostic
controls. First capture the production blocked-worker state and effective
pipeline inputs; then compare against the successful fixture. Only after the
process boundary is explained, make a Mac Devtool source change, bundle it,
apply it on Mini, and build the authoritative image.

### Do

1. Captured the valid production pipeline trace and a one-attach GDB run on
   the fixed Mini/QEMU flow.
2. Edited the Devtool-managed Filament source on Mac, committed it as
   `27f57649c`, and generated the patch through Yocto Devtool's
   component-scoped `update-recipe` flow.
3. Imported only that generated patch into the canonical layer; no
   `FLR0026`-named directory or new runtime namespace was created.

### Check

GDB/runtime evidence is PASS for the selected boundary and the canonical
patch is byte-identical to the Devtool output. Mini metadata, `do_patch`,
`do_compile`, full-image build, QMP-only capture, and QMP teardown are PASS.
The production 3D result remains FAIL (`0/223200`) while the HUD is visible;
the evidence supports moving the next cut to fence/present completion.
The raw-evidence handoff failure was fixed in the receiver cleanliness
contract and is separately verified before the next bundle handoff.

### Act

Use the current layer commit already handed off in one verified bundle to the
fixed Mini receiver. Preserve the QMP evidence manifest and choose the next
independent ticket around the later fence/present completion boundary. This
diagnostic patch is not a product fix. The historical namespace remains
read-only and is not a current directory, receiver, environment variable, or
evidence name.
