# Flutter runtime bounded context

## Purpose

Flutter Engine、Embedder API、ivi launcher、plugin hostがapp bundleを起動し、thread、message、renderer、surface lifecycleを成立させるcontractを定義・観測する。

## Ubiquitous language

| Term | Meaning in this context |
| --- | --- |
| Engine | Dart isolate、frame scheduling、rendererをhostするFlutter Engine instance。 |
| embedder | Engineへplatform task runner、renderer callback、surface/windowを提供するnative host。 |
| launcher | AGL/Wayland環境でbundleとEngineを起動するprocess integration。 |
| task runner | platform、UI、raster等のthread/task execution contract。 |
| platform channel | Dartとnative pluginのmessage transport。domain scene commandそのものではない。 |
| renderer configuration | OpenGL/Vulkan/software等のembedder renderer callback設定。 |
| Flutter surface | Flutter frameが描画・presentされるruntime-owned rendering target。Wayland/Vulkan surfaceと同義ではない。 |
| plugin registration | native pluginをmessenger/lifecycleへ接続するhost operation。 |

## Inputs

- App bundle、entrypoint、assetsとlaunch configuration。
- Flutter Engine/embedder/launcher source revision。
- Plugin registrationとplatform message contract。
- Graphics contextから提供されるsurface/device capability。

## Outputs

- `RuntimeLaunchContract`: bundle、entrypoint、readiness/error signal。
- `PluginHostContract`: registration、channel、thread、lifecycle、surface handshake。
- `FlutterRenderRequirement`: graphics adapterへ渡すrenderer/surface requirements。
- Engine、thread、surface、present callbackのownership evidence。

## Invariants

- UI、platform、raster、Filament render threadを明示的に区別する。
- Flutter surface、Wayland surface、Vulkan surface、Filament swap chainを同一objectとして扱わない。
- Backendはsource optionだけで断定せず、effective configとtarget evidenceで確認する。
- Flutter frameとFilament frameのcomposition方式はevidenceが揃うまでUNKNOWNとする。
- `flutter-runtime-investigator`はread-onlyであり、Engine build、launcher起動、target操作をしない。

## Anti-corruption boundaries

- **Fluorite demo:** bundle/entrypoint/readinessを受ける。scene semanticsをEngine lifecycleへ混ぜない。
- **Filament:** plugin registration、message transport、thread/surface handshakeだけを共有し、entity/material semanticsをruntimeへ持ち込まない。
- **Graphics:** renderer requirementをWayland/Vulkan primitiveへadapterで翻訳し、driver selectionをsource optionから推測しない。
- **Target Validation:** probe名とexpected signalを渡し、runtime agentはtarget verdictを付けない。

## Ownership and tools

- Primary read-only role: `flutter-runtime-investigator`。
- MCP: `flutter_runtime` (`catalog_embedder_surfaces`, `search_embedder_contract`, `read_runtime_source`)。
- Runtime probe: `target-validator`へhandoffする。

Context relationshipsは[Domain context map](../../docs/architecture/domain-context-map.md)を参照する。
