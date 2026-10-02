# FLR-0401 — capture the live FEngine stack at unmatched Present on image 0334

- Status: Done
- Priority: High
- Created: 2026-10-02
- Owner: Mac observer/test source / Mini QEMU / guest Flutter+GDB / QMP evidence roles
- Branch: `feature-flr-0401-live-present-stack` (local only; stacked on FLR-0400 observer dependency)
- Dependency: [FLR-0400](FLR-0400-bounded-live-observer-polling.md), observer commit `a113c0e` and evidence commit `1e4672b`
- Plan: [FLR-0401 implementation plan](../../docs/superpowers/plans/2026-10-02-flr0401-live-present-stack.md)
- Working log: [FLR-0401 working log](../logs/2026-10-02-flr0401.md)
- Fresh run reserved: `flr0401-0001`
- Reused candidate: patch 0334; rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`; kernel/qemuboot hashes are pinned in the FLR-0399 starter.

## Objective

On the exact already-built 0334 image, capture one bounded GDB stack from the
live `FEngine::loop` thread when a Flutter queue-Present begin has no matching
return. Keep the application, scene, image, launch arguments, runtime
environment, and QEMU profile fixed. Change only debugger supervision from a
GDB-owned `run` whose later backtrace is deferred, to a direct app launch plus
one identity-checked live attach. This is a diagnostic unit, not a rendering
fix or product-acceptance pass.

## Facts, inferences, hypotheses, and unknowns

### Facts

- FLR-0400 used the exact 0334 rootfs and one bounded run. A full identity-
  bracketed QMP frame while Flutter was `READY=1` shows the CPU/GPU/FPS HUD and
  Scenes control; the fixed Sequoia ROI is uniform black. The earlier WAITING
  full frame is black and byte-identical to the pre-launch frame.
- The same live samples report `READY=1`, `PRESENT_BEGIN=1`,
  `PRESENT_RETURN=0`, and `SUN=1`. The 120-second observer ended with
  `PRESENT_DEADLINE_EXPIRED`; QMP postflight found no target process, socket,
  or forwarded-port residue.
- The saved kernel journal records an `FEngine::loop` page-fault/Oops at
  `02:44:30 UTC`; the focused coredump query is `EMPTY`. The saved instruction
  bytes contain `ff <cf>`, and the low 32 bits of RSP match the reported fault
  address. No current-run shared-library mapping, GDB stack, or causal ordering
  between the Oops and the unmatched Present was captured.
- FLR-0400 launched Flutter under `/usr/bin/gdb --batch -ex run -ex 'thread
  apply all bt 8'`. The bounded collector ran before the 150-second inferior
  timeout; the `run` command had not returned, so the queued backtrace was not
  emitted into the preserved log.
- FLR-0341 previously attached GDB to a normally launched live process and
  captured an `FEngine::loop` stack reaching Lavapipe
  `lvp_pipe_sync_wait` → `wsi_common_queue_present` on an older image. That is
  prior evidence, not proof of the current 0334 stack.
- FLR-0366 and FLR-0391 document a similar `FEngine::loop` Oops / `ff <cf>`
  signature. FLR-0366 explicitly shows that opcode/RIP symbol resemblance
  alone does not establish the faulting operation or root cause.
- The local implementation covers the counter/run-ID contract, opt-in direct
  app launch, bounded selected-thread GDB script, one-shot unmatched-Present
  trigger, and bounded failure-safe teardown. The focused observer suite
  passes 69/69. The exact-image Mini runtime result is recorded below; this was
  an observer/evidence run, not a product fix.
- Initial read-only reviews identified five pre-fix observer hazards: app/GDB
  writes used independent file offsets; GDB did not recheck inferior identity
  before thread inspection; empty/failed stack collection could be reported as
  complete; fixed guest-GDB timeouts could outlive the host serial wait; and
  teardown could delete a script not created by this invocation. One reviewer
  explicitly said its response was not model-certified as GPT-6.1 Sol. The
  requested model-certified GPT-6.1 Sol review then found two serial transport
  races: a nonzero GDB diagnostic status made an already-completed guest
  command look like serial failure, and a Present return between the sampled
  unmatched counters and the guest-side recheck emitted `PRESENT_MATCHED` but
  also exited nonzero. Both caused the observer to skip guest evidence as
  unconfirmed. The code now preserves the diagnostic/expected-skip marker in
  the shared guest log and returns transport success after the command itself
  completes; regressions exercise fake GDB exit 5 and the balanced-counter
  race, then assert observer evidence collection and cleanup. The latest
  GPT-6.1 Sol re-review found no further issues and confirmed both
  P2 transport gaps are closed; actual guest runtime remains unverified.

### Inferences

- The absence of a FLR-0400 GDB backtrace is explained by command ordering and
  the observer deadline; it is not evidence against either a WSI wait or a
  separate FEngine fault path.
- The next information-rich boundary is a selected live thread stack while
  `PRESENT_BEGIN > PRESENT_RETURN`, before the bounded run is stopped.
- Visible HUD pixels prove some Flutter output reached the QMP framebuffer;
  they do not prove a Sequoia render, native-surface composition, or healthy
  present loop.

### Hypotheses

1. **The unmatched Present again waits in Lavapipe/WSI.** Support would be a
   live `FEngine::loop` stack containing `lvp_pipe_sync_wait` and
   `wsi_common_queue_present` (or a directly nested queue-submit path).
   Refutation would be a complete selected stack that remains outside that
   wait path.
2. **The page-fault/Oops is a distinct FEngine execution path, not the caller
   of the unmatched Present.** Support would be an Oops/thread exit before a
   stable unmatched-present sample, or a selected stack outside the Present
   wait. Refutation would be a live stack at the unmatched boundary directly
   inside the Lavapipe/WSI wait.
3. **The black Sequoia ROI is a separate output/composition problem that can
   coexist with the present stall.** A stack capture alone cannot prove or
   refute this; after the present boundary is understood, retain a separate
   QMP pixel/surface discriminator.

### UNKNOWN

- Whether any unrecorded/deeper frame reaches FLR-0341's Lavapipe/WSI wait
  path. No captured top-eight frame contains `lvp_pipe_sync_wait`.
- Which Linux LWP produced the current-run Oops TID 715, and whether that TID
  maps to GDB's short LLVM stack or another `FEngine::loop` thread.
- Whether the missing Present return means blocking, thread fault/exit, or a
  different interruption; the observed event ordering is not causation.
- The current-run Oops faulting instruction's loaded object, source location,
  and root cause. Do not infer an LLVM defect or stack-address truncation from
  the opcode/address pattern alone.
- Why Sequoia pixels are absent, whether SUN setup produces visible scene
  output, and whether original material/texture/light or HUD composition is
  correct.

## Runtime result and visual evidence — `flr0401-0001`

- Candidate: patch 0334, rootfs SHA-256
  `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`;
  same pinned kernel/qemuboot and fixed 6144-MiB QEMU profile. No image build
  or product-source change occurred.
- Full `PRESENT_UNMATCHED` QMP capture at 2026-10-02 14:52:29 JST is
  1280x800, SHA-256
  `5511064a97cbef85b76cd44809e258f334cf9b18298fd1bfd47c2c894e740f1c`.
  Visually, the CPU/GPU/FPS HUD and Scenes button are visible at the top; the
  remaining area is black and Sequoia is not visible. The Sequoia ROI
  `[440,220,400,360]` is 144,000/144,000 black pixels, with zero chromatic or
  edge pixels. The HUD ROI `[0,0,320,200]` has 1,192 chromatic pixels.
- The first-live-state WAITING QMP capture is 1280x800, SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`;
  all four raw QMP video frames have this same hash and are uniformly black.
  Mini had no `ffmpeg`, so it retained raw frames rather than an MP4. A
  four-frame, 2-fps MP4 was encoded locally from those exact QMP frames and
  visually checked; it documents the WAITING state, not the later HUD frame.
- App identity at the live attach: PID 640, UID 1001, start value 2635;
  `READY=1`, `PRESENT_BEGIN=1`, `PRESENT_RETURN=0`, `SUN=1`. GDB identity
  recheck passed and all seven threads named `FEngine::loop` were collected.
  Six captured stacks wait on futex/condition paths: four are Mesa
  `lp_cs_tpool_worker`, one is Vulkan `vk_queue_submit_thread_func`, and one is
  in `libc++.so.1`. The remaining thread has two unresolved frames in
  `libLLVM.so.18.1` followed by a short/unusable unwind. No captured frame
  contains `lvp_pipe_sync_wait`; the short LLVM unwind prevents a stronger
  exclusion.
- Kernel journal records `Oops: 0000 [#1]`, `CPU: 3 PID: 715 Comm:
  FEngine::loop`, RIP `0x7fef595d1541`; focused coredump query is `EMPTY`.
  The GDB output did not record Linux `ptid`/LWP identifiers or the process
  mappings/build ID, so TID 715 cannot be correlated to a captured GDB thread
  or symbolized from this run.
- The observer command returned `FAIL` after runtime collection because its
  postprocessor forced a 1280x800 `full` ROI on the 720x400 pre-launch PPM
  (`region extends outside the PPM image`). This is a host-side analysis
  failure, not evidence that Flutter failed to start. The captured 1280x800
  live still was re-analyzed at its actual dimensions: full, HUD, and Sequoia
  regions all returned successfully with the pixel results above.
- Exact app/GDB-script/QEMU teardown passed: GDB script cleanup marker was
  recorded, final postflight reports `processes=0`, `qmp=ABSENT`, ports
  `10930,10931,10932:FREE`; an independent targeted process check also found
  no QEMU/runqemu/Flutter/BitBake/GDB process.
- Full evidence index: [FLR-0401-0001 manifest](../evidence/FLR-0401-0001.md).
  Review still: [full QMP PNG](../evidence/FLR-0401-0001/present-unmatched.png).
  Four-frame WAITING video: [QMP MP4](../evidence/FLR-0401-0001/waiting-4-frames.mp4).
  Raw PPM captures and serial/GDB logs remain at `$BUILD_EVIDENCE/flr0401-0001/qemu/`.

### Evidence-based hypothesis update

1. The captured stack does **not support** the prior FLR-0341 WSI-wait
   hypothesis: none of the seven recorded stacks contains
   `lvp_pipe_sync_wait` or `wsi_common_queue_present`. Because one LLVM stack
   is short and no TID/LWP mapping exists, this result does not prove that the
   Oops and unmatched Present are separate.
2. The Oops-to-thread relationship remains **UNKNOWN**: kernel TID 715 is not
   mapped to GDB's internal thread number/Linux LWP and no process mapping was
   saved. The next product diagnostic must capture those identities and the
   loaded-object/build-ID ranges before attributing the fault.
3. The live screenshot confirms a separate visible-output symptom: HUD is
   rendered while the Sequoia ROI is black. It does not identify whether the
   first missing boundary is scene draw, submit/sync, or surface presentation.

### Ticket disposition

This ticket is **Done only as the bounded observer/live-stack evidence unit**:
the exact image preflight, one unmatched-Present GDB capture, full QMP still,
four-frame video, visual review, runtime markers, and teardown were completed.
The observer's post-analysis failure is preserved as a separate FLR-0402
tooling defect. 3D display, original materials/textures/lighting, composition,
interaction stability, five-minute Present progression, and two-boot
acceptance remain open; this disposition does not satisfy the product goal.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | One unmatched Present plus one selected live `FEngine::loop` stack |
| Where | Exact 0334 Mini QEMU guest, existing Example Demo and Lavapipe/WSI path |
| When | First identity-stable `PRESENT_BEGIN > PRESENT_RETURN` sample; attach once |
| Who | Flutter PID/UID/start identity, selected FEngine thread, guest graphics stack |
| How | Bounded host polling, one deadline-derived 5–18-second GDB attach plus 2-second kill grace, QMP still/video, focused journal |

## Scope and controls

- Reuse the exact 0334 kernel/rootfs/qemuboot hashes, 6144-MiB QEMU profile,
  ports 10930–10932, Example Demo bundle, scene, arguments, environment, and
  existing evidence/build roles. Fresh preflight must verify each immediately
  before the single run.
- Preserve the FLR-0400 render-test environment exactly:
  `FLR0026_NATIVE_MODEL_MATCH=sequoia`,
  `FLR0026_NATIVE_MODEL_LIMIT=2`,
  `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1`, and
  `FLR0305_PRODUCTION_SCENE_LIGHT=1`. These are diagnostic overrides; this
  ticket cannot establish original material/lighting acceptance.
- Change only debugger supervision: launch the same Flutter app directly,
  observe its combined app/GDB log, and attach GDB once only after a live
  unmatched-Present precondition. Append bounded GDB output to that same log
  source so readiness and debugger evidence cannot diverge.
- At the trigger, bracket process identity and capture the full QMP still
  before GDB pauses the target. Preserve the controller's one four-frame video
  from the first identity-bracketed live state; label it WAITING if that was
  the first sample. GDB selects only threads
  named `FEngine::loop`, records at most eight frames per candidate, and
  expands only a stack containing `lvp_pipe_sync_wait` to 24 frames. Guest GDB
  is bounded to 5–18 seconds plus 2 seconds of kill grace, derived from the
  remaining deadline; the host wait reserves serial-return and post-attach
  identity-read time. If fewer than 26 seconds remain after the QMP still, skip
  the attach explicitly. If serial does not confirm GDB completion, issue no
  further guest serial commands and quit only this run's QMP-owned QEMU.
- Preserve the marker slice, bounded GDB/inferior log, focused kernel Oops and
  coredump query before exact app/QMP teardown. One run ID, one QEMU, one GDB
  attach; no retry after any result.
- Do not change product source, patch, camera, GLB, material, texture, light,
  Flutter UI, recipe, image, build inputs, cache, or Mini TMPDIR. Do not disable
  HUD/input/repaint to make the frame look better.

## Success criteria

1. TDD proves the direct launch uses the pinned app/environment and shared log;
   the GDB command fails closed on changed identity or matched Present; the
   selected-thread stack cap is 8 frames/24 only for `lvp_pipe_sync_wait`; the
   observer attempts attach at most once and preserves logs before teardown.
2. Fresh Mini preflight confirms exact image hashes, receiver revision,
   processes, ports, QMP socket, and unused `flr0401-0001` evidence path.
3. One QEMU run either records a live identity-matched selected stack at the
   unmatched boundary or records a precise bounded no-trigger/process-exit/
   attach-failure/timeout outcome. A missing stack is never treated as a root
   cause.
4. Full QMP still and four-frame video are preserved and visually inspected;
   Sequoia and HUD ROIs, image hashes, exact marker counts, Oops state, and
   capture identity are recorded. Only QMP screenshots/frames may be copied
   for review; no QEMU disk image, rootfs, or build artifact is copied to Mac.
5. GDB, app, QEMU, socket, and ports are cleanly detached/stopped and independently
   verified after the run. No unrelated process is touched.
6. Record the resulting discriminator and open the next one-factor task based
   on the actual stack. This ticket cannot claim that 3D, original materials,
   HUD composition, interaction stability, five-minute present, or two-boot
   acceptance is complete.

## Plan / Do / Check / Act

### Plan

- Freeze the 0334 image, Demo launch, environment, QEMU profile, and one-run
  evidence roles. Change observer/debugger supervision only.
- Use separate red/green slices for counters/run IDs, direct launch/GDB command,
  and the one-shot identity-checked trigger. No build; one fresh QEMU run only
  after committed bundle transfer and a clean Mini preflight.

### Do

- Task 1 adds strict READY/PRESENT/SUN counter preservation and accepts the
  fresh `flr0401-NNNN` run namespace in the Python and shell validators.
- Task 2 adds an opt-in direct Flutter launch using the same Demo bundle,
  identity capture, Wayland/XDG setup, diagnostic environment, timeout, and
  shared log. The default FLR-0400 launch command remains byte-for-byte fixed
  by a baseline SHA-256 contract.
- The one-shot GDB guest command validates PID/UID/start and unmatched Present
  counters, appends selected stacks to the shared log, and uses the historical
  FLR-0110 low-memory settings via `-iex` before attach. It loads only Lavapipe
  symbols, selects `FEngine::loop`, and caps collection at `bt 8` plus
  conditional `bt 24` for `lvp_pipe_sync_wait`; its timeout and kill grace total
  at most 20 seconds.
- Direct mode creates the fresh run-scoped app log once; app and GDB output
  append to that same file. The run-scoped GDB command file is base64-transferred,
  SHA-256 verified, removed by exact path in normal and EXIT-trap cleanup, and
  checks selected-inferior PID/UID/starttime/comm before symbol loading or
  thread enumeration. Empty, partial, identity-changed, no-thread, and
  no-stack outcomes are distinct; `COMPLETE` requires an actual stack frame.
- The controller consumes its one-shot before I/O, captures the dedicated
  `PRESENT_UNMATCHED` QMP still before GDB attach, checks identity around the
  still and attach, caps attach by the remaining global deadline, and retains
  callback errors without retry. The legacy default `gdb-run` command remains
  pinned by its byte-for-byte digest test.
- GDB timeout is derived from remaining wall-clock budget (5–18 seconds), with
  2 seconds for guest timeout kill grace, 4 seconds for serial return, and 15
  seconds reserved for post-attach identity verification. With less than 26
  seconds available after the still, the attach is skipped without launching
  guest GDB. Missing completion marker is treated as an unsafe unknown: local
  partial evidence is retained, guest serial collection/stop/script cleanup are
  skipped, and cleanup proceeds through QMP only.
- Script cleanup is issued only after this invocation receives the
  `FLR0401_GDB_SCRIPT=READY` marker from its preparation command. Creation uses
  shell noclobber to avoid overwriting a path that appears after preflight.
- No product source, image, recipe, build input, cache, or Mini build state was
  changed. One bounded Mini runtime ran after fresh owner/image/port/socket/
  evidence-path preflight; no concurrent process was touched.

### Check

- Task 1 red: 46 focused tests ran with 4 failures and 3 errors at the missing
  counter/run-ID contracts.
- Task 1 green: focused suite 46/46 PASS; QEMU start-helper `bash -n` and
  no-write Python syntax parse PASS.
- Task 2 red: the baseline-default launch digest passed; direct-mode and
  capture-command contracts exposed the missing APIs, and the CLI rejected
  `--launch-mode` (3 errors across 4 selected tests).
- Task 2 green: the final observer suite passed 52/52. Generated commands for
  all supported IDs and both launch modes parse as bash and POSIX sh; the
  default launch digest is unchanged; the CLI mode reaches the guest command
  builder.
- First local read-only review (not model-certified as GPT-6.1 Sol): exact
  range `7ad86a0..f7b1222` was reviewed. Findings were the app/GDB shared-log
  overwrite race, missing in-GDB identity recheck, and false `COMPLETE` on
  empty/failed stack collection. The current diff adds append-only shared
  logging, inferior identity validation, and explicit failure/partial outcomes.
  The specifically requested model-certified GPT-6.1 Sol re-review is pending.
- Task 3 red: six new controller cases initially errored because `run_once`
  did not yet accept the one-shot callback. Two additional review findings
  reproduced in tests: fixed guest timeout could outlive the host deadline and
  preflight rejection still led to script cleanup. After the fixes, the full
  focused suite passes 67/67. Coverage includes deadline-derived GDB timeout
  and identity reserve, no further guest serial commands after unconfirmed GDB
  completion, QMP-only teardown of that exact run, no cleanup after failed
  preflight, one-shot callback behavior, QMP-still-before-GDB ordering, and
  generated guest-script preparation/cleanup. GDB simulations reject PID
  reuse, missing threads/frames, and stack collection errors rather than
  returning `COMPLETE`.
- GPT-6.1 Sol review follow-up: first identified that GDB exit 5 (and other
  completed diagnostic outcomes) propagated as a serial command failure, so
  the observer dropped post-attach identity and guest kernel/coredump evidence.
  The capture command now records `FLR0401_GDB_CAPTURE_RESULT=<outcome> rc=<n>`
  and exits 0 once GDB has returned; a generated-shell test executes fake GDB
  exit 5 and verifies marker/log persistence and script cleanup. The next Sol
  pass found the race where guest counters become balanced after the host
  selected an unmatched sample; `PRESENT_MATCHED` now likewise goes to the
  shared log and exits 0 without launching GDB. Regression checks first failed
  at the nonzero shell status, then passed after the fix; observer integration
  confirms this completed skip is followed by identity recheck, guest evidence
  collection, app stop, script cleanup, and exact QMP teardown. The focused
  suite is now 69/69 PASS. The latest GPT-6.1 Sol review reported no further
  findings and confirmed both P2 gaps are closed.
- `make verify`: canonical, privacy, and shell checks passed; an earlier 203-test
  run had 202 PASS and one known unrelated FLR-0397 stale-run-ID failure in
  `test_serial_exec_capture_passes_strict_gate_without_setup_preamble`. The
  fixture invokes `flr0350_launch_gate.py --validate` without its now-required
  run ID. The latest default-sandbox attempt was blocked by five pre-existing
  localhost socket-bind `PermissionError`s. The same `make verify` with host
  permission ran 218 tests: 217 PASS and the same one unrelated FLR-0397 stale-
  run-ID failure; `make verify` stops at that Python gate.
- Remaining gates run separately: MCP smoke PASS; Markdown links FAIL on the
  same 11 historical missing targets (0391/0395 ticket links and 0338/0339
  QMP media links); file-size, QEMU/runtime harness, runtime-log-slice, Devtool
  finish/component-rebase, Mini recipe-patch, and Podman/bundle-handoff gates
  all PASS. No FLR-0401 link is missing. These checks do not include a Mini
  handoff, BitBake, QEMU, or runtime validation.
- Runtime acceptance review: fresh Mini preflight PASS; one exact-image
  unmatched-Present live GDB attach captured seven `FEngine::loop` stacks;
  full QMP still and four-frame WAITING video were preserved and visually
  reviewed. HUD ROI has 1,192 chromatic pixels; Sequoia ROI is 144,000/144,000
  black. Kernel Oops TID 715/RIP `0x7fef595d1541`, coredump `EMPTY`; Oops-to-LWP
  mapping remains UNKNOWN. The observer's final status is FAIL only because
  720x400 pre-launch PPM was analyzed as 1280x800; 1280x800 live captures
  re-analyzed successfully at their actual dimensions. Final postflight PASS:
  no processes, QMP socket absent, ports 10930–10932 free.
- Video media verification: Mini reports ffmpeg unavailable and retains four
  raw frames; all four raw PPM hashes match. The local H.264 review MP4 is
  1280x800, 2 seconds, exactly four frames, SHA-256
  `bc759243230a99f71f1be9c8366fe17d7680bb101441261dea37ba4d8bc7282c`;
  the PNG full still SHA-256 is
  `68aaf2609276d3dc2d325a7304aba7a8b9ad741e09857cb97555220b6e641308`.

### Act

- FLR-0401 closes as a bounded observer/live-stack evidence unit. The QMP
  analyzer failure is split into FLR-0402; the next product discriminator is
  a separate Oops TID ↔ GDB LWP/ELF-map correlation ticket. No root cause is
  assigned from this run. The global Fluorite goal remains active: Gate A/B,
  original materials/textures/lighting, input/repaint stability, five-minute
  Present progression, and two independent boots are still unproven.

## Impact

- **Build-time / packaging:** none; reuse the existing exact image and cache.
- **Runtime:** one bounded debugger attach briefly pauses the selected target;
  collect QMP video first and always detach.
- **Integration risk:** attaching to the wrong process, repeated GDB attaches,
  stale log parsing, or confusing another present-stall run could alter the
  observation. Prevent this with one run ID, strict PID/UID/start checks,
  unmatched-counter gating, one attach, and one shared bounded log.
