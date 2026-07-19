# ADR-0003 — Separate MCP servers by bounded context

- Status: Accepted
- Date: 2026-07-19

## Purpose

AGL、Yocto、Fluorite、Flutter runtime、Filament、graphics、target validationでは、同じ語でも対象・責務・証拠の意味が異なる。各agentへ必要なcontextだけを渡し、誤ったdomain間推論と巨大outputを抑える。

## Facts

- AGLは車載向けdistributionとimage組立を扱い、Yoctoはlayer、recipe、task、packageのbuild semanticsを扱う。
- Fluorite demo、Flutter runtime、Filament bridge、Vulkan/GPU stackには別々のsource rootと検証観点がある。
- build、target操作、任意shellはread-only source観測より大きな副作用を持つ。

## Considered paths

1. 全componentを1つのsource-knowledge MCPへまとめる。
2. bounded contextごとにserverを分離し、evidence envelopeだけをshared kernelにする。
3. tool 1個ごとにserverを分ける。

## Decision

Option 2を採用する。AGLとYoctoは別serverとし、Fluorite、Flutter runtime、Filament、graphics、target validationも独立させる。定型command実行はallowlist runbook専用serverへ隔離し、任意shellを公開しない。

共有してよいものはprotocol transport、pagination、redaction、evidence ID、error envelopeに限る。domain vocabulary、root allowlist、tool contract、agent accessは共有しない。

## Access rule

- specialist agentは担当domainのMCPだけを有効化する。
- primary agentは短いsummaryとevidence IDを受け取り、必要時だけ該当domainを読む。
- cross-domain結論は各domain evidenceを明記し、推論として記録する。
- write/build/target mutationはread-only観測と同じtool surfaceへ追加しない。

## Consequences

- contextと障害範囲を分離でき、AGLとYoctoの意味を混同しにくい。
- server数と設定は増える。
- shared kernel変更には全serverのcontract testが必要になる。
- 新componentは既存serverへ安易に追加せず、語彙・source root・owner roleが同じかを先に判定する。

## Unknowns

- source indexが大きくなった場合にbuild host常駐serverが必要かはUNKNOWN。まずMac上のstdio + allowlist rootでlatencyとcontext量を測る。
- write-capable build orchestrationをMCP化する時期はUNKNOWN。read-only contractとrunbookが安定してから別ticketで判断する。
