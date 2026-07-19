# Task dashboard

Last updated: 2026-07-20

## Current focus

**[FLR-0025 — Bounded BitBake monitor MCP](work/tickets/FLR-0025-bitbake-monitor-mcp.md)**

WIP limit: 原則`In Progress`は1件。緊急割込みは理由をworking logへ残す。

## In Progress

| ID | Problem / outcome | Owner | PDCA | Next action |
| --- | --- | --- | --- | --- |
| FLR-0025 | fixed BitBake監視からartifact/QEMU/Fluorite確認までを完遂する | primary role + build-runner + checker role | Do → Check | pseudo/tar workaroundをMini PCへ同期し、image retry後にartifact hash→SCP→QEMUへ進む |

## Active loop state

| Phase | State | Evidence / next gate |
| --- | --- | --- |
| Monitor implementation | Check | clientと別SID/PGIDのCooker/Workerをlive確認。新規server group追跡・停止test PASS |
| Git synchronization | Complete | Mac/origin/Mini PCは`157c1ed`。worktree cleanを再確認する |
| Demo compile | Complete | bounded demo compile exit 0。image input変更はdemo recipe外 |
| Image build | In Progress | pseudo/tar失敗をMini PCで再現し、project layer workaroundを追加。同期後に再実行 |
| Artifact transfer | Blocked by image | kernel/rootfsのidentity、size、SHA-256確認後、Macのactive qemux86-64 artifact directoryへ置換 |
| QEMU / Fluorite | Blocked by transfer | snapshot QEMU、`agl-driver` Wayland session、explicit `flutter-auto -b <bundle>`、readiness/render/crash判定 |
| Failure loop | Ready | build/log/QEMU/app/renderの層を分離し、最小修正後にcompileから再開 |

## Next

FLR-0025のみをIn Progressとする。FLR-0024はrenamed-layer metadata/patch gate済みで、FLR-0025のcompile/image acceptance待ち。FLR-0019のbuild-to-render loopはFLR-0025の固定監視runbookで再開する。devへの通常mergeはFluorite動作確認まで行わない。

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
| [FLR-0008](work/tickets/FLR-0008-fluorite-demo.md) | Fluorite 3D demoの成功状態とscene/native境界を固定する | FLR-0001, FLR-0015 |
| [FLR-0016](work/tickets/FLR-0016-bitbake-preflight.md) | 既存 AGL checkout/cache を再利用する BitBake preflight を固定する | FLR-0001, FLR-0006, FLR-0007 |
| [FLR-0017](work/tickets/FLR-0017-qemu-evidence-mcp.md) | legacy QEMU contractをbounded evidence observerへ落とし込む | FLR-0002, FLR-0005, FLR-0008, FLR-0016 |
| [FLR-0018](work/tickets/FLR-0018-qemu-launch-runbook.md) | QEMU launchをregistered Execution runbookへ固定する | FLR-0017 |
| [FLR-0019](work/tickets/FLR-0019-qemu-build-iteration.md) | BitBake成果物からQEMU stable-render verdictまでを反復する | FLR-0018 |
| [FLR-0020](work/tickets/FLR-0020-self-contained-build-workspace.md) | meta-fluorite-trialだけでAGL/Yocto build workspaceを再構成する | FLR-0019 |
| [FLR-0023](work/tickets/FLR-0023-project-owned-fluorite-layer.md) | meta-fluorite-trial layerをFluorite固有実装のsource of truthとしてBitBake入力を再構成する | FLR-0021, FLR-0022 |
| [FLR-0024](work/tickets/FLR-0024-project-layer-naming.md) | legacy meta-localをmeta-fluorite-trial layerへ置き換える | FLR-0023 |
| [FLR-0025](work/tickets/FLR-0025-bitbake-monitor-mcp.md) | bounded BitBake監視MCPを追加する | FLR-0024 |

## Waiting

- [FLR-0001](work/tickets/FLR-0001-canonical-repository-baseline.md): foundation deliveryとCIはPASS。PR review/merge、Linux build roleの同一revision checkout、remote MCP、branch policyのacceptance待ち。
- push後、canonical cloneをproject rootにしたfresh Codex taskでcustom-agent/MCP routingをsmokeする。
- 実機検証条件（Raspberry Pi 4、display、input、network）の詳細はUNKNOWN。
- GitHub repository settingsで`Branch policy / validate-branch-flow`をrequired status checkにする。

## Inbox

- FLR-0016: BitBake preflight中のMACHINE/conf/cache identityを確認する（Waiting、manifest provenance UNKNOWN）。
- FLR-0017: legacy `docs/mac-qemu.md`のexplicit launch/readiness/crash evidenceをQEMU observerへ移す。
- FLR-0018: current QEMU app-launch evidenceを固定Execution runbookへ移す。
- FLR-0019: pseudo/tar packagecopy failureを切り分け、成果物ができた場合のみscp/QEMUへ進む。
- FLR-0020: `/AGL/trout` に依存しない fixed-manifest workspace bootstrap を設計する。
- FLR-0021: `meta-vulkan` add-layer有無ではなく、fixed manifestとactive meta-flutter layer topologyの不一致を比較する。

- MCP explainability contractをdomain payloadと混ぜずに運用する。

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
