# MCP architecture boundaries

## Decision

調査と実行automationを、8個のbounded contextごとのstdio MCPへ分離する。server実装はpagination、redaction、evidence IDなどのtechnical kernelだけを共有し、domain vocabularyとpayloadは共有しない。

| Server | Owned meaning | Placement | Authority |
| --- | --- | --- | --- |
| `agl` | manifest、feature、image/packagegroup、compositor/service integration | Linux build roleへ固定SSH stdio | read-only |
| `yocto` | layer、recipe、append、class、configuration、task log | Linux build roleへ固定SSH stdio | read-only |
| `fluorite` | Dart scene、asset、interaction、startup contract | Mac repository | read-only |
| `flutter_runtime` | Engine/embedder、launcher、thread、surface | Mac repository | read-only |
| `filament` | Dart/native bridge、Filament engine、material/render asset | Mac repository | read-only |
| `graphics` | Wayland、Vulkan、Mesa、DRM、GPU presentation path | Mac repository | read-only |
| `target_validation` | Mac QEMU/Raspberry Piの既存validation evidence | Mac repository | read-only |
| `command_runner` | Git管理された固定runbookのplan、実行、status、bounded log | Linux build roleへ固定SSH stdio | gated state change |

AGLは車載distributionのintegrationを、Yoctoはbuild metadataの解決を所有するため、同一serverへ統合しない。詳しい用語とhandoffは[DDD operating model](../../docs/architecture/ddd.md)と[Domain registry](../../domains/README.md)を正とする。

## Host boundary

CodexとMac QEMU検証はMac roleに置く。AGL source、Yocto build tree、BitBakeとbuild commandはLinux mini-PC roleに置く。

`agl`、`yocto`、`command_runner`だけを`scripts/run-remote-mcp.sh`で固定SSH stdio接続する。他の5 serverは`scripts/run-mcp.sh`でMac上から起動する。remote wrapperはserver ID、SSH role alias、repository pathをallowlist検証し、任意remote commandを受け取らない。

Linux roleにはCodex CLIを導入しない。canonical clone、SSH、既存Python 3.10+だけをruntime contractとし、実pathと接続情報はGit-ignored role configurationに保存する。

## Execution boundary

最初の7 serverはcommandを起動せず、登録root内の既存source/log/evidenceだけを読む。状態変更は`command_runner`へ隔離し、次をすべて満たした場合だけ実行する。

1. Git管理されたrunbook IDとfinite typed parameterである。
2. Mac roleとLinux roleのexecution gateが両方有効である。
3. `plan_runbook`が発行した未期限切れplan IDをconfirmationとして渡す。
4. MCP hostがstate-changing toolを明示承認する。

`command`、任意`argv`、任意`cwd`、任意setup scriptはtool inputにしない。`repo sync`、`cleanall`、`cleansstate`、cache削除は公開しない。long-running operationは`start_runbook`、`get_run_status`、`read_run_log`、`cancel_run`でprocess ownershipを保つ。

## Evidence contract

responseは`bounded_context`、`operation`、`observed_at`、domain固有`payload`、`unknowns`、`evidence_ids`、`truncated`、`warnings`、`next_queries`を持つ。MCPは原因推論を返さない。raw source/logはbounded readとopaque paginationで必要範囲だけ返し、ticket側でfacts、inferences、hypothesesを分離する。

## Agent routing

primary roleでは全serverをdefault disabledにする。custom investigatorは担当serverだけを有効化する。build runnerだけが`command_runner`を受け取り、PDCA checkerはexecution toolを持たない。設定のsource of truthは[project MCP configuration](../../.codex/config.toml)と[agent routing guide](../../docs/agents.md)である。

## Compared paths

1. Macからgeneric SSH/shellを公開する方式は導入が小さいが、任意command、巨大output、秘密情報、ownership喪失のriskが高い。
2. context別MCPと固定SSH stdio方式はserver数が増えるが、語彙、root、権限、failure radiusを分離できる。

2を採用した。host-local indexやpersistent supervisorが必要になるかは、実測前のためUNKNOWNである。
