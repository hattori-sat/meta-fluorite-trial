# 最新イメージの並列確認メモ

更新日: 2026-09-08

> この文書の旧rootfsはMac側の容量整理により保持対象から外しました。現在
> の確認対象は `work/parallel-verification-latest-shadow-disabled-image-20260907152732.md`
> と `work/artifacts/latest-image-shadow-disable-20260907152732/` です。旧QMP
> 写真・markers・ログは証拠として保持しています。

## Mac側の配置

このリポジトリの以下にmini PCからSCPした最新成果物を置いています。

```text
work/artifacts/latest-image-20260907130705/
```

- rootfs: `agl-ivi-image-flutter-qemux86-64.rootfs-20260907130705.ext4`
- QEMU設定: `agl-ivi-image-flutter-qemux86-64.rootfs-20260907130705.qemuboot.conf`
- rootfs SHA-256: `b98c48343db42e36915b3262f4e27c420915bb24d662ade0514f09f6d25e52f0`
- qemuboot SHA-256: `fcfad03fae29844f16e4a1e750ab1b532f49b0dce487cce68117bfc913417470`

Mac側での照合:

```sh
shasum -a 256 work/artifacts/latest-image-20260907130705/*
```

このイメージは、今回の影無効化診断patchをまだ含まない最新の権威ビルドです。qemuboot設定にはビルド機側のパスが含まれるため、Macで直接起動する場合は設定を書き換えず、同一成果物をMac側の役割パスへ展開してから実行してください。証拠性を優先する場合は、ビルド機側の固定QEMU手順を使います。

## 現在の決定的なQMP写真

- 8灯成功: `work/evidence/flr0048-model1-env0-light8-native-trace/light8.png`
- 9灯失敗（通常）: `work/evidence/flr0048-model1-env0-light9-native-trace/light9.png`
- 9灯失敗（162/164除外）: `work/evidence/flr0048-model1-env0-light9-skip162-164-native-trace/light9-skip162-164.png`
- 9灯全属性採取: `work/evidence/flr0048-model1-env0-light9-all-native-props/light9-all.png`

写真はすべてQMPの`screendump`相当のピクセル取得で、ウィンドウ座標のスクリーンショットではありません。9灯ケースはHUDとFPS/CPU/GPU/System delayだけが表示され、中央の本番GLBは表示されません。各ケースでQMPの`SHUTDOWN reason=host-qmp-quit`を受け、QEMU/runqemu/flutter-autoの残留がないことを確認しています。

## 今回までの解析結果

事実:

1. `model=1`、環境ステージ無効で、8灯は本番GLBのピクセルが出ます。
2. 9灯ではGLBが出ず、HUDだけになります。
3. 8灯と9灯のnative light component、instance、Scene登録は成立します。
4. 最初の8灯（GUID 126〜140）は `cast_shadows=false` です。
5. 9灯目のGUID 162は `cast_shadows=true`、強度`2.4e7`、falloff`300.1`です。
6. GUID 162を除外してGUID 164を9灯目にしても失敗します。162固有だけでは説明できません。
7. GUID 162と164を除外して後続ライトを9灯目にしてもQMPはHUDだけです。総数または、後続ライトで初めて入る共通の描画資源経路が候補です。
8. Filamentの一般ライト上限は255であり、9灯はその上限ではありません。

推論:

- 現時点の最有力仮説は、9灯目で点光源の影マップ準備が有効になり、モデル描画または提示経路を壊していることです。
- まだ確定ではありません。影を診断的に無効化するフラグをDevtoolソースへ追加済みですが、そのpatchを含むイメージは未ビルドです。

## 次の再現手順

1. MacのDevtoolコンテナは`fluorite-mac-devtool`を再利用する。
2. `work/devtool-edit/flr0048/light_system.cc`の変更をDevtool管理ソースへ反映し、ソースGitへローカルコミットする。
3. Yocto公式Devtoolでpatchを生成し、`layers/meta-fluorite-trial`へ登録する。
4. Macでレイヤー変更をコミットし、既知のbaseからGit bundleを作る。
5. bundleを固定receiverへ送り、mini PCの固定build directory/TMPDIRで`do_patch`、`do_compile`、イメージbuildを順に実行する。
6. 新しいrootfsのハッシュを記録し、1台だけQEMUを起動する。
7. ゲスト内で次の環境変数を指定して検証する。

```text
FLR0026_MODEL_LIMIT=1
FLR0026_SKIP_ENVIRONMENT_STAGES=1
FLR0026_NATIVE_LIGHT_LIMIT=9
FLR0026_NATIVE_LIGHT_DISABLE_SHADOWS=1
```

8. QMPで画像を取得し、8灯成功・9灯通常・9灯影無効化を比較する。
9. QMPのquitハンドシェイク、`SHUTDOWN reason=host-qmp-quit`、残留プロセスなしを確認する。

長時間buildの前には、`MACHINE`、`DISTRO`、`BBLAYERS`、`SRC_URI`、`TMPDIR`と使用容量を確認する。protectedな`downloads`、`sstate-cache`、`tmp`は削除しない。

関連チケット: `work/tickets/FLR-0048-isolate-light-count-vs-identity.md`
