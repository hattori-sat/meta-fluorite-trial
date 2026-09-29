# FLR-0360 — Same-point GDB attach precondition diagnostics Implementation Plan

> **For agentic workers:** execute task-by-task. Keep one In Progress ticket. Record each gate in the FLR-0360 working log; never retry a consumed run ID.

**Goal:** Name the exact existing GDB attach predicate that rejects a fresh Mini run, while preserving the current fail-closed acceptance rules.

**Architecture:** Add a test at the guest attach command's serial-output boundary. Refactor the existing precondition into named results computed from one snapshot, emit a compact marker immediately before the existing GDB branch, and leave the condition set unchanged. Bundle that commit to the established Mini receiver, then use one fresh QEMU run to identify the failed predicate; stop before GDB/GO if any predicate fails.

**Tech Stack:** POSIX shell guest command, Python `unittest` launch-gate contract, existing Mac-to-Mini Git bundle handoff, pinned Mini runqemu/QMP harness.

**Spec:** [FLR-0360 ticket](../../../work/tickets/FLR-0360-diagnose-gdb-attach-precondition.md).

## Global Constraints

- FLR-0359 closed as a bounded helper-provenance/runtime-attempt unit in commit `7f6c4ba`; FLR-0360 is the only In Progress ticket on its dedicated feature branch.
- Keep the existing syscall fd 3 requirement and every other current predicate exactly fail-closed; this plan adds observability, not alternate acceptance.
- Modify only the guest attach diagnostic command, its static regression, ticket/log/plan, and task dashboard.
- Use the established committed-bundle handoff to the fixed Mini receiver. Do not create another source receiver, build directory, TMPDIR, or cache.
- Do not run BitBake, Devtool, product image builds, or copy QEMU images to Mac.
- Use exactly one fresh run ID only after local checks and read-only Mini preflight pass. Never retry any consumed ID.
- Capture QMP-only still and eight-frame video, classify by GO, and prove the run-owned FIFO, QMP, QEMU, and app cleanup.
- Store large artifacts outside Git; commit concise facts, hashes, role paths, commands, and results only. Never record private connection values.

---

### Task 1: Lock the attach diagnostic contract with a failing test

**Files:**
- Modify: `tests/test_flr0350_launch_gate.py`
- Read: `work/commands/FLR-0350-attach-pre-submit.cmd`
- Read: `work/commands/FLR-0350-run-sync-producer.sh` static command-size and syntax gate

**Interface under test:** the one-line guest attach command emits a bounded serial marker named `FLR0350_GDB_ATTACH_PREFLIGHT`. It identifies each current check individually, reports `syscall_nr`, `syscall_fd`, `fd0_same_gate`, and `fd3_same_gate`, then emits the existing PASS/FAIL attach marker. A failure must not enter `/usr/bin/gdb`.

- [x] Add `test_attach_preflight_reports_each_existing_predicate` asserting the guest command contains named fields for process/pid-start/comm/uid, fd3 gate identity, syscall read number/fd, script readability, and each pre-existing collision path.
- [x] Add `test_attach_failure_stays_before_gdb_and_release_go` asserting the named preflight failure branch precedes GDB and the runner requires the attach PASS marker before release-GO.
- [x] Add `test_attach_preflight_evaluates_failures_and_keeps_fd0_diagnostic_only` using a temporary proc-shaped fixture to execute the actual pre-GDB command prefix for all-pass, syscall-fd failure, and fd0-only mismatch cases.
- [x] Run the per-predicate test against the old command; it failed because only the generic `FLR0350_GDB_ATTACH=FAIL precondition` existed. The first assertion initially dumped the 3528-byte command; it was shortened to a bounded failure message before rerunning the red check.
- [ ] Keep the test assertions on the serial-output contract and gate ordering; do not add a fake rule that treats fd 0 as acceptable.

### Task 2: Emit same-point named predicates without changing the gate

**Files:**
- Modify: `work/commands/FLR-0350-attach-pre-submit.cmd`
- Test: `tests/test_flr0350_launch_gate.py`
- Validate through: `work/commands/FLR-0350-run-sync-producer.sh --check`

**Output contract:** for example, the preflight marker can contain:

```text
FLR0350_GDB_ATTACH_PREFLIGHT pid_present=PASS start_match=PASS comm_match=PASS uid_match=PASS fd3_same_gate=PASS syscall_read=PASS syscall_fd3=FAIL fd0_same_gate=PASS script_readable=PASS armed_clear=PASS gdb_pid_clear=PASS gdb_start_clear=PASS log_clear=PASS syscall_nr=0 syscall_fd=0x0
FLR0350_GDB_ATTACH=FAIL precondition failed=syscall_fd3
```

The observed example is a format example, not an expected Mini result. Implementation steps:

- [x] Read the current command and enumerate its exact original predicate set: pid present; expected/current start match; `comm=sh`; target UID match; fd 3 path equals gate; syscall is `read(3)`; GDB script readable; armed/GDB PID/GDB start/log paths absent.
- [x] Compute each result once from the command's current snapshot. Also compare `/proc/$pid/fd/0` and `/proc/$pid/fd/3` device/inode with the run-owned gate for diagnosis; do not use fd 0 equality as an acceptance predicate.
- [x] Emit one bounded `FLR0350_GDB_ATTACH_PREFLIGHT` line containing every check plus syscall number/fd and both descriptor-identity results.
- [x] Build a named `failed=` token list from the same original checks. If non-empty, emit `FLR0350_GDB_ATTACH=FAIL precondition failed=<tokens>` and do not start GDB. If empty, proceed to the existing GDB code unchanged.
- [x] Run all three focused tests; the behavioral fixture proves the exact failed syscall-FD predicate is named and that an fd0 mismatch remains diagnostic-only. The failure-before-GDB/GO test preserves an existing boundary rather than changing it.
- [x] Run `sh -n work/commands/FLR-0350-attach-pre-submit.cmd`; it remains one command of 4041 bytes (limit 4096). `bash work/commands/FLR-0350-run-sync-producer.sh --check` passes all static/helper markers and 34 tests.
- [x] Review the diff: all thirteen original acceptance predicates remain required; fd0/fd3 inode values are diagnostic only. Astra's judgment-only audit found no blocker and its mutation checks confirmed the test catches an inverted syscall-fd predicate or cleared failure accumulator.
- [ ] Commit the tested change locally and record the exact commit in the FLR-0360 working log.

### Task 3: Bundle the exact commit and make one Mini diagnostic attempt

**Files/commands:**
- Use: `scripts/handoff-fluorite-bundle.sh <base-commit> <tip-commit>`
- Use: `scripts/reuse-mini-build-receiver.sh` through the standard handoff helper
- Execute on Mini: `bash work/commands/FLR-0350-run-sync-producer.sh flr0360-0001`
- Inspect only: exact receiver/image identity, preflight summary, attach marker, QMP analysis, cleanup marker

- [ ] Record the resolved receiver base commit before transfer and prove the worktree is clean.
- [ ] Transfer the exact local commit by the standard bundle helper; record command, bundle SHA-256, local tip, receiver base/tip, clean state, fixed build/TMPDIR roles, and effective-template result.
- [ ] Prove pinned kernel/rootfs/qemuboot hashes, BitBake idle, ports free, no prior run-owned targets, and absent evidence parent for `flr0360-0001`; if any preflight gate fails, do not launch QEMU or consume the ID.
- [ ] Run only the one fresh ID `flr0360-0001`; log the exact role-redacted invocation before reading results.
- [ ] Confirm helper/command provenance, then read the preflight marker. If any predicate fails, verify no GDB attach/GO marker and let the runner clean up; do not loosen the predicate.
- [ ] If all predicates pass, record the next stage from the same run; do not infer 3D success from a GO marker or fixture-only pixels.
- [ ] Preserve the QMP full-frame still and eight one-second frames/video, analyze full frame and the existing fixed 3D ROI, include pixel counts and SHA-256, and label pre-GO/post-GO accurately.
- [ ] Verify `FLR0350_FIFO_CLEANUP=PASS removed=run-owned-fifo`, QMP quit accepted, app/QEMU/QMP residuals zero; do not issue a global kill.
- [ ] Update the work log and ticket with facts/inferences/three-to-five ranked hypotheses/UNKNOWNs, failed probes, exact commands, and PDCA result. Close FLR-0360 only after its own evidence/privacy/checkpoint review; production 2D+3D remains a separate acceptance goal.

**Acceptance:** the first attach predicate is identified from same-point output, or every attach predicate passes and the next measured stage is recorded; acceptance semantics are unchanged; exactly one new Mini run is attributable to the committed bundle; QMP evidence and cleanup are complete; no rendering claim is made from pre-GO evidence.
