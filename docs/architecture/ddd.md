# Domain-driven operating model

## Decision

Fluorite labを8個のbounded contextへ分ける。各contextは独自のubiquitous language、evidence、invariant、MCP、investigatorを持つ。primary roleだけがticketの問いに沿って複数contextの結果を統合する。

これはruntimeをmicroservice化する判断ではない。調査・automation・agent contextで意味が混ざることを防ぐためのmodel boundaryである。

## Why bounded contexts

たとえば`feature`はAGLでは製品integrationの選択、Yoctoでは`DISTRO_FEATURES`などmetadata上の値になり得る。`surface`もFlutter embedder、Filament、Wayland、Vulkanでownershipとlifecycleが異なる。単一schemaや単一investigatorへ集約すると、同名語を同一概念として扱う誤りが起きやすい。

### Compared approaches

1. Single lab domain and one large MCP
   - server設定と横断検索は単純になる。
   - 用語、権限、source revision、巨大logが一つのtool surfaceへ集まり、context isolationが弱い。
2. Independent bounded contexts with a small shared transport contract
   - translationとserver運用は増える。
   - domain vocabulary、versioning、permission、agent ownership、failure radiusを別々に保てる。

2を採用する。共有するのは`EvidenceEnvelope`と`Handoff`のtransport metadataだけである。domain固有payload、原因推論、state transitionは共有kernelへ入れない。

## Context boundaries

| Context | Core question | Does not decide |
| --- | --- | --- |
| AGL | automotive imageへ何をどう統合するか | recipe/taskの実効解決 |
| Yocto | metadataがどのtask/package/artifactへ解決されるか | demoの正しい見た目 |
| Fluorite demo | どのscene/asset/interactionが成功を意味するか | EngineやGPU内部ownership |
| Flutter runtime | app、embedder、thread、surface、pluginをどうhostするか | Filament scene semantics |
| Filament | Dart/native commandを3D engine stateとframeへどう変換するか | driverが実際に選択されたか |
| Graphics | Wayland/Vulkan/Mesa/DRM/deviceがどう接続されpresentするか | app-level scene acceptance |
| Target Validation | 特定imageとtarget sessionで何が観測・合格されたか | build metadataの真因 |
| Execution | 承認済みoperationをどう安全かつ再現可能に実行するか | operation結果のdomain上の意味 |

各contextの詳細は[Domain registry](../../domains/README.md)に置く。

## Filament split decision

当面はDart/native bridgeとFilament engine integrationを一つのFilament context内の二つのmoduleとして扱う。bridgeがengine object ID、lifecycle、version compatibilityを翻訳するため、現在は同じ変更理由を持つという仮説に基づく。

次のいずれかが確認された場合は、`Filament Bridge`と`Filament Engine`へ分割する。

- bridgeとengineが独立してrelease/versioningされる。
- bridgeがFilament以外のengineも扱う。
- engine調査がplugin protocolを一切必要としない割合が高くなる。
- 両者の担当、permission、MCP source rootを独立させる必要が出る。

この判断の妥当性は現時点ではUNKNOWNであり、source revisionとcall pathを確認するFLR-0010で再評価する。

## Ownership and change rule

- Domain READMEは、そのcontextの用語とcontractのsource of truthである。
- Cross-context contract変更は両contextのownerが確認し、primary roleがdecisionとして記録する。
- Investigatorはread-onlyであり、factsを返す。実装fileを変更しない。
- State-changing operationはExecution contextだけがplanし、明示承認とrunbookを要求する。
- Checkerは実装者と分離し、自分の成果を自己承認しない。

## Related documents

- [Domain context map](domain-context-map.md)
- [Evidence and handoff contract](evidence-handoff-contract.md)
- [Agent installation and routing](../agents.md)
- [Durable domain context](../../work/context/domain-boundaries.md)
