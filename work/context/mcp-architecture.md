# MCP architecture boundaries

## Objective

Fluorite lab固有のYocto/QEMU/target状態を、小さく監査可能なtool contractでagentへ提供する。任意shellをMCPとして公開しない。

## Server 1 — Source knowledge

Purpose: fixed revisionのAGL、Fluorite demo、Flutter/launcher、Filament、graphics sourceをbounded evidenceとして読む。

Candidate tools:

- `list_components`
- `get_component_revision`
- `search_symbols`
- `trace_references`
- `get_recipe_relationship`
- `get_patch_targets`
- `read_evidence`

Constraints: domain必須、source root allowlist、excerpt上限、pagination、revision付きevidence ID。詳細は[MCP context control](mcp-context-control.md)。

## Server 2 — AGL/Yocto observer

Purpose: build host上のAGL manifest/layerとYocto configuration、cache、build、artifactをread-onlyで観測する。

Candidate tools:

- `get_host_baseline`
- `get_repo_revisions`
- `get_recipe_resolution`
- `get_layer_status`
- `get_build_config`
- `get_effective_bitbake_vars`
- `get_cache_usage`
- `get_build_processes`
- `list_artifacts`
- `get_image_manifest`
- `tail_task_log`

Constraints: allowlist path、output上限、secretと個人識別情報のredaction、command timeout、対象変数allowlist、全callのaudit record。responseの`host`は個別hostnameでなくrole IDを返す。

## Server 3 — Target observer

Purpose: QEMUまたはRaspberry Piから共通schemaでvalidation evidenceを取得する。

Candidate tools:

- `get_target_identity`
- `get_boot_health`
- `get_service_status`
- `get_graphics_stack`
- `get_vulkan_summary`
- `get_flutter_fluorite_logs`
- `get_input_devices`
- `capture_validation_bundle`

Constraints: targetごとの接続profile、journal取得範囲、PII/secret redaction、image identityとの紐付け。

## State-changing tools — deferred and isolated

`start_build`、`cancel_build`、`launch_qemu`、`stop_qemu`、target rebootはobserver serverへ入れない。read-only serverが安定した後、承認gate、idempotency、process ownership、timeoutを持つ別serverまたは別tool groupとして設計する。

## Transport options

1. Mac上のstdio MCPが固定SSH commandを実行する。
   - 導入が小さく、既存鍵を再利用できる。
   - Mac processがredactionとtimeoutを確実に担う必要がある。
2. build host上でMCP serverを動かす。
   - host-local観測を実装しやすい。
   - deployment、versioning、remote transport、認証の管理が増える。

PrototypeはOption 1を推奨する。ただし任意command parameterは受け取らず、固定されたqueryだけを公開する。

## Evidence contract

各responseに`observed_at`、`host`、`source_path`、`command_or_method`、`truncated`、`warnings`を含める。推論はMCP responseへ混ぜず、agentがticket上でfactsから導く。
