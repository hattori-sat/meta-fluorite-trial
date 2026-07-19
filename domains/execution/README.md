# Execution / Runbooks bounded context

## Purpose

Environment source、metadata evaluation、build、QEMU/target operationを、登録済みrunbook、parameter schema、risk class、approval、process ownership、bounded logとして安全かつ再現可能に実行する。domain上の意味付けは各contextへ返す。

## Ubiquitous language

| Term | Meaning in this context |
| --- | --- |
| runbook | Git管理された固定operation manifest。任意shell文字列ではない。 |
| plan | precondition、resolved parameter、予定command class、予想side effect。実行ではない。 |
| dry-run | planを返し、実operationを開始しないmode。underlying toolの`-n` optionとは同義でない。 |
| environment profile | source scriptとbuild directoryをrole/allowlistで参照するlocal configuration。 |
| risk class | `read_only`、`metadata_write`、`build`、`target_mutation`のauthority分類。 |
| approval | exact plan/risk/targetに対する実行許可。credentialとして保存しない。 |
| run ID | plan、process、log、outcomeを結ぶopaque identity。 |
| process owner | start、monitor、cancel、cleanupを担当するrole/session。 |
| bounded log | cursor、size limit、redactionを持つrun output。 |

## Inputs

- Registered runbook ID。
- Enum/allowlistで検証されたdomain parameters。
- Git対象外のenvironment/connection profile。
- Risk classに応じたapprovalとticket ID。
- Expected artifacts/evidence signals。

## Outputs

- Resolved plan、precondition result、declared side effects。
- Run ID、status、duration、process ownership。
- Cursor付きbounded/redacted logとartifact/evidence references。
- Actual side effects、exit status、cancellation/timeout result。

## Invariants

- Yocto setup/build runbookはLinux build host roleだけを対象にし、Macでは計画またはQEMU validation runbookだけを扱う。
- Arbitrary command、script path、environment assignment、SSH destinationをinputとして受け取らない。
- `source`はallowlisted environment profileを固定wrapper内で処理する。
- Dry-runは実行しない。`bitbake -n`や`bitbake -e`はmetadata/log/lockを書き得るため`metadata-write`に分類する。
- real executionはriskにかかわらずplanと明示approvalを必要とする。
- downloads、sstate-cache、tmpの削除、`cleanall`をrunbookとして公開しない。`cleansstate`も通常catalogへ入れない。
- Secretsと個人識別情報をenvironment dump、command echo、log、artifact pathへ出さない。
- Execution successはdomain successではない。exit statusとevidenceをsource contextへ返す。

## Risk classes

| Class | Examples | Authority |
| --- | --- | --- |
| `read_only` | fixed source/artifact identity、既存log range | plan確認と明示承認 |
| `metadata_write` | environment setup、BitBake parse、`bitbake -e`、`bitbake -n` | plan確認と明示承認 |
| `build` | compile、package、image build | resource確認、plan、明示承認 |
| `target_mutation` | QEMU launch/stop、service restart、reboot | target scope、rollback、明示承認 |

Destructive operationは公開対象外である。

## Anti-corruption boundaries

- 各contextはdomain intentをrunbook IDとtyped parameterへ翻訳する。ExecutionはAGL feature、Yocto provider、scene、surface、driverの正しさを判断しない。
- Outputはrun IDとevidence envelopeで返す。各domain agentがdomain verdictへ翻訳する。
- Log analysisは`log-analyzer`へbounded evidence IDでhandoffし、raw log全体をprimary contextへ返さない。

## Ownership and tools

- Write-capable execution role: `build-runner`。明示されたrunbookだけを所有する。
- Read-only supporting role: `log-analyzer`。
- MCP: `command_runner` (`list_runbooks`, `describe_runbook`, `plan_runbook`, `execute_runbook`, `start_runbook`, `get_run_status`, `read_run_log`, `cancel_run`)。
- `execute_runbook`はdry-run default、fixed manifest only、arbitrary shell禁止。

Initial catalogはshort read-only observationだけを持つ。ticket IDをplan/runへbindingし、environment setup失敗時はcommandを開始しない。runtimeはmetadata-writeをasync startに限定するが、MCP/SSH終了時のprocess cleanupまたはpersistent supervisor/lock/reattach、disk/process preflight、artifact inventory、allowlisted variableのlossless captureが未実装のため、parse、dry-run、effective environment、image buildを公開しない。これらはFLR-0006/FLR-0004のacceptanceまでUNKNOWNである。

Context relationshipsは[Domain context map](../../docs/architecture/domain-context-map.md)を参照する。
