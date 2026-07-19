# FLR-0004 — Build a read-only AGL/Yocto observer MCP

- Status: Next
- Priority: High
- Depends on: FLR-0001
- Contexts: [MCP architecture](../context/mcp-architecture.md), [MCP context control](../context/mcp-context-control.md)

## Purpose

fixed AGL/Yocto build treeの実効状態を、任意shellや巨大outputを使わず再現可能なevidenceとして取得する。agentがSSH commandを都度組み立てることによる観測揺れ、誤操作、context肥大化を防ぐ。

## Success criteria

- read-only toolだけを公開する。
- AGL manifest/layer、Yocto recipe resolution、conf/cache/process/artifact/logを構造化して返す。
- secretをredactし、巨大outputをpageまたはsummary化する。
- tool callと対象pathを監査logへ残す。
- destructive commandをAPI surfaceに含めない。

## Candidate tools

`get_host_baseline`, `get_agl_manifest`, `get_layer_revisions`, `get_recipe_resolution`, `get_build_config`, `get_effective_vars`, `get_cache_usage`, `get_build_status`, `list_artifacts`, `get_image_manifest`, `tail_task_log`.

## Implementation paths

1. Mac上のstdio MCPが固定SSH commandを実行する。
2. build host上のMCPへremote transportで接続する。

まず1をprototypeし、権限境界と運用性を比較する。build hostへの追加CLI導入は測定上必要になるまで行わない。
