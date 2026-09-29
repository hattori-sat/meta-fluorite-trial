# FLR-0189 — reconcile stale 0235/0236 ECS APIs before compile

- Status: Done
- Priority: High
- Owner: Mac Devtool source + Yocto layer integration role
- Created: 2026-09-15
- Predecessor: [FLR-0188](FLR-0188-compile-and-validate-clean-3d-runtime.md)
- Working log: `work/logs/2026-09-15-flr0189.md`

## Work unit

Rebase the active 0235 and 0236 diagnostic/fix patches against the current
`fluorite-plugins` source and current ECS/SceneTextDeserializer APIs. Preserve
their intended behavior, keep them as separate official Devtool patches, and
prove Mini `flutter-auto:do_compile` before returning to runtime validation.

## Problem

FLR-0187 made the patch stack apply without fuzz, but the first compile fails
because active patches reintroduce an older API vocabulary. 0236 calls
`vInitSystems`, `GetStrand`, and `vRouteMessage`; current ECSManager exposes
`initialize`, `getStrand`, and `RouteMessage`. 0235 references `camera_`, which
is not a member of the current SceneTextDeserializer.

## Success criteria

- [x] Preserve the exact Mini compile failure and source locations.
- [x] Identify which patch introduced each stale API reference and compare at
  least two safe remediation paths.
- [x] Retire 0235 and 0236 from the active recipe because their state/API
  assumptions do not exist in the current source and their intended ordering
  is already represented by the current implementation.
- [x] Verify Mac `do_patch` and `do_compile` for the corrected stack.
- [ ] Bundle once and prove Mini clean `do_patch` and `do_compile` pass.

## Facts

- Receiver tip: `42689fdc5c66dbe537ae1cb2456fa0dd68c04c29`.
- Mini compile summary:
  `evidence/FLR-0188/compile-flutter-auto.summary`.
- Raw task log:
  `/mnt/yocto/flr0023-tmp-835a04e-selfinstall/work/corei7-64-agl-linux/flutter-auto/2.0/temp/log.do_compile.3267076`.
- 0235 adds `SetCameraFromDeserializedLoad` using undeclared `camera_` and
  calls `vRouteMessage` in `scene_text_deserializer.cc`.
- 0236 adds `vInitSystems`, `GetStrand`, and `vRouteMessage` in
  `filament_view_plugin.cc`.
- Current source declarations observed in the failed build are
  `ECSManager::initialize()`, `ECSManager::StartMainLoop()`,
  `ECSManager::RouteMessage()`, and `ECSManager::getStrand()`.
- Two remediation paths were compared: current-API rebase versus retirement.
  Retirement is smaller because 0235 references nonexistent `camera_`, while
  the current source already synchronously completes `initialize()` before
  registration continues and exposes the current routing methods.
- Removed only the active SRC_URI registrations for 0235 and 0236 from
  `flutter-auto_2.0.bbappend`; the historical patch files remain unchanged.
- Mac `flutter-auto:do_patch`, `do_configure`, and `do_compile` passed after
  the retirement.
- Bundle SHA256: `900600b84455ddaaf193ee8789706350b6ea411d095f8017db98668d5510e0d0`.
- Mini `flutter-auto:do_patch` and `do_compile` passed at receiver
  `44c88ec1fe69506f561ad09330da05d788eef187`.

## Inferences

- The first compile failure is deterministic and source-level; QEMU is not yet
  a valid diagnostic step.
- 0235 and 0236 must be re-evaluated separately because one modifies scene
  fixture state and the other modifies ECS initialization/routing.

## Hypotheses / UNKNOWN

| Hypothesis | Prediction | Falsifier |
| --- | --- | --- |
| H1: 0236 is a stale API rebase only | current APIs can preserve its deferred ECS ordering without new behavior | current API lacks an equivalent ordering seam |
| H2: 0235's pure-fixture branch is stale/obsolete | current deserializer state has no camera object and the branch must be retired or rewritten | current source history provides an equivalent camera object/API |
| H3: later patches depend on the old names | after 0235/0236 correction, another patch exposes the same API mismatch | Mini compile reaches the next source boundary |

## 4W1H (Why excluded)

| Dimension | Record |
| --- | --- |
| What | Remove compile-blocking stale API references |
| Where | `filament_view_plugin.cc` and `scene_text_deserializer.cc` |
| When | after clean 0232 patch application and before image/QEMU |
| Who | Mac Devtool source role, layer role, Mini compile-gate role |
| How | inspect current API → separate source commits → official patch regeneration → Mini compile |

## PDCA

### Plan

1. Inspect current source declarations, 0235/0236 history, and all active
   callers before editing.
2. Select the smallest behavior-preserving current-API rebase, or retire an
   obsolete diagnostic branch if its state no longer exists.
3. Generate both canonical patches through the persistent Devtool workflow.
4. Verify Mac and Mini patch/compile gates before any QEMU launch.

### Do

- Opened after FLR-0188 failed at compile with deterministic API errors.
- Confirmed the errors map directly to active 0235/0236 patch content.

### Check

- Source/API comparison and the two-path decision are PASS.
- Mac patch/configure/compile gates are PASS after retiring only 0235/0236
  registrations.
- Mini clean patch and compile gates are PASS; the obsolete API boundary is
  closed.

### Act

- Close FLR-0189 and return to FLR-0188 for image/QEMU evidence. If another
  stale patch appears, open a new patch-boundary ticket instead of expanding
  this scope.

## UNKNOWN

- Whether 0235 remains semantically required for the current source is UNKNOWN.
- Whether 0236 can preserve deferred ECS ordering with the current APIs is
  UNKNOWN.
- 3D pixels, light/material state, camera visibility, and QMP evidence remain
  UNKNOWN until compile and image build pass.
