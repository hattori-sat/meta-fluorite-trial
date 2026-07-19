# Filament bounded context

## Purpose

Fluoriteのpublic Dart facadeからnative plugin bridgeを経由してFilament engine object、resource、frame submissionへ到達するlifecycleとtranslationを定義・観測する。

## Internal modules

- **Bridge module:** Dart API、platform message、ID mapping、plugin registration、event/error translation。
- **Engine integration module:** Engine、Renderer、View、Scene、Camera、SwapChain、material/model/resource lifecycle。

初期段階では両moduleが同じobject ownershipとversion compatibilityを変更理由として持つため、一つのbounded contextとする。分割triggerは[DDD operating model](../../docs/architecture/ddd.md#filament-split-decision)に置く。

## Ubiquitous language

| Term | Meaning in this context |
| --- | --- |
| Dart facade | Fluoriteへ公開するtyped scene/entity/material operation API。 |
| bridge command | Dart facadeのoperationをnative lifecycleへ翻訳したmessage。 |
| entity handle | Dart/native境界を越えるlogical identity。native pointerではない。 |
| Engine | Filament resourceとrender lifecycleを所有するinstance。Flutter Engineとは別物。 |
| View / Scene | Filament engineがrender対象を構成するobject。demo scene/viewとは別物。 |
| Renderer | Filament Viewをframeへsubmitするengine component。 |
| SwapChain | Filamentがpresent targetへ接続するlifecycle object。Vulkan swapchainと同義とは限らない。 |
| render asset | engine version/material contractに適合するmodel、material、texture、environment resource。 |

## Inputs

- Fluorite contextの`SceneCommandContract`。
- Flutter runtimeの`PluginHostContract`。
- Bridge、Filament recipe/source、patch、version evidence。
- Graphics contextが提供するsurface/device/backend capability。

## Outputs

- Bridge registration、message、ID、error/eventのtranslation evidence。
- Engine/resource/surface lifecycleとthread ownership evidence。
- `FilamentRenderRequirement`。
- Asset/material/version compatibility facts。

## Invariants

- Dart handleとnative pointerを同一identityとして公開しない。
- Bridge、Engine、Renderer、View、Scene、SwapChainのownerとdestroy orderを追跡する。
- Filament EngineとFlutter Engineを区別する。
- Filament View/SceneとFluorite demo view/sceneを区別する。
- Build optionやlibrary presenceだけでruntime initialization成功を断定しない。
- `filament-investigator`はread-onlyであり、plugin/engine buildやtarget操作をしない。

## Anti-corruption boundaries

- **Fluorite demo:** Dart facadeをpublished languageとし、native lifecycleを隠す。
- **Flutter runtime:** plugin host adapterがmessenger、thread、surface contractを翻訳し、Filament entity semanticsをruntimeへ漏らさない。
- **Graphics:** backend requirementをdevice、queue、surface、present contractへ翻訳し、Vulkan handleをDartへ露出しない。
- **Yocto:** recipe/package configurationはversion provenanceとして受け取るが、engine semanticsをrecipe名から推測しない。

## Ownership and tools

- Primary read-only role: `filament-investigator`。
- MCP: `filament` (`catalog_render_assets`, `search_render_bridge`, `read_render_source`)。
- Runtime probe: `target-validator`へhandoffする。

Context relationshipsは[Domain context map](../../docs/architecture/domain-context-map.md)を参照する。
