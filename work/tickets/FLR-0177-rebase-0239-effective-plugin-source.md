# FLR-0177 — rebase 0239 on the effective plugin source

- Status: Waiting
- Priority: High
- Owner: Yocto flutter-auto plugin baseline + Mac Devtool rebase role
- Created: 2026-09-15
- Predecessor: [FLR-0176](FLR-0176-rebase-0236-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0177.md`

## Work unit

Rebase `0239-fix-apply-deserialized-camera-over-default-primary-devtool.patch`
on the exact effective source after 0238. Use the fixed Mac Podman Devtool
source, official `update-recipe`, and the deterministic Mini recipe gate.

## Problem

Mini `do_patch` applies through 0238, then both 0239 hunks fail in
`plugins/filament_view/core/systems/derived/view_target_system.cc`. The Mini
`S` tree has a different API shape from the 0239 predecessor retained in the
Mac Devtool history. This is now split to [FLR-0178](FLR-0178-deterministic-mini-recipe-workdir.md)
as a workdir-provenance gate; do not regenerate 0239 against the mismatched
tree.

## Success criteria

- [x] Capture the exact effective 0239 target source and hash.
- [ ] Keep one active Devtool recipe for the selected source path.
- [ ] Import the effective source as the baseline through the source Git wrapper
  after FLR-0178 establishes a clean predecessor.
- [ ] Commit only the intended 0239 source change through guarded `git add .`
  and staged-path validation.
- [ ] Generate and register the official Devtool patch in the canonical layer.
- [ ] Hand off one commit and prove Mini `do_patch` advances beyond 0239.

## Facts

- FLR-0176 regenerated 0236 and the deterministic gate advanced through 0238.
- The next boundary is 0239 hunks 1 and 2 in `view_target_system.cc`.
- The exact next effective target SHA256 is
  `25468df139f1b454c375dc9265cded50ee2a2d67ac13287fdcd67fbb446551d4`.
- Compile, full image, QEMU, and 3D remain unstarted for this boundary.

## Inferences

- 0239 is a stale-context source rebase, not evidence against the
  deterministic recipe gate.
- The one-to-one Devtool registration and guarded source commit flow remain
  reusable prerequisites.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0239 has stale context | effective-source Devtool generation applies after 0238 | regenerated patch fails at the same context |
| H2: one source baseline is sufficient | one active component registration yields stable update-recipe output | duplicate or wrong-source registration remains |
| H3: deserialized camera priority API remains compatible | do_patch advances beyond 0239 and compile is next | compile rejects the regenerated change |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase 0239 deserialized camera priority patch |
| Where | fixed Mac Devtool source and canonical layer |
| When | after 0238, before compile/image/QEMU |
| Who | source, Devtool, and Mini BitBake roles |
| How | effective source → baseline → source commit → update-recipe → recipe gate |

## PDCA

### Plan

1. Read only the 0239 task boundary and target source file.
2. Import the effective source into the fixed Devtool source and preserve both
   baseline and source-change commits.
3. Generate the official patch and validate it with the fixed Mini gate.

### Do

- Captured the Mini `S` target hash and bounded 0239 failure evidence.
- Compared the target API shape with the Mac Devtool predecessor history.
- Stopped source editing when the Mini tree proved not to be the 0239
  predecessor; no mismatched source was committed.

### Check

- FLR-0176 gate: 0236/0237/0238 PASS; 0239 hunks 1/2 FAIL.
- Mini target SHA256 is
  `25468df139f1b454c375dc9265cded50ee2a2d67ac13287fdcd67fbb446551d4`.
- The effective Mini target has `onSystemInit` and no
  `vSetCameraFromSerializedData` definition, while 0239 expects the older
  `vOnInitSystem`/`vSetCameraFromSerializedData` shape.

### Act

- FLR-0178 owns the recipe-scoped workdir reset. Resume this ticket only after
  clean→unpack→patch produces the actual 0239 predecessor source.

## UNKNOWN

- Whether the regenerated 0239 patch applies on a clean Mini workdir is
  UNKNOWN until FLR-0178 completes.
- Runtime and 3D behavior are UNKNOWN and must not be inferred from patch
  application.

## Evidence

- Predecessor: `work/tickets/FLR-0176-rebase-0236-effective-plugin-source.md`.
- Exact failing task log:
  `$BUILD_TMPDIR/work/.../flutter-auto/2.0/temp/log.do_patch.3188833`.
- Mini bounded failure evidence SHA256:
  `2318e61866426ecd984b32d044eb92814acaa3607127f81f63c096ea8eca6c51`.
