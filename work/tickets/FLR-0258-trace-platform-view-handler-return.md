# FLR-0258 — trace PlatformView handler return boundary

- Status: Done
- Priority: High
- Owner: flutter-auto `platform_views_handler.cc` call/return and MethodResult ownership
- Created: 2026-09-21
- Predecessor: [FLR-0257](FLR-0257-trace-platform-view-create-result.md)

## Objective

Determine whether the running `flutter/platform_views` handler enters and
returns from `PluginsAoiPlatformViewCreate`, and whether the
`MethodResult` unique pointer reaches the generated plugin registrant branch.

## Facts

- FLR-0257's official patch is present in the guest binary.
- The Filament C API registration returns and the process remains alive.
- The markers immediately around `result->Success()` in the generated plugin
  registrant are absent.
- The app-side `onPlatformViewCreated` and readiness markers are absent.
- The 2D HUD is visible, while the production 3D ROI remains black.
- The handler-entry markers occur once each, but the markers after the
  `PluginsAoiPlatformViewCreate` call do not occur.

## Hypotheses

1. `platform_views_handler.cc` does not return from the
   `PluginsAoiPlatformViewCreate` call after the C API returns.
2. The running handler uses a different result/lifecycle path than the
   generated registrant source inspected by FLR-0257.
3. Native result completion occurs, but the engine/Dart Future boundary loses
   the completion after handler return.

## Result

The first hypothesis is confirmed for the tested runtime path: the
`platform_views` create handler enters and reaches the
`PluginsAoiPlatformViewCreate` call, but the call does not return during the
bounded run. The result markers and Dart callback markers therefore cannot be
classified as downstream failures yet. The repair or deeper native call-stack
analysis is split to FLR-0259.

## Scope boundary

Add bounded diagnostics only at handler entry, immediately before the
`PluginsAoiPlatformViewCreate` call, immediately after it returns, and at the
handler return. Do not change result behavior, model payload, camera, light,
material, renderer, Wayland stacking, or QMP input.

## Success criteria

- Static source identifies the effective handler and result ownership path.
- If source changes are needed, use the persistent Mac Devtool source Git and
  official generated patch flow; do not hand-author generated patch text.
- Mini patch/compile/full-image/QMP/cleanup gates pass at the exact bundle tip.
- One bounded run classifies handler entry, call return, generated result
  boundary, and Dart callback completion.

## Verification plan

1. [x] Inspect the effective `flutter-auto` source and existing handler patch stack.
2. [x] Add the smallest handler-only diagnostic through official Devtool.
3. [x] Reuse the fixed Mini receiver/build/TMPDIR and explicit single-app launch.
4. [x] Split the next native call/return analysis into a new ticket after the
   first missing boundary.

## UNKNOWN

- Whether `PluginsAoiPlatformViewCreate` blocks on a specific native thread,
  lock, or API call.
- Whether the generated registrant and `MethodResult::Success` are reachable
  after the blocking call is repaired.
- Whether callback completion can occur before the handler boundary is fixed.
