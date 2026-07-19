# Target Validation bounded context

## Purpose

特定のimage identityをQEMUまたはRaspberry Pi target roleで実行し、boot、service、graphics、Fluorite render、interactionを再現可能なcaseとして観測・判定する。

## Ubiquitous language

| Term | Meaning in this context |
| --- | --- |
| target role | 個別hostname/IPを公開しないQEMUまたはRaspberry Piのrepository-safe identifier。 |
| image identity | source revision、machine、distro、image、artifact digest/manifestを結ぶidentity。 |
| validation session | 一つのimage/target/boot instanceに紐づく観測期間。 |
| validation case | precondition、action、expected signal、actual evidence、verdictを持つ検証単位。 |
| boot health | kernel/userspace/serviceがacceptance pointへ到達した観測。 |
| render verdict | 指定sceneのvisibility/correctnessに対する判定。 |
| interaction verdict | inputから期待scene changeまでの判定。render verdictとは別。 |
| evidence bundle | bounded logs、identities、probe summariesをsessionへ結び付けた集合。 |

## Inputs

- Yocto contextの`ImageArtifactManifest`。
- AGLの`IntegrationAcceptanceProfile`。
- Fluoriteの`DemoAcceptanceProfile`。
- Flutter、Filament、Graphicsのprobe contracts。
- Approved target profileとrunbook。接続値はGit対象外。

## Outputs

- Session identityとboot/service/graphics/render/interaction cases。
- `PASS`、`FAIL`、`UNKNOWN`のcase-level verdictとevidence IDs。
- Runtime facts、negative results、missing evidence。
- Causeを断定しない、context別handoff request。

## Invariants

- build hostが作ったartifact identityを入力とし、Mac validatorはlocal buildやtimestampによるartifact選択を行わない。
- Linux `runqemu`とmacOS QEMUは別target role、別validation sessionとして扱う。
- Image identityとtarget roleを確認できないsessionはsuccess baselineにしない。
- Boot、service、graphics capability、render、interactionを別々に評価する。
- Validatorは観測事実とverdictを返し、build/sourceのroot causeを断定しない。
- Read-only observationをdefaultにする。launch、restart、reboot、service mutationはExecution contextの承認済みrunbookだけで行う。
- 個人account、IP、hostname、credential、個人名を含むabsolute pathをevidenceへ入れない。

## Anti-corruption boundaries

- **Yocto:** artifactをpathではなくidentity/manifest contractとして受け取る。
- **AGL/Fluorite:** acceptance profileをvalidation caseへ翻訳し、domain source internalsをtarget commandへ変換しない。
- **Runtime/Graphics:** probe contractをbounded observer queryへ翻訳し、logから隣接contextの原因を推測しない。
- **Execution:** state changeはrunbook ID、risk class、approvalへ変換し、validator自身はcommand ownerにならない。

## Ownership and tools

- Primary role: `target-validator`。observer callはread-only。state changeは明示承認済みprocedureだけ。
- MCP: `target_validation` (`list_validation_bundles`, `summarize_boot_evidence`, `summarize_graphics_evidence`, `read_target_evidence`)。
- Cross-context verdict review: `pdca-checker`。

Initial MCPはGit外rootに既に存在するevidence fileをlist/search/readするobserverであり、targetへ接続せず、artifact manifestを自動検証せず、session verdictも発行しない。role-local configにimage/sessionのcombined identityがないresponseは`identity_status=insufficient`であり、上記invariantによりsuccess baselineへ使えない。image manifest ingestionとcase verdict生成はFLR-0005で実装する。

Context relationshipsは[Domain context map](../../docs/architecture/domain-context-map.md)を参照する。
