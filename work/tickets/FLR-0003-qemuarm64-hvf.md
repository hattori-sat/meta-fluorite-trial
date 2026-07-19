# FLR-0003 — Decide whether qemuarm64 + HVF is the primary Mac path

- Status: Next
- Priority: High
- Depends on: FLR-0002

## Problem

Apple Silicon上のx86-64 TCGは低速でLLVM crashも観測されている。qemuarm64 + HVFがより安定した検証経路か証拠がない。

## Success criteria

- qemuarm64 imageを既存cacheでbuildできる。
- HVFでbootし、virtio GPU、Wayland、Mesa/Vulkanを確認できる。
- 同一sceneの起動時間、安定性、操作性をqemux86-64 baselineと比較できる。
- primary pathをdecision recordで決定できる。

## Hypotheses

1. HVFによるnative arm64実行はsoftware renderingでもTCGより実用的である。
2. graphics support不足により、CPU高速化だけではFluorite表示経路が成立しない。
