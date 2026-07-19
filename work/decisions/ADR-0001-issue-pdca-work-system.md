# ADR-0001 — Use a single-WIP issue and PDCA work system

- Status: Accepted
- Date: 2026-07-19

## Context

Yocto、QEMU、graphics、Flutter、Raspberry Pi、MCPを同時に扱うため、context混線、根拠喪失、過剰改修のriskが高い。

## Options

1. 1つの長い作業日誌だけで管理する。
2. GitHub Issueだけで管理する。
3. repository内ticketをindexとし、context/log/decision/evidenceを分離する。

## Decision

Option 3を採用する。GitHub Issueは将来同期可能だが、offlineでもcloneと同時に全contextを再現できるrepository内Markdownをsource of truthにする。

## Consequences

- AIは必要なcontextだけを選択して読める。
- 判断とraw observationを区別できる。
- file数は増えるため、`TASKS.md`と相互linkを必須にする。
- Done判定にはPDCA checkerを通す。
