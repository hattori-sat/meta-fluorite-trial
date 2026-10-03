# FLR-0419 — make checkpoint-generated logs immediately verifiable

- Status: Inbox
- Priority: Medium
- Created: 2026-10-04
- Owner: runtime-checkpoint / regression-test roles
- Related discovery: [FLR-0418](FLR-0418-preserve-serial-wait-completion.md)
- Existing related work: [FLR-0361](FLR-0361-fail-closed-ticket-status-matcher.md) covers a different status-counting defect.

## Objective

Make `scripts/runtime-checkpoint.sh new` produce an iteration block that
immediately satisfies the headings required by `runtime-checkpoint.sh verify`,
or update the verifier to accept the generated contract. Today `new` writes
Facts/Inferences/Hypotheses/UNKNOWN/Evidence/Decision/Next action, while
`verify` requires a Check or Verification section; a fresh log therefore fails
its own follow-up gate until manually edited.

## Success criteria

1. A temporary-repository regression runs `new`, then `verify`, without manual
   heading edits and passes.
2. The generated log retains the required Facts, Hypotheses, UNKNOWN, Check,
   and Act/Next action evidence sections.
3. `--dry-run` still does not modify the log; the single-active-ticket guard
   remains fail-closed.
4. No QEMU, Mini, BitBake, product source, cache, or build operation is needed.

## Evidence and scope

- Triggered during FLR-0418 iteration setup on 2026-10-04: checkpoint `new`
  returned PASS, then immediate `verify` returned
  `working log has no Check or Verification section`.
- In scope: `scripts/runtime-checkpoint.sh` and
  `tests/test-runtime-checkpoint.sh` only.
- Out of scope: ticket-status matching tracked separately by FLR-0361 and all
  rendering/runtime investigation.

## Facts / inference / UNKNOWN

### Facts

- `new` does not emit a `### Check` heading in its generated block.
- `verify` requires `### Check` or `### Verification` in the log.

### Inference

- The helper's two documented operations currently do not compose without
  manual intervention, creating avoidable PDCA gate failures.

### UNKNOWN

- Whether other generated headings or script tests have the same producer / consumer mismatch.

## Plan / Do / Check / Act

### Plan

- Add an isolated fixture test that creates a ticket/log, runs `new`, then runs
  `verify` against the resulting log.

### Do

- Not started; remains in Inbox.

### Check

- Pending.

### Act

- Promote after FLR-0418 closes and before another workflow starts depending on
  the checkpoint helper.

## PDCA checker

- Status: NOT CHECKED
- Checked by:
- Findings: Reproducible command output and checker criteria are documented; no
  fix is claimed.
