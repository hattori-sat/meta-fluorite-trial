# FLR-0182 — rebase effective ViewTarget frame boundary patch

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0180](FLR-0180-rebase-0228-effective-plugin-source.md)
- Working log: `work/logs/2026-09-15-flr0182.md`

## Work unit

Rebase `0001-diag-trace-effective-ViewTarget-frame-boundary.patch` on the
exact current `view_target.cc` after the clean Mini gate advanced through
0228. Use the fixed Mac Podman Devtool source Git and official
`update-recipe` flow.

## Problem

The patch stack now fails at three hunks in `view_target.cc` at lines 492,
523, and 552. Its context is stale against the current effective source.

## Success criteria

- [ ] Capture the exact current target source and hash.
- [ ] Preserve a Devtool baseline commit and one intended source-change commit.
- [ ] Generate the patch through official Devtool `update-recipe`.
- [ ] Register it byte-identically in the canonical layer.
- [x] Bundle once and prove the clean Mini gate advances beyond this patch.

## Facts

- FLR-0180 clean gate passed 0228.
- The next failing patch is `0001-diag-trace-effective-ViewTarget-frame-boundary.patch`.
- All three failed hunks target `plugins/filament_view/core/scene/view_target.cc`.
- The historical patch lived below `files/flutter-auto/`; the fixed rebase
  helper requires canonical patches below `files/`, so the regenerated patch
  is now stored at `files/0001-diag-trace-effective-ViewTarget-frame-boundary.patch`.

## Inferences

- This is a source-context rebase boundary, not evidence about runtime or 3D.
- The current source must be captured from the clean Mini workdir before
  editing the fixed Mac Devtool source.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: only patch context is stale | current-source Devtool generation applies | an earlier patch fails after clean reset |
| H2: one source file is sufficient | guarded source commit contains only `view_target.cc` | another path changes |
| H3: official generation is reproducible | generated/canonical patch hashes match | repeated official generation differs |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase effective ViewTarget frame-boundary diagnostics |
| Where | fixed Mac Devtool source and canonical layer |
| When | after 0228, before compile/image/QEMU |
| Who | source, Devtool, and Mini BitBake roles |
| How | source identity → baseline → source commit → update-recipe → bundle → clean gate |

## PDCA

### Plan

1. Capture only the current target file from the clean Mini source.
2. Map each old diagnostic hunk to current functions and edit one source file.
3. Generate/register through official Devtool and run one clean Mini gate.

### Do

- Captured the current target source and committed baseline `b310de6`.
- Added the current `DrawFrame` begin/render/end and begin-false diagnostics
  as source commit `96e91a5` through the guarded Devtool source wrapper.
- Generated the patch through official `update-recipe` and registered it at
  the helper-supported `files/` path; the old nested duplicate was removed.

### Check

- Initial helper path check failed closed because the canonical path was under
  `files/flutter-auto/`; no patch was installed by that failed attempt.
- Official rebase then passed with generated source `96e91a5` and canonical
  SHA256 `de9e7858197c4bc9e692a358f137858d0895e959543a1f0f7566b61f4b8531db`.
- The source change touched only `view_target.cc` and logs the current
  `beginFrame → render → endFrame` boundary.
- Mini clean gate: this patch passed; the next first failure is
  `0240-diag-flush-wayland-child-surface-after-present-devtool.patch`.
- Summary SHA256:
  `df202bad22f213aa4fab110e0e9326c3673fa1df4b05254eb7107d8308e68304`.
- Bounded failure SHA256:
  `396d3ba3a97b20b6a00981152f00e5a6f28f4f3d140721f51b177efe5195881f`.
- Mini task log SHA256:
  `f171f6f8c17d97c10fbda73bd58f8306ab678ee5c0df665019a339ee4e450e0f`.

### Act

- FLR-0183 owns the next first failing patch; compile/runtime claims remain
  out of scope.

## UNKNOWN

- The current source mapping for all three hunks is UNKNOWN until inspected.
- Compile, runtime, QEMU, and 3D behavior are outside this ticket.

## Evidence

- Predecessor summary SHA256:
  `06786363ce6fb7e2bc53537e8e478e63ed0604c6adc0f72e225cbf6802e622fc`.
- Predecessor bounded failure SHA256:
  `37adaa535c2e6c9578b679ab7272eadc3b5c781e76d4a9b93fc65d36c64fa1e2`.
- Devtool baseline commit: `b310de60fe209d222416b3227ab9cf3672930d06`.
- Devtool source commit: `96e91a5e2591651568b9c9f807245c6e9eca0215`.
- Canonical patch SHA256:
  `de9e7858197c4bc9e692a358f137858d0895e959543a1f0f7566b61f4b8531db`.
