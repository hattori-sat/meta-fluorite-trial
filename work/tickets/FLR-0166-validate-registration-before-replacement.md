# FLR-0166 — validate registration before canonical patch replacement

- Status: Done
- Priority: High
- Owner: Mac Devtool workflow + layer integration role
- Created: 2026-09-15
- Updated: 2026-09-15
- Predecessor: [FLR-0165](FLR-0165-explicit-canonical-patch-replacement.md)
- Blocked work: [FLR-0160](FLR-0160-rebase-0221-current-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0166.md`

## Work unit

Make canonical patch replacement transactional at the helper boundary: validate
the existing Yocto registration before copying a new generated patch.

## Facts

- Explicit replacement copied the generated patch, then rejected the existing
  multiline `SRC_URI` registration because the helper expected a one-line
  assignment.
- The canonical patch became a working-tree change before the helper failed.
- The existing bbappend registration already contains the correct patch name
  and `patchdir` on one multiline entry.

## Inferences

- Registration validation must use the registration line fragment and happen
  before any canonical patch copy.
- The generated patch and registration must both pass before the lock refresh.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: ordering caused the partial update | validation-before-copy prevents canonical changes when registration is invalid | a failed run still changes the patch |
| H2: fragment matching supports Yocto multiline syntax | existing `file://...;patchdir=...` passes without appending a duplicate | valid multiline registration is rejected |

## Success criteria

- [x] Invalid registration fails before canonical patch copy.
- [x] Existing multiline registration is accepted exactly once.
- [x] Contract/full verification passes.
- [x] One local commit records only this ordering fix, test, and evidence.

## PDCA

### Plan

1. Validate the registration fragment before target copy.
2. Keep default mismatch refusal and explicit replacement behavior.
3. Test and run full verification, then commit locally.
4. Resume FLR-0160 and record the generated/canonical hashes.

### Do

- Moved registration validation ahead of canonical patch replacement.
- Matched the existing multiline Yocto registration by its exact file/patchdir
  fragment.
- Kept the explicit replacement old-SHA output.

### Check

- The corrected helper accepted the existing multiline registration before
  copying and completed the explicit replacement path.
- It reported previous SHA-256
  `869611ac03fe1721404a2b32799576fadaf41d5a43f1209da257543de5cab596` and
  generated SHA-256
  `d54a77c21647167759ad60f34e64327c14c3d5c204c46889d49f2e8dc38c17f4`.
- The focused contract and `make verify` passed.
- Local commit is the remaining closeout action.

### Act

- This fix is Done after its local commit. FLR-0160 now owns the generated
  patch, canonical registration, and baseline-lock change.

## Evidence

- Partial-update failure: canonical patch changed before the registration
  mismatch was reported.
