# Domain registry

## Purpose

Fluoriteの3D demoをAGL image上で起動・描画・操作できる状態まで追跡するため、同じ語が別の意味で使われる領域をbounded contextとして分離する。このdirectoryはsource codeの配置ではなく、各contextが所有する言語、判断、入出力、invariantのregistryである。

## Bounded contexts

| Context | Owns the meaning of | Primary agent | MCP boundary |
| --- | --- | --- | --- |
| [AGL](agl/README.md) | automotive distributionとしてのfeature、image、service/app integration | `agl-investigator` | `agl` |
| [Yocto](yocto/README.md) | BitBake metadata resolution、task、package、artifact | `yocto-investigator` | `yocto` |
| [Fluorite demo](fluorite-demo/README.md) | scene、asset、interaction、demo readiness | `fluorite-investigator` | `fluorite` |
| [Flutter runtime](flutter-runtime/README.md) | Engine/embedder lifecycle、thread、surface、platform channel | `flutter-runtime-investigator` | `flutter_runtime` |
| [Filament](filament/README.md) | Dart/native bridgeとFilament engine lifecycle | `filament-investigator` | `filament` |
| [Graphics](graphics/README.md) | Wayland、Vulkan、Mesa、DRM、device/driver/present | `graphics-investigator` | `graphics` |
| [Target Validation](target-validation/README.md) | imageをtargetで実行した観測とacceptance verdict | `target-validator` | `target_validation` |
| [Execution](execution/README.md) | approved runbook、risk class、process、bounded log | `build-runner` | `command_runner` |

`log-analyzer`と`pdca-checker`はbounded contextのownerではない。前者は指定されたcontextのevidenceを読むsupporting role、後者はdelivery processを監査するindependent governance roleである。

## Separation rule

- 各contextの用語は、そのcontextのREADMEに書かれた意味でのみ使う。
- 別contextへ渡すときはcontext map上のpublished contractへ翻訳する。
- 共通化するのは[evidence envelopeとhandoff metadata](../docs/architecture/evidence-handoff-contract.md)だけで、domain payloadは共通schemaへ押し込まない。
- MCP server、agent instruction、source allowlist、write authorityをcontext単位で分離する。
- cross-contextの原因を一つのagentが断定しない。primary roleが複数contextのfactsをticket上で統合する。

全体の関係は[Domain context map](../docs/architecture/domain-context-map.md)を参照する。
