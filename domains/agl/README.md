# AGL bounded context

## Purpose

Automotive Grade Linux distributionとして、どのfeature、image、package group、service、compositor、launcher、applicationを一つのproduct integrationとして組み立てるかを記述・観測する。

## Ubiquitous language

| Term | Meaning in this context |
| --- | --- |
| AGL feature | distribution integrationを選択するnamed capability。Yocto variableそのものではない。 |
| image | AGLが定義するproduct filesystem/runtime compositionのintent。deploy artifactとは区別する。 |
| integration point | componentをimage、service、launcher、compositorへ接続するmetadataまたはcontract。 |
| package group | runtime package集合をproduct intentとして束ねるAGL metadata。 |
| service integration | unit、startup order、runtime dependencyを含むservice組込み。 |
| app integration | bundle、launcher entry、permission、startup policyを含むapplication組込み。 |
| manifest baseline | repositoryとrevisionを固定したAGL source identity。 |

## Inputs

- [Official AGL workflow](../../docs/agl-official-workflow.md)とfixed `trout` manifest。
- Product goalとtarget class。
- Pinned manifest baselineとAGL layer source。
- Fluorite、Flutter、Filament、graphics componentのintegration requirements。
- Existing image、feature、package group、service/app metadata。

## Outputs

- `ImageCompositionRequest`: image、feature、package group、machine/distro intent。
- `IntegrationAcceptanceProfile`: boot後に存在・起動・接続すべきservice/app/compositor/launcher。
- AGL source revisionに紐づくintegration factsとevidence IDs。
- Yocto contextへ渡すtranslation inputs。recipe resolutionそのものは返さない。

## Invariants

- `feature`を`DISTRO_FEATURES`、`PACKAGECONFIG`、recipe名と同義にしない。
- Baseline観測前にmanifest sync、branch変更、revision更新を行わない。
- source acquisitionと`aglsetup.sh`はLinux build host roleで行い、Mac QEMU validationと混ぜない。
- 全evidenceへmanifest/revision identityを付ける。
- `agl-investigator`はread-onlyであり、setup、build、metadata generationを実行しない。
- AGLに存在するintegration metadataだけでruntime成功を断定しない。

## Anti-corruption boundaries

- **Yocto:** `ImageCompositionRequest`をYocto adapterがeffective variables、providers、recipes、tasksへ翻訳する。AGL agentはBitBake解決を推測しない。
- **Fluorite/Flutter/Filament:** componentをinstallable/integratable unitとして扱い、scene、thread、engine objectの内部語をAGL modelへ持ち込まない。
- **Graphics:** graphics feature intentとruntime device/driver selectionを分ける。
- **Execution:** setup/parse/buildが必要な場合はregistered runbook IDとparameterへ翻訳し、任意shellを渡さない。

## Ownership and tools

- Primary read-only role: `agl-investigator`。
- MCP: `agl` (`get_manifest_catalog`, `search_integration_points`, `read_integration_evidence`)。
- State-changing operation: [Execution context](../execution/README.md)へhandoffする。

Context relationshipsは[Domain context map](../../docs/architecture/domain-context-map.md)を参照する。
