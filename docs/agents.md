# Agent installation and routing

## Outcome

各bounded contextへ狭いproject-scoped custom agentを割り当てる。primary roleは問いをcontext単位へ分解し、専門agentはbounded evidenceだけを返す。raw source、巨大log、隣接domainの推測をprimary contextへ持ち込まない。

Codexはproject-scoped custom agentを`.codex/agents/*.toml`から読み込む。各fileの`name`、`description`、`developer_instructions`がroleを定義し、project MCPのon/offを同じconfiguration layerで上書きする。形式は公式[Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)に合わせる。

## Setup

1. Canonical repositoryをproject rootとして開く。
2. `bash scripts/assert-canonical-repository.sh`がPASSすることを確認する。
3. [Setup](setup.md)に従ってcheck-only setupを先に実行する。installやstate changeは明示された任意stepだけを選ぶ。
4. [Verification](verification.md)に従ってTOML、MCP import、privacy、link checksを実行する。
5. Project configurationを確実に再読込するため、repository rootから新しいCodex taskを開始する。

`.codex/config.toml`は各MCP transportを定義しなければならず、agent TOMLはそのserverをenable/disableする。serverをsetupしていない場合、agentはgeneric shellでremote accessを代替せず`UNKNOWN`を返す。

## Agent-to-context matrix

| Agent | Bounded context | MCP access | Authority | Output |
| --- | --- | --- | --- | --- |
| `agl-investigator` | [AGL](../domains/agl/README.md) | `agl` only | read-only | manifest/integration facts |
| `yocto-investigator` | [Yocto](../domains/yocto/README.md) | `yocto` only | read-only | effective metadata/dependency facts |
| `fluorite-investigator` | [Fluorite demo](../domains/fluorite-demo/README.md) | `fluorite` only | read-only | scene/asset/interaction contract |
| `flutter-runtime-investigator` | [Flutter runtime](../domains/flutter-runtime/README.md) | `flutter_runtime` only | read-only | embedder/thread/surface contract |
| `filament-investigator` | [Filament](../domains/filament/README.md) | `filament` only | read-only | bridge/engine lifecycle contract |
| `graphics-investigator` | [Graphics](../domains/graphics/README.md) | `graphics` only | read-only | Wayland/Vulkan/Mesa/DRM path facts |
| `target-validator` | [Target Validation](../domains/target-validation/README.md) | `target_validation` only | read-only observer | case verdict/evidence bundle |
| `build-runner` | [Execution](../domains/execution/README.md) | `command_runner` only | approved execution | plan/run ID/status/artifacts |
| `log-analyzer` | Yocto supporting role | `yocto` only | read-only | first causal error/hypotheses |
| `pdca-checker` | Delivery governance | no project domain MCP | read-only | PASS/FAIL/UNKNOWN gate |

`log-analyzer`と`pdca-checker`はdomain ownerではない。`target-validator`もgraphicsのroot causeを判断せず、必要ならprimary roleが`graphics-investigator`へ別handoffする。

## Routing rules

1. Active ticketの問いを[Domain context map](architecture/domain-context-map.md)上の一つのsource contextへ割り当てる。
2. そのcontextのprimary agentへ、一つの判定可能な問いだけを渡す。
3. 別contextのfactsが必要ならagentを追加し、同じagentへtool accessを足さない。
4. State-changing operationは`build-runner`へ別handoffし、先に`plan_runbook`を取得する。
5. Primary roleが各resultをticketへ統合し、`pdca-checker`が独立してevidenceを監査する。

Recommended assignment:

```text
ticket_id: FLR-XXXX
question: <one falsifiable question>
source_context: <one context ID>
scope: <revision, repository-safe role paths, evidence IDs>
required_inputs: <ticket and domain contract>
expected_output: <facts, unknowns, domain payload>
prohibited_actions: <edit/build/sync/target mutation>
output_budget: <summary and excerpt limits>
```

Resultとhandoffの完全なschemaは[Evidence and handoff contract](architecture/evidence-handoff-contract.md)を参照する。

## Context isolation

- Investigatorは割り当てられたDomain README、active ticket、直接必要なevidenceだけを読む。
- Investigatorはread-only。file edit、build、sync、environment source、target mutationを行わない。
- Cross-context questionでは内部toolを増やさず、`HANDOFF_NEEDED`、必要context、最小の問いを返す。
- Agent TOMLは他のproject domain MCPを`enabled = false`にする。MCP以外の親tool permissionはruntimeから継承するため、instruction上の禁止事項も必須である。
- Primary roleはraw logを貼らず、facts、UNKNOWN、evidence ID、decisionだけをdurable recordへ残す。
- `agents.max_depth = 1`を維持し、specialistからの再帰的fan-outを避ける。追加handoffはprimary roleが行う。

## Command authority

`build-runner`だけが`command_runner`へaccessする。`list_runbooks`、`describe_runbook`、`plan_runbook`は計画用、`execute_runbook`、`start_runbook`、`cancel_run`はtool approvalに加えてticket上の明示承認を必要とする。長時間operationは`start_runbook`後に`get_run_status`とbounded `read_run_log`で追跡する。

- 任意command、script path、SSH destination、raw environment assignmentを渡さない。
- Dry-runをdefaultにし、plan上のside effectとrisk classを確認する。
- `bitbake -e`、parse、`bitbake -n`を`metadata-write`として扱う。
- downloads、sstate-cache、tmpを削除しない。
- `cleanall`を実行しない。`cleansstate`は通常runbookへ含めない。

Target launch/reboot等のmutationは、専用runbookとrollback/ownership contractが追加・検証されるまでUNKNOWN/deferredとする。

## Privacy

Agentへのprompt、result、MCP response、working logへ個人名、個人account、IP address、hostname、個人名を含むabsolute path、email、credentialを含めない。role pathは`$PROJECT_ROOT`、`$AGL_ROOT`、`$BUILD_HOST`、`$TARGET`を使う。privacy checkが失敗した場合、値を再掲せずredactし、全作業を止める。

## Smoke test

新しいtaskで一度に一agentずつ、read-only queryを依頼する。

```text
Use agl-investigator for FLR-XXXX. Read the AGL bounded context first, list the fixed manifest identity, and return facts plus evidence IDs. Do not inspect Yocto metadata.
```

Expected:

- Agent名とsource contextが一致する。
- `agl`以外のproject domain MCPが無効である。
- Resultがfacts/inferences/hypotheses/UNKNOWNを分離する。
- Personal identifierやraw connection valueを返さない。

各agentの実spawnまでをCIだけで完全検証できるかはUNKNOWNである。TOML/schema/import checkに加えて、新しいCodex taskでのsmoke testをrelease gateにする。
