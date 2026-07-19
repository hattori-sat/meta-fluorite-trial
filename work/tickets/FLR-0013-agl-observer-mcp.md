# FLR-0013 — Build a read-only AGL observer MCP

- Status: Prototype implemented; remote acceptance pending
- Priority: High
- Depends on: FLR-0001
- Contexts: [domain boundaries](../context/domain-boundaries.md), [MCP architecture](../context/mcp-architecture.md)

## Purpose

AGLのfixed manifest、feature、image、packagegroup、compositor、launcher、service組立を、Yocto内部のtask semanticsと混ぜずに観測する。

## Success criteria

- AGL manifestとsource revisionをbounded evidenceとして返す。
- bounded search/readによってimageからFluorite packageまでのAGL側assembly evidenceを集められる。
- AGL feature、template、service、compositor integration pointをbounded searchで識別する。
- Yocto recipe/task詳細が必要な場合はevidence IDを保ったままFLR-0004のdomainへ引き渡す。
- arbitrary shell、write、network fetchを公開しない。
- large multi-repository checkoutはallowlisted repository/subtree rootへ分割し、scan cap後の`truncated`をabsence evidenceにしない。

## Implemented tools

`get_manifest_catalog`、`search_integration_points`、`read_integration_evidence`。

## Check and unknowns

- local protocol、bounded IO、privacy、Yoctoとのtool separation: PASS。
- 4,000 files/32 MiBを超えるglobal scanはcompleteではなく、role-local configでmanifest/meta-agl等のsubrootへ分割する。actual checkoutでのcoverage: UNKNOWN。
- Macからfixed SSH stdioでbuild host runtimeを起動する方式を採用した。build hostへCodex CLIは導入しない。
- mini PC上のactual Python 3.10 stdio handshakeとGit外role configuration: UNKNOWN。push後にread-only acceptanceを行う。
