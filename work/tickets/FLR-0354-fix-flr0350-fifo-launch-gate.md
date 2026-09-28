# FLR-0354 — repair and deterministically test the pre-exec FIFO launch gate

- Status: Done
- Priority: High
- Owner: Mac launch-gate harness / AGL runtime process roles
- Created: 2026-09-29
- Updated: 2026-09-29
- Work unit: repair the FLR-0350 pre-exec FIFO observation and prove its acceptance/rejection and guarded-cleanup behavior with local deterministic tests
- Links: [plan](../../docs/superpowers/plans/2026-09-29-flr0354-fifo-launch-gate.md), [working log](../logs/2026-09-29-flr0354.md), [FLR-0350 source ticket](FLR-0350-correlate-lavapipe-sync-release-producer.md)

## Problem

### Purpose

Make the one-shot producer-correlation harness able to establish that the
blocked `read` syscall is waiting on the exact run-owned FIFO before GDB
attaches or the GO token is released. Ensure the wrapper identity is recorded
early enough for guarded cleanup if this gate rejects.

### Success measure

The exact gate predicate used by the runner passes when the syscall's actual
FD (whether 0, 3, or another reported descriptor) refers to the same FIFO
object as the run-owned gate, and rejects mismatches, malformed observations,
or uncertain process identity. Regression tests exercise that predicate
directly. No runtime or rendering claim is made by this ticket.

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Pre-exec launch gate rejects before GDB attach/GO; cleanup cannot prove the wrapper identity because its start marker is written only after gate pass | FLR-0350 Iteration 5 serial transcript and `work/commands/FLR-0350-launch-paused-production.cmd` |
| Where | Mac-side runner/guest serial gate boundary for the fixed qemux86-64 diagnostic profile | FLR-0350 ticket, runner and guest command |
| When | One consumed attempt, `flr0350-0001`; gate runs after launch and before GDB attach | FLR-0350 runner ordering and recorded run evidence |
| Who | Host runner, guest shell wrapper, `/proc` observer, and guarded cleanup role | FLR-0350 command sequence |
| How | Command expected syscall argument FD 3 and inspected `/proc/PID/fd/3`; observed blocked syscall had argument FD 0 after shell redirection `<&3` | FLR-0350 Iteration 5 `FLR0350_FIFO_READ_GATE=FAIL` evidence |

### Priority selection

- Compared strata: wrong gate descriptor assumption; incomplete pre-gate process identity capture; unrelated Flutter render/lighting behavior.
- Selected focus: launch-gate correctness and safe fail-path cleanup, because the run stopped before app execution and therefore produced no Flutter rendering evidence.
- Selection evidence: guest marker shows `comm=sh`, sleeping state, expected run-owned FIFO visible at FD 3, while `/proc/PID/syscall` reports `read` argument FD 0; the gate currently requires FD 3 and does not compare the actual FD target object.

### Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| Start paused wrapper | run-owned FIFO and unchanged FLR-0344 Flutter profile | Wrapper blocks reading the gate; PID/start identity is saved before verdict | Wrapper was launched; start identity is saved only after the current descriptor gate succeeds | launch command |
| Validate read gate | `/proc/PID/syscall`, FD link/stat, gate FIFO stat, process identity | Actual syscall FD points to same FIFO object (type/device/inode), process is stable and blocked | Gate compares FD 3 and syscall arg 3; recorded syscall arg was 0 | FLR-0350 Iteration 5 |
| Attach GDB / release GO | Passed gate and recorded identity | GDB attaches to exact wrapper before GO; app exec follows | Not reached | runner transcript |
| Failure cleanup | Captured PID/start, UID, command identity, owned FIFO | Signal only the exact recorded process; remove only validated run-owned FIFO; no broad kill | Stop helper reported identity unknown because start marker was not written on gate failure | FLR-0350 cleanup transcript |

### Problem point

The first incorrect process step is the gate's hard-coded FD-3 assumption: the
shell command redirects FD 3 to standard input for `read`, so the blocked
syscall uses FD 0. The next weakness is that the wrapper start identity is
persisted only after this gate passes, leaving the failure path without a
recorded process identity.

### Ideal condition

The runner validates one strict observation from the actual blocked syscall;
the descriptor reported by that syscall resolves to a FIFO with the same
device and inode as the run-owned gate. PID, start time, UID, command, state,
syscall number, and tracer status are checked. Identity is recorded before
gate evaluation; cleanup never signals an unknown or mismatched process.

### Current condition — Facts

- FLR-0350's only one-shot QEMU run stopped at `FLR0350_FIFO_READ_GATE=FAIL`.
- The guest observation recorded PID 708, `comm=sh`, sleeping state, UID 1001,
  FD 3 linked to the gate pathname, and syscall `0 0x0 ...`.
- The launch command required syscall argument `0x3` and checked only FD 3;
  therefore it did not inspect the object referenced by the actual read FD 0.
- Flutter and GDB did not start. The black QMP frame is not a render result.
- The wrapper start marker was not created because it was inside the gate-pass
  branch; guest stop/cleanup consequently reported identity unknown.
- Run ID `flr0350-0001` is consumed and must never be reused.

### Gap

The gate does not validate the descriptor actually used by `read`, and its
fail path cannot safely identify the wrapper. Static substring checks alone
would not prove the parser's runtime decision.

### Impact

The producer-correlation experiment cannot begin; its captured black frame
cannot answer whether Flutter, 3D, lighting, texture loading, or composition
works. Repeating the same gate with the same run ID is prohibited.

### Point of occurrence

FLR-0350 runner step `launch` → FIFO gate evaluation, before `attach-gdb`.

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| H1: FD 3 is not the descriptor used by the blocked `read`; shell redirection maps it to FD 0 | `/proc/PID/syscall` reports argument 0; FD 0 target is the object that must be compared with the gate | Require descriptor number to come from the syscall observation; fixtures where FD 0 or FD 3 targets the same FIFO pass, a different target fails | Strongly supported for the recorded run; same-FIFO identity for FD 0 remains UNKNOWN because its symlink/stat were not captured | FLR-0350 Iteration 5; [POSIX shell language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html); [POSIX `read`](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/read.html) |
| H2: FIFO object identity differs from the run-owned FIFO despite a matching path string | Device/inode/type comparison fails | Compare `stat` identity of the actual syscall FD target with the gate FIFO; mismatched-device/inode fixtures reject | UNKNOWN for the consumed run; no actual-FD target stat was recorded | no `fd/0` stat in captured observation |
| H3: wrapper identity was lost only because start marker is delayed until gate pass | Marker is absent on any rejected gate, so stop helper cannot verify PID reuse protection | Save PID/start before the gate verdict; fixture gate failure then exercise cleanup decision without signaling mismatched identity | Supported by current launch-command ordering; corrected cleanup requires tests | launch command and cleanup transcript |

### Confirmed root cause

The gate's FD-3 expectation contradicts the recorded syscall argument FD 0.
Whether FD 0 referenced the exact FIFO object is UNKNOWN in the consumed run;
this ticket adds object-identity evidence to future runs rather than inferring
it from the pathname.

### Minimal countermeasure

Use a strict host-side validator for a structured guest observation containing
the actual syscall FD and the type/device/inode of both that FD target and the
gate FIFO. Record wrapper identity before the gate verdict and retain
fail-closed exact PID/start/UID/command checks for cleanup. Do not modify the
product or assume the descriptor number.

## Scope

### In scope

- Mac-side gate parser, predicate tests, fixed runner ordering, guest one-line
  observation command, process-start extraction/recording, and guarded failure
  cleanup.
- Preserve the fixed FLR-0344 production environment and CLI arguments.
- Record every verification result in this ticket and its working log.

### Out of scope

- Reusing `flr0350-0001`, QEMU/RunQEMU execution, Mini writes/transfers,
  BitBake, Devtool, image/product patches, graphics, Light/camera/material
  changes, or any 3D/render conclusion.
- Changing the one-run evidence artifacts already recorded under FLR-0350.

## Success criteria

- Tests call the same parser/predicate used by the runner.
- Matching FIFO identity passes for FD 0 and another FD; actual-FD mismatch,
  gate-FIFO mismatch, malformed/duplicate/missing fields, wrong syscall,
  process state/identity/tracer, and unknown values fail closed.
- Linux `/proc/PID/stat` start-time extraction is tested with `comm` strings
  containing spaces and parentheses.
- A rejected gate has a previously captured wrapper identity; cleanup signals
  only a matching recorded PID/start/UID/command and never uses broad kill.
- Runner refuses consumed `flr0350-0001` and accepts a fresh
  ticket-correlated ID, preserving the one-attempt-per-ID rule.
- Static runner check proves validator runs before GDB attach and GO release;
  all guest serial commands remain single-line and <=4096 bytes.
- Local tests, syntax, privacy, checkpoint, and scoped repository checks pass.
- A later runtime attempt uses a new ticket and fresh run ID; this ticket does
  not claim QEMU or display success.

## Visual evidence

- QMP-only evidence: none for this Mac-side harness correction.
- FLR-0350's prior AGL splash/black frame is linked in the source ticket and is
  explicitly not a Flutter image.
- Next runtime ticket must capture the complete QMP frame/video before making
  any visual claim.

## Hypotheses

1. The actual blocked read descriptor is often FD 0 because the wrapper uses
   `<&3`; a validated descriptor target, rather than a fixed number, is the
   correct gate.
2. Matching only a FIFO pathname is insufficient; comparing FIFO type plus
   device and inode will prove object identity and reject replacement/race
   cases.

## PDCA

### Plan

- Verification sequence: strict observation parser → fixture tests against the
  production predicate → runner/guest command integration → static/syntax and
  checkpoint gates → local commit.
- Expected observations: matching same-object descriptors pass; every
  ambiguous, malformed, changed-identity, or wrong-target observation fails
  before GDB attach or GO.
- Stop conditions: command exceeds serial limit, cleanup could target an
  unrecorded/mismatched process, environment/CLI diverges from FLR-0344, or
  tests do not exercise the production predicate.
- Risks: guest `stat` option availability is not proven by host fixture tests;
  the new runtime attempt must preflight its exact supported behavior before
  app launch.

### Do

- Working log: [2026-09-29 FLR-0354](../logs/2026-09-29-flr0354.md).

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Parser/predicate | Matching same-FIFO descriptor passes; all mismatches fail | 23 tests pass, including FD 0/3, malformed/duplicate markers, target/object mismatch, process identity, proc-stat parsing, and CLI | working log Iteration 2; runner `--check` | PASS |
| Runner ordering | Validator precedes GDB attach and GO | Static test proves launch → observe → validator → GDB → GO; consumed run ID is rejected | working log Iteration 2; runner `--check` | PASS |
| Serial/static safety | Commands one-line <=4096; shell syntax valid | 11 guest commands pass syntax/size checks; profile/CLI exactly match FLR-0344 | runner `--check`; repo shell tests | PASS |
| Privacy/checkpoint | No private identifiers; exactly one active ticket | `make check-privacy` PASS; checkpoint verification PASS with active=1 | working log Iteration 2 | PASS |
| Whole-repository `make verify` | All repository gates pass | Stopped at 9 pre-existing missing FLR-0338/0339 QMP PNG/MP4 links; those files were unchanged | working log Iteration 2 | FAIL (unrelated existing evidence links) |
| Remaining repository contracts | File-size, QEMU, log-slice, Devtool, Mini recipe/handoff checks pass | All seven targets pass; 1,830 files under size cap | working log Iteration 2 | PASS |

### Act

- Standardize the parser and tests. The scoped gates pass; retain the unrelated
  Markdown-link failure as a condition rather than changing other tickets.
- This task is closed. Continue the 3D objective only in a new runtime ticket
  with a fresh ID, QMP-only screenshot/video, and explicit teardown evidence.

## Decision log

- Use the actual syscall FD observation; do not change the hard-coded expected
  descriptor from 3 to 0.
- Compare FIFO object type, device, and inode, not pathname alone.
- Keep this correction Mac-side; no Mini build, bundle transfer, or QEMU run.

## Unknowns

- Whether FD 0 in the consumed runtime run referenced the exact gate FIFO
  object; its symlink and device/inode were not captured.
- Whether the target image's `stat` supports the exact `-L -c` invocation;
  the next fresh run must prove this in a preflight.
- Whether a corrected gate will pass on the next runtime attempt.
- Whether Flutter, 2D+3D composition, Sequoia color, lighting, or producer
  correlation works in that attempt.

## PDCA checker

- Status: PASS WITH CONDITIONS
- Checked by: primary engineering role (evidence-based self-review)
- Findings: All FLR-0354 acceptance criteria and scoped checks pass. The
  repository-wide `make verify` stops at nine pre-existing missing FLR-0338/
  FLR-0339 QMP links in unchanged files; repair is tracked separately. No
  runtime, rendering, light, camera, or composition conclusion is claimed.
