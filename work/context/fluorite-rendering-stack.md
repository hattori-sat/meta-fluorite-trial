# Fluorite rendering stack — initial source map

## Purpose

Fluorite demoがFlutter UIからnative 3D描画、Wayland、Vulkan/Mesa、target GPUへ到達するprocessを、component単位で調査できるようにする。

## Observed component chain

```text
AGL image / packagegroup
  -> Fluorite Flutter AOT bundle (fluorite_examples_demo)
  -> ivi launcher / flutter-auto
  -> Flutter Engine embedder API
  -> Dart package: filament_scene
  -> platform messages and event channels
  -> native plugin: filament_view
  -> Filament rendering engine
  -> Vulkan loader / Wayland surface
  -> Mesa driver
  -> QEMU software/virtual GPU or Raspberry Pi GPU
```

矢印は初期source mapであり、すべてのownership・thread・surface共有方式が確認済みという意味ではない。

## Facts from source and recipes

以下は`$LEGACY_ROOT`のsource snapshotと既存build evidenceから得た初期事実。canonical build hostのfixed revisionと一致するかはFLR-0001/0007で照合する。

### Fluorite demo

- Flutter app名は`fluorite_examples_demo`。
- `filament_scene` packageをlocal path dependencyとして使う。
- sceneはPlayground、Radar、Settings、Planetarium、Trainset。
- native readinessを待ってからsceneとevent channelを初期化する。
- model、HDR、material、font等のassetがあり、source snapshotではasset総量が大きい。

### filament_scene

- Dartでscene、entity、camera、material、model、event APIを提供するFlutter plugin。
- Linux plugin classは`FilamentViewPlugin`。
- native coreは`filament_view` componentに実装されるとREADMEに記載される。

### ivi launcher and Flutter Engine

- launcherはFlutter Embedder APIをdynamic library経由で呼ぶ。
- Wayland EGLとWayland Vulkanのbackend実装が存在する。
- Vulkan backendはFlutter renderer config、image acquisition、present callback、Wayland surfaceを扱う。

### native Filament integration

- Yocto appendは`flutter-auto`に`filament-view` PACKAGECONFIGを追加する。
- 有効時はnative plugin build option、Filament include/library pathを渡し、Filament、curl、Vulkan loaderへ依存する。
- local patchは`ivi-homescreen-plugins/plugins/filament_view`配下へ適用される。

### Filament and Vulkan

- Filament recipeはVulkan、Wayland、OpenGLをPACKAGECONFIG候補に持つ。
- current customizationはFilament 1.69.4、cross-build host tools、header/static library installを調整する。
- built image manifestにはVulkan loader、Mesa Vulkan drivers、Vulkan toolsが含まれる。

## Inferences

- Fluoriteは単純なFlutter Canvas 3Dではなく、Dart UIからnative Filament engineを操作する構造。
- Flutter Engine自身のrendererとFilament engineのrendererは別の責務を持つ可能性が高い。
- crashや描画不良を調べるには、Dart lifecycle、platform message、native plugin、Filament、Vulkan/Mesaを分けて観測する必要がある。

## Unknowns

- Flutter frameとFilament frameの最終composition方式。
- native pluginが使用するwindow/surface/textureのownership。
- Flutter UI thread、platform thread、Filament render thread間の同期契約。
- current imageでFlutter renderer backendが必ずVulkanか、target/configで変わるか。
- Raspberry Piで選択される実Vulkan device/driver。
- assetまたはmaterialがFilament versionにどの程度固定されるか。
- `$LEGACY_ROOT`のcustom layer snapshotとcurrent build host版の差分。

## Current runtime checkpoint (2026-10-01)

### Facts

- FLR-0394 used the exact rootfs built with Sequoia patch 0333. QMP showed the
  self-created blue LIT/SUN fixture and CPU/GPU/FPS HUD together. The native
  ROI contained 119,716 changed/chromatic pixels; the full-frame screenshot,
  video, checksums, present counters, timeout, and cleanup are indexed in
  work/evidence/FLR-0394-0001.md.
- FLR-0391 applied the same constant-blue LIT expression to Sequoia renderable
  primitives and built it through the Mini. Its live QMP Sequoia ROI was
  black during an unmatched present and FEngine Oops. The binding marker count
  is not a primitive count.
- Source comparison found one concrete material-interface mismatch: the
  fixture declares FLOAT3 `color` and sets the instance to the same linear RGB
  even on its constant-source branch; Sequoia patch 0333 omits both operations.
- FLR-0396 applied that exact difference with Devtool patch 0334 and built a
  fresh Mini image. Runtime reached READY/PARAM and SUN, then logged two
  present-begin records, one return, and an `FEngine::loop` kernel Oops. The
  readiness observer watched a different file from the GDB launch, so no live
  QMP frame was captured. The post-exit black QMP still is not a live-render
  result; whether colored Sequoia appeared is UNKNOWN. See
  `work/evidence/FLR-0396-0001.md`.
- The visual gates are intentionally separate: FLR-0396 tests colored
  production Sequoia pixels in a current-image live frame; FLR-0396's missing
  observer window means it did not pass. FLR-0399 will correct evidence capture
  using the same 0334 image. FLR-0398 will test same-frame Sequoia+HUD
  composition only after Gate A passes. The
  historical native-only FLR-0049 frame and the user's un-attributed
  HUD+vehicle-fragment photo are not substitutes for current-image acceptance.
- The user's photo is retained as
  `work/evidence/FLR-0398-user-provided-composition-reference.jpg`, SHA-256
  `df30ba433b979f631c552328c0db29ef95a8a6dfefe795e3d5976ddd4b4cd3d3`. It
  shows `Shapes: On` and `Colliders: Off`; the white wireframe-like lines are
  very likely Shape visualization. A 2026-10-02 visual comparison with
  `work/evidence/flr0027/shape-only-late.png` found a strong match in polygon
  layout and line geometry. Exact renderer/source attribution remains UNKNOWN
  without an attributable run, so neither those lines nor their overlap with
  the red vehicle pixels counts as Sequoia geometry.

### Inferences

- The exact image can render the simple native fixture and HUD; a universal
  native 3D-output failure is falsified for that fixture path.
- Production Sequoia remains the unresolved boundary. Matching color
  expressions do not prove identical material variants or assignment behavior.

### Unknowns

- Whether the Sequoia Oops causes the missing pixels or is correlated.
- Whether the simple fixture and Sequoia use equivalent generated shader
  variants.
- Whether Sequoia becomes visible before the first runtime fault.

### Next bounded discriminator

FLR-0396's bounded result is recorded above. FLR-0399 is the next distinct
ticket: reuse the exact 0334 image, align the guest app/GDB output path with the
observer, persist GDB output to Mini evidence before teardown, and capture a
live PID-bracketed QMP frame at READY/first present/fault. No image rebuild or
material/camera/light edit is in scope. The live full frame must separately
classify Sequoia color and whether HUD pixels are present; a native-above-parent
presentation masks HUD but does not disable Flutter 2D. Gate A (colored
production Sequoia) and Gate B (same-frame HUD+Sequoia composition) remain
independent. FLR-0398 owns Gate B after Gate A is established; FLR-0395 keeps
its older 0333 baseline.

## Evidence needed

- exact Yocto recipeとSRCREVからnative plugin sourceを取得。
- `filament_view`のplugin registration、engine creation、surface/texture creationを追跡。
- launcherのbackend selectionとFlutter renderer configを実効configから確認。
- targetで`vulkaninfo`、Mesa/DRM/Wayland情報、process/thread logを収集。
