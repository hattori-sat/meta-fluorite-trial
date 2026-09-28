# FLR-0105 — capture the production caller at the LLVM fault boundary

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Filament/Vulkan/llvmpipe + target-validation roles
- Created: 2026-09-12
- Depends on: [FLR-0103](FLR-0103-trace-post-scene-vulkan-present-boundary.md), [FLR-0104](FLR-0104-runtime-debug-tools.md)
- Working log: `work/logs/2026-09-12-flr0105.md`

## Work unit

Determine whether the current production `FEngine::loop` OOPS reaches
`llvm::CmpInst::isOrdered` through a normal call or lands one byte into the
function because of corrupted control-flow/return state. Use the installed
guest GDB tools with a pending breakpoint at the known symbol entry and a
small caller/register capture. Keep the production image and rendering
semantics unchanged.

This is a debugger evidence unit. Do not patch Vulkan present, fences,
semaphores, compositor, lights, camera, materials, Filament, Mesa, or LLVM
until the caller and expected control flow are established.

## Success criteria

- One QEMU run reuses the FLR-0104 debug image and the fixed Mini receiver.
- The GDB client uses a symbol-entry breakpoint or equivalent address
  breakpoint and records only a bounded caller/register/instruction sample.
- The result distinguishes at least these cases: normal entry into
  `isOrdered`, no entry before a one-byte-offset OOPS, or an inconclusive
  observation caused by debugger/runtime interference.
- The run records 2D/HUD and native-region QMP evidence, selected marker
  order, memory pressure, and QMP teardown.
- Guest-side broad `addr2line`, full all-thread dumps, and unbounded log
  transfers are not used while the application is under observation.
- The exact producer remains UNKNOWN unless the caller and operation are
  directly evidenced. No source patch is created by this ticket alone.

## Facts inherited from FLR-0103

- The self-made fixture returns from queue present and produces native 3D
  pixels; the production Example Demo retains the HUD but has a black native
  region.
- The production run reaches the post-scene/present boundary and later
  reports a user-space RIP in `libLLVM.so.18.1` for `FEngine::loop`.
- Current mapping arithmetic resolves the RIP to file offset `0xb1d541`,
  symbolized as `llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)` with no
  source line. The earlier FLR-0030 mapping matches this result.
- The standard batch GDB client did not receive a normal signal stop for the
  kernel OOPS. A later guest `addr2line` extraction caused an independent OOM
  and SIGKILL, so the next run must be memory-bounded.
- The bounded `gdb-r2` run hit the symbol-entry breakpoint at
  `0x7fffee804540`, the normal entry of `isOrdered`, with `rdi=0xc` and
  `rsi=0`. Its eight-frame backtrace stayed in LLVM:
  `matchSelectPattern` → `matchDecomposedSelectPattern` →
  `InstCombinerImpl::visitFCmpInst` → `InstCombinerImpl::run` →
  `combineInstructionsOverFunction` → `InstCombinePass::run`.
- The same run later reported the kernel OOPS at `0x7fffee804541`, one byte
  past the normal entry, in a different `FEngine::loop` thread. The breakpoint
  hit therefore proves a normal call exists but does not prove that it caused
  the later invalid control flow.
- The QMP frame was 1280x800 with native region `0/223200` and HUD region
  `1250/100000`, bounding box `[200,113,29,66]`. Its PPM SHA-256 is
  `3da26a6795d446e4918debab57d1b7a1aaeb6441f0ff32267ea1f3d04a2e539e`.
- At the final focused sample, `flutter-auto` RSS was `1139220` kB and the
  guest had no swap. This is a resource-pressure warning, but this run did
  not produce the separate OOM kill seen in FLR-0103.
- QMP quit was accepted and cleanup reported zero residual target processes and
  zero residual QMP sockets.

## Hypotheses

1. A normal LLVM call is entered from a production-only shader/resource path.
   The entry breakpoint hit, but the bounded backtrace ended inside LLVM;
   the outer Mesa/llvmpipe caller remains unobserved.
2. The OOPS is an invalid indirect target or return state. Prediction: the
   a later fault lands at `isOrdered+1` or another non-entry address even
   though a normal entry was observed separately. This remains plausible.
3. GDB or the large debug image changes timing or memory enough to prevent a
   faithful observation. The breakpoint-only run stayed below the separate
   OOM condition, but its caller depth was intentionally bounded.

## Plan / Do / Check / Act

### Plan

1. Verify canonical repository, sole active ticket, fixed debug-image hash,
   and zero residual runtime targets.
2. Run one production Demo under `gdbserver` with a pending breakpoint at the
   known symbol and a bounded command list: breakpoint hit count, `$pc`, a
   short backtrace, selected registers, and one disassembly window.
3. Capture one QMP frame and only focused memory/process/kernel evidence.
4. Teardown through QMP, classify the result, and open a separate source
   patch ticket only if the expected operation and owner are directly shown.

### Do

- Reused the FLR-0104 debug image and fixed Mini receiver in one QEMU.
- Started the production Demo under one `gdbserver` and a bounded GDB command
  file. The entry breakpoint hit once, emitted PC/registers and eight frames,
  disabled itself, detached, and exited.
- Captured the QMP frame and analyzed the native/HUD regions, then terminated
  QEMU through QMP. A path typo in the first serial-exec attempt was retained
  as a harness failure and corrected without restarting QEMU.

### Check

The normal LLVM entry and its bounded internal caller chain were captured.
The later OOPS still landed at `isOrdered+1`, while the application continued
to show HUD-only output. This satisfies the ownership-boundary observation but
does not identify the outer producer or justify a source patch.

### Act

- Close FLR-0105 as a debugger evidence unit and continue in
  [FLR-0106](FLR-0106-capture-llvm-outer-producer.md). Its scope is a bounded
  16-frame capture to expose the caller above LLVM, with no rendering-semantic
  patch.

## UNKNOWN

- The outer caller and resource/command state that precede the OOPS; the
  captured eight frames end inside LLVM.
- Whether the normal `isOrdered` call and the later `isOrdered+1` OOPS share
  the same invocation or state.
- Whether this kernel-OOPS form can be captured by `coredumpctl` on the image.
