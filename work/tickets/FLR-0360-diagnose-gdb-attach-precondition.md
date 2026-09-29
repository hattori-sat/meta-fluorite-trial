# FLR-0360 — diagnose the GDB attach precondition at the same decision point

- Status: Inbox
- Priority: High
- Owner: QEMU guest attach gate / runtime evidence roles
- Created: 2026-09-29
- Predecessor: [FLR-0359](FLR-0359-use-committed-qemu-runtime-helper.md)
- Plan: [implementation plan](../../docs/superpowers/plans/2026-09-29-flr0360-diagnose-gdb-attach-precondition.md)
- Working log: [FLR-0360 log](../logs/2026-09-29-flr0360.md)

## Objective

Identify which exact predicate makes `FLR0350_GDB_ATTACH=FAIL precondition` in the current Mini guest, without changing the gate's acceptance semantics. Preserve same-point evidence for syscall number/fd, fd 0/fd 3 FIFO identity, process identity, GDB script readability, and collision markers. If any predicate fails, stop before GDB attach and GO.

## Why this is the next unit

FLR-0359 used the exact committed helper and passed the official FIFO read gate, then stopped at the GDB attach precondition. The observer saw `read(0)` (`arg1=0x0`) whose FIFO device/inode matched the gate, while attach requires `read(3)` (`arg1=0x3`). The attach command emits only a generic failure, so this is a leading hypothesis, not a confirmed cause.

Historical evidence is fallible and scoped:

- FLR-0350's original log explicitly left target `/proc` and ptrace unproven.
- FLR-0356 observed matching process/FIFO identity but failed host framing before GDB/GO.
- FLR-0358 did not exercise its serial fix because the Mini selected an older helper.
- FLR-0359 now proves the current committed helper path passes serial framing and the FIFO gate, then fails at the separate attach precondition.
- FLR-0251 and FLR-0286 prove HUD plus self-made 3D fixture composition; FLR-0287 is a distinct production Sequoia draw/present run with a zero-chroma native ROI. None proves this run's renderer because GO was not sent.

## Success criteria

1. A static regression test fails before the change because the current attach command does not expose named precondition results.
2. The guest emits one bounded `FLR0350_GDB_ATTACH_PREFLIGHT` record from the exact attach decision point, with an individual PASS/FAIL for each existing predicate and observed `syscall_nr`, `syscall_fd`, `fd0_same_gate`, and `fd3_same_gate` values.
3. Existing predicate semantics remain unchanged: syscall fd 3 remains required; no descriptor equivalence or alternate path is allowed without separate evidence and approval. Any failure keeps GDB and GO unexecuted.
4. The command remains POSIX-shell-valid, a single serial command no larger than 4096 bytes, and the existing launch-gate `--check` passes.
5. One fresh Mini run uses the exact committed bundle tip and existing pinned QEMU artifacts. Its first failed predicate is named, or all predicates pass and the runner's next measured stage is recorded. Do not retry the run ID.
6. Preserve QMP-only full-frame screenshot and eight-frame video; label each pre-GO/post-GO. Prove run-owned FIFO removal, QMP quit, and zero run-owned process residuals.
7. Record exact role-redacted command invocations, output markers, source/bundle/image identity, pixel hashes/counts, and failed/corrected probes in this ticket's working log. Never dump unrelated full logs.

## 4W1H stratification (Why excluded)

| Dimension | Current evidence | Next discriminator |
| --- | --- | --- |
| What | Generic GDB attach precondition failure after FIFO gate PASS | Same-point per-predicate status and values |
| Where | `work/commands/FLR-0350-attach-pre-submit.cmd`, before `/usr/bin/gdb` | Output immediately before the existing GDB branch |
| When | Run `flr0359-0001`, after `FLR0350_GATE_OBSERVATION`, before GDB/GO | One new fresh run ID on the unchanged pinned image |
| Who | Guest command owns predicate evaluation; runner owns stopping on FAIL; evidence role owns QMP/cleanup | Keep the ownership boundaries unchanged |
| How | Observer measured `read(0)` on a FIFO inode matching the gate; attach requires `read(3)` and other conditions | Report fd number, fd 0/3 identity, and every existing check from one snapshot |

## Hypotheses

1. **Highest:** `syscall_fd3` is the only failed predicate. Prediction: same-point marker reports `syscall_fd3=FAIL`, `fd0_same_gate=PASS`, and every other current precondition PASS.
2. **Next:** fd 3 does not refer to the gate or a process identity predicate differs by attach time. Prediction: the marker reports `fd3_same_gate=FAIL` or one named identity check fails.
3. **Next:** the GDB script is unreadable or one of the arm/PID/start/log collision paths exists. Prediction: the marker names that particular check.
4. **Lower:** state changes between FIFO observation and attach evaluation. Prediction: attach-time values differ from the observer's immediately preceding fields or process identity.

Do not weaken the gate based on the observer-only `read(0)` record. The current failure has not demonstrated that fd 0 is an intended equivalent to fd 3.

## Scope

### In scope

- One test-first diagnostic improvement to the guest attach command and its existing static contract.
- Exact bundle transfer to the fixed Mini receiver and one fresh run on the existing pinned image, only after local gates and read-only preflight pass.
- Bounded QMP screenshot/video, first-divergence record, and run-owned cleanup verification.

### Out of scope

- Changing the required syscall descriptor or other attach predicate semantics.
- Flutter, Filament, camera, lighting, material, texture, Wayland composition, or product image changes.
- BitBake, Devtool, image build, new receiver/TMPDIR, cache cleanup, QEMU image transfer to Mac, or retrying `flr0359-0001`.
- Claiming 2D/3D renderer behavior from a pre-GO frame.

## Visual evidence

- Prior run `flr0359-0001` post-run QMP frame and video are retained under `/private/tmp/flr0359-0001/qemu/`; that evidence is pre-GO and is not reused as proof for this ticket.
- This ticket requires a new run-specific QMP still and eight-frame video. Evidence paths, hashes, regions, GO state, and cleanup result are pending.

## PDCA

### Plan

- See [FLR-0360 implementation plan](../../docs/superpowers/plans/2026-09-29-flr0360-diagnose-gdb-attach-precondition.md).

### Do

- Not started. FLR-0359 remains the sole In Progress ticket until its closeout checker passes.

### Check

| Gate | Expected | Result |
| --- | --- | --- |
| Test-first static contract | Fails on current generic attach marker, then passes on named per-predicate output | NOT RUN |
| Guest command limit/syntax | One line, <=4096 bytes, `sh -n` passes | NOT RUN |
| Mini source/image identity | Exact bundle tip, fixed receiver, pinned artifacts, one fresh ID | NOT RUN |
| Attach predicate result | First failing predicate named; no GDB/GO on failure | NOT RUN |
| QMP evidence/cleanup | Still + eight-frame video, GO classification, FIFO removed, residuals zero | NOT RUN |

### Act

- Keep in Inbox until FLR-0359 is closed and this ticket is promoted to the sole In Progress work unit.

## PDCA checker

- Status: NOT CHECKED
- Checked by: pending
- Findings: scope and acceptance are separated from production 3D success; execution has not started.
