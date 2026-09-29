# FLR-0157 — make Devtool and runtime evidence loops deterministic

- Status: Done
- Priority: High
- Owner: Mac Devtool handoff + runtime evidence harness roles
- Created: 2026-09-14
- Updated: 2026-09-15
- Predecessor: [FLR-0156](FLR-0156-restore-pure-fixture-camera-projection.md)
- Working log: `work/logs/2026-09-14-flr0157.md`

## Work unit

Remove repeated manual Devtool recipe-name/finish-destination errors and stop
full runtime-log dumps from consuming the investigation loop. Keep one fixed
Podman container, one source workspace, one finish layer, one build/TMPDIR, and
one raw runtime log per run; automate only selection and validation.

## Problem

- A direct `devtool finish flutter-auto ...` failed because the active Devtool
  recipe was `fluorite-plugins`, not `flutter-auto`.
- A direct finish into the canonical layer created an unwanted temporary
  `recipes-fluorite-plugins` scaffold. The generated patch was valid, but the
  destination and source-to-recipe mapping were not guarded.
- Runtime commands repeatedly used broad `grep` output against large serial
  logs. The raw log must remain available, but interactive output should only
  contain bounded, tagged boundary lines and first actionable errors.

## Success criteria

- [x] Add a fail-closed Devtool finish helper that resolves the active recipe
  from the source path, always finishes into the one fixed finish layer, selects
  the patch whose header matches the exact source commit, and refuses a wrong
  recipe, ambiguous result, duplicate registration, canonical scaffold, or
  dirty source state.
- [x] Add a bounded runtime-log slicer that never edits the raw log, selects
  only configured native/render/compositor/error markers, reports counts, and
  caps displayed lines deterministically.
- [x] Add static/unit checks for both helpers, including the observed wrong
  recipe and broad-log failure modes.
- [x] Record the current failure and a successful helper run in this ticket's
  working log before resuming FLR-0156.
- [x] Keep all changes in `meta-fluorite-trial`, commit locally, and do not
  start the camera build/QEMU gate until this ticket's checks pass.

## Facts

- The canonical repository guard passed before this ticket was created.
- The active persistent Devtool workspace reports `fluorite-plugins` and
  `filament-vk`; `flutter-auto` is not an active Devtool recipe.
- The current camera source commit is `fix: restore pure fixture camera
  projection`, and official finish generated a matching patch after the
  correct recipe was used.
- The copied camera patch is byte-identical to the official generated output;
  canonical registration is prepared but FLR-0156 is waiting for this process
  improvement.
- The wrapper now rejects canonical-layer finish destinations and treats any
  non-zero `devtool finish` exit as failure before inspecting generated patches.
- The wrapper now rejects canonical-layer finish destinations and treats any
  non-zero `devtool finish` exit as failure before inspecting generated patches.
- The raw FLR-0155 runtime log, QMP screenshot, and QMP video remain outside
  Git under the role-based receiver evidence path.

## Inferences

- The repeated Devtool failures are process-contract failures: the wrapper
  accepts a caller-supplied recipe and destination without checking the active
  source-to-recipe mapping or rejecting direct canonical finish output.
- Bounded selection is sufficient for interactive diagnosis because the raw
  log remains retained as evidence; selected output must preserve first error
  and boundary order without printing every frame/event.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: source-path recipe auto-resolution removes the wrong-recipe failure | helper resolves `fluorite-plugins` from Devtool status and never calls finish with `flutter-auto` | status contains zero or multiple matching recipes and helper still proceeds |
| H2: fixed finish layer plus exact source-commit matching prevents scaffold/patch ambiguity | helper returns one byte-stable patch for current source HEAD and canonical layer has no finish scaffold | more than one unmatched/current patch is accepted or canonical scaffold is created |
| H3: bounded marker slicing reduces loop output without losing first actionable boundary | selected output is capped and includes error/native/present/Wayland summaries while raw log hash/path is unchanged | selected output is unbounded or drops first actionable error |

## 4W1H (Why excluded)

| Dimension | Contract |
| --- | --- |
| What | deterministic Devtool finish and bounded runtime evidence selection |
| Where | `scripts/`, fixed Podman Devtool wrapper, runtime evidence loop |
| When | before each source patch handoff and after each runtime attempt |
| Who | Mac Devtool/handoff role and QEMU/runtime evidence role |
| How | fail-closed shell helpers with static/unit checks and one fixed state contract |

## PDCA

### Plan

1. Preserve the already-generated FLR-0156 camera patch and stop its Mini gate.
2. Implement the Devtool finish helper and bounded runtime-log slicer with
   tests for the observed failure modes.
3. Run repository verification, commit the improvement, then resume FLR-0156
   through the new helper.

### Do

- Ticket created after the wrong recipe and unwanted finish scaffold were
  observed during FLR-0156 patch generation.
- Implemented and exercised both helpers in the existing Podman container/state;
  the full failure sequence and successful run are in the working log.

### Check

- `bash -n` for the changed shell files, runtime-log unit test, Devtool finish
  contract test, and a real persistent-container helper run all passed. The
  helper returned the exact source HEAD and byte-identical patch SHA; no
  canonical finish scaffold remains.
- `make verify` passed after the baseline lock was updated for the registered
  camera patch: privacy, shell, Python, MCP, Markdown, file-size, QEMU/runtime
  harness, runtime slicer, and Devtool finish contract gates all returned exit
  status 0.

## UNKNOWN

- FLR-0156's camera projection patch has not yet been built on the Mini PC or
  validated with a new QMP-only frame. 3D visibility remains UNKNOWN until
  that separate ticket is resumed.

### Act

- Local commit `b6f7e3c` contains this improvement state and the prepared
  FLR-0156 patch registration. FLR-0157 is complete; resume FLR-0156 as the
  next independently verifiable unit.
- If a helper cannot prove a unique current source patch, stop and retain the
  raw output; do not fall back to manual patch manufacture.

## Evidence

- Failure: `devtool finish flutter-auto` returned `No recipe named
  'flutter-auto' in your workspace`.
- Current finish output and camera patch: `$RECEIVER` role path under the
  FLR-0156 handoff evidence.
- Raw runtime evidence predecessor:
  `$RECEIVER/evidence/flr0155/qemu-diagnostic-20260914/`
