# FLR-0350 — correlate blocked Present sync with its release producer

- Status: Done
- Priority: High
- Owner: Mesa sync producer / FEngine submit / GDB / Mini QEMU evidence roles
- Created: 2026-09-28
- Predecessor: [FLR-0348](FLR-0348-watch-lavapipe-signal-without-fence-type.md)
- Runtime baseline: exact FLR-0335 image hashes recorded in FLR-0344
- Launch profile: exact FLR-0344/0348 diagnostic profile; conclusions are
  limited to that profile, not neutral production
- Run ID: `flr0350-0001` (one unchanged-image QEMU attempt only)
- Working log: [2026-09-28 FLR-0350 working log](../logs/2026-09-28-flr0350.md)

## Objective

Determine whether the producer associated with the FLR-0348 Present wait,
under its pinned diagnostic profile, executes and publishes either release
predicate (`sync->signaled` or `sync->fence`) to the *same sync-object instance*
used by that waiter. Correlate the submit, wait, producer, and object
lifetime/generation; a successful queue submit or a raw pointer match without
lifetime evidence is insufficient. This ticket does not establish neutral
production behavior.

This is one diagnostic boundary, not a rendering fix. Reuse the exact
FLR-0335 image and Example Demo. Do not change product source, image, scene,
HUD, camera, Light, material, texture, compositor, or memory settings. No
Devtool patch or BitBake build is in scope.

## Inherited facts from FLR-0348

- One exact-image run using the FLR-0344/0348 diagnostic launch profile
  reproduced queue-submit result 0 and Present-enter with `wait=true`, with no
  Present return during the observation.
- The waiter remained in Mesa 24.0.7 `cnd_wait` →
  `lvp_pipe_sync_wait_locked` → `lvp_pipe_sync_wait`.
- Both GDB hardware watches were accepted: `sync->signaled` and raw-address
  storage for `sync->fence`. They armed successfully, but neither hit during
  the 8.07-second interval; the values remained false/null.
- QMP showed a visible 2D HUD/metrics/Scenes control, while the fixed lower
  3D ROI was completely black in the still and all eight video frames.
- The observation does not prove that the fields never change, identify the
  expected producer, establish object lifetime, or prove causality between
  the stalled wait and the black ROI. Historical fixture and GLB screenshots
  are not production success evidence for this run.

## Current handoff state (2026-09-29)

- FLR-0351 is Done. Read-only Mini evidence proves the fixed receiver is clean
  at the exact delivered diagnostic tip, BitBake is idle, effective build
  roles match, and the existing bundle identity is verified.
- The original helper's terminal marker is UNKNOWN, but receiver state is
  independently proven. Do not retransmit or build; verify the runner hash
  against this source worktree before the one authorized launch.
- A fresh Mini runtime preflight found no QEMU, `runqemu`, or Flutter-auto
  process, free diagnostic ports/run ID, matching pinned image inputs, and
  sufficient memory/storage headroom. Recheck the runner hash and use the
  fixed one-shot runner; do not retry if any gate differs.

## Diagnostic-profile boundary

- The FLR-0344/0348 launch sets `FLR0026_TREAT_UNLINKED_FENCE_READY=1`, which
  bypasses Filament's unlinked-frame-fence readiness result. It also fixes
  existing diagnostic overrides including the unlit override, light skip/limit,
  model limit/match, wide camera, and runtime tracing. FLR-0350 must preserve
  this exact profile to retain the known Present-wait reproducer.
- FLR-0058 and FLR-0098 show that the bypass can restore frame-start/queue
  activity without restoring native 3D pixels. Its causal relationship to the
  Lavapipe Present stall is UNKNOWN. The profile may affect submission timing
  and object sequencing; results here are diagnostic-profile-specific.
- Astra's judgment-only review selected same-profile producer correlation:
  removing the bypass first may prevent reaching the relevant submission and
  make a missing stall inconclusive. Neutral-profile isolation is a separate
  follow-up, and any production-causality claim must wait for it.

## Pre-exec debugger gate decision

- Astra compared a self-`SIGSTOP` wrapper with a run-owned FIFO token gate and
  recommended FIFO. The wrapper must block in builtin `read(3)` on a newly
  created mode-0600 FIFO; the launcher records PID/start identity and verifies
  `/proc/<pid>/syscall` is reading the exact FIFO before attaching GDB.
- The release command sends only the exact `FLR0350_GO` token after checking
  the armed marker, root GDB process identity, matching `TracerPid`, wrapper
  start identity, FIFO descriptor, and read syscall. The wrapper exits on EOF,
  failed read, or any other token; only the exact token reaches direct `exec`.
- The armed marker proves only pre-exec attachment and exec/fork policy. It
  does **not** prove shared-library symbols are resolved. After GO, GDB must
  catch same-PID exec and the `libvulkan_lvp.so` load boundary, verify the
  exact Build ID and all required breakpoint locations before the first
  relevant call, and invalidate the experiment if debugger coverage is lost.
- The FIFO prevents Flutter exec before authorization; it cannot prevent a
  debugger failure immediately after GO. All stages are deadline-bounded;
  inability to prove the read state, attachment, process identity, symbol
  resolution, or callback coverage means no further release/observation and
  an UNKNOWN result. No fallback instrumentation method is allowed in this
  run.

## Static runtime map (FLR-0335 exact Lavapipe ELF)

- FLR-0342's runtime SHA-256 and Build ID were reverified on Mini:
  `5f72d1fb5dc375f86ffcb1bd16aed98b2f074c05acbfcabd9a0c920299d789b1` and
  `18eb7b64f7fcae9a4b5ef5bbe1fe58a65944a403`. The separate debug ELF hash is
  `461799d4298e981d49d9c1ade2094aaac1cff6cac89803dd121409b28216ee68` with the
  same Build ID. `addr2line` maps these runtime addresses to `lvp_pipe_sync.c`:

  | Function | ELF address | Source line | Observed field/lifecycle operation |
  | --- | --- | --- | --- |
  | `lvp_pipe_sync_init` | `0xc5d30` | 38 | initializes `fence` to null and sets `signaled` from its initial input |
  | `lvp_pipe_sync_finish` | `0xc5cf0` | 52 | releases a stored fence and destroys condition/mutex |
  | `lvp_pipe_sync_signal_with_fence` | `0xc6040` | 67 | sets `signaled` iff input fence is null; dispatches fence-slot reference update; broadcasts |
  | `lvp_pipe_sync_signal` | `0xc5c90` | 80 | sets `signaled=true`; broadcasts |
  | `lvp_pipe_sync_reset` | `0xc5c30` | 98 | clears `signaled`, releases the fence slot, broadcasts |
  | `lvp_pipe_sync_move` | `0xc5b80` | 117 | clears source fields, transfers fence/signaled state to destination, broadcasts both |
  | `lvp_pipe_sync_wait` | `0xc5d70` | 228 | wrapper for the wait path; the inlined locked wait/cnd_wait is recorded in FLR-0342 |

- Bounded disassembly confirms `signaled=sync+0x68` and `fence=sync+0x70`,
  consistent with FLR-0343's DWARF layout. `lvp_queue_submit` directly calls
  `lvp_pipe_sync_signal_with_fence` at `0xace91`. No direct call-site
  reference to `lvp_pipe_sync_signal` appeared in the filtered caller scan;
  it may be reached through a callback, but its registration/dispatch path is
  not yet established. Do not infer that it has no callers.
- The extracted Mini evidence copy's runtime `.gnu_debuglink` names
  `libvulkan_lvp.so`, and resolving it beside that copy produces a CRC warning.
  The separate debug ELF does share the Build ID and `addr2line` succeeds when
  explicitly pointed at it. This warning does not prove the FLR-0335 guest's
  own debug-file lookup is broken: FLR-0103 records guest GDB loading `.debug`
  files on a different rootfs. The exact FLR-0335 guest GDB must verify the
  Build-ID-matched symbols; explicitly load them only if automatic lookup fails.
- Downstream Mesa `SRCREV` and applied patch stack remain UNKNOWN. The
  Mini-side cache-resolution attempt exited while sourcing
  `oe-init-build-env`; the exact archived source was not reread in this
  iteration. Preserve FLR-0342's upstream archive hash as prior evidence, not
  proof of exact post-patch source.

## Competing hypotheses

1. **Expected producer is not invoked during the stall.** Prediction: the
   submit-to-wait association is established, but the corresponding producer
   boundary is not reached in the bounded window.
2. **Producer operates on a different sync object or generation.** Prediction:
   a producer runs, but its destination identity/lifetime differs from the
   waiter's exact object.
3. **Producer reaches the matched object without publishing either release
   predicate.** Prediction: matched producer entry and exit occur while both
   source-defined release predicates remain false/null.
4. **A predicate is published to the matched object but Present remains
   blocked.** Prediction: publication is observed for the same live object,
   yet Present does not return; record any subsequent reset before attributing
   the remaining fault to wake behavior.

## Success criteria

- Read the exact source/runtime version and identify every relevant producer
  path that can set either release predicate. Record function/source locations,
  call chain, object ownership, and lifetime/reuse semantics. Do not infer the
  producer solely from the wait function name.
- Account for signal, signal-with-fence, reset, move, init, and finish when
  defining object generation/lifetime. Prove whether signal is reached through
  the sync-type callback table and identify the matched queue-submit/wait
  relationship; a direct-call scan is not complete callback coverage.
- Prove a way to arm instrumentation before the first relevant submission and
  verify that target GDB resolves the matching debug ELF (load it explicitly
  only if automatic lookup fails). Use the approved FIFO gate: establish the
  exact blocked read, prove GDB attachment and catchpoint policy before GO,
  then stop again at same-PID exec and Lavapipe load to prove breakpoint
  resolution before relevant calls.
  Capture the submit-to-wait identity and object generation, producer entry
  and exit, predicate publication (or lack of it), and Present return.
  If symbols, call coverage, or object lifetime cannot be established, stop
  before runtime and mark the gate UNKNOWN.
- Use the exact pinned FLR-0335 image and unchanged FLR-0344/0348 diagnostic
  launch profile in one QEMU instance. Observe through
  at most 10 seconds after the matched Present wait begins. Log only the
  identity and markers required by this ticket; do not dump all threads or
  unfiltered logs.
- Decide the producer-boundary gate precisely: **green** only if a qualifying
  predicate is published to the matching live object; **red** only if complete
  instrumentation proves the producer is absent, targets another object, or
  exits without publication. A green producer gate is not a 3D-rendering fix.
- Capture QMP full-frame still/eight-frame sequence and fixed-ROI pixel summary
  from the same run. Stop the recorded app, QMP-quit the same QEMU, and verify
  zero residual application/QEMU/compositor processes and run-owned sockets.
- No retry, image build, `do_patch`, Devtool operation, product patch, or
  experimental scene/light/HUD change in this ticket.

## Plan / Do / Check / Act

### Plan

1. Verify the predecessor record and exact pinned image identity.
2. Map source and runtime producer paths and object lifecycle; compare the
   waiter's object with the submit/producer object before designing a probe.
3. Validate the FIFO gate and instrumentation coverage/startup order locally.
   Keep the observation bounded and avoid unrelated log collection.
4. Commit diagnostics locally, transfer the canonical bundle to the fixed
   Mini receiver, and verify remote hashes and immediate runtime preflight.
5. Run once on the unchanged image, collect QMP evidence, and independently
   prove teardown.

### Do

- Iteration 2 drafted the guest preflight, FIFO-blocked production launcher,
  and separately gated exact-token release command. Host-side shell syntax,
  diagnostic profile/CLI equivalence, size checks, and invalid/exact-token
  behavior passed. These are command artifacts only: no guest command, GDB,
  QEMU, build, product patch, or image change has run in FLR-0350.
- Iteration 3 added lifecycle-aware GDB event logging, the post-watchpoint
  matched-wait marker, exact PID/start identity checks, 180-second GO-relative
  window, 10-second matched-wait window, failure teardown, and a ticket-specific
  Mini runner. The compressed GDB script is sent in four <=4096-byte serial
  commands and verified by guest SHA-256 before launch. Static checking passes;
  target GDB behavior and QMP evidence are still unverified.
- Self-review found that failure cleanup could continue to runtime/QMP capture
  if the exact GDB process had not been confirmed stopped. The runner now skips
  guest state/QMP evidence in that case and QMP-quits the owned VM; its static
  checker asserts the stop-before-capture ordering. This is a fail-closed
  evidence gap, not a runtime diagnosis.
- Read-only Mini preflight found no QEMU/runqemu/flutter-auto process, no
  listener on serial/SSH/telnet ports 10930–10932, an unused fixed evidence ID,
  and exact FLR-0344 helper hashes. No Mini files were changed and no QEMU was
  started.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Canonical source/ticket | Guard, privacy, checkpoint, and full verification pass; one In Progress unit | Guard, privacy, checkpoint, and `make verify` PASS; FLR-0350 remains sole In Progress | PASS (local) |
| Runtime identity/symbol map | Exact ELF/debug Build ID, producer fields, call and lifecycle locations | PASS for runtime/debug ELF hashes, Build ID, addresses/lines, field operations, and direct `lvp_queue_submit` → `_with_fence` call; callback registration and downstream Mesa patch provenance UNKNOWN | PARTIAL |
| Diagnostic-profile boundary | Fixed known reproducer; no claim of neutral production behavior | FLR-0348 launch has unlinked-fence-ready and light/model/camera/unlit diagnostic overrides; Astra recommends preserve for this producer gate and limit conclusions to this profile | PASS (scope fixed) |
| Pre-exec FIFO gate source | One explicit, fail-closed token authorizes direct app exec | Static check passed, but runtime gate returned `FLR0350_FIFO_READ_GATE=FAIL`: fd 3 points to the FIFO while the blocked `read` syscall reported fd 0; the gate required fd 3 and stopped before GDB attach/app exec | FAIL (harness gate; no producer observation) |
| Bundle handoff preflight | Fixed role configuration and TMPDIR validation pass before receiver mutation | FLR-0351 is Done; receiver exact tip, clean worktree, idle BitBake, effective `TOPDIR`/`TMPDIR` agreement, and existing bundle SHA are independently verified; no retransmission needed | PASS (receiver state) |
| Debug-symbol loading | Correct debug ELF identified and usable by FLR-0335 guest GDB | Build IDs match and `addr2line` works; Mini evidence-copy debuglink CRC warning; prior auto-load was on another rootfs; exact guest lookup not yet proven | Pending |
| Pre-submit instrumentation and teardown | All relevant producer paths observable before first submission; no post-window observation after failed debugger stop | Seven embedded GDB Python blocks parse, but GDB never attached because the launch gate failed | UNKNOWN (runtime instrumentation not reached) |
| Runtime association | Submit, waiter, producer, predicate, and Present result attributable | No attach-GDB/GO/matched-wait stage ran because launch gate failed; producer/object relationship not observed | UNKNOWN (not reached) |
| QMP and teardown | Same-run screenshot/ROI plus zero residuals | Full-frame still and eight frames captured; post-run frame uniformly black, but app did not launch. QMP quit accepted and independent host check found zero QEMU/runqemu/flutter-auto processes and no QMP socket; guest app-stop reported unknown identity and runner cleanup exited 1 | PARTIAL (host resources clear; guest stop not proven) |

### Act

- This one-shot experiment is complete as a partial diagnostic result. The
  producer correlation acceptance criteria were not met; do not interpret the
  black post-run image as Flutter output because the fail-closed launch gate
  prevented the app exec. The syscall/fd mismatch and conservative guest
  cleanup are transferred to a separate harness-correction ticket. A later
  runtime attempt must use a new ticket and run ID.
- FLR-0354 owns the launch-FIFO descriptor check and safe failed-launch
  cleanup behavior. Validate the gate against the observed guest process
  before authorizing any new QEMU run.
- Keep the overall 2D+production-3D capability open until both appear in the
  same QMP frame under the intended production flow.

## Run outcome (2026-09-29; bounded attempt complete, producer result UNKNOWN)

- Fixed run `flr0350-0001` ran once and exited 1 at the pre-exec FIFO gate.
  The guest reported `pid=708`, `comm=sh`, `state=S`, `uid=1001`, fd 3 linked
  to `/run/user/1001/flr0350-go.fifo`, while `/proc/<pid>/syscall` began
  `0 0x0` (read syscall, descriptor 0). The current gate expects `0x3` and
  reports `FLR0350_FIFO_READ_GATE=FAIL`. The guest's fd 0 target was not
  recorded, so whether that descriptor was the same FIFO remains UNKNOWN.
- No attach-GDB, GO release, symbol gate, or matched-wait stage ran; guest
  reported `flutter_processes=0`. Therefore this run says nothing about
  Flutter rendering, the 3D producer, or the prior colored Sequoia evidence.
- QMP pre-launch showed the AGL startup splash. The post-run full frame and
  all eight video frames were black (post-run PPM SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`;
  every sequence frame had the same hash). The 1280x800 analysis reported
  luma `[0,0]`, zero chromatic pixels, and an undetectable geometry indicator.
  Since Flutter never launched, this black frame is not a renderer result.
- Runner cleanup reported `FLR0350_APP_STOP=FAIL` and
  `FLR0350_FIFO_CLEANUP=FAIL` because the expected process identity was
  unknown. QMP quit was accepted; an independent Mini check found zero
  residual QEMU/runqemu/flutter-auto targets and no QMP socket. Host cleanup
  is proven; guest app-stop is not.
- Evidence (QMP-only):

  ![Pre-launch AGL splash](../evidence/FLR-0350-qmp-run-0001-pre-launch.png)

  ![Post-run QMP frame after the failed pre-exec gate](../evidence/FLR-0350-qmp-run-0001-post-run.png)

  [Eight-frame QMP sequence (H.264, 8 seconds)](../evidence/FLR-0350-qmp-run-0001-post-run.mp4)

  PNG hashes: pre-launch `36f52fb5ea8b95fbe9ceb5415efca8c20bf355b511bdb057c0670ea020ac689d`;
  post-run `3e25a09ca6defc8efa884ff9945f86dea746b99e7fd6c70fdfdfa8109877351a`.
  Video SHA-256: `51dd4a38b3541618548e81450c678c721c8cbc50b261e95c57444cc1cb091f6c`.
- Conclusion: FLR-0350 is closed as the completed one-shot experiment record,
  not as a producer-correlation or 3D success. The producer result and
  original correlation acceptance remain UNKNOWN. The overall 3D objective
  stays open; the next task is a separately ticketed runner gate/cleanup fix.

## UNKNOWN

- Exact release-producer function(s), all publication paths, submit/wait
  object mapping, pointer lifetime/generation, and whether the instrumentation
  can be armed before the first relevant submission remain UNKNOWN until the
  static and runtime gates prove them.
- Whether `lvp_pipe_sync_signal` is installed in the runtime sync-type callback
  table and the complete indirect producer call chain.
- Whether guest fd 0, used by the blocked shell `read`, resolved to the exact
  pre-exec FIFO; the run recorded fd 3's target but not fd 0's target.
- Whether FLR-0335 guest GDB automatically resolves the matching debug ELF;
  explicit symbol loading may be needed if the exact-image check fails.
- Whether the diagnostic unlinked-fence-ready override causes, exposes, or
  merely coexists with the Lavapipe wait stall; FLR-0350 will not answer the
  neutral-production question.
