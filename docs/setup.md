# 開発環境のセットアップ

## Outcome

このrepositoryのsetupは、最初に環境を**観測して不足を明らかにする**方式です。`make setup`と`setup-*.sh`はpackageのinstall、環境scriptの`source`、BitBake、QEMU起動、cache削除を行いません。

検証全体は[verification guide](verification.md)を参照してください。

## Facts

- project toolingとMCPにはBash、Git、Make、Python 3.11以降、ripgrepを使います。
- macOSはlocal検証用にQEMU AArch64とXcode command line toolsを確認します。
- build hostは既存のAGL checkoutとYocto host toolを確認します。
- 接続先、account、checkoutの実pathはGitへ保存せず、local環境変数で渡します。
- `bitbake -n`と環境初期化はlog、lock、cacheなどを書き得るため、`read_only`とは扱いません。

## Host roles

- Mac: repository、Codex/agent/MCP、local gate、QEMU実行検証。
- Linux mini PC: official AGL source flow、`aglsetup.sh`、Yocto/BitBake、cache、image build。

公式手順との対応、source acquisition、artifact handoffは[Official AGL workflow and project host split](agl-official-workflow.md)を先に確認してください。Mac setup checkの成功はAGL build host要件を満たしたことを意味しません。

## 1. Project setup

canonical cloneのrootで実行します。

```sh
make setup
```

これは次を確認します。

- canonical `meta-fluorite-trial` Git repositoryであること
- `AGENTS.md`、`TASKS.md`、`Makefile`、canonical guardが存在すること
- Bash、Git、Make、Python 3.11以降、ripgrepが使えること

不足があればexit status `1`で終了します。検査中にfileを作成・更新しません。

## 2. macOS setup check

```sh
make setup-macos
```

macOSではproject toolに加え、Xcode command line tools、`qemu-system-aarch64`、Hypervisor.frameworkを確認します。x86 QEMUは既存qemux86-64 baseline用の任意項目です。macOS以外では`SKIP`します。

このcheckはQEMU imageをdownloadせず、VMを起動せず、system settingを変更しません。

defaultの`foundation` checkではAArch64 QEMUをproject基盤として要求し、x86 binaryは観測だけにします。対象ticketを始める前はtarget-specific gateを使います。

```sh
FLUORITE_MAC_QEMU_TARGET=qemux86-64 make setup-macos
FLUORITE_MAC_QEMU_TARGET=qemuarm64 make setup-macos
```

前者は`qemu-system-x86_64`、後者はAArch64 QEMUのHVF capabilityを必須にします。

## 3. Build-host setup check

build host自身のcanonical cloneから、checkoutの場所をlocal環境変数で指定して実行します。

```sh
export AGL_ROOT="your-existing-agl-checkout"
export AGL_BUILD_DIR="your-existing-build-directory"  # 任意
export AGL_CACHE_ROOT="filesystem-containing-build-caches"  # 任意、90 GiB gate
make setup-build-host
```

`AGL_ROOT`は必須です。`AGL_BUILD_DIR`を指定した場合だけ、`conf/local.conf`と`conf/bblayers.conf`のreadabilityを確認します。`AGL_CACHE_ROOT`を指定した場合は、そのfilesystemに90 GiB以上の空きがあることを確認します。値そのものはworking logやcommit対象fileへ記録しません。

確認範囲は次のとおりです。

- Linux host tool: compiler、archive、patch、RPC、compressionなど
- fixed repo checkout: manifest、repo launcher、`aglsetup.sh`
- source filesystemへのread access
- Yocto Python 3.8+、Git/tar/GCC/GNU makeのScarthgap minimum、remote MCP Python 3.10+、8 GiB RAM、UTF-8 locale
- optional cache filesystemの90 GiB free-space gate
- 既にsource済みの場合だけ、`bitbake`がPATHに存在すること

このcheckは`aglsetup.sh`をsourceせず、manifestをsyncせず、BitBake taskを開始しません。`downloads`、`sstate-cache`、`tmp`にも書きません。

## 4. Materialize an exact captured configuration

preferred fresh-build pathは、mini PC上でfixed revisionの公式`aglsetup.sh`を使ってbase confを生成し、project差分を適用する方法です。fixed source、`meta-vulkan`、および本repoの`layers/meta-fluorite-trial`が存在し、ticketがcaptured snapshotの完全復元を選んだ場合だけ、sanitized baselineからbuild confを生成できます。defaultはdry-runです。

```sh
scripts/materialize-build-conf.sh \
  --target qemux86-64 \
  --agl-root "$AGL_ROOT" \
  --output-dir "$AGL_BUILD_DIR"
```

dry-runはdirectory structureだけを確認し、source revision identityは検証しないためUNKNOWNと表示します。fixed AGL manifestとexternal-layer revisionを別evidenceで照合した場合だけ、`--write --source-identity-verified`を追加します。これは照合済みというoperator assertionであり、script自身がGit revisionを証明するものではありません。`conf/local.conf`または`conf/bblayers.conf`が既に存在すると上書きを拒否します。Raspberry Pi snapshotはcaptured BBLAYERSに含まれる`$AGL_BUILD_DIR/workspace/conf/layer.conf`も事前に要求します。生成後もBitBakeは開始しません。

```sh
scripts/materialize-build-conf.sh \
  --target qemux86-64 \
  --agl-root "$AGL_ROOT" \
  --output-dir "$AGL_BUILD_DIR" \
  --write \
  --source-identity-verified
```

`raspberrypi4-64`も同じinterfaceです。2つの設定は一時directoryで生成を完了してから`conf/`として同一filesystem内でpublishするため、render途中の失敗で片方だけを残しません。templateは採取baselineを保つためcache pathを含みます。実行前に対象ticketでcache ownershipとdisk spaceを確認し、生成後はFLR-0004のYocto観測でMACHINE、layer、override、cache pathの実効値を確認します。

## 5. Connect Mac agents to mini-PC MCPs

AGL、Yocto、command runnerはMacからSSH stdioでmini PC側runtimeを起動します。mini PCへCodex CLIやripgrepを追加する必要はありません。既存Python 3.10+、SSH、canonical cloneを使います。

1. feature branchがpushされた後、mini PCのcanonical cloneを同じcommitへ更新する。
2. Macで[mcp/remote-role.example.conf](../mcp/remote-role.example.conf)を`.fluorite-mcp/remote-role.conf`へcopyし、Git対象外のSSH role alias、remote repository path、両roleで一致させるfull project commitを設定する。
3. mini PCで[mcp/config.example.json](../mcp/config.example.json)をcanonical clone内の`.fluorite-mcp/config.json`へcopyし、AGL source/build rootとGit外audit fileを設定する。
4. 各domain identityへ固定manifest/combined source digestを設定する。未設定ならresponseはidentity不足となりbaseline evidenceに使えない。
5. 最初は両方のexecution gateをfalse/0のままにし、`agl`と`yocto`のprotocol smokeを行う。
6. build ticketのplanが承認された場合だけ、command runnerのlocal/remote gateとMCP tool approvalを個別に有効化する。

実際のhost、account、absolute path、credentialはどちらのfileもGitへ追加しません。詳細は[MCP runtime](../mcp/README.md#mac-to-build-host-transport)を参照してください。

## Optional manual installation

以下はcheckが不足を報告した場合の**手動の候補**であり、setup scriptやCIは実行しません。組織のpackage policyと対象AGL releaseのhost要件を確認してから、別途承認して実行します。

### macOS

Apple command line toolsがない場合：

```sh
xcode-select --install
```

Homebrewの利用が許可されている場合のproject/QEMU tool：

```sh
brew install python ripgrep qemu
```

実行後に`make setup`と`make setup-macos`を再実行します。

### Linux build host

distributionごとにpackage名が異なるため、setup scriptはpackage managerを呼びません。`setup-build-host.sh`が`MISSING`としたcommandを、対象AGL/Yocto releaseがサポートするdistributionのpackageからsystem administratorが導入します。確認対象のcommand一覧は[scripts/setup-build-host.sh](../scripts/setup-build-host.sh)を正とします。

## Explicitly state-changing operations

次の操作はsetupに含まれません。ticketのscope、revision、build directory、cache pathを確認し、明示承認を得た後に個別runbookから実行します。

- AGL environment scriptの`source`とbuild directory初期化
- `repo sync`またはrevision変更
- `bitbake -n`、`bitbake -e`を含むBitBake invocation
- QEMUやtargetの起動・停止
- package installまたはsystem setting変更
- build cacheのclean

UNKNOWNが残る場合は、値を推測してcommandを組み立てず、対象domain agentへevidence収集を依頼します。

## Troubleshooting

- `canonical repository check: FAIL`: remote名を上書きせず、canonical cloneを開き直します。
- `Python 3.11+ MISSING`: optional installationを承認・実施後、shellのPATHを確認します。
- `AGL_ROOT MISSING`: local shellだけにcheckout pathを設定します。`.env`をcommitしません。
- `sourced BitBake environment UNKNOWN`: setupとしては正常な観測です。environmentは自動sourceされません。
- privacy checkが失敗した場合: 値を表示・再掲せず、対象fileをredactしてから先へ進みます。
