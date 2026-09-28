# FLR-0354 Plan — repair the FIFO launch gate and fail-path identity

## Goal

Correct the FLR-0350 pre-exec gate without guessing whether FD 0 or FD 3 is the
right descriptor. Prove that the descriptor used by the blocked `read` refers
to the same FIFO object as the run-owned gate, and make gate rejection safely
cleanable using recorded process identity.

This is local Mac harness work only. Do not run QEMU, Mini commands, BitBake,
Devtool, a bundle transfer, or a product/image modification. The consumed
`flr0350-0001` identifier and its evidence are immutable; the next runtime
attempt requires a fresh ticket and fresh ID.

## Evidence and design decision

- FLR-0350 observed a sleeping `sh` wrapper owned by UID 1001 and a blocked
  syscall `0 0x0 ...`. The old gate required FD 3 and did not inspect the
  actual read descriptor's FIFO object.
- `read <&3` redirects FD 3 to standard input, making FD 0 the syscall's read
  descriptor. That explains the number mismatch but does not establish that
  FD 0 referenced the expected FIFO in the consumed run. The redirection and
  `read` behavior follow the [POSIX shell language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
  and [POSIX `read` utility](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/read.html).
- The old launch command writes the PID start marker only after the gate passes,
  so its failure path cannot prove the wrapper's identity.
- Chosen: emit one structured guest observation; a host-side Python module
  strictly parses and validates it. Compare FIFO type/device/inode, not the
  descriptor number or pathname. Persist PID/start identity before evaluation.
- Rejected: simply change expected FD 3 to FD 0, because that assumes rather
  than verifies the descriptor target. Rejected: a transferred guest helper,
  because it introduces extra versioning/quoting/lifecycle state.

## Implementation steps

1. Add `scripts/flr0350_launch_gate.py` with one strict parser and one
   validation predicate used by both CLI and tests. Reject absent/duplicate
   markers, duplicate/missing/unknown keys, malformed values, wrong process or
   syscall state, non-FIFO targets, and FIFO type/device/inode mismatch.
2. Add focused tests in `tests/test_flr0350_launch_gate.py`: same FIFO through
   FD 0 and FD 3 passes; FD-3 correctness cannot mask a different actual read
   target; missing/malformed/duplicate observations and each identity/type/
   device/inode/syscall/state mismatch fail. Test Linux proc-stat start-time
   extraction with spaces and parentheses in `comm`.
3. Update the one-line guest launch command to save wrapper PID/start before
   evaluating the gate. Add a bounded observation command that captures the
   actual read FD and dereferenced stat identity for both that FD and the gate,
   then emits exactly one structured observation. Fail closed if any required
   field is unavailable.
4. Update the host runner to call the production validator immediately after
   observation and before GDB attach or GO. Extend its local `--check` to run
   focused tests and prove ordering without starting QEMU. Accept a validated
   fresh `flrNNNN-NNNN` run ID while explicitly rejecting consumed
   `flr0350-0001`.
5. Harden the failed-launch stop/FIFO cleanup behavior around the recorded
   identity. Use `/proc/PID/stat` parsing robust to spaces/parentheses in
   `comm`. No signal is sent if PID/start/UID/command is missing or mismatched;
   no process-wide kill is permitted. Confirm the exact FIFO type, owner, and
   mode before unlinking the fixed run-owned path.
6. Keep guest commands single-line and <=4096 bytes; validate shell syntax,
   exact FLR-0344 environment/CLI parity, command order, fresh-ID guard, and
   test behavior.
7. Run canonical/privacy/checkpoint gates and scoped repository checks, record
   failures as well as passes, and make one local privacy-safe commit. Do not
   push or transfer this harness-only change during FLR-0354.

## Execution checklist

- [x] Create the independent FLR-0354 ticket, working log, and plan.
- [x] Add tests against the production gate predicate; observe the initial red
  result before implementation.
- [x] Implement strict observation parsing, object identity checks, early
  process identity capture, robust proc-stat parsing, and fresh-ID guard.
- [x] Integrate the gate validator before GDB attach/GO and add it to `--check`.
- [x] Run full repository verification; record the unrelated Markdown-link
  failure and run the remaining repository gates individually.
- [ ] Stage only FLR-0354 files, pass privacy/staged-whitespace checks, and
  commit locally without push or Mini transfer.

## Acceptance criteria

- Tests execute the exact parser/predicate that the runner uses.
- Descriptor number is incidental; object identity is the acceptance test.
- Missing/ambiguous observations fail before GDB attach/GO.
- Cleanup uses exact pre-recorded identity and is fail-closed.
- The runner rejects consumed `flr0350-0001` and supports a later
  ticket-correlated ID without creating per-run guest files/directories.
- All guest command size and syntax gates pass; local `--check` reports that
  QEMU was not started.
- Ticket and working log explicitly preserve UNKNOWN for the next target's
  `stat` support and all Flutter/rendering outcomes.

## Risk and impact

- Build-time: none; no BitBake or image build.
- Runtime/packaging: no product binary, package, recipe, or image changes.
- Harness integration: guest `stat -L -c` support is not yet proven; the next
  fresh-run preflight must validate the exact command before launch.
- Rendering: no evidence is gathered here; 2D+3D/Sequoia/light state remains
  UNKNOWN until a distinct QMP-captured runtime attempt.
