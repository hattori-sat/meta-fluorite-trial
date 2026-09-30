# FLR-0374 — correlate manual present stall with preserved kernel evidence

- Status: Done
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
- At FLR-0374 opening, FLR-0373's app log was volatile under `/run/user/1001`
  and was not copied before QEMU shutdown; the new run's Oops/coredump state
  was therefore UNKNOWN until this ticket's observation.
- FLR-0371 established the manual route: the QEMU helper starts one identified
  guest, strict root SSH is pinned only after QEMU listener ownership is
  verified, then root uses `su` to launch the app as `agl-driver`. Direct guest
  SSH as `agl-driver` was rejected by public-key authentication.

## Result

- Exact candidate image hashes matched FLR-0371/0373. QEMU used 6144 MiB; the
  guest, compositor, Wayland socket, and Example Demo 3.32.5 bundle passed
  preflight. One `/usr/bin/flutter-auto` ran manually as UID 1001, PID 703;
  only `FLUORITE_PRESENT_TRACE=1` was set, with fixture/light/camera/color
  overrides absent.
- The app log has two `FLUORITE_VK_QUEUE_PRESENT_ENTER` markers and exactly
  one `FLUORITE_VK_QUEUE_PRESENT_RETURN result=0`; the second enter has no
  return. At guest monotonic 575.268590 s, the kernel reported a user-mode
  page-fault Oops on TID 746 (`FEngine::loop`). PID 703 survived and TID 746
  was absent afterward. Guest uptime/app elapsed put the Oops about 35 seconds
  after launch. No coredump was listed.
- Oops context: CR2 `0x00000000267f8750`, RSP `0x00007fb8267f8750`, user RIP
  `0x7fb888079541`. RIP maps to `libLLVM.so.18.1` Build-ID
  `359c1108040bc6bc1af64bb639d0b25385858051`, file offset `0xb1d541`,
  `llvm::CmpInst::isOrdered`. The recorded instructions are register-only;
  this symbol is not a proven invalid-memory access cause.
- Runtime log reports reading `assets/models/sequoia_ngp.glb`; emissive
  texture index 6 later becomes ready and is applied. This does not prove that
  all GLB images load or that any texture is sampled. The log has 28
  “No default parameter value” messages; their effect is UNKNOWN.
- The full QMP frame is 1280×800: a gray-white field and a large black
  polygon, with no recognizable Sequoia or HUD. Native ROI
  `(440,220,400,360)` is uniform black; HUD ROI `(1120,0,160,80)` is uniform
  gray with zero chromatic pixels. Raw PPM SHA-256:
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
- All eight sequence captures have that same PPM hash; no visual transition
  appears across the replay. Pre-Flutter QMP was fully black, PPM hash
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- Local QMP screenshot `work/evidence/FLR-0374-0001/FLR-0374-0001-qmp-production.png`,
  SHA-256 `dddb1b3e017d85600974be4d48c3b4e57990d9460eb573f24cd8587ff477c19d`;
  eight-frame replay `work/evidence/FLR-0374-0001/FLR-0374-0001-qmp-sequence.mp4`,
  SHA-256 `3c3f8c4a87549b8954388c3ff44c7ab91951dc972bca7e92b90ea1a2a70b07ab`.
  These review derivatives are ignored runtime artifacts; source QMP PPM and
  frames remain on Mini under the role-based evidence directory.
  App log SHA-256:
  `da93fc8951647019b7eeff23133d6b3d068ebaeb875dc3e0363ecfa298411847`.
- Bounded app/kernel/thread/QMP evidence is retained under
  `$BUILD_EVIDENCE/flr0374-0001/qemu/`; local review derivatives are under
  `work/evidence/FLR-0374-0001/`. No QEMU disk image was copied to Mac.
- PID 703 was stopped after UID/command verification. The existing QMP
  harness accepted quit; independent Mini checks found zero target processes,
  absent run socket, and free reserved ports. No source, recipe, image, or
  launcher script changed.

### Measurement correction

- The initial derived `runtime-gate-final.txt` counted generic `result=0`
  text and incorrectly reported `present_success=12`. It is retained as a
  failed check. The exact queue-present marker reports one successful return;
  see the corrected exact-marker count above, the local ignored
  `runtime-gate-corrected.txt`, and the raw Mini app log.

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
  kernel Oops/coredump state for at most 300 seconds after app start. Stop
  early on Oops or app exit. Poll a bounded summary at 5-second intervals; do
  not dump whole logs.
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

- Run `flr0374-0001` used the exact candidate image and manual strict SSH →
  `su` → Flutter route. No app-launch helper or script edit was used.
- A nested guest SSH command without `-n` consumed the remainder of a
  stdin-fed Mini wrapper. Read-back proved its expected artifact was absent,
  so it was not accepted as a pass. Later probes used `ssh -n`, `pipefail`,
  and explicit artifact checks. An over-escaped `$!` left the PID file blank;
  read-only identity inspection found PID 703 before any retry, and no
  duplicate app was started.
- `coredumpctl list --boot` was unsupported; corrected
  `coredumpctl list --no-pager` reported no coredumps. A generic `result=0`
  count yielded 12 and failed the exact-marker cross-check; the corrected
  queue-present return count is 1. Both the failed derivative and correction
  are retained.
- Full run findings and command corrections are in the
  [working log](../logs/2026-09-30-flr0374.md).

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Image and guest identity | Exact candidate hashes and ready guest | Candidate hashes, kernel, compositor, Wayland, bundle, and zero-stale-app preflight passed | PASS |
| Manual app route | One app as UID 1001, fixture overrides absent | PID 703, UID 1001, exact Example Demo; only present-trace override | PASS |
| Event classification | Oops, app exit, continued presents, or bounded no-Oops state with evidence | 2 exact queue-present enters / 1 successful return; TID 746 Oops/disappearance; parent survived; no coredump | PASS for classification; rendering gate FAIL |
| Save-before-stop | Bounded app/kernel/process evidence and QMP still/sequence persisted | App log, Oops excerpts, thread/process snapshots, QMP PPM/eight frames, ROI and hashes saved before stop | PASS |
| Teardown | Exact app/QEMU gone; socket and ports free | PID 703 stopped; QMP quit accepted; independent process/socket/port checks zero | PASS |

### Act

- Close this ticket as a diagnostic evidence unit, not as a rendering fix.
  FLR-0375 inspects the exact candidate's packaged Sequoia GLB image
  references. The recurring fault already has dedicated historical
  investigations in FLR-0337/0338/0339/0340 and FLR-0366; do not repeat that
  trace without a new discriminator. Keep launch scripts unchanged.

## Visual evidence

- QMP-only pre-Flutter baseline PNG is retained locally as
  `work/evidence/FLR-0374-0001/FLR-0374-0001-qmp-pre-flutter.png`
  (SHA-256 `3e25a09ca6defc8efa884ff9945f86dea746b99e7fd6c70fdfdfa8109877351a`).
- The production screenshot and eight-frame replay listed above belong to
  `flr0374-0001`; they are not a rendering pass. Runtime media remains ignored
  by Git; the ticket retains run identity and checksums.
