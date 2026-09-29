# FLR-0170 — deterministic Mini recipe patch gate

- Status: Done
- Priority: High
- Owner: fixed-receiver Yocto patch-gate role
- Created: 2026-09-15
- Predecessor: [FLR-0169](FLR-0169-rebase-0224-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0170.md`

## Work unit

Replace repeated ad-hoc Mini `do_patch` SSH commands with one deterministic,
recipe-scoped gate. This is a development-flow improvement and is independent
of the Fluorite 3D rendering diagnosis.

## Problem

The prior loop assembled a new remote command for each patch boundary. That
made the command shape, output volume, active-process checks, and task-log
selection vary between attempts. The 0229 failure was also buried in a long
BitBake output stream after 0224 had already passed.

## Success criteria

- [x] Add a fixed-receiver, fixed-build, fixed-TMPDIR recipe gate.
- [x] Reject image recipes and active BitBake duplicate processes.
- [x] Record a filtered metadata summary and bounded patch failure evidence.
- [x] Add a static contract test and include it in `make verify`.
- [x] Document the gate and its official Yocto workflow relationship.
- [x] Run the gate on the Mini PC against `flutter-auto` and record its first
  failing patch boundary.
- [x] Commit the script, tests, docs, and ticket evidence locally.

## Facts

- FLR-0169 regenerated 0224 through the fixed Mac Devtool source and official
  component-scoped `update-recipe`; the generated patch was byte-identical in
  the canonical layer.
- The manual Mini gate advanced through 0224 and stopped at 0229 hunk 2 in
  `light_system.cc`; the evidence is retained outside Git under the fixed
  receiver evidence role.
- The repository already enforces one fixed receiver/build/TMPDIR and bundle
  handoff, but did not yet provide one reusable recipe-scoped Mini gate.
- The new gate ran against receiver revision `11a2c01...`; metadata preflight
  passed and `do_patch` reproduced the first failure at 0229 hunk 2 in
  `light_system.cc`.

## Inferences

- A single validated gate reduces process variation without changing the
  recipe, source, or patch stack.
- Filtering at the evidence boundary saves context while retaining the first
  actionable patch boundary and exact task-log identity.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: the gate is deterministic | repeated invocation has the same preflight shape and selected recipe | gate creates a second build/TMPDIR or accepts a dirty receiver |
| H2: bounded output preserves diagnosis | failed 0229 run identifies the same first failed hunk and task log | failure output omits the first actionable boundary |
| H3: the flow is recipe-scoped | image recipes are rejected before BitBake | image task starts from this gate |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | fixed Mini recipe `do_patch` gate |
| Where | `$BUILD_RECEIVER`, `$BUILD_DIR`, `$BUILD_TMPDIR` |
| When | after one clean bundle handoff, before compile/image/QEMU |
| Who | handoff role, recipe patch-gate role, Mini BitBake role |
| How | contract preflight → filtered metadata → one forced `do_patch` → bounded evidence |

## PDCA

### Plan

1. Add the reusable gate and its contract test.
2. Run the gate once on the fixed Mini receiver for `flutter-auto`.
3. Record the exact first boundary and use a separate ticket for the 0229
   source rebase.

### Do

- Implemented `scripts/run-mini-recipe-patch-gate.sh`.
- Added its static contract test and `make verify` target.
- Documented the official recipe workflow and the bounded gate.

### Check

- Local shell syntax, contract test, and `git diff --check` pass.
- Mini execution passed its preflight and bounded-output checks. The gate
  failed for the expected independent 0229 source boundary, not in the gate.

### Act

- The workflow unit is committed and handed off. The next 0229 source rebase
  is owned by FLR-0171.
- Do not start compile, full image, or QEMU from this ticket.

## UNKNOWN

- Whether a regenerated 0229 patch compiles is UNKNOWN until FLR-0171.
- The 0229 source mismatch is outside this workflow ticket and belongs to its
  own follow-up ticket.

## Evidence

- Local contract test: `tests/test-mini-recipe-patch-gate.sh`.
- Official workflow reference: `docs/mac-devtool-bundle-workflow.md`.
- Bundle SHA-256: `cfa8be6740961ed56727fa914486f44c0ec8d1e852470e2c1fcd03775ea24dfb`.
- Gate summary SHA-256: `7cd2b2041d080b41fdbf551878c422fb58762fd9ca0a6f37eb0ec2c860746f49`.
- Bounded failure SHA-256: `7771eac40a0cc185f2032a88e94f7fe8e0a68fb2f93f4b2f1d6e96d4c191967f`.
- Metadata summary SHA-256: `32fa75be824b63bb1fe637c239ce905e807a25cecca98ab788ef5537efbfe831`.
- Exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3162127`.
