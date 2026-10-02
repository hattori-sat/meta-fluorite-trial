# FLR-0403 — correlate the FEngine Oops with its GDB LWP and present

- Status: In Progress
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

- Keep the image, patch 0334, Example Demo scene, HUD, launch environment,
  camera/material/light settings, and QEMU profile fixed. No BitBake, image
  build, Devtool, product-source patch, diagnostic material override, input
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
- Record GDB thread number, name, complete `ptid`, and filtered current-image
  objfile filename/Build-ID. Do not infer causality from symbol names or a
  matching offset alone.
- Use one fresh run ID only. Do not retry a consumed ID or run on an unverified
  receiver tip. Commit locally without push; use the official bundle workflow.
- Keep raw logs on Mini. Transfer only bounded review evidence and checksums;
  do not record connection details or personal paths in Git.

## Success criteria

1. Local regression tests require `ptid`/LWP and bounded current objfile
   Build-ID markers in the generated GDB script, and prove they reach the same
   guest log as readiness/present evidence without exceeding the existing
   serial command limit.
2. A read-only Mini preflight proves receiver tip, exact kernel/rootfs/qemuboot
   hashes, no active owner, free ports, and an unused evidence/run ID before
   any QEMU start. Any mismatch stops before runtime mutation.
3. One manual Flutter runtime reaches a live capture point. Save a full QMP
   screenshot plus four consecutive QMP frames before GDB interruption; retain
   actual PPM dimensions, hashes, HUD/Sequoia pixel analysis, readiness, and
   present counters. If no live Flutter frame is reached, classify startup and
   do not call it a rendering result.
4. In the same run, retain timestamp-aligned GDB `ptid`/LWP and loaded
   Build-IDs, process identity, present state, and kernel Oops TID (if any).
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
- Add a regression first for GDB `ptid` and filtered `gdb.Objfile.build_id`
  markers; keep the generated serial command within its current limit.
- Use the official bundle handoff and read-only Mini preflight. Start one
  exact-image QEMU only if all ownership, hash, port, and fresh-ID gates pass.
- Manually launch Flutter with the already-proven guest command, capture QMP
  before GDB, then collect one bounded GDB/kernel state sample. Do not build.

### Do

- Pending. No source/runtime edit or new QEMU has been started for FLR-0403.

### Check

- Pending local regression, Mini preflight, same-run visual/runtime evidence,
  and exact cleanup.

### Act

- Decide the next smallest product boundary from the first correlated event.
  If TID/ptid or Build-ID remains unavailable, preserve UNKNOWN and improve
  only that observation path. If present progresses but Sequoia stays black,
  move to the earliest evidenced scene/material/texture/surface boundary.

## Impact

- **Build-time / packaging:** none; no Yocto recipe or image is changed.
- **Runtime:** one bounded diagnostic QEMU run if and only if the Mini
  preflight proves it cannot disturb another owner.
- **Integration risk:** GDB pauses the inferior. Capture QMP before attach,
  bound GDB duration, use identity-checked detach/cleanup, and never interpret
  debugger-induced changes as normal runtime behavior.
