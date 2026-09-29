# FLR-0374 — correlate manual present stall with preserved kernel evidence

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / strict guest SSH / manual Flutter / QMP and kernel-evidence roles
- Created: 2026-09-30
- Predecessor: [FLR-0373 production Sequoia scene runtime](FLR-0373-production-sequoia-scene-runtime.md)
- Branch: `feature-flr-0374-present-oops-correlation` (local, no push)
- Working log: [FLR-0374 working log](../logs/2026-09-30-flr0374.md)
- Candidate image: build output SHA-256
  `3b627cfda1c255783b281a00b469b6c30c7a6bcef4823e8b655ca15c30eb84b3`;
  rootfs SHA-256
  `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`;
  kernel SHA-256
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.

## Objective

Use one fresh manual QEMU → strict guest SSH → `agl-driver` →
`/usr/bin/flutter-auto` run on the same candidate image to determine whether the
unmatched Vulkan present is followed by a kernel Oops, app exit, or a bounded
no-Oops stall. Preserve evidence before shutdown. This classifies the runtime
boundary; it does not claim production 2D+3D acceptance passed.

## Facts

- FLR-0373 manually launched the installed Example Demo 3.32.5 bundle with
  fixture overrides absent. After 45 seconds it recorded 2 present enters and
  1 return/success; the app remained alive and the second present was
  unmatched.
- Its full QMP PPM exactly matches FLR-0366's pre-fault and post-fault frame.
  The current frame showed a gray-white field and black polygon without
  recognizable Sequoia or HUD. Pixel identity does not establish scene
  identity or fault causality.
- FLR-0366 separately recorded an `FEngine::loop` kernel Oops after the same
  2-enter/1-return pattern. GDB caught no signal; `llvm::CmpInst::isOrdered`
  was a symbol correlation, not an established fault cause.
- FLR-0373's app log was volatile under `/run/user/1001` and was not copied
  before QEMU shutdown. Current-run Oops/coredump state is UNKNOWN.
- FLR-0371 established the manual route: the QEMU helper starts one identified
  guest, strict root SSH is pinned only after QEMU listener ownership is
  verified, then root uses `su` to launch the app as `agl-driver`. Direct guest
  SSH as `agl-driver` was rejected by public-key authentication.

## Hypotheses and predictions

1. **Present stall without Oops in the bounded window.** Expect the same
   unmatched present while the app remains alive, no new kernel Oops/coredump
   through 300 seconds, and a static QMP frame.
2. **The historical kernel fault recurs.** Expect a timestamped kernel Oops
   after the unmatched present and a corresponding `FEngine::loop` thread
   change/disappearance; preserve journal, app markers, and QMP frame before
   teardown.
3. **Present continues; missing scene/HUD is a separate rendering boundary.**
   Expect repeated returned presents while the QMP frame still lacks HUD or
   recognizable production vehicle pixels. This lowers the priority of the
   historical Oops branch.
4. **The app exits or crashes by another path.** Expect a process exit or
   coredump/journal record before timeout, not merely an unchanged QMP frame.

## Scope and success criteria

- Use the exact candidate rootfs/kernel/qemuboot and existing Mini build and
  QEMU/capture helpers. No build, source, recipe, fixture override, launch
  script, or helper change. Do not copy disk-image artifacts to Mac.
- Preflight exact residual QEMU/runqemu/Flutter processes, QMP socket, and
  ports before fresh run ID `flr0374-0001`; use 6144 MiB and the previously
  verified port triplet. Pin the guest SSH key only after verifying that the
  listener belongs to this run's QEMU child.
- Verify kernel, compositor, Wayland socket, Example Demo bundle, executable,
  fixture-variable absence, and zero stale app processes before launch.
- Manually start one `/usr/bin/flutter-auto` as UID 1001 through strict root
  SSH followed by `su`; use only `FLUORITE_PRESENT_TRACE=1`. Do not invoke an
  app-launch helper.
- Observe only selected present/error markers, app PID/thread state, and
  kernel Oops/coredump state for at most 300 seconds after app start. Poll a
  bounded summary at 5-second intervals; do not dump whole logs.
- Before stopping the app or QEMU, persist at most the last 256 KiB of its app
  log, selected kernel Oops/journal context, coredump listing/availability,
  exact process/thread state, marker counts, and hashes under
  `$BUILD_EVIDENCE/flr0374-0001/qemu/`. Capture a complete QMP still and eight
  QMP frames; retain a local review PNG/MP4 without transferring the image.
- Stop only the recorded Flutter PID and this QEMU through its recorded QMP
  socket. Independently verify PIDs, socket, and all reserved ports are clear.
- This diagnostic ticket passes only if event classification, evidence
  retention, screenshot, image identity, and exact teardown are conclusive.
  Otherwise record FAIL/UNKNOWN and keep the task Waiting; do not claim a
  rendering fix.

## Impact

- **Build-time:** none; reuse the identified candidate image.
- **Packaging:** none; verify the installed bundle before launch.
- **Runtime:** one manual diagnostic app run, bounded to 300 seconds.
- **Integration risk:** no software mutation. Event classification selects
  the next diagnostic ticket; it cannot prove the Oops caused missing pixels.

## Plan / Do / Check / Act

### Plan

Replay the known manual SSH/Flutter sequence first, with no script edits. Set
up evidence persistence before app start, capture the first unmatched-present
state, then observe selected signals until Oops/exit or the 300-second bound.
Save logs and QMP evidence before exact-PID/QMP teardown.

### Do

- Ticket opened from FLR-0373's manually observed 2-enter/1-return state and
  missing volatile-log evidence. No run has started yet.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Image and guest identity | Exact candidate hashes and ready guest | Pending | PENDING |
| Manual app route | One app as UID 1001, fixture overrides absent | Pending | PENDING |
| Event classification | Oops, app exit, continued presents, or bounded no-Oops state with timestamped evidence | Pending | PENDING |
| Save-before-stop | Bounded app/kernel/process evidence and QMP still/sequence persisted | Pending | PENDING |
| Teardown | Exact app/QEMU gone; socket and ports free | Pending | PENDING |

### Act

- Pending the one manual runtime observation. No source or runner automation
  changes before its result.

## Visual evidence

- Pending fresh QMP-only full-frame screenshot and short sequence for
  `flr0374-0001`; do not substitute FLR-0373 or FLR-0366 evidence for this
  run's capture.
