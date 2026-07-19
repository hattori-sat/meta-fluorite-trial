# FLR-0002 — Capture a reproducible Mac qemux86-64 baseline

- Status: Next
- Priority: High
- Depends on: FLR-0001

## Problem

既存qemux86-64 imageはMacでFluorite初期化まで到達したが、起動command、観測結果、LLVM crashの再現条件が標準化されていない。

## Success criteria

- `FLUORITE_MAC_QEMU_TARGET=qemux86-64 make setup-macos`がPASSする。
- mini PCで生成したartifact bundleのrevision、image target、MACHINE、hash、boot parametersを固定する。
- image hashとQEMU versionを固定する。
- buildとQEMU実行を別run/evidence IDへ分離する。
- boot、SSH、compositor、Flutter、Vulkan、Fluoriteを別々に判定する。
- SIGSEGVを最低3回の同条件試行で再現性判定する。
- logとscreen evidenceを保存する。
- qemuarm64へ進む比較baselineを作る。

## Hypotheses

1. crashはx86-64 TCGがguest LLVM JIT/llvmpipe命令を扱う条件に依存する。
2. crashはFluorite/Filamentのthreadingまたはasset reuseに起因し、CPU backendに依存しない。

## PDCA

### Plan

FLR-0001完了後に具体化する。mini PC上の既存imageを変更せずartifact identityを採取し、Macへallowlist転送してから観測を始める。公式Linux `runqemu` commandをMacへそのまま移植せず、artifactとboot contractを抽出する。

### Do

Not started.

### Check

Not started.

### Act

Not started.
