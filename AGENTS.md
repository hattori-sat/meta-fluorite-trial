# AGENTS.md

## Operating mode

- 作業開始時に`scripts/assert-canonical-repository.sh`を実行する。失敗したrepositoryでは調査以外の変更を止める。
- 編集前に短い計画を示す。
- Facts、inferences、hypotheses、UNKNOWNを分ける。
- Yocto調査はmanifest、conf、layer、recipe、logの順で証拠を集める。
- 非自明な問題は最低2つの仮説または実装案を比較する。
- 変更は最小限にし、build-time、runtime、packaging、integration riskへの影響を説明する。
- `TASKS.md`を確認し、原則として1件だけを`In Progress`にする。
- ticketなしに非自明な調査・実装・buildを開始しない。
- Plan / Do / Check / Actを更新し、commandと結果をworking logへ追記する。
- facts、inferences、hypotheses、decisionsを混ぜず、対応するcontextまたはticketへ記録する。
- 新しい問題を発見しても現在のscopeへ混ぜず、別ticketとしてInboxへ置く。
- 問題解決は、目的確認、4W1H（Whyを除く）による層別、重点選定、process解析、問題点特定、真因分析、対策、PDCAの順で進める。
- 4W1HのWhoは個人名でなくrole・責務で記録する。
- 原因仮説はprocess上の問題点を特定してから立て、相関だけで真因と断定しない。

## Safety

- AGL/Yoctoのsource取得、environment初期化、parse、build、cacheはLinux build host roleだけで扱う。Macはartifactを受け取りQEMU検証を行う。
- AGL sourceを新規取得・更新する前に公式`trout` manifest手順、fixed manifest、active ticket、approvalを照合する。
- build hostからMacへ渡すartifactはrevision、image identity、SHA-256、package manifest、boot parameterをindex化し、timestampだけで選ばない。
- `/mnt/yocto/**/{downloads,sstate-cache,tmp}` を削除しない。
- `bitbake -c cleanall` を実行しない。
- `bitbake -c cleansstate` は根拠と明示承認なしに実行しない。
- baseline採取前に `repo sync`、branch変更、SRCREV更新を行わない。
- 既存変更を戻さず、秘密情報、鍵、巨大log、deploy artifactをGitへ追加しない。
- commitとpushはユーザーの明示承認後にのみ行う。
- 氏名、個人account、IP address、hostname、個人名を含む絶対path、credentialをGitへ記録しない。
- 接続情報はGit対象外のlocal環境変数へ置き、文書とlogでは`$BUILD_HOST`、`$AGL_ROOT`などのrole名を使う。

## Naming

製品名は `Fluorite`。既存の `flourite` パスは互換性のため変更しない。

## Validation

- host roleと検証目的を先に固定し、Linux `runqemu`の結果とmacOS QEMUの結果を同じstratumへ混ぜない。
- 対象build directoryへ設定変更を適用した後は `bitbake -e agl-ivi-image-flutter` の実効値を確認する。
- recipe/layerのfunctional content変更後は最小のparseまたは対象taskから検証し、長時間build開始前にユーザーへ知らせる。未適用のevidence snapshotやidentity metadataだけの変更は、非適用理由とruntime UNKNOWNをticketへ記録する。
- PDCA checkerの判定が`FAIL`または`UNKNOWN`の場合、証拠不足を解消してからticketをDoneにする。
- privacy checkが失敗した場合は全作業を止め、値を再掲せずredactしてから続行する。

## Git workflow

- `main`は検証済み安定点とし、直接commitしない。
- 開発区切りごとに`main`から`dev-<milestone>`を作る。
- ticketごとに対象`dev-*`から`feature-<ticket>-<slug>`を作る。
- Pull requestは`feature-*`から`dev-*`、区切りのSuccess criteria達成後に`dev-*`から`main`へ送る。
- branchをまたいで未関連ticketを混在させない。
- branch作成、commit、push、PRの状態をworking logへ記録する。
