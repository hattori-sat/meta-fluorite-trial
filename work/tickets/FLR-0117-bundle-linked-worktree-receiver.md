# FLR-0117 — accept linked-worktree receiver in bundle handoff

- Status: Done
- Priority: High
- Owner: Mac bundle handoff role
- Created: 2026-09-13
- Updated: 2026-09-13
- Depends on: [FLR-0116](FLR-0116-flutter-auto-material-variant-crash.md), [FLR-0054](FLR-0054-podman-bundle-handoff-simplification.md)
- Working log: `work/logs/2026-09-13-flr0117.md`

## Work unit

Make the single bundle handoff helper accept the fixed Mini receiver whether
Git represents it as a normal checkout or a linked worktree. Replay the same
already-transferred bundle and prove the receiver reaches the exact source tip
without touching the canonical checkout, build cache, or TMPDIR.

This is an infrastructure gate split from FLR-0116. It does not alter the
Flutter/native COLOR fix or any rendering hypothesis.

## Problem

The self-contained bundle was created and copied to the Mini inbox, and the
remote bundle SHA-256 matched. Receiver update then stopped with the helper's
`fixed receiver is missing` error because the helper required
`$receiver/.git` to be a directory. The fixed receiver is a valid Git linked
worktree, where `.git` is a file pointing at worktree metadata. The receiver
was not changed by this failed attempt.

## Success criteria

- [x] Add a failing static contract test for linked-worktree receiver
  validation, preserving the observed pre-fix failure.
- [x] Validate a receiver through Git's public worktree interface rather than
  the filesystem shape of `.git`.
- [x] Update the helper documentation, checkpoint skill, and contract test with
  the normal-checkout/linked-worktree rule.
- [x] Replay the existing one-bundle handoff and verify remote SHA, receiver
  exact tip, clean status outside evidence, fixed build/TMPDIR identity, and no
  active BitBake process.
- [x] Commit the helper/skill/ticket change locally and do not push.

## Facts

- Bundle creation and local/remote SHA-256 verification passed for the FLR-0116
  layer tip.
- The first receiver update attempt exited before fetch/checkout because the
  helper tested `$receiver/.git` with `test -d`.
- The fixed receiver is a valid linked worktree; Git commands run from it can
  resolve repository metadata and status.
- No Mini receiver checkout, build configuration, cache, or TMPDIR was changed
  by the failed attempt.
- After the Git-native validation fix, the same bundle updated the linked
  receiver to full tip
  `93b91ea2e2e99ee90bab3ad89fccccb057953ea3`; the helper reported the fixed
  build and TMPDIR identities and `status=ready`.
- A direct retry with short tip `93b91ea` failed at the local full-SHA
  precondition after the fix; it did not contact the Mini. The helper now
  requires a 40-character full SHA, matching the official handoff path.

## Inferences

- The failure is a helper precondition bug, not a missing receiver and not a
  bundle corruption.
- `git rev-parse --is-inside-work-tree` is the stable validation seam because it
  accepts both `.git` directory and `.git` file representations.
- The full-SHA precondition is intentionally fail-fast because the remote
  bundle fetch needs an exact object identifier.

## Hypotheses and falsifiers

1. Replacing the filesystem-shape check with Git worktree validation will allow
   the same linked receiver to update. Falsifier: the helper still rejects the
   receiver before bundle fetch.
2. Detached checkout of the exact tip is valid for this linked receiver.
   Falsifier: Git rejects checkout or the build layer path no longer resolves.
3. The helper's existing dirty/evidence and active-BitBake gates remain valid.
   Falsifier: the replay changes a non-evidence file or proceeds with BitBake
   active.

## PDCA

### Plan

1. Add the contract assertion and run it to capture the expected RED result.
2. Apply the minimum helper change, update the skill/documentation, and rerun
   the static checks.
3. Replay the same remote bundle against the fixed receiver and record exact
   tip/clean/build identity evidence.

### Do

- Created this separate ticket after the bundle transfer passed but receiver
  validation failed on the linked-worktree representation.
- Added the RED contract assertion, then implemented Git-native receiver
  validation and the full-SHA precondition.
- Updated the checkpoint skill and bundle workflow documentation.
- Replayed the same transferred bundle successfully; the receiver reached the
  exact FLR-0116 tip and the fixed build/TMPDIR checks passed.

### Check

- Pre-fix linked-worktree contract: **RED reproduced**; the filesystem-shape
  check rejected the linked receiver.
- Existing handoff attempt: **FAIL** at receiver filesystem-shape check.
- Bundle transfer/hash: **PASS**.
- Full-SHA receiver exact-tip update: **PASS**.
- Short-SHA retry: **FAIL FAST** before remote access, by design.
- Receiver dirty/evidence, build, TMPDIR, and BitBake preconditions: **PASS**.

### Act

- Resume FLR-0116 at the Mini `do_patch` gate using receiver tip `93b91ea`.

## UNKNOWN

- No remaining UNKNOWN within this ticket: the linked receiver was updated and
  all later helper preconditions passed in the replay.

## Evidence locations

- Working log: `work/logs/2026-09-13-flr0117.md`
- Bundle handoff helper: `scripts/handoff-fluorite-bundle.sh`
- Receiver update helper: `scripts/reuse-mini-build-receiver.sh`
- Contract test: `tests/test-podman-bundle-handoff.sh`
