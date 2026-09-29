# FLR-0176 — rebase 0236 on the effective plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0175](FLR-0175-rebase-0235-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0176.md`

## Work unit

Rebase `0236-fix-defer-viewtarget-request-until-ecs-init-devtool.patch` on the
exact effective source after 0235. Use the fixed Mac Podman Devtool source,
official `update-recipe`, and the deterministic Mini recipe gate.

## Problem

Mini `do_patch` applies through 0235, then both 0236 hunks fail in
`plugins/filament_view/filament_view_plugin.cc`. The patch context is stale
against the current effective source.

## Success criteria

- [x] Capture the exact effective 0236 target source and hash.
- [x] Keep one active Devtool recipe for the selected source path.
- [x] Import the effective source as the baseline through the source Git wrapper.
- [x] Commit only the intended 0236 source change through guarded `git add .`
  and staged-path validation.
- [x] Generate and register the official Devtool patch in the canonical layer.
- [x] Hand off one commit and prove Mini `do_patch` advances beyond 0236.

## Facts

- FLR-0175 regenerated 0235 and the deterministic gate proved 0235 applies.
- The next boundary is 0236 hunks 1 and 2 in `filament_view_plugin.cc`.
- The exact next effective target SHA256 is
  `f5e44d4c4b68a41349765c34733da6e61cf089d64eb32eef9d6a69d34c699142`.
- The effective source exposes `vInitSystems` / `vRouteMessage` in
  `ECSManager`, while existing `filament_view_plugin.cc` call sites use
  `initialize` / `RouteMessage`. This pre-existing API mismatch is separate
  from the 0236 patch context and requires compile-time follow-up.
- The fixed Mac Devtool baseline commit is
  `eecd1c2a89022cf814d6251459fd5d431da1a4ed`; the guarded source change is
  commit `df40bd7a757333d9550f7b211a993b83c5850a2d`.
- Compile, full image, QEMU, and 3D remain unstarted for this boundary.

## Inferences

- 0236 is a stale-context source rebase, not evidence against the
  deterministic recipe gate.
- The one-to-one Devtool registration and guarded source commit flow remain
  reusable prerequisites.
- The old 0236 patch also assumes the `v*` ECS API at its context boundaries;
  the effective source must be reconciled against the actual public API before
  compile claims are made.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0236 has stale context | effective-source Devtool generation applies after 0235 | regenerated patch fails at the same context |
| H2: one source baseline is sufficient | one active component registration yields stable update-recipe output | duplicate or wrong-source registration remains |
| H3: deferred ViewTarget request API remains compatible | do_patch advances beyond 0236 and compile is next | compile rejects the regenerated change |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase 0236 deferred ViewTarget request patch |
| Where | fixed Mac Devtool source and canonical layer |
| When | after 0235, before compile/image/QEMU |
| Who | source, Devtool, and Mini BitBake roles |
| How | effective source → baseline → source commit → update-recipe → recipe gate |

## PDCA

### Plan

1. Read only the 0236 task boundary and target source file.
2. Import the effective source into the fixed Devtool source and preserve both
   baseline and source-change commits.
3. Generate the official patch and validate it with the fixed Mini gate.

### Do

- Imported the exact effective `filament_view_plugin.cc` and committed the
  baseline through the source Git wrapper.
- Rebased the deferred ViewTarget request change onto the effective API,
  including same-strand routing and `v*` ECS method names at the affected
  boundaries.
- Ran official Devtool `component-add` and `update-recipe`; the generated patch
  was copied byte-identically to canonical 0236. Generated/canonical SHA256 is
  `4d0e201b03d2453d53c92d773f63a88d5ca531bf9ea44dc5640e84981c11fd62`.

### Check

- FLR-0175 gate: 0235 PASS; 0236 hunks 1/2 FAIL.
- Static API check: `ECSManager` declares `vInitSystems` and `vRouteMessage`,
  but existing plugin call sites use undeclared `initialize` and
  `RouteMessage`; compile status is UNKNOWN until a separate API-alignment
  task is scoped.
- Mac-side official rebase: PASS; one source commit, one generated patch,
  canonical registration PASS, baseline lock refreshed.
- Mini recipe gate is the remaining check: hand off the canonical commit and
  prove that 0236 applies.
- Mini recipe gate: preflight PASS, metadata PASS, 0236 PASS; 0237/0238 also
  passed before the next first failing patch, 0239. Both 0239 hunks fail in
  `view_target_system.cc`.

### Act

- Commit the canonical patch/lock checkpoint, hand off one bundle to the fixed
  receiver, and run the recipe-scoped Mini `do_patch` gate.

## UNKNOWN

- Whether 0239 and later patches apply is UNKNOWN and is split to FLR-0177.
- Runtime and 3D behavior are UNKNOWN and must not be inferred from patch
  application.

## Evidence

- Predecessor: `work/tickets/FLR-0175-rebase-0235-effective-plugin-source.md`.
- Exact failing task log:
  `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3185064`.
- Mini bounded failure evidence SHA256:
  `5e97fed5001b38ae55421d20963eb108f950e26e03bff9aa760f1e77d3549e89`.
- Bundle SHA256: `3f3174b4716d10826aeb816cadb0562635a953cc369688267374c2bbab331570`.
- Mini receiver revision: `4667dc5c6f947eacf77ac77371a24109eaeefbce`.
- Mini metadata evidence SHA256:
  `32fa75be824b63bb1fe637c239ce905e807a25cecca98ab788ef5537efbfe831`.
- Mini bounded 0239 failure evidence SHA256:
  `2318e61866426ecd984b32d044eb92814acaa3607127f81f63c096ea8eca6c51`.
- Mini exact 0239 task log SHA256:
  `ddd1030c2917e364034f8d8a8394132ab1e4a7dc87142dbe6b779593cd6da8d3`.
- Next effective `view_target_system.cc` SHA256:
  `25468df139f1b454c375dc9265cded50ee2a2d67ac13287fdcd67fbb446551d4`.
- Mini metadata evidence SHA256:
  `32fa75be824b63bb1fe637c239ce905e807a25cecca98ab788ef5537efbfe831`.
- Mini exact task log SHA256:
  `73c7e4284acdcdef225aa3784ffc010e936ea48fa6112be00092b2269e3bbbf7`.
- Canonical 0236 SHA256:
  `4d0e201b03d2453d53c92d773f63a88d5ca531bf9ea44dc5640e84981c11fd62`.
