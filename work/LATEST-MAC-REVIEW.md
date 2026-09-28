# FLR-0049 最新Mac側確認案内

## 現在の最新run（透明Alphaビルド、QMP動画）

最新の権威イメージは、MacでDevtoolから生成した透明Alphaパッチを含めて
Mini PCで11748/11748タスク成功後に作成したものです。確認対象は
`work/latest-mac/flr0049-002f86e/alpha-build-ffab658/` にあります。

- `qmp-alpha-runtime.mp4`: QMP framebufferのみから作成した1280x800、1 fps、
  39秒の動画。SHA-256は
  `35537195f38d4cfa80e54dbb3c00dd9685cffdaa273f046459a1d9925de6e209`。
- `qmp-alpha-runtime-representative.png`: 上記動画の代表フレーム。3Dの
  Sequoia車体と赤い灯火が見える。SHA-256は
  `765ce7cff84f18c993a6a65d247fa74478f419371bec4220b3998c2aee0f7864`。
- `runtime-alpha.log`: Alpha選択、モデル読込、scene/renderable、presentの
  対応ログ。

このrunでは`FLR0026_VK_COMPOSITE_ALPHA transparent=true supported=0x3
selected=0x2`を確認しました。3D実画素はPASSですが、同じフレームに2D HUD/
CPU/FPSが現れるところまでは未達です。したがって、Alphaパッチで3D描画は壊れて
いない一方、native面とFlutter 2D面の合成はUNKNOWNとして次の切り分けへ進みます。

QEMUはQMP `quit`で終了し、`host-qmp-quit`、QEMU/runqemu/flutter-auto/QMP
socket残留なしを確認済みです。

動画を再現する場合は`docs/mac-devtool-bundle-workflow.md`の「動画が必要な
検証」手順を使います。連続フレームは同じQMP証跡run directoryへ置き、ビルド用
TMPDIRやコンテナを増やしません。

## 最新結果（2026-09-08）

readback診断を有効にしない同一rootfs・同一固定QEMUで、本番
`sequoia_ngp.glb`の3D車体がQMP framebufferへ表示された。確認画像は
`no-readback-35s.png`と`no-readback-60s.png`で、両方とも35秒/60秒時点の
QMP専用取得である。両画像のSHA-256は同一で、候補領域
`[200,100,400,250]`の変更画素は`65299/100000`だった。

これは「本番GLBが全く描画できない」という仮説を棄却する証拠である。
一方、ネイティブ面が白背景で前面を覆うため、この条件では2D HUDは見えない。
2D HUDのbaselineは下記の`qmp-latest-20s.png`を参照する。

対応ログは`runtime-no-readback.log`、要約は
`runtime-no-readback-summary.txt`。約60秒時点でpage fault/Oops/SIGSEGVはなく、
QMP終了後のQEMU、flutter-auto、QMP socket残留もない。

## 確認場所

すべての確認対象は次のディレクトリです。

`work/latest-mac/flr0049-002f86e/`

まず見るファイル:

- `qmp-latest-20s.png`: 2D HUD、CPU/GPU/FPSのbaseline。
- `route17-shm-cube.png`: 自作SHMキューブがQMP framebufferに出た証拠。
- `route18-shm-skip-stack.png`: stack probe条件を変えたA/B画像。
- `serial-19.log`: 最新診断runのシリアル出力。
- `no-readback-35s.png`: readbackなしproduction SequoiaのQMP画像。
- `no-readback-60s.png`: 同一画像の60秒時点安定性確認。
- `runtime-no-readback-summary.txt`: 同一runのruntime到達点とクラッシュ検索結果。
- `handoff.md`: commit、bundle、rootfs、checksum、判定の記録。

## 並列確認の手順

1. `qmp-latest-20s.png`で2D baselineを確認する。
2. `route17-shm-cube.png`で、自作キューブが画面中央の黒いネイティブ領域へ表示されていることを確認する。
3. `route18-shm-skip-stack.png`と比較し、stack条件変更で自作キューブが消えていないことを確認する。
4. `serial-19.log`で`NATIVE_READBACK_`、`FRAME_BEGIN`、`WAYLAND_SHM_PROBE_`を検索し、画像と同じrunの証拠であることを確認する。
5. `handoff.md`の「production 3D」の判定を確認する。本番Filament sceneが実画素で見えたとは、別途QMP画像で確認できるまで判定しない。

### 最新runの注意

`serial-19.log`には、約133.4秒時点の`FEngine::loop`（ゲストPID 673）のページフォルト/Oopsが含まれます。自作SHMキューブの画像証拠、本番Filament 3Dの成功判定、runtime crashの判定は分離してください。

readbackなしの安定runでは同じpage faultを再現しなかったため、readbackは表示成立条件ではなく、現時点では別チケット相当の診断経路として扱う。

## 次回の再現入口

- Mac側の作業tree: `work/` と `layers/meta-fluorite-trial/`
- 最新bundle: `work/flr0049-002f86e.bundle`
- ソース/build artifact tip: `002f86e8c39111f0ae9622ad802310f3a311f86f`
- 最新証跡・案内コミット: `56fd895`
- Mini PC側の固定receiver、build directory、TMPDIRは `handoff.md` に記録したものを再利用する。
- 画像取得はQMP専用capture手順を使い、ホストGUIのスクリーンショットは証拠にしない。
