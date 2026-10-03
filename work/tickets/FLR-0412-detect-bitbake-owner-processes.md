# FLR-0412 — detect active BitBake owners by executable identity

- Status: Inbox
- Priority: High
- Created: 2026-10-03
- Predecessor: [FLR-0410](FLR-0410-synchronize-event-callback-map.md)
- Scope: harden Mini build-owner guards only; do not change or interrupt the
  active FLR-0410 image build.

## Problem

The current Mini guard checks use `pgrep -x bitbake` and `pgrep -x
bitbake-server`. A real running BitBake invocation was invisible to the
parallel `ps -eo comm=` check because BitBake runs as Python processes whose
Linux `comm` values are `KnottyUI`, `Cooker`, and `Worker` (with a `pseudo`
child). A later argv-based check found the live build and its `bitbake`,
`bitbake-server`, and `bitbake-worker` script paths. A guard based only on
exact process names can therefore misclassify a busy build as idle.

## Facts

- During FLR-0410's single Mini full-image build, the bounded task log reached
  task 11888/11898 (`do_rootfs`). The SSH build session remained live.
- A `comm`-only query reported no BitBake process, while an argv query showed
  the active `timeout` → Python BitBake client, server, workers, and pseudo
  process. No second build or process-control command was issued.
- `scripts/reuse-mini-build-receiver.sh` and
  `scripts/run-mini-recipe-patch-gate.sh` currently use exact-name `pgrep`
  checks for BitBake ownership.

## Inference and risk

The current exact-name guard is not a reliable proof of idleness on this
Mini's Python-based BitBake process model. A future receiver update or recipe
gate could overlap a real build unless the guard identifies the executable
script/owner robustly. This observation does not mean a collision occurred in
FLR-0410; only one image build was started and monitored.

## Work unit

Implement a bounded, fail-closed BitBake owner detector for the existing Mini
handoff and recipe-patch gates. Recognize the active BitBake client, server,
workers, and timeout wrapper by executable/script identity or verified process
ancestry, not `comm` names alone. Exclude the checker itself and unrelated
Python processes. Never kill an owner as part of detection.

## Success criteria

- [ ] A live Python BitBake client/server/worker fixture is detected even when
  its `comm` is `KnottyUI`, `Cooker`, or `Worker`.
- [ ] A timeout wrapper and child are attributed to the same BitBake owner;
  unrelated Python and the detector do not self-match.
- [ ] Handoff refuses before bundle fetch/receiver checkout when the owner is
  active; recipe patch gate refuses before evidence creation or recipe clean.
- [ ] The no-owner case passes, existing fixed paths remain unchanged, and no
  process is killed or signaled.
- [ ] Focused regressions, shell checks, privacy/checkpoint, and local commit
  pass; no push.

## Plan / Do / Check / Act

### Plan

Inspect all BitBake ownership gates and their tests, define the narrow argv/
ancestry predicate from the observed Mini process model, then add deterministic
tests for active, unrelated, and self-process cases. Preserve the current
FLR-0410 build/runtime state.

### Do

- Not started. This ticket remains Inbox while FLR-0410 owns the product
  candidate build and runtime.

### Check

- Discovery only. The new owner detector and regression tests do not yet exist.

### Act

- Begin after FLR-0410 no longer needs the existing Mini build/TMPDIR/QEMU.
- Keep the full image-build log and completion state in FLR-0410; this ticket
  owns only the future guard correction.
