# FLR-0186 — rebase 0227 on the current plugin source

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0185](FLR-0185-current-fixture-camera-lookat.md)
- Working log: `work/logs/2026-09-15-flr0186.md`

## Work unit

Regenerate the existing 0227 async model-source lifetime patch against the
current effective `fluorite-plugins` source so Mini `do_patch` has no fuzz.
Do not alter the camera patch, fixture behavior, compile, or runtime in this
ticket.

## Problem

The fixed Mini recipe gate applies the new 0251 camera patch, then fails the
QA task because 0227 applies with fuzz. The patch is therefore semantically
accepted by GNU patch but is not deterministic under Yocto's `patch-fuzz`
QA policy.

## Success criteria

- [x] Record the exact Mini failure boundary and receiver tip.
- [x] Rebase 0227 from the current effective source through Mac Devtool.
- [x] Generate the patch with official `update-recipe --mode patch --append
  --no-remove` and copy it byte-identically to the canonical layer file.
- [x] Pass Mac recipe `do_patch` and repository verification.
- [x] Bundle once and prove Mini clean `flutter-auto:do_patch` advances beyond
  0227 without fuzz.

## Facts

- Mini receiver tip: `013d02b96623f059ad05eab32f5e8299be2cc715`.
- Mini bundle SHA256: `9c739ca756103662030732da9ad78838850056827bbd42b3e708534af59d99ae`.
- Mini gate: `evidence/FLR-0186/patch-gate-flutter-auto.summary`.
- 0251 applied; the first failing patch is
  `0227-defer-async-model-source-release-current-plugin-devtool.patch`.
- The bounded failure reports fuzz at `model_system.cc` lines 429 and 607.
- The canonical 0227 patch currently carries source commit
  `b90e6ac831549a6f119968494e8bc53a776552d2`.
- The first unstacked rebase used baseline
  `e73c859fa60f1dd129ec9920c14b593fc660b468` and source commit
  `de485e4e562186cbc040d156a8bf51745de75b8a`; Mini still reported fuzz
  because earlier active patches were absent from that baseline.
- The correct Mini-effective pre-0227 baseline is
  `2163242e9973336153871ed63b34bb5ed8282145`, the parent of the retained
  effective-source import `32f4fab...`.
- The corrected Devtool source commit is
  `41e1026d51bd2dad868ec4bf696d4f38d97a5f79`.
- The generated patch is
  `0001-fix-defer-async-model-source-release-on-effective-ba.patch`; canonical
  SHA256 is
  `3353aba2b55be91572656ecbe8ffa1c9583e7a612300645216b106553a143033`.
- Mini clean-gate preflight, metadata, and recipe-workdir reset passed. The
  bounded task log shows 0227 applying before 0232; 0227 has no fuzz and 0232
  reports hunk 1 and hunk 2 with fuzz 2, so 0232 is the next deterministic
  rebase boundary.

## Inferences

- The first rebase baseline was not the Mini-effective source: active 0174 and
  0185 context was absent. The retained Devtool history provides the correct
  pre-0227 parent.
- Because Yocto rejects fuzz, a successful semantic application is not enough;
  the regenerated patch must apply with zero fuzz on the clean Mini workdir.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0227 is valid but stale | official regeneration produces a zero-fuzz patch and Mini advances | regenerated patch still fuzzes or fails at the same hunk |
| H2: source behavior changed materially | current-source diff requires review beyond context refresh | generated patch changes only context and preserves the two lifetime changes |
| H3: another patch becomes the next boundary | after 0227, Mini reports a later patch | Mini still stops at 0227 after clean handoff |

## 4W1H (Why excluded)

| Dimension | Record |
| --- | --- |
| What | Remove 0227 patch fuzz through current-source regeneration |
| Where | `fluorite-plugins/plugins/filament_view/core/systems/derived/model_system.cc` |
| When | After 0251 applies and before compile/runtime |
| Who | Devtool source role, Yocto layer role, Mini patch-gate role |
| How | source baseline → one source commit → official update-recipe → bundle → clean gate |

## PDCA

### Plan

1. Inspect the current source and 0227's intended behavior.
2. Compare at least two explanations for fuzz and select the smallest
   current-source rebase.
3. Use the existing persistent Mac Devtool container and source Git.
4. Commit the canonical patch and evidence, then hand off one bundle.

### Do

- Ticket opened from the FLR-0185 patch-stack boundary.
- Created `devtool-FLR-0186-source` in the persistent Mac Podman Devtool
  container and retained the first attempt under a separate branch.
- The first unstacked rebase reproduced Mini fuzz and was not promoted.
- Read the Devtool history, selected the Mini-effective pre-0227 parent, and
  applied the current-source equivalent of 0227 only to
  `model_system.cc`: delayed `releaseSourceData()` until async scene
  insertion and removed the earlier immediate release.
- Committed only that source file as
  `41e1026d51bd2dad868ec4bf696d4f38d97a5f79`.
- Official `update-recipe --mode patch --append --no-remove` generated the
  replacement patch. Generated and canonical files compare byte-identically.
- Mac recipe-level `flutter-auto:do_patch` passed.

### Check

- Mac patch application is PASS.
- Mini clean-gate preflight, metadata, and workdir reset are PASS.
- Mini applies 0251 and 0227 without fuzz, then fails the QA check at 0232
  because both reported hunks use fuzz 2. The raw task log is retained under
  the Mini TMPDIR and the bounded summary is recorded under
  `evidence/FLR-0186/patch-gate-flutter-auto.summary`.

### Act

- Open FLR-0187 for the 0232 current-source rebase. Compile/runtime/3D remain
  out of scope until the complete patch stack is clean.

## UNKNOWN

- Whether 0227's source lifetime behavior is still needed by the current
  plugin source is UNKNOWN until the current call sites and patch result are
  compared.
- Compile/runtime/3D evidence is explicitly out of scope until the patch stack
  is clean.
