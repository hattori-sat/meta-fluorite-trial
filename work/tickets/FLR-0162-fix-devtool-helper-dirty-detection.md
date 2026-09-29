# FLR-0162 — fix false dirty detection in the one-shot Devtool helper

- Status: Done
- Priority: High
- Owner: Mac Devtool workflow role
- Created: 2026-09-15
- Updated: 2026-09-15
- Predecessor: [FLR-0161](FLR-0161-one-shot-devtool-component-rebase.md)
- Blocked work: [FLR-0160](FLR-0160-rebase-0221-current-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0162.md`

## Work unit

Correct the one-shot component-rebase helper's clean-source parser so a normal
Git branch header is not reported as a dirty source tree.

## Facts

- The fixed Devtool source was clean at commit `74d6154...` after the source
  commit.
- The helper stopped before patch generation with `source tree is dirty`.
- The bounded status output contains a normal `## branch` header and the
  wrapper's `mount-permission=PASS` line; neither is a worktree change.
- The parser used `$1` while matching a whole-line `## ` pattern, so the branch
  header could not match the intended exclusion.

## Inferences

- The failure is a helper parser defect, not a Devtool source or patch-context
  failure.
- Matching the complete line preserves the bounded status contract and avoids
  accepting unrelated output as clean.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: the branch header is the false dirty line | matching `$0` removes the false failure while a real ` M` line still fails | a clean status still fails or a modified status passes |
| H2: wrapper metadata is the only other benign line | excluding `mount-permission=` and `## ` is sufficient | another benign line is required for a clean status |

## Success criteria

- [x] Focused contract test passes and asserts whole-line branch-header parsing.
- [x] Full repository verification passes.
- [x] One local commit records only the helper and its contract test.

## PDCA

### Plan

1. Change the parser to match complete status lines.
2. Extend the static contract test for the `$0` match.
3. Run focused and full verification, then commit this independent fix.
4. Resume FLR-0160 and rerun the official component rebase helper.

### Do

- Changed the helper's dirty-line filter from field matching to complete-line
  matching.
- Added a contract assertion for the whole-line `## ` exclusion.

### Check

- Focused contract test and `make verify` passed.
- Local commit `974cefe` records the helper parser fix, contract test, and
  ticket evidence.

### Act

- This fix is Done. Resume FLR-0160 after the recipe-role guard in FLR-0163.

## Evidence

- First helper failure: `source tree is dirty` immediately after a clean
  `source-git-status` result.
- Fixed source status: clean branch at the committed 0222 source.
