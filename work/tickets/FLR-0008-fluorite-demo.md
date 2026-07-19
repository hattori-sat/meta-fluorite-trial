# FLR-0008 — Understand the Fluorite demo behavior and native boundary

- Status: Next
- Priority: High
- Depends on: FLR-0001
- Context: [rendering stack](../context/fluorite-rendering-stack.md)

## Purpose

最終的に何が表示・操作できればFluorite成功なのかを、Flutter sourceとassetから定義する。

## Initial facts

- appは`fluorite_examples_demo`。
- 5種類のsceneを持つ。
- native readiness後にevent channelと初期sceneを開始する。
- Dart `filament_scene` APIを通じてmodel、camera、material、animation等を操作する。
- imported `meta-local`にはdemo用patch 3件が残るが、対応bbappendの`SRC_URI`は`config.toml`だけを参照し、現baselineではpatchはinactive。
- `agl-driver-shell-env`のrecipeは`agl-driver-env.sh`だけを参照し、同directoryの`bashrc.agl-driver`はinactive。
- `flutter-auto`のmipmap patchはcommented-out `SRC_URI`にしか現れず、現baselineではinactive。

## Success criteria

- sceneごとのasset、初期化、interaction、expected outputを整理する。
- 最小validation sceneを1つ選び、選定根拠を示す。
- Dartからnativeへ渡るAPI/messageを分類する。
- startup timelineと失敗観測点を定義する。

## Priority selection candidate

最初はassetとinteractionが比較的小さいsceneを候補にする。ただしsource計測前はUNKNOWNであり、名称だけで選定しない。

inactive fileはbuild-hostから採取したbaseline treeのintegrityを保つため、このticketでは削除・修正しない。実効metadataで非参照を確認した後、保持、削除、再有効化を別countermeasureとして判断する。patch形式の妥当性は未適用であることからruntime根拠に使わず、現時点ではUNKNOWNとする。
