# FLR-0178 — make the Mini recipe patch gate deterministic

- Status: Done
- Priority: High
- Owner: Yocto Mini build and patch-gate role
- Created: 2026-09-15
- Predecessor: [FLR-0177](FLR-0177-rebase-0239-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0178.md`

## Work unit

Make the authoritative Mini `do_patch` check independent of stale or
manually-modified recipe workdirs. Keep the fixed build/TMPDIR and receiver,
and reset only the selected recipe workdir before applying the committed
recipe patch stack.

## Problem

The 0239 gate failed against a `view_target_system.cc` whose API shape did not
match the source immediately preceding 0239. Mac Devtool history retained the
expected predecessor, while the Mini `S` tree contained a different source
state. Reusing that workdir makes the first failing patch depend on prior
operations instead of the receiver commit and recipe metadata.

## Success criteria

- [ ] The gate records metadata and the selected recipe workdir reset result.
- [ ] The gate uses only `bitbake -f -c clean <recipe>` for reset; it does not
  use `cleanall`, `cleansstate`, or delete shared downloads/sstate/TMPDIR.
- [ ] A reset failure stops before `do_patch` and exposes bounded diagnostics.
- [x] A reset followed by `do_patch` gives a reproducible first patch boundary.
- [x] Shell contract and full repository verification pass.

## Facts

- Fixed Mini receiver, build directory, and TMPDIR are already part of the
  existing gate contract.
- The prior gate passed 0236, 0237, and 0238, then failed both 0239 hunks.
- The Mini effective target file SHA256 was
  `25468df139f1b454c375dc9265cded50ee2a2d67ac13287fdcd67fbb446551d4`.
- The source state did not contain the `vOnInitSystem` and
  `vSetCameraFromSerializedData` context present in 0239.

## Inferences

- The mismatch is consistent with a reused or otherwise non-predecessor
  workdir; it is not sufficient evidence that the 0239 source change itself
  is wrong.
- Resetting the single recipe workdir is the smallest deterministic repair
  that preserves downloads, sstate, and the shared TMPDIR.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: stale recipe workdir caused the source mismatch | clean→do_patch starts from the recipe's unpacked source and changes the first boundary | clean→do_patch reproduces the same mismatch with identical source identity |
| H2: the reset is scoped safely | downloads, sstate, shared TMPDIR, and other recipes remain present | reset removes data outside this recipe workdir |
| H3: the gate is fail-closed | reset failure prevents do_patch and reports a bounded clean error | do_patch starts after a reset failure |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | deterministic recipe workdir reset before patch gate |
| Where | fixed Mini build role and fixed receiver |
| When | immediately before the selected recipe's do_patch |
| Who | Yocto patch-gate role |
| How | metadata → recipe-scoped clean → bounded do_patch → first boundary |

## PDCA

### Plan

1. Add a recipe-scoped clean step to the existing bounded gate.
2. Fail closed if that reset fails and retain only bounded diagnostics in the
   tracked evidence summary.
3. Run the contract and full verification, then use the gate before resuming
   the 0239 Devtool rebase.

### Do

- Added `bitbake -f -c clean "$recipe"` immediately before the forced
  `do_patch` task in the fixed Mini gate.
- Added bounded `workdir-reset=PASS` and `workdir-reset=FAIL` evidence; a
  reset failure exits before `do_patch`.
- Added contract assertions for the command and fail-closed output.

### Check

- `bash -n scripts/run-mini-recipe-patch-gate.sh`: PASS.
- `bash tests/test-mini-recipe-patch-gate.sh`: PASS.
- `make verify`: PASS (52 MCP tests; 577 Markdown links; 983 files; QEMU,
  runtime-log, Devtool, and Mini gate contracts PASS).
- Mini clean→do_patch gate: preflight PASS, metadata PASS,
  `workdir-reset=PASS mode=recipe-clean`, and the same 0239 hunk 1/2 failure
  reproduced. Summary SHA256:
  `049eda25f508e557e223bee22c6db203d11bb6af15cdf17deb61f59ed8db7bd5`.
- Mini bounded failure SHA256:
  `2267ef90c031ff275d1ac3b56a6115f79a928f74499972497573c9cdda09ed2d`.
- Mini task log SHA256:
  `4f2209960cc716392857486cee6cb41daddbdf98106309ca78e8101a7b4622ff`.

### Act

- Commit this gate improvement locally. FLR-0179 now owns removal of the
  obsolete 0239 recipe item; FLR-0177 resumes only for a real current-API
  camera change.

## UNKNOWN

- Whether the Mini clean→do_patch run will apply 0239 is UNKNOWN until the
  updated gate executes.
- Runtime, QEMU, and 3D behavior remain outside this work unit.

## Evidence

- Predecessor: `work/tickets/FLR-0177-rebase-0239-effective-plugin-source.md`.
- Prior bounded failure SHA256:
  `2318e61866426ecd984b32d044eb92814acaa3607127f81f63c096ea8eca6c51`.
- Local verification: `make verify` PASS on 2026-09-15.
