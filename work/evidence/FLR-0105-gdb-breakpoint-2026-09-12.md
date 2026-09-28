# FLR-0105 evidence — bounded LLVM-entry breakpoint (2026-09-12)

## Outcome

The production process entered `llvm::CmpInst::isOrdered` normally. A single
bounded GDB breakpoint captured the entry instruction, registers, and eight
frames, then detached. The captured frames remained inside LLVM's InstCombine
path. About 265 seconds later, a different `FEngine::loop` thread reported an
OOPS at the next byte (`isOrdered+1`). This proves that the symbol is normally
called but does not prove that the normal call produced the later corrupted
control flow. Production 3D remains unresolved.

## Runtime identity

- Image role: FLR-0104 debug image
- Rootfs SHA-256:
  `368662e10eb6710123f45f94b7fa940a5c93d20d09633b88f3c1c3f128e7863c`
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Qemuboot SHA-256:
  `ba6711550d96677f66e99f3a06af308a61c1e58a7b776f7489b42c8cc470136d`
- QMP evidence role:
  `$RECEIVER/evidence/flr0103-post-scene-present/gdb-r2/`
- QEMU contract: one instance, preflight/start/guest-ready PASS, QMP-only
  capture, QMP quit PASS, residual target processes `0`, residual QMP sockets
  `0`.

## GDB entry evidence

The client first registered a pending breakpoint for
`llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)`. It then captured:

```text
FLR0105_GDB_BREAKPOINT_HIT pc=0x7fffee804540
=> 0x7fffee804540 <...isOrdered...>: dec %edi
FLR0105_REGS rip=0x7fffee804540 rsp=0x7fffed2b1328 rdi=0xc rsi=(nil) rdx=0x5 rcx=(nil)
#0 llvm::CmpInst::isOrdered(...)
#1 matchSelectPattern(...)
#2 llvm::matchDecomposedSelectPattern(...)
#3 llvm::matchSelectPattern(...)
#4 llvm::InstCombinerImpl::visitFCmpInst(...)
#5 llvm::InstCombinerImpl::run()
#6 combineInstructionsOverFunction(...)
#7 llvm::InstCombinePass::run(...)
```

The breakpoint was disabled after the first hit and GDB detached. No full
all-thread backtrace or guest-side `addr2line` was run during this observation.

## Later fault and runtime state

- Kernel OOPS: approximately 265 seconds after boot; `PID: 715 Comm:
  FEngine::loop`; RIP `0x7fffee804541`; CR2 `0x0000000091062750`.
- The fault RIP is one byte after the normal breakpoint entry. The normal
  entry and later OOPS are different observed events; same-invocation identity
  is UNKNOWN.
- At the focused post-hit sample, `flutter-auto` RSS was `1139220` kB; guest
  `MemAvailable` was `609180` kB and swap was disabled.
- The production frame stream reached a valid first frame but later emitted
  frame begin/draw-event/return records with `started=false`.

## QMP visual evidence

- QMP PPM: `gdb-breakpoint-late.ppm`
- PPM SHA-256:
  `3da26a6795d446e4918debab57d1b7a1aaeb6441f0ff32267ea1f3d04a2e539e`
- Resolution: `1280x800`
- Native candidate region `[300,80,620,360]`: `0/223200`, no bounding box
- HUD region `[200,100,400,250]`: `1250/100000`, bbox `[200,113,29,66]`
- Visual result: Fluorite HUD, FPS/CPU/GPU/Script/system-delay graph,
  Scenes button, and bottom controls are visible; the central 3D region is
  entirely black.

## Failed or corrected observations

- The first status collection used an incomplete receiver path and failed to
  create its output file. It did not execute the guest command and did not
  affect QEMU. The corrected full receiver path succeeded on the same QEMU.
- The breakpoint-only run avoided the separate OOM caused by the prior
  guest-side `addr2line` extraction. Memory pressure is retained as a runtime
  risk, not a root-cause conclusion.

## Classification

- Normal LLVM symbol entry: PASS
- Outer producer above LLVM: UNKNOWN; eight-frame sample ends inside LLVM
- Later one-byte-offset OOPS: PASS as reproduced evidence
- Production native 3D pixels: FAIL (`0/223200`)
- 2D HUD pixels: PASS
- Product fix: not justified by this evidence unit
