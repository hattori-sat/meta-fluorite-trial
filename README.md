# Fluorite on AGL for Raspberry Pi 4

Toyota Connected の **Fluorite** デモを Automotive Grade Linux (AGL) 上で再現・検証するための管理リポジトリです。

> 製品名の正式表記は `Fluorite` です。既存ビルド環境には `build-flourite` や `/mnt/yocto/flourite` という互換パスがあり、これらは改名しません。

## 現在の状態

- ベースライン: AGL `trout` / AGL 20.0.4 系、BitBake 2.8.1
- 対象: `raspberrypi4-64`、`qemux86-64`
- イメージ: `agl-ivi-image-flutter`
- build host: Git対象外のlocal設定で接続先を指定
- 調査結果: [docs/baseline-2026-07-19.md](docs/baseline-2026-07-19.md)

## ディレクトリ

- `layers/meta-local/`: Fluorite固有レイヤー、パッチ、設定fragment
- `conf/`: 採取時点のbuild別設定（参照用baseline）
- `manifests/`: AGL/Yoctoと外部レイヤーの固定revision
- `scripts/`: 非破壊の環境確認・再現補助
- `.codex/agents/`: 調査、ビルド、ログ解析、target検証の専用agent
- `TASKS.md`: WIPを制限したissue/PDCA dashboard
- `work/`: ticket、context、working log、decision、evidenceの分離保管

## 安全原則

既存の `downloads`、`sstate-cache`、`tmp` は再利用し、削除しません。`repo sync`、revision更新、`cleanall`、`cleansstate`、長時間buildはbaseline確認後に明示的に実施します。秘密情報、SSH鍵、deploy image、巨大logはGitへ登録しません。

## 次の開始点

1. この管理treeをcanonical cloneへ同期する。
2. `scripts/collect-baseline.sh` でrevisionと実効cache pathを再検証する。
3. `meta-local`、完全なfixed manifest、参照用confを取り込む。
4. `conf/` をテンプレートとして既存cacheを指すbuild directoryを初期化する。

canonical repositoryはGit remote `origin`です。Macとbuild hostの両方で`$HOME/work/meta-fluorite-trial`へclone済みです。接続先、account名、個人を識別できる絶対pathはGitへ保存しません。

## 作業管理

すべての実作業は[TASKS.md](TASKS.md)から開始します。原則として`In Progress`は1件だけです。各ticketはPlan / Do / Check / Actを持ち、実行内容を日付別working log、入力となる事実をcontext、成果物をevidence、採用判断をdecisionへ分離します。

## Git branch workflow

- `main`: 検証済みの安定点
- `dev-<milestone>`: ある程度まとまった開発区切り。`main`から作る
- `feature-<ticket>-<slug>`: 1 ticketの作業branch。対象`dev-*`から作る

Pull requestは`feature-* → dev-* → main`の順に統合します。`main`と`dev-*`へ直接commitしません。詳細は[ADR-0002](work/decisions/ADR-0002-git-branch-workflow.md)を参照してください。
