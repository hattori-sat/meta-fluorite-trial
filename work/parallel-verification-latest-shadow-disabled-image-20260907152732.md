# 最新影無効化診断イメージの並列確認メモ

更新日: 2026-09-08

## Mac側の配置

今回のMini PC権威ビルド成果物は、このリポジトリの以下にあります。

```text
work/artifacts/latest-image-shadow-disable-20260907152732/
```

- rootfs: `agl-ivi-image-flutter-qemux86-64.rootfs-20260907152732.ext4`
- qemuboot: `agl-ivi-image-flutter-qemux86-64.rootfs-20260907152732.qemuboot.conf`
- rootfs SHA-256: `7f44934f5366e0dc2bf2c7dd2a5aba4b0e82f2c0630e725618d58103bb233442`
- qemuboot SHA-256: `9d5a775cd1b29d10def96d365675e704a99fa2840b2b5d009c303e5e1a132e4e`

rootfsは大容量成果物のためGitには追加していません。Mac側では次で照合できます。

```sh
shasum -a 256 work/artifacts/latest-image-shadow-disable-20260907152732/*
```

## 対応するQMP写真

```text
work/evidence/flr0048-shadow-disabled/shadow-disabled-model1.png
```

これはQEMUウィンドウの撮影ではなく、Mini PC上のQMP `screendump` で取得
した1280x800のゲストピクセルです。写真はHUDとCPU/GPU/System delayを
表示しますが、中央のproduction GLBは表示していません。

## 再現条件

Example Demoを正しい`agl-driver`権限と`fluorite` app-id経路で起動し、次を
同じプロセス環境へ渡します。

```text
FLR0026_NATIVE_MODEL_LIMIT=1
FLR0026_NATIVE_SKIP_ENVIRONMENT=1
FLR0026_NATIVE_LIGHT_LIMIT=9
FLR0026_NATIVE_LIGHT_DISABLE_SHADOWS=1
```

Mini PC側の固定receiver/build/TMPDIR/QEMU手順は、既存の
`work/parallel-verification-latest-image-20260907130705.md` と
`docs/mac-devtool-bundle-workflow.md` を参照してください。新しいcontainer、
receiver、TMPDIR、QEMUは作成していません。

## 判定

影無効化分岐は`/usr/bin/flutter-auto`の静的文字列でも確認でき、パッチ適用・
compile・full imageも成功しました。それでも3Dが出ないため、影だけが9灯
境界の原因という仮説は反証済みです。
