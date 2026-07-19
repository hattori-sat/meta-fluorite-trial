# Graphics bounded context

## Purpose

Flutter/Filamentのrender requirementsがWayland、Vulkan loader/ICD、Mesa、DRM、device/driver、queue、present pathへどう実効接続されるかを定義・観測する。

## Ubiquitous language

| Term | Meaning in this context |
| --- | --- |
| Wayland display | clientがcompositorへ接続するdisplay connection。physical displayではない。 |
| Wayland surface | compositorへcontent roleを提供するprotocol object。 |
| Vulkan instance/device | loader経由で選択・生成されるAPI instanceとlogical device。 |
| physical device | Vulkanが列挙するgraphics device identity。target hardware名と必ずしも一対一ではない。 |
| ICD / driver | Vulkan implementationをloaderへ公開するcomponent。package presenceだけではselectionを示さない。 |
| queue | command submit/present capabilityを持つVulkan queue。 |
| swapchain / present | image acquisitionからcompositor/displayへ提示するVulkan contract。 |
| Mesa | targetでdriver implementationを提供し得るuserspace graphics stack。 |
| DRM node | kernel graphics deviceへ接続するdevice interface。 |
| software renderer | CPUでgraphics pipelineを実行するdriver path。hardware accelerationとは区別する。 |

## Inputs

- Flutter contextの`FlutterRenderRequirement`。
- Filament contextの`FilamentRenderRequirement`。
- Target imageのloader、ICD、Mesa、DRM、Wayland configuration。
- Target probe evidenceとcomponent source revision。

## Outputs

- Backend、instance/device、driver/ICD、surface、queue、swapchain/present pathのfacts。
- `GraphicsProbeContract`とcapability summary。
- Hardware、virtual GPU、software rendererを区別したselected path evidence。

## Invariants

- Package/configuration present、device enumerated、device selected、frame presentedを別のstateとして扱う。
- Wayland、Vulkan、Mesa、DRM、kernel/deviceの各layerを区別してevidenceを収集する。
- Driver/device identityとimage ID、target role、observation timeを結び付ける。
- Vulkan availabilityだけでhardware accelerationやcorrect renderingを断定しない。
- `graphics-investigator`はread-onlyであり、driver install、device permission変更、target起動をしない。

## Anti-corruption boundaries

- **Flutter runtime / Filament:** renderer固有のsurface/frame用語をgraphics primitiveへadapterで翻訳する。ownerを暗黙に移さない。
- **Yocto:** package/recipe evidenceはavailability hypothesisとして受け取り、runtime selectionはtarget evidenceで確認する。
- **Target Validation:** probe contractとexpected signalsを渡し、graphics agentはuser-visible acceptanceを決めない。
- **Execution:** probe実行が必要ならapproved target runbookへ変換し、任意commandを要求しない。

## Ownership and tools

- Primary read-only role: `graphics-investigator`。
- MCP: `graphics` (`catalog_graphics_configuration`, `search_graphics_path`, `read_graphics_evidence`)。
- Runtime probe: `target-validator`へhandoffする。

Context relationshipsは[Domain context map](../../docs/architecture/domain-context-map.md)を参照する。
