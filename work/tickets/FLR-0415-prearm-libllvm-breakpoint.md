# FLR-0415 — pre-arm the libLLVM hardware breakpoint before ordinary rendering

- Status: In Progress
- Priority: Critical
- Created: 2026-10-03
- Owner: guest GDB / UID-1001 Example Demo / Mini QEMU / QMP evidence
- Branch: `feature-flr-0415-prearm-libllvm-breakpoint`
- Predecessor: [FLR-0414](FLR-0414-capture-libllvm-iret-control-transfer.md)
- Candidate baseline: [FLR-0410-0001](../evidence/FLR-0410-0001.md)
- Prior run: [FLR-0414-0001](../evidence/FLR-0414-0001.md)
- Working log: [FLR-0415 working log](../logs/2026-10-03-flr0415.md)

## Work unit

Use the unchanged FLR-0410 image and ordinary Example Demo profile to capture
the first execution of `libLLVM.so.18.1` ELF VMA `0xb1d541`. First perform
bounded, read-only checks that the exact guest GDB can script Python, catch the
target library load, and resolve the exact ELF/mapping. If those pass, start
`flutter-auto` as GDB's inferior from process start, catch the target DSO load,
verify its Build-ID and PT_LOAD/live-map relationship, insert and verify one
hardware breakpoint, then continue once until the first hit or a bounded stop.
On the first hit, save registers, bytes, stack, thread identity, app log, and a
full QMP frame/video, then leave the inferior stopped for capture and teardown.

This is a single diagnostic unit, not a product fix or visual acceptance run.
No source/image edit, build, cache operation, scene/material/camera override,
input suppression, present bypass, ordinary-launch fallback, or software
breakpoint fallback is permitted. If a prerequisite or hardware insertion
fails, preserve the exact failure and stop without restarting the guest.

## Facts, inference, and UNKNOWN

- **Fact:** FLR-0414-0001 used rootfs SHA-256
  `f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08`.
- **Fact:** ordinary Example Demo UID 1001 launched. QMP showed the Flutter
  CPU/GPU/FPS HUD and Scenes button; the defined 3D ROI was uniformly black.
- **Fact:** present counters were begin/return/success `1/0/0`. A page fault
  followed by an `FEngine::loop` Oops occurred at RIP
  `0x7fbf96e39541`, mapping to ELF VMA `0xb1d541` in guest libLLVM Build-ID
  `359c1108040bc6bc1af64bb639d0b25385858051`.
- **Fact:** no GDB process or hardware breakpoint was started before that Oops.
  The later command only resolved the live map/address after the fault.
- **Inference:** GDB-owned app startup plus a pre-run load catchpoint can close
  the sequencing gap if the exact guest GDB supports the required commands.
- **UNKNOWN:** guest GDB's Python support/dependencies and load-catchpoint
  behavior; whether hardware insertion succeeds; whether the target address is
  reached again; the preceding transfer; and primary cause across Fluorite,
  LLVM, Mesa, QEMU/TCG, or guest kernel.

## Competing hypotheses

1. **A pre-run library-load catchpoint permits a verified hardware breakpoint
   before the target VMA's first hit.** Prediction: GDB stops at the target
   DSO load, Build-ID/PT_LOAD/mapping checks pass, and `hbreak` is inserted
   before execution resumes. Falsifier: required guest GDB capability is
   absent, the mapping is inconsistent, or hardware insertion fails.
2. **The exact candidate reaches the same address under GDB.** Prediction: the
   hardware breakpoint stops at runtime `load_bias + 0xb1d541` with the same
   Build-ID and an attributable PID/UID/start identity. Falsifier: a different
   first fault, clean bounded timeout, or no hit while exact identities remain
   intact.
3. **Debugger instrumentation changes ordering or suppresses the prior fault.**
   Prediction: under the same image and ordinary launch environment, present
   and fault ordering differs from FLR-0414-0001. One instrumented run cannot
   prove causality; any difference remains a timing correlation.

Sol's judgment-only review prefers GDB-owned launch plus an in-GDB load
catchpoint/Python calculation over an external interactive FIFO. It requires
Build-ID and PT_LOAD/mapping validation, verified hardware insertion, and no
automatic continue at the first hit. The review does not assign a product or
emulator root cause.

## Plan / Do / Check / Act

### Plan

1. Run the repository guard; confirm FLR-0415 is the sole In Progress ticket;
   record branch/revision and verify the inherited FLR-0410 candidate identity.
2. Before QEMU, inspect the exact candidate rootfs read-only for GDB version and
   configure/build features, Python runtime/dependencies, load-catchpoint
   command support, libLLVM Build-ID, and PT_LOAD layout. Validate the mapping
   calculation against the recorded FLR-0414 map and static ELF facts. If a
   prerequisite is absent or cannot be established without a boot, stop before
   QEMU and record UNKNOWN precisely.
3. Immediately before runtime, verify no Mini QEMU/runqemu/flutter-auto/
   BitBake owner, used port/QMP socket, or conflicting evidence directory.
   Re-hash the exact rootfs/kernel/qemuboot inputs; do not build or transfer a
   bundle.
4. Use one QMP-first Mini run and a fresh ID `flr0415-0001`. Start GDB as UID
   1001 with the same ordinary environment and Example Demo bundle. Set the
   exact `catch load` before `run`; at the stop, verify the mapped path and
   Build-ID, calculate load bias from ELF PT_LOAD plus live map offset, and
   prove the target is inside the matching executable mapping.
5. Insert exactly one hardware breakpoint at `load_bias + 0xb1d541`. Require
   positive insertion evidence and fail closed on any software-breakpoint
   substitution or insertion error. Continue once. On the first hit, save
   `RIP/R10/RSP/EFLAGS/CS/SS`, instruction bytes/disassembly, a bounded stack,
   TID/LWP, PID/UID/start token, present/kernel state, and complete QMP still
   plus short QMP-only video. Do not auto-continue after the hit.
6. If the app Oopses/exits, the breakpoint misses, or a timeout occurs, save
   the exact first boundary and do not relaunch within this ticket. Stop only
   the recorded GDB/app/QEMU identities, send QMP `quit`, and verify processes,
   ports, sockets, and candidate hashes.
7. Record evidence hashes and PDCA. Preserve product rendering goal as open;
   create a new ticket only if the captured boundary identifies a distinct
   next work unit.

### Success criteria

- [ ] Read-only preflight identifies guest GDB version/features, Python support
  and runtime dependency state, target load-catchpoint support, exact libLLVM
  Build-ID/PT_LOAD, and a deterministic address calculation. No QEMU starts if
  an essential prerequisite is UNKNOWN or FAIL.
- [ ] One owner-free Mini QEMU run reuses the exact FLR-0410 rootfs, kernel,
  qemuboot, ordinary UID-1001 environment, and Example Demo bundle; identity
  is recorded before and after.
- [ ] GDB is the ordinary app's parent from launch. The target DSO load catch
  is set before `run`; exact path/Build-ID and PT_LOAD/live mapping agree.
- [ ] Hardware insertion at the computed `load_bias+0xb1d541` is directly
  verified before continuing. No software breakpoint or plain unverified
  breakpoint is accepted.
- [ ] First target hit or bounded failure is captured with exact registers,
  bytes, stack, thread, PID identity, same-run present/kernel evidence, and a
  full QMP still/video. First hit remains stopped after capture.
- [ ] One-run cleanup passes for the exact app/GDB/QEMU identities, ports,
  QMP socket, and candidate artifact hashes.
- [ ] Facts/inferences/hypotheses/UNKNOWN and command results are recorded in
  this ticket/log/manifest; canonical, privacy, checkpoint, link, and diff
  checks pass or retain only the known historical broken-link set.

### Do

- Read-only capability preflight is pending. No FLR-0415 Mini command, QEMU,
  source edit, build, or artifact transfer has run.

### Check

- Breakpoint capture is diagnostic only. A load catch, GDB stop, process
  liveness, or matching RIP is not product rendering success.
- Product gates remain: original Sequoia texture/material/light, same-frame
  HUD+Sequoia, view/depth/occlusion, input/repaint stability, five minutes of
  advancing present, and two independent boots on the same final image.

### Act

- If a hit is captured, use its same-run stack/register/map evidence to select
  one next process boundary; do not patch a layer based on address correlation
  alone. A breakpoint hit does not guarantee reconstruction of the preceding
  control transfer.
- If preflight or insertion fails, preserve exact command/output and stop this
  run safely. Do not retry with ordinary startup, another debugger mechanism,
  or a second VM under the same ticket.
- Only evidence that points to a controllable product boundary may justify a
  minimal Devtool source change. The overall product goal remains open.

## Visual evidence

Required QMP-only full-screen still and short video are evidence of the state
at the GDB load stop, target breakpoint hit, or first bounded failure. State
what is visibly present, image/run identity, fixed ROI pixel summary and hash.
Keep raw PPM/logs on Mini; local PNG/MP4 previews may be ignored by Git and
linked from the evidence manifest. This diagnostic capture cannot satisfy Gate
A or Gate B.

## Out of scope

- Any patch, build, bundle transfer, or cache invalidation.
- Any Sequoia material, texture, lighting, camera, scene, input, repaint,
  compositor, or present modification.
- Claiming LLVM/QEMU/Mesa/Filament root cause from a matching fault address.
