# Project context

## Durable facts

- 正式名は`Fluorite`。既存pathの`flourite`は互換性のため変更しない。
- canonical repository: Git remote `origin`
- Mac clone: `$HOME/work/meta-fluorite-trial`
- build-host clone: `$HOME/work/meta-fluorite-trial`
- AGL source: `$AGL_ROOT`（default `$HOME/AGL/trout`）
- legacy reference snapshot: `$LEGACY_ROOT`（Git対象外）
- build-host接続情報: Git対象外のlocal設定
- image: `agl-ivi-image-flutter`
- target: `qemux86-64`, `qemuarm64`, `raspberrypi4-64`
- Mac host: Apple Silicon arm64, QEMU 11.0.1, HVF/TCG available

## Safety constraints

- cache、downloads、tmpを削除しない。
- baseline前にsync/revision更新をしない。
- `cleanall`を実行しない。`cleansstate`は原則実行しない。
- 長時間build、commit、pushはユーザーの明示了承後に行う。

## Known observations

- qemux86-64はMac TCG上でFluorite/Vulkan/llvmpipe初期化まで到達した。
- その試行では`libLLVM.so.18.1`内でSIGSEGVした。
- qemuarm64 deploy artifactはまだ確認されていない。

## Inferences

- Mac検証の主経路はqemuarm64 + HVFが有望だが、graphics成立前は仮説である。
- まずqemux86-64の再現baselineを採ると、比較可能性が高まる。

## Unknowns

- `aglsetup.sh` local変更の意図。
- qemuarm64のFluorite package互換性。
- Raspberry Pi実機検証の接続条件。

## Related context

- [Agent boundaries](agent-boundaries.md)
- [MCP architecture](mcp-architecture.md)
- [Privacy boundary](privacy-boundary.md)
- [Fluorite rendering stack](fluorite-rendering-stack.md)
- [MCP context control](mcp-context-control.md)
