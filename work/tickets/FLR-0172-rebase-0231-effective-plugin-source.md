# FLR-0172 — rebase 0231 on the effective plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0171](FLR-0171-rebase-0229-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0172.md`

## Work unit

Rebase `0231-fix-wait-for-ecs-systems-before-channel-setup-devtool.patch` on
the exact effective source after 0229. Use the fixed Mac Podman Devtool source,
official `update-recipe`, and the deterministic Mini recipe gate.

## Problem

Mini `do_patch` now applies 0229, then 0231 fails at hunk 1 in
`plugins/filament_view/filament_view_plugin.cc`; hunks 2 and 3 apply with fuzz.
The patch context is stale against the current effective source.

## Success criteria

- [x] Capture the exact effective 0231 target source and hash.
- [x] Keep one active Devtool recipe for the selected source path.
- [x] Import the effective source as the baseline through the source Git wrapper.
- [x] Commit only the intended 0231 source change through guarded `git add .`
  and staged-path validation.
- [x] Generate and register the official Devtool patch in the canonical layer.
- [x] Hand off one commit and prove Mini `do_patch` advances beyond 0231.

## Facts

- FLR-0171 regenerated 0229 and the deterministic gate proved 0229 applies.
- The next boundary is 0231 hunk 1 in `filament_view_plugin.cc`.
- Compile, full image, QEMU, and 3D remain unstarted for this boundary.
- The effective target `filament_view_plugin.cc` SHA-256 is
  `42f6a1607daf94d4954bad4ca04db493ebf9c59b60251e065522e38f36f71268`.
- Official Devtool used baseline `bda328c9da9d4f5e7eb067bec3c2f2f8a4fd9cf5`
  and source commit `3c08dbb36b073b16c2553925fa3478268e6ad362`.
- Generated canonical 0231 patch SHA-256 is
  `41fb70c509f546f8ba3ef37580ba812a2c5abcf652e537ff34856dd110d1b394`.
- Mini `do_patch` applied 0231 and advanced to 0233; 0233 hunk 2 is the next
  independent boundary owned by FLR-0173.

## Inferences

- 0231 is a stale-context source rebase, not a failure of the new gate.
- The one-to-one Devtool registration and guarded source commit flow are now
  reusable prerequisites.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0231 has stale context | effective-source Devtool generation applies after 0229 | regenerated patch fails at the same context |
| H2: one source baseline is sufficient | one active component registration yields stable update-recipe output | duplicate or wrong-source registration remains |
| H3: current API remains compatible | do_patch advances beyond 0231 and compile is next | compile rejects the regenerated change |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase 0231 ECS/channel setup patch |
| Where | fixed Mac Devtool source and canonical layer |
| When | after 0229, before compile/image/QEMU |
| Who | source, Devtool, and Mini BitBake roles |
| How | effective source → baseline → source commit → update-recipe → recipe gate |

## PDCA

### Plan

1. Read only the 0231 task boundary and target source file.
2. Import the effective source into the fixed Devtool source and preserve both
   baseline and source-change commits.
3. Generate the official patch and validate it with the fixed Mini gate.

### Do

- Imported and committed the effective source baseline through the wrapper.
- Applied and committed the intended current-API channel setup change.
- Re-generated and registered 0231 with official Devtool.

### Check

- FLR-0171 gate: 0229 PASS, 0231 hunk 1 FAIL.
- Final gate: 0231 PASS, 0233 hunk 2 FAIL.

### Act

- 0231 is complete; continue with FLR-0173 for 0233.

## UNKNOWN

- The exact effective 0231 source semantics are UNKNOWN until imported.
- Runtime and 3D behavior are UNKNOWN and must not be inferred from patch
  application.

## Evidence

- Predecessor gate summary: fixed receiver evidence role for FLR-0171.
- Exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3169194`.
- Final task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3173793`.
- Bundle SHA-256: `d5480d20825505f1d897021d9f168fc1a2bf4e3bebebac5e1a7385256bfa08e4`.
- Gate summary SHA-256: `37fe44a9339955f7c230cb9cf212cda866a467bb30fac9b8a1ade5d3f1e9a738`.
- Result: `0231=PASS`, `0233 hunk 2=FAIL`; compile/image/QEMU/3D were not run.
