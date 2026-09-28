# FLR-0253 — restore production frame-event registration order

- Status: Done
- Priority: High
- Owner: Example Demo readiness and frame-event registration
- Created: 2026-09-21
- Predecessor: [FLR-0252](FLR-0252-verify-production-planetarium-3d.md)

## Objective

Restore the production app's readiness and frame-event registration order so
the native ViewTarget can call the Dart frame handler after the platform view
exists. Validate that this boundary changes runtime markers and production
pixels without changing the native renderer, camera, light, or payload.

## Facts

- The current app source commit `c5cf3cd` contains the FLR-0251 reverse patch
  that restores `unawaited(initializeReadiness())` in `MyAppState.initState`.
- `startListeningForEvents()` installs the `FrameEventChannel` method handler,
  but it is called only after `NativeReadiness.isNativeReady()` returns true.
- The current QEMU run produced `MissingPluginException`/timeout records for
  the readiness channel and did not produce a route transition marker.
- The earlier official FLR-0249 patch `0081` moved readiness startup into the
  `poGetFilamentScene.onCreated` callback. Its Mini runtime evidence reached
  `FLR0249_READINESS_START_AFTER_PLATFORM_VIEW`, `READY`, and
  `CALLBACK_DISPATCHED`.
- The current initial `SceneView` still supplies the production model, scene,
  shape, and camera payload. The current `PlanetariumSceneView` lifecycle is
  intentionally inert from prior isolation tickets; it is not changed by this
  ticket.

## Hypotheses

1. Restoring post-platform-view readiness registration allows the Dart frame
   handler to be installed and removes the first registration boundary that
   prevents the production route from progressing.
2. The timeout is independent of frame-event registration and production GLB
   loading remains the first failure.

## Success criteria

- Official Mac Devtool generates exactly one patch from the current source
  history, with the source commit recorded before `update-recipe`.
- The canonical layer registers that patch after `0082` and `0083` without
  editing generated patch text by hand.
- Mini `do_patch`, target compile, and full image build pass using the exact
  committed bundle.
- One QEMU run records readiness registration/return markers, frame-event
  markers, bounded model-stage markers, QMP-only pixels, and clean teardown.
- The result is classified by pixels: production ROI changes from the current
  black baseline, or the hypothesis is falsified with stronger evidence.

## Verification plan

1. Use the persistent Mac Devtool container and its existing source Git
   workspace. Re-read the source commit history and make only the registration
   order change.
2. Commit the source change in the Devtool source Git, run official
   `devtool update-recipe`, and register the generated patch in the canonical
   layer.
3. Commit the layer, create and transfer one complete-history bundle to the
   fixed Mini receiver, and run the progressive BitBake gates.
4. Launch one QEMU instance with the existing production payload and bounded
   traces. Accept only QMP `screendump`/ROI evidence and the fixed cleanup
   result.

## UNKNOWN

- Whether the frame-event handler is the exact unresolved native future seen
  by GDB in FLR-0252.
- Whether production Sequoia pixels will appear after registration is fixed.
- Whether the intentionally inert Planetarium lifecycle needs a separate
  later ticket after this registration boundary is proven.

## Current execution evidence

- Mac Devtool source commit: `b344d75f566535d9e85e314191843f78f4f7cc5c`.
- Official Devtool baseline: `c5cf3cdc2fcba4a83110deb4910dc03ad767e05a`.
- Official generated patch: `0084-flr0253-restore-readiness-after-platform-view-devtool.patch`.
- Generated patch SHA-256: `158298f5ea1105fc5e0cf2f87ffc35611ab8c304fd303bbcfc828e303a4926b8`.
- The canonical recipe registers `0084` once after `0081`, `0082`, and `0083`.
- The first generation attempt correctly failed closed because no active
  Devtool recipe registration existed. Re-registering the final source HEAD
  was also rejected as a zero-diff baseline. Registering `c5cf3cd` first and
  then checking out `b344d75` produced exactly one official patch.
- Mac `recipe-task ... do_patch` is currently blocked by the focused Mac
  profile: `Nothing PROVIDES 'quilt-native'`. This is an environment gate,
  not a patch-application conflict; it is split to FLR-0254.

## Final classification

- Mini `do_patch`, app `do_compile`, and full `agl-ivi-image-flutter` build
  passed at receiver commit `24cdb3a6185c790795d7d856c6ca85fea67b46ca`.
- The final rootfs `libapp.so` contains the `0084` marker, proving that the
  generated patch reached the runtime artifact.
- QMP initial and settled frames were byte-identical with SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- The HUD ROI `[1120,0,160,80]` had `2845` chromatic pixels. The production
  ROI `[200,100,400,250]` had `0` chromatic pixels and only grayscale edges.
- Runtime did not emit `poGetFilamentScene onCreated` or
  `FLR0249_READINESS_START_AFTER_PLATFORM_VIEW`. It emitted
  `FLR0247_READINESS_POLL_START`, then `FLR0248_DART_CALL_ERROR` with
  `MissingPluginException` and repeated timeouts before native ViewTarget
  registration completed.
- QMP teardown passed with `residual_targets=0` and `residual_qmp=0`.

The patch-generation and patch-delivery hypothesis is therefore closed. The
first runtime divergence is split to FLR-0255.
