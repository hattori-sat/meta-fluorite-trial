# Task dashboard

Last updated: 2026-07-19

## Current focus

**[FLR-0008 — Understand the Fluorite demo](work/tickets/FLR-0008-fluorite-demo.md)**

WIP limit: 原則`In Progress`は1件。緊急割込みは理由をworking logへ残す。

## In Progress

| ID | Problem / outcome | Owner | PDCA | Next action |
| --- | --- | --- | --- | --- |
| FLR-0008 | Fluorite 3D demoの成功状態とscene/native境界が未固定 | Fluorite investigator + checker role | Plan | target別に観測可能な3D成功指標を定義し、demo entrypointとassetを固定revisionから追う |

## Next

FLR-0008で最終目的であるFluoriteの成功状態を先に定義し、その後FLR-0007でAGL組立process、FLR-0009〜0011で下位描画stackを追う。PDCA Checkで順序は再評価する。

| ID | Problem / outcome | Depends on |
| --- | --- | --- |
| [FLR-0002](work/tickets/FLR-0002-mac-qemu-baseline.md) | Macで既存qemux86-64の再現可能な起動baselineを採る | FLR-0001 |
| [FLR-0003](work/tickets/FLR-0003-qemuarm64-hvf.md) | qemuarm64 + HVFがMac検証の主経路になるか判定する | FLR-0002 |
| [FLR-0004](work/tickets/FLR-0004-yocto-observer-mcp.md) | build hostのYocto状態を安全に観測するread-only MCPを作る | FLR-0001 |
| [FLR-0005](work/tickets/FLR-0005-target-validation-mcp.md) | QEMU/実機の証拠収集を標準化するvalidation MCPを作る | FLR-0002 |
| [FLR-0006](work/tickets/FLR-0006-raspberrypi-build.md) | 固定baselineからRaspberry Pi 4 imageを再build・検証する | FLR-0003, FLR-0004 |
| [FLR-0007](work/tickets/FLR-0007-agl-architecture.md) | AGLがimage、compositor、launcher、appを組み立てるprocessを固定revisionから理解する | FLR-0001 |
| [FLR-0009](work/tickets/FLR-0009-flutter-engine-embedder.md) | Flutter Engineとivi launcherの描画・thread・surface契約を理解する | FLR-0007, FLR-0008 |
| [FLR-0010](work/tickets/FLR-0010-filament-bridge.md) | Dart APIからnative filament_viewとFilamentまでのcall pathを特定する | FLR-0008 |
| [FLR-0011](work/tickets/FLR-0011-vulkan-gpu-stack.md) | Filament/FlutterからVulkan、Mesa、GPUまでの実効経路をtarget別に特定する | FLR-0009, FLR-0010 |
| [FLR-0012](work/tickets/FLR-0012-source-knowledge-mcp.md) | component別MCPのshared contractを固定する | FLR-0007, FLR-0008 |
| [FLR-0013](work/tickets/FLR-0013-agl-observer-mcp.md) | AGLのmanifest、feature、image組立をYoctoから分離して観測する | FLR-0001 |
| [FLR-0014](work/tickets/FLR-0014-command-runner-mcp.md) | allowlist runbookだけを実行するcommand MCPを作る | FLR-0001, FLR-0004, FLR-0013 |

## Waiting

- [FLR-0001](work/tickets/FLR-0001-canonical-repository-baseline.md): foundation deliveryはPASS。Linux build roleの同一revision checkout、remote MCP、GitHub CI/repository settingsのacceptance待ち。
- push後、canonical cloneをproject rootにしたfresh Codex taskでcustom-agent/MCP routingをsmokeする。
- 実機検証条件（Raspberry Pi 4、display、input、network）の詳細はUNKNOWN。
- GitHub repository settingsで`Branch policy / validate-branch-flow`をrequired status checkにする。

## Inbox

- `meta-agl/scripts/aglsetup.sh`のlocal変更の必要性を特定する。
- qemux86-64の`libLLVM.so.18.1` SIGSEGVを再現し、TCG/LLVM/threadingの仮説を比較する。
- qemuarm64のMesa/Vulkan/virtio-gpu package構成を確認する。
- Flutter EngineとFilamentが同一window、別surface、external textureのどれで合成されるか特定する。

## Done

- 2026-07-19: mini PCの読み取り専用baseline調査。
- 2026-07-19: Macとmini PCのclone location/origin/HEAD確認。
- 2026-07-19: foundationをrole metadata commitへ固定し、fresh clone gate後にdev/feature refsをremoteへ配布。

## Someday / Maybe

- build開始・停止を扱うwrite-capable MCP。read-only MCPが安定してから検討する。
- Raspberry Pi実機の自動電源制御、serial console、screen capture連携。
