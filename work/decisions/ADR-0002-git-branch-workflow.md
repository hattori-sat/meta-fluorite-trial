# ADR-0002 — Use milestone development branches and ticket feature branches

- Status: Accepted
- Date: 2026-07-19

## Purpose

安定点、開発区切り、個別ticketの差分を分離し、問題・変更・検証結果を1対1で追跡する。

## Considered paths

1. `main`へfeature branchを直接mergeする。
2. 長期間1本のdevelopment branchだけを使う。
3. `main → dev-<milestone> → feature-<ticket>-<slug>`とする。

## Decision

Option 3を採用する。

```text
main
  └─ dev-foundation
       ├─ feature-flr-0001-repository-baseline
       ├─ feature-flr-0008-fluorite-demo
       └─ feature-flr-0012-source-knowledge-mcp
```

## Rules

- `main`はPDCA Check済みの安定点。
- `dev-*`は複数の関連ticketを統合する開発区切り。
- `feature-*`は原則1 ticket、1 purpose、1 owner role。
- feature PRのbaseは対応する`dev-*`。
- dev PRのbaseは`main`。
- `main`と`dev-*`へ直接commitしない。
- PDCA checker、privacy、required validationがPASSするまでmergeしない。
- GitHub Actionsの`Branch policy`をrequired status checkに設定して初めてmerge blockerとして強制される。設定完了までは運用規則として扱う。

## Naming

- Development: `dev-<milestone>`
- Feature: `feature-<ticket-lowercase>-<short-slug>`
- 例: `feature-flr-0001-repository-baseline`

## Consequences

- 開発区切り全体のintegrationを`dev-*`で確認できる。
- feature差分とticket evidenceを対応づけやすい。
- dev branchを長期間放置するとmainとの差が大きくなるため、milestoneを小さく保つ。
