# MCP context-control design

## Objective

AGL、Yocto、Fluorite、Flutter runtime、Filament、graphics、target validation、executionの情報を混ぜず、active ticketの判定に必要なbounded evidenceだけをagentへ渡す。

## Context selection

問いを最初に一つのbounded contextへ割り当てる。

- image/feature/serviceの組立は`agl`。
- recipe/task/package/overrideの解決は`yocto`。
- scene/asset/interactionは`fluorite`。
- embedder/thread/surface/plugin hostingは`flutter_runtime`。
- bridge/engine/material/frameは`filament`。
- Wayland/Vulkan/Mesa/DRM/device/presentationは`graphics`。
- 特定artifactとsessionのboot/screen/log/input判定は`target_validation`。
- 承認済みoperationのplanとprocess ownershipは`command_runner`。

複数domainが必要な問いは一つの巨大queryにせず、evidence IDを保ったhandoffに分割する。同名語の意味は各[Domain README](../../domains/README.md)を優先する。

## Input discipline

- rootはlocal configurationのrole aliasから選び、absolute pathをtool inputにしない。
- pathはroot相対とし、`..`、symlink escape、sensitive role-config directory、unsupported extensionを拒否する。source readはoversized fileを拒否し、task-log tailだけはbounded end-windowをstreamする。
- searchはquery、file kind、page token、bounded limitだけを受け取る。
- advertised object schemaをruntimeでも検証し、未定義fieldを無視せず拒否する。
- executionはregistered runbook ID、finite enum parameter、fresh plan confirmationだけを受け取る。
- network fetch、generic shell、generic SSH、free-form environment sourceをtool surfaceへ出さない。

## Response discipline

default responseはsummaryとevidence IDだけを返す。source/log本文は明示的なread callでline/byte上限内だけを読む。

Every response:

- `bounded_context`
- `operation`
- `observed_at`
- domain-owned `payload`
- `unknowns`
- `evidence_ids`
- `truncated`
- `warnings`
- `next_queries`

source occurrenceはfactだが、failureの原因であるとは限らない。原因、反証、countermeasureはticketへ記録し、MCP payloadへ混ぜない。

## Host and privacy discipline

- Mac-local server: `fluorite`、`flutter_runtime`、`filament`、`graphics`、`target_validation`。
- Linux build-role server via fixed SSH stdio: `agl`、`yocto`、`command_runner`。
- 実hostname、account、IP、credential、個人名をrepository、response、auditへ保存しない。
- pathは`$AGL_ROOT`、`$YOCTO_BUILD_ROOT`などのrole aliasで返す。
- stdoutはJSON-RPC専用とし、diagnosticはstderrへ分離する。
- redaction後の値をerror messageへ再掲しない。

## Execution and lifecycle discipline

read-only serverとstate-changing serverを同じauthorityにしない。`command_runner`のreal executionにはdual host gate、plan confirmation、MCP approvalを要求する。async runは起動したprocess groupだけを所有し、status/log/cancelを同じserver processで扱う。

server再起動後のresume、distributed ownership、persistent event streamは現在未実装でUNKNOWNである。generic auditの`ok`はhandlerがrequestを受理した時点を表し、正常終了時は別のcompletion lifecycle eventがplan/outcome digestを記録する。server異常終了時のcompletion欠落検出は未実装である。必要性を計測するまでdaemonや新しいremote runtimeを追加しない。

## Verification

- 全8 serverでinitialize、tools/list、bounded tools/callをprotocol smokeする。
- AGLとYoctoが別tool surface・別agent accessであることをconfiguration testする。
- traversal、symlink escape、oversize、pagination、redaction、stable evidence IDをunit testする。
- runbook schema、unknown executable、dual gate、plan expiry、async status、bounded log、process cancellationをtestする。
- Mac-to-build-role wrapperは3 serverのallowlist、role config validation、shell metacharacter rejectionをtestする。

実装と運用手順は[MCP runtime](../../mcp/README.md)、handoff schemaは[evidence contract](../../docs/architecture/evidence-handoff-contract.md)を正とする。
