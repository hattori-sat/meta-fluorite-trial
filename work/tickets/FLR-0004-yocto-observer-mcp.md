# FLR-0004 — Build a read-only Yocto observer MCP

- Status: Prototype implemented; remote acceptance pending
- Priority: High
- Depends on: FLR-0001
- Contexts: [MCP architecture](../context/mcp-architecture.md), [MCP context control](../context/mcp-context-control.md)

## Purpose

fixed Yocto build treeのlayer、recipe、task、package状態を、任意shellや巨大outputを使わず再現可能なevidenceとして取得する。agentがSSH commandを都度組み立てることによる観測揺れ、誤操作、context肥大化を防ぐ。AGL distributionの観測はFLR-0013へ分離する。

## Success criteria

- read-only toolだけを公開する。
- Yocto layer metadata、recipe candidate、conf/metadata search、bounded source、既存task logを構造化して返す。
- secretをredactし、巨大outputをpageまたはsummary化する。
- `audit_file`をrole-local configへ設定した場合、tool callと対象pathをprivacy-redacted JSONLへ残す。
- destructive commandをAPI surfaceに含めない。
- large build treeはmetadata/task-logのallowlisted subrootへ分割し、scan cap後の`truncated`をabsence evidenceにしない。

## Implemented tools

`list_layer_metadata`、`find_recipe_candidates`、`search_metadata`、`read_metadata`、`list_task_logs`、`tail_task_log`。

## Implementation decision

1. Mac上のstdio MCPが固定SSH commandを実行する。
2. build host上のMCPへremote transportで接続する。

MacのMCP hostからfixed SSH stdioを使い、build hostのcanonical cloneでdependency-free Python runtimeを起動する。任意SSH commandは受け付けず、Codex CLIをbuild hostへ導入しない。

cache/process/artifact inventoryと実効BitBake variableは、このread-only prototypeのtool surfaceにはまだ含めない。`bitbake -e`やparseはwriteを伴い得るためExecutionへ分離するが、full environmentを先頭64 KiBだけで扱わず、allowlisted variableをlosslessに取得するrunbookを別途実装する。source/log scanは4,000 files/32 MiBで停止し、その外側へpaginationできないため、role-local configでrepositoryまたは`tmp/work`の対象subtreeごとにroot aliasを分ける。

## Check

- local protocol、bounded IO、privacy、AGLとのtool separation: PASS。
- `tmp/work/.../temp/log.do_*` discoveryとbounded tail: unit PASS。actual build treeのcompleteness: UNKNOWN。
- audit hook/redaction: unit PASS。実remote audit fileへの書込み: UNKNOWN。
- mini PC上のactual Python 3.10 stdio handshakeとGit外role configuration: UNKNOWN。push後にread-only acceptanceを行う。
