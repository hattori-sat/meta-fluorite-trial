# FLR-0414 — capture the live control transfer into `libLLVM+0xb1d541`

- Status: Waiting — the live run reproduced the page fault before GDB or the planned hardware breakpoint was started; follow-up is [FLR-0415](FLR-0415-prearm-libllvm-breakpoint.md)
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
   Use the ticket-scoped, syntax-checked guest commands in
   `work/commands/FLR-0414-guest-launch.cmd`,
   `work/commands/FLR-0414-guest-gdb-prepare.cmd`,
   `work/commands/FLR-0414-guest-hwbp.cmd`,
   `work/commands/FLR-0414-guest-evidence-export.cmd`, and
   `work/commands/FLR-0414-guest-stop.cmd`; pin the current committed QMP
   helpers inside this run's evidence directory, not in the build receiver.
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

- [x] Preflight proved there was no competing Mini build/QEMU/runtime owner; the
  exact candidate identity is verified before launch.
- [x] One ordinary UID-1001 Example Demo run is bracketed by exact process and
  image identities; QMP recorded KVM disabled, while TCG remains an inference.
- [ ] Hardware-breakpoint insertion and live hit/miss boundary are verified.
  The Oops happened before GDB was started, so this criterion failed; no
  software-breakpoint fallback was attempted.
- [x] Full-screen live QMP stills and short videos are saved even though the run
  was unhealthy; pixels are classified from the full frame, not inferred from logs.
- [x] The first guest Oops, present counters, app/thread lifecycle, and QEMU
  state share a run identity and one log destination; observer failure and
  product failure are distinguished.
- [x] QEMU, app, ports, QMP socket, and handoff receiver pass exact postflight;
  selected evidence hashes and commands/results are in this log and manifest.
- [x] Run canonical, privacy, checkpoint, markdown-link and diff checks; the
  known 11 historical missing targets may remain, but no new FLR-0413/0414 or
  evidence link is broken. Commit only the FLR-0413 closeout transition,
  FLR-0414 ticket/log, evidence manifest, and TASKS state locally, with no push.

### Do

- One Mini `runqemu` instance ran the ordinary Example Demo on the exact
  FLR-0410 rootfs/kernel/qemuboot hashes recorded in the evidence manifest.
  Guest PID 646, UID 1001, start token 8925 passed the launch identity gate.
- The QEMU 8.2.7 QMP monitor reported `query-kvm: enabled=false,present=true`;
  TCG is inferred from the default because no explicit accelerator was named.
- Before debugger startup, QMP captured the complete 1280×800 frame and eight
  frames. The CPU/GPU/FPS HUD and Scenes button are visible; the 3D ROI
  `(x=0..1279, y=200..799)` is exactly black (768,000/768,000 pixels). All
  sixteen pre-/post-Oops review frames share SHA-256
  `d6293e5f4d1ed369e246fc836a4d917223627d6f42fe2b2abfcfa343656bc02f`.
- Present counters at the first fault: begin/return/success `1/0/0`; 53 shape
  readiness markers had appeared. At uptime 119.913246 the page fault began;
  the Oops was recorded at 119.915315 in TID 697 (`FEngine::loop`). RIP and
  R10 were `0x7fbf96e39541`, RSP `0x00007fbf38ad3750`, CR2
  `0x0000000038ad3750`, EFLAGS `0x217`. The runtime executable map and exact
  Build-ID resolve RIP to ELF VMA `0xb1d541`, whose bytes begin `cf 83 ff 07`.
- No GDB process was launched and no hardware breakpoint was inserted. A
  read-only post-Oops map preparation command resolved the matching runtime
  address only after the fault; it cannot recover the transfer that preceded
  the first hit.
- The post-Oops frame still shows HUD over a black 3D region and is identical
  to the pre-Oops frame. This is a real negative 3D observation, not a fully
  black-screen claim and not a successful Sequoia/material/lighting result.
- Exact app stop, negotiated QMP quit, harness cleanup, and independent
  postflight passed. Candidate hashes were unchanged. No build, bundle
  transfer, product edit, cache operation, or second QEMU run occurred.

### Check

- **Runtime result: FAILED for the planned control-transfer capture.** The
  fault recurred, and same-run RIP/Build-ID/map/CR2 evidence was obtained, but
  the hardware breakpoint was never armed because the app was launched first
  and faulted before GDB startup. The missed breakpoint is an observer/sequence
  failure; it does not prove the page fault's cause.
- QMP proves the HUD is visible while the 3D region is black on this exact
  candidate. It does not prove why 3D is black. Root cause across Filament,
  LLVM, Mesa, QEMU/TCG, or guest kernel remains UNKNOWN.
- A GDB stop, process liveness, READY, or matching register values alone do not
  pass production Sequoia pixels, depth, input/repaint, five-minute progressing
  present, or two-boot gates. Those remain open.

### Act

- Close this work unit as Waiting with the exact failed boundary recorded. Do
  not spend time on a post-fault breakpoint attempt in the same run.
- [FLR-0415](FLR-0415-prearm-libllvm-breakpoint.md) starts the ordinary app as
  a GDB inferior, catches the exact libLLVM load, validates Build-ID and
  PT_LOAD/mapping arithmetic, then inserts a hardware breakpoint before
  continuing. It first performs bounded read-only capability checks and fails
  closed if the required GDB support is absent.
- No Filament, LLVM, Mesa, QEMU, or guest-kernel product patch is justified by
  this run alone.
- Product goal remains open until the full final-image acceptance matrix passes.

## Evidence location

- Mini raw evidence: `$BUILD_EVIDENCE/flr0414-0001/qemu/`
- Local review artifacts: one `work/evidence/FLR-0414-0001/` child directory;
  QMP PPM and logs on Mini remain authoritative.
- [FLR-0414-0001 evidence manifest](../evidence/FLR-0414-0001.md) indexes the
  hashes, pixel result, selected logs, and QMP visual proof.
- No rootfs, kernel, VM disk, credentials, personal account, IP, or hostname in
  Git.
