# FLR-0051 — Ticket cadence and evidence discipline

- Status: Done
- Priority: High
- Owner: project coordination + runtime validation roles
- Created: 2026-09-08
- Updated: 2026-09-09
- Work unit: 独立した検証・修正・運用改善ごとにMarkdown ticketを切り、完了単位の証跡と次ticketへの境界を維持する
- Depends on: [FLR-0050](FLR-0050-flutter-parent-alpha-frame-loop.md)
- Working log: `work/logs/2026-09-08-flr0051.md`

## Problem

### Purpose

3D表示の検証を長期間同じticketで続けると、仮説、失敗、成功、次の作業範囲が混在し、
どの時点で何が判定されたか追跡しにくくなる。作業の完了単位ごとにticketを切り、
証跡と次の独立課題を明示する運用を定着させる。

### Success measure

- 1つのMarkdown ticketは1つの独立した検証または修正単位だけを扱う。
- 現在のticketのSuccess criteriaが判定された時点で、新しい仮説・修正・画面遷移を別ticketへ分割する。
- 各ticketにFacts/Inferences/Hypotheses/UNKNOWN、Plan/Do/Check/Act、成功・失敗ログ、QMP-only画面証拠を紐付ける。
- `TASKS.md`では原則`In Progress`を1件だけにし、次の作業はInboxまたはNextへ登録する。
- 同じ失敗を繰り返した場合、原因と再発防止策をworking logまたは運用文書へ反映する。

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | ticketの粒度、WIP状態、証跡の所在が曖昧になり得る | `TASKS.md`、FLR-0049/0050履歴 |
| Where | canonical repository内のticket、working log、evidence、layer変更 | repository policy |
| When | 独立した判定・修正・route transition・build/runtime loopの境界 | FLR-0049からFLR-0050への分割 |
| Who | project coordination、runtime diagnosis、build、validation roles | `AGENTS.md` |
| How | 既存ticketを再利用せず、完了単位ごとに新しいMarkdown ticketを作る | `TASKS.md` ticket unit policy |

### Priority selection

- Compared strata: ticket粒度、証跡保存、WIP状態、次ticket登録
- Selected focus: 独立作業単位の境界と、次ticketを切る判定基準
- Selection evidence: 同じ3D検証でも、model render boundary、parent alpha、frame loop、route transitionは別の検証可能な境界である

### Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| 1 | 新しい仮説または作業結果 | 独立ticketを作成 | FLR-0049からFLR-0050は分割済み | `TASKS.md` |
| 2 | 作業中の新しい改善点 | 現在ticketへ混ぜずInboxへ登録 | ticket cadence改善は未登録だった | 本ticket作成時の確認 |
| 3 | 判定可能な完了単位 | 成功/失敗証跡と次ticketを記録 | 運用ルールは既存記載があるが、改善項目のticketが不足 | `TASKS.md` |

### Problem point

新しい独立した運用課題を発見した時点で、現在の実装ticketとは別のInbox ticketを即時登録する工程が明文化・実行されていなかった。

### Ideal condition

新しい仮説、修正、画面遷移、build/runtime loop、または再発防止策が現在ticketのSuccess criteriaに含まれない場合、
作業開始前に新しいMarkdown ticketを作成し、`TASKS.md`へ登録する。

### Current condition — Facts

- `TASKS.md`には1 ticket 1独立検証単位の方針がある。
- `FLR-0050`が現在唯一のIn Progress ticketである。
- ticket cadence自体の改善項目は、今回の確認時点では登録されていなかった。
- `FLR-0051`をInboxとして登録した。

### Gap

方針は存在するが、新しい改善点を検出した瞬間の登録アクションとチェックが不足している。

### Impact

作業履歴の追跡性、証跡と判定の対応関係、次のAIセッションでの再開性が低下する。

### Point of occurrence

作業中にscope外の独立課題を検出し、現在ticketを継続するか新ticketへ分ける判断の直後。

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| ticket policyはあるが登録トリガーが弱い | policyがあっても改善項目がInboxへ自動的に現れない | 新しい改善点を発見した時点のTASKS確認 | Supported | 本ticket作成前の確認 |
| 長期検証ではticketの完了境界が不明確になる | model、alpha、frame loop、routeが同じticketへ戻りやすい | FLR-0049/0050の境界を比較 | Partially supported | `FLR-0049`、`FLR-0050` |

### Confirmed root cause

新しい独立課題の検出時に、現在ticketのscope判定とInbox登録を必須チェックとして実行する工程が不足していた。

### Minimal countermeasure

各作業ループの開始・完了時に、次の4点をチェックする。

1. 現在ticketのSuccess criteriaに含まれる作業か。
2. 含まれない場合は新しいMarkdown ticketを先に作成したか。
3. `TASKS.md`のIn Progressが1件だけか。
4. 成功・失敗・UNKNOWNの証拠と、次ticketの境界を記録したか。

## Scope

### In scope

- ticketを切るタイミングと粒度の運用基準
- `TASKS.md`のWIP/Inbox/Next更新
- working log、QMP-only画像、runtime/buildログの紐付け基準
- 同じ失敗を繰り返さないためのチェック項目

### Out of scope

- Flutter親alphaの実装・ビルド・runtime検証（FLR-0050）
- production 2D+3D合成とroute transitionの実装・検証（後続ticket）
- Jiraへの登録

## Success criteria

- 本ticketの運用ルールが`TASKS.md`と作業skill/runbookへ反映される。
- 次の独立作業が開始される前に、対応する新ticketが存在する。
- 各ticketの完了時に、成功・失敗・UNKNOWNと証跡の対応が確認できる。

## Visual evidence

- QMP-only screenshotまたは承認済み実機capture: 運用ticketのため該当なし
- 画像で見える内容 / 見えない内容: 該当なし
- Run ID / image identity / captured at: 該当なし
- Pixel count / bounding box / SHA-256 / evidence ID: 該当なし
- Artifact attachment or role-based link: ticket運用のため該当なし

## Hypotheses

1. 登録トリガーを作業ループの必須チェックにすれば、scope混在を減らせる。
2. WIP 1件とInbox/Nextの境界を同時に確認すれば、長期ticketの再利用を防げる。

## PDCA

### Plan

- Verification sequence: ticket policy確認 → 独立課題の抽出 → Inbox登録 → TASKS反映 → 次ticket開始前チェック
- Expected observations: 現在ticketのscope外作業が新しいticketとして追跡できる
- Stop conditions: 現在ticketへscope外作業を追加しない
- Risks: ticket数の増加だけで粒度が細かくなり過ぎる可能性

### Do

- 本ticketを、今回検出したticket cadence改善の独立作業として登録する。
- `TASKS.md`へInbox項目を追加する。
- 実際の運用反映は本ticketの作業単位として別のDoで行う。

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| 独立ticket登録 | FLR-0051が存在 | 登録済み | 本ticket | PASS |
| WIP分離 | FLR-0050のみIn Progress | 維持 | `TASKS.md` | PASS |
| scope分離 | FLR-0050へ改善作業を混ぜない | 分離済み | `TASKS.md`、本ticket | PASS |

### Act

- 本ticketを次の運用改善作業の対象としてInboxに置く。
- 以後、独立した検証・修正・route transitionごとに新しいMarkdown ticketを切る。
- 完了判定後はこのticketへ新しい開発を追加せず、次の独立作業は新ticketへ切る。

## Decision log

- 2026-09-08: FLR-0050の実装・検証を中断せず、ticket cadence改善はFLR-0051へ分離した。
- 2026-09-08: Jiraは使用せず、canonical repository内のticketとworking logを正本とする。

## Unknowns

- 既存skill/runbookのどこまでを本ticketで更新するかは未着手。
- ticket数と粒度の最適なバランスは運用後に再評価する。

## PDCA checker

- Status: NOT CHECKED
- Checked by: runtime validation role
- Findings: Ticket registration and WIP separation checked; skill/runbook update is pending.
