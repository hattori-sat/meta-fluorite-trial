# Fluorite on AGL for Raspberry Pi 4

Toyota Connected の **Fluorite** デモを Automotive Grade Linux (AGL) 上で再現・検証するための管理リポジトリです。

> 製品名の正式表記は `Fluorite` です。既存ビルド環境には `build-flourite` や `/mnt/yocto/flourite` という互換パスがあり、これらは改名しません。

## 現在の状態

- ベースライン: AGL `trout` / AGL 20.0.4 系、BitBake 2.8.1
- 対象: `raspberrypi4-64`、`qemux86-64`
- イメージ: `agl-ivi-image-flutter`
- source: fixed AGL manifest、sanitized build conf、Fluorite固有`meta-fluorite-trial` layer
- automation: 8 bounded-context MCP、10 custom agent、local/CI共通gate
- build host: Git対象外のlocal設定で接続先を指定
- 調査結果: [docs/baseline-2026-07-19.md](docs/baseline-2026-07-19.md)

このrevisionで証明済みなのはrepository開発環境と採取baseline artifactのintegrityです。fresh source checkout、実効Yocto metadata、build再現、Mac QEMU上の3D描画、Raspberry Pi再build/実機動作は未検証であり、`UNKNOWN`のまま次ticketへ引き渡します。

## 最初の5分

canonical cloneのrootで実行します。setupはcheck-onlyで、package install、source sync、BitBake、QEMU起動を行いません。

```sh
make setup
make verify
```

- [開発環境のsetup](docs/setup.md)
- [AGL公式手順とMac/mini-PCの役割分離](docs/agl-official-workflow.md)
- [検証gate](docs/verification.md)
- [Agentの導入とrouting](docs/agents.md)
- [DDD bounded contexts](docs/architecture/ddd.md)
- [MCPの構成と使い方](mcp/README.md)

## ディレクトリ

- `layers/meta-fluorite-trial/`: Fluorite固有レイヤー、パッチ、設定fragment
- `conf/`: 採取時点のbuild別設定（参照用baseline）
- `manifests/`: AGL/Yoctoと外部レイヤーの固定revision
- `domains/`: bounded contextごとの用語、契約、invariant、owner
- `mcp/`: context別stdio MCPと共有transport kernel
- `runbooks/`: allowlist済みの定型command定義
- `scripts/`: 非破壊の環境確認・再現補助
- `.codex/agents/`: 調査、ビルド、ログ解析、target検証の専用agent
- `TASKS.md`: WIPを制限したissue/PDCA dashboard
- `work/`: ticket、context、working log、decision、evidenceの分離保管

## 安全原則

既存の `downloads`、`sstate-cache`、`tmp` は再利用し、削除しません。`repo sync`、revision更新、`cleanall`、`cleansstate`、長時間buildはbaseline確認後に明示的に実施します。秘密情報、SSH鍵、deploy image、巨大logはGitへ登録しません。

## 次の開始点

1. [TASKS.md](TASKS.md)でcurrent focusとWIP limitを確認する。
2. FLR-0008でFluorite 3Dのscene、操作、合格条件を固定する。
3. FLR-0002で既存imageのMac QEMU起動baselineを採る。
4. component agent/MCPへbounded queryを渡し、結果をevidence IDでticketへ戻す。
5. QEMUで合格後、FLR-0006で既存cacheを再利用してRaspberry Pi buildへ進む。

canonical repositoryはGit remote `origin`です。Macとbuild hostの両方で`$HOME/work/meta-fluorite-trial`へclone済みです。接続先、account名、個人を識別できる絶対pathはGitへ保存しません。

## 作業管理

すべての実作業は[TASKS.md](TASKS.md)から開始します。原則として`In Progress`は1件だけです。各ticketはPlan / Do / Check / Actを持ち、実行内容を日付別working log、入力となる事実をcontext、成果物をevidence、採用判断をdecisionへ分離します。

## Git branch workflow

- `main`: 検証済みの安定点
- `dev-<milestone>`: ある程度まとまった開発区切り。`main`から作る
- `feature-<ticket>-<slug>`: 1 ticketの作業branch。対象`dev-*`から作る

Pull requestは`feature-* → dev-* → main`の順に統合します。`main`と`dev-*`へ直接commitしません。詳細は[ADR-0002](work/decisions/ADR-0002-git-branch-workflow.md)を参照してください。
