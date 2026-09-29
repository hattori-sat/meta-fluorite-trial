# FLR-0164 — use the standard Devtool update-recipe path

- Status: Done
- Priority: High
- Owner: Mac Devtool workflow role
- Created: 2026-09-15
- Updated: 2026-09-15
- Predecessor: [FLR-0163](FLR-0163-reject-wrong-devtool-recipe.md)
- Blocked work: [FLR-0160](FLR-0160-rebase-0221-current-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0164.md`

## Work unit

Make the one-shot split-component helper use Yocto's standard
`update-recipe --mode patch --append --no-remove` path after baseline
registration, without forcing an explicit initial revision.

## Facts

- Correct component recipe `fluorite-plugins` still failed when the helper
  passed `--force-patch-refresh --initial-rev <baseline>`.
- In the same fixed container/source state, the standard update-recipe command
  with no optional flags succeeded and generated one patch.
- Previous successful FLR-0155/0157 records use the standard path after
  baseline registration.

## Inferences

- The helper's forced initial-revision option is the first remaining process
  defect in this rebase path.
- The explicit baseline/source commits and branch checks remain useful; the
  Devtool command itself should follow the standard documented path.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: forced initial revision causes the failure | removing optional flags lets the helper select the committed source delta and generate one patch | helper still fails or emits no source-matching patch |
| H2: baseline branch checks are sufficient | standard update-recipe preserves exact source-commit matching | generated output is ambiguous or unrelated |

## Success criteria

- [x] Helper no longer invokes `--initial-rev` or force-refresh for this path.
- [x] Contract test proves the standard update-recipe contract.
- [x] Full repository verification passes.
- [x] One local commit records only this helper correction, test, docs, and evidence.

## PDCA

### Plan

1. Keep the successful standard command as the reference behavior.
2. Remove optional initial-revision/force-refresh arguments from the helper.
3. Add the static contract assertion and run full verification.
4. Commit locally, then rerun FLR-0160's helper with `fluorite-plugins`.

### Do

- Changed the helper to call standard component `update-recipe` with only the
  recipe and fixed workspace layer.
- Updated the workflow documentation and contract test.

### Check

- Contract test and `make verify` passed.
- The standard reference command generated one patch in the fixed workspace
  append directory.
- Local commit is the remaining closeout action.

### Act

- This ticket is Done after its local commit. Rerun FLR-0160 and inspect the
  generated patch before touching canonical registration.

## Evidence

- Failed helper boundary: `Unable to find initial revision`.
- Successful reference boundary: standard update-recipe generated one patch
  under the fixed workspace append directory.
