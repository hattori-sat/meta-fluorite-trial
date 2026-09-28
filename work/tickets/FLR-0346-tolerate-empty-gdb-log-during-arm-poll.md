# FLR-0346 — tolerate an empty GDB log while polling for armed watchpoints

- Status: Done
- Priority: High
- Owner: bounded GDB arm-poll / runtime evidence roles
- Created: 2026-09-28
- Predecessor: [FLR-0344](FLR-0344-capture-lavapipe-watch-failure-deterministically.md)
- Baseline image: FLR-0335 kernel/rootfs/qemuboot exact hashes recorded in FLR-0344
- Working log: `work/logs/2026-09-28-flr0346.md`

## Objective

Make the GDB arm-poll distinguish a missing state file from a valid, newly
created but still-empty GDB transcript. Prove the empty-log timing case with a
fast deterministic regression test and make the smallest helper correction.
This ticket ends at the local regression gate; a separate follow-up ticket
will use the corrected poll in one same-image QEMU run. No renderer change.

## Facts inherited from FLR-0344

- The exact-image QMP run `flr0344-0001` reproduced Present-enter/no-return
  (`enter=1`, `return=0`) and showed the HUD with a uniformly black lower 3D
  ROI. The full-frame screenshot/video are linked from the predecessor.
- GDB launch reported success. The immediately following arm command emitted
  `FLR0344_ARM_WAIT=FAIL missing-gdb-state`; the eight-second watch was skipped.
- A later bounded runtime-state capture saw `gdb_comm=gdb`, ptrace-stopped
  render threads, and a persisted GDB transcript containing thread-creation
  lines but no arm marker or specific error. Its SHA-256 is recorded in the
  FLR-0344 log.
- The committed `FLR-0344-wait-armed.cmd` tests both the PID file and log with
  `-s` (must exist and be nonempty) before entering its 22-second polling loop.
  The failure marker does not record which predicate was false. A fresh empty
  transcript is therefore the leading helper-race explanation, not yet an
  individually measured operand.
- This helper failure does not explain the production black ROI; sync fields,
  writer, and renderer causality remain UNKNOWN.

## Scope

- In scope: the arm-poll state predicate, a fast red-capable test of its
  empty-log timing case, precise missing-state diagnostics, and local
  repository validation.
- Out of scope: changing Fluorite/Filament/Mesa source, Devtool or BitBake,
  building an image, changing scene/HUD/camera/light/material/texture, or
  declaring a fixture/texture image to be production success.

## Success criteria

- A deterministic, agent-runnable regression test exercises the actual helper
  with a fixture PID accepted by a controlled fake `ps`, existing empty
  transcript, and delayed arm marker;
  it reproduces the predecessor's empty-log guard failure and passes through
  the corrected helper. PID and log are independently checked.
- The corrected serial wrapper remains one line and ≤4096 bytes; shell syntax,
  privacy, links, checkpoint, and staged-whitespace gates pass.
- No Mini transfer, QEMU, image build, source patch, or renderer variable
  change occurs in this ticket. The QEMU retest is a separate follow-up.

## Ranked hypotheses

1. **The fresh transcript is empty when the arm command starts.** Prediction:
   the red-capable test reproduces immediate `missing-gdb-state`; accepting an
   existing empty log and polling waits for the delayed marker or timeout.
2. **GDB attach/thread enumeration is slow.** Prediction: after the guard is
   fixed, the bounded wait reaches its deadline with GDB alive and a growing
   thread transcript, but no armed marker.
3. **The selected waiter frame/locals are unavailable.** Prediction: GDB
   reaches the Python command and persists a concrete waiter/frame/variable
   error.
4. **The PID file is missing at the first poll.** Lower priority because
   launch succeeded and a later poll read `gdb_comm=gdb`; a separated PID-file
   failure will make this hypothesis directly visible.

## Plan / Do / Check / Act

### Plan

1. Build a fast test at the arm-poll seam; confirm it fails on empty initial
   log and passes when the delayed marker is visible.
2. Change only the state-file predicate/diagnostic needed to let an empty but
   present log enter the bounded polling loop; preserve PID-specific cleanup.
3. Run local syntax, command-size, test, privacy, link, checkpoint, and staged
   whitespace gates; commit locally.
4. Run the focused regression plus local shell/command-size and repository
   gates; commit the helper/test locally.
5. Create a separate runtime ticket for the one exact-image QEMU retest.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Red-capable local regression | Legacy guard fails; corrected helper waits through empty log and sees delayed marker | PASS | `tests/test_flr0346_arm_poll.py` executes the predecessor command and corrected shell helper; 1 test passed |
| Missing-state diagnostics | Missing PID and missing log are reported distinctly | PASS | Same test exercises both separate failure markers |
| Local/repository gates | Syntax, 4096-byte limit, privacy, links, checkpoint, whitespace | PASS | 86 Python tests, 51 shell syntax checks, privacy, Markdown links (1,048), canonical guard, checkpoint, and diff whitespace passed; staged whitespace is verified before commit |
| Scope | No QEMU, build, or renderer mutation | PASS | This ticket is local helper/test only; runtime retest is deferred to a new ticket |

### Act

- If the regression test confirms the empty-log race but GDB later times out,
  use the persisted transcript in the follow-up runtime ticket to choose only
  the next narrow GDB boundary.
- Local gates passed. [FLR-0347](FLR-0347-retest-empty-log-arm-poll-on-exact-image.md)
  owns one exact-image runtime run. Interpret sync fields/writer separately
  from the black QMP ROI; create another ticket for any renderer, HUD-off, or
  Wayland-owner change.
- No guessed renderer patch follows from this helper failure.

## UNKNOWN

- Which `-s` predicate failed in FLR-0344 at arm-poll time; whether GDB would
  have armed within 22 seconds; current Lavapipe sync field values/writer; and
  whether the Present stall causes or merely coincides with black 3D output.
