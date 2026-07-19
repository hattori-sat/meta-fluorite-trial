# Repository verification

## Outcome

変更をpushする前の共通gateは次の1 commandです。

```sh
make verify
```

同じentry pointをGitHub Actionsでは`make ci`から実行します。setupとplatform固有checkは[setup guide](setup.md)を参照してください。

## Success criteria

| Gate | Command | Success |
| --- | --- | --- |
| Canonical repository | `make check-canonical` | originのrepository名と管理fileがcanonical contractに一致する |
| Privacy | `make check-privacy` | tracked候補の文書・設定・project layerに個人path、接続先、email、credential候補、canonical remoteの個人namespaceがない |
| Shell syntax | `make check-shell` | trackedおよびuntracked候補の全`.sh`が`bash -n`を通る |
| Python unittest | `make check-python` | `tests/test_*.py`がすべて成功する |
| MCP protocol smoke | `make check-mcp` | MCPが存在する場合、`test_mcp*.py`でinitialize、tool discovery、callが成功する |
| Markdown links | `make check-markdown` | repository内linkとMarkdown anchorが存在し、tree外へescapeしない |
| File size | `make check-file-sizes` | Git対象候補の各fileが既定1 MiB以下である |

MCP packageがまだ存在しないrevisionではMCP gateだけ`SKIP`できます。MCP packageが存在するのにsmoke testがない状態は`FAIL`です。

## Hypotheses and alternatives

### Path A: one local aggregate command

`make verify`はdeveloperとCIが同じscriptを使えるため、CIだけ成功する差異を減らせます。個別gateも直接実行できるので、失敗範囲を小さく再検証できます。これを採用します。

### Path B: logicをworkflow YAMLへ直接記述

CI設定だけは短くなりますが、local再現時にcommandを再構成する必要があり、domain agentごとに手順がずれます。workflowには環境選択だけを置き、検証logicはrepository scriptへ残します。

## Verification plan

通常の変更では次の順に実行します。

```sh
make setup
make verify
git add <reviewed-paths>
make check-staged-whitespace
git status --short
```

取り込み元とのバイト対応をhashで固定したbaseline artifactには、取り込み元由来の行末空白が含まれる場合があります。これらを空白修正だけのために書き換えません。staged差分では、project-authored fileを`git diff --cached --check`で検査し、次のbyte-locked範囲を除外します。

- `conf/*/*.template`
- `layers/meta-local/**`
- `manifests/agl-trout-fixed.xml`
- `manifests/local-changes/**`

除外範囲は`tests/test_baseline_artifacts.py`がfile countとhashを検証します。baselineを機能変更するticketではbyte lockを更新するだけでなく、変更対象fileを個別にwhitespace検査します。

`make check-staged-whitespace`は非ignoreのuntracked候補が残っていれば失敗し、通常成果物についてcached snapshotと未stage差分の両方を検査します。したがってcommit直前、review済みpathをstageした後に実行します。

Yocto、AGL、targetの実行検証はこのrepository gateとは別です。対象ticketのSuccess criteriaに従い、revision、image ID、task、target evidenceを記録します。`make verify`の成功だけでFluoriteのruntime動作を証明したことにはなりません。

## Gate behavior

- `PASS`: check対象を観測し、条件を満たした。
- `FAIL`: pushを止め、値を漏らさず原因を修正する。
- `SKIP`: componentがrevisionに存在しないなど、明示された条件だけに使う。
- `UNKNOWN`: optionalなplatform能力やunsourced environment。runtime検証を開始する前に解消する。

privacy checkerは一致した値を出力せず、候補file名だけを報告します。project管理の`layers/`、`conf/`、`manifests/`、patch、lock、templateを含めてscanします。取り込むpatchのauthor/trailer identityはhunkを変えずrole表現へ匿名化し、identity-normalized hashでsource contentとの対応を保ちます。

file size上限を一時的に狭めてchecker自体を検証する場合だけ、local processへ値を渡せます。

```sh
MAX_FILE_BYTES=65536 make check-file-sizes
```

上限を緩めてartifactをGitへ追加する用途には使いません。大きなlog、deploy image、downloads、sstate、build outputはGit外のevidence storageへ置きます。

## GitHub Actions

[CI workflow](../.github/workflows/ci.yml)はpull request、`main`/`dev-*`/`feature-*`へのpush、手動dispatchで動作します。

- repository contentはread-only permission
- checkout credentialは保持しない
- official actionをreview済みfull commit SHAへ固定
- secretやbuild-host credentialを参照しない
- network build、SSH、BitBake、QEMUは実行しない

GitHub branch protectionではCI jobとbranch policy jobをrequired checkに設定します。repository setting自体はversion control外なので、設定完了まではUNKNOWNとして追跡します。
