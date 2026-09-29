# FLR-0338 — capture control-flow context at `isOrdered+1`

- Status: Done
- Priority: High
- Owner: production FEngine / LLVM caller-context diagnosis roles
- Created: 2026-09-28
- Predecessor: [FLR-0337](FLR-0337-capture-user-and-kernel-fault-trace.md)
- Working log: `work/logs/2026-09-28-flr0338.md`

## Problem

### Purpose

FLR-0337 captured the recurring `exceptions:page_fault_user` event on the
same TID and at the same IP/address as the FEngine Oops. The IP maps to
`libLLVM.so.18.1` file offset `0xb1d541`, `llvm::CmpInst::isOrdered+1`.
Historical FLR-0335 GDB disassembly at this exact image offset decoded the
byte at `+1` as `iret`, while FLR-0106 captured the normal function entry at
`+0` as the two-byte instruction `dec %edi` in an InstCombine/Gallivm stack.
The recurring RIP merits a pre-instruction capture, but does not yet prove
malformed control flow or identify the producer.

### Success measure

Use one bounded GDB run with a single hardware execution breakpoint at the
ASLR-adjusted address corresponding to file offset `0xb1d541`. If it hits,
capture the exact TID, registers, nearby instructions, and a bounded caller
stack before the target instruction executes. If it does not hit or hardware
breakpoints are unavailable, retain the bounded failure evidence and stop.
Capture a full QMP frame/short sequence and leave zero app/QEMU residue.
Make no product patch in this ticket.

### Facts / inferences / hypotheses

- **Facts:** FLR-0337 captured a matching same-TID user-fault/Oops pair at
  `isOrdered+1`; FLR-0335 GDB disassembled the same exact image offset as
  `iret`; FLR-0106 captured normal `isOrdered+0` entry as `dec %edi` and a
  caller chain through LLVM InstCombine and Mesa Gallivm.
- **Inference:** the reported RIP is one byte into the instruction beginning
  at the normal function entry. This is an instruction-boundary anomaly, not
  proof that LLVM itself produced it.
- **Hypothesis 1:** the FEngine thread reaches the second byte and would
  execute `iret`; prediction: the hardware breakpoint stops at the exact
  offset before the Oops and yields a caller/register state.
- **Hypothesis 2:** the kernel Oops carries saved/context RIP rather than the
  actual faulting operation; prediction: the hardware breakpoint does not
  trigger and the kernel/user event path differs or the TID exits first.
- **Hypothesis 3:** debugger attachment changes timing enough to avoid the
  fault. Prediction: bounded wait expires without a hardware-breakpoint hit;
  classify this as inconclusive, not as a fix.

## 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | FEngine user page fault/Oops at `libLLVM+0xb1d541` | FLR-0337 fault-window trace |
| Where | Fixed Mini QEMU guest; production Example Demo; llvmpipe/LLVM | Same image hashes as FLR-0335/0337 |
| When | About 29 seconds after the app starts in FLR-0337 | Guest monotonic journal and launch marker |
| Who | One `FEngine::loop` TID within the surviving `flutter-auto` process | Matching TID 703 user event and Oops |
| How | One-byte-offset RIP at the second byte of the normal function-entry instruction | Historical FLR-0335 and FLR-0106 disassembly |

## Scope and controls

### In scope

- Reuse the exact FLR-0335/0337 rootfs, qemuboot, kernel, build/TMPDIR,
  no-GDB production app profile, and 6144-MiB QEMU harness.
- Derive the ASLR-adjusted runtime address from the live process's
  `/proc/<pid>/maps` entry for `/usr/lib/libLLVM.so.18.1` and the known file
  offset `0xb1d541`; verify the resulting address maps to the expected file.
- Use **only a hardware execution breakpoint** at that address. A software
  breakpoint would overwrite byte `0xcf`, which is also part of the prior
  instruction's encoding, and is prohibited.
- Bound the GDB wait to 45 seconds. Record hit/timeout status and immediately
  detach/stop the exact guest app and QMP VM; do not leave a surviving parent
  running after its worker faults.
- Keep raw GDB/serial evidence on the Mini and retain a QMP-only full frame
  and eight-frame replay.

### Out of scope

- Editing LLVM, Mesa, Filament, Flutter, shader, material, texture, light,
  camera, kernel, recipe, layer, or system configuration.
- Devtool, patch creation, bundle transfer, BitBake, image rebuild, broad
  `strace`, or an unbounded all-thread GDB dump.
- Software breakpoints, second simultaneous QEMU, new build/TMPDIR/cache, or
  copying the QEMU disk image to Mac.

## PDCA

### Plan

1. Run the canonical guard; confirm FLR-0338 is the sole In Progress ticket
   and the previous QEMU/app/socket residue is zero.
2. Upload the committed start, one-line guest commands, and orchestration
   script to one new Mini evidence parent; do not transfer an image. Every
   attempt gets a unique `flr0338-NNNN` run ID, and existing evidence is never
   reused or overwritten.
3. Run `FLR-0338-run-hardware-breakpoint.sh flr0338-NNNN`. It revalidates all
   three fixed image hashes and guest debugger/library availability before
   app launch, then starts one QEMU and the production profile.
4. Derive the live breakpoint address from `/proc/<pid>/maps`; reject a
   missing/ambiguous mapping. Set only the hardware breakpoint and capture
   the breakpoint TID, registers, `x/8i $pc-4`, and `bt 16`.
5. Bound the debugger wait to 45 seconds; capture QMP full frame and eight
   frames, analyze the lower 3D ROI, and collect only selected app/Oops lines.
6. The runner's EXIT trap stops the exact debugger/app and QMP VM; require
   zero residual runtime processes/socket before accepting the run. The
   hardware-breakpoint startup handshake is bounded to 12 seconds; an active
   attach is treated as pending and observed by the 45-second poll, not failed
   merely because GDB has not printed its breakpoint line after one second.

### Check

| Criterion | Expected | Actual | Result |
| --- | --- | --- | --- |
| Canonical repo / one active ticket | PASS | Guard passed; FLR-0338 sole active ticket | PASS |
| Image hashes and debugger preflight | Exact existing image; debugger/library available | Exact FLR-0335 image; GDB 14.2 and expected library hash | PASS |
| Bounded hardware-breakpoint outcome | Exact hit context or a bounded no-hit result with the breakpoint demonstrably armed | Run 0003 armed at `0x7fd2cc71d541`, matching the ASLR-adjusted `libLLVM+0xb1d541` address; no stop PC within 45 seconds (`timeout` 124) | PASS for bounded no-hit outcome; target execution UNKNOWN |
| QMP | HUD/3D full-frame evidence and eight-frame sample | Run 0003 HUD/metrics/Scenes visible; lower ROI `(0,200,1280,600)` is 768,000 black pixels; all eight frames have one identical QMP hash; PNG/video retained | PASS for capture; 3D NOT SHOWN |
| Runtime correlation | Report bounded draw/present/Wayland state without causal overclaim | 19 draw-end and 19 native commits; one queue-present begin/enter; zero return/done; Sequoia asset/emissive binding and magenta override markers reached | PASS for bounded observations; fault/present causality UNKNOWN |
| Cleanup | Exact app stopped; QMP quit; zero processes/socket | App count 0; QMP quit accepted; Mini residual targets/socket 0 | PASS |

### Act

- The corrected run demonstrably inserted the hardware breakpoint at the
  expected address, serialized the complete bounded GDB transcript, and
  reached its 45-second no-hit timeout. This satisfies this ticket's explicit
  bounded hit-or-no-hit measure; it does not prove the address is never
  executed or that the Oops RIP is contextual.
- Close this narrow breakpoint experiment without a source change. FLR-0339
  now owns a different discriminator: one short all-thread GDB snapshot after
  `FLUORITE_VK_QUEUE_PRESENT_ENTER` persists with no return.
- The 3D acceptance criterion remains open. Asset/emissive readiness and the
  magenta-unlit override marker do not prove shader execution or visible
  pixels; no Light/texture/camera conclusion is made here.

## Unknowns

- Which caller/control-flow producer places the thread at `isOrdered+1`.
- Whether the faulting thread attempts an `iret` from the second byte or the
  saved RIP is contextual.
- Whether this fault causes the missing queue-present return/native buffer
  publication.

## PDCA checker

- Status: PASS for the bounded hit-or-no-hit objective; target execution and root cause remain UNKNOWN
- Checked by: FLR-0338 run 0003 transcript, QMP screenshot/video, cleanup evidence, and repository verification
- Findings: hardware breakpoint was armed at the exact image-relative address but did not stop within 45 seconds; present-enter/no-return remains the more actionable next boundary. No source patch/build is justified.
