# FLR-0161 — make split-component Devtool rebase one-shot and bounded

- Status: Done
- Priority: High
- Owner: Mac Devtool workflow + Yocto layer integration role
- Created: 2026-09-15
- Updated: 2026-09-15
- Predecessor: [FLR-0160](FLR-0160-rebase-0221-current-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0161.md`

## Work unit

Reduce repeated split-component patch failures by providing one idempotent,
fail-closed entry point for the official Yocto Devtool rebase flow. The helper
must reuse the existing Podman container/state, use an explicit effective-source
baseline and source-change commit, and complete canonical patch registration and
baseline-lock refresh without making a local index file.

## Problem

The previous flow required separate manual `component-reset`, branch creation,
`component-add`, branch switching, `update-recipe`, patch copying, recipe
registration, and baseline-lock updates. A retry could reuse the wrong active
component or source baseline, and a successful source change could still omit
registration or lock metadata. This process cost more time than the patch
itself and made a Mini `do_patch` failure harder to classify.

## Success criteria

- [x] Preserve the in-progress 0222 source work without mixing it into this
  process ticket.
- [x] Add an idempotent `source-git-ensure-branch` operation that verifies an
  existing branch points at the requested commit before reusing it.
- [x] Add one split-component rebase helper that serializes official Devtool
  operations, selects exactly one generated patch by source commit, refuses
  unsafe overwrite, and verifies one recipe registration.
- [x] Automatically refresh the authorized project-layer baseline lock after
  patch registration.
- [x] Bound helper failure output to the first actionable lines instead of
  emitting the full Devtool log.
- [x] Run the contract tests and canonical verification, then create one local
  commit containing the helper, docs, and ticket evidence.

## Facts

- FLR-0160's current source edit was dirty in the persistent Devtool source and
  was preserved through the wrapper as stash `stash@{0}` with object
  `1036ec370027e5a2453d391479695a73d351d945`.
- The existing wrapper already serializes operations with one fixed lock and
  one persistent Podman container/state, but it exposed the rebase steps as
  separate commands.
- A local index file is not present in the canonical repository and is not a
  Yocto/Devtool input for this workflow.
- `conf/local.conf` is generated build state. The wrapper owns only its fixed
  `DL_DIR`, `SSTATE_DIR`, and `TMPDIR` block; it is not a layer file to commit.
- `manifests/baseline-sources.lock` is the tracked metadata required when the
  project layer changes.

## Inferences

- The highest-leverage correction is to make the source baseline, source
  commit, generated patch identity, registration, and lock update one checked
  transaction at the Mac workflow boundary.
- Existing branches can be reused safely only when their commit identity is
  exact; silently switching an existing branch to another commit would hide a
  source-history error.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: repeated failures are primarily process-state mismatch | explicit baseline/source commits plus idempotent branch checks remove reset/add ambiguity | the same exact source commit still generates a patch that does not match its baseline |
| H2: the remaining risk is canonical integration omission | one helper can prove byte-identical copy, one registration, and lock refresh | registration or lock still requires a second manual command |
| H3: bounded output is sufficient for the first failure boundary | helper output identifies the failing operation without dumping the raw log | diagnosis requires unselected historical log lines |

## 4W1H (Why excluded)

| Dimension | Record |
| --- | --- |
| What | Make split-component Devtool patch rebase reproducible and one-shot |
| Where | Fixed Mac Podman Devtool state and `meta-fluorite-trial` layer |
| When | Before resuming FLR-0160's 0222 source rebase and Mini `do_patch` |
| Who | Mac Devtool source role and Yocto layer integration role |
| How | explicit baseline/source commit → official reset/add/update → exact patch selection → registration/lock verification |

## PDCA

### Plan

1. Preserve any dirty source state and keep FLR-0160 as a separate waiting
   ticket.
2. Add the smallest wrapper primitive needed for safe branch reuse.
3. Add a single split-component orchestration helper and a lock-refresh helper.
4. Add contract tests and document the exact command and local-index policy.
5. Run repository verification and commit this process unit locally.

### Do

- Preserved FLR-0160's dirty 0222 source edit in the fixed Devtool source Git
  stash; no source edit was discarded.
- Added `source-git-ensure-branch` to the Podman wrapper and the container-side
  bounded Devtool command implementation.
- Added `scripts/rebase-fluorite-devtool-component.sh`, which captures each
  operation output, stops at the first failed boundary, reuses exact branches,
  uses official `component-reset`, `component-add`, and `update-recipe`, and
  rejects a non-identical canonical patch.
- Added `scripts/refresh-project-layer-baseline.py`; the rebase helper invokes
  it after canonical registration so a layer-file change cannot silently omit
  the lock refresh.
- Removed one duplicated Podman `AGL_SETUP_FEATURES` environment assignment.

### Check

- `make verify` passed: privacy, shell syntax, 85 Python tests, MCP smoke,
  Markdown links, file-size, QEMU/runtime harness, runtime-log slice, Devtool
  finish contract, and component-rebase contract.
- The exact 13-file scope was committed locally as `9012626`.
- Mini compile/image/QEMU work is intentionally not part of this process unit.

### Act

- Resume FLR-0160 by restoring its preserved source stash and use the new
  helper for the 0222 official patch generation.
- If the Mini gate still fails, create a new patch-boundary ticket and retain
  only the bounded task summary plus exact task-log path.

## Evidence

- Persistent source preservation: fixed Devtool source stash `stash@{0}`
  (`1036ec370027e5a2453d391479695a73d351d945`).
- New helper: `scripts/rebase-fluorite-devtool-component.sh`.
- New baseline refresh: `scripts/refresh-project-layer-baseline.py`.
- Working log: `work/logs/2026-09-15-flr0161.md`.
- Local commit: `9012626`.
