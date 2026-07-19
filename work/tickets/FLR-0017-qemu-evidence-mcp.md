# FLR-0017 — QEMU Fluorite evidence observer

- Status: In Progress — Check
- Priority: High
- Depends on: FLR-0002, FLR-0005, FLR-0008, FLR-0016
- Contexts: Target Validation, Flutter runtime, Graphics, Fluorite demo

## Feature boundary

このticketは`feature-flr-0017-qemu-evidence-mcp`の唯一のoutcomeであり、Target Validationのread-only QEMU session evidenceを完成させる。QEMU起動はExecution context、scene meaningはFluorite context、renderer meaningはGraphics/Flutter contextへhandoffする。

## Purpose

既存のQEMUノウハウを失わず、artifact identity、boot、explicit `flutter-auto` launch、Vulkan/Wayland swapchain、native readiness、Filament scene creation、crash/coredumpをbounded evidenceとして採取する。QEMU実行そのものと、Fluorite/Flutter/Graphicsの解釈を混ぜない。

## 4W1H

- What: qemux86-64のbootからFluorite scene initializationまでのvalidation evidence。
- Where: MacのQEMU target role。Linux build/cache roleとは別session。
- When: artifact manifestとQEMU launch contractが固定されたvalidation session。
- Who: target-validatorが観測、Fluorite/Flutter/Graphics investigatorが各domainを解釈、PDCA checkerが判定を監査。
- How: read-only evidence MCP、または登録済みbounded runbookを通じて、snapshot disk、bounded timeout、固定bundle path、serial log、screen/coredump locatorを保存する。

## Legacy evidence facts

- `$LEGACY_ROOT/docs/mac-qemu.md`にはq35、TCG multi-thread、4 vCPU、2 GiB、`virtio-vga`、Cocoa display、serial monitor、user networkingのlaunch contractがある。
- 同資料では、shellから`su - agl-driver`後に`flutter-auto -b <bundle>`を明示起動している。bundleはFluorite demo AOT assetを含む。
- 実測ログにはFlutter EngineのVulkan backend、llvmpipe Mesa 24.0.7 / LLVM 18.1.8、1280x720 swapchain、native readiness、`poGetFilamentScene onCreated`、event channels createdが順に現れる。
- その後、`FEngine::loop`が`libLLVM.so.18.1`内でSIGSEGVし、`coredumpctl`で`flutter-auto`のcoreを確認している。
- これはlegacy artifact/sessionの証拠であり、現在のartifactで再現した事実ではない。

## Facts / Inferences / Hypotheses / Unknowns

### Facts

- 現在の`target_validation` MCPは既存evidence fileのlist/read/keyword summaryを提供するが、QEMU起動、guest command、screen capture、coredump collectionは行わない。
- 現在のGUI QEMU smokeはAGL compositorと`applaunchd`まで到達したが、explicit app launchとscene evidenceを採取していない。
- `$LEGACY_ROOT`はroot Git repositoryではなく、nested source repositoriesとartifact/docsを含む参照directoryである。raw qemuboot/testdataにはhost固有absolute pathがあるため、そのままGitへ取り込まない。
- legacy RPi notesには、native pluginなしのplatform-view registration failure、V3DVでのnative readiness/asset load、material version mismatch、Mesa BO allocation failureが記録される。これらはqemux86-64 LLVM crashとは別target/sessionである。

### Inferences

- FLR-0005のtarget validation MCPを、QEMU-specific launch/evidence contractへ分解して実装する必要がある。
- `boot health`、`graphics capability`、`demo readiness/render`、`crash diagnosis`を別caseにしないと、過去のLLVM crashを描画失敗一般へ誤って拡張する。

### Hypotheses and disproof conditions

1. 過去のSIGSEGVはqemux86-64 TCG + llvmpipe Vulkanのscene rendering経路で再現する。反証は同一artifact/contractでscene ready後もbounded interval安定すること。
2. 明示的`flutter-auto`起動が必要で、AGL compositor/applaunchd起動だけではdemo validationに到達しない。反証は自動launcherが同じbundleを起動し、同じready evidenceを生成すること。
3. swapchain/surface成立はrender successの必要条件だが十分条件ではない。反証はswapchain evidenceなしでもscreen/scene acceptanceが成立すること。

### Unknowns

- 現artifactのbundle path、launch user、launcher registry、screen capture方式。
- app launchをQEMU guest内でどの固定runbookとして許可するか。
- coredumpをsnapshot終了前に安全に回収できるか。
- QEMU image/source/artifact exact identityとlegacy evidenceの対応。
- legacy qemubootのduplicate VGA optionsとdocsの`virtio-vga` profileをどの正規launch profileへ統合するか。

## Smallest next action

legacy contractを入力に、まずread-onlyの「artifact/session identity + launch plan + evidence locator」MCP schemaを設計する。次に、明示承認付きの短時間QEMU launch runbookを別ticket/Execution contextで追加し、current artifactではboot、explicit app launch、ready/crash signalの順に一回だけ観測する。

## QEMU analysis MCP boundary

- 新しいbounded domain `qemu` は作らず、QEMUをTarget Validationのtarget roleとして扱う。
- read-only MCPは、indexed `ImageArtifactManifest`、`ValidationSession`、qemuboot metadata、bounded serial/journal/app log、optional screen locatorを入力にする。
- 最小operationは `summarize_qemu_boot`、`summarize_app_launch`、`summarize_render_case`、`read_target_evidence`。出力はcase-level `PASS`/`FAIL`/`UNKNOWN`、expected-vs-actual signals、negative results、evidence IDsとし、原因を断定しない。
- app signalにはApplication Id/Bundle Path、Vulkan backend/device、swapchain、asset/material read、`Native is ready`、Event Channels、platform-view registration、SIGSEGV/abort/Postcondition/BO allocationを含める。
- QEMU/app起動は`command_runner`のregistered target-mutation runbookだけが担当し、analysis MCP自身は起動・SSH・BitBake・cache変更を行わない。

## Acceptance criteria

- QEMU runはartifact identity、QEMU version、machine/accelerator/CPU/display/GPU/network/input/kernel args、timeout、snapshot modeを記録する。
- guest boot/service、explicit app launch、graphics/Vulkan、Fluorite readiness/render、crash/coredumpを別evidence IDsへ分離する。
- `PASS`はready signalまたはscreen evidenceがある場合だけ、crash/absence/identity不足は`FAIL`または`UNKNOWN`として返す。
- MCPは任意shellを受け付けず、target mutationはExecutionのregistered runbookとapprovalへ分離する。
- legacy evidenceをcurrent runの事実として再利用せず、revision/image/session identityを明示する。

## Candidate launch profile (plan, not yet executed)

- Target role: `qemux86-64-macos-tcg`.
- Artifact inputs: existing indexed kernel/rootfs/qemuboot metadata; no artifact recopy.
- Machine: q35; accelerator: TCG multi-thread; CPU: qemu64 with the legacy feature flags; memory: 2048 MiB; vCPU: 4.
- Display/input: Cocoa, virtio-vga, serial monitor, USB tablet/keyboard; network: user-mode with no host forwarding unless explicitly required.
- Disk safety: ext4 rootfs with `snapshot=on`; never write the source artifact.
- Timeout: 90 seconds for boot/app readiness, with a separately approved 600-second soak only if readiness succeeds.
- Guest action: explicit `flutter-auto -b <indexed-Fluorite-bundle>` under the target's registered launcher user and Wayland session environment. Bundle path/user must be observed from the current image before execution, not copied from legacy assumptions.
- Evidence outputs: serial log, QEMU/boot parameters, app log markers, optional screen locator, and coredump locator. Store only bounded session evidence beside the existing QEMU artifact; do not duplicate kernel/rootfs.

Execution remains blocked until the current artifact's bundle path, launch user, Wayland variables, and evidence output directory are read-only confirmed.

## Current artifact read-only preflight

### Facts

- Current qemux86-64 manifest contains `flutter-auto` 2.0, `agl-driver-shell-env`, and `toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo`.
- Current testdata includes `packagegroup-agl-ivi-services-applaunchd`, `vulkan-loader`, `mesa-vulkan-drivers`, and `vulkan-tools`.
- Host-side rootfs inspection tools for ext4 are unavailable on the Mac role; no rootfs mount, copy, or mutation was attempted.

### Resolved facts

- Guest bundle path, launcher user (`agl-driver`), `XDG_RUNTIME_DIR=/run/user/1001`, and `WAYLAND_DISPLAY=wayland-0` were confirmed during the bounded session.
- The session log and hash are indexed in `work/evidence/FLR-0017-qemu-session.md`.

### Remaining unknowns

- A persistent coredump locator and screen capture locator were not collected before the snapshot session ended.
- QEMU parameter/session metadata is currently indexed manually; FLR-0018 must emit it as a sidecar.

## Current QEMU validation result

### Evidence IDs

- `E-FLR0017-QEMU-005`: current qemux86-64 snapshot session, role locator `$QEMU_ARTIFACT_ROOT/flr0017-qemu-session.log`, SHA-256 `0762b170ae9ec08efa5c0692711c31065c8cb3b5366d31f39fb393d3c1544f71`.
- `ev-target-validation-612fdcf462b63a9f6d53`: bounded `summarize_app_launch` response with sufficient image/session identity.
- `ev-target-validation-89d0d234a95761ba762b`: bounded `summarize_render_case` response with sufficient image/session identity.

### Facts

- Guest boot reached AGL compositor, `applaunchd`, login prompt, and active `agl-driver` Wayland session (`/run/user/1001/wayland-0`).
- Current image contains and successfully launched the Fluorite bundle as `agl-driver` with `XDG_RUNTIME_DIR=/run/user/1001` and `WAYLAND_DISPLAY=wayland-0`.
- App evidence includes Application Id `fluorite`, Flutter Engine Vulkan backend, llvmpipe Mesa 24.0.7 / LLVM 18.1.8, Filament initialization, swapchain creation, native readiness, and event channels.
- The process then terminated with `FEngine::loop` SIGSEGV in `libLLVM.so.18.1` after approximately 74 seconds. This reproduces the legacy failure signature on the current artifact/session profile.

### Verdict

- Boot/service: PASS.
- Explicit app launch/readiness: PASS.
- Render initialization: OBSERVED, not a stable render PASS.
- Stable Fluorite 3D rendering: FAIL for this session because the renderer process crashed after readiness.
- Root cause: UNKNOWN; the evidence is consistent with the llvmpipe/LLVM hypothesis but does not prove causality.

### Handoff

- FLR-0018 owns conversion of this manual launch into a registered Execution runbook. Flutter runtime, Graphics, and Fluorite investigators receive only the bounded evidence IDs and role locators.
