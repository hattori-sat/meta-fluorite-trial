# FLR-0087 — repair serial-exec completion evidence

- Status: Done
- Priority: High
- Owner: QEMU runtime evidence harness
- Created: 2026-09-11
- Depends on: [FLR-0055](FLR-0055-tps-bounded-qemu-harness.md)
- Working log: `work/logs/2026-09-11-flr0087.md`

## Work unit

Make the bounded serial command runner report the command exit status
reliably. This is a harness-only maintenance unit discovered while executing
FLR-0086; it must not change the guest application or image.

## Success criteria

- Reproduce the malformed completion record with a harmless guest command.
- Change the completion record so the receiver reads the exit status before
  the unique completion marker.
- Re-run harmless zero and non-zero commands through the same QEMU without
  creating a second runtime.
- Record the result and return FLR-0086 to the active diagnostic loop.

## Facts

- The guest command ran and printed output, but `serial-exec` returned
  `completion-status-not-observed`.
- The saved serial bytes ended at
  `__FLR_SERIAL_COMMAND_DONE_7B31__`; the trailing `rc=...` bytes were never
  read because the receiver stopped as soon as it saw the marker.
- This defect is in evidence collection, not in the Flutter or Filament
  runtime.

## Inferences

- Moving the marker after the status line is the minimal fix and preserves the
  one-line command and bounded-read contract.
- The first parser correction still required a byte after the marker, but the
  bounded receiver intentionally stops as soon as the marker bytes arrive.
  The parser must therefore treat the marker itself as the terminal boundary.

## Hypotheses

1. The parser will accept a status line followed by the marker and will retain
   non-zero guest command status as a failure.
2. The current QEMU remains usable; no image or application restart is needed
   for the harness-only validation.

## UNKNOWN

- Whether the previously attempted application launch exited because of its
  runtime command or because its stderr was redirected into the unobserved
  guest log path. FLR-0086 owns that runtime question.

## Plan / Do / Check / Act

### Plan

Patch only `serial-exec`, validate syntax and diff, commit locally, send the
same revision to the fixed Mini receiver, and re-run the current QEMU gate.

### Do

- Reproduced the malformed completion record on the active FLR-0086 QEMU.
- Moved the status field before the unique marker and tightened the parser to
  read `rc=<number>` immediately before that marker.

### Check

- Local `bash -n`, `git diff --check`, and completion-record simulations passed.
- Commits `9c0851b` and `7c93b64` were bundled to the fixed Mini receiver;
  final receiver revision is `7c93b64dff8ac81c33d8bb63b9d495862431480d`.
- On the same active QEMU, `true` returned
  `serial-exec=PASS command_status=0`.
- On the same active QEMU, deliberate `false` returned
  `serial-exec=FAIL command_status=1`, and the saved serial output contains
  `rc=1` followed by the terminal marker.

### Result

The harness completion-record defect is fixed. It no longer hides a command
status behind its own marker, and non-zero guest commands remain failures.

### Act

Return the sole `In Progress` focus to FLR-0086 and continue the
present-boundary runtime evidence.
