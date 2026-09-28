# FLR-0049 latest Mac-side verification handoff

このファイルは、Mini PCで権威ビルドした最新成果物をMac側で確認するための入口です。
成果物は同じticketの作業ディレクトリに集約し、QEMUのホストウィンドウではなくQMP経由で取得した画像だけを証拠にします。

## 確認場所

- 最新bundle: `work/flr0049-<commit>.bundle`
- Macへ回収した最新成果物: `work/latest-mac/flr0049-002f86e/`
- QMP framebuffer画像: `work/latest-mac/flr0049-002f86e/qmp-latest-20s.png` と `qmp-correct-control-18s.png`
- QMP raw画像: 同じディレクトリの`*.ppm`
- runtime log: 同じディレクトリの`runtime.log`、`runtime-2.log`、`runtime-3.log`
- ビルド・回収記録: `work/latest-mac/flr0049-002f86e/handoff.md`
- 今回回収した最新QMP画像: `work/latest-mac/flr0049-002f86e/route17-shm-cube.png`、`route18-shm-skip-stack.png`
- 今回回収した最新シリアルログ: `work/latest-mac/flr0049-002f86e/serial-19.log`

bundleに含めたfeature branchのcommit短縮値は`002f86e`です。IPアドレスや個人環境の絶対パスは成果物へ記録しません。

## Mac側からの回収手順

1. Mini PC側の固定receiverにbundleを渡し、Mini PCでそのcommitを展開して権威ビルドする。
2. Mini PC側でrootfs、qemuboot、runtime log、QMP画像、各SHA-256を固定成果物ディレクトリへ集める。
3. Mac側の`work/latest-mac/flr0049-<commit>/`を一度だけ作り、Mini PCからそのディレクトリへSCPする。今回の確認先は`work/latest-mac/flr0049-002f86e/`。
4. `handoff.md`のcommit、rootfs SHA-256、qemuboot SHA-256と、回収後Macで再計算したSHA-256を照合する。
5. まず`qmp-latest-20s.png`を開いて2D HUD/CPU/GPU/FPSのbaselineを確認し、次に`qmp-correct-control-18s.png`を開く。画像の取得はQMP専用スクリプトを使い、ホストGUIのスクリーンショットは証拠にしない。
6. `runtime-3.log`で`MODEL_STAGE_SCENE_ADD_DONE`、primitive/material/resource trace、readback/present markerを確認し、画像結果と同じ試験条件として記録する。shape/lightの診断制御名は`FLR0027_NATIVE_SKIP_SHAPES`と`FLR0027_NATIVE_SKIP_LIGHTS`を使う。

## 今回の回収状態

- Mini PCの権威ビルドcommit: `002f86e8c39111f0ae9622ad802310f3a311f86f`
- rootfs、qemuboot、kernelはMini PCの固定TMPDIRからMacへ再SCP済み。
- Mac側で再計算した3ファイルのSHA-256は`handoff.md`の記録と一致。
- 最新controlled QMP画像は取得済みだが、現時点では本番3Dの実画素表示成功とは判定していない。baselineの2D表示と、controlled runの診断結果を分けて確認する。
- `route17-shm-cube.png` と `route18-shm-skip-stack.png` は今回Mini PCからMacへSCPで回収したQMP専用画像で、自作SHMキューブの表示を確認できる。これは合成経路の疎通証拠であり、本番Filament 3Dの成功証拠とは分けて扱う。
- `serial-19.log` には約133.4秒時点の`FEngine::loop`（ゲストPID 673）のページフォルト/Oopsがある。最新runはruntime crashを伴うため、本番3D成功とは判定しない。

## 再現時の制約

- MacのDevtool source workspaceでソースを編集し、patchはYocto公式`devtool finish`で生成する。
- patchは`layers/meta-fluorite-trial/recipes-graphics/toyota/files/`へ置き、既存の`flutter-auto_2.0.bbappend`から登録する。
- BitBakeはMini PCだけで実行し、固定build directory・TMPDIR・receiverを再利用する。
- QEMUは常に1個だけ起動し、終了はQMPの`quit`を使ってsocketとプロセスが消えたことを確認する。
- `downloads`、`sstate-cache`、`tmp`は削除しない。
