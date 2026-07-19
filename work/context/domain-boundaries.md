# Domain boundaries — durable context

## Facts

- Fluoriteを表示する実行経路はAGL integration、Yocto build metadata、Fluorite demo、Flutter runtime/embedder、Filament bridge/engine、graphics stack、target executionを横断する。
- 同じ`feature`、`scene`、`frame`、`surface`、`view`という語でもcomponentごとにownerとlifecycleが異なる。
- buildやtarget commandの実行にはread-only source investigationとは異なる権限とside effectがある。
- projectにはread-only investigator、build runner、target validator、PDCA checkerというrole separationが既にある。

## Inferences

- 一つのMCPと一つの共通domain schemaへ全componentを入れると、tool definitionとresponseだけでなく用語の意味も混ざる。
- bounded contextごとにagentとMCPを割り当て、summary contractだけ共有すると、primary contextへ持ち込む情報量と権限を制御しやすい。

## Hypotheses

1. Filament Dart/native bridgeとFilament engine integrationは同じlifecycle/version contractを持つため、初期段階では一つのcontextとして保守しやすい。
2. source追跡が進むとbridgeとengineの変更理由・versioning・担当が分かれ、二つのcontextへ再分割した方がよくなる可能性がある。

FLR-0010でcall pathとversion boundaryを確認し、両仮説を比較する。現時点の妥当性はUNKNOWN。

## Decisions

- 8 bounded contextsを採用する: AGL、Yocto、Fluorite demo、Flutter runtime、Filament、Graphics、Target Validation、Execution。
- AGLとYoctoは必ず別context、別agent、別MCPとする。
- 共通化するのはevidence envelope、pagination、redaction、audit/run ID、handoff metadataだけとする。
- domain固有payload、用語、cause inference、write authorityは共有しない。
- primary roleがcross-context integrationを担当し、investigatorは隣接domainの判断をしない。
- state-changing commandはExecution contextへ隔離し、任意command inputを公開しない。

## Unknowns

- 各MCPを独立processとしてdeployする場合の実測context削減量と運用cost。
- Filament contextをbridge/engineへ分割するtriggerがcurrent source revisionで成立するか。
- Flutter frameとFilament frameの最終composition/ownership contract。

## References

- [DDD operating model](../../docs/architecture/ddd.md)
- [Domain context map](../../docs/architecture/domain-context-map.md)
- [Evidence and handoff contract](../../docs/architecture/evidence-handoff-contract.md)
- [Domain registry](../../domains/README.md)
