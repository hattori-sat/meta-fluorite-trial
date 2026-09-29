# Mac devtool → meta-fluorite-trial → mini PC build workflow

この文書は、Fluoriteのnative/Dart変更を安全に検証するための実測済み
handoff手順である。後続のAIは、patchを直接書かず、この手順と対象ticketを
先に読むこと。ホスト・container・mount・cacheの短い契約は
[environment.md](environment.md)を正本として参照する。

## 役割分担

- Mac: canonical `meta-fluorite-trial` のfeature worktree、Podman/devtoolでの
  source編集とpatch生成、Git commit/bundle作成、QEMU実行・QEMU-only画面証跡。
- mini PC (`$BUILD_HOST`): bundleを受け取るisolated receiver、exact revisionの
  `bitbake`、image artifactの生成。canonical checkoutは変更しない。
- `do_patch`の最終判定、component compile、image build、QEMU実行はmini PC側の
  Yocto環境を正本とする。Mac側ではrecipe taskを定常ループに入れない。Macで成功しても
  mini PCの適用・build・runtime証拠の代わりにはならず、Mac側のrecipe taskは障害の
  切り分けが必要なときだけ行う任意診断とする。
- GitHub: 作業成果を置くrepository。patchは必ず
  `layers/meta-fluorite-trial` 配下に登録する。

## 絶対ルール

1. 作業開始時に `scripts/assert-canonical-repository.sh`、`TASKS.md`、対象ticket、
   working logを確認する。別repositoryを変更しない。
2. source変更はMacのPodman内devtool管理sourceで行う。agentが編集するのは
   devtool source workspaceのsource fileであり、patch fileそのものではない。
3. source変更をdevtool管理Gitへcommitし、通常recipeは`devtool finish --mode patch`、
   split componentは公式`devtool update-recipe --mode patch --append --no-remove`で
   patchを生成する。生成patchの本文を手で作成・書き換えない。
4. 生成patchは変更せず、`meta-fluorite-trial`の対象recipe配下へ移し、
   `SRC_URI`/`patchdir`へ登録する。recipe patchはGitで管理する。
5. `meta-fluorite-trial` feature branchへ適宜milestone commitする。mini PCへの
   handoffはcherry-pickではなくGit bundleを使う。cherry-pickは将来のPR作成時だけに使う。
6. mini PC上でpatchを編集しない。canonical checkoutがdirtyなら触らず、receiverを
   別directoryに作る。
7. QEMU検証はQEMU-onlyのQMP framebufferを証跡にする。不要なQEMUは試行終了時に
   QMP `quit`で終了し、`qemu-system-x86_64`が残っていないことを確認する。
8. patchのcontextが合わない場合、生成済みpatch本文を手で直さない。Devtoolの
   source workspaceで対象関数・適用順・baselineを確認し、context-safeなsource
   変更をcommitしてからpatchを再生成する。

## 1. Mac側のsource変更とpatch生成

### 1.1 worktreeとticketを固定

```sh
cd "$FLUORITE_REPO"
sh scripts/assert-canonical-repository.sh
git status --short --branch
sed -n '1,240p' TASKS.md
sed -n '1,260p' work/tickets/FLR-XXXX-*.md
```

feature worktreeをcleanにし、変更対象ticketを原則1件だけ `In Progress` にする。
既存のdirty worktreeは退避や破棄をせず、作業対象から外す。

### 1.2 Podmanとdevtoolを初期化（固定machine/containerを再利用）

Macでは、AGL sourceをread-only、project layerとbuild/downloads/sstateを既存の
作業ディレクトリ配下のbindとしてUbuntu 22.04のdevtool imageへ渡す。Yoctoの
`TMPDIR`はmacOS共有filesystemの制約を避けるため、同じ固定コンテナ内の
`/workspace/tmp`を唯一のactive TMPDIRとして使う。BitBake control socketは
`/tmp/fluorite-bitbake-control`へ置くが、これはbuild stateやTMPDIRではない。
Podman machineは初回に1台だけoperatorが準備し、wrapperは
machine/containerのライフサイクルを管理しない。ticketごとに新しいmachine、
container、volume、state directoryを作らない。

```sh
podman machine list
podman build --tag localhost/fluorite-yocto-devtool:22.04 tools/yocto-devtool
scripts/run-podman-devtool.sh status
scripts/run-podman-devtool.sh status
```

backendが無い場合だけ、operatorがrootful machineを1台準備してから続行する。
初回の`status`がPodman containerを作成し、2回目は同じcontainerを再利用する。
container ID、mount、label、state bindが変わっている場合はwrapperがcontract
mismatchとして停止する。Podman wrapperはnamed volumeを作らず、`status`実行時に
project/AGL/stateのmount権限を確認する。

Devtool操作はwrapperがMac側のUID/GIDを`podman exec --user`へ渡して実行する。
rootのままDevtoolを起動せず、source所有者のUID/GIDを指定する。rootで環境を
初期化すると、Yoctoの`Do not use Bitbake as root`チェックで停止する。

容量確認は次の読み取り専用コマンドで行う。

```sh
podman inspect fluorite-mac-devtool-podman
podman volume ls
podman system df
```

通常のticket終了時はcontainerを停止するだけにし、bind stateやmachineを削除しない。
state削除は、source workspaceと証跡が不要であることを確認し、明示承認を得た
場合だけ行う。Docker compose定義とnamed volumeは互換fallbackとしてのみ保持する。

Podman socketやbind mountへアクセスできない場合は、追加machine/containerを
作らず、最初のエラーを記録してから権限または容量を確認する。

同じbuild directoryを共有するDevtool/BitBake操作（`status`、`add`、`modify`、
`update-recipe`、`finish`、recipe task）は同時に実行しない。1操作が終了し、
BitBake server/lockの残留がないことを確認してから次を開始する。並列照会で
`Loading cache...done.` のまま停止した場合は、追加起動せずに残留を確認し、
同じcontainerで直列に再実行する。`run-mac-devtool.sh` と
`run-podman-devtool.sh` は同じ固定 `/tmp/fluorite-mac-devtool-operation.lock`
を取得してこの直列化を強制する。直接`docker exec`/`podman exec`を使わず、
必ずwrapper経由で操作する。

Macの`/tmp`は実体表示時に`/private/tmp`へ正規化される。wrapperはstate bindを
canonical pathへ正規化してからcontainer labelと比較するため、同じ既存bindを
契約不一致と誤判定しない。過去のroot-owned stateを直す全走査はownership markerが
ない初回だけ行い、必要な場合だけ`FLUORITE_MAC_DEVTOOL_REPAIR_STATE=always`で
再実行する。通常の呼出しで全stateを毎回`find/chown`してはならない。

Devtool/BitBake操作は既定300秒でboundedに終了する。開始前に前回の
`devtool`/`run-devtool`/`bitbake-server`残留を検査し、残留があれば新しい操作を
開始せず、記録されたPIDだけを回収してから再試行する。タイムアウト後にsocketや
serverを黙って再利用しない。

#### Mac側recipe taskは任意診断

Mac側の通常ループではrecipe taskを実行しない。Macの責務は、固定Podman/devtool
source workspaceで既存patchを適用したbaselineからsourceを編集・commitし、公式
`devtool update-recipe`でpatchを生成して`meta-fluorite-trial`へ登録・commitする
ところまでである。patchの適用可否は、bundleを固定receiverへ渡した後のMini PCの
`do_patch`で一度だけ判定する。

BitBake socket、xattr、provider差異を切り分ける必要がある場合に限り、次の任意診断を
使う。結果は補助情報として記録し、成功・失敗をMini PC gateの代わりにしない。

```sh
scripts/run-podman-devtool.sh recipe-task filament-vk do_patch
```

`recipe-task`はMac上では`do_patch`と`do_configure`だけを許可し、先に
`cp --preserve=xattr`を検査する。Podman providerがxattrを満たさない、または
BitBake control serverが停止しない場合は、Mac側で再試行・buildを続けず、最初の
エラーを記録してMini PCの固定buildへbundleを渡す。image taskや長時間のcompileは
Macで実行しない。

local index fileはYocto/Devtoolのこの運用に必要なファイルではなく、作成・追跡しない。
`conf/local.conf`は各buildの実行時設定であり、Macのwrapperが固定した
`DL_DIR`、`SSTATE_DIR`、`TMPDIR`の管理ブロックを冪等に維持する。これは
`meta-fluorite-trial`へcommitするlayer設定ではない。layerの追跡ファイル数とtree hashを
更新する必要がある場合だけ、`manifests/baseline-sources.lock`を同じcheckpointへ
更新する。

### 1.3 devtool source workspaceを用意

対象recipeが通常のrecipeとして解決できる場合は、`devtool modify`を使う。

```sh
devtool modify <recipe>
```

sourceが別のgit componentで、既存recipeのsource workspaceに対象ファイルが
存在しない場合は、今回実績のあるcomponent-scopedな方法を使う。

```sh
devtool add <component> <temporary-layer>
```

どちらの場合も、`devtool status`でworkspaceとrecipeを確認してから編集する。
`devtool reset`は既存変更を失う可能性があるため、明示承認なしに使わない。

### 1.4 sourceをagentが編集してsource commitを作る

devtoolが示したsource workspace内の実ファイルを読み、変更はsource側へ適用する。
必要ならsource fileを一時的にMacへ取り出して `apply_patch` で編集し、同じsource
workspaceへ戻す。patch directoryのpatchを直接編集してはいけない。

```sh
git -C "$DEVTOOL_SOURCE" diff --check
git -C "$DEVTOOL_SOURCE" add <changed-source-file>
git -C "$DEVTOOL_SOURCE" \
  -c user.name='Fluorite Devtool' \
  -c user.email='fluorite-devtool@example.invalid' \
  commit -m 'fix: describe source change'
git -C "$DEVTOOL_SOURCE" status --short --branch
```

source commitのhashと変更理由をworking logへ記録する。診断変更とproduction
fixを同じsource commitに混ぜない。

Devtool Gitのalternatesはcontainer内のLinux pathを指すため、Mac hostから
`git -C`を直接実行するとsource historyを読めない場合がある。その場合は固定
Podman wrapperのbounded source Git操作を使う。任意shellや未指定ファイルのcommitは
許可しない。

```sh
scripts/run-podman-devtool.sh source-git-status <container-source-path>
scripts/run-podman-devtool.sh source-git-diff-check <container-source-path>
scripts/run-podman-devtool.sh source-git-commit <container-source-path> \
  <relative-source-file> '<source commit message>'
scripts/run-podman-devtool.sh source-git-branch <container-source-path> \
  <new-branch-name> <baseline-or-source-commit>
```

これらは固定container内でのみsource Gitを実行する。source file自体はMacの
bind-mounted Devtool workspaceをagentが編集し、commit wrapperは変更パスが1件だけ
であることを確認した上でsource rootの`git add .`、`git commit`を実行する。
Devtoolのpatch生成はその後に実行する。

Yocto公式の既存recipe経路は`devtool modify <recipe>`である。`modify`はrecipeの
`SRC_URI`にある既存patchをsource workspaceへ適用し、local Gitのcommitとして積む。
変更後は`git add .`、`git commit`を完了してから`devtool update-recipe <recipe>`を
実行する。未commit変更は`update-recipe`の対象にならない。詳細は
[Yocto Project Reference Manualのdevtool節](https://docs.yoctoproject.org/4.0.34/ref-manual/devtool-reference.html#updating-a-recipe)
および[patch context更新のQA手順](https://docs.yoctoproject.org/5.3/ref-manual/qa-checks.html#patch-fuzz-warning)に従う。

既存recipeを扱う場合は`component-add`を使わない。`component-add`はsplit componentを
一時recipeとして登録する場合に限り、baseline commitを初期revisionとして実行する。
既存recipeのpatch履歴を含むsourceは、必ず`modify --no-extract`で開き、変更commitを
作成してから`update-recipe`する。

split componentを再登録するときは、既存のsource Gitを直接patch directoryへ戻さず、
次の順序を固定する。変更commitを先に保存し、baseline commitで新しいbranchを作成し、
`component-add`を実行し、変更commit側の新しいbranchへ戻してから`update-recipe`を実行する。
変更HEADのまま`component-add`すると、そのHEADが初期revisionになり、
`update-recipe`が差分ゼロになるため禁止する。

```sh
scripts/run-podman-devtool.sh source-git-branch <source> \
  devtool-<ticket>-baseline <baseline-commit>
scripts/run-podman-devtool.sh component-add fluorite-plugins <source>
scripts/run-podman-devtool.sh source-git-branch <source> \
  devtool-<ticket>-source <source-commit>
scripts/run-podman-devtool.sh update-recipe fluorite-plugins \
  /workspace/state/build/workspace
```

この操作はDevtoolの公式component登録・patch生成を再現するためのbounded wrapperで
あり、patch本文をagentが作る経路ではない。既存recipeがworkspaceに見えない場合に
いきなり`update-recipe`を繰り返さず、baseline登録が欠けていないかを先に確認する。

### 1.5 親recipeの`devtool finish`でpatchを生成

split componentを`flutter-auto`としてfinishしてはならない。親recipeのsource変更だけは
次のhelperを使う。helperは
`devtool status`からsource pathに一致するactive recipeを1件だけ解決し、finish先を
固定finish layerに限定し、生成patchの`From <source HEAD>`を検証してから既存の
`meta-fluorite-trial` bbappendへ1回だけ登録する。失敗時はpatch/recipeを推測せず停止
する。

```sh
scripts/finish-fluorite-devtool-patch.sh \
  /workspace/state/build/workspace/sources/<parent-source> \
  layers/meta-fluorite-trial/recipes-graphics/toyota/files/<NNNN>-<slug>.patch \
  layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend
```

このhelperはcanonical layerへ`devtool finish`を向けない。既存patchとの重複、
patchdir違い、source dirty、active recipeの0件/複数件、生成patchの0件/複数件、
canonical finish scaffoldをfail-closedで拒否する。生成patch本文は変更せず、rawの
Devtool出力は必要ならticketのrole-based evidenceへ保存する。

### 1.5.1 split componentは`update-recipe`を使う

`ivi-homescreen-plugins`のようにrecipe内の`patchdir`へ戻すcomponentは、
`scripts/rebase-fluorite-devtool-component.sh`を使う。このhelperはbaselineと
source commitを引数に取り、active登録確認、baseline branch、公式`component-add`、
source branch、公式`update-recipe --mode patch --append --no-remove`、source HEADの
`From`一致、byte-identical copy、単一registration、baseline lock更新を直列に行う。

```sh
scripts/rebase-fluorite-devtool-component.sh \
  FLR-XXXX fluorite-plugins \
  /workspace/state/build/workspace/sources/fluorite-plugins \
  <baseline-commit> <source-commit> \
  layers/meta-fluorite-trial/recipes-graphics/toyota/files/<NNNN>-<slug>.patch \
  layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend \
  ivi-homescreen-plugins
```

split componentで`finish-fluorite-devtool-patch.sh`を使ったり、生成patchを
直接作成・編集したりしない。

```sh
devtool finish <recipe> "$TEMP_LAYER" --mode patch
```

`finish_rc=0`、生成patch名、source commit由来のheader、変更対象を確認する。
生成物をそのまま `meta-fluorite-trial`へ移す。

```sh
cp "$TEMP_LAYER/recipes-graphics/.../files/0001-...patch" \
  "$FLUORITE_REPO/layers/meta-fluorite-trial/recipes-graphics/.../files/00NN-...patch"
```

コピー後にpatch本文を整形したり、手書きhunkを追加したりしない。必要な修正は
source workspaceへ戻ってsource commitを更新し、もう一度 `devtool finish`する。

既存recipeがread-onlyの別layerにあり、恒久layerがbbappend中心の場合は、同じ
Podman state bind内の固定finish layerを使う。これはticketごとに作り直さず、
wrapperがリポジトリのtemplateから一度だけ同期する。recipe本体を恒久layerへ
移動させる必要はなく、finish layerのpatchだけを正本layerへ移す。

```sh
scripts/run-podman-devtool.sh finish filament-vk \
  /workspace/state/build/workspace/finish-layer
```

このrecipe形状では、生成物に既存layer patchが再出力されることがある。既存patch
と生成patchのSHA-256を比較し、既存と同一のものは再登録せず、新しいsource commit
に対応するpatchだけを変更せずに`meta-fluorite-trial`へコピーする。finish先を
元recipeのread-only layerへ向けたり、生成patchのhunkを手で編集したりしない。

split componentを既存recipeの`patchdir`へ登録する場合だけは、元recipeそのものを
`modify`するのではなく、対象サブディレクトリを表す合成component recipeを
baseline commitで公式`devtool add`した後、新source commitをcheckoutし、公式の
`update-recipe`で一時workspace layerへ出力する。この例外ではsource pathを一つの
recipeだけに登録する。同じsource pathへ`flutter-auto`とcomponent recipeを同時登録
してはならない。

```sh
devtool add fluorite-plugins "$DEVTOOL_SOURCE_AT_BASELINE"
# source側で変更をcommitし、DEVTOOL_SOURCE_AT_BASELINEへcheckout
devtool update-recipe fluorite-plugins --mode patch \
  --append /workspace/build/workspace --no-remove
```

出力patchを変更せず、対象recipeのfilesへコピーして`patchdir`付きで登録する。
一時component recipeをworkspaceから片付ける必要がある場合だけ、同じ操作を
直列にした上で`devtool finish`を続けて実行する。既存のtarget recipeを直接
finishすると、source commitが既にbaselineとして扱われている場合に既存patchを
削除することがあるため、生成patchとappend差分を確認してから行う。

共有workspaceでcomponentの基準を切り替えるときは、上記の手動列を繰り返さず、
1.9の`rebase-fluorite-devtool-component.sh`を使う。これにより`reset`、`add`、
`update-recipe`、canonical registration、baseline lock更新が固定container・
固定operation lockの直列実行に入り、先行patch適用済みbaselineを明示できる。
`run-mac-devtool.sh`は互換fallbackとして残すが、split componentのrebaseでは使わない。
生成物は`workspace/appends`側を確認し、`attic`に残った旧生成物を取り込まない。

### 1.6 過去patchをdevtool local Gitへ取り込む

既存patchがlayerに手書きで積まれている場合、そのままupstream sourceから
新patchを作ると、recipeが先行patchを適用した後のsourceとhunk contextが一致
しないことがある。新しい変更の前に、対象recipeが実際に使うsourceへ過去patch
を取り込んだ状態をdevtool local Gitのbaselineとして記録する。

1. 対象recipeのupstream sourceを`devtool modify`（通常recipe）または
   component-scopedな`devtool add`（split component）でsource workspaceにする。
   `devtool status`でrecipe名とsource pathが一意であることを確認する。
2. recipeの`SRC_URI`にある過去patchを、適用順どおりsourceへ適用する。最初は
   `bitbake -c do_patch -f <recipe>`で実効sourceを作り、適用後の対象fileを
   そのままMacのdevtool sourceへ戻す方法が最も確実である。patch fileを手で
   書き換えない。
3. 過去patch適用済みのsourceをdevtool local Gitへ`baseline: import existing
   recipe patches`としてcommitする。複数componentはcomponentごとにbaselineを
   作り、無関係なcomponentの変更を混ぜない。
4. そのbaseline commitを起点にdevtoolを再登録し、新しい変更だけをsourceへ
   編集し、`git add .`と`git commit`を行う。`devtool update-recipe --mode patch`または`devtool finish --mode patch`の生成patchに新変更だけが
   含まれ、recipeの先行patch適用後にもcleanに適用できることを確認する。

```sh
# devtool source側で、実効sourceをbaselineとして記録する例
git -C "$DEVTOOL_SOURCE" checkout -b devtool-baseline-<ticket> <upstream-rev>
cp "$EFFECTIVE_SOURCE_FILE" "$DEVTOOL_SOURCE/<same-relative-path>"
git -C "$DEVTOOL_SOURCE" add <same-relative-path>
git -C "$DEVTOOL_SOURCE" commit -m 'baseline: import existing recipe patches'

# baseline commitをrecipe起点として再登録してから、新変更を追加する
devtool reset --no-clean <recipe>
devtool add <recipe> "$DEVTOOL_SOURCE"
# agent edits source files here, then commits only the new change
devtool finish <recipe> "$TEMP_LAYER" --mode patch
```

`devtool add`直後に新変更済みsourceを登録すると、devtoolがその変更をbase
revisionとして扱い、`No patches or files need updating`になることがある。必ず
「baseline commitで登録→新変更commit→finish」の順序にする。sourceがdetached
HEADだとfinishできないため、専用branchをcheckoutする。

生成patchを`git apply --check`または同じrecipeの`do_patch`でclean sourceへ
適用できることを確認してから、`meta-fluorite-trial`へ配置・登録する。

このプロジェクトでは、元recipeがread-onlyの別layerにあり、恒久layerがbbappend
中心である。したがってfinishの出力先は、repository内の
`tools/yocto-devtool/finish-layer` templateから固定stateへ同期される一つの
finish layerとする。wrapperがrecipe配置用の最小placeholderを含むlayerを用意する
ため、ticketごとに一時layerを作らない。

```sh
scripts/run-podman-devtool.sh finish filament-vk \
  /workspace/state/build/workspace/finish-layer
```

finish出力に既存patchが含まれる場合は、既存layer patchとのSHA-256を比較する。
同一patchは再登録せず、新しいsource commit由来のpatchだけを本文変更なしで
`meta-fluorite-trial`へコピーする。元recipeのread-only layerへ書き込ませたり、
生成patchのhunkを手で修正したりしない。

### 1.8 patch contextがずれた場合

`do_patch`が特定関数の先行patch適用後に失敗した場合は、patch fileのhunkを編集
しない。まずDevtool sourceのbaseline commitとrecipeのpatch適用順を比較し、必要な
過去変更をDevtool local Gitへimportしたbaselineからsourceを開く。その後、agentが
source fileを編集して新しいsource commitを作り、Devtoolのpatch生成機能で再生成
する。component-scopedなworkspaceでは`update-recipe --mode patch`を優先し、
`git format-patch`を通常手段にしない。新patchをlayerへ登録した後、mini PCの
同じrecipeで`do_patch`を再実行する。

### 1.9 split componentの一発rebase

手動で`reset`、branch作成、`add`、branch切替、`update-recipe`を繰り返すと、
baselineとsource commitの取り違え、既存patchの上書き、registration漏れが起きる。
source側の編集とsource commitが済んだ後は、次のhelperへ二つのcommitを明示する。
helperは対象componentだけを再登録し、既存branchはcommit一致を確認して再利用する。
生成patchはsource commitの`From` headerに一致する一件だけを選び、canonical patchが
異なる場合は上書きせず停止する。

```sh
scripts/rebase-fluorite-devtool-component.sh \
  FLR-XXXX fluorite-plugins \
  /workspace/state/build/workspace/sources/fluorite-plugins \
  <effective-baseline-commit> <source-change-commit> \
  layers/meta-fluorite-trial/recipes-graphics/toyota/files/00NN-change.patch \
  layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend \
  ivi-homescreen-plugins [--replace-canonical]
```

既存canonical patchと生成物が異なる場合は、既定では上書きせず停止する。
同じpatch slotを意図的にrebaseする場合だけ`--replace-canonical`を明示し、
置換前後のSHA-256を証跡へ記録する。

このhelperの順序は、対象recipeのactive登録確認 → 必要なら`component-reset` →
effective baseline branchの確保 → 公式`component-add` → source-change branchの
確保 → 公式標準`update-recipe --mode patch --append --no-remove` → patchのsource
commit照合 → byte-identical copy → 一意registration
確認 → baseline lock refreshで固定される。失敗時は最初の境界だけを表示し、Devtoolの
全ログを端末へ流さない。次のMini `do_patch`はこのhelperが成功してから、固定receiver
へbundleを渡して一回だけ実行する。

### 1.10 レシピ単位のMini patch gate

layer commitをbundleで固定receiverへ渡した後は、手作業でremote shellを組み立てず、
対象recipeだけを次のgateで確認する。

```sh
scripts/run-mini-recipe-patch-gate.sh FLR-XXXX flutter-auto
```

このhelperは、固定receiverのexact Git revision、固定buildの`TMPDIR`、receiver
layer、BitBake/BitBake serverの二重起動を先に検査する。次に対象recipeの
`bitbake -e`から`PN`、`PV`、`FILE`、`WORKDIR`、`SRC_URI`、`S`だけを要約して保存し、
`bitbake -f -c do_patch <recipe>`を一回だけ実行する。成功時は`do_patch=PASS`と
要約pathだけを返し、失敗時はraw outputを端末へ流さず、パッチ適用境界、最初の
`Hunk`/`FAILED`/`ERROR`行、最新の`log.do_patch.*` pathだけをticket evidenceへ
記録して同じexit statusで終了する。image recipeは受け付けないため、patch gateと
full image buildの境界が混ざらない。

これは、Yoctoの公式な「変更をsource Gitへcommitしてからrecipeをupdateする」順序と
整合する。`devtool modify`はrecipeの既存patchをsourceへ適用し、変更をcommitした
後に`devtool update-recipe`でpatchを生成する。未commit変更はupdate対象にならない。
詳細はYoctoの[devtool reference](https://docs.yoctoproject.org/4.0.34/ref-manual/devtool-reference.html#updating-a-recipe)
を参照する。既存patchのcontext更新には、公式QA文書の
[patch-fuzz guidance](https://docs.yoctoproject.org/5.3/ref-manual/qa-checks.html#patch-fuzz-warning)
の考え方を適用し、生成patch本文は手で編集しない。

### 1.7 project layerへ登録してlocal commit

patchの配置先は必ず `meta-fluorite-trial`。対象bbappend/recipeの
`SRC_URI:append`へpatch名を追加し、別componentを対象にするpatchだけに
`patchdir=<source-subdirectory>`を付ける。

```sh
git diff --check
git diff -- layers/meta-fluorite-trial
git add layers/meta-fluorite-trial work/tickets work/logs work/evidence docs
git commit -m 'fix: describe fluorite validation milestone'
git status --short --branch
```

commit前に、秘密情報、個人名、IP/hostname、巨大log、deploy artifactがGit対象に
入っていないことを確認する。QEMU image、PPM/PNG、serial log本体はGit外に置き、
evidenceにはrole path、hash、要約だけを記録する。

## 2. Git bundleをmini PCへ渡す

cleanなfeature branchから、baseとtipを明示したbundleを作る。baseは比較点として
祖先関係を検証し、bundle自体はreceiverが別履歴でも受け取れるself-contained形式にする。
通常は次の
一つのhelperを使う。bundleは固定の外部artifact directoryに一つだけ作られ、
remote hashと固定receiverのexact tipまで同じコマンドで検証される。

```sh
scripts/handoff-fluorite-bundle.sh <base-commit> <tip-commit>
```

このhelperは`BUILD_HOST`、`BUILD_BUNDLE_INBOX`、`BUILD_RECEIVER`、`BUILD_DIR`、
`BUILD_TMPDIR`をlocal role設定から読み、canonical checkoutがcleanであることを
先に確認する。Podman machineやMini PC roleが未準備ならbundleを送らずfail-closedする。
旧来の個別コマンドは、helperの検証境界を調査する場合だけ使う。

```sh
git status --short --branch
git bundle create "$BUNDLE" <base-commit>..<tip-commit>
git bundle verify "$BUNDLE"
shasum -a 256 "$BUNDLE"
```

実際のrepositoryで使うbundle helperがある場合はそれを優先し、manifestの
base/tip/ref/hashを保存する。`scp`で`$BUILD_HOST`のinboxへ送り、転送後に
remote側hashと一致することを確認する。canonical cloneへ直接fetch/checkout
しない。

## 3. mini PCの固定receiverと権威build

mini PCでは、ticket/commitごとにreceiverとTMPDIRを増やさず、ticket単位の固定
receiver、固定build directory、固定TMPDIRを再利用する。canonical checkoutは
変更しない。receiver helperはbundle、receiver clean状態、固定layer、BitBake idle、
effective `TOPDIR`/`TMPDIR`を変更前に検査する。effective値は既存buildへ
`oe-init-build-env`をsourceした後、targetなしのbounded `bitbake -e -T 5`から取得し、
固定role pathとcanonical directoryで照合する。Yoctoの[BitBake user manual](https://docs.yoctoproject.org/bitbake/bitbake-user-manual/bitbake-user-manual-intro.html#the-bitbake-command)は`-e`をglobal/per-recipe環境表示、`-T`をserver idle timeoutとして定義している。query失敗、timeout、process残留、
path不一致の場合は`git fetch`/checkout前にfail-closedする。bundleのverifyとadvertised
tipも更新前に確認し、成功後はexact revisionとworktree cleanを再確認する。
固定receiverは通常checkoutまたはGit linked worktreeのどちらでもよく、
`.git`の存在形状ではなく`git rev-parse --is-inside-work-tree`で有効性を判定する。

```sh
export BUILD_HOST=<build-host-role>
export BUILD_RECEIVER=<fixed-receiver-path>
export BUILD_DIR=<fixed-build-path>
export BUILD_TMPDIR=<fixed-tmp-path>
scripts/reuse-mini-build-receiver.sh <remote-bundle-path> <tip-full-commit>

source "$AGL_ROOT/external/poky/oe-init-build-env" "$BUILD_DIR"
bitbake -e agl-ivi-image-flutter > "$EVIDENCE_DIR/bitbake-e-image.txt"
bitbake -c do_patch -f flutter-auto
bitbake -c do_compile -f flutter-auto
bitbake agl-ivi-image-flutter
```

handoffの有効TMPDIR検査は`conf/local.conf`の文字列grepに置き換えない。
`do_patch`、対象`do_compile`、full imageの順で進める。対象taskが失敗したら、
原因を記録するまでfull buildへ進まない。`downloads`、`sstate-cache`、固定TMPDIR
の削除、`cleanall`、未承認の`cleansstate`は行わない。過去のcommit suffix付き
receiver/build/TMPDIRが残っている場合は、まずactive process、evidence、deploy
artifactを確認し、不要性を記録してから限定的に削除する。

生成したkernel/rootfs/qemubootのSHA-256とreceiver revisionを記録し、必要な
artifactだけをMacへ戻す。artifactはGitへ追加しない。

## 4. Mac QEMUとpixel evidence

同じQEMU profile、同じartifact hash、同じguest bundle path、同じregistered
Wayland userを使用する。appは必要ならguest内で`agl-driver`として明示起動する。
画面証跡はデスクトップ全体ではなくQMP framebufferから採取する。

Flutter-autoの起動では、guestにインストールされたBUNDLEのパスを`-b`へ渡し、
BUNDLE内の`config.toml`が指定する短い`app_id = "fluorite"`を使わせる。長い
パッケージ名を`--xdg-shell-app-id`へ渡してはならない。app-idが長い名前になると
compositorでsurface roleが確定せず、QMPが黒画面でもアプリやnative rendererの
失敗とは限らない。起動ログの`Application Id: fluorite`とcompositorのactivationを
確認してから画面を判定する。

`QEMU_RUN`はrunごとに一意なディレクトリにする。同じsocket pathnameでQEMUを
並列起動すると、古いQMP endpointがunlinkされ、後から終了できない残留プロセスを
作る危険がある。起動前に対象socketが存在しないことも確認する。

```sh
QEMU_RUN="$QEMU_ARTIFACT_ROOT/run-$(date +%Y%m%d%H%M%S)-$$"
mkdir -p "$QEMU_RUN"
test ! -e "$QEMU_RUN/qmp.sock"
qemu-system-x86_64 ... \
  -drive file="$ROOTFS",if=virtio,format=raw,snapshot=on \
  -qmp unix:"$QEMU_RUN/qmp.sock",server=on,wait=off
python3 scripts/qemu-pixel-capture.py \
  --socket "$QEMU_RUN/qmp.sock" \
  --output "$QEMU_RUN/frame.ppm"
```

動画が必要な検証では、同じQMP framebufferを連続取得してからMac側で動画へ変換
する。QEMUのホストウィンドウやデスクトップ録画は使用しない。Mini PCでQEMUを
起動した場合は、Macの`qemu-pixel-capture.py`を証跡run directoryへ一時転送して
次を実行し、生成したframe directoryだけをMacへ戻す。

```sh
scp scripts/qemu-pixel-capture.py "$BUILD_HOST:$QEMU_RUN/"
ssh "$BUILD_HOST" \
  "python3 '$QEMU_RUN/qemu-pixel-capture.py' video \
    --socket '$QEMU_RUN/qmp.sock' \
    --frames-dir '$QEMU_RUN/qmp-video-frames' \
    --frames 40 --interval 0.75"
scp -r "$BUILD_HOST:$QEMU_RUN/qmp-video-frames" "$MAC_EVIDENCE_DIR/"
ffmpeg -y -loglevel error -framerate 1 \
  -i "$MAC_EVIDENCE_DIR/qmp-video-frames/frame-%05d.ppm" \
  -c:v libx264 -pix_fmt yuv420p "$MAC_EVIDENCE_DIR/qmp-runtime.mp4"
```

`qmp-video-frames`は既存ファイルを混ぜず、1 runにつき1回だけ作る。再撮影時は
新しいQEMU証跡run directoryを使うが、ビルドの固定TMPDIRやコンテナは増やさない。
動画と代表PNGを同じticketの証跡へ置き、動画のFPS、解像度、フレーム数、SHA-256を
記録する。

各runには、QEMU command/profile、dimensions、frame hash、3D regionのchanged pixel数/
bounding box、10秒間のprocess生存、serial/native logを記録する。最初にQMPから
full-frameを`qmp-full.ppm`として保存し、そのファイルを表示・目視確認してから、同じ
frameの固定3D候補regionを切り出してpixel count/hashを記録する。full-frameが保存・
表示できないrunはvisual gate UNKNOWNとし、ROI統計だけで先へ進めない。

GLBから抽出したemissive/albedo等の静的テクスチャ画像はresource evidenceであり、
QEMU実画面のvisible-pixel evidenceではない。静的画像に色や輪郭があっても、同じrunの
QMP full-frameに対応するpixelがなければnative 3Dは未達と判定する。
2D overlay、FPS、CPU/GPU値、Scenes menuだけでは3D成功と判定しない。正しいBUNDLE
起動でこれら2D要素が表示され、候補regionが黒のままなら、2DはPASS、native 3Dは
未達として別々に判定する。

終了時は必ずQMPで終了する。

固定のQEMU run/artifact directoryを運用する場合は、試行ごとにtmp directoryを
増やさず、QMP socketだけを未使用の名前にして同じrunを再利用する。rootfsは
必ず`snapshot=on`で起動し、検証中にartifact本体を変更しない。既存のrootfsが
変更された場合は、停止後に権威build artifactのhashを確認して固定artifactへ
復元する。QEMUの終了後はsocketが消え、起動PTYが終了したことを確認する。

```sh
printf '%s\n' '{"execute":"quit"}' | nc -U "$QEMU_RUN/qmp.sock"
ps -ax | grep '[q]emu-system-x86_64' || true
```

## 5. 証跡と判定

同じevidenceへ次を紐付ける。

- Mac feature commit、devtool source commit、生成patch名。
- bundleのbase/tip/ref/SHA-256、mini PC receiver revision。
- `bitbake -e`、`do_patch`、`do_compile`、full imageの結果。
- kernel/rootfs/qemuboot hash、QEMU profile、guest bundle/user/Wayland。
- QEMU-only screenshotのpath、dimensions、hash、3D region統計。
- Facts、Inferences、Hypotheses、UNKNOWNを分離した結論。

目標の3D成功条件は、`payload → native entity/renderable → Filament frame/present
→ Wayland attach/commit → 対象regionのvisible 3D pixel`の順序を証明することである。
2Dが表示されても3D pixelがない場合は、成功ではなく次の診断境界を明記する。
