# FLR-0012 — Establish the component MCP shared contract

- Status: Implemented; live identity acceptance pending
- Priority: Medium
- Depends on: FLR-0007, FLR-0008
- Context: [MCP context control](../context/mcp-context-control.md)

## Purpose

AGL、Yocto、Fluorite、Flutter runtime、Filament、graphicsを別MCPとして保ったまま、明示されたsource/image identity、bounded output、evidence linkの共通contractを定める。

## Success criteria

- source rootをallowlistし、contextのsubjectとrevision/image identityをrole-local configで宣言する。未設定時はidentity不足を明示する。
- domain vocabularyとsource rootは各serverが所有する。
- default responseをsummaryとevidence IDに限定する。
- source excerptに行数上限とpaginationを持たせる。
- arbitrary shell、write、network fetchを公開しない。
- privacy checkerとaudit recordを通す。

## Implemented contract

- contextごとにcatalog/search/read tool名とdomain payloadを所有する。
- shared kernelはopaque cursor、bounded byte/line cap、redaction、stable evidence ID、audit hookだけを提供する。
- response envelopeはcontext、operation、subject、revision/image identity、identity status、observation time、unknowns、evidence IDs、truncation、warning、next query、redaction policyを共有する。
- evidence IDへsubject/revision identityを含め、identityが変われば同じpayloadでもIDを分ける。
- source occurrenceをfactとして返し、原因推論はticketへ分離する。

## Installation decision

prototypeはMac上のstdio MCPとして実装する。serverはbounded contextごとに分離し、transport、pagination、redaction、evidence envelopeだけをshared kernelにする。build host側CLI追加は現時点で不要。必要性はSSH latency、index size、event-stream要件を測ってから再判定する。

AGL、Yocto、command runnerはLinux build roleへfixed SSH stdioで接続し、他5 contextはMac-localにする形へtransportだけを拡張した。domain contractの分離は維持する。

## Check

- 全8 serverのinitialize/tools/list/bounded tools/call: PASS。
- traversal、symlink escape、pagination、redaction、evidence ID: PASS。
- identity field、missing-identity UNKNOWN、identity-scoped evidence ID: PASS。
- fresh Codex taskでのcustom-agent override reload: UNKNOWN。
- configured identityと実source/artifactの照合はremote acceptanceまでUNKNOWN。複数rootはcombined manifest/digestを使う。
