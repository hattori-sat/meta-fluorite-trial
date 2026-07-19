# FLR-0014 — Build an allowlisted command-runner MCP

- Status: Implemented; remote acceptance pending
- Priority: High
- Depends on: FLR-0001, FLR-0004, FLR-0013
- Context: [MCP context control](../context/mcp-context-control.md)

## Purpose

環境source、dry run、状態確認、log要約を定型runbookへ固定し、agentが長いshell commandを毎回再生成する量と誤操作riskを下げる。

## Success criteria

- runbook IDとtyped parameterだけを受け付け、任意command文字列を受け付けない。
- read-only、metadata-write、build、target mutation、destructiveを別classとして表示する。
- state-changing runbookはdry-run default、dual host gate、fresh plan confirmation、MCP approvalを要求する。
- command、cwd、timeout、exit status、bounded output、evidence IDを記録する。
- long-running operationをstart/status/log/cancelへ分け、serverが起動したprocessだけを所有する。
- MacからLinux build roleへはfixed SSH stdioを使い、任意remote commandを受け付けない。
- `cleanall`、`cleansstate`、cache削除、`repo sync`を公開しない。

## Initial runbooks

`repository-baseline`、`host-capacity`。

実際のIDとeffect classは[runbook policy](../../runbooks/README.md)を正とする。

## Implemented transport

- Mac側の`.fluorite-mcp/remote-role.conf`とLinux側の`.fluorite-mcp/config.json`はGit対象外にする。
- remote wrapperは`agl`、`yocto`、`command_runner`だけを許可する。
- Linux roleはcanonical cloneとPython 3.10+を使い、Codex CLIを必要としない。
- real executionはMac gate、Linux gate、plan confirmation、tool approvalの4条件を要求する。
- plan/startは`FLR-NNNN` ticket IDを要求し、ticketをconfirmationとrun IDへbindingする。
- runtimeはmetadata-write runbookを同期実行せずasync `start_runbook`に限定するが、initial catalogではlong-running state changeを公開しない。
- environment setupがnon-zeroならcommandを起動しない。
- run recordとcompletion lifecycle auditはplan ID/digest、working root role、timeout、return status、output byte/digest/truncationを保持する。

## Unknowns

- mini PCのcanonical cloneをpush後の同一commitへ更新し、remote protocol smokeを通した結果はUNKNOWN。
- server再起動後のrun resumeとdistributed process ownershipはUNKNOWN。
- generic call auditの`ok`はhandler受付を表す。別のcompletion lifecycle eventがprocess outcome/digestを記録するが、server異常終了時のcompletion欠落検出は未実装であり、long-running catalog公開前のacceptanceとする。
- effective `bitbake -e`はallowlisted variableの完全captureが未実装、image buildはdisk/process preflightとartifact inventoryが未実装のため、initial catalogへ公開しない。
- parse/dry-runを含むlong-running operationは、MCP/SSH終了時のprocess cleanupまたはpersistent supervisor/lock/reattach contractが未検証のため、initial catalogへ公開しない。
