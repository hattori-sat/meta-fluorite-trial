# FLR-0173 — rebase 0233 on the effective plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0172](FLR-0172-rebase-0231-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0173.md`

## Work unit

Rebase `0233-diag-add-native-control-fields-devtool.patch` on the exact
effective source after 0231. Use the fixed Mac Podman Devtool source, official
`update-recipe`, and the deterministic Mini recipe gate.

## Problem

Mini `do_patch` applies 0231, then 0233 fails at hunk 2 in
`plugins/filament_view/core/scene/view_target.h`; hunks 1 and 3 apply with
offset/fuzz. The patch context is stale against the current effective source.

## Success criteria

- [x] Capture the exact effective 0233 target source and hash.
- [x] Keep one active Devtool recipe for the selected source path.
- [x] Import the effective source as the baseline through the source Git wrapper.
- [x] Commit only the intended 0233 source change through guarded `git add .`
  and staged-path validation.
- [ ] Generate and register the official Devtool patch in the canonical layer.
- [x] Hand off one commit and prove Mini `do_patch` advances beyond 0233.

## Facts

- FLR-0172 regenerated 0231 and the deterministic gate proved 0231 applies.
- The next boundary is 0233 hunk 2 in `view_target.h`.
- Compile, full image, QEMU, and 3D remain unstarted for this boundary.
- The exact Mini effective target was `.../flutter-auto/2.0/git/ivi-homescreen-plugins/plugins/filament_view/core/scene/view_target.h` with SHA256 `90b7f10adec34dd36cfc9700a6b16e99b014f2bc5703650bb4a15deb9d900a87`.
- The fixed Mac Devtool source baseline is commit
  `99eaacbb0bc861cbb9f28322d9b59a97ebe41604`; the guarded source change is
  commit `58bbff3dfc3561e8779af21976571b1b289bf922`.

## Inferences

- 0233 is a stale-context source rebase, not a failure of the new gate.
- The one-to-one Devtool registration and guarded source commit flow are now
  reusable prerequisites.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0233 has stale context | effective-source Devtool generation applies after 0231 | regenerated patch fails at the same context |
| H2: one source baseline is sufficient | one active component registration yields stable update-recipe output | duplicate or wrong-source registration remains |
| H3: current control-field API remains compatible | do_patch advances beyond 0233 and compile is next | compile rejects the regenerated change |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase 0233 native control fields patch |
| Where | fixed Mac Devtool source and canonical layer |
| When | after 0231, before compile/image/QEMU |
| Who | source, Devtool, and Mini BitBake roles |
| How | effective source → baseline → source commit → update-recipe → recipe gate |

## PDCA

### Plan

1. Read only the 0233 task boundary and target source file.
2. Import the effective source into the fixed Devtool source and preserve both
   baseline and source-change commits.
3. Generate the official patch and validate it with the fixed Mini gate.

### Do

- Imported the exact effective `view_target.h` into the fixed Mac Devtool
  source and committed the baseline through `source-git-commit-baseline`.
- Applied only the intended 17-line header change through `source-git-commit`,
  which enforced one changed path, `git add .`, and staged-path validation.
- Ran official Devtool `component-add` and `update-recipe`; the generated
  `0001-diag-add-native-control-fields.patch` was copied byte-identically to
  canonical 0233. Generated/canonical SHA256 is
  `b3a7e5bd05276b3f1893d110e19cfd6fb42b05b6e385b895038f5b776c9d7ee5`.

### Check

- Mac-side official rebase: PASS; one source commit, one generated patch,
  canonical registration PASS, baseline lock refreshed.
- Mini recipe gate: preflight PASS, metadata PASS, 0233 PASS; `do_patch`
  advanced to the next boundary, 0234. The first failing patch is
  `0234-diag-add-native-minimal-geometry-control-devtool.patch`; its hunk 1/2
  failed in `view_target.cc`, while hunk 3/4 applied with offset/fuzz.

### Act

- Commit the canonical patch/lock checkpoint, hand off one bundle to the fixed
  receiver, and run the recipe-scoped Mini `do_patch` gate.

## UNKNOWN

- Whether 0234 and later patches apply is UNKNOWN and is split to FLR-0174.
- Runtime and 3D behavior are UNKNOWN and must not be inferred from patch
  application.

## Evidence

- Predecessor gate summary: fixed receiver evidence role for FLR-0172.
- Exact task log: `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3173793`.
- Mac Devtool source baseline: `99eaacbb0bc861cbb9f28322d9b59a97ebe41604`.
- Mac Devtool source change: `58bbff3dfc3561e8779af21976571b1b289bf922`.
- Generated/canonical patch SHA256:
  `b3a7e5bd05276b3f1893d110e19cfd6fb42b05b6e385b895038f5b776c9d7ee5`.
- Bundle SHA256: `9a255202430486ce85318eb396bc6814a5d975c86e083f73450172b154bd901a`.
- Mini receiver revision: `be6ab094c6e66350103dc96961c237561c646757`.
- Mini metadata evidence SHA256:
  `32fa75be824b63bb1fe637c239ce905e807a25cecca98ab788ef5537efbfe831`.
- Mini bounded failure evidence SHA256:
  `87299d20fac4acfdf7590f6ddcc5fbbd12505d3770d602d50ab2bb6ed6a473df`.
- Mini exact task log SHA256:
  `c0593bad9b9d78f3d9b892c89387c30048c0fad36601c21ae7ccef3969216854`.
- Next effective `view_target.cc` SHA256:
  `83ecb458c9a4bfa7502b18ec8b4ef6dcc781cb92c4ae687ba30be499dc3e87a3`.
