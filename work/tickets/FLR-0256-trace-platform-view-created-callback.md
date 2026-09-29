# FLR-0256 — trace PlatformView-created callback reachability

- Status: Done
- Priority: High
- Owner: Flutter PlatformView callback and Dart frame-event registration
- Created: 2026-09-21
- Predecessor: [FLR-0255](FLR-0255-defer-readiness-poll-until-platform-view.md)

## Objective

Prove the exact boundary between native `ViewTarget` registration and the
Flutter `onPlatformViewCreated`/`poGetFilamentScene.onCreated` callback in the
production Example Demo. The result must distinguish an uncalled callback
from a callback whose marker or readiness registration is lost later.

## Facts

- FLR-0251 proves the same image can display the 2D HUD and a self-made native
  3D cube.
- FLR-0255 proves native production model selection, render/draw, Vulkan
  present, and Wayland attach, but production QMP ROI remains black.
- FLR-0255 contains no `poGetFilamentScene onCreated` or readiness-completion
  marker after the deferred poll change.

## Hypotheses

1. `onPlatformViewCreated` is not dispatched after native registration; the
   Dart readiness/frame-event boundary therefore never becomes active.
2. The callback is dispatched, but the existing marker is outside the bounded
   log path or is lost before `onCreated`; a callback-local probe will prove
   this without changing rendering.
3. The callback and readiness handler run, but the first frame-event response
   remains unresolved; this is a downstream native↔Dart future boundary.

## Scope boundary

This ticket may add callback-boundary diagnostics and one minimal readiness
registration A/B. It must not change the production model list, camera, light,
material, native renderer, Wayland stacking, or QMP harness.

## Success criteria

- Static call-chain evidence identifies the exact callback path.
- If source changes are needed, one official Mac Devtool source commit and one
  generated patch are recorded; generated patch text is not hand-edited.
- The exact canonical commit is bundled to Mini and passes `do_patch`, app
  compile, full image, QMP capture, and cleanup.
- One bounded QEMU run classifies callback, readiness, frame-event response,
  and production ROI independently.

## Verification plan

1. Read the current `SceneView` callback chain and existing marker placement.
2. Compare the three hypotheses using the smallest diagnostic change.
3. Use the fixed Mini image/QEMU harness and record only bounded callback,
   readiness, frame-event, draw/present, and ROI evidence.
4. Split any render/camera/light/composition change into a new ticket.

## UNKNOWN

- Whether the production `AndroidView` callback is reached in the shipped
  Linux embedding path.
- Whether `onCreated` is the first missing boundary or only the first missing
  marker.
- Whether production pixels can change before the frame-event future is
  resolved.

## Check — authoritative Mini and QEMU result

- Source commit: `12cb66604ca74a9deb6dafc799209c1fa41a4fb3`.
- Official patch `0086` SHA-256:
  `afdbec4c8171f6b13c05910d8c1116a6592722d996f391c61ac48e7dc0db792d`.
- Canonical layer commit: `91cf7df30a300cce4ad70bff98b1b4e2a83db064`.
- Mini bundle handoff SHA-256:
  `074e35c933de4fd9f472b958a37c5d3ce665a1ec60a6309abd6a9f4d85ecac28`.
- Mini recipe `do_patch=PASS`, app `do_compile=PASS` with `1674/1674`
  attempted tasks, and full image `PASS` with `11758/11758` attempted tasks.
- Rootfs:
  `agl-ivi-image-flutter-qemux86-64.rootfs-20260921021254.ext4`, SHA-256
  `9fc8e0f8d8ba5731641541e502371c94e82f54c7063facea634566b45d20aabe`.
- QMP `initial.ppm` and `settled.ppm` are byte-identical with SHA-256
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- HUD ROI `[1120,0,160,80]` contains `2845` chromatic pixels. Production ROI
  `[200,100,400,250]` contains `0` chromatic pixels and `116` grayscale
  changed pixels.
- The same bounded run emits `FLR0247_STATE_REGISTER`, native ViewTarget
  registration, shape preparation, draw/present, and Wayland attach markers.
- The callback probe markers
  `FLR0256_PLATFORM_VIEW_CREATED`, `FLR0256_CONTROLLER_COMPLETED`,
  `FLR0256_ON_CREATED_DISPATCH_BEGIN`, `FLR0256_PO_ON_CREATED_BEGIN`, and
  `FLR0256_READINESS_START_CALL` each occur `0` times. Existing readiness
  completion markers also occur `0` times.
- The Flutter SDK contract calls the PlatformView callbacks only after
  `AndroidViewController.create()` awaits the native `flutter/platform_views`
  `create` result. Native static source routes that call through
  `PluginsAoiPlatformViewCreate` and then `result->Success(id)`, but the
  result boundary itself is not yet instrumented.
- QEMU teardown passed: `cleanup=PASS residual_targets=0 residual_qmp=0`.

## Final classification

The app-side callback probe proves that the first missing runtime boundary is
before `_onPlatformViewCreated`; this is not evidence that the native draw
path or QMP capture is broken. The native `create` result boundary is split to
[FLR-0257](FLR-0257-trace-platform-view-create-result.md).
