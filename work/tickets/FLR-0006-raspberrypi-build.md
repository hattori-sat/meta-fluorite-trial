# FLR-0006 — Rebuild and validate the Raspberry Pi 4 image

- Status: Next
- Priority: High
- Depends on: FLR-0003, FLR-0004

## Problem

既存Raspberry Pi imageはあるが、canonical repositoryから同じlayer/revision/cacheを用いて再build・実機検証できることが未証明。

## Success criteria

- build runbookを追加する前に、ticket/source identity、実効`DL_DIR`/`SSTATE_DIR`/`TMPDIR`容量、外部BitBake process、environment setupをpreflightする。
- real buildはasync start/status/log/cancelだけを使い、MCPの同期tool timeoutへ依存しない。
- `raspberrypi4-64` imageを既存cache再利用でbuildする。
- kernel/rootfs/disk image、boot parameter、package manifest、revision、byte size、SHA-256をartifact inventoryとして生成する。
- boot、display、input、Wayland、Vulkan、Flutter、Fluoriteを検証する。
- QEMUで得たcountermeasureが実機へ不要な副作用を持たないと確認する。
