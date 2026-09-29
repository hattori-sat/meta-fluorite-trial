# FLR-0185 — restore current fixture camera projection and lookAt

- Status: Done (patch-stack boundary)
- Priority: High
- Owner: Mac Devtool source + Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0184](FLR-0184-rebase-native-fixture-local-camera.md)
- Working log: `work/logs/2026-09-15-flr0185.md`

## Work unit

Implement the intent of 0242 using the current direct Filament camera API:
when the pure minimal fixture is enabled, apply the Dart default perspective
projection and set the ViewTarget camera to `eye=(0,0,5)`,
`target=(0,0,0)`, `up=(0,1,0)` through the direct `filament::Camera` API.

## Problem

The historical 0251 patch calls the removed camera-manager API. The current
source creates and owns a direct `filament::Camera`, so the old patch cannot
apply and must be mapped to `_initCamera()`. The pure fixture has no normal
camera payload at initialization, so its projection must be initialized before
the guarded lookAt.

## Success criteria

- [x] Current source/API mapping is recorded.
- [x] One guarded Devtool source commit changes only `view_target.cc`.
- [x] Official Devtool generates and registers the current 0251 replacement.
- [x] Mac recipe-level `do_patch` passes with the canonical patch stack.
- [x] Bundle once and prove clean Mini do_patch applies 0251 and advances to
  the next patch boundary.

## Facts

- 0241 was retired because its camera-manager method no longer exists.
- Current Filament exposes `Camera::lookAt(double3,double3,double3)` and
  `Camera::setProjection(...)`.
- The Dart default projection is 60 degrees vertical FOV, near 0.05, far
  1000; the fixture-only source gate applies the same values.
- Devtool source commit:
  `e73c859fa60f1dd129ec9920c14b593fc660b468`.
- Official generated patch:
  `0002-fix-restore-pure-fixture-camera-projection.patch`.
- Canonical replacement SHA256:
  `46bd8586884ebea9f20300d9b25d18b4e69292ab698a3c8347cf6af5035d07a5`.

## Inferences

- This is the current-API equivalent of the historical local-fixture camera
  diagnostic and directly advances the 3D fixture objective.

## Hypotheses

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: fixture projection plus direct lookAt restores camera framing | 0251 applies and later runtime can show fixture geometry | patch applies but fixture pixels remain absent |
| H2: scope is fixture-only | normal scenes are unchanged when env gates are absent | non-fixture camera changes |

## 4W1H

| Dimension | Record |
| --- | --- |
| What | current fixture camera lookAt |
| Where | ViewTarget `_initCamera()` |
| When | pure minimal fixture initialization |
| Who | Mac Devtool source + Mini build roles |
| How | guarded source commit → official patch → bundle → clean gate |

## PDCA

### Plan

- Validate the generated 0242 through Mini clean do_patch, then compile and
  runtime-test the fixture if the full patch stack permits.

### Do

- Added the fixture-gated default perspective projection and direct
  `camera_->lookAt` mapping in the fixed Mac Devtool source.
- Committed only `view_target.cc` in Devtool source commit
  `e73c859fa60f1dd129ec9920c14b593fc660b468`.
- Generated `0002-fix-restore-pure-fixture-camera-projection.patch` using the
  standard `update-recipe --mode patch --append --no-remove` path and copied it
  byte-identically to the canonical 0251 filename; generated/canonical SHA is
  `46bd8586884ebea9f20300d9b25d18b4e69292ab698a3c8347cf6af5035d07a5`.
- The first regeneration attempt remained running in the existing BitBake
  server; after completion it produced the expected current-source patch.

### Check

- Mac `do_patch` passed after canonical replacement.
- `make verify` passed all repository gates, including the Devtool component
  rebase contract and Mini recipe-gate contract. The bounded output is in the
  untracked local evidence log `/tmp/fluorite-verify-FLR0185.log`; it is not a
  repository artifact.
- Mini fixed-receiver gate reached the canonical `51100aa...` tip, reset the
  recipe workdir, and applied 0251. It then failed closed on QA fuzz in the
  older 0227 patch. This proves 0251 is no longer the first boundary; the next
  independent work unit is [FLR-0186](FLR-0186-rebase-0227-current-plugin-source.md).

### Act

- Keep the camera patch unchanged and hand the 0227 fuzz boundary to FLR-0186.
- Do not claim compile, runtime, or 3D pixels from this patch-stack gate.

## UNKNOWN

- Whether the full patch stack applies beyond 0242 is UNKNOWN.
- Runtime QMP pixels and actual 3D visibility are UNKNOWN.

## Evidence

- Devtool baseline: `96e91a5e2591651568b9c9f807245c6e9eca0215`.
- Devtool source: `e73c859fa60f1dd129ec9920c14b593fc660b468`.
- Mini evidence: `evidence/FLR-0185/patch-gate-flutter-auto.summary` records
  receiver `51100aa...`, workdir reset PASS, and the next failing patch
  `0227-defer-async-model-source-release-current-plugin-devtool.patch`.
