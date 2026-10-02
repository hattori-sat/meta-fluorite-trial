# FLR-0405 — capture ordinary-profile FEngine fault and present order

- Status: In Progress
- Priority: High
- Created: 2026-10-02
- Owner: Mini QEMU / guest Example Demo+GDB / shared app log / QMP and kernel evidence
- Branch: `feature-flr-0405-post-present-qmp` (from local `dev-flr-0404-ordinary-profile` transition checkpoint)
- Depends on: [FLR-0404](FLR-0404-run-default-sequoia-on-0334.md); exact rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`
- Plan: [post-present QMP observation plan](../../docs/superpowers/plans/2026-10-03-flr0405-post-present-qmp.md); no product-source edit or build
- Working log: [FLR-0405 working log](../logs/2026-10-02-flr0405.md)

## Objective

On one unchanged patch-0334 image and ordinary Example Demo launch, determine
the event order between the second unmatched Vulkan present and the first
FEngine page fault/Oops. Capture the relevant live LWP/thread state and module
identity early enough that the faulting thread has not already disappeared.
This is a runtime-boundary ticket, not a product rendering pass or final root
cause claim.

## Facts, inferences, hypotheses, and UNKNOWN

### Facts

- FLR-0404 used the exact patch-0334 rootfs/kernel/qemuboot and no optional
  selector/material/light/camera/render/sync override. Its QMP frame showed a
  white field and one black polygon, with no HUD or recognizable Sequoia.
- The identity-bracketed app log recorded two present begins and one successful
  return. Guest kernel Oops at uptime 266.762166 s names TID 691
  `FEngine::loop`; the parent `flutter-auto` remained alive and TID 691 was
  absent from the later thread list.
- The Oops RIP maps to `libLLVM.so.18.1`, Build-ID
  `359c1108040bc6bc1af64bb639d0b25385858051`, and `addr2line` reports
  `llvm::CmpInst::isOrdered(llvm::CmpInst::Predicate)`. This location alone
  does not establish causality.
- A GDB attach after the Oops exceeded its 12-second bound, returned rc=137,
  and produced no backtrace. The exact app resumed; no stopped thread or GDB
  process remained. `coredumpctl` reported no dump.
- FLR-0400/0401/0403 and older present tickets contain related incomplete
  present/Oops observations. They are comparison evidence, not proof that the
  same producer or root cause is involved.

### Inferences

- The next useful observation must capture thread identities/stacks before the
  faulting TID disappears, and align them with the app's present markers and
  kernel Oops timestamp in one run.
- Another material, lighting, camera, surface-order, or input change would
  confound this runtime-boundary discriminator and has lower information value
  until a healthy present baseline exists.
- GDB attachment can perturb timing. Any changed or prevented failure under
  the debugger must be reported as an observer effect, not a product fix.

### Hypotheses

1. **The FEngine fault removes work required by the pending present.** Support:
   timestamped GDB shows the faulting LWP executing render/submit work and its
   disappearance precedes a dependent present stall. Refute: present is already
   stalled in an independent WSI/synchronization wait before the fault.
2. **The present/synchronization stall precedes or is independent of the Oops.**
   Support: a live stack shows an incomplete wait before the Oops, or the Oops
   LWP is unrelated to the pending present. Refute: captured dependency state
   shows the faulting LWP owns the only producer for the pending present.
3. **The late GDB timeout was caused by attaching to the already-large thread
   set, not an unavailable debugger.** Support: early bounded attach completes
   with LWP IDs and selected stacks. Refute: the same attach stalls before
   thread enumeration while the app has few threads.

### UNKNOWN

- Whether the Oops precedes, follows, or causes the unmatched present.
- Which current LWP owns the pending present and whether it shares a dependency
  with TID 691.
- Whether the white/black-polygon screen is a scene, renderer, or Wayland
  composition result; FLR-0404's unhealthy present path prevents isolation.
- Whether the original Sequoia material/texture/light path is reached or
  sampled, and whether a supported viewpoint control exists.
- Whether a debugger changes or suppresses the fault.

## Current status (2026-10-02)

- Waiting only on the bounded serial-exec gate work in FLR-0406. No product
  source, image, or cache change is a dependency of FLR-0406.
- The ordinary-profile frame/present/Oops evidence remains as recorded above;
  the Oops-versus-present event order and guest SIGTERM completion remain
  UNKNOWN. Do not restart QEMU or reuse the consumed run ID until the exact
  harness is verified through the documented Mini handoff.
- Product rendering, 2D+3D composition, interaction/repaint stability,
  five-minute present health, and two-boot acceptance remain NOT MET.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | LWP stacks, mapped ELF Build-IDs, present begin/return, first kernel Oops, full QMP pixels |
| Where | Exact Mini patch-0334 image, ordinary Example Demo 3.32.5, guest/QMP framebuffer |
| When | One fresh boot; collect initial state, attach GDB as soon as the live app identity exists, stop at the first abnormal boundary |
| Who | Mini runtime operator, guest `agl-driver`, bounded GDB observer, QMP and kernel evidence capture |
| How | One image/profile; one QEMU; direct launch with allow-listed environment; shared timestamped app/GDB/observer log |

## Scope and controls

- Runtime-only. Do not modify Devtool source, recipe, patch stack, layer, image,
  cache, or build directory. Do not run BitBake or transfer a bundle.
- Start QEMU with the existing generic `scripts/qemu-runtime-harness.sh`, using
  the paths recovered from FLR-0404's saved run command. Do not use the
  FLR-0399 starter (it rejects this run ID) or
  `scripts/flr0399_live_capture.py` (its direct mode includes diagnostic
  selectors/material/SUN values and is not the ordinary profile).
- Use the ticket-scoped POSIX guest commands in
  `work/commands/FLR-0405-guest-*.cmd` for preflight, direct launch, identity
  gates, early GDB, first-boundary monitoring, log export, and scoped stop.
  Validate one-line framing, `sh -n`, and the 4096-byte limit before transfer.
- Use `FLR-0405-guest-wall-clock-context.cmd` once to retain same-boot
  `journalctl -o short-iso-precise` fault lines with the identity-verified app
  log when correlating present wall time to kernel monotonic time.
- Use the Mini receiver's pinned pixel helper only for QMP capture/video; its
  analyzer differs from the current local copy, so do not pass local-only
  `--region full`. Analyze transferred review frames locally with explicit
  dimensions/regions after their hashes are recorded.
- Before the one QEMU start, recheck canonical local repository, authoritative
  receiver tip/cleanliness, exact rootfs/kernel/qemuboot hashes, configured
  layer identity, no existing runtime owner, free ports, storage/memory, and a
  fresh run ID `flr0405-0001`. Use only the recorded fixed receiver and the
  exact 0334 artifact; do not touch the unrelated dirty FLR-0019 checkout.
- Use the existing QEMU runtime harness, one 6144-MiB instance, and ports
  10930–10932. No second QEMU and no copied rootfs/image on Mac.
- Launch the same ordinary Example Demo as `agl-driver`, with only
  `HOME`, `PATH`, `XDG_RUNTIME_DIR`, and `WAYLAND_DISPLAY`; do not set optional
  model-selection, material, light, camera, render, or synchronization flags.
- Preserve a full QMP still before debugger attachment. Record PID/UID/start
  identity immediately before and after every selected capture/observer action.
- Attach GDB once as early as possible after launch. First capture `info threads`
  with target IDs/LWPs and mapped modules/Build-IDs, then bounded relevant
  `FEngine::loop`/renderer backtraces. Use one 30-second hard bound; do not use
  an unbounded `thread apply all` on a late large thread set. Append GDB output
  to the same guest app log used for readiness and present observations.
- Monitor at most 300 one-second samples, comparing the launch-time kernel
  fault baseline. Stop at the first new kernel fault or after two consecutive
  samples with present-begin greater than present-return; capture a bounded
  thread/map and focused journal/coredump summary at that boundary.
- Capture the first Oops/present boundary and a full QMP frame before teardown.
  If present is still unhealthy, stop; no pointer/hover/click trial or blind
  five-minute wait. Do not infer root cause from a symbol name alone.
- Keep raw PPM/log evidence on Mini and transfer only small review PNG/MP4 files
  after hashing. Record every failed as well as successful command.
- If the first boundary is localized enough to justify a source change, create
  a separate patch ticket. Do not add that fix to this observation ticket.

## Success criteria — bounded diagnostic completion, not product acceptance

1. The exact image/receiver/process/port/run-ID gates pass before start, with
   image hashes unchanged.
2. One ordinary Example Demo launches with the recorded app identity and no
   diagnostic override; the debugger/observer uses the shared run-scoped log.
3. Full-screen QMP captures are identity-bracketed. GDB records thread/LWP IDs,
   relevant stacks, and current ELF mapping/Build-ID, or reports the exact
   bounded failure and observer impact.
4. Present markers and kernel fault data are timestamped in the same run so the
   event order is classified as supported, refuted, or UNKNOWN. No symbol-only
   root cause claim.
5. Exact app/QMP/QEMU cleanup, free reserved ports, unchanged artifacts, and
   all command results/evidence hashes are recorded.

The user-visible Sequoia+HUD goal remains open regardless of this ticket's
diagnostic result.

## Plan / Do / Check / Act

### Plan

- Reuse exact 0334 and the direct ordinary launch that FLR-0404 established.
- Move bounded GDB observation to immediately after app identity capture, not
  after the pending present/Oops. Preserve QMP first and share one log sink.
- Change no scene, material, texture, light, camera, surface order, input, or
  build variable. Stop at the first unhealthy boundary.

### Do

- One QEMU (6144 MiB) and the ordinary Example Demo ran on the exact 0334
  image; guest-ready/preflight passed and launch recorded PID 645, UID 1001,
  start token 12499, with the allow-listed environment. No build or product
  source change occurred. Read-only Mini inspection recovered the receiver from
  FLR-0404 evidence: HEAD `54c02bdcddbf80be579c4fd7d493f5bd24f6df6c`, clean
  outside ignored `evidence/`. The recorded 0404 runqemu command resolves the
  same fixed qemux86-64 build/TMPDIR; local.conf selects qemux86-64 and exactly
  one BBLAYERS path has basename `meta-fluorite-trial`.
- Fresh read-only preflight passed: 0404 evidence exists, 0405 run ID/QMP path
  is unused, exact kernel/rootfs/qemuboot hashes match the 0334 baseline,
  generic QEMU harness and exact process-cleanup helper match local hashes,
  zero target processes and listeners on ports 10930-10932; the first
  `qmp.sock` candidate was 88 bytes. The final pre-create recheck passed with receiver HEAD unchanged
  and clean, exact image/helper hashes, zero target owners, free ports,
  qemux86-64/one configured Fluorite layer, and 28,195,316 KiB available RAM,
  8,331,456 KiB swap, and 15,353,132 KiB free evidence space. The Mini pixel-capture
  helper differs from the local version; its `capture`/`video` interfaces were
  checked.
- Procedure corrections (no runtime or file state changed): initial nested
  SSH/find quoting attempts were rejected before the remote read-only query;
  local command-template interpolation also failed before SSH. One early
  preflight counted substring occurrences and stopped at the layer gate because
  the receiver directory name also contains `meta-fluorite-trial`; replacing
  that with exact BBLAYERS path-basename counting yielded one entry and the
  full preflight passed. The final check used one labeled script over SSH
  stdin, not another helper or QEMU start.
- Two subsequent read-only preflight attempts also failed closed before any
  mutation: one had a shell `test` operand-order typo; the next compared the
  configured BBLAYERS path with the receiver root instead of its `layers/`
  directory. The exact configured layer path was then verified and the full
  pre-create recheck passed. No evidence directory was created.
- The prior 0404 guest command files confirm direct Example Demo launch as UID
  1001 with only HOME/PATH/XDG_RUNTIME_DIR/WAYLAND_DISPLAY. The old 0399
  observer is explicitly excluded because it would change that profile.
- Guest-command review found and corrected one serial-shell hazard: an
  unscoped `set -e`/early `exit` could close the persistent shell before the
  harness completion marker. All eight commands now isolate their state and
  exits in a subshell. `/bin/sh -n`, one-line, and 4096-byte checks pass; the
  largest command is 4001 bytes.
- The initial static contract check on the added wall-clock query failed
  because the final subshell close lacked a separating semicolon. `sh -n` alone
  did not catch this serial-wrapper formatting rule. The terminator was fixed;
  all eight commands then passed syntax, one-line, and size checks. The new
  wall-clock command SHA-256 is
  `789c9838e394cbc386b3a8b0f1eaa156dd3f39c3da340149b58fdf19ec5e0ed4`.
- The actual ticket-standard `qmp-0405.sock` path is 93 bytes and was unused
  before startup; no shorter candidate socket was created.
- Initial and post-boundary full QMP PPMs are both 1280x800 and byte-identical
  (SHA-256 `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`),
  matching FLR-0404's initial white/black-polygon frame. Eight 0.5-second
  post-boundary frames were captured; manifest SHA-256 is
  `34d85614a75b4e3df1232284dc3fdaf586034c5d90177293c43695b7f30bea19`.
- Present remained at 2 begins/1 successful return. GDB completed rc=0 at
  uptime 252.14 with zero stopped threads and Build-ID
  `359c1108040bc6bc1af64bb639d0b25385858051`. The launch-fault baseline was 0;
  two later dmesg lines matched the pattern, but are not proven independent
  faults. One Oops record is timestamped kernel monotonic 160.228273, PID/TID
  691 `FEngine::loop`, RIP `0x7ff601633541`—earlier than the first live gate at
  uptime 182.35 and GDB at 231.04. Launch uptime is missing, so Oops-vs-launch
  and Oops-vs-present order are UNKNOWN. The first monitor detected an already
  existing fault at its initial sample; it did not observe the event live.
- The same identity remained alive through QMP capture at uptime 447.76. The
  guest app/GDB/observer log export passed (164,507 guest-log bytes). The
  bounded same-boot ISO journal query was attempted twice, but both serial-exec
  sessions stopped at `echo-off-response-unexpected` before the guest command
  was dispatched. Event order remains UNKNOWN because app markers use wall
  time while the Oops currently has only monotonic time. Do not infer causality
  from the event count, address, or LLVM symbol.
- Validation: canonical/privacy/checkpoint/shell/file-size gates pass. The
  loopback-enabled Python suite remains 222/223 with one unrelated serial-exec
  validator fixture failure; Markdown has 11 historical missing links outside
  FLR-0405. Runtime is negative/unhealthy; product acceptance remains
  NOT MET/UNKNOWN. QMP teardown and host postflight passed; guest SIGTERM
  completion is unverified because serial-login confirmed only prompt
  synchronization and no stop-result marker was captured.
- Local checkpoint `5d8d4f2` committed TASKS, this ticket, its working log, and
  the seven guest commands on the FLR-0405 feature branch; no push was made.
- Local-only commit `88928b1` added the bounded wall-clock guest command and
  pre-run evidence; the post-run closeout is being checked before its own
  local-only commit. No push occurred.
- Next: keep FLR-0405 In Progress and resolve the serial-exec observation gate
  under the separate Inbox FLR-0406 before another fresh-ID runtime attempt.
  Do not infer product root cause from a harness failure, symbol, or event
  count.

### Check

- The runtime reproduced the prior negative frame and present/Oops symptoms.
  QMP teardown and postflight PASS. Product rendering, input/repaint,
  five-minute stability, second boot, and overall acceptance remain NOT MET;
  event ordering and guest SIGTERM completion remain UNKNOWN.

### Act

- If the Oops/pending-present ordering and LWP dependency are evidenced, open a
  separate smallest-fix ticket for that boundary. If GDB perturbs or misses the
  failure, keep causality UNKNOWN and use the next discriminator with evidence
  from FLR-0400/0401/0403/0404; do not repeat the same late-attach command.

## Impact

- **Build-time / packaging:** none planned.
- **Runtime:** one fresh 6144-MiB QEMU and one ordinary guest app; a bounded
  debugger attach can perturb timing. No parallel QEMU/build.
- **Integration risk:** no product source/image changes. Exact identity checks,
  QMP-only captures, and scoped teardown limit interference with other work.

## Run closeout evidence (2026-10-02)

- The transferred wall-clock command matched SHA-256
  `789c9838e394cbc386b3a8b0f1eaa156dd3f39c3da340149b58fdf19ec5e0ed4`, was
  1,345 bytes, one line, and passed `sh -n`. Both serial-exec attempts returned
  `FAIL reason=echo-off-response-unexpected`; both guest command outputs were
  empty, so the journal query was never dispatched. The first 52-byte setup
  transcript matches the earlier successful guest-launch setup bytes. The
  second 38-byte setup transcript contains two adjacent
  `root@qemux86-64:~#` prompts after echo was already disabled. Mini and local
  harness SHA-256 values match (`436d010e…`). Preserve the first attempt's
  precise branch cause as UNKNOWN; the repeated prompt state warrants separate
  mock-backed FLR-0406 work.
- An initial read-only host probe incorrectly searched the guest's
  `/run/user/1001` identity file on Mini and failed before mutation. A later
  file-inventory command also exited before changing state because its shell
  `printf` format began with `---`; both were corrected as read-only probes.
- An initial stop-command invocation looked in the Mini repository's
  `work/commands` instead of the run-scoped transferred command and failed its
  read precondition; it did not connect to the guest. The correct run-scoped
  stop command matched the committed source hash
  `e579363db2a92d97f37ce4cc8b62724f715f695c7c64f37873e00f735f019765`.
  `serial-login` reported `prompt-synchronized=true`, but its interface does
  not return the command's status; the stop marker was absent from the separate
  boot-serial file. Treat guest SIGTERM completion as UNKNOWN. The subsequent
  negotiated QMP quit passed and reported zero residual target processes and
  zero QMP socket.
- Postflight rehashed the exact 0334 artifacts: rootfs
  `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`, kernel
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and
  qemuboot `2363530e2f39d4e57465cb89e724327f699b8ab6247d9e1bb75fdc2a60780c10`
  all match preflight. Ports 10930–10932 are free; receiver HEAD remains
  `54c02bdcddbf80be579c4fd7d493f5bd24f6df6c`, clean. No build, product source,
  or image file was changed.
- The post-boundary QMP still and all eight 0.5-second PPM frames have the same
  source hash `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
  Mini has no available image/video encoder. The PPM bytes were streamed through
  SSH directly into Mac ffmpeg; no raw PPM was persisted on Mac. Review PNG SHA-256:
  `dddb1b3e017d85600974be4d48c3b4e57990d9460eb573f24cd8587ff477c19d`;
  MP4 SHA-256 `4a9b9e835156b8cb73f493cd8a0c3d96c4c8f3d32b94e0ba42a8409277dc527f`
  (1280x800, 8 frames at 2 fps, 4.0 seconds). The repeated identical pixels
  show no visual change during this short sample; they do not prove a healthy
five-minute present stream.

## Iteration 2 — FLR-0405-0002 (2026-10-03)

### Facts

- The committed serial-exec helper passed the focused Mini suite (16/16) and
  every serial command in this run returned `rc=0`; the former echo/prompt
  setup failure did not recur.
- The exact 0334 image hashes were revalidated. One 6144-MiB QEMU boot used
  the ordinary Example Demo launch as `agl-driver` UID 1001 with no diagnostic
  overrides. Guest preflight confirmed the run-scoped `/run` log and identity
  files were absent before launch.
- Bounded GDB completed with zero stopped threads. No kernel Oops was recorded
  in the returned run summary. The first live-gate sample showed one present
  begin and zero returns; a later `queuePresent result=0` arrived. Exact final
  totals and Oops/present ordering were not recovered by the bounded closeout
  review and remain UNKNOWN.
- Four full-screen identity-bracketed QMP captures were black. The run evidence
  order places all four before the first successful present return; no
  post-present pixel capture exists. Therefore these frames do not establish
  that the application presented black pixels or that Sequoia/HUD rendering
  failed.
- The reviewed still is 1280x800 RGB, SHA-256
  `3e25a09ca6defc8efa884ff9945f86dea746b99e7fd6c70fdfdfa8109877351a`.
  Raw QMP frame set SHA-256:
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  Guest app-log export SHA-256:
  `9a493d04d671185299c99213694916d05d5bfff9e834a445d34e7d806ee094b6`.
  Raw evidence manifest SHA-256:
  `e3fded46041c2895207f04bb937199dbbfc16c6711c67400625326fe13bb547e`.
- The remote MP4 encoder failed; exact stderr was not retained. PNG previews
  and raw QMP frames remain available under the Mini evidence run directory.
  Some observer markers returned by individual commands were missing from the
  final shared app-log export; the cause is UNKNOWN. Do not infer success or
  failure from command `rc=0` alone.
- App stop, own-QEMU QMP quit, process/wrapper cleanup, free ports, and
  unchanged image hashes passed.

### Inferences and competing explanations

1. **Capture preceded the first real present.** Support: each black frame is
   ordered before the first successful queue-present return. Refute: a
   same-identity QMP frame taken after balanced successful returns is still
   black or lacks HUD/scene pixels.
2. **The first successfully returned present carried a black/incomplete
   buffer.** Support: a post-present QMP capture after two balanced successful
   returns is black. Refute: the same capture shows Flutter HUD or Sequoia.

Current evidence cannot choose between these explanations. A successful
`queuePresent result=0` alone is not pixel evidence.

### Plan / next action

- Keep the 0334 image, ordinary profile, app UID, and all product variables
  fixed. On a fresh run ID `flr0405-0003`, keep the early GDB/present/fault
  observation bounded, then require at least two `result=0` returns with
  `present_begin == successful_present_return` for the same PID/UID/start
  identity before taking the decisive full-screen QMP capture.
- If the two-return gate reaches its bound without readiness, capture only as
  a clearly labeled no-present boundary if the same app identity still exists;
  do not call it a post-present render result. If identity changes, fail
  closed and do not capture against a different process.
- Save QMP-only stills and a short frame sequence; use the local Mac FFmpeg
  installation to encode the review PNG sequence if the Mini encoder fails.
  Do not change Filament, material, texture, light, camera, surface order, or
  image in this discriminator.
- FLR-0406 is Done for serial-harness reliability only. This FLR-0405 run did
  not meet any production 3D/HUD acceptance criterion.

## Iteration 3 — post-present gate hardening (2026-10-03)

### Facts

- The pinned patch source encodes the `FLR0026_VK_QUEUE_PRESENT_BEGIN`
  trailing `\\n` as a literal backslash+n in its C format string, then emits
  the return record with `result`, `surface`, `swapchain`, and `index` fields.
  The previous whole-physical-line matcher would have missed that serialized
  form. The current exact ERE accepts the literal delimiter or a normal line
  boundary and counts only `result=0` as success.
- Launch keeps the four-field identity contract and creates one fresh shared
  app log. Flutter, launch context, GDB, and observer use append mode. The live
  gate requires an explicit post-check baseline, bounds the app log to 900,000
  bytes, bounds each `dmesg` read to two seconds, bounds wait to 60 samples / 45
  seconds, and performs UID/state/start/comm/unique-process checks after log
  and kernel sampling. Mini guest preflight checks `/usr/bin/timeout`.
- The gate compares aggregate begin/result counts; it does not pair individual
  queue/swapchain/index calls. Kernel count equality cannot exclude a
  simultaneous old-entry eviction/new-entry addition. These remain UNKNOWN,
  not product-health proof.
- A source-level review identified missing-baseline, stale process-state,
  marker-format, and kernel-ring edge cases. The requested model override did
  not return a confirmable GPT-6.1 Sol identity, so its output is not treated
  as that model's sign-off; concrete findings were addressed or retained as
  explicit UNKNOWN limits.
- No product source, image, build directory, cache, or QEMU was changed or run
  in this iteration.

### Inferences / hypotheses

1. Run 0002's black frames preceded the first successful return, so they do
   not distinguish a late capture from a black returned buffer.
2. A gate that does not recognize the source's escaped delimiter can itself
   create a false no-present timeout; emitter-compatible matching removes
   that observation-path defect, but does not establish scene pixels.
3. Run 0003 will discriminate only after its post-QMP `PROGRESS_READY` bracket
   and full-frame pixels agree. A ready marker alone is non-visual evidence.

### UNKNOWN

- Whether image 0334's live app log uses exactly the pinned source format for
  every relevant marker; the next run will preserve the actual raw line.
- Individual swapchain/index pairing, same-count dmesg ring replacement,
  Sequoia pixels, and HUD composition remain UNKNOWN.

### Plan / Do / Check / Act

- **Plan:** preserve exact 0334/ordinary profile and change only observation
  commands/records; capture after two balanced successful returns, then
  require a new successful return after capture.
- **Do:** updated only FLR-0405 observation commands, plan, ticket, and log.
  No product patch or build.
- **Check:** canonical guard, `make check-privacy`, `make check-file-sizes`
  (2,083 files), `make check-shell` (59 files), `/bin/sh -n`, one-line limit,
  emitter fixtures, wrapped size, `git diff --check`, and FLR-0405 checkpoint
  (`active=1`) passed. Exact wrapper lengths: launch 2,720 bytes, default gate
  3,863, post-check gate 3,921 (limit 4,096). Escaped successful fixture
  counted 1 begin / 1 return / 1 success; a `result=-4` fixture counted 1
  return / 0 successes. `make check-markdown` still fails on 11 historical
  missing targets in FLR-0338/0339/0340/0391/0395; none is a FLR-0405 link.
  Prior attempts recorded: import without `PYTHONPATH=scripts` failed to
  locate the helper; an oversized candidate wrapped to 4,112 bytes; an
  initial fixture used two literal slashes and matched 0/0/0. Each was
  corrected before runtime use. A direct `VAR=value ( ... )` post-gate
  invocation was rejected by `/bin/sh` as invalid syntax; semicolon
  assignments in the disposable serial-child command passed and wrap to 3,921
  bytes. No invalid variant was sent to the guest.
- **Act:** after all local gates pass, commit only FLR-0405 plan/commands/
  ticket/log, transfer through the canonical bundle helper, verify the exact
  Mini receiver and focused suite, then recheck QEMU/build/process/port/resource
  ownership before one fresh 0334 runtime run. Do not run QEMU on conflict.
