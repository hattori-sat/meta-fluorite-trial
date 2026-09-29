# FLR-0163 — reject wrong recipe before split-component Devtool reset

- Status: Done
- Priority: High
- Owner: Mac Devtool workflow role
- Created: 2026-09-15
- Updated: 2026-09-15
- Predecessor: [FLR-0162](FLR-0162-fix-devtool-helper-dirty-detection.md)
- Blocked work: [FLR-0160](FLR-0160-rebase-0221-current-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0163.md`

## Work unit

Make the split-component rebase helper fail closed when the caller supplies an
outer recipe name for a source path that is registered under a different
Devtool component recipe.

## Facts

- The helper was invoked with `flutter-auto` for the nested source path.
- The fixed Devtool status identifies the source component as
  `fluorite-plugins`; `flutter-auto` is the outer recipe.
- The helper accepted the mismatch, ran reset/add, and reached
  `update-recipe`, which failed with `Unable to find initial revision`.
- The source tree remained clean at the intended source commit; no canonical
  patch was overwritten by this failed attempt.

## Inferences

- The first actionable boundary is caller recipe/source-role validation, not
  `update-recipe` initial-revision handling.
- The helper must inspect exact source-path registrations before any reset or
  add operation.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: wrong outer recipe is the cause | exact source-path/active-recipe guard rejects `flutter-auto` before reset and accepts `fluorite-plugins` | correct component recipe still reaches the same failure |
| H2: multiple registrations need explicit component selection | a mismatch or ambiguous source mapping is reported before mutation | helper silently selects an outer recipe |

## Success criteria

- [x] Helper rejects a source/recipe mismatch before `component-reset`.
- [x] Contract test covers the source-path/active-recipe guard.
- [x] Full repository verification passes.
- [x] One local commit records only this guard, test, and evidence.

## PDCA

### Plan

1. Parse the exact source path from bounded `devtool status` output.
2. Reject a requested recipe unless it is registered for that exact source path.
3. Add a static contract test and run full verification.
4. Commit locally, then resume FLR-0160 with `fluorite-plugins`.

### Do

- Added the source-path/active-component guard before `component-reset`.
- Added a contract assertion for the required split component recipe.
- Replayed the wrong-recipe case; it stopped with the expected guard message
  before reset/add and reported `wrong-recipe guard: PASS`.

### Check

- Focused wrong-recipe guard test passed.
- `make verify` passed: privacy, shell syntax, 85 Python tests, MCP smoke,
  Markdown links, file-size, QEMU/runtime harness, runtime-log slice, Devtool
  finish contract, and component-rebase contract.
- Local commit is pending at this ticket boundary.

### Act

- This ticket is Done after its local commit. Resume FLR-0160 using
  `fluorite-plugins` as the split component recipe and preserve the outer
  `flutter-auto` bbappend as the canonical registration target.

## Evidence

- Bounded failure: `update-recipe` reported `Unable to find initial revision`.
- Pre-failure status showed the same source path registered for the component
  role `fluorite-plugins` and outer role `flutter-auto`.
