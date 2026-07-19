# FLR-0001 — Establish the canonical repository baseline

- Status: In Progress
- Priority: Critical
- Owner: primary agent + user
- Created: 2026-07-19
- Updated: 2026-07-19
- Links: [project context](../context/project.md), [2026-07-19 log](../logs/2026-07-19.md)

## Problem

### Purpose

Fluoriteの調査、変更、build、検証を、別環境でも説明・再現できるsource of truthとして管理する。

### Success measure

fresh cloneから固定revision、独自layer、build設定、issue、作業履歴へ到達でき、privacy・secret・容量checkを通過する。

### Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | baseline、独自layer、履歴が単一repositoryに揃っていない | Git status、baseline report |
| Where | canonical clone、現在workspace、build hostのAGL tree、旧参照directoryに分散 | project context |
| When | repository初期化から最初のQEMU/build作業へ進む前 | working log |
| Who | primary roleが統合、checker roleがgate判定。個人名は管理しない | agent boundaries |
| How | 管理文書は同期済みだが、独自layerと完全manifestが未取得 | Check table |

### Priority selection

- Compared strata: QEMU crash、qemuarm64未build、MCP未実装、repository baseline分散。
- Selected focus: repository baseline分散。
- Selection evidence: 他の全作業の入力、差分、結果保存に影響し、後からの復元costが最も高い。

### Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| 1. clone identity | remoteとHEAD | Mac/build hostで一致 | 一致 | working log |
| 2. management tree | ticket/context/agent | canonical cloneへ保存 | 同期済み | Git status |
| 3. build baseline | fixed manifest/conf | canonical cloneへ保存 | 一部のみ。完全manifest未保存 | baseline report |
| 4. custom layer | `meta-local` | Git管理対象 | build hostにのみ存在 | baseline report |
| 5. gate | repository tree | privacy/secret/size/PDCA PASS | privacy修正中、PDCA FAIL | checker section |

### Problem point

Step 3でbuild baselineの保存が不完全になり、Step 4のcustom layerもsource of truthへ入っていない。

### Ideal condition

固定revision、Fluorite固有layer、設定、issue、working log、agent設定が1つのcanonical Git repositoryから追跡できる。

### Current condition — Facts

- canonical clone候補はMacとmini PCの`meta-fluorite-trial`で、同じorigin/HEADを持つ。
- Codexの現在workspaceは別の未commit Git repository。
- `$HOME/work/fluorite`は過去成果物とsourceを含む非Gitの参照directory。
- `meta-local`はmini PCのAGL tree内でGit管理外。

### Gap

baseline調査と運用設定がcanonical cloneに入っておらず、source of truthが分散している。

### Impact

作業履歴、根拠、patchの由来が失われ、QEMUとRaspberry Piの結果を説明・再現できない。

### Point of occurrence

repository初期化と既存実験資産の整理段階。

## Root-cause analysis

| Cause hypothesis | Prediction | Falsification test | Result | Evidence |
| --- | --- | --- | --- | --- |
| workspaceとcanonical cloneが別pathで、直接保存先になっていない | 管理treeが片方だけに作られる | 両Git statusとhashを比較 | management treeでは成立 | working log |
| remote artifact取得の承認境界によりbaseline copyが止まった | 調査stdoutはあるがfile本体がない | canonical treeでmanifest/layerを確認 | 成立 | Git tree |

### Confirmed root cause

現在workspaceとcanonical cloneの分離、およびremote artifact取得の承認未完了により、調査結果がcanonical repository artifactへ変換されていない。

### Minimal countermeasure

canonical cloneを作り直さず、検証済み管理treeを非破壊同期し、必要な`meta-local`、fixed manifest、confだけをallowlistで追加する。

## Scope

### In scope

- management documents、agent設定、baseline reportをcanonical cloneへ配置する。
- `main → dev-* → feature-*`のbranch workflowとcanonical guardを設定する。
- fixed manifest、`meta-local`、conf snapshotの安全な取り込み方法を確定する。
- 大容量成果物をGit対象外にする。

### Out of scope

- QEMU起動、Yocto build、recipe修正、MCP実装、commit、push。

## Success criteria

- Macとmini PCのcloneで同じ管理treeを取得できる。
- `TASKS.md`からactive ticket、context、log、evidenceへ辿れる。
- current feature branchが対象dev branchから派生し、GitHub branch policyで検査できる。
- `meta-local`と完全な固定manifestがGit管理対象になる。
- secret scanとGit対象容量checkが通る。
- PDCA checkerがPASSする。

## Hypotheses

1. 現workspaceの管理ファイルをcanonical cloneへ同期するのが最小変更である。
2. canonical cloneを作り直す方が安全である可能性もあるが、既存cloneはcleanなので利点が小さい。

## PDCA

### Plan

1. 現workspaceの小さい管理ファイルをcloneへ非破壊同期する。
2. remoteから`meta-local`、conf、fixed manifestを取得する。
3. hash、secret、Git対象容量を検証する。
4. checker監査後にcommit候補を提示する。

Stop condition: path衝突、秘密情報、大容量file、remote/local差分を検出した場合は同期・stageを止める。

### Do

- [2026-07-19 working log](../logs/2026-07-19.md)

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| clone identity | Mac/mini PCで同じorigin/HEAD | 一致 | working log | PASS |
| management tree | canonical cloneに存在 | 2026-07-19に非破壊同期済み | git status | PASS |
| `meta-local` | Git管理対象 | 未取得 | UNKNOWN | FAIL |
| fixed manifest | 完全なrevision pin | stdoutで採取、未保存 | baseline report | FAIL |
| privacy | 個人識別情報をGit対象へ含めない | role変数へ置換しchecker PASS | privacy checker | PASS |
| Git worktree | canonical repositoryで作業 | current Codex projectは別repository、canonical cloneへ同期 | canonical guard | PASS WITH CONDITION |
| branch flow | `main → dev-* → feature-*` | `dev-foundation`とticket feature branchを作成 | Git refs | PASS |

### Act

`meta-local`と完全なfixed manifestの取得へ進む。未達のため次ticketへはまだ進まない。

## Unknowns

- remoteからのcopyを今回許可できるか。
- `aglsetup.sh`のlocal変更を保存対象とするか。

## PDCA checker

- Status: FAIL
- Checked by: initial self-check
- Findings: privacy blockerは解消済み。`meta-local`と完全なfixed manifestが未完了。
