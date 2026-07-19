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

## Success criteria

- sceneごとのasset、初期化、interaction、expected outputを整理する。
- 最小validation sceneを1つ選び、選定根拠を示す。
- Dartからnativeへ渡るAPI/messageを分類する。
- startup timelineと失敗観測点を定義する。

## Priority selection candidate

最初はassetとinteractionが比較的小さいsceneを候補にする。ただしsource計測前はUNKNOWNであり、名称だけで選定しない。
