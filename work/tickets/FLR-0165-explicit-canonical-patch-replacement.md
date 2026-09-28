# FLR-0165 — allow explicit canonical patch replacement during rebase

- Status: Done
- Priority: High
- Owner: Mac Devtool workflow + layer integration role
- Created: 2026-09-15
- Updated: 2026-09-15
- Predecessor: [FLR-0164](FLR-0164-standard-devtool-update-recipe.md)
- Blocked work: [FLR-0160](FLR-0160-rebase-0221-current-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0165.md`

## Work unit

Permit the one-shot helper to replace an existing canonical patch only when
the caller explicitly requests a rebase replacement, and record the old
SHA-256 alongside the new one.

## Facts

- Standard official update-recipe generated one current-source patch.
- The existing canonical 0222 slot differs from that generated patch.
- The helper correctly refused to overwrite it, so no canonical change was
  made by the failed run.
- Rebase of the same patch slot is an intentional layer mutation in FLR-0160.

## Inferences

- Silent overwrite is unsafe, but permanent refusal makes an intentional
  patch rebase impossible through the one-shot workflow.
- An explicit flag plus old/new hash evidence preserves both safety and speed.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: explicit replacement is sufficient | the flag replaces only the selected canonical patch and reports the previous SHA | another file changes or the old SHA is absent |
| H2: default refusal remains useful | the same mismatch without the flag still stops before copy | mismatch is silently overwritten without the flag |

## Success criteria

- [x] Default mismatch still fails closed.
- [x] Explicit replacement copies only the byte-checked generated patch and reports the previous SHA.
- [x] Contract/full verification passes.
- [x] One local commit records the helper, docs, tests, and evidence.

## PDCA

### Plan

1. Add an optional explicit replacement flag.
2. Preserve default refusal and print the previous canonical SHA on replacement.
3. Add contract checks, run full verification, and commit locally.
4. Resume FLR-0160 using the flag for the intentional 0222 rebase.

### Do

- Added `--replace-canonical` as an explicit opt-in.
- Added previous-SHA evidence after a successful replacement.
- Updated the runbook and contract test.

### Check

- Default mismatch replay stopped with the expected refusal message.
- Contract test and `make verify` passed.
- Local commit is the remaining closeout action.

### Act

- This ticket is Done after its local commit. Rerun FLR-0160 with explicit
  replacement and record the generated/canonical SHA in its ticket.

## Evidence

- Failed closed boundary: `existing canonical patch differs; refusing overwrite`.
- Reference generated patch exists in the fixed workspace append directory.
