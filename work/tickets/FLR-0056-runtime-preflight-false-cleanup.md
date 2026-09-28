# FLR-0056 — correct false QEMU cleanup and serial validation

- Status: Waiting
- Created: 2026-09-09
- Owner: target-validation role
- Context: runtime orchestration
- Branch: feature-flr-0023-3d-qemu-validation
- Predecessor: [FLR-0055](FLR-0055-tps-bounded-qemu-harness.md)
- Working log: [2026-09-09-flr0056.md](../logs/2026-09-09-flr0056.md)

## Outcome / success criteria

Detect actual QEMU and interpreted runqemu processes before any launch or
socket cleanup; execute syntactically valid serial code. Stop the two identified
orphaned instances and prove the result using executable/PID evidence. Resume
FLR-0050 with the current image, not the older harness-smoke image.

## Facts / stratification

What: two live QEMUs contradict the preceding residual-zero report.
Where: build-host process inspection and the committed shell/Python harness.
When: continuation audit after commit `4a5d0dc`.
Who: validation owner, not the Flutter or image owner.
How: `ps comm` truncates long executable names; runqemu appears as Python.
The serial heredoc also contains an unexpected indent ignored by `bash -n`.

## Hypotheses

- H1: full command/executable identity reveals processes missed by short comm.
- H2: a new unrelated launch explains the residuals. Check PID start time and
  rootfs/QMP arguments before stopping anything.

## Plan / Do / Check / Act

- Plan: record identities, stop only the known orphaned runs, reproduce the
  detector and Python-syntax failures, make the minimal harness correction.
- Do: corrected detector and Python syntax, stopped the two owned orphaned runs.
- Check: behavioral regressions PASS; latest image preflight/start and guest
  SSH PASS. Serial late-attach times out without a fresh login prompt.
- Act: serial late-attach remains Waiting. Continue FLR-0050 via proven guest
  SSH on the one current QEMU. No Yocto build or native source change.

## UNKNOWN

This task does not establish Flutter pixels or composition. QMP paths were
unlinked while processes were live; signal-based recovery may be required.

## Impact

Build-time/packaging: none. Runtime: only owned validation QEMUs. Integration:
stopping residual snapshots loses their volatile guest state; preserve existing
evidence and artifacts. No cache, image, source, or volume deletion.
