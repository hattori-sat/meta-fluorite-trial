# FLR-0011 — Map the effective Vulkan and GPU path

- Status: Next
- Priority: High
- Depends on: FLR-0009, FLR-0010

## Purpose

Flutter/Filamentの描画要求がVulkan loader、Mesa、DRM/virtual GPUを通り、Wayland compositorへpresentされる実効経路をtarget別に確認する。

## Success criteria

- QEMU x86-64、QEMU arm64、Raspberry Piを別stratumとして比較する。
- Vulkan instance/device/driver、extensions、surface format、present modeを記録する。
- hardware、virtual GPU、software rendererを区別する。
- FlutterとFilamentのdevice/surface ownershipを確認する。
- performanceとcorrectnessを別指標で評価する。

## Cause hypotheses to preserve

- software Mesa/LLVM固有の問題。
- CPU emulationとguest instruction/threadingの相互作用。
- Filament lifecycleまたはcross-thread API misuse。
- Wayland/Vulkan surface/composition契約の不整合。
