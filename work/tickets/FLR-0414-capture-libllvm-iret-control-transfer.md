# FLR-0414 — capture the live control transfer into `libLLVM+0xb1d541`

- Status: In Progress
- Priority: Critical
- Created: 2026-10-03
- Owner: Mini QEMU / ordinary Flutter Example Demo / guest GDB / QMP evidence
- Predecessor: [FLR-0413](FLR-0413-resolve-fengine-loop-page-fault-instruction.md)
- Candidate source ticket: [FLR-0410](FLR-0410-synchronize-event-callback-map.md)
- Candidate runtime evidence: [FLR-0410-0001](../evidence/FLR-0410-0001.md)
- Working log: [FLR-0414 working log](../logs/2026-10-03-flr0414.md)

## Work unit

On the exact existing FLR-0410 candidate (rootfs SHA-256
`f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08`), make
one bounded ordinary Example Demo run and arm a hardware breakpoint at the
mapped `libLLVM.so.18.1` address for ELF VMA `0xb1d541`. Capture the live
instruction, registers, caller, accelerator, same-run present/kernel state,
and full-screen QMP evidence before teardown. No product edit, build, cache
operation, diagnostic scene/material, input suppression, or present bypass.

This is a fault-boundary discriminator, not a visual/product acceptance run.
If the breakpoint or capture cannot be established safely, fail closed, save
the reason, and do not silently change instrumentation or launch a second VM.

## Facts and inferences entering the run

- **Fact:** FLR-0410-0001's exact rootfs, loaded mapping, ELF Build-ID, file
  offset, and saved Oops bytes agree. RIP `0x7f1c3bd22541` maps to VMA
  `0xb1d541`; the byte there is the second byte of `ff cf`, i.e. bare `CF`.
- **Fact:** Intel defines bare `CF` in 64-bit mode as IRETD (32-bit operand
  size); IRETQ requires REX.W. Exact QEMU 8.2.7 TCG source routes this form
  through the 32-bit stack-read path.
- **Inference:** If TCG ran with CS.L=1 and a flat SS cache with B=1, truncating
  RSP `0x00007f1bd9486750` to 32 bits yields the observed CR2
  `0x00000000d9486750`. The previous run did not capture those runtime
  conditions.
- **UNKNOWN:** What control transfer entered `isOrdered+1`, whether the same
  Oops recurs on the exact candidate, and whether either event caused the
  unmatched present or missing pixels.

## Competing hypotheses

1. **The exact QEMU TCG IRETD helper explains the immediate CR2.** Prediction:
   a hit at `+0xb1d541` has the saved register shape, and same-run guest/QEMU
   evidence confirms TCG plus compatible long-mode/SS state; if it continues,
   the first fault reports the corresponding stack read. Falsifier: different
   accelerator, effective address, or faulting instruction.
2. **The immediate emulation path is compatible, but upstream control flow is
   corrupt or unexpected.** Prediction: the hardware breakpoint captures an
   indirect branch/return into the middle of `dec %edi`, with a caller or
   predecessor inconsistent with a legitimate LLVM return. Falsifier: a
   defensible valid control-flow path reaches the address.
3. **The static Oops lacks enough context or does not recur on this candidate.**
   Prediction: the bounded run misses the address or terminates at a different
   fault while exact PID/image identity remains verified. Falsifier: one
   identity-bound hit and subsequent same-boundary fault.

## Plan / Do / Check / Act

### Plan

1. Re-run the canonical guard and verify the sole-ticket state. Read the
   existing Mini handoff/build/runtime procedure and exact 0410 artifact hashes;
   do not sync branches, transfer a new bundle, or invoke BitBake.
2. Before any launch, inspect Mini process argv/ancestry, BitBake ownership,
   ports, QMP sockets, current candidate paths, and run-directory state. If any
   existing task owns QEMU/build/evidence resources, do not touch them.
3. Reuse only the exact `f8ed8f11…` candidate and established Mini `runqemu`
   QMP-first procedure, with one fresh run ID `flr0414-0001`, one QEMU, the
   ordinary Example Demo as UID 1001, and one shared guest-log destination.
4. Query the active accelerator using the QEMU monitor/QMP path. Bracket the
   app PID, UID, `/proc` start token, loaded libLLVM Build-ID/map, READY state,
   and present/fault counters.
5. Resolve runtime address from the live mapping and set exactly one **hardware**
   breakpoint at `libLLVM base + 0xb1d541`. Require GDB to report hardware
   insertion. On hit, preserve `RIP`, `R10`, `RSP`, `RFLAGS`, `CS`, `SS`,
   instruction bytes/disassembly, short backtrace, and thread identity. If
   supported without a second VM, capture QEMU's stopped-vCPU descriptor state
   and effective IRET stack address. Never substitute a software breakpoint.
6. Capture a complete QMP still and short QMP-only video while the app is live,
   then preserve the first Oops/present state before stopping the exact app and
   QEMU. If the breakpoint hit changes run progress, record that instrumentation
   boundary; do not call it a product pass.
7. Hash only the selected run artifacts and close with exact app/QEMU/port/socket
   cleanup checks. No automatic retry under this ticket.

### Success criteria

- [ ] Preflight proves there is no competing Mini build/QEMU/runtime owner; the
  exact candidate identity is verified before launch.
- [ ] One ordinary UID-1001 Example Demo run is bracketed by exact process and
  image identities; active accelerator is captured or explicitly UNKNOWN.
- [ ] Hardware-breakpoint insertion is verified. Record either a live hit with
  its caller/register/instruction context or a bounded miss and exact stopping
  boundary. No software-breakpoint fallback.
- [ ] Full-screen live QMP still and short video are saved even if the run is
  unhealthy; pixels are classified from the full frame, not inferred from logs.
- [ ] The first guest Oops, present counters, app/thread lifecycle, and QEMU
  state share a run identity and one log destination; observer failure and
  product failure are distinguished.
- [ ] QEMU, app, ports, QMP socket, and handoff receiver pass exact postflight;
  selected evidence hashes and commands/results are in this log and manifest.
- [x] Run canonical, privacy, checkpoint, markdown-link and diff checks; the
  known 11 historical missing targets may remain, but no new FLR-0413/0414 or
  evidence link is broken. Commit only the FLR-0413 closeout transition,
  FLR-0414 ticket/log and TASKS state locally, with no push.

### Do

- Pending live run. No QEMU/build/process operation has yet been performed
  under FLR-0414.

### Check

- A GDB stop, process liveness, READY, or matching register values alone do not
  pass Sequoia pixels, HUD composition, depth, input/repaint, five-minute, or
  two-boot gates. Those remain product acceptance conditions.

### Act

- If the address is hit, use the predecessor and same-run signal/stack evidence
  to choose one next process boundary; do not yet patch Filament, LLVM, Mesa, or
  QEMU by correlation alone.
- If it is not hit or the app faults elsewhere, preserve that as a bounded
  negative result and compare with prior exact-image evidence before opening a
  new ticket. No same-ticket retry or candidate build.
- Product goal remains open until the full final-image acceptance matrix passes.

## Evidence location

- Mini raw evidence: `$BUILD_EVIDENCE/flr0414-0001/qemu/`
- Local review artifacts: one `work/evidence/FLR-0414-0001/` child directory;
  QMP PPM and logs on Mini remain authoritative.
- No rootfs, kernel, VM disk, credentials, personal account, IP, or hostname in
  Git.
