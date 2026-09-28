# FLR-0106 — capture the producer above LLVM InstCombine

- Status: Done
- Priority: High
- Owner: runtime diagnosis + Mesa/llvmpipe + Filament/Vulkan + target-validation roles
- Created: 2026-09-12
- Depends on: [FLR-0105](FLR-0105-gdb-breakpoint-ownership.md), [FLR-0104](FLR-0104-runtime-debug-tools.md)
- Working log: `work/logs/2026-09-12-flr0106.md`

## Work unit

Expose the first caller above LLVM's InstCombine path when the production
scene reaches `llvm::CmpInst::isOrdered`. FLR-0105 proved a normal entry and
captured eight LLVM frames, but the outer Mesa/llvmpipe or Filament producer
was outside that bounded sample. Use one entry breakpoint and a bounded
16-frame capture, then correlate the caller with the scene/present markers and
the later one-byte-offset OOPS. Do not change renderer semantics.

This is an ownership-evidence unit. No patch to present, synchronization,
surface composition, light, camera, material, Filament, Mesa, or LLVM is
allowed until the producer and expected operation are directly evidenced.

## Success criteria

- Reuse the FLR-0104 debug image, fixed Mini receiver, build/TMPDIR, and one
  QEMU at a time.
- Capture the first `isOrdered` entry with a bounded 16-frame backtrace and
  enough return-address/module information to identify the outer producer, or
  explicitly classify the stack as unresolved.
- Preserve QMP-only visual evidence, native/HUD pixel counts, marker order,
  process count, RSS/available-memory sample, and QMP teardown.
- Do not invoke guest `addr2line`, full all-thread backtraces, or unbounded log
  extraction during the live run.
- Keep the source fix out of scope unless the producer and expected behavior
  are proven; otherwise open another narrower evidence ticket.

## Facts inherited from FLR-0105

- Production entered `isOrdered` at its normal entry address and reached
  `matchSelectPattern`, `matchDecomposedSelectPattern`,
  `InstCombinerImpl::visitFCmpInst`, and `InstCombinePass::run`.
- The later OOPS landed one byte after the entry in another `FEngine::loop`
  thread, while the QMP frame remained HUD-only (`0/223200` native).
- The debug image has the required GDB/LLVM tools, but guest memory is limited
  and swap is disabled. The previous bounded run reached about 1.1 GiB RSS.

## Hypotheses

1. Mesa/llvmpipe shader compilation calls LLVM InstCombine for a production
   shader/material. Prediction: a 16-frame stack reaches `libvulkan_lvp.so`,
   Mesa, or a shader compiler frame above LLVM.
2. Filament or Flutter submits malformed IR/state through a generic compiler
   entry. Prediction: the outer frame is Filament, Flutter, or application
   code rather than Mesa/llvmpipe.
3. The later OOPS is unrelated corrupted control flow. Prediction: the normal
   entry stack is stable across repeated hits, while the later OOPS has no
   matching entry event or has a different thread/state.

## Plan / Do / Check / Act

### Plan

1. Verify canonical repository, sole active ticket, fixed image hashes, and no
   residual runtime targets.
2. Run the production Demo under the existing bounded entry breakpoint, using
   `bt 16` only on the first hit and then detaching.
3. Capture one QMP frame and focused marker/memory evidence.
4. Teardown through QMP and classify the outer producer. Open a source-patch
   ticket only after the expected operation is proven.

### Do

- Reused the FLR-0104 debug image, fixed Mini receiver, existing build/TMPDIR,
  and one QEMU instance.
- Started one production Example Demo under the pending
  `llvm::CmpInst::isOrdered` entry breakpoint. On the first hit, GDB recorded
  registers and `bt 16`, disabled the breakpoint, detached, and exited.
- Captured the QMP frame after the GDB observation, ran focused native/HUD
  pixel analysis, collected focused marker/process/memory/OOPS evidence, and
  terminated the same QEMU through QMP.

### Check

- PASS: the first non-LLVM frame is Mesa
  `gallivm_compile_module()` at `lp_bld_init.c:620`.
- PASS: one guest `flutter-auto`/`gdbserver` pair was observed; no duplicate
  application process was present.
- PASS: QMP screenshot and hashes are retained. Native region is
  `0/223200`; focused HUD region is `1218/100000`.
- PASS: QMP quit and residual checks reported zero targets and zero sockets.
- FAIL: production native 3D remains black; the source-level root cause is
  not proven.

### Act

- Closed this bounded ownership-evidence unit without a source or image
  patch.
- Opened FLR-0107 to inspect the Gallivm/LLVM input and return contract.

## UNKNOWN

- Whether the Mesa Gallivm callsite receives invalid LLVM input or state.
- Whether the normal `isOrdered` entry and later OOPS share a corrupted state.
- Whether the producer can be fixed in the Fluorite layer or requires an
  upstream/runtime change.

See `work/evidence/FLR-0106-gdb-outer-producer-2026-09-12.md` for the complete
runtime and QMP evidence.
