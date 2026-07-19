# FLR-0001 — Establish the canonical repository baseline

- Status: In Progress
- Priority: Critical
- Owner: primary role + checker role
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
| What | baseline、独自layer、履歴をcandidate treeへ統合したが、commit/push前でfresh cloneへ未配布 | Git status、baseline report |
| Where | canonical linked worktreeに統合済み。remote branchとbuild-role cloneは旧revision | project context、Git refs |
| When | repository初期化から最初のQEMU/build作業へ進む前 | working log |
| Who | primary roleが統合、checker roleがgate判定。個人名は管理しない | agent boundaries |
| How | fixed input、project layer、DDD/MCP/agent/setup/CIをfeature worktreeへ統合済み。commit/pushはfinal gate後 | Check table |

### Priority selection

- Compared strata: QEMU crash、qemuarm64未build、component automation不足、repository baseline分散。
- Selected focus: repository baseline分散。
- Selection evidence: 他の全作業の入力、差分、結果保存に影響し、後からの復元costが最も高い。

### Process analysis

| Step | Input | Expected process/output | Actual observation | Evidence |
| --- | --- | --- | --- | --- |
| 1. clone identity | remoteとHEAD | Mac/build hostで一致 | 一致 | working log |
| 2. management tree | ticket/context/agent | canonical cloneへ保存 | candidate treeへ同期済み、commit待ち | Git status |
| 3. build baseline | fixed manifest/conf | canonical cloneへ保存 | 35-project fixed manifest、external lock、sanitized target confをcandidate treeへ保存 | baseline lock/tests |
| 4. custom layer | `meta-local` | Git管理対象 | 45 filesをcandidate treeへ取り込み、patch identity metadataをrole表現へ匿名化。commit待ち | baseline lock/tests |
| 5. development environment | domain/authority/host境界 | DDD、agent、MCP、setup、CIへ変換 | 8 contexts、10 agents、8 MCP、check-only setup、CIをcandidate treeへ実装 | architecture/tests |
| 6. final gate | repository tree | privacy/secret/size/PDCA PASS後にcommit/push | local gate PASS。independent re-check、commit、push待ち | checker section |

### Problem point

発生時はStep 3でbuild baselineの保存が不完全となり、Step 4のcustom layerもsource of truthへ入らなかった。現在の問題点はStep 6で、検証中candidateが未commit・未pushのためfresh cloneから取得できないこと。

### Ideal condition

固定revision、Fluorite固有layer、設定、issue、working log、agent設定が1つのcanonical Git repositoryから追跡できる。

### Current condition — Facts

- Macとmini PCのcanonical cloneはbaseline調査時に同じorigin/HEADを持っていた。
- feature作業はcanonical repositoryのlinked worktreeに限定している。
- build-host由来のfixed manifest、target conf、current `meta-local`をhash付きcandidate artifactへ変換した。
- source/buildはLinux mini-PC role、QEMU実行検証はMac roleとするhost boundaryを固定した。

### Gap

artifactはcanonical linked worktreeに存在するが未commit・未pushであり、remoteまたはfresh cloneはまだ取得できない。

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

問題発生時、workspaceとcanonical cloneが分離し、remote artifact取得の承認境界も未完了だったため、調査結果がrepository artifactへ変換されなかった。allowlist取得とlinked worktree統合でこの原因への対策は完了し、残るdelivery gapはcommit/pushである。

### Minimal countermeasure

canonical cloneを作り直さず、検証済み管理treeを非破壊同期し、必要な`meta-local`、fixed manifest、confだけをallowlistで追加する。全gateとclean-clone検証後、featureとdev refsをcommit/pushする。

## Scope

### In scope

- management documents、agent設定、baseline reportをcanonical cloneへ配置する。
- `main → dev-* → feature-*`のbranch workflowとcanonical guardを設定する。
- fixed manifest、`meta-local`、conf snapshotの安全な取り込み方法を確定する。
- bounded context、component別MCP、custom agent、setup、CI gateをfresh cloneから利用できる形で配置する。
- 大容量成果物をGit対象外にする。
- approved feature branchをcommitし、`dev-foundation`とfeature branchをGit remote `origin`へpushする。

### Out of scope

- QEMU起動、Yocto build、既存recipe/patchの機能修正、target mutation、Pull Request merge。

2026-07-19に、repository baselineだけでなく今後の作業環境を完成させてpushするようscopeが拡張された。既存runtime codeは変更せず、foundation artifactとして同じticketで管理する。

## Success criteria

- Macとmini PCのcloneで同じ管理treeを取得できる。
- `TASKS.md`からactive ticket、context、log、evidenceへ辿れる。
- current feature branchが対象dev branchから派生し、GitHub branch policyで検査できる。
- `meta-local`と完全な固定manifestがGit管理対象になる。
- AGL/Yoctoを分離したbounded context、MCP、agent routingがconfiguration testを通る。
- `make setup`と`make verify`が同じentry pointでlocal/CI gateを実行できる。
- secret scanとGit対象容量checkが通る。
- PDCA checkerがPASSする。
- approved branchが`origin`へpushされる。

## Hypotheses

1. 現workspaceの管理ファイルをcanonical cloneへ同期するのが最小変更である。
2. canonical cloneを作り直す方が安全である可能性もあるが、既存cloneはcleanなので利点が小さい。

## PDCA

### Plan

1. 現workspaceの小さい管理ファイルをcloneへ非破壊同期する。
2. remoteから`meta-local`、conf、fixed manifestを取得する。
3. DDD context、component別MCP、agent、setup、CIを実装する。
4. hash、privacy、protocol、test、Git対象容量を検証する。
5. checker監査後にcommitし、approved branchをpushする。

Stop condition: path衝突、秘密情報、大容量file、remote/local差分を検出した場合は同期・stageを止める。

### Do

- [2026-07-19 working log](../logs/2026-07-19.md)

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| clone identity | Mac/mini PCで同じorigin/HEAD | baseline調査時の旧HEADは一致。current feature commitのmini PC checkoutはpush前のためUNKNOWN | working log | PASS WITH CONDITION |
| management tree | canonical cloneに存在 | candidate linked worktreeへ非破壊同期済み、未commit | git status | DELIVERY PENDING |
| `meta-local` | Git管理対象 | 45 files、exact repository hash、identity-normalized hashをcandidateに保存、未commit | baseline lock/test | DELIVERY PENDING |
| fixed manifest | 完全なrevision pin | 35 projectsをcommit hashへ固定したcandidate、未commit | manifest/test | DELIVERY PENDING |
| target conf | 個人/接続先固有値を含まない比較可能なsnapshot | 個人/host値を除去し、role/cache baseline pathとhashでRaspberry Pi/QEMUを保存 | conf/test | PASS |
| DDD/agent/MCP | AGL/Yoctoを分離しcomponent contextを限定 | 8 contexts、10 agents、8 MCP、single-server routing | config/protocol tests | PASS |
| host boundary | buildはLinux mini PC、QEMU validationはMac | official workflow、setup、remote/local transportへ反映 | setup docs/tests | PASS |
| privacy | project layerを含め個人識別情報・credential候補をGit対象へ含めない | patch identity metadataをrole化し、全対象checker PASS | privacy/baseline tests | PASS |
| local verification | working treeの共通gate | setup、61 unit tests、46 MCP focused tests、16 shell files、107 links、171 candidate files、privacy/sizeがPASS。Mac foundation/qemux86-64/qemuarm64 checkもPASS | `make setup`, `make verify`, `make setup-macos` | PASS |
| Yocto effective validation | functional config/recipe/layer変更時に`bitbake -e`/parse | live build treeへ変更を適用せず、imported patch hunkも不変。実効metadataは次のExecution acceptanceまでUNKNOWN | baseline hash、working log | NOT TRIGGERED |
| Git worktree | canonical repositoryで作業 | canonical repositoryのlinked feature worktreeで作業 | canonical guard | PASS |
| branch flow | `main → dev-* → feature-*` | `dev-foundation`とticket feature branchを作成 | Git refs | PASS |
| commit/push | fresh cloneが成果物を取得できる | final implementationは未commit、remote branch未作成 | Git status/remote refs | FAIL |

### Act

privacy監査で発見したproject-layer除外、圧縮IPv6/private hostname、Yocto `tmp/work` task-log discoveryを是正し、全working-tree gateを再実行した。独立checker PASS後にimplementationをcommitし、clean cloneで同じgateを実行してから`dev-foundation`とfeature branchをpushする。push確認後にFLR-0008を次のWIPへする。

## Unknowns

- fresh Codex taskでのcustom agent/MCP override読み込み。
- GitHub repository settingsでrequired checkを有効化できているか。
- `aglsetup.sh`のmode-only local変更がbuild再現に必要か。
- fixed snapshotをmini PCの同一commitから読み、Yocto effective metadata/parseを通した結果。

## PDCA checker

- Status: PASS WITH CONDITIONS
- Checked by: independent checker role
- Findings: privacy、MCP境界、remote revision/cleanliness、large-log、schema、response locator、lifecycle evidenceを再監査し、working-tree blockerなし。commit/push/clean-clone CI、実mini-PC handshake、fresh custom-agent override、BitBake/QEMU/Raspberry Pi runtimeは条件として未達またはUNKNOWN。
