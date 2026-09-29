# FLR-0103 — trace the post-scene Vulkan/LLVM present boundary

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan/llvmpipe + target-validation roles
- Created: 2026-09-12
- Depends on: [FLR-0102](FLR-0102-instrument-production-scene-draw-seam.md), [FLR-0101](FLR-0101-isolate-libllvm-fault-trigger.md)
- Working log: `work/logs/2026-09-12-flr0103.md`
- Prerequisite completed: [FLR-0104](FLR-0104-runtime-debug-tools.md)

## Work unit

Identify the first divergent operation after the production scene draw seam and
before the native pixels that are visible in the self-made fixture. The current
production run completes the instrumented scene-pass marker, enters engine
execution and queue present, then reports an `FEngine::loop` page fault at the
known Vulkan/LLVM boundary. The fixture completes the same seam, returns from
queue present, and produces native pixels.

This ticket is an evidence unit. Do not change present, fence, semaphore,
compositor, light, camera, or material semantics until the exact failing
operation is mapped.

## Success criteria

- Static source mapping names the exact caller chain from scene-pass completion
  through `VulkanSwapChain::present` / `vkQueuePresentKHR` and the relevant
  llvmpipe/LLVM path before any source edit.
- One fixed-image fixture control and one fixed-image production case are
  compared with the same one-QEMU, guest-side process guard, and QMP-only
  evidence contract.
- Runtime evidence correlates marker order, queue-present entry/return,
  `FEngine::loop` fault state, native/HUD pixel counts, and QMP frame hashes.
- The first missing or faulting boundary is identified, or remains explicitly
  UNKNOWN with a narrower next observation. No causal claim is made from a
  symbol or address alone.
- The fixed QMP teardown leaves no QEMU, `runqemu`, `flutter-auto`, or QMP
  socket residuals.
- New controls, markers, ticket names, and evidence paths use the neutral
  `FLUORITE_*` namespace. No legacy operation namespace is extended.

## Facts

- FLR-0102's self-made fixture reached the scene-pass BEGIN/END markers,
  returned from queue present, and produced `41750/223200` native pixels while
  the HUD remained visible.
- FLR-0102's production Example Demo reached scene-pass BEGIN/END for command
  counts `0`, `1`, and `552`, then reached engine execute, queue wait, and
  present entry, but remained at `0/223200` native pixels.
- The same production run reported a page fault/Oops in `FEngine::loop`; no
  retained queue-present return was observed.
- Earlier runtime matrices reached model completion, camera application, and
  present markers across multiple light counts without native pixels. Those
  results do not justify a light-count or camera patch.
- The canonical layer commit, fixed Mini build/TMPDIR, installed image, and
  QMP evidence roots are already established by FLR-0102 and must be reused.
- The FLR-0103 documentation/evidence commit was transferred through the
  existing bundle helper; the Mini receiver now matches that exact tip. No
  image rebuild was needed for this documentation-only follow-up.
- Static inspection of the persistent source maps the boundary as
  `FEngine::execute → VulkanDriver::commit → VulkanSwapChain::present →
  VulkanPlatform::present → VulkanPlatformSurfaceSwapChain::present →
  vkQueuePresentKHR`. The return marker is immediately after the Vulkan call.
- The FLR-0104 debug image was reused without a source or image-semantic
  change. Its rootfs SHA-256 is
  `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`.
- The one-QEMU `gdb-r1` run passed preflight, start, guest-ready, and QMP
  capture. GDB loaded the guest `.debug` files and kept one gdbserver and one
  `flutter-auto` process; no second runtime was created.
- The QMP mid and late frames were both HUD-only by visual inspection. Their
  PPM SHA-256 values are
  `31ba97e46be0d2e81f01c086e1e053aa2ddef66afa26fa6ecaa3dfc979d1f437` and
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- The retained production frame stream continued to emit frame begin/draw
  event/return records with `started=false` through at least sequence `990`;
  no native 3D pixels appeared in the QMP frames.
- At approximately 347 seconds the guest kernel reported a user-space RIP
  `0x7fffee804541` and CR2 `0x0000000091006750` for `PID: 699 Comm:
  FEngine::loop`. The process map placed the RIP in the executable
  `libLLVM.so.18.1` mapping.
- RIP arithmetic against the current mapping gives file offset `0xb1d541`.
  Guest `llvm-symbolizer` resolved that address to
  `llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)` with no source line,
  matching the earlier FLR-0030 mapping. This identifies a symbol boundary,
  not the original producer or root cause.
- GDB did not report `Program received signal` for the kernel OOPS; the
  process remained alive until a later diagnostic `addr2line` invocation
  caused guest OOM and the kernel killed `flutter-auto` with SIGKILL. That
  OOM is a separate failed observation and is not the production fault
  verdict.
- `coredumpctl list --no-pager` remained empty in this run. QMP quit completed
  with zero residual target processes and zero residual QMP sockets.

## Inferences

- The generic Flutter 2D path and the basic native fixture presentation path
  are working; the failure is narrower than QEMU startup or global Wayland
  visibility.
- Because the production scene-pass marker closes before the fault, the next
  useful observation is the common post-scene execution/present path rather
  than another scene-content selector.
- The fault may be in production command/resource interaction with llvmpipe,
  in a common Vulkan present call, or in the native surface handoff. Current
  evidence does not select one of these owners.
- The fixture control with present tracing returned `result=0` repeatedly, while
  the production case entered the same present call without a return marker.
- The same QEMU run completed through QMP teardown with zero residual target
  processes and sockets.
- The debug-image run confirms that 2D HUD rendering remains visible while the
  production native region is black; the failure is not a global Flutter or
  QMP display failure.
- The current RIP maps one byte into the known LLVM `isOrdered` symbol at
  offset `0xb1d541`. Corrupted control flow or return state is plausible from
  the instruction position, but the evidence does not prove that `isOrdered`
  produced the corruption.
- The standard batch GDB command is not sufficient for this kernel-OOPS form:
  it loaded symbols but did not receive a normal signal stop. The next useful
  observation is a minimal breakpoint at the symbol entry with a bounded
  caller/register capture.
- Guest-side symbol inspection while the application is running is unsafe at
  this memory pressure. Future runs must avoid broad `addr2line`/all-thread
  collection and retain only targeted output.

## Hypotheses

1. A production command or resource state reaches a llvmpipe/LLVM operation
   that faults after scene command recording. Prediction: the production trace
   faults before a common post-scene return while the fixture returns.
2. The production and fixture command streams both complete, but a common
   `vkQueuePresentKHR` or surface handoff differs in argument/state. Prediction:
   a call/return or syscall-level trace localizes the divergence without a
   scene-specific marker stop.
3. The queue-present return marker is misplaced or lost by the observation
   path. Prediction: debugger/syscall evidence shows a return even when the
   application log does not; QMP pixels still distinguish the cases.

## UNKNOWN

- The exact source line and producer of the fault, including whether the
  `isOrdered` boundary reflects a bad call target, return state, or corrupted
  LLVM/llvmpipe state.
- Whether `vkQueuePresentKHR` is entered with the same swapchain, image, wait
  semaphore, and surface state in the fixture and production cases.
- Whether the production native buffer contains any usable pixels before the
  compositor receives it.
- Whether the empty `coredumpctl` result is expected for this kernel-OOPS form
  or reflects a missing coredump capture configuration.

## Plan / Do / Check / Act

### Plan

1. Verify the canonical repository, active ticket, fixed image identity, and
   zero residual runtime targets.
2. Inspect the current persistent Mac Devtool source and map the post-scene
   call chain, including symbols for the existing fault boundary.
3. Reuse the FLR-0102 image and run the smallest fixture/production comparison
   that captures the next boundary with QMP-only frames and guest logs.
4. Use GDB, syscall, or existing runtime diagnostics only as needed to
   distinguish call entry, return, and fault; keep observation changes opt-in.
5. If a source probe is required, edit only the persistent Mac Devtool source,
   generate the official Devtool patch, commit it to the layer, bundle it, and
   rebuild on the Mini before runtime validation.

### Do

- Ticket and working log created after the canonical-repository check passed.
- Read-only static mapping completed in the persistent Mac Devtool source.
- Reused one QEMU and the FLR-0102 image. The fixture was launched with the
  neutral trace controls, captured by QMP, stopped by its recorded PID, and the
  production Example Demo was launched with the same image and trace controls.
- Preserved the unsupported pixel-analysis invocation and the first noisy log
  extraction as failed observations; both were corrected without restarting
  QEMU.
- Reused the new debug image for `gdb-r1`; GDB loaded guest debug files,
  captured the live process/map state, and the LLVM symbol was resolved with
  `llvm-symbolizer`.
- Preserved the kernel OOPS and the later diagnostic OOM as separate evidence;
  no source or rendering-semantics patch was made.

### Check

The fixture QMP frame recorded `41750/223200` native pixels and its present
return was `result=0`. The production frame recorded `0/223200` native pixels
and HUD `1091/100000`; production scene command count `552`, submit return, and
present entry were observed, but the queue-present return was absent. The guest
reported a page fault/Oops in `FEngine::loop` after approximately 299 seconds.
The full evidence index is
`work/evidence/FLR-0103-post-scene-present-2026-09-12.md`.

The `gdb-r1` run added a current-map resolution to
`libLLVM.so.18.1` / `llvm::CmpInst::isOrdered` at file offset `0xb1d541`.
The normal GDB client did not stop on the kernel OOPS. A later guest
`addr2line` observation caused an independent OOM and SIGKILL; it is retained
as a failed collection, not as the product fault.

### Act

The first missing boundary is narrowed to the `vkQueuePresentKHR` call or its
callee, and the current fault maps to the known LLVM `isOrdered` symbol. The
source line, caller, and root cause remain UNKNOWN. Close FLR-0103 as the
boundary-evidence unit and continue in
[FLR-0105](FLR-0105-gdb-breakpoint-ownership.md), which captures the symbol
entry caller with a memory-bounded GDB breakpoint before any source patch is
considered.
