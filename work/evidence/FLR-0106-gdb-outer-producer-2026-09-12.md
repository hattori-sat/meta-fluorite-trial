# FLR-0106 evidence — bounded outer-producer GDB capture (2026-09-12)

## Outcome

The bounded GDB capture reached the first non-LLVM frame above the previously
known InstCombine chain: Mesa's `gallivm_compile_module()` at
`lp_bld_init.c:620`. The runtime producer boundary is therefore identified as
the Mesa/llvmpipe Gallivm compilation path. This does not prove malformed IR,
memory corruption, or causality for the later OOPS. Production native 3D
remains unresolved and is still `0/223200` in the QMP frame.

## Runtime identity

- Image role: FLR-0104 debug image
- Rootfs SHA-256:
  `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Qemuboot SHA-256:
  `ba6711550d96677f66e99f3a06af308a61c1e58a7b776f7489b42c8cc470136d`
- Evidence directory:
  `$RECEIVER/evidence/flr0103-post-scene-present/gdb-r3/`
- Run contract: one QEMU, bounded GDB, QMP-only capture, QMP quit, and zero
  residual runtime targets/QMP sockets.

## Facts

### Bounded GDB result

The first breakpoint at the normal entry of
`llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)` captured the following
bounded chain:

```text
FLR0106_GDB_BREAKPOINT_HIT pc=0x7fffee804540
=> 0x7fffee804540 <...isOrdered...>: dec %edi
FLR0106_REGS rip=0x7fffee804540 rsp=0x7fffed2b1328 rdi=0xc rsi=(nil) rdx=0x5 rcx=(nil)
#0  llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)
#1  matchSelectPattern(...)
#2  llvm::matchDecomposedSelectPattern(...)
#3  llvm::matchSelectPattern(...)
#4  llvm::InstCombinerImpl::visitFCmpInst(...)
#5  llvm::InstCombinerImpl::run()
#6  combineInstructionsOverFunction(...)
#7  llvm::InstCombinePass::run(...)
#8  llvm::detail::PassModel<...>::run(...)
#9  llvm::PassManager<...>::run(...)
#10 llvm::detail::PassModel<...>::run(...)
#11 llvm::ModuleToFunctionPassAdaptor::run(...)
#12 llvm::detail::PassModel<...>::run(...)
#13 llvm::PassManager<...>::run(...)
#14 LLVMRunPasses()
#15 gallivm_compile_module(...) at
    /usr/src/debug/mesa/24.0.7/src/gallium/auxiliary/gallivm/lp_bld_init.c:620
```

The complete bounded output is retained in
`$RECEIVER/evidence/flr0103-post-scene-present/gdb-r3/gdb-hit-serial.log`.
The GDB client detached after the first hit; no full all-thread backtrace,
guest `addr2line`, or unbounded log transfer was used.

### Runtime and marker evidence

- The guest process list showed one `flutter-auto` under one `gdbserver`; no
  duplicate application process was observed.
- Focused markers retained `FLUORITE_VK_PRESENT_ENTER`, successful submit
  return (`result=0`), present-call start, and queue-present entry. Later
  frame samples retained `started=false`.
- At the focused sample, `flutter-auto` RSS was `1135368 kB`.
- Guest memory sample: `MemTotal=2026992 kB`, `MemFree=19064 kB`,
  `MemAvailable=613292 kB`, `SwapTotal=0 kB`.
- The kernel still reported the previously observed separate-looking OOPS:

  ```text
  BUG: unable to handle page fault for address: 0000000091062750
  Oops: 0000 [#1] PREEMPT SMP NOPTI
  CPU: 0 PID: 749 Comm: FEngine::loop
  RIP: 0033:0x7fffee804541
  CR2: 0000000091062750
  ```

The normal entry and the later `isOrdered+1` OOPS were observed as separate
events. Same-invocation identity and corrupted-state causality remain
`UNKNOWN`.

## QMP visual evidence

- QMP PPM:
  `$RECEIVER/evidence/flr0103-post-scene-present/gdb-r3/gdb-outer-bt-late.ppm`
- PPM SHA-256:
  `e21b04cb75d5289637a704cc0390b997a26996eb60311f2541d90bd95d2e6fca`
- Resolution: `1280x800`
- Native candidate region `[300,80,620,360]`: `0/223200` changed pixels;
  bounding box `null`
- Focused HUD region `[200,100,400,250]`: `1218/100000` changed pixels;
  bounding box `[200,113,29,66]`
- Visual result: the Fluorite HUD, performance labels/graph, `Scenes` button,
  and bottom controls are visible; the central native 3D region is black.

The screenshot was captured through QMP and is retained on the Mini receiver;
no host-side display capture was used.

## Teardown evidence

The same QEMU instance was terminated through the QMP socket after capture:

```text
qmp=PASS capabilities=negotiated quit=accepted
cleanup=PASS residual_targets=0 residual_qmp=0
```

The final residual check found no `runqemu`, `qemu-system-x86_64`,
`gdbserver`, or `flutter-auto` process and the QMP socket was absent.

## Classification

- Normal LLVM entry: PASS
- First non-LLVM producer: PASS — Mesa `gallivm_compile_module()`
- Later one-byte-offset OOPS reproduction: PASS
- Production native 3D pixels: FAIL (`0/223200`)
- 2D HUD pixels: PASS
- Root cause: UNKNOWN
- Source/image fix: not justified by this evidence unit

## Next gate

FLR-0107 will inspect the Mesa `gallivm_compile_module()` callsite and the
LLVM input/return boundary with static source evidence and one narrower
runtime observation. It must establish the expected operation and any
invalid input before a source patch is proposed.

## Source handoff

- Local commit: `7406dc63e164d9cccce3c872c416c0a8b369bb20`
- Bundle SHA-256:
  `564213c44be386bc3bddc9d4340ccb58b3a43c7e899e92cea63176f79710533e`
- Fixed Mini receiver revision: `7406dc63e164d9cccce3c872c416c0a8b369bb20`
- Existing build directory and TMPDIR were reused; no image rebuild was
  required for this documentation/evidence-only unit.
- An initial handoff attempt used a nonexistent inbox and stopped before
  transfer. The corrected fixed inbox accepted the same verified bundle.
