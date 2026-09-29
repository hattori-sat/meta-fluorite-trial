# FLR-0181 — allow valid QEMU override patch registrations

- Status: Done
- Priority: High
- Owner: Devtool rebase helper role
- Created: 2026-09-15
- Predecessor: [FLR-0180](FLR-0180-rebase-0228-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0181.md`

## Work unit

Fix the Devtool rebase helper's canonical registration check so one patch may
be registered on distinct machine override lines, while exact duplicate lines
remain rejected.

## Problem

QEMU patch 0228 is correctly registered for both `qemux86-64` and
`qemuarm64`. The helper counted occurrences of the shared registration text
and rejected the valid two-line override as non-unique, after Devtool had
already generated the correct current-API patch.

## Success criteria

- [x] Distinct override registration lines are accepted.
- [x] An exact duplicate registration line is rejected.
- [x] The helper remains byte-identical and fail-closed for canonical patch
  replacement.
- [x] Contract and full verification pass.
- [x] FLR-0180 resumed without hand-editing the generated patch.

## Facts

- The generated 0228 patch changes one current-API line from `Ultra` to
  `Lowest`.
- The active recipe has two valid 0228 registrations, one per QEMU machine.
- The helper currently rejects count greater than one rather than checking
  duplicate full registration lines.

## Inferences

- Registration uniqueness must be evaluated at full-line scope, not by the
  shared patch substring.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: full-line duplicate detection is correct | two distinct override lines pass | valid override lines still fail |
| H2: exact duplicates remain blocked | replay with an identical line fails closed | duplicate line is accepted |
| H3: generated patch flow is unchanged | FLR-0180 resumes through byte-identical canonical copy | helper alters generated patch content |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | fix valid QEMU override registration validation |
| Where | Devtool component rebase helper and contract test |
| When | before resuming 0228 canonical registration |
| Who | Devtool rebase helper role |
| How | full-line match set → exact duplicate check → normal copy/register |

## PDCA

### Plan

1. Replace occurrence counting with full-line duplicate detection.
2. Run helper contract and full verification.
3. Resume FLR-0180's official rebase flow.

### Do

- Added `assert_unique_registration_lines` to accept distinct override lines
  and reject exact duplicate lines.
- Added contract assertions for the new fail-closed check.

### Check

- `bash tests/test-devtool-component-rebase.sh`: PASS.
- `make verify`: PASS (52 MCP tests; 583 Markdown links; 989 files; QEMU,
  runtime-log, Devtool, and Mini gate contracts PASS).
- Official FLR-0180 rebase: PASS; the generated current-API patch was copied
  byte-identically and both QEMU override registrations passed.

### Act

- FLR-0180 owns the Mini clean gate for the regenerated 0228 patch.

## UNKNOWN

- Whether the resumed official rebase reaches canonical replacement is UNKNOWN.

## Evidence

- FLR-0180 generated source commit:
  `5b34318b08bfd59c1e94b438a2e3b2203bad4f91`.
