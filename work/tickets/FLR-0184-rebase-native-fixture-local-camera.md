# FLR-0184 — rebase native fixture local-camera patch

- Status: Waiting
- Priority: High
- Owner: Mac Devtool source + Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0183](FLR-0183-rebase-wayland-child-surface-flush.md)
- Working log: `work/logs/2026-09-15-flr0184.md`

## Work unit

Rebase `0241-diag-keep-native-fixture-on-local-camera-devtool.patch` on the
current `view_target.cc` after the clean Mini gate advanced through 0240.

## Problem

The clean Mini gate stops at 0241 with one failed hunk at line 361 in
`plugins/filament_view/core/scene/view_target.cc`.

## Success criteria

- [ ] Capture current source and hash.
- [ ] Preserve a Devtool baseline and one source-change commit.
- [ ] Generate/register 0241 through official Devtool.
- [ ] Bundle once and prove clean Mini do_patch advances beyond 0241.

## Facts

- 0240 is retired as obsolete for the current API.
- 0241 is the next active patch boundary with one `view_target.cc` hunk.

## Inferences

- 0241 needs current-source context reconciliation; runtime meaning is UNKNOWN.
- The current source has no `vSetupCameraManagerWithDeserializedCamera`; the
  current ViewTarget owns a direct Filament camera instead. 0241 is therefore
  obsolete for this API, not merely shifted context.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: current-source rebase is sufficient | regenerated 0241 applies | earlier patch fails after clean reset |
| H2: one-file scope remains valid | only `view_target.cc` changes | additional paths change |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase native fixture local-camera diagnostic |
| Where | fixed Mac Devtool source and canonical layer |
| When | after 0240 retirement |
| Who | source, Devtool, Mini roles |
| How | exact source → guarded commit → update-recipe → bundle → clean gate |

## PDCA

### Plan

- Inspect 0241 and current source, generate one official patch, then run one
  clean Mini gate.

### Do

- Inspected 0241 and the current ViewTarget camera implementation.
- Removed only the 0241 active `SRC_URI` registration; retained the historical
  patch file.

### Check

- Mini clean gate: reset PASS; 0241 hunk 1 FAIL.
- Current source has no valid 0241 insertion point and uses the direct camera
  API instead of the removed camera-manager method.

### Act

- FLR-0185 owns 0242's current direct-camera lookAt implementation.

## UNKNOWN

- Current 0241 mapping and later patch boundary are UNKNOWN.
- Compile/runtime/QEMU/3D remain out of scope.

## Evidence

- Predecessor summary SHA256:
  `5a1110c7d81fe76cf1b8456e0fbc90a92925e3565f56492c18190271488c826d`.
- Predecessor bounded failure SHA256:
  `06aa56180fc7e73dbec1b256e1f7058aafc36a58b1ab5dc65d9837f62748144b`.
- 0241 is obsolete for the current API; no replacement source patch was
  generated.
- Mini clean gate after 0241 retirement: 0242 became the first failure.
  The gate evidence is recorded under FLR-0184.
