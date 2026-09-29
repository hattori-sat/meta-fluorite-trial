# FLR-0361 — fail closed on legacy active-ticket status variants

- Status: Inbox
- Priority: Medium
- Owner: ticket-state / runtime-checkpoint roles
- Created: 2026-09-29
- Predecessor: [FLR-0359](FLR-0359-use-committed-qemu-runtime-helper.md)
- Working log: [FLR-0361 log](../logs/2026-09-29-flr0361.md)
- Plan: [implementation plan](../../docs/superpowers/plans/2026-09-29-flr0361-fail-closed-ticket-status-matcher.md)

## Objective

Make the runtime checkpoint reject multiple active tickets even when older ticket files express the status as `In Progress — Do`, `In Progress — Check`, or `In Progress (Do)` rather than the canonical exact status.

## Evidence and problem point

- During FLR-0359 closeout, `runtime-checkpoint.sh verify` printed `active=1` while FLR-0015, FLR-0017, FLR-0018, and FLR-0025 still contained legacy In Progress variants alongside FLR-0359.
- The current matcher searches only the exact line `^- Status: In Progress$`; it silently ignores both suffix variants and the legacy line without a Markdown bullet.
- Those four tickets were normalized to Waiting in FLR-0359 closeout because their own records show incomplete work but no current execution. This corrects current state, but does not fix the matcher.

## Success criteria

1. A deterministic fixture test fails against the current matcher when one canonical In Progress ticket and one legacy In Progress variant coexist.
2. The corrected checker recognizes all documented legacy spellings as active and fails with an actionable count instead of printing `active=1`.
3. Waiting/Done tickets are not counted as active.
4. Existing checkpoint verification and dry-run tests pass; no QEMU, Mini, BitBake, or product source work is performed.

## Scope

- In scope: `scripts/runtime-checkpoint.sh`, its deterministic test, and this ticket's PDCA record.
- Out of scope: changing the statuses normalized by FLR-0359, altering unrelated old tickets, or changing QEMU/render acceptance.

## Facts / inference / UNKNOWN

### Facts

- The false-positive result was observed during FLR-0359 closeout.
- Four legacy ticket files used active status variants; the exact matcher did not count them.

### Inference

- The checkpoint gate is not fail-closed against status syntax drift; a stale active task can be hidden while the dashboard claims the WIP limit is met.

### UNKNOWN

- Whether there are other legacy status spellings outside the current scan. The regression test should define supported legacy variants and reject unrecognized `In Progress...` forms rather than silently treating them as inactive.

## PDCA

### Plan

- Add a temporary-repository fixture with one canonical and one legacy active status; observe the current false PASS; update the matcher; verify red-to-green and the full checkpoint test.

### Do

- Not started. FLR-0359 remains the sole In Progress unit; this ticket stays in Inbox.

### Check

| Gate | Expected | Result |
| --- | --- | --- |
| Legacy variant fixture | Current implementation fails the test; corrected implementation detects two active tickets | NOT RUN |
| Existing checkpoint tests | PASS | NOT RUN |

### Act

- Promote only after FLR-0359 closeout passes. Keep the ticket-state fix separate from QEMU attach diagnostics.

## PDCA checker

- Status: NOT CHECKED
- Checked by: pending
- Findings: evidence is linked to the closeout defect; no source change or implementation is claimed.
