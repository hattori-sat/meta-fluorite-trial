# MCP context-control design

## Objective

AGL、Yocto、Fluorite、Flutter、Filament、Vulkanの大量source/logを会話contextへ直接流さず、問いに必要なbounded evidenceだけを返す。

## Recommended boundaries

### Source knowledge MCP

Read-only。固定revisionのsource、recipe、patch、documentationを対象にする。

- component catalog
- revision and provenance
- symbol/reference search
- recipe/patch relationship
- dependency path
- bounded source excerpt
- evidence handle generation

Domainsは`agl`, `fluorite-demo`, `flutter-engine`, `ivi-launcher`, `filament-bridge`, `filament`, `graphics`で明示指定する。

### AGL/Yocto observer MCP

Read-only。build hostの実効configuration、layer、task、cache、artifactを対象にする。

- layer and recipe resolution
- `bitbake -e` allowlisted variables
- package dependency and manifest
- task/log status
- artifact identity

### Target observer MCP

Read-onlyを基本とし、QEMU/Raspberry Piのboot、service、Wayland、Vulkan、Flutter、Filamentを共通schemaで観測する。

## Response discipline

toolはdefaultでsummaryだけを返す。raw source/logはevidence IDとして保存し、必要なrangeだけ別callで読む。

Every response:

- `domain`
- `revision_or_image_id`
- `observed_at`
- `facts`
- `unknowns`
- `evidence_ids`
- `truncated`
- `next_queries`

MCPは原因推論を返さない。factsとsource locationを返し、原因分析はticket側で仮説・反証として行う。

## Tool-shape comparison

### Generic shell/search tools

実装は小さいが、任意command、巨大output、秘密情報、context汚染のriskが高い。

### Domain-specific bounded tools

実装量は増えるが、revision、path allowlist、output size、redaction、evidence linkを強制できる。本projectではこちらを採用する。

## Initial transport

Mac上でstdio MCPを動かし、build host観測だけ固定SSH commandへ委譲する。build hostへCodex CLIやMCP runtimeを直ちに導入しない。POSIX tools、Git、repo、BitBake、Pythonが既に使える範囲でprototypeする。

remote-side installationが必要になるのは、大量indexをhost-localで保持する、long-running event streamを扱う、またはSSH round-tripが測定上のbottleneckになった場合。
