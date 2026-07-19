# Yocto bounded context

## Purpose

BitBake metadataが特定のmachine、distro、image、overrideでどのprovider、task、package、deploy artifactへ実効解決されるかを記述・観測する。AGL固有のproduct intentとは分離する。

## Ubiquitous language

| Term | Meaning in this context |
| --- | --- |
| layer | metadata collectionとpriority/dependencyを持つBitBake layer。 |
| recipe / append / class | build behaviorを定義・修正・共有するmetadata unit。 |
| provider | dependencyを満たすためBitBakeが選択するrecipe。 |
| override | machine、distro、class等の条件で値またはtask behaviorを選ぶ仕組み。 |
| `PACKAGECONFIG` | recipe-local optional build capabilityとdependency mapping。AGL featureではない。 |
| `DEPENDS` / `RDEPENDS` | build-time / runtime dependency。相互に置換できない。 |
| task | parse後のbuild graph上で実行されるoperation。 |
| cache | downloads、sstate、task output等の再利用可能state。artifactとは区別する。 |
| artifact | deploy directoryへ生成され、identityを持つimage/package/output。 |

## Inputs

- AGL contextの`ImageCompositionRequest`。
- Fixed manifest/repository revision、layer configuration、machine、distro、image。
- Recipe、append、class、configuration、既存BitBake environment/log。
- Allowlisted variable namesとevidence query。

## Outputs

- Layer、recipe、append、provider、overrideのeffective resolution。
- Dependency/task graphのbounded facts。
- Package/image manifestと`ImageArtifactManifest`。
- Cache、artifact、task logのidentity付きevidence。

## Invariants

- manifest、conf、layer、recipe、logの順で証拠を狭める。
- Static sourceの記述とeffective BitBake valueを区別する。
- `bitbake -e`、parse、dry-runはmetadata/log/lockを書く可能性があるためread-only queryと見なさず、Execution contextへ委譲する。
- downloads、sstate-cache、tmpを削除しない。`cleanall`を実行しない。根拠と明示承認なしに`cleansstate`を実行しない。
- cache missを不具合、package presentをruntime successと同義にしない。
- `yocto-investigator`と`log-analyzer`は編集・buildを行わない。

## Anti-corruption boundaries

- **AGL:** AGL feature/image intentを受け取り、Yocto用のbuild requestへadapterで翻訳する。AGLのproduct semanticsをYocto variable名へ漏らさない。
- **Execution:** parse/build/task commandはregistered runbookとして実行し、Yocto contextはplanに必要なdomain parametersだけを渡す。
- **Target Validation:** artifact pathだけでなくimage ID、machine、distro、source revision、package manifestを渡す。targetのpass/failからrecipe原因を逆推定しない。

## Ownership and tools

- Primary read-only role: `yocto-investigator`。
- Supporting read-only role: `log-analyzer`（必ずYocto contextを指定して使う）。
- MCP: `yocto` (`list_layer_metadata`, `find_recipe_candidates`, `search_metadata`, `read_metadata`, `list_task_logs`, `tail_task_log`)。
- Build/parse role: `build-runner` via [Execution context](../execution/README.md)。

Context relationshipsは[Domain context map](../../docs/architecture/domain-context-map.md)を参照する。
