# FLR-0247 — trace Planetarium readiness callback reachability

- Status: Done
- Priority: High
- Owner: NativeReadiness callback and Planetarium activation boundary
- Created: 2026-09-21
- Predecessor: FLR-0246

## Objective

Determine why a directly mounted `PlanetariumSceneView` renders alongside the
native fixture but does not emit its readiness-gated `onCreate` marker. Add only
bounded diagnostic markers around the existing `NativeReadiness` polling and
callback dispatch, then prove whether the Planetarium camera/lifecycle path is
reachable without reintroducing a `ValueListenableBuilder` rebuild.

## Facts

- FLR-0245 proves removing `ValueListenableBuilder` preserves HUD and native 3D.
- FLR-0246 proves direct `PlanetariumSceneView` mounting also preserves both
  pixel regions.
- FLR-0246 has 21 native shape-ready markers but zero
  `FLR0241_PLANETARIUM_LIFECYCLE_INERT onCreate` markers.
- `StatefulSceneViewState.initState` registers `onCreate` through
  `NativeReadiness.addCallback`; that callback dispatches only after
  `isNativeReady()` returns true.
- Static inspection found matching Dart/native channel and method names:
  `plugin.filament_view.readiness_checker` / `isReady`.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | readiness method-channel never returns true | polling-start/attempt markers continue without callback dispatch | Logging every poll would be too noisy; use bounded counters |
| 2 | callback dispatch occurs but Planetarium marker is masked/late | readiness dispatch and onCreate markers appear after startup | Need to preserve one-run evidence before teardown |
| 3 | direct widget state is not mounted as expected | initState registration marker is absent | Flutter build path may differ from static source assumption |

## Scope and invariants

- Add bounded markers only at polling start, first-ready/timeout, callback
  dispatch, and Planetarium lifecycle entry.
- Do not change camera, light, material, native shapes, parent Stack, Builder
  structure, QMP coordinates, or ROI thresholds.
- Use the fixed Mac Devtool history and official generated patch flow.
- Run the same Mini gates and one QMP session; save logs before teardown.

## Success criteria

- [x] Static inspection identifies the smallest readiness-trace instrumentation.
- [x] Official source commit, generated patch, canonical commit, bundle, and Mini
  gates are recorded.
- [x] Runtime bounded markers distinguish registration, readiness, dispatch, and
  `PlanetariumSceneView.onCreate`.
- [x] HUD/native pixel results remain comparable to FLR-0246, and cleanup is zero.
- [x] The next ticket is selected from evidence; no logging-only patch becomes a
  production fix.

## Evidence

- Predecessor: [FLR-0246](FLR-0246-mount-planetarium-directly-without-builder.md)
- Working log: [2026-09-21-flr0247.md](../logs/2026-09-21-flr0247.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0247/`
- Source commit: `cec84c1435e6c964f550bd1322bb07e6c4b35acd`.
- Official generated patch:
  `0079-flr0247-trace-planetarium-readiness-callback-devtool.patch`.
- Patch SHA-256: `da0ad3cbe9999712250ca5baf8dfb40a90d3cb9f98725871aecc1d2e32c0d444`.
- Canonical layer commit: `eb6070de39e1db36483a2bc61bcbdc83134cba3a`.
- Bundle SHA-256: `007db5624f713170c639fd9b57c7f333481083f6d4218a627fe77fc2f6a7957f`.
- Mini rootfs SHA-256: `3d2bf04262732ad15a2cd96d14af3fb527fcb9271c20171f4037a968ead1255e`.
- Mini qemuboot SHA-256: `4f1426052a9f8787831d46bd6a8b384e9203a9cef03e84637007e12e927cf542`.
- Mini kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QMP initial/up SHA-256:
  `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`.
- Pixel-analysis SHA-256: `5f462f651166f15199564daa63b9cd37d8757b23c741b7c804d316e46ff5e129`.
- Bounded app-marker output SHA-256:
  `a63252905359c25a470faac636c678b562ace40b1221ac60132b21c13b1815cc`.
- Cleanup: `qmp_residual=0 qemu_residual=0 app_residual=0`.

## UNKNOWN

- Whether the readiness method channel reaches true in this image.
- Whether the native handler is reached for every poll, or whether a call is
  stalled/errored after the first false result.
- Whether Planetarium `onCreate` can activate the production camera without
  causing the former white HUD boundary.

## Result

FLR-0247 proved the registration boundary and the first false readiness result,
but did not prove a ready transition or lifecycle callback. All QMP frames kept
HUD `2883` and native fixture ROI `100800` chromatic pixels, so this diagnostic
patch did not regress the known 2D/native fixture path. The exact missing
MethodChannel boundary remains UNKNOWN and is isolated into
[FLR-0248](FLR-0248-trace-readiness-method-channel-boundary.md).
