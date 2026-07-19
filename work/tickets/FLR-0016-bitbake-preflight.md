# FLR-0016 — BitBake preflight and existing cache identity

- Status: Waiting — metadata observed; provenance incomplete
- Priority: High
- Depends on: FLR-0001, FLR-0006, FLR-0007
- Contexts: AGL, Yocto, Fluorite demo

## Purpose

既存 AGL checkout と cache を再利用し、MACHINE・manifest・layer・conf・cache identity を混同せずに、Fluorite image の最小 BitBake 観測経路を固定する。

## Scope

- Mini PC の既存 `$AGL_ROOT` checkout、build directory、manifest、layer、conf、cache の read-only preflight。
- `agl-ivi-image-flutter` に対する最小 metadata/parse/effective-value observation。
- build host role、source identity、cache identity、log locator の handoff。

Build、deploy、QEMU、Raspberry Pi 書き込みは、preflight success criteria を満たした後に段階的に承認する。

## Success criteria

- targetごとに `MACHINE`、`DISTRO`、`DL_DIR`、`SSTATE_DIR`、`TMPDIR`、manifest identity を分離して記録する。
- existing cache reuse の可否を cache identity と target compatibility の根拠付きで判定する。
- qemux86-64、qemuarm64、raspberrypi4-64 の conf矛盾を明示し、誤った build directory を使わない。
- 最小の BitBake observation（metadata/parse/effective values）を bounded evidence として保存する。
- 長時間 build に進む前に、残る UNKNOWN、runtime/packaging/integration risk、次の承認点を記録する。

## Initial facts

- `build-flourite` は Raspberry Pi 用の設定を含み、既存 `tmp` は deploy artifact 未確認。
- `build-flourite-qemuarm64` は local.conf の MACHINE 設定と directory 名の整合性が UNKNOWN。
- qemux86-64 用の専用 cache root は存在確認が不足している。
- shared download/sstate cache は存在するが、異なる MACHINE に安全に共有できることは未証明。

## Hypotheses and disproof conditions

1. shared downloads は target 間で再利用可能。反証は fetcher identity、mirror、license/source state の target-specific divergence。
2. sstate は一部 task だけ target 間で再利用可能。反証は MACHINE/TUNE/PACKAGE_ARCH/GPU backend の異なる signatures。
3. `build-flourite` を qemux86-64 観測へ流用できる。反証は effective MACHINE、layer selection、TMPDIR lock、sstate signature の不一致。

## Smallest next action

既存 conf/include、fixed manifest、layer status、cache directory identity を read-only で採取し、正しい qemux86-64 preflight environment を決める。BitBake はその後、短時間の read-only metadata observation から開始する。

## First BitBake observation

### Facts

- 既存 Raspberry Pi build directory で `bitbake -e agl-ivi-image-flutter` を実行し、exit 0 を確認した。
- 実効値は `MACHINE=raspberrypi4-64`、`DISTRO=poky-agl`、`PN=agl-ivi-image-flutter`、`PV=1.0`。
- 実効 `AGL_FEATURES` は aglcore、agl-flutter、agl-kuksa-val、agldemo、agl-app-fw を含む。
- `IMAGE_INSTALL` に Toyota packagegroup、Fluorite関連 shell environment、Vulkan loader、Mesa Vulkan drivers、Vulkan tools が含まれる。
- `bitbake -e` は metadata/effective-value observation のみで、image build、deploy publish、QEMU、target mutation は行っていない。

### Inferences

- canonical repository の meta-local customization は、少なくとも Raspberry Pi image metadata へ到達している。
- 既存 RPi cache/tmp は同じ `MACHINE` の再検証候補だが、現在の source revision と完成 image の provenance が一致することは未確認。

### Unknowns

- BBLAYERS の全 layer revision と canonical fixed manifest の一致。
- current source tree と既存 deploy artifact の exact SRCREV/image digest 対応。
- qemux86-64 専用 environment の cache hit rate と parse success。

### Smallest next action

BitBake output から BBLAYERS、layer revision、Fluorite recipe append の bounded evidence を抽出し、RPi build を再利用するか qemux86-64 専用 buildへ進むかを判定する。

## Observation result

- `bitbake -e agl-ivi-image-flutter`: exit 0。
- Effective target: `MACHINE=raspberrypi4-64`, `DISTRO=poky-agl`, `PN=agl-ivi-image-flutter`, `PV=1.0`。
- Effective AGL features include `agl-flutter`, `agl-kuksa-val`, `agldemo`, and `agl-app-fw`.
- Image metadata includes Toyota packagegroup, `agl-driver-shell-env`, `vulkan-loader`, `mesa-vulkan-drivers`, and `vulkan-tools`.
- `BBFILE_COLLECTIONS` includes `meta-local`, `vulkan-layer`, `agl-flutter-layer`, `flutter-layer`, and `flutter-apps-layer` among the resolved collections.

This is metadata evidence only. It does not prove source revision equivalence with the existing deploy artifact or successful runtime rendering.

## Identity limitation

### Facts

- Mini PC で `repo manifest -r` は exit 127。`repo` command が利用できず、現在の checkout 全体の manifest identity は取得できない。
- `meta-vulkan`、`meta-agl-demo`、`external/poky`、`self-install/meta-flutter` の一部 revision は取得できた。
- `self-install/meta-flutter/conf/include/common.inc` に未commit変更が1件ある。

### Decision

今回の `bitbake -e` は「現在の build tree の metadata observation」として扱い、canonical fixed manifest と一致した source evidence や clean baseline の証明には使わない。既存 source の変更を戻したり、`repo sync` したりしない。

### Unknowns

- 完全な repo manifest identity。
- dirty `meta-flutter` change の内容と、effective metadata への影響。
- current build tree と canonical repository の meta-local/layer provenance の一致。

## QEMU-first observation

### Facts

- Mini PC の `build-flourite-qemux86-64` は `MACHINE=qemux86-64`、`DISTRO=poky-agl`、専用の `downloads`、`sstate-cache`、`tmp` を持つ。
- 同じ qemux86-64 cache root と deploy directory に、Fluorite demo package、Flutter Engine 3.38.3、Vulkan loader、Mesa Vulkan drivers、Vulkan tools を含む既存 artifact がある。
- Mac の既存 qemux86-64 artifact を `-snapshot` disk mode で QEMU 11 に渡し、q35、TCG multi-thread、4 vCPU、2 GiB memory、serial console、user networking で起動した。
- guest は Linux 6.6.111-yocto-standard、systemd、AGL compositor/applaunchd を起動し、AGL login prompt へ到達した。QEMU は monitor 経由で正常終了し、disk image への永続書込みは行っていない。
- この観測は guest boot/service baseline であり、`-display none` のため Fluorite scene の3D描画成功を示さない。
- 過去の別記録には、Flutter scene 初期化後に llvmpipe 上の `libLLVM.so.18.1` SIGSEGV が記録されている。今回の serial-only boot で再現した事実ではない。

### Inferences

- qemux86-64 は、既存 cache と deploy artifact を使って長時間 build を避けながら、Mac 側の QEMU boot baseline を先に固定できる。
- boot/service 成功と scene rendering 成功は別 acceptance gate として扱う必要がある。

### Hypotheses and disproof conditions

1. GUI display を有効にした同じ artifact で、AGL compositor と Fluorite app の起動観測まで進められる。反証は guest display initialization failure、app launch failure、または再現性のある renderer crash。
2. 過去の LLVM crash は qemux86-64 の software Vulkan/llvmpipe 経路に依存する。反証は display 有効化した再観測で同じ crash が発生しない、または別 backend でも同じ fault が出ること。

### Unknowns

- GUI 起動時に Fluorite app が自動起動するか、また scene readiness をどの evidence ID で判定するか。
- 現在の Mac artifact と Mini PC 側 artifact の exact source revision/digest 対応。
- QEMU display 経路で Vulkan device、surface、frame presentation が成立するか。

### Evidence IDs

- `E-FLR0016-BB-001`: Raspberry Pi build の bounded `bitbake -e` effective values。
- `E-FLR0016-ID-001`: Mini PC checkout の manifest command unavailable と dirty meta-flutter evidence。
- `E-FLR0016-QEMU-001`: qemux86-64 deploy/package inventory と dedicated cache identity。
- `E-FLR0016-QEMU-002`: Mac QEMU snapshot serial boot が AGL login prompt へ到達した観測。
- `E-FLR0016-QEMU-003`: historical llvmpipe/libLLVM crash record（現 run の再現ではない）。

### Smallest next action

同一 artifact を保護付き disk mode のまま短時間 GUI 起動し、display/compositor/app launch の最初の観測点を採取する。scene rendering の判定は、ready signal または画面 evidence が得られるまで UNKNOWN とする。

## GUI observation result

### Facts

- 同一 qemux86-64 artifact を `-display cocoa` と `-snapshot` で起動した。
- guest は systemd、AGL compositor、`applaunchd.service`、AGL login prompt まで到達した。
- serial output に Fluorite scene ready signal、Flutter renderer initialization、または renderer crash は現れなかった。
- QEMU は約30秒のbounded observation 後、monitor exit で正常終了した。

### Decision

GUI window の生成と compositor service 起動は確認できたが、画面キャプチャまたは app readiness がないため、Fluorite 3D rendering は UNKNOWN のままとする。

### Smallest next action

アプリ起動経路（`applaunchd` registry/launcher contract）を read-only で特定し、同じ snapshot artifact に対する明示的な app launch と ready-signal capture を bounded command として設計する。
