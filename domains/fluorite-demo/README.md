# Fluorite demo bounded context

## Purpose

Fluoriteの3D demoが利用者へ提供するscene、asset、readiness、interactionと、その成功条件を定義・観測する。runtime、engine、GPUの内部実装はこのcontextのmodelにしない。

## Ubiquitous language

| Term | Meaning in this context |
| --- | --- |
| demo | Fluoriteのuser-visible application behavior全体。 |
| scene | 利用者が選択・観測する3D experience。Filament scene objectとは別物。 |
| asset | demo behaviorが参照するmodel、material、texture、HDR、font等のlogical resource。 |
| readiness | native capabilityがscene commandを受けられるとdemoが判断した状態。 |
| interaction | touch、pointer、keyboard等からscene stateへ至るuser action contract。 |
| scene command | public Dart APIを通じて3D operationを依頼するdomain message。 |
| demo acceptance | scene visibility、asset completeness、interactionを個別に評価する条件。 |

## Inputs

- Fluorite Dart source、asset declaration、test/README evidence。
- Product goalと対象scene/interaction。
- Flutter runtimeのlaunch/readiness contract。
- Filament contextのpublic Dart facade contract。

## Outputs

- Scene/asset/interaction catalog。
- `RuntimeLaunchContract`と`SceneCommandContract`。
- `DemoAcceptanceProfile`: render、readiness、interactionを分離したcases。
- Source revisionに紐づくcall-site evidenceとUNKNOWN。

## Invariants

- 製品名は`Fluorite`。既存の`flourite` pathはcompatibility identifierとして変更しない。
- Demo sceneとFilament engine sceneを同一entityにしない。
- Native readiness前のcommandとreadiness後のcommandを区別する。
- Assetがrepositoryにあることとtargetでload可能なことを区別する。
- Render successとinteraction successを別々に判定する。
- `fluorite-investigator`はread-onlyであり、asset生成、app起動、target操作をしない。

## Anti-corruption boundaries

- **Flutter runtime:** app bundle、entrypoint、readiness signalだけをpublished contractにし、Engine task runnerやsurfaceをdemo modelへ持ち込まない。
- **Filament:** public Dart facadeとevent contractだけを使用し、native pointer、engine object、Vulkan handleを参照しない。
- **Target Validation:** user-visible acceptance casesを渡し、probe commandやtarget接続を指定しない。
- **AGL:** app install/startup requirementを渡すが、recipe/package groupをdemoが選ばない。

## Ownership and tools

- Primary read-only role: `fluorite-investigator`。
- MCP: `fluorite` (`catalog_scene_assets`, `search_scene_contract`, `read_scene_source`)。
- Runtime observation: `target-validator`へ`DemoAcceptanceProfile`をhandoffする。

Context relationshipsは[Domain context map](../../docs/architecture/domain-context-map.md)を参照する。
