# FLR-0355 — relay a fresh run ID and retest the FIFO gate on QEMU

- Status: In Progress
- Priority: High; blocks the next producer-correlation runtime attempt
- Owner: Mac runtime-harness / Mini QEMU / QMP evidence roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Predecessor: [FLR-0354](FLR-0354-fix-flr0350-fifo-launch-gate.md)
- Plan: [FLR-0355 plan](../../docs/superpowers/plans/2026-09-29-flr0355-fresh-fifo-gate-runtime.md)
- Working log: [FLR-0355 log](../logs/2026-09-29-flr0355.md)
- Fresh run ID: `flr0355-0001` (one attempt only)

## Purpose

Make the fresh run ID deterministic from the host runner through QEMU preflight
and start, then use the corrected actual-FD FIFO gate in one unchanged-image
Mini-hosted QEMU attempt. Capture the complete QMP frame, an eight-frame QMP
sequence and MP4, runtime evidence, and exact teardown. This is a diagnostic
gate, not a promise that the producer will be observed or that 3D will render.

## Facts

- FLR-0354 corrected the gate predicate to compare the actual blocked `read`
  descriptor's FIFO type/device/inode with the run-owned FIFO and to save
  process identity before evaluation. Its commits are prerequisite commits on
  this branch; no product source/image changed.
- `work/commands/FLR-0350-run-sync-producer.sh` accepts a positional fresh ID,
  uses it for the evidence parent, and validates `flr0355-0001` in `--check`.
- The original pre-fix inspection found it invoked `bash "$start_script"`
  without passing the ID or a mode.
- In that initial baseline, `work/commands/FLR-0350-qemu-start.sh` defaulted to
  consumed `flr0350-0001` and rejected any other ID. The runner and starter
  therefore disagreed before QEMU launch.
- The handoff is now repaired locally: the runner calls an ID-bearing,
  non-mutating `preflight` before creating the evidence parent, records that
  successful result, then calls `start` with the same ID. The starter requires
  the ID and mode, checks it with the shared validator, and repeats the
  process/port/helper/image checks before creating the QEMU run directory.
- The starter still invokes the existing QEMU harness preflight after its run
  directory is created, followed by the unchanged harness start. That second
  validation protects against changed host state between checks; if it fails,
  this one-shot ID is consumed and must not be retried.
- Regression coverage is green: 27 focused tests pass, including rejection of
  missing/consumed IDs and the preflight/start ordering. `--check` passes and
  reports `FLR0350_TARGET_PREFLIGHT=NOT_RUN qemu=NOT_STARTED`.
- The seven-file local harness/docs change is committed on
  `feature-flr-0355-fresh-runtime-gate` as `1b3f90c` using the repository's
  privacy-approved integration-role metadata. No push occurred.
- The documented role variables were absent from the current process, but the
  established fixed-role handoff was recovered from prior successful helper
  history without recording its values. The existing bundle helper transferred
  the committed tip; Mini reported the exact receiver revision and effective
  TOPDIR/TMPDIR checks PASS.
- The first handoff-helper invocation exposed a plan error: it requires
  hexadecimal commit objects, not the branch name `dev-mini-recovery`; it
  failed at argument validation before creating a bundle or accessing the
  network. The plan now resolves both refs with `git rev-parse --verify`.
- The corrected hash-based helper invocation failed closed at the unset
  `BUILD_HOST` requirement, before bundle creation or SSH. No Mini state changed.
- One Mini-hosted QEMU attempt ran against the pinned existing image. Guest
  readiness, production-profile preflight, GDB script transfer, and paused
  launch wrapper all passed, but the runner stopped before the actual FIFO
  observation because it had not staged the observer command. QMP still/eight
  frames and teardown evidence were captured. No BitBake build or Devtool
  operation occurred.
- The FLR-0350 run stopped before Flutter/GDB execution; its black QMP image
  is not evidence about Flutter or 3D.
- The approved QMP capture helper writes PPM frames, not MP4. The project
  runtime-evidence procedure transfers only QMP frames to the Mac and encodes
  the reviewable video there with FFmpeg.
- The current agent shell still has no `BUILD_*` role variables loaded. This
  did not prevent the already-authorized transfer: the same fixed helper role
  set used by earlier successful handoffs was reused transiently and was not
  printed or written to Git.
- No `CONTEXT.md` or runtime/graphics ADR was found in this checkout. The
  accepted branch workflow in [ADR-0002](../decisions/ADR-0002-git-branch-workflow.md)
  applies; the behavior/evidence source of truth is `TASKS.md`, FLR-0350/0354
  tickets and logs, the starter/runner, and the runtime evidence procedure.

## Capability contract

| Field | Contract |
| --- | --- |
| Requested capability | Continue toward visible Fluorite 3D by obtaining an attributable runtime observation after the corrected FIFO gate. |
| Target/environment | The fixed Mini-hosted Yocto `runqemu` environment with the exact pre-existing FLR-0335 kernel/rootfs/qemuboot artifacts; no image rebuild. |
| Stimulus | One invocation of the production diagnostic runner with `flr0355-0001`; its QMP/GDB flow is unchanged except for correctly relaying that run ID. |
| Expected observation | Starter preflight and start use the same fresh ID; the actual syscall FD target is proven against the owned FIFO before GDB attach/GO; QMP full frame and frame sequence are attributable to that instance. |
| Repeatability | One attempt, because the guest and evidence gate are stateful and the ID is consumed once the run directory is created. |
| Identity | Branch tip and bundle receiver revision; pinned kernel/rootfs/qemuboot hashes; QMP socket/PID for this run; guest process identity from the FLR-0354 gate. |
| Evidence | Red/green regression test; bounded runner logs; QMP-only PPM still and eight frames; MP4 derived only from those frames; SHA-256 and fixed ROI pixel analysis; teardown evidence. |
| Scope/stops | Harness-only; no recipe/image changes or build. Stop before launch on missing role config, dirty/mismatched receiver, existing target process/port/socket/run ID, or artifact hash mismatch. Do not retry the run ID or use global kills. |

## 4W1H and focus

| Dimension | Observation |
| --- | --- |
| What | At the initial baseline, the host accepted `flr0355-0001`, but the QEMU starter fell back to `flr0350-0001`; that runtime attempt could not be attributed to a fresh ID. The local relay fix is now committed; target retest is pending. |
| Where | Mac-side runner → QEMU starter handoff → Mini `runqemu`/QMP boundary. |
| When | Before the first runtime process launch in the next producer-correlation attempt. |
| Who | Mac harness role validates and transfers the committed runner; Mini QEMU role validates image/process identity and starts/stops the owned VM; QMP evidence role captures pixels. |
| How | Runner passes a validated argument; starter independently checks the same ID in a non-mutating preflight and a separate start phase. |

### Ranked hypotheses

1. **Confirmed in the pre-fix baseline:** absent ID propagation made the starter use the consumed default and reject or collide before QEMU started. The current source fix is locally tested; the Mini runtime retest remains pending.
2. **Unknown until target observation:** the guest supports the exact `stat -L -c` observation command. If unsupported, the corrected fail-closed gate stops before GDB/GO.
3. **Unknown until target observation:** the actual blocked syscall FD resolves to the same FIFO object as the owned gate. A name-only match is insufficient.
4. **Unknown until target observation:** after the gate passes, GDB can attach and the producer/wait path reaches the selected watch window.
5. **Independent visual question:** whether the QMP 3D region contains rendered content. Gate/present/log markers cannot substitute for QMP pixels.

## Root-cause/countermeasure decision

The first observed process divergence is in the host start handoff, not in
Flutter: a fresh run ID is validated by the runner but not relayed to the
starter, whose fallback is the already-consumed ID. The minimal countermeasure
is an explicit ID-bearing, read-only preflight followed by an explicit
ID-bearing start; the starter rejects missing/consumed IDs via the shared
validator. This changes only diagnostic shell/Python harness behavior. It has
no build-time, packaging, or product-runtime impact. The sole runtime impact
is one 6-GiB QEMU instance using the existing pinned artifacts. Integration
risk is confined to the local runner/starter contract and is covered by a
regression test before transfer.

## Competing explanations after the handoff fix

| Hypothesis | Prediction | Falsifier/experiment | Current result |
| --- | --- | --- | --- |
| H1 starter ID mismatch | Preflight rejects or resolves a different run path | Assert same ID in both runner calls; invoke `--check`; verify QEMU start uses exact ID | Source defect fixed locally; 27 tests and `--check` pass; Mini/runtime confirmation pending |
| H2 guest stat syntax unavailable | Gate observation command errors or produces no valid marker | Capture bounded serial observation and exact target command result before GDB/GO | UNKNOWN |
| H3 actual FD is not the gate FIFO | Device/inode/type mismatch causes strict reject | Compare actual syscall FD target and gate FIFO | UNKNOWN |
| H4 producer wait path remains unresolved | Corrected gate/attach succeeds but wait marker or watch result does not reach a producer hit | Bounded GDB sequence on the same run/image | UNKNOWN |
| H5 3D remains absent for a separate reason | QMP HUD may be visible while fixed ROI has no chromatic/geometry pixels | Analyze and inspect the complete QMP frame independently of logs | UNKNOWN |

## Scope

### In scope

- A red/green host-runner/starter run-ID propagation regression test.
- Explicit read-only starter preflight and explicit start using the same ID.
- Existing fixed-bundle transfer to the Mini receiver, exact tip check, one
  unchanged-image QEMU attempt, QMP visual evidence, and targeted teardown.
- Full-frame visual inspection plus independent 2D and fixed-ROI 3D pixel
  analysis; MP4 generated from the QMP frames on the Mac.

### Out of scope

- Product source, Devtool, recipe, patch-stack, image, or build changes.
- Changing camera, light, material, scene, compositor, or QEMU graphics profile.
- A second run, another run ID in this ticket, a retry of `flr0355-0001`,
  copying kernel/rootfs/qemuboot to the Mac, or recording the Mac desktop.
- Claiming producer causality or 3D success from a gate/log marker, static
  texture, HUD, or black screenshot alone.

## Success criteria

- [x] The new test is red before the edit and green after it; it proves the
  same fresh ID reaches both starter modes and the consumed ID is rejected.
- [x] `--check` passes, preserves the exact diagnostic profile and hash pins,
  and explicitly reports `QEMU_NOT_STARTED`.
- [x] The Mini receiver is the exact committed bundle tip; no BitBake build or
  product/image mutation occurred.
- [x] The single QEMU attempt used pinned artifacts and fresh
  `flr0355-0001`; a QMP full frame and eight QMP frames were retained.
- [ ] The actual-FD gate passes before attach/GO, or a gate-specific fail-closed
  reason and serial evidence are recorded. The current run did not reach this
  gate; its one-shot ID is consumed and will not be retried.
- [x] A QMP still and H.264 MP4 are visible in this conversation; hashes,
  resolution, frame count/FPS, full-frame summary, and ROI summary are logged.
- [x] Cleanup proves recorded app stop, QMP quit, QEMU exit, socket removal,
  and zero matching QEMU/runqemu/Flutter/compositor processes.
- [x] 2D/HUD and 3D ROI verdicts are separate. This capture is uniformly black;
  it is not evidence about Flutter rendering because the run stopped before
  GDB attach/GO. 3D is not established.

## Plan / Do / Check / Act

### Plan

1. Add a red regression at the runner/starter boundary.
2. Pass the fresh ID to both read-only preflight and start; reject the consumed
   ID in the starter itself.
3. Run all local static/privacy gates and commit only FLR-0355 harness/docs.
4. Transfer the exact bundle tip using the established Mini receiver workflow.
5. Verify target process/port/path/artifact preconditions, then launch once.
6. Inspect QMP full frame before interpreting the fixed 3D ROI, create the
   video from QMP frames on Mac, and prove teardown.

### Do

- Initial evidence and failed tool attempts are in
  [the FLR-0355 working log](../logs/2026-09-29-flr0355.md).
- The runner/starter contract is implemented and locally verified. The exact
  bundle was transferred and one QEMU attempt ran; Iteration 5 of the working
  log records that the runner failed to stage the FIFO-observer command before
  it attempted to execute it. The observer gate, attach, and GO did not run.

### Check

| Gate | Expected evidence | Result |
| --- | --- | --- |
| Run-ID red/green | Regression fails before edit, passes after | PASS: prior red was 25 tests/2 new failures; current 27 tests pass |
| Local runner | `--check`, syntax, profile parity, existing tests | PASS: both `bash -n`, focused tests, exact profile parity, and `--check`; QEMU NOT STARTED |
| Documentation gates | Privacy and checkpoint contracts pass; markdown links resolve | Privacy/checkpoint PASS; `make check-markdown` still fails on 9 pre-existing FLR-0338/0339 QMP evidence links, none in FLR-0355 |
| Mini handoff | exact bundle SHA/tip and fixed receiver state | PASS: exact receiver tip; bundle SHA recorded in Iteration 5 |
| Runtime | one run ID, target/image identity, actual-FD FIFO predicate | PARTIAL/FAIL: guest and launch setup passed; missing staged observer command stopped the run before the predicate |
| Visual | QMP full-frame and eight-frame sequence, MP4, pixel summary | CAPTURE PASS; full frame and 3D ROI uniformly black; Flutter rendering not reached |
| Teardown | no app/QEMU/process/socket residue | PASS: app/FIFO cleanup, QMP quit, zero residual target processes |

### Act

- Any further runner fix or runtime attempt is a distinct ticket with a new
  run ID. Do not retry `flr0355-0001`.

## Visual evidence

- `flr0355-0001` QMP still: `$EVIDENCE_ROOT/flr0355-0001/qemu/post-run.ppm`,
  1280x800, SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
- QMP-only H.264: eight frames at 1 fps, 1280x800; the Mac review copy is
  outside Git. All eight frames and the still have the same pixel hash.
- Full frame and fixed 3D ROI are pure black: 0 changed pixels, 0 edge pixels,
  0 chromatic pixels, luma range `[0,0]`. The QMP capture is shown in the
  conversation. Because the run stopped before attach/GO, it is not a Flutter
  rendering verdict.

## UNKNOWN

- Whether the exact-FD FIFO observation passes once its command is staged and
  invoked on a fresh runtime.
- Whether GDB attachment, GO, producer correlation, and any Flutter/3D drawing
  occur after that gate.
