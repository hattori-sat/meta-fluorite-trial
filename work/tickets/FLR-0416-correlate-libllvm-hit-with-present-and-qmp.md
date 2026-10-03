# FLR-0416 — correlate the first libLLVM hit with present and QMP

- Status: In Progress
- Priority: High
- Created: 2026-10-03
- Owner: guest GDB observer / UID-1001 Example Demo / Mini QEMU / QMP evidence
- Branch: `feature-flr-0416-capture-first-hit`
- Predecessor: [FLR-0415](FLR-0415-prearm-libllvm-breakpoint.md)
- Candidate baseline: [FLR-0410-0001](../evidence/FLR-0410-0001.md)
- Working log: [FLR-0416 working log](../logs/2026-10-03-flr0416.md)
- Execution plan: [FLR-0416 plan](../../docs/superpowers/plans/2026-10-03-flr0416-first-hit-observer.md)

## Work unit

Correct the deterministic GDB first-hit observer failure, then perform exactly
one fresh run of the unchanged FLR-0410 image. Correlate the target hardware
breakpoint with the guest boot/process identities, caller mapping, app-present
counters, guest clocks, kernel state, and QMP screenshots immediately before, at, and
after the hit. This is diagnostic only: no product/layer change, build,
Devtool/BitBake operation, image or cache mutation, or product acceptance run.
After a clean local ticket commit and read-only Mini ownership check, the
official handoff helper may transfer that helper-only commit to the fixed
receiver so the diagnostic commands are available there; it must not start a
build or change the product image.

## Purpose and success measure

The prior run reached the target breakpoint, but nested formatting raised
`TypeError` before the `-hit` marker or explicit hold was proven. The success
measure here is a deterministic observer whose early `HIT_BEGIN` is followed
by a separate post-callback `HIT_READY` only after exact identity/PC and
all-app-thread stop checks. It remains held until a digest- and
identity-validated controller release, or accepts a controller abort without
continuing. Caller unwind can be UNKNOWN while QMP evidence is still captured;
that gap blocks release. This yields enough identity/time/present/QMP evidence
to choose the next product boundary without treating a breakpoint hit or black
post-exit frame as a product verdict. App Vulkan-present markers are not
compositor-present counters; live PC/caller PC is available only at a
controlled stop. Guest and host monotonic clocks have different origins, so
report capture intervals rather than false simultaneity.

## Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | First-hit observer marker/hold failed after target hardware breakpoint was reached | FLR-0415 transcript and observer source |
| Where | GDB Python callback on UID-1001 Example Demo; Mini QEMU; unchanged FLR-0410 image | FLR-0415 ticket, exact image manifest, runtime log |
| When | At the first `libLLVM+0xb1d541` hit, after one present return and a second unmatched begin marker | FLR-0415 bounded GDB/app transcript |
| Who | GDB observer, Flutter frame-engine thread, Mini runtime evidence role | GDB LWP and process identity records |
| How | Nested `%` formatting in the generated command list raised TypeError before marker creation; QMP samples lacked live-process/present brackets | Exact GDB source expression and bounded log; FLR-0415 screenshots |

## Priority selection

- Compared strata: observer failure versus potential target/app failure; the
  target breakpoint is already shown reachable on the exact candidate.
- Selected focus: make the first-hit observation reliable before any product
  source change.
- Selection evidence: the previous observer failure prevents distinguishing
  a normal helper call from the first renderer/synchronization failure. One
  corrected run can add caller mapping, precise process/time/present state, and
  live QMP brackets at all three stages.

## Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| GDB/Python gate | Exact FLR-0410 rootfs | guest GDB accepts the typed hardware-breakpoint callback and marker helper | GDB 14.2 Python/load-catch passed in 0415; hardware-breakpoint Python API not yet tested | 0415 preflight transcript |
| Load target DSO | Verified Build-ID, PT_LOAD, live mapping | Save identity and hold before the target VMA executes | 0415 armed the verified hardware breakpoint; no controlled load-stage QMP capture | 0415 GDB transcript |
| First target hit | Exact breakpoint address | Marker first, bounded stack/register/caller map, inferior remains stopped | The nested-format callback raised TypeError and no hit marker was recorded | 0415 GDB transcript and script |
| QMP observation | Same QEMU and exact run | Guest boot ID and process/app-present/clock snapshots bracket each QMP capture | QMP frames were black but their relationship to the inferior/presents was UNKNOWN | 0415 QMP samples and mismatched timestamps |
| Release and continuation | Captured hit evidence | Explicit release, single continuation, bounded post-hit capture | Not proven in 0415 | Missing hit/release markers |

## Problem point

The first normal-process boundary failure is not established. The confirmed
process/tooling problem is the generated GDB callback formatting expression:
outer `%` interpolation also consumes the callback's inner `%d/%s`, so the
inner expression receives an extra argument and raises `TypeError` before the
hit marker is created. Runtime/pixel causal boundary remains UNKNOWN.

## Ideal condition and gap

- Ideal: a constant `HIT_BEGIN` marker is flushed before optional diagnostics,
  the same guest boot/app identity is verifiably stopped and retained until
  evidence-validated explicit release, and every QMP frame is bracketed by exact process
  identity, host/guest clock bounds, app-present, and kernel state.
- Current: the address is reachable, but the marker/hold and frame-to-present
  relationship were not demonstrated.
- Gap: instrumentation reliability and event correlation, not yet a proven
  product or LLVM defect.

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| Nested formatting in the old hit command consumes the callback format tokens twice | The old command raises before `-hit`; constructing an equivalent record through typed data avoids generated command formatting | Unit test of the old failure shape and new helper; actual guest GDB smoke | Confirmed for the observer TypeError; product causality UNKNOWN | FLR-0415 exact source line and error text |
| The app/GDB independently exited before a stable hit hold | Correct observer still cannot prove matching inferior/GDB identity after the target stop, or a first crash precedes it | One identity-bracketed run; preserve exact first exit/fault boundary | UNKNOWN until FLR-0416 runtime | FLR-0415 lacked reliable marker/exit ordering |
| The target helper is a normal call and not the initiating rendering fault | Caller resolves to a normal caller and the app advances/presents after release without a new fault | Caller mapping plus present/QMP/process comparison at load/hit/post-release | UNKNOWN until FLR-0416 runtime | FLR-0415 return address unresolved |

### Confirmed root cause

Only the instrumentation TypeError is explained: the old callback source
embedded `%d`/`%s` format tokens inside a string formatted by an outer `%`
operation, then evaluated that callback format a second time. This broke the
observer's marker/hold path. It is not the root cause of black rendering or the
earlier FEngine Oops; those remain UNKNOWN.

## Scope

### In scope

- A testable GDB observer and bounded, ticket-scoped guest commands.
- One owner-free QEMU run on the exact unchanged FLR-0410 candidate.
- QMP capture at the pre-hit library-load hold if safely controllable, at the
  first target hit, and after explicit continuation; all performed stages are
  bracketed by identity/time/app-present/kernel state.
- Exact teardown, artifact hash postflight, evidence manifest, and push-free
  local commit.
- One standard `scripts/handoff-fluorite-bundle.sh` transfer of the committed
  ticket/helper-only change set to the fixed Mini receiver, only after a
  read-only ownership check; no manual SCP/receiver update path.
- Mac-side preview export of only allowlisted QMP screen frames after exact
  QEMU teardown; raw PPMs and logs remain on Mini. The Mini host does not need
  FFmpeg installed.

### Out of scope

- Product/layer/source changes, Devtool, BitBake, `do_patch`, image build,
  product bundle, or cache cleanup.
- Camera/material/texture/light/scene/input/present/composition changes.
- Calling this breakpoint, a black screenshot, or any one present result a
  product-render pass or root cause.
- Five-minute/two-boot product acceptance; that requires a later final image.

## Success criteria

- [x] Focused Mac regression tests cover exact caller-map selection, missing/
  ambiguous-map fail-closed behavior, deterministic JSON, create-only output,
  controller ACK/manifests and identity-matched abort decisions. Host preflight
  tests cover unreadable/unresolved proc entries, confirmed disappearance,
  hidepid, zombie ownership, missing/failed `ss`, and occupied/free ports.
  Guest-consumed JSON is atomically published; controller and guest share a
  540-second collection window with a 60-second guest abort grace. Host abort
  publication has its own monotonic 50-second cap inside that grace. Before
  every incremental kernel-journal query, probe the saved cursor before and
  after the read using `journalctl --cursor=<saved> --lines=+1 --show-cursor`
  and require exactly one returned cursor equal to the saved anchor on both
  probes. This detects nearest-entry fallback when an entry has rotated out
  during the read. Only then may exact `-- No entries --` mean zero new
  records; preserve the verified anchor. Missing, ambiguous, or different
  cursor output fails closed; the two queries are not an atomic journal lock.
  Start the load deadline before GDB/Example Demo launch and the hit deadline
  before load-release publication; each stage must inherit the original
  deadline. If a release is published but its ACK cannot be validated, record
  acceptance and inferior-held state as UNKNOWN and require exact teardown.
- [ ] Guest GDB smoke validates Python subclass support and the explicit
  hardware-breakpoint constant before Flutter starts.
- [ ] One owner-free Mini QEMU run uses exactly the FLR-0410 kernel/rootfs/
  qemuboot hashes and ordinary UID-1001 Example Demo environment.
- [ ] Immediately before QEMU start, the Mini gate inspects every visible
  numeric `/proc` entry under a `/proc` mount without `hidepid`; any unreadable
  or unresolved live entry fails closed. Confirmed PID disappearance is
  counted separately. Each requested `ss` port query must exit cleanly with no
  diagnostic and empty output; errors are UNKNOWN, never “free”.
- [ ] The run records one guest boot ID and exact app/GDB PID/UID/start-token
  identities for the same candidate.
- [ ] If GDB safely exposes a controllable DSO-load stop, retain its Build-ID,
  PT_LOAD/live mapping, process identity, clock bounds, app-present/kernel
  snapshot, and full QMP frame. Otherwise mark only this pre-hit phase UNKNOWN.
- [ ] The first target hit writes/flushed `HIT_BEGIN` before querying GDB, then
  records PID/UID/start token/LWP/PC/caller resume PC/map with independently
  guarded fields. After the callback returns, `HIT_READY` requires matching
  guest boot ID, GDB/app identities, exact target PC, and every app thread's
  stopped state. The breakpoint's arm-time number/type/address is retained;
  the auto-deleted temporary breakpoint is not inspected after hit. Caller
  UNKNOWN allows capture but blocks release and requires explicit abort.
- [ ] A bracketed at-hit QMP still and eight-frame sequence plus a bracketed
  post-release still/eight-frame sequence distinguish stopped from advancing
  pixels, app presents, and any first fault. Release requires durable artifact
  hashes, a rechecked guest/manifest SHA-256, exact app/GDB identities, and
  controller acknowledgement; the hit manifest must include the bracket record,
  full still, and exactly named eight PPM frames. A load-stage release likewise
  requires its QMP still and bracket record. No timeout auto-releases. Evidence
  gaps permit only an identity-matched controller abort.
- [ ] After QEMU cleanup, the Mac exporter fetches only allowlisted PPM screen
  captures and their capture metadata, verifies source hashes, and creates
  local PNG/MP4 previews. Preview metadata records measured capture intervals,
  the nominal 4-fps playback rate, and `real_time_video=false`; MP4 creation is
  not evidence that the runtime or product passed. Raw PPMs/logs remain on Mini.
- [ ] Exact app/GDB/QEMU cleanup, zero residual socket/ports, and unchanged
  postflight image hashes are recorded. No second QEMU/build or image mutation.
- [ ] Facts/inferences/hypotheses/UNKNOWN, commands, screenshot/video refs, and
  hashes are in the ticket/log; canonical, privacy, checkpoint, diff pass and
  only the known historical Markdown-link failures remain.

## Competing hypotheses

1. The marker/hold failure was solely nested formatting in the observer. A
   typed callback will write its marker first and remain stopped until release.
2. The app/GDB has an independent exit/fault at or after the target hit. The
   corrected callback may still capture a fault or unmatched present while
   the exact process identity disappears.
3. The target helper is not causal; the caller/present sequence and post-release
   frame may show normal progress despite its hit.

These are tested only on one unchanged image/run. A single instrumented run can
show ordering and association but cannot by itself prove a general cause.

## Visual evidence

- QMP-only screenshots/video: pending one run.
- Required content: full 1280×800 frames at target hit and after release;
  load-stop frame when safely controllable; eight-frame sequences at hit and
  after release.
- Run/image identity, capture brackets, pixel hashes/ROI counts, and artifact
  role paths: pending.
- Raw PPM and logs stay on Mini; local PNG/MP4 preview only from screen media.
- Mini has no FFmpeg-compatible encoder. The runtime records
  `PENDING_MAC_PREVIEW`; `scripts/export_flr0416_media_preview.py` validates a
  hash-manifested screen-only archive and uses the Mac's existing FFmpeg after
  teardown. Do not install packages on Mini for this diagnostic run.

## Plan / Do / Check / Act

### Plan

1. Verify canonical branch and ticket state; keep FLR-0415 Waiting and FLR-0416
   sole In Progress.
2. Test the GDB helper on Mac and validate every guest command/payload offline.
   Do not access Mini runtime/build state before the scripts pass locally.
3. Immediately preflight Mini owners, ports, paths, and exact FLR-0410 hashes.
   Reject restricted proc visibility, unreadable/unresolved PID records,
   occupied ports, and failed port queries. Repeat the process/port gate at the
   final start boundary. If any owner is active/ambiguous or any hash differs,
   stop before QEMU.
4. Boot one 6144-MiB QMP-first QEMU. Verify GDB 14.2 Python callback API before
   launching Flutter; no fallback launch.
5. Hold at target library load and collect its QMP bracket before the
   identity/hash-validated release. If that boundary is not safely controlled,
   record it UNKNOWN and abort this exact run; do not proceed without an armed
   first-hit breakpoint. Capture all hit evidence while app threads are
   stopped, validate hashes and controller acknowledgement, then explicitly
   release once. Capture the bounded post-continue window and exact teardown.
6. Record a bounded classification; only a clear controllable product
   boundary may justify a new source-change ticket.

### Do

- Implemented the typed first-hit observer, bounded capture controller, and
  screen-only Mac preview exporter. A final controller record now separates
  diagnostic status from verified QEMU/QMP teardown. Successful QMP brackets
  explicitly carry `verified=true`; the exporter rechecks run/stage, load-ready
  identity, process state, capture hashes, host time containment, guest time,
  present counters, and kernel counters before labeling correlation verified.
- The first formal Mini preflight stopped before QEMU with
  `ffmpeg-unavailable-for-required-video`. Rather than install software on Mini,
  encoding was removed from the runtime controller and deferred to Mac after
  QEMU teardown. Mini remains the raw PPM evidence source; transfer is limited
  to an exact screen-media allowlist plus controller-final metadata.
- Review findings were closed before commit: producer and exporter now use the
  same stage/identity/clock/process/present/kernel bracket validator, and clean
  QEMU disappearance is separately verified by recorded PID/start-time,
  QMP-socket absence, and the exact postflight success marker. `run()` preserves
  PASS/0 only when the final teardown record verifies and returns
  INCOMPLETE/nonzero otherwise.
- No QEMU or product image/source operation has occurred in this iteration.
  Commands/results are recorded in [the working log](../logs/2026-10-03-flr0416.md).

### Check

- Latest focused suite: 82 tests PASS. Repository-wide suite: 331 tests PASS.
- The focused suite includes a real local FFmpeg PNG/fragmented-MP4 synthetic
  smoke and verifies nominal 4-fps playback is not represented as real time.
- Fresh read-only Mini ownership/port scan: PASS, 254 `/proc` entries scanned,
  zero disappeared/unresolved, zero relevant owners, and all three requested
  ports free. Receiver is clean at `b13d6aa`; fixed build/TMPDIR directories
  exist and the intended project layer is selected. No QEMU was started.
- The local role file is absent and role variables are unset. The GPT-6.1 Sol
  override was requested for judgment; the recommendation was to use only
  previously verified transient roles after fresh checks. The response itself
  could not verify model attribution. The standard helper's effective
  `TOPDIR`/`TMPDIR` check and the full start preflight remain pending.
- Post-edit canonical, privacy, runtime-checkpoint, diff, and shell-syntax gates
  pass. The Markdown checker still reports the same 11 historical missing
  targets; no new FLR-0416 link is missing.
- Prior Mini preflight failed on missing FFmpeg before creating a run or QEMU;
  this code revision has not yet been transferred or passed through the full
  start-profile preflight.
- QEMU/GDB smoke, live first-hit evidence, runtime pixels, and all product
  acceptance gates remain UNKNOWN / NOT RUN.

### Act

- Two rounds of read-only review findings were addressed; the final review found
  no remaining blocker in this scope. GPT-6.1 Sol was requested by explicit
  model override, but the reviewer could not verify model attribution. Commit
  locally, use the standard bundle handoff after one more read-only Mini
  ownership/receiver check, and repeat the full Mini start preflight.
  Only if owner/image/resource gates pass should one unchanged FLR-0410 QEMU be
  started; exact GDB 14.2 smoke must pass before Flutter.
- This diagnostic ticket cannot complete the 3D product goal. Production
  Sequoia material/texture/lighting, same-frame HUD, interaction/repaint
  stability, five-minute present, and two-boot acceptance remain open.

## Unknowns

- Whether the app remains alive and GDB remains present after the target hit
  with the corrected observer.
- Whether GDB 14.2 safely returns control at the library-load catchpoint and
  supports this callback/temporary-breakpoint interaction. Constructor success
  alone is not proof of runtime hardware insertion.
- Exact caller DSO/build ID for `0x7fff89afc320` and its relationship to
  Filament/Mesa present/synchronization. An unwound caller PC is a return/resume
  address, not automatically the exact call instruction.
- Whether successful present calls contain Sequoia/HUD pixels before, at, or
  after the hit.
- Why the prior QMP samples were black, whether production Sequoia's original
  texture/material/light works on this candidate, and whether 2D+3D composition
  remains stable after input/repaint.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings: One fresh same-image observation is planned; no runtime result yet.
