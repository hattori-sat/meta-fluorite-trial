# FLR-0183 — rebase Wayland child-surface flush patch

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0182](FLR-0182-rebase-effective-viewtarget-frame-boundary.md)
- Working log: `work/logs/2026-09-15-flr0183.md`

## Work unit

Rebase `0240-diag-flush-wayland-child-surface-after-present-devtool.patch`
on the exact current `view_target.cc` after FLR-0182 passed.

## Problem

The clean Mini gate stops at 0240 with one failed hunk at line 617 in
`plugins/filament_view/core/scene/view_target.cc`.

## Success criteria

- [x] Capture the exact current target source and hash.
- [x] Confirm whether 0240 has a valid current-API mapping.
- [x] Keep the historical 0240 patch out of active `SRC_URI` when its
  current-API precondition is absent.
- [x] Bundle once and prove clean Mini do_patch advances beyond 0240.

## Facts

- FLR-0182 passed and the next failure is 0240.
- 0240 has one `view_target.cc` hunk.
- Current `OnFrame` explicitly says not to call `wl_surface_commit` because
  commit occurs elsewhere; the 0240 context is therefore obsolete, not merely
  shifted line numbers.

## Inferences

- 0240 has stale source context; no runtime conclusion follows.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: one current-source mapping is sufficient | regenerated 0240 applies | another earlier patch fails |
| H2: the patch remains one-file scoped | only `view_target.cc` changes | additional files change |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase Wayland child-surface flush diagnostic |
| Where | fixed Mac Devtool source and canonical layer |
| When | after FLR-0182 |
| Who | source, Devtool, Mini roles |
| How | exact source → guarded commit → update-recipe → bundle → clean gate |

## PDCA

### Plan

1. Inspect only 0240 and the current target function.
2. Edit one source file through the fixed Devtool Git wrapper.
3. Generate/register, bundle, and run one clean Mini gate.

### Do

- Inspected the 0240 hunk and the current clean `OnFrame` implementation.
- Removed only the 0240 active `SRC_URI` registration; retained the historical
  patch file.

### Check

- Mini clean gate before this ticket: reset PASS and 0240 hunk 1 FAIL.
- Current source contains no valid 0240 commit/flush insertion point and
  explicitly documents that commit is performed elsewhere.

### Act

- The next clean gate boundary will be split into a new ticket after this
  checkpoint.

## UNKNOWN

- Current mapping of 0240 is UNKNOWN until inspected.
- Compile/runtime/QEMU/3D remain out of scope.

## Evidence

- Predecessor summary SHA256:
  `df202bad22f213aa4fab110e0e9326c3673fa1df4b05254eb7107d8308e68304`.
- Predecessor bounded failure SHA256:
  `396d3ba3a97b20b6a00981152f00e5a6f28f4f3d140721f51b177efe5195881f`.
- 0240 is obsolete for the current API; no replacement source patch was
  generated.
- After retirement, clean Mini do_patch advanced to 0241. Summary SHA256:
  `5a1110c7d81fe76cf1b8456e0fbc90a92925e3565f56492c18190271488c826d`.
- 0241 bounded failure SHA256:
  `06aa56180fc7e73dbec1b256e1f7058aafc36a58b1ab5dc65d9837f62748144b`.
- 0241 task log SHA256:
  `fd026b1332b6b50f63fa0e2b11ce01742ff6f3dce9dbddf4ea47ffa1a748a590`.
