# FLR-0005 — Build a target validation MCP

- Status: Next
- Priority: Medium
- Depends on: FLR-0002
- Context: [MCP architecture](../context/mcp-architecture.md)

## Problem

QEMU/実機のboot、graphics、input、log採取が手作業で、試行間比較と説明可能性が不足している。

## Success criteria

- image identity、boot state、services、graphics stack、Flutter/Fluorite logを一括採取する。
- QEMUとRaspberry Piで共通schemaを使う。
- write operationは明示承認が必要な別toolに分離する。
- evidence indexを自動生成する。
