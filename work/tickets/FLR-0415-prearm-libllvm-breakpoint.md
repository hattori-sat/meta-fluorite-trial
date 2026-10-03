# FLR-0415 — pre-arm the libLLVM hardware breakpoint before ordinary rendering

- Status: Waiting
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
- **Fact:** read-only inspection of the exact FLR-0410 rootfs found
  `/usr/bin/gdb` (11,697,224 bytes), a `libpython3.12.so.1.0` dependency and
  matching runtime library, and embedded `catch load [REGEX]` support text.
- **Fact (FLR-0415-0001):** the unchanged FLR-0410 rootfs/kernel/qemuboot
  passed the Mini preflight; guest GDB 14.2's Python command and load
  catchpoint passed before the single UID-1001 Example Demo launch.
- **Fact:** guest PID 776, UID 1001, start token 123232 loaded the expected
  libLLVM Build-ID
  `359c1108040bc6bc1af64bb639d0b25385858051`. PT_LOAD/live mapping and
  load-bias arithmetic resolved VMA `0xb1d541` to
  `0x7fffefb4d541`; GDB confirmed a hardware-assisted breakpoint there.
- **Fact:** the breakpoint hit on `FEngine::loop` LWP 818 inside
  `llvm::CmpInst::isOrdered()+1`. The GDB transcript contains RIP/R10/RSP/
  EFLAGS/CS/SS, instruction bytes/disassembly, threads, and a bounded stack.
  The caller return address `0x7fff89afc320` remains unsymbolized.
- **Fact:** at least one Vulkan queue-present call returned `result=0`;
  a second `FLR0026_VK_QUEUE_PRESENT_BEGIN` appears before the hit, with no
  matching result line in the saved transcript. The bounded dmesg comparison
  reported kernel fault baseline/current `0/0`.
- **Fact:** the breakpoint command's Python hit-marker formatting raised
  `TypeError: not all arguments converted during string formatting` after
  the diagnostic register/stack commands. No `-hit` marker or
  `FLR0415_RELEASE=TIMEOUT` line was recorded; the exact GDB/app exit path
  after the sourced-command error is UNKNOWN.
- **Fact:** QMP saved a full 1280×800 still and two eight-frame sequences.
  All observed frame hashes were
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`,
  visually uniform black. The guest/app/QMP capture times were not reliably
  bracketed, so these pixels are not a product-render verdict.
- **Fact:** read-only postflight SHA-256 checks after exact teardown matched
  the same FLR-0410 kernel, rootfs, and qemuboot artifacts recorded before
  startup; the diagnostic run did not mutate the candidate image.
- **Inference:** GDB-owned startup closed the earlier sequencing gap for this
  one run: the exact target instruction was reached with the verified
  hardware breakpoint armed. That does not prove LLVM is defective or caused
  the prior Oops.
- **Inference:** a guest-side observer formatting defect interrupted the
  planned first-hit hold. It is an instrumentation failure, not evidence of a
  product crash or renderer root cause.
- **UNKNOWN:** caller DSO/Build-ID and control flow for return address
  `0x7fff89afc320`; the exact relationship between successful queue-present
  calls and QMP pixels; whether any QMP still was captured while the inferior
  was still alive; the reason the visible framebuffer was black; and primary
  cause across Fluorite, LLVM, Mesa, QEMU/TCG, or guest kernel.

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
   command support, libLLVM Build-ID, and PT_LOAD layout. Fail before QEMU if
   the exact GDB or a required runtime dependency/catchpoint facility is
   missing. Static strings do not prove that GDB's Python command is active.
3. If static inspection leaves only runtime GDB/Python command support
   uncertain, test `gdb --version`, a short `python import gdb` command, and
   `help catch load` inside the **same single QEMU run**, before launching the
   app. If the smoke test fails, capture the result, skip Flutter, and tear
   down that same QEMU; never boot a second VM for the capability check.
4. Immediately before runtime, verify no Mini QEMU/runqemu/flutter-auto/
   BitBake owner, used port/QMP socket, or conflicting evidence directory.
   Re-hash the exact rootfs/kernel/qemuboot inputs; do not build or transfer a
   bundle.
5. Use one QMP-first Mini run and a fresh ID `flr0415-0001`. Start GDB as UID
   1001 with the same ordinary environment and Example Demo bundle. Set the
   exact `catch load` before `run`; at the stop, verify the mapped path and
   Build-ID, calculate load bias from ELF PT_LOAD plus live map offset, and
   prove the target is inside the matching executable mapping.
6. Insert exactly one hardware breakpoint at `load_bias + 0xb1d541`. Require
   positive insertion evidence and fail closed on any software-breakpoint
   substitution or insertion error. Continue once. On the first hit, save
   `RIP/R10/RSP/EFLAGS/CS/SS`, instruction bytes/disassembly, a bounded stack,
   TID/LWP, PID/UID/start token, present/kernel state, and complete QMP still
   plus short QMP-only video. Do not auto-continue after the hit.
7. If the app Oopses/exits, the breakpoint misses, or a timeout occurs, save
   the exact first boundary and do not relaunch within this ticket. Stop only
   the recorded GDB/app/QEMU identities, send QMP `quit`, and verify processes,
   ports, sockets, and candidate hashes.
8. Record evidence hashes and PDCA. Preserve product rendering goal as open;
   create a new ticket only if the captured boundary identifies a distinct
   next work unit.

### Prepared execution assets

- `work/commands/FLR-0415-qemu-start.sh` derives the exact run artifacts from
  the saved FLR-0414 runqemu command, checks their recorded hashes and fixed
  `qemux86-64` build context, then calls the committed QEMU harness. It uses
  one new evidence directory, ports 10940–10942, and 6144 MiB.
- `work/commands/FLR-0415-prearm-libllvm.gdb` performs the guest GDB-owned
  launch. It reads only ELF headers/program headers/PT_NOTE, verifies Build-ID
  and executable PT_LOAD against the live mapping, inserts one always-inserted
  hardware breakpoint, records the first stop, and waits for explicit host
  release without auto-continuing.
- `work/commands/FLR-0415-guest-gdb-smoke.cmd` gates Flutter startup. The GDB
  script is transferred through bounded, base64-aligned `serial-exec` chunks;
  the guest verifies its SHA-256 before launch. Serial inputs are one physical
  line and at most 4096 bytes.
- Guest snapshot/status/export/release/stop commands are ticket-scoped and
  identity checked. Full GDB output is transferred if bounded below the serial
  transcript cap; oversized output falls back to a focused, recorded tail. The
  QMP capture helper and QEMU harness are checksum-pinned before start. No
  product source, image, cache, or build state is changed.

### Success criteria

- [x] Read-only preflight identifies the exact rootfs GDB binary/dependency
  evidence, target load-catchpoint facility, exact libLLVM Build-ID/PT_LOAD,
  and deterministic address calculation. Any remaining Python-command
  uncertainty is checked in the same QEMU, before app launch; a missing static
  prerequisite stops before QEMU.
- [x] One owner-free Mini QEMU run reuses the exact FLR-0410 rootfs, kernel,
  qemuboot, ordinary UID-1001 environment, and Example Demo bundle; identity
  is recorded before and after.
- [x] GDB is the ordinary app's parent from launch. The target DSO load catch
  is set before `run`; exact path/Build-ID and PT_LOAD/live mapping agree.
- [x] Hardware insertion at the computed `load_bias+0xb1d541` is directly
  verified before continuing. No software breakpoint or plain unverified
  breakpoint is accepted.
- [ ] First target hit or bounded failure is captured with exact registers,
  bytes, stack, thread, PID identity, same-run present/kernel evidence, and a
  full QMP still/video. First hit remains stopped after capture.
- [x] One-run cleanup passes for the exact app/GDB/QEMU identities, ports,
  QMP socket, and candidate artifact hashes.
- [ ] Facts/inferences/hypotheses/UNKNOWN and command results are recorded in
  this ticket/log/manifest; canonical, privacy, checkpoint, link, and diff
  checks pass or retain only the known historical broken-link set.

### Do

- Read-only Mini rootfs inspection found the exact GDB binary, libpython
  dependency/runtime library, and `catch load [REGEX]` support text. Fresh
  Mini preflight rehashed the unchanged FLR-0410 rootfs/kernel/qemuboot and
  found no runtime/build owner, reserved-port conflict, or consumed run ID.
- One QEMU started from the exact candidate with 6144 MiB. The 16 transferred
  command/helper files matched their local SHA-256 values. No BitBake, build,
  source edit, cache action, bundle transfer, or image mutation occurred.
- The first serial-exec invocation used relative command/output paths; the
  harness rejected it before guest execution. The corrected absolute-path
  invocation passed. Guest GDB 14.2 reported Python support, accepted the
  `catch load` command, and passed the pre-app smoke. App and hardware
  breakpoint were explicitly NOT STARTED/NOT ATTEMPTED at that gate.
- The GDB script transferred through two aligned serial chunks and its guest
  SHA-256 matched source: `d6e2153b9e5d4018a2004d5258ec0291900d7c51080ed0f2733504b31227859f`.
- The first app launch guard returned `rc=1` because the guest install
  sentinel contained the literal two characters `\n` after the expected hash.
  It failed before recording the GDB/app identity. The sentinel formatter is
  corrected locally; the same QEMU is retained and no second instance is
  permitted. An updated guest check must prove no GDB/Flutter process before
  retrying this not-yet-started app launch once.
- Before Flutter launch, QMP captured the full 1280×800 frame and eight frames
  0.5 seconds apart. All 1,024,000 pixels were exact black and all eight
  samples had one hash (`d4e96a65…`). This is a pre-app/boot-state screenshot,
  not evidence about Flutter or the product scene.
- The corrected finalizer/status/launch command files were committed locally
  as `d07607e`, copied only into this existing run evidence directory, and
  matched their local SHA-256 values. The no-process gate initially passed
  while the old sentinel correctly failed; the fixed finalizer then returned
  `FLR0415_GDB_INSTALL=PASS`, and the complete prelaunch gate returned
  `FLR0415_PRELAUNCH=PASS_ready`.
- The single GDB-owned app launch returned
  `FLR0415_LAUNCH=PASS wrapper=758 gdb=763 uid=1001 kernel_fault_baseline=0`.
  Guest status confirmed Build-ID/map agreement and
  `Hardware assisted breakpoint 2 at 0x7fffefb4d541`.
- The bounded GDB log is 123,842 bytes. It records two Vulkan queue-present
  begins and one earlier `result=0`, then the target hit and formatting
  exception. Guest snapshot reports app identity EXITED and kernel
  fault baseline/current `0/0`; do not attribute that exit to a kernel Oops.
- The QMP observation still and eight frames had hash
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  The post-hit still and eight-frame sample were also uniform black with that
  hash. Because guest and Mini capture timestamps were inconsistent and
  process liveness was not bracketed around each capture, this does not prove
  a live product frame was black.
- Exact guest teardown reported `FLR0415_STOP=PASS exact_residual=none`.
  QMP quit was accepted and reported `cleanup=PASS residual_targets=0
  residual_qmp=0`. The recorded Mini runqemu/QEMU PIDs 3139225/3139252 and
  their start ticks 292522835/292522842 were absent afterward; QMP socket and
  ports 10940–10942 were clear. Postflight hashes matched kernel
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`,
  rootfs
  `f8ed8f1194d13175fe91676fba24cdd8d564a69deb58d1bc0b7d91a87faeef08`, and
  qemuboot
  `3872b66339ac3601c701f1b54cab5630796ccf5f0f95ebc4e7077210e89d107f`.
  Evidence remains on Mini; no image/build/cache data was transferred,
  modified, or deleted.

### Check

- Breakpoint capture is diagnostic only. A load catch, GDB stop, process
  liveness, or matching RIP is not product rendering success.
- The GDB breakpoint itself reached the target and the required register,
  instruction, stack, present, kernel, QMP, and teardown evidence was saved.
  The hit-marker Python exception means the first hit was not held through the
  planned explicit-release gate; criterion 5 remains incomplete.
- QMP evidence is visually black, but capture-time/process-state/present
  correlation is UNKNOWN. The prior GDB exception and later process exit do not
  establish a product-render failure or kernel Oops.
- Static closeout checks: canonical repository PASS, privacy PASS, and
  `git diff --check` PASS. Markdown link check reports the same 11 historical
  missing targets outside this ticket; no FLR-0415 link is among them. The
  ticket checkpoint is deferred until the successor is the sole In Progress
  item.
- Product gates remain: original Sequoia texture/material/light, same-frame
  HUD+Sequoia, view/depth/occlusion, input/repaint stability, five minutes of
  advancing present, and two independent boots on the same final image.

### Act

- The one FLR-0415 application launch is spent. Do not relaunch in this ticket.
  Keep this ticket Waiting for FLR-0416, which owns correction and offline
  validation of hit-marker construction plus a new bounded capture unit.
- Do not patch a layer from the target address or black QMP pixels alone.
  FLR-0416 must resolve the caller mapping and bracket captures with present,
  process, and clock evidence before selecting a product boundary.
- If static preflight fails, do not start QEMU. If the in-guest GDB smoke or
  insertion fails, do not launch/restart Flutter; save QMP evidence and stop
  the same recorded QEMU safely. A pre-inferior script/hash guard error may be
  corrected once after recording the cause, but must reuse the same QEMU and
  re-prove that no GDB/Flutter process started. Do not use ordinary startup,
  another debugger mechanism, or a second VM under this ticket.
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
