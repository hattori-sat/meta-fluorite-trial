# FLR-0009 — Understand Flutter Engine and the ivi embedder contract

- Status: Next
- Priority: High
- Depends on: FLR-0007, FLR-0008

## Purpose

Flutter AOT bundleがlauncherへ読み込まれ、thread、renderer、Wayland surface、platform messageをどう扱うか特定する。

## Success criteria

- Engine version/source revisionとYocto recipeを結ぶ。
- launcherからEmbedder APIまでのstartup sequenceを示す。
- UI/platform/render threadとtask runnerのownershipを示す。
- EGL/Vulkan backend選択条件と実効backendを確認する。
- Filament pluginとのcomposition境界を特定する。

## Root-cause guard

Engine、launcher、plugin、Mesaのどこで最初に異常が現れるかを分けるまで、Flutter Engine自体を原因と断定しない。
