# FLR-0403 — correlate the FEngine Oops with its GDB LWP and present

- Status: Waiting
- Completion note: run completed; required LWP/ELF correlation not obtained
- Priority: High
- Created: 2026-10-02
- Owner: Mac observer/test source / Mini QEMU / guest Flutter+GDB / QMP and kernel evidence roles
- Branch: `feature-flr-0403-oops-lwp-present-correlation` (dependent on the exact FLR-0402/0401 observer tip)
- Dependency: [FLR-0401](FLR-0401-capture-live-fengine-present-stack.md), [FLR-0402](FLR-0402-dimension-aware-qmp-analysis.md); exact image rootfs `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`
- Plan: [FLR-0403 implementation plan](../../docs/superpowers/plans/2026-10-02-flr0403-oops-lwp-present-correlation.md)
- Working log: [FLR-0403 working log](../logs/2026-10-02-flr0403.md)

## Objective

On one unchanged patch-0334 image, correlate that run's kernel Oops PID/TID
with the identity-checked GDB thread table (`ptid`/LWP), current mapped ELF
Build-IDs, and the outstanding present. Preserve the live full QMP frame before
GDB interrupts the inferior. This is a product-runtime discriminator, not a
Sequoia rendering pass or root-cause claim.

## Facts, inferences, hypotheses, and UNKNOWN

### Facts

- FLR-0401 used rootfs SHA-256
  `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`, kernel
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and
  qemuboot `2363530e2f39d4e57465cb89e724327f699b8ab6247d9e1bb75fdc2a60780c10`.
- Its live 1280x800 QMP frame showed CPU/GPU/FPS HUD and Scenes, while the
  Sequoia ROI `[440,220,400,360]` was 144,000/144,000 black pixels. Counters
  were `READY=1`, `PRESENT_BEGIN=1`, `PRESENT_RETURN=0`, `SUN=1`.
- GDB collected seven `FEngine::loop` stacks: six waits and one short,
  unresolved LLVM unwind. Kernel later recorded `FEngine::loop` Oops PID 715,
  RIP `0x7fef595d1541`; coredump query was empty. The GDB log did not retain
  Linux `ptid`/LWP, `/proc/<pid>/maps`, or current-image Build-ID, so this
  Oops is not mapped to the earlier GDB thread table.
- On older, different rootfs images FLR-0366/0374 mapped a similar RIP offset
  to LLVM `CmpInst::isOrdered`; this is correlation only, not a proven access
  cause. FLR-0341 observed a Lavapipe WSI wait but did not prove completion.
- FLR-0394's progressing LIT fixture+HUD is a positive control on a different
  rootfs (`54da69d…`), not a current-image Sequoia pass.
- GDB's documented `InferiorThread.ptid` tuple is `(PID, LWPID, TID)` and
  `gdb.Objfile.build_id` returns an ELF Build-ID when present:
  [Threads In Python](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Threads-In-Python.html),
  [Objfiles In Python](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Objfiles-In-Python.html).

### Inferences

- The next highest-information observation is one exact-image run that records
  the thread identifiers and loaded object identities at the same time as the
  existing present/visual evidence. A source or material change before this
  correlation would confound the discriminator.
- FLR-0401's 18-second gap between the live capture and Oops means a thread
  table sampled only once may describe pre-fault state. Preserve timestamps,
  thread presence, and the kernel Oops from the same run; if the thread exits
  before it can be mapped, report that limitation explicitly.

### Hypotheses

1. **A render/LLVM worker fault blocks work needed by the unmatched present.**
   Support: the Oops TID maps to a captured FEngine LWP in the relevant render
   path and its disappearance precedes a stalled dependent present. Refute:
   the mapped thread is unrelated or its work completes while the unmatched
   present remains unresolved.
2. **A synchronization/WSI wait is independent of the Oops.** Support: a
   distinct identified thread remains in a concrete present/wait path with an
   incomplete producer while the Oops thread is separate. Refute: the faulting
   thread itself owns the blocked path and no separate wait remains in the
   timestamp-aligned observation. Handle equality or submit success alone is
   not completion proof.
3. **Black Sequoia pixels are an independent scene/content/surface defect.**
   Support: present keeps progressing on the same image while the Sequoia ROI
   stays black. Refute: recognizable Sequoia appears with scene/material and
   visual inputs unchanged after the runtime path recovers.

### UNKNOWN

- Whether the current image reproduces the Oops or unmatched present.
- Which LWP faults, what Build-ID is loaded by the current image, and whether
  either event causes the black Sequoia ROI.
- Whether a continuing healthy present would render the original Sequoia
  material, textures, and lighting.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | One run's QMP frame, present counters, GDB `ptid`/LWP, ELF Build-ID, kernel Oops TID |
| Where | Exact FLR-0401 runtime image and its existing guest/QMP/GDB observer paths |
| When | Full QMP still before GDB interruption; thread/object snapshot at unmatched present; timestamped kernel/app state through first abnormal event |
| Who | Mini runtime owner, manual guest Flutter operator, GDB observer, QMP/kernel evidence collector |
| How | Same image/profile; one fresh run ID; one combined guest evidence log; no product/build changes |

## Scope and controls

- Keep the image, patch 0334, Example Demo scene, HUD, camera, and QEMU profile
  fixed. Preserve FLR-0401's diagnostic LIT/SUN overrides for this
  Oops/present-correlation run; that profile is explicitly not product
  acceptance. No BitBake, image build, Devtool, product-source patch, input
  suppression, or second QEMU.
- First verify the exact receiver/build artifacts and that Mini has no active
  QEMU/runqemu/Flutter/BitBake/GDB owner, occupied reserved ports, or run-ID
  collision. If any owner/state is ambiguous, do not start or stop it.
- Reuse the documented QEMU start/profile and direct manual guest Flutter
  command. Do not rewrite the launch helper to compensate for an unverified
  manual command. No new shell automation until the existing sequence passes.
- Capture full QMP still and four-frame sample before debugger attach. Preserve
  exact PPM hashes on Mini; show the selected full-frame PNG/video in the
  evidence record. Never use post-exit black as a live-render verdict.
- GDB, inferior identity/readiness, present markers, and kernel timestamp
  records must resolve to the same run ID and one combined guest log sink;
  copy the log before stopping the app. Record PID/UID/start identity.
- Record GDB thread number/name/target ID and mapped ELF path/Build-ID from the
  current image. Do not infer causality from symbol names or a matching offset
  alone.
- Use one fresh run ID only. Do not retry a consumed ID or run on an unverified
  receiver tip. This runtime-only task requires no build-receiver source
  change: do not transfer documentation-only bundles or mutate the receiver.
  Commit local records without push.
- Keep raw logs on Mini. Transfer only bounded review evidence and checksums;
  do not record connection details or personal paths in Git.

## Success criteria

1. Before changing any observer, the documented manual guest commands capture
   `gdb info threads` target IDs, `/proc/<pid>/maps`, and `readelf -n`
   Build-IDs for the actually mapped LLVM/Vulkan/Filament objects. Record the
   exact successful commands and append them to the same run-scoped guest log
   used for readiness and present markers. If a required tool is absent, record
   UNKNOWN and do not silently substitute another source.
2. A read-only Mini preflight proves receiver tip, exact kernel/rootfs/qemuboot
   hashes, no active owner, free ports, and an unused evidence/run ID before
   any QEMU start. Any mismatch stops before runtime mutation.
3. One manual Flutter runtime reaches a live capture point. Save a full QMP
   screenshot plus four consecutive QMP frames before GDB interruption; retain
   actual PPM dimensions, hashes, HUD/Sequoia pixel analysis, readiness, and
   present counters. If no live Flutter frame is reached, classify startup and
   do not call it a rendering result.
4. In the same run, retain timestamp-aligned GDB target IDs (including LWP),
   mapped-file paths/Build-IDs, process identity, present state, and kernel
   Oops TID (if any).
   Explicitly state whether the TID maps, disappeared before sampling, or was
   absent; keep root-cause causality UNKNOWN unless dependency evidence exists.
5. Exact app/QEMU/QMP cleanup and postflight prove no new residual processes or
   listeners. No other owner's processes are touched.
6. All evidence, failures, hashes, commands, and the next discriminator are in
   this ticket/log. A diagnostic result does not satisfy the user's final
   production-rendering criteria.

## Plan / Do / Check / Act

### Plan

- Close FLR-0402 as analyzer-only and make FLR-0403 the sole active ticket.
- Reuse the proven QEMU and manual Flutter launch sequence. First inspect the
  exact saved commands and log destinations; do not change the observer.
- Verify receiver/build state read-only. Use the existing generic QEMU harness
  for one exact-image run only if ownership, hash, port, receiver, and fresh-ID
  gates pass; do not check out or update the receiver.
- Manually capture QMP before GDB, then run bounded `info threads`, maps, and
  Build-ID commands against the identity-checked process. Only after the
  manual commands succeed may a separate ticket automate them. Do not build.

### Do

- One run, `flr0403-0001`, completed on the unchanged patch-0334 image. The
  exact rootfs/kernel/qemuboot hashes matched the FLR-0401 baseline; no source,
  build, image, receiver, or cache was changed. The run used the same diagnostic
  LIT-material and SUN overrides as the prior observation, so it is not an
  original-material/light product test.
- The direct `flutter-auto` process was PID 646, UID 1001, start token 44270.
  A QMP-only 1280x800 full-frame capture showed CPU/GPU/FPS HUD and Scenes, but
  the Sequoia ROI `[440,220,400,360]` was uniformly black (144,000/144,000
  pixels). The capture was not bracketed by an immediately-before/after app
  identity check; classify the frame as visual evidence, not a certified live
  app snapshot. See [run evidence](../evidence/FLR-0403-0001.md).
- Guest kernel recorded an `FEngine::loop` page-fault Oops (TID 695, RIP
  `0x7fb61183e541`, CR2 `0x00000000aaff9750`) at estimated UTC
  `2026-10-02T08:01:52.307952Z`; guest uptime was 475.594763 s. The nearest
  app READY/present snapshot was later, and the QMP image was later still.
  `coredumpctl` found no core. The app eventually returned 124 from the
  configured timeout; this status alone is not a product-crash verdict.
- The process exited before the attempted GDB/maps/Build-ID collection. No
  `ptid`/LWP mapping or same-run ELF Build-ID was obtained. Oops-to-present
  causality remains UNKNOWN. The four QMP frame samples had the same PPM hash;
  this does not establish frame progress.
- `runqemu` initially appeared as its Python wrapper rather than a
  `qemu-system` process; read-only descendant inspection identified the actual
  QEMU child. BusyBox rejected `dmesg --ctime`; plain bounded `dmesg` then
  succeeded. Both failed checks and their corrections are retained in the
  working log.
- Exact QMP teardown and postflight passed: no owned QEMU/runqemu/Flutter/QMP
  process or reserved listener remained, and image hashes were unchanged.

### Check

- Exact-image preflight and generic harness preflight passed; QEMU and guest
  Flutter ran once; full QMP evidence, focused guest log export, bounded
  kernel Oops evidence, and exact cleanup/postflight were recorded.
- The central diagnostic success criterion failed: process lifetime ended
  before GDB could map Oops TID to LWP or collect current-image Build-IDs.
  The visual capture is not identity-bracketed, and both visual content and
  runtime progress are unhealthy/uncertain. This ticket is therefore Waiting,
  not Done; the failed criterion must not be relabeled as product evidence.
- Raw guest/QMP artifacts remain on the Mini. The committed evidence manifest
  contains the QMP PNG, raw PPM/frame hashes, bounded app-log hash, and
  role-relative Mini evidence location.

### Act

- Preserve the Oops/LWP/Build-ID relationship as UNKNOWN; do not infer that the
  Oops caused the black ROI. Do not spend another run on the same debugger
  window without new evidence.
- The next highest-value product check is a fresh, single-QEMU run of the
  installed Example Demo on the exact same image with the diagnostic material
  and SUN overrides absent. That separates the diagnostic profile from the
  actual Sequoia material/lighting path. It is FLR-0404, a separate ticket.

## Impact

- **Build-time / packaging:** none; no Yocto recipe or image is changed.
- **Runtime:** one bounded diagnostic QEMU run completed after read-only Mini
  ownership/hash/port gates passed; teardown and postflight passed.
- **Integration risk:** GDB pauses the inferior. Capture QMP before attach,
  bound GDB duration, use identity-checked detach/cleanup, and never interpret
  debugger-induced changes as normal runtime behavior.
