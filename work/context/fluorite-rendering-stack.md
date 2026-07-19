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

## Evidence needed

- exact Yocto recipeとSRCREVからnative plugin sourceを取得。
- `filament_view`のplugin registration、engine creation、surface/texture creationを追跡。
- launcherのbackend selectionとFlutter renderer configを実効configから確認。
- targetで`vulkaninfo`、Mesa/DRM/Wayland情報、process/thread logを収集。
