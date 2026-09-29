# FLR-0180 — rebase QEMU quality patch 0228

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0179](FLR-0179-retire-obsolete-0239-patch.md)
- Working log: `work/logs/2026-09-15-flr0180.md`

## Work unit

Rebase the QEMU-only 0228 quality patch on the exact current
`view_target.cc`, using the fixed Mac Podman Devtool source Git commit and
official `update-recipe` generation. This ticket does not claim runtime or
3D behavior.

## Problem

After the deterministic clean gate skipped obsolete 0239, 0228 became the
first failing patch. Its single hunk fails in `view_target.cc` at line 195,
so its source context is stale against the current effective API.

## Success criteria

- [ ] Capture the exact current target source and hash.
- [ ] Preserve a Devtool baseline commit and one intended source-change commit.
- [ ] Generate 0228 through official Devtool `update-recipe`.
- [x] Register the generated patch byte-identically in the canonical layer
  after FLR-0181 fixes valid override registration validation.
- [x] Bundle once and prove the clean Mini gate advances beyond 0228.

## Facts

- FLR-0179 clean gate: 0239 skipped; 0228 hunk 1 failed.
- The failing file is `plugins/filament_view/core/scene/view_target.cc`.
- 0228 is appended only for QEMU machines.

## Inferences

- 0228 has stale context and needs a source rebase, not a runtime conclusion.
- The fixed Devtool source must be based on the current target file, not the
  old 0239 API history.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0228 context is stale only | effective-source Devtool regeneration applies after 0239 removal | another earlier active patch fails |
| H2: QEMU scope remains correct | non-QEMU builds do not receive 0228 | recipe metadata applies 0228 without a QEMU override |
| H3: official generation is reproducible | generated patch matches the canonical replacement byte-for-byte | repeated generation differs |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | rebase QEMU quality patch 0228 |
| Where | Mac Devtool source and `flutter-auto` recipe layer |
| When | after 0239 retirement, before compile/image/QEMU |
| Who | source, Devtool, and Mini BitBake roles |
| How | source identity → baseline → source commit → update-recipe → bundle → clean gate |

## PDCA

### Plan

1. Capture the current `view_target.cc` from the fixed clean Mini gate.
2. Edit only that file in the fixed Mac Devtool source and commit it through
   the guarded source wrapper.
3. Generate/register 0228, bundle it, and run the clean Mini gate.

### Do

- Captured the clean Mini `view_target.cc` and imported it into the fixed Mac
  Devtool source.
- Created baseline commit `b310de6` and source-change commit `5b34318` through
  the guarded source Git wrapper.
- Official Devtool generated the current-API patch in the fixed workspace
  append directory.
- The first helper run stopped before canonical replacement because 0228 is
  registered once for each of two valid QEMU machine overrides.
- After FLR-0181, the official helper generated and registered 0228
  byte-identically; canonical SHA256 is
  `1598ae0987ff16f423b3e1acb1ad85d0ceec263332eb69773e97cc8f8b210135`.

### Check

- Clean Mini gate before this rebase: 0228 hunk 1 failed in `view_target.cc`.
- Mac source status and one-file source commit: PASS.
- Official `update-recipe`: generated patch content changes
  `ChangeQualitySettings(...Ultra)` to `...Lowest` at current source line 277.
- Canonical patch replacement and two machine-specific registrations: PASS.
- Mini gate after this checkpoint: 0228 PASS; next first failure is
  `0001-diag-trace-effective-ViewTarget-frame-boundary.patch`.
- Summary SHA256:
  `06786363ce6fb7e2bc53537e8e478e63ed0604c6adc0f72e225cbf6802e622fc`.
- Bounded failure SHA256:
  `37adaa535c2e6c9578b679ab7272eadc3b5c781e76d4a9b93fc65d36c64fa1e2`.
- Mini task log SHA256:
  `28523ae6ffec5be43ada48f7c6fd967e5a3571b48edcbca9c1674e430c1e35dd`.

### Act

- FLR-0182 owns the next first failing patch. Compile/runtime claims remain
  out of scope until the full patch stack passes.

## UNKNOWN

- Whether 0228 is the only stale patch boundary is UNKNOWN.
- Compile, runtime, QEMU, and 3D behavior are outside this ticket.

## Evidence

- Predecessor summary SHA256:
  `bbeb81c3c191a380825410af66cebb848b7046b29707991489a5b140fd71caee`.
- Predecessor bounded failure SHA256:
  `67ea2f198c83cc413ea9564265fbbf63da9f805203ee19c96a8faf3ba6a03d43`.
- Devtool baseline commit: `b310de60fe209d222416b3227ab9cf3672930d06`.
- Devtool source commit: `5b34318b08bfd59c1e94b438a2e3b2203bad4f91`.
- Official rebase result: generated patch and canonical patch are
  byte-identical; previous canonical SHA256 was
  `198c5eeb65e1d8b21fa4503511ff4a3c0beddf086f674c9115965c884f8c4f4e`.
