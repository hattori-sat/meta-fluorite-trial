# FLR-0248 — trace readiness MethodChannel call/response boundary

- Status: Done
- Priority: High
- Owner: NativeReadiness Dart/native MethodChannel boundary
- Created: 2026-09-21
- Predecessor: FLR-0247

## Objective

Identify the first missing event in the readiness path used by
`PlanetariumSceneView`: Dart invocation start, native `isReady` handler entry,
native response, Dart return/error, and bounded timeout. Keep the direct
Planetarium mount and the proven 2D/native fixture composition unchanged.

## Facts

- FLR-0247 observed `StatefulSceneView` registration and the first readiness
  result as `false`.
- FLR-0247 observed no later ready, callback-dispatched, timeout, or
  `PlanetariumSceneView.onCreate` marker in the bounded run.
- Static source inspection found the Dart channel name
  `plugin.filament_view.readiness_checker` and the native `isReady` handler use
  the same channel and method name.
- The native handler computes readiness from
  `ECSManager::GetRunState() == ECSManager::RunState::Running`.
- FLR-0247 preserved HUD `2883` and native fixture ROI `100800` in every QMP
  frame, so the diagnostic instrumentation did not break the tested 2D/native
  composition.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Native handler is not reached after the first call | Dart begin markers appear without native receive/response markers | Channel registration or messenger lifecycle issue |
| 2 | Native handler is reached but readiness remains false | Native receive/response markers repeat with a non-running state | `ECSManager` transition may never reach `Running` |
| 3 | Dart invocation does not return or errors are swallowed | Dart begin appears without return/error until the bounded timeout | Existing catch block hides the distinction |

## Scope and invariants

- Add bounded diagnostic markers only around the existing readiness call and
  native handler; add a short per-call timeout so one stalled call cannot hide
  subsequent evidence.
- Do not change camera, light, material, scene objects, parent `Stack`,
  `Builder` structure, QMP coordinates, or pixel thresholds.
- Use the fixed Mac Devtool source history and official generated patch flow.
- Run the same Mini patch/compile/image gates and one QMP session; save logs
  before teardown.

## Success criteria

- [x] Static inspection identifies the smallest call/response instrumentation.
- [x] Official source commit, generated patch, canonical commit, bundle, and
  Mini gates are recorded.
- [x] Runtime evidence identifies the first missing readiness boundary or
  proves a bounded repeated-false path.
- [x] HUD/native pixel results remain comparable to FLR-0247.
- [x] Cleanup proves zero residual QEMU/QMP/flutter-auto processes.
- [x] A production readiness fix is not claimed until the missing boundary is
  identified and separately ticketed.

## Evidence

- Predecessor: [FLR-0247](FLR-0247-trace-planetarium-readiness-callback.md)
- Working log: [2026-09-21-flr0248.md](../logs/2026-09-21-flr0248.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0248/`
- Dart source commit: `3cbbaad09b8cd3571228b267a59ef5a234dd1016`.
- Native source commit: `18c518bcb20576bd2370e64d13aa2497acf7e789`.
- Official generated app patch:
  `0080-flr0248-trace-readiness-method-channel-boundary-devtool.patch`.
- App patch SHA-256: `015e69c68147de6cc06932722eaa70d80a6abf009c6349b248c508a53208e66f`.
- Official generated native patch:
  `0274-flr0248-trace-native-readiness-method-call-devtool.patch`.
- Native patch SHA-256: `b9be5778a870e8d25f8dd3d43119944ac49e86b6b8fbe3e93348752ccb434a19`.
- Canonical layer commit: `7447073659dc04acd4d28dd07210bdee63d2bc4f`.
- Bundle SHA-256: `39f454e33b5824b5c891244ea9e6ca3a8e2e3d59357cadaf40e5e88c3888e80c`.
- Mini rootfs SHA-256: `c3d9232b967f507b61a41908158fec5cbcb82307f4ced76d71c57eca91973ed0`.
- Mini qemuboot SHA-256: `4867978c68f9a5f5ef57630d08c029ef407e9ab7e9fb28ccddaec35a7fe00843`.
- Mini kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- Compile: `flutter-auto do_compile`, 2686 attempted tasks, all succeeded.
- Full image: `agl-ivi-image-flutter`, 11758 attempted tasks, all succeeded.
- QMP PPM SHA-256: initial/move-x/move-y/down/up all
  `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`.
- Pixel-analysis SHA-256: `86622f49d5d711c2212615439ca3ac81b2fae73d4872e559f21b2fccb6dd77dd`.
- Serial marker output SHA-256: `a9d81569d819c150532b8cb1ad669457a0d567649cf94371ee6c799b2107d9b9`.
- App log SHA-256: `3ab3f5c98342f32a4066d557a3a6a4b8cc8d146c0d288eff5b185057c3e9343f`.
- Cleanup: `residual_targets=0 residual_qmp=0`.

## UNKNOWN

- Whether the native handler is reached for every poll.
- Whether `ECSManager::GetRunState()` changes to `Running` in this image.
- Whether the missing production geometry is downstream of readiness or an
  independent scene/camera/light issue.

## Runtime result

- The exact Mini build worktrees contain both FLR-0248 diagnostic markers,
  proving the generated patches reached the build inputs.
- Dart recorded two `MissingPluginException` errors for the first calls, then
  345 bounded `FLR0248_DART_CALL_TIMEOUT` results. No
  `FLR0248_DART_CALL_RETURN` result occurred.
- Native `FLR0248_NATIVE_CALL_RECEIVED` and
  `FLR0248_NATIVE_CALL_RESPONDED` counts were both zero.
- The readiness boundary is therefore the native handler
  registration/reachability boundary, not a repeated `false` state from
  `ECSManager`.
- The self-made native 3D fixture and 2D HUD remained visible in every QMP
  frame, so FLR-0248 did not regress the proven 2D/native fixture path.

## Result

FLR-0248 identified the first missing runtime boundary: the Dart readiness
MethodChannel does not reach the native handler in the built image. The exact
registration-order/lifetime mechanism remains UNKNOWN; FLR-0249 isolates that
correction. Production Planetarium geometry and its camera/light path remain
unproven.
