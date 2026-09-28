# Yoctoイメージのランタイム解析・修正ループ

この文書は、Yoctoで作成した組み込みLinuxイメージを、静的解析とランタイム解析で切り分け、MacとMini PCに分かれた環境で再現可能に修正するためのプロジェクト運用記録である。3Dに限らず、サービス、GUI、デバイス、ドライバ、IPC、入力、表示の不具合に適用する。

詳細な汎用手順は`yocto-runtime-debugging` Skillを参照し、コンテキスト圧縮に耐えるcheckpoint契約は[project-local yocto-runtime-checkpointing skill](../skills/yocto-runtime-checkpointing/SKILL.md)と`./scripts/runtime-checkpoint.sh`を参照する。MacからMini PCへの既存プロジェクト手順は[mac-devtool-bundle-workflow.md](mac-devtool-bundle-workflow.md)を参照する。`devtool`の仕様は[Yocto Project devtool reference](https://docs.yoctoproject.org/dev/ref-manual/devtool-reference.html)と[Development Tasks Manual: using devtool](https://docs.yoctoproject.org/dev/dev-manual/devtool.html)を正とし、インストール済みreleaseの`devtool --help`も確認する。

## 0. Markdown ticketを作業単位にする

1つのMarkdown ticketは、独立して判定できる1つの作業単位だけを持つ。完了条件、scope、証拠が揃ったら、そのticketのPDCAを閉じ、次の検証は必ず新しいMarkdown ticketに切る。同じ製品目標でも、別の仮説・境界・成功条件なら同じticketへ追記しない。前ticketの結論と`evidence_id`だけをリンクして引き継ぐ。

各作業ループの開始前後には`runtime-checkpoint.sh verify`を実行し、ループ境界では`runtime-checkpoint.sh new`でFacts/Inferences/Hypotheses/UNKNOWN/Evidence/Decision/Next actionを同じworking logへ追加する。新しい独立課題は先にInbox ticketを作り、現在のticketへ混ぜない。失敗コマンドも削除せず、最初の actionable errorと成功結果を同じcheckpointへ残す。

画面や表示状態を主張するticketには、`Visual evidence`欄を必須にする。QMP-only画像（または承認済み実機capture）、画像で見える内容、run/image identity、取得時刻、pixel count/bounding box/SHA-256またはevidence IDを記録する。大きな画像本体はGit外へ置き、ticketから添付・リンクし、Gitにはindexとchecksumだけを残す。画像が取れていない場合はUNKNOWNとし、想定画面を実測結果として書かない。

## 1. まず期待値と実測値を分ける

最初に「本来どうあるべきか」を観測可能な契約として書く。例は、serviceが`active (running)`になる、processがdeviceをopenしてloopを進める、frameがsubmit/commitされ指定pixel regionが変化する、button入力でrouteが遷移する、などである。

次に、同じimage revision・target identity・stimulusを付けた実測値を書く。黒画面、timeout、status 139、FPS 0は症状であり、原因名ではない。最初に欠けたmarker、戻らなかったsyscall、失敗したservice、変化しなかったpixelを一次境界とする。

## 2. 層別して仮説を比較する

What/When/Where/Who/Howで整理する。

| 観点 | 確認対象 |
| --- | --- |
| What | 期待イベント、実測イベント、error、exit status、pixel |
| When | boot-relative/monotonic timestamp、最初の不一致 |
| Where | layer、recipe、service、process/thread、device、socket、surface |
| Who | source、build、deploy、runtimeを担当するrole |
| How | input、callback、IPC、syscall、driver、compositorの経路 |

変更前に最低2つの説明を並べる。典型的には、image/package設定、systemd/process起動、device/driver、native bridge、resource/pipeline、Wayland/compositorのいずれかである。一つのログ行から真因を断定しない。

## 3. 静的解析

権威build環境でmanifest、conf、layer、recipe、bbappend/bbclass、override、依存関係、patch順を確認する。

```sh
bitbake-layers show-layers
bitbake-layers show-recipes <recipe>
bitbake-layers show-appends <recipe>
bitbake -e <recipe> > "$EVIDENCE_ROOT/recipe.env.txt"
bitbake -e agl-ivi-image-flutter > "$EVIDENCE_ROOT/image.env.txt"
```

`SRCREV`、`S`、`WORKDIR`、実効`SRC_URI`、`PACKAGECONFIG`、`DEPENDS`、`RDEPENDS`、`MACHINE`、`DISTRO`、`BBLAYERS`、`DL_DIR`、`SSTATE_DIR`、`TMPDIR`を記録する。patch番号の大小だけで適用順を判断しない。

sourceはcall chain、thread、callback、所有権、resource lifetimeを読む。binaryでは利用可能なら`readelf`、`nm`、`objdump`、`addr2line`、`gdb`でアドレスをsource境界に戻す。debug symbolやtoolが無い場合はUNKNOWNとして記録し、推測で補わない。

## 4. ランタイム解析

イメージに収録されたtoolを確認し、短く再現可能な観測を行う。

```sh
systemctl list-units --type=service --all
systemctl status "$APP_UNIT" "$COMPOSITOR_UNIT" --no-pager
journalctl -b -u "$APP_UNIT" --no-pager
journalctl -b -u "$COMPOSITOR_UNIT" --no-pager
journalctl -k -b --no-pager
coredumpctl list --boot --no-pager
```

processが生きていればGDB attachでthread/backtrace/shared libraryを採取する。再現の短い窓では`strace -ff -ttt -T -yy`で`openat`、`ioctl`、`mmap`、`poll/epoll`、`futex`、Waylandの`sendmsg/recvmsg`を確認する。`/dev/dri/*`のopen、Vulkan/DRM ioctl、futexの反復、戻らないpoll、coredumpの最初のnative frameをjournalのmonotonic timestampと突き合わせる。

表示不具合は、process起動 → device/driver初期化 → scene/entity/resource準備 → draw command記録 → queue submit → present/buffer handoff → surface attach/commit → target pixel、の順で個別にPASS/FAIL/UNKNOWNにする。2D HUDが見えることは3Dの証明ではなく、fixtureやclear colorのpixelも本番sceneの証明ではない。

### 4.1 raw logと対話表示を分離する

raw serial/journal logは証跡ディレクトリへそのまま保存し、対話中に全量を表示しない。
次のslicerはraw logを変更せず、first actionable error、native/ViewTarget、draw、
present、Waylandの境界だけを順序付きで最大120行に制限し、カテゴリ別件数も出す。

```sh
scripts/runtime-log-slice.sh --max-lines 120 "$RAW_RUNTIME_LOG"
```

`--max-lines`を下げてもfirst errorは最大8件まで残る。selected markerが上限を
超えた場合は先頭/末尾と省略件数だけを表示する。raw logのpath、SHA-256、slicerの
出力をticketへ記録し、slicerの短い出力をraw evidenceの代わりに扱わない。

## 5. 真因分析と対策

「rendererが壊れた」ではなく、「現在のframe promiseを完了する前に後続frameをscheduleしている」「invalid resourceをdriver commandへ渡している」のように、問題のある行動・所作を記述する。その行動に対してなぜを繰り返し、source/configurationで変更可能な課題へ落とす。

```text
hypothesis | prediction | experiment | observed result | decision
```

最小のdiagnostic switchまたはproduction fixを一つだけ選び、結果がどうなら仮説を棄却するかを先に書く。diagnostic switchで安定しただけなら、要求された本番動作の成功とは数えない。

## 6. Devtoolでの修正とpatch化

source変更はMacの固定Docker container内にある既存のDevtool管理sourceで行う。既存recipe patchがある場合は、先行patch適用後のsourceを同じDevtool local Gitのbaselineとしてcommitしてから、新しいsource変更をcommitする。毎回container、source workspace、build/TMPDIRを作り直さない。

```sh
devtool status
devtool modify <recipe>
git diff --check
git add <source-file>
git commit -m '<source change>'
devtool finish <recipe> <temporary-project-layer> --mode patch
```

Yocto標準では、`devtool modify`でrecipeの既存patchをlocal Gitへ取り込み、source変更をcommitし、開発中のrecipe更新には`devtool update-recipe`を使える。今回の恒久layerへのhandoffでは、workspaceの状態を戻しながらlayerへ反映する公式の`devtool finish`を採用する。この運用でlayer patchを生成する経路は`devtool finish <recipe> <layer> --mode patch`だけである。`git diff`、`git format-patch`、quiltでlayer patchを代作しない。`finish`が失敗した場合はそこで停止して原因を記録し、先行patch適用後のbaseline、`SRC_URI`、patch順を同じDevtool workspaceで直して再実行する。hunk offsetや生成patch本文を手で直してはならない。生成物を変更せず、`layers/meta-fluorite-trial`の対象recipe配下へ登録し、layer変更をfeature branchへローカルcommitする。

## 7. 2台間のhandoffと権威build

Mac側のlayer commitをbase/tip付きGit bundleにし、fixed receiverへ送る。Mini PCではbundleのchecksumとexact revisionを確認してreceiverだけをcheckoutし、canonical checkoutは変更しない。Mini PCが唯一の権威BitBake環境である。

```sh
git bundle create <bundle> <base-commit>..<tip-commit>
git bundle verify <bundle>
shasum -a 256 <bundle>
```

Mini PCでは、同じbuild directory、TMPDIR、downloads、sstate-cacheを再利用する。`bitbake -e`で実効設定とpatch orderを確認し、`do_patch`、対象`do_compile`、full imageの順に進める。失敗したら最初のtaskで停止する。cherry-pickは将来のPR作成時だけに使う。

## 8. QEMU・入力・証拠

QEMUは一度に1個だけ起動し、承認済みprofileとexact image hashを使う。画像の主証拠はQMP framebufferのQMP-only screenshotとし、early/late、input座標、route、pixel count/bounding box/SHA-256を記録する。macOS window screenshotやログmarkerだけでvisible pixelを主張しない。

終了時は記録したQMP socketへ`quit`を送り、socket/PIDとQEMU、app、compositorの残留を確認する。global `pkill`やsocket削除でlive processを隠さない。

## 9. 完了条件

完了は「buildできた」ではなく、exact image・source/layer revision・target identityが対応し、要求された動作がQMP-only pixel証拠で確認され、journal/kernel/coredumpに新しい異常がなく、指定された入力・scene遷移を通過し、再現回数とteardown条件を満たした時だけとする。必要な証拠が欠ける場合はUNKNOWNまたはFAILとしてticketを開いたままにする。

完了後はticketをDoneまたはWaitingへ遷移し、次の独立した作業を新しいMarkdown ticketとして作成する。1つのticketを製品目標の完了まで使い続けない。

## 実績から得た注意点

- 2D HUD、CPU/GPU/FPSが表示されてもnative 3Dは未確認の場合がある。
- 自作fixtureの成功は、Wayland/Vulkan/Filament最小経路の証明であってproduction resourceの成功ではない。
- `started=false`、fence timeout、queue待ちは結果として現れることがあるため、最初の失敗境界と分けて扱う。
- Docker daemonやVMの停止はFluoriteの原因と混ぜず、Docker/VMログを別の外部障害として記録する。
- `downloads`、`sstate-cache`、active `tmp`、証拠、ユーザーの未追跡変更を、容量対策のために一括削除しない。
