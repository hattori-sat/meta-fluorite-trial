# FLR-0006 — Rebuild and validate the Raspberry Pi 4 image

- Status: Next
- Priority: High
- Depends on: FLR-0003, FLR-0004

## Problem

既存Raspberry Pi imageはあるが、canonical repositoryから同じlayer/revision/cacheを用いて再build・実機検証できることが未証明。

## Success criteria

- `raspberrypi4-64` imageを既存cache再利用でbuildする。
- manifestとimage hashを記録する。
- boot、display、input、Wayland、Vulkan、Flutter、Fluoriteを検証する。
- QEMUで得たcountermeasureが実機へ不要な副作用を持たないと確認する。
