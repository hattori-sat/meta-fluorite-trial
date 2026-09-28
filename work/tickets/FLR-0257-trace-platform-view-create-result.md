# FLR-0257 — trace native PlatformView create result delivery

- Status: Done
- Priority: High
- Owner: flutter/platform_views create result and Dart callback completion
- Created: 2026-09-21
- Predecessor: [FLR-0256](FLR-0256-trace-platform-view-created-callback.md)

## Objective

Determine whether the native `flutter/platform_views` `create` method returns
success to Dart after the Filament platform view has registered, and identify
the exact boundary before `AndroidViewController.create()` invokes its
`onPlatformViewCreated` callbacks.

## Facts

- FLR-0256 app-side markers show `_onPlatformViewCreated` is not reached.
- The same run reaches `FLUORITE_VIEWTARGET_CAPI_REGISTER_RETURN state=1`,
  native shape preparation, draw/present, and Wayland attach.
- Flutter SDK `AndroidViewController.create()` awaits `_sendCreateMessage()`
  before dispatching the callback list.
- Native `platform_views_handler.cc` routes `create` to
  `PluginsAoiPlatformViewCreate`; the Filament branch calls
  `result->Success(EncodableValue(id))` after the C API returns.

## Hypotheses

1. The native `result->Success` path is not reached or is not returning to the
   engine after the Filament C API call.
2. The result is delivered, but the Flutter engine/Dart Future completion is
   lost before the callback list is invoked.
3. The app-side callback is reached only after a lifecycle condition not
   represented in the current bounded log; the new native markers will falsify
   this if result delivery is complete.

## Scope boundary

Add only native create/result boundary diagnostics in the existing
`fluorite-plugins`/flutter-auto path as needed. Do not change model payload,
camera, light, material, renderer, Wayland stacking, or QMP input behavior.

## Success criteria

- Static source and one runtime classify create entry, Filament C API return,
  `result->Success` invocation/return, and Dart callback completion.
- If source changes are needed, use the persistent Mac Devtool source Git and
  official Devtool-generated patch flow, then commit the canonical layer.
- Mini patch/compile/full-image/QMP/cleanup gates pass at the exact bundle tip.

## Verification plan

1. Instrument the native result boundary with bounded markers.
2. Reuse the fixed Mini receiver/build/TMPDIR and one QMP-first QEMU run.
3. Compare marker order with the existing app-side callback markers and the
   2D/production ROIs.
4. Split any actual callback repair or renderer change into a new ticket.

## UNKNOWN

- Whether `MethodResult::Success` is invoked after the current C API return.
- Whether the engine's Dart Future receives the success response.
- Whether production Sequoia pixels can appear after callback completion.

## Check — authoritative Mini and QEMU result

- Canonical commit: `99485e04021bdf3dd0ad416e169fcaee8122abc9`.
- Official patch `0275` SHA-256:
  `5d679c0c47fd8431362dbdc7e7244dc82a4e1495868b520ef45bf17c35caa2a0`.
- Source commit: `d0583288f06a31cd776ddc37c4ee5564a0cc9098`; baseline:
  `18c518bcb20576bd2370e64d13aa2497acf7e789`.
- Mini bundle SHA-256:
  `7463b089848dcb6118191d8efa7dc8943c89ae20b693980f7b36400d433f6a74`.
- Mini `flutter-auto:do_patch`, `do_compile` (`2686/2686`), and full image
  (`11758/11758`) all passed. Rootfs SHA-256:
  `6376b0ffab4ade19d397e20f6f6f6f7081793b4fea927a1ac4c31ca5fed455fd`.
- QEMU preflight/start/guest-ready and QMP capture passed. The first frame was
  pre-launch black because the image does not auto-start the Example Demo; this
  was classified as a launch-contract observation, not a rendering result.
- After one explicit `agl-driver` launch using the installed 3.38.3 release
  bundle, settled QMP frame SHA-256 was
  `98fefc82310d2c9ab2ae8decfb55a19bcaca5d4d17d506899cc37172c4bfa09e`.
- HUD ROI `[1120,0,160,80]`: `2845` chromatic pixels. Production ROI
  `[200,100,400,250]`: `0` chromatic pixels and `116` grayscale changed
  pixels. Native 3D candidate ROI `[300,250,620,400]` was uniformly black.
- Eight video frames were byte-identical to the settled frame. The video and
  screenshot are retained under
  `$RECEIVER/evidence/FLR-0257/qemu-create-result/`.
- Runtime log SHA-256:
  `b39de8e5cbc12edffde66eceaa6b2b042f47b24d67408af70bb0b96b7808343f`.
  `FLUORITE_VIEWTARGET_CAPI_REGISTER_RETURN` and
  `FLUORITE_VIEWTARGET_RENDERING_LOOPS_ROUTED` occurred once; all
  `FLR0257_PLATFORM_VIEW_RESULT_SUCCESS_*` and FLR-0256 app callback markers
  occurred zero times. The guest `flutter-auto` stayed alive after the C API
  return, so this is not an immediate process crash.
- The guest `/usr/bin/flutter-auto` contains both FLR-0257 marker strings, and
  the Mini patched source plus `.pc/0275-*` backup contain the same markers.
  Therefore the zero runtime count is not an unpatched-image explanation.
- QEMU quit and cleanup passed: `residual_targets=0 residual_qmp=0`.

## Final classification

The official native patch reached the guest binary and the C API registration
returned, but the markers immediately before and after
`result->Success(EncodableValue(id))` in `generated_plugin_registrant.cc` did
not execute. The application callback also remained absent, while the process
stayed alive and the 2D HUD remained visible. The exact caller/handler return
boundary is therefore still UNKNOWN and is split to
[FLR-0258](FLR-0258-trace-platform-view-handler-return.md). No rendering,
camera, light, model, or composition change belongs in this next diagnostic.
