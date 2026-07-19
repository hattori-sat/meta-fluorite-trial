# FLR-0012 — Build the source knowledge MCP

- Status: Next
- Priority: Medium
- Depends on: FLR-0007, FLR-0008
- Context: [MCP context control](../context/mcp-context-control.md)

## Purpose

AGL、Fluorite、Flutter Engine、ivi launcher、Filament、graphics sourceを、revision固定・bounded output・evidence link付きで検索する。

## Success criteria

- source rootとrevisionをallowlistする。
- domainを必須parameterにする。
- default responseをsummaryとevidence IDに限定する。
- source excerptに行数上限とpaginationを持たせる。
- arbitrary shell、write、network fetchを公開しない。
- privacy checkerとaudit recordを通す。

## Candidate tools

- `list_components(domain)`
- `get_component_revision(component)`
- `search_symbols(component, query, cursor)`
- `trace_references(component, symbol)`
- `get_recipe_relationship(recipe)`
- `get_patch_targets(patch)`
- `read_evidence(evidence_id, start, limit)`

## Installation decision

prototypeはMac上のstdio MCPとして実装する。build host側CLI追加は現時点で不要。必要性はSSH latency、index size、event-stream要件を測ってから再判定する。
