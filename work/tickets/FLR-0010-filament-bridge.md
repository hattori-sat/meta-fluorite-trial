# FLR-0010 — Trace Dart filament_scene to native Filament

- Status: Next
- Priority: High
- Depends on: FLR-0008

## Purpose

Dart API、generated messages、native plugin、Filament Engine、surface/textureのcall pathを特定する。

## Success criteria

- plugin source revisionを固定する。
- plugin registrationとFilament Engine creationを特定する。
- command/event channelとthread handoffを分類する。
- asset/material loadingとFilament version compatibilityを確認する。
- render target、swapchain、surfaceまたはexternal textureのownershipを示す。

## Competing implementation hypotheses

1. Filamentは独立Wayland/Vulkan surfaceへ直接描画する。
2. FilamentはFlutter compositorへ渡すtexture/backing storeへ描画する。

sourceとruntime evidenceで判別する。
