# FLR-0255 — defer readiness polling until Platform View creation

- Status: Done
- Priority: High
- Owner: Example Demo readiness lifecycle and Platform View callback
- Created: 2026-09-21
- Predecessor: [FLR-0253](FLR-0253-restore-production-frame-event-registration.md)

## Objective

Prevent `NativeReadiness.addCallback()` from starting a MethodChannel poll
before the Flutter `AndroidView.onPlatformViewCreated` callback has run. Start
the one readiness poll only after the native Platform View has registered its
channels, then verify that the callback and frame-event registration become
observable in the same QEMU run.

## Facts

- FLR-0253 official patch `0084` is present in the Mini source, final rootfs,
  and `libapp.so`.
- Runtime still emits `FLR0247_READINESS_POLL_START` before native ViewTarget
  registration and then reports `MissingPluginException`/timeouts.
- `StatefulSceneView.initState()` calls `readinessController.addCallback()`.
- `NativeReadiness.addCallback()` immediately launches its polling loop.
- `SceneView._onPlatformViewCreated()` is the only static call site that proves
  the Flutter Platform View creation callback has fired.
- `poGetFilamentScene.onCreated` is downstream of that callback and was not
  observed in FLR-0253.

## Hypotheses

1. The first divergence is the eager `NativeReadiness.addCallback()` poll from
   the mounted PlanetariumSceneView; deferring poll startup until
   `onPlatformViewCreated` will remove the MissingPluginException and allow
   `FLR0249_READINESS_START_AFTER_PLATFORM_VIEW` to appear.
2. Native channel registration is independently broken; deferring the poll
   will still produce no Platform View callback or marker.

## Scope boundary

This ticket changes only readiness-poll ownership and callback ordering. It
does not change the production model list, camera, light, native renderer, or
Planetarium lifecycle bodies.

## Success criteria

- One source commit is created in the persistent Mac Devtool workspace from
  the current source history.
- One official Devtool patch is generated and registered in the app recipe.
- Mini `do_patch`, app compile, and full image pass at the exact bundle tip.
- One QEMU run emits Platform View/onCreated/readiness/frame-event markers in
  the expected order and leaves no QEMU or QMP residue.
- The QMP HUD remains visible and the production ROI is reclassified with
  fresh pixels. Production 3D may remain a separate next boundary.

## Verification plan

1. Keep the current source and recipe stack as the baseline. Compare an
   explicit-start API versus a callback-local start and choose the smallest
   change that preserves existing callback registration semantics.
2. Generate the patch through official Devtool, bundle the canonical commit to
   the fixed Mini receiver, and run progressive BitBake gates.
3. Launch one QEMU instance, collect bounded readiness/native/model markers,
   capture QMP-only frames, and teardown through the recorded QMP socket.

## UNKNOWN

- Whether `StatefulSceneView` callbacks can be registered before poll startup
  without changing the intended scene lifecycle.
- Whether the onCreated callback will expose production 3D after readiness is
  fixed.

## Current execution evidence

- Source baseline was the completed FLR-0253 source commit `b344d75`.
- Source commit: `ac7c9d281a83e5b2b8d9851f2a483e4694478dc8`.
- Official generated patch:
  `0085-flr0255-defer-readiness-poll-until-platform-view-devtool.patch`.
- Generated patch SHA-256:
  `1e0ee94e82003f52f5e27a472b2f538be89ea404bd8e2904c0700f4f5c654c2f`.
- The patch separates callback registration from readiness polling and starts
  the single poll from `poGetFilamentScene.onCreated`.
- Canonical layer commit: `ca980dc`; the complete-history bundle tip on Mini is
  `ca980dca3e02a87841b68eb31fecef2847cc828f`.
- Mini patch gate passed with `0085` present, app `do_compile` passed with
  `1674/1674` tasks, and the full image passed with `11758` attempted tasks and
  no failures.
- Rootfs SHA-256:
  `e4a4b719b967c9033a072ee7ecd3dd0f677f84df96cbd951531eb5ffd44c7cad`.
- QEMU preflight, start, guest-ready, and all bounded serial collection gates
  passed. QMP `initial.ppm` and `settled.ppm` are byte-identical with SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- QMP HUD ROI `[1120,0,160,80]` contains `2845` chromatic pixels. The
  production ROI `[200,100,400,250]` contains `0` chromatic pixels and only
  `116` grayscale changed pixels.
- Runtime reaches `FLUORITE_VIEWTARGET_CAPI_REGISTER_RETURN state=1`, model
  selection for `sequoia_ngp.glb`, render-pass/draw markers, Vulkan queue
  submit/present result `0`, and Wayland `wl_surface@39.attach`.
- The bounded runtime outputs contain no
  `FLR0249_READINESS_START_AFTER_PLATFORM_VIEW`,
  `FLR0247_READINESS_READY`, `FLR0247_READINESS_CALLBACK_DISPATCHED`, or
  `poGetFilamentScene onCreated` marker. The deferred poll removed the earlier
  pre-registration poll from the collected slice, but did not prove the Dart
  PlatformView callback boundary.
- QEMU teardown passed with `cleanup=PASS residual_targets=0 residual_qmp=0`.

## Final classification

The patch-delivery and early-readiness-poll hypotheses are closed for this
ticket. The image is reproducible and the native render/present path is active,
but production 3D is still not visible. The first unproven boundary is now
the Flutter PlatformView-created callback / Dart frame-event registration
boundary, split to [FLR-0256](FLR-0256-trace-platform-view-created-callback.md).
