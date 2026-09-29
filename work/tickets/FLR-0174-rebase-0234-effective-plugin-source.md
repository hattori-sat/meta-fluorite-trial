# FLR-0174 — rebase 0234 on the effective plugin source

- Status: Done
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0173](FLR-0173-rebase-0233-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0174.md`

## Work unit

Rebase `0234-diag-add-native-minimal-geometry-control-devtool.patch` on the
exact effective source after 0233. Use the fixed Mac Podman Devtool source,
official `update-recipe`, and the deterministic Mini recipe gate.

## Problem

Mini `do_patch` applies through 0233, then 0234 fails at hunks 1 and 2 in
`plugins/filament_view/core/scene/view_target.cc`; hunks 3 and 4 apply with
offset/fuzz. The patch context is stale against the current effective source.

## Success criteria

- [x] Capture the exact effective 0234 target source and hash.
- [x] Keep one active Devtool recipe for the selected source path.
- [x] Import the effective source as the baseline through the source Git wrapper.
- [x] Commit only the intended 0234 source change through guarded `git add .`
  and staged-path validation.
- [ ] Generate and register the official Devtool patch in the canonical layer.
- [x] Hand off one commit and prove Mini `do_patch` advances beyond 0234.

## Facts

- FLR-0173 regenerated 0233 and the deterministic gate proved 0233 applies.
- The next boundary is 0234 hunks 1 and 2 in `view_target.cc`.
- The exact next effective target SHA256 is
  `83ecb458c9a4bfa7502b18ec8b4ef6dcc781cb92c4ae687ba30be499dc3e87a3`.
- The fixed Mac Devtool baseline commit is
  `1998214348aec717cc056b43bdabb530d3c856cd`; the guarded source change is
  commit `957a7b9230c662577f38775d8c86af89628aad5c`.
- Compile, full image, QEMU, and 3D remain unstarted for this boundary.

## Inferences

- 0234 is a stale-context source rebase, not evidence against the
  deterministic recipe gate.
- The one-to-one Devtool registration and guarded source commit flow remain
  reusable prerequisites.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0234 has stale context | effective-source Devtool generation applies after 0233 | regenerated patch fails at the same context |
| H2: one source baseline is sufficient | one active component registration yields stable update-recipe output | duplicate or wrong-source registration remains |
| H3: native minimal geometry API remains compatible | do_patch advances beyond 0234 and compile is next | compile rejects the regenerated change |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase 0234 native minimal geometry control patch |
| Where | fixed Mac Devtool source and canonical layer |
| When | after 0233, before compile/image/QEMU |
| Who | source, Devtool, and Mini BitBake roles |
| How | effective source → baseline → source commit → update-recipe → recipe gate |

## PDCA

### Plan

1. Read only the 0234 task boundary and target source file.
2. Import the effective source into the fixed Devtool source and preserve both
   baseline and source-change commits.
3. Generate the official patch and validate it with the fixed Mini gate.

### Do

- Imported the exact effective `view_target.cc` into the fixed Mac Devtool
  source and committed the baseline through the source Git wrapper.
- Applied only the intended 143-line `view_target.cc` change through the
  guarded source commit path.
- Ran official Devtool `component-add` and `update-recipe`; the generated
  `0001-diag-add-native-minimal-geometry-control.patch` was copied
  byte-identically to canonical 0234. Generated/canonical SHA256 is
  `1520975ac3ead6b06d2d31e8a477400c9d5d98efbeb371dba751e40e662d8f5f`.

### Check

- FLR-0173 gate: 0233 PASS, 0234 hunks 1/2 FAIL, hunks 3/4 applied with
  offset/fuzz.
- Mac-side official rebase: PASS; one source commit, one generated patch,
  canonical registration PASS, baseline lock refreshed.
- Mini recipe gate is the remaining check: hand off the canonical commit and
  prove that 0234 applies.
- Mini recipe gate: preflight PASS, metadata PASS, 0234 PASS; `do_patch`
  advanced to the next boundary, 0235. The first failing patch is
  `0235-diag-isolate-native-fixture-setup-devtool.patch`; hunk 2 failed in
  `scene_text_deserializer.cc`, while hunk 1 applied with offset 1.

### Act

- Commit the canonical patch/lock checkpoint, hand off one bundle to the fixed
  receiver, and run the recipe-scoped Mini `do_patch` gate.

## UNKNOWN

- Whether 0235 and later patches apply is UNKNOWN and is split to FLR-0175.
- Runtime and 3D behavior are UNKNOWN and must not be inferred from patch
  application.

## Evidence

- Predecessor: `work/tickets/FLR-0173-rebase-0233-effective-plugin-source.md`.
- Exact failing task log:
  `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3177713`.
- Mini bounded failure evidence SHA256:
  `87299d20fac4acfdf7590f6ddcc5fbbd12505d3770d602d50ab2bb6ed6a473df`.
- Effective target SHA256:
  `83ecb458c9a4bfa7502b18ec8b4ef6dcc781cb92c4ae687ba30be499dc3e87a3`.
- Source baseline/change commits:
  `1998214348aec717cc056b43bdabb530d3c856cd` /
  `957a7b9230c662577f38775d8c86af89628aad5c`.
- Canonical 0234 SHA256:
  `1520975ac3ead6b06d2d31e8a477400c9d5d98efbeb371dba751e40e662d8f5f`.
- Bundle SHA256: `85a7a08dcbf121dd049e86a770359ce1f8cd144bd8941f09864f857f0ff7321a`.
- Mini receiver revision: `63bbf780add972b3d9142c03c8df5675cc931db6`.
- Mini metadata evidence SHA256:
  `32fa75be824b63bb1fe637c239ce905e807a25cecca98ab788ef5537efbfe831`.
- Mini bounded failure evidence SHA256:
  `565fb9bbe4f3ee8aefa813eddbba67d0086c5663431667624255a1140e0c027f`.
- Mini exact task log SHA256:
  `ec0e2650e387f398036d832a452cdf3a74a9e45fc488802fef02e4ca6bf6cfcf`.
- Next effective `scene_text_deserializer.cc` SHA256:
  `d0d1ae57235c3fdf3a5cf74094e9fe2d37d7a83a4b853c3863a59f9460ac3c3c`.
