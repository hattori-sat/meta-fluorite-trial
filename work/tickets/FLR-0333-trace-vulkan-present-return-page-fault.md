# FLR-0333 — trace Vulkan present return and FEngine page fault

- Status: Done
- Priority: High
- Owner: Vulkan WSI present / llvmpipe-LLVM / FEngine loop roles
- Created: 2026-09-28
- Predecessor: [FLR-0332](FLR-0332-trace-native-buffer-publish-trigger.md)
- Working log: `work/logs/2026-09-28-flr0333.md`
- Completed: 2026-09-28 (present/fault boundary classified; root cause remains UNKNOWN)

## Objective

Identify the first failing substep between `FLUORITE_VK_PRESENT_CALL_BEGIN`,
`FLR0026_VK_QUEUE_PRESENT_BEGIN`, and the missing present return in the
authoritative QEMU image. Restore a deterministic diagnostic boundary before
changing production Light, camera, material, or Scene behavior.

## Success criteria

- Reproduce the present-return boundary once using the existing Mini receiver,
  build, QEMU, and QMP evidence workflow.
- Compare at least two plausible causes: WSI semaphore/present ownership and
  llvmpipe/LLVM or ABI/runtime fault.
- Collect only bounded serial, journal, process, and QMP evidence; do not read
  unrelated full logs into the working context.
- Decide whether the next minimal Devtool patch belongs in the present path,
  the runtime ABI/source baseline, or neither.
- Preserve QMP-only full-frame evidence and clean teardown.

## Facts / hypotheses / UNKNOWN

### Facts

- `beginFrame=true`, Scene draw submit, render return, and draw end are logged.
- Explicit `FLUORITE_NATIVE_WAYLAND_COMMIT=1` does not create native pixels.
- `FLR0026_VK_QUEUE_PRESENT_BEGIN` is logged, but the present return/result is
  absent.
- Wayland parent surface `@14` attaches SHM buffers; the child ViewTarget
  surface commits without an attached buffer.
- The guest reports a page fault in `FEngine::loop`.
- The same-image production diagnostic profile loaded the Sequoia GLB and added
  two model instances with 12 and 22 renderables. The PaintColor primitive was
  replaced by the magenta unlit diagnostic material, but the QMP vehicle ROI
  remained black.
- `FLUORITE_VK_PRESENT_CALL_BEGIN` and
  `FLR0026_VK_QUEUE_PRESENT_BEGIN` appeared without a corresponding return.
  A later FEngine worker reported a user-mode page fault; its exact module and
  relation to the earlier present call are not established.
- A GDB attach after the fault found the surviving FEngine/llvmpipe workers in
  Mesa condition-variable waits. The faulting worker was already absent and
  `coredumpctl` had no matching core.

### Hypotheses

1. **Generic semaphore/WSI ownership fault. Weakened, not falsified.** The
   historical no-wait probe did not remove the stall, and the same image's
   pure native fixture returned successfully through queue-present. A
   production-specific WSI interaction remains possible.
2. **Production scene/resource or llvmpipe/LLVM runtime fault. Best supported,
   not proven.** The production run reached model insertion and an unlit
   PaintColor override, then had a missing present return and an FEngine
   user-mode fault. The faulting instruction was not symbolicated.
3. **Light or texture sampling is the primary cause. Unsupported by this
   run.** The magenta unlit replacement still produced no vehicle pixels, so
   neither lighting nor the original PaintColor texture explains the first
   missing visible pixels by itself.

### UNKNOWN

- Exact faulting instruction/library frame and whether it is the same thread
  that entered queue-present.
- Whether the user-mode fault caused the missing present return or was a
  separate concurrent failure.
- Whether any production GLB texture is sampled successfully at runtime.

## Plan / PDCA

1. Reuse the existing image and QEMU evidence directory; verify no duplicate
   QEMU/TMPDIR/container.
2. Run the smallest present-boundary A/B already represented by existing
   project controls, beginning with read-only/trace-only evidence.
3. Inspect the resulting bounded kernel/runtime markers and QMP ROI.
4. If a source change is justified, use the Mac persistent Devtool source Git,
   official rebase/update-recipe flow, canonical patch registration, bundle,
   Mini `do_patch`/compile/image, and one QMP run.

## Result and PDCA close

- The boundary gate is complete: queue-present begins but has no observed
  return; the same QEMU run records a user-mode fault in an FEngine worker.
- The generic semaphore-only explanation is weakened by the historical
  no-wait result and the successful fixture queue-present control. The
  production-scene/FEngine runtime path is now the leading investigation
  boundary, but no root cause or patch location is asserted.
- The QMP production still shows the HUD and Scenes control over a black
  vehicle region. The PaintColor magenta-unlit override is logged as applied,
  yet ROI `(440,220,400,360)` is `0/144000` changed pixels. All eight video
  frames have the same SHA-256, so the displayed HUD is not evidence of live
  frame updates in this run.
- The control fixture contains a cube, but its diagnostic camera looks
  directly at one face; its blue square does not prove visible depth. Its
  queue-present returned `result=0`, proving only the fixture path.
- No source patch, recipe edit, build, or image rebuild was made. Only tracked
  evidence-command helpers and ticket/evidence records changed.
- Follow-up: [FLR-0334](FLR-0334-symbolize-production-fengine-render-fault.md)
  will catch and symbolize the fault before changing Light, texture, camera,
  or production scene behavior.

## Visual evidence

- Run: `$EVIDENCE_ROOT/flr0333-0001/qemu`; exact image hashes and QMP-only
  screenshot/video checksums are in
  [the FLR-0333 evidence index](../evidence/FLR-0333-present-boundary-2026-09-28.md).
- Full production QMP frame: `qmp-0333-production-full.ppm`, SHA-256
  `e468e624acf85b21ed086cadc222008d5fc967f153269f21006c396e6350e5e8`.
- Visible: HUD telemetry and Scenes button; the central vehicle/3D region is
  black. The eight captured production frames are byte-identical.

## Stop conditions

- Do not treat `FLUORITE_NATIVE_WAYLAND_COMMIT` as a product fix.
- Do not change Light, camera, material, Scene ownership, or stacking until the
  present-return/page-fault boundary is classified.
- Do not start a second QEMU or create a new receiver/TMPDIR for this ticket.
