# FLR-0175 — rebase 0235 on the effective plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0174](FLR-0174-rebase-0234-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0175.md`

## Work unit

Rebase `0235-diag-isolate-native-fixture-setup-devtool.patch` on the exact
effective source after 0234. Use the fixed Mac Podman Devtool source, official
`update-recipe`, and the deterministic Mini recipe gate.

## Problem

Mini `do_patch` applies through 0234, then 0235 hunk 2 fails in
`plugins/filament_view/core/scene/serialization/scene_text_deserializer.cc`;
hunk 1 applies with offset 1. The patch context is stale against the current
effective source.

## Success criteria

- [x] Capture the exact effective 0235 target source and hash.
- [x] Keep one active Devtool recipe for the selected source path.
- [x] Import the effective source as the baseline through the source Git wrapper.
- [x] Commit only the intended 0235 source change through guarded `git add .`
  and staged-path validation.
- [x] Generate and register the official Devtool patch in the canonical layer.
- [x] Hand off one commit and prove Mini `do_patch` advances beyond 0235.

## Facts

- FLR-0174 regenerated 0234 and the deterministic gate proved 0234 applies.
- The next boundary is 0235 hunk 2 in `scene_text_deserializer.cc`.
- The exact next effective target SHA256 is
  `d0d1ae57235c3fdf3a5cf74094e9fe2d37d7a83a4b853c3863a59f9460ac3c3c`.
- The fixed Mac Devtool baseline commit is
  `6add4ef9c7a8e8a4ef647fa53e976e50d8e72fd3`; the guarded source change is
  commit `04e07ec6b13f9d1ea95e81b7d825c0d4c6f06241`.
- The old 0235 patch used `v*` method names, but the effective source uses
  `RunPostSetupLoad()` and non-`v` deserializer methods. The rebase follows the
  effective implementation boundary; the header declaration mismatch remains
  an independent compile-time issue to verify later.
- Compile, full image, QEMU, and 3D remain unstarted for this boundary.

## Inferences

- 0235 is a stale-context source rebase, not evidence against the
  deterministic recipe gate.
- The one-to-one Devtool registration and guarded source commit flow remain
  reusable prerequisites.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0235 has stale context | effective-source Devtool generation applies after 0234 | regenerated patch fails at the same context |
| H2: one source baseline is sufficient | one active component registration yields stable update-recipe output | duplicate or wrong-source registration remains |
| H3: fixture setup API remains compatible | do_patch advances beyond 0235 and compile is next | compile rejects the regenerated change |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase 0235 fixture setup isolation patch |
| Where | fixed Mac Devtool source and canonical layer |
| When | after 0234, before compile/image/QEMU |
| Who | source, Devtool, and Mini BitBake roles |
| How | effective source → baseline → source commit → update-recipe → recipe gate |

## PDCA

### Plan

1. Read only the 0235 task boundary and target source file.
2. Import the effective source into the fixed Devtool source and preserve both
   baseline and source-change commits.
3. Generate the official patch and validate it with the fixed Mini gate.

### Do

- Imported the exact effective `scene_text_deserializer.cc` into the fixed Mac
  Devtool source and committed the baseline through the source Git wrapper.
- Added the intended pure-fixture guard at the effective
  `RunPostSetupLoad()` boundary and committed it through the guarded source
  path.
- Ran official Devtool `component-add` and `update-recipe`; the generated
  patch was copied byte-identically to canonical 0235. Generated/canonical
  SHA256 is
  `30621f15c5441046e888532235e1456553ed421995d25bc4246ea9616ce81b99`.

### Check

- FLR-0174 gate: 0234 PASS, 0235 hunk 2 FAIL, hunk 1 applied with offset 1.
- Mac-side official rebase: PASS; one source commit, one generated patch,
  canonical registration PASS, baseline lock refreshed.
- Mini recipe gate is the remaining check: hand off the canonical commit and
  prove that 0235 applies.
- Mini recipe gate: preflight PASS, metadata PASS, 0235 PASS; `do_patch`
  advanced to 0236. Both 0236 hunks fail in `filament_view_plugin.cc`.

### Act

- Commit the canonical patch/lock checkpoint, hand off one bundle to the fixed
  receiver, and run the recipe-scoped Mini `do_patch` gate.

## UNKNOWN

- Whether 0236 and later patches apply is UNKNOWN and is split to FLR-0176.
- Runtime and 3D behavior are UNKNOWN and must not be inferred from patch
  application.

## Evidence

- Predecessor: `work/tickets/FLR-0174-rebase-0234-effective-plugin-source.md`.
- Exact failing task log:
  `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3181353`.
- Mini bounded failure evidence SHA256:
  `565fb9bbe4f3ee8aefa813eddbba67d0086c5663431667624255a1140e0c027f`.
- Effective target SHA256:
  `d0d1ae57235c3fdf3a5cf74094e9fe2d37d7a83a4b853c3863a59f9460ac3c3c`.
- Source baseline/change commits:
  `6add4ef9c7a8e8a4ef647fa53e976e50d8e72fd3` /
  `04e07ec6b13f9d1ea95e81b7d825c0d4c6f06241`.
- Canonical 0235 SHA256:
  `30621f15c5441046e888532235e1456553ed421995d25bc4246ea9616ce81b99`.
- Bundle SHA256: `20d0b33b8580e148321f5321cd78690e973080295a5e8866befa08f523aae568`.
- Mini receiver revision: `d4c8f4f46f399789fd1d9ad778d4da50fe12073c`.
- Mini metadata evidence SHA256:
  `32fa75be824b63bb1fe637c239ce905e807a25cecca98ab788ef5537efbfe831`.
- Mini bounded failure evidence SHA256:
  `5e97fed5001b38ae55421d20963eb108f950e26e03bff9aa760f1e77d3549e89`.
- Mini exact task log SHA256:
  `73c7e4284acdcdef225aa3784ffc010e936ea48fa6112be00092b2269e3bbbf7`.
- Next effective `filament_view_plugin.cc` SHA256:
  `f5e44d4c4b68a41349765c34733da6e61cf089d64eb32eef9d6a69d34c699142`.
