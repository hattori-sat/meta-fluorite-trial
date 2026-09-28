# Fluorite 3D表示到達・検証実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fluoriteの自作3D fixtureとリリース済みのFlowライトExample Demoを、Macでパッチ作成、mini PCで権威ビルド、Mac上のQEMUで検証する一貫したループで切り分け、最終的に画面上の実pixelとして3Dオブジェクトが表示されることを証明する。

**Architecture:** 現在のFlutter Dart payload → flutter-auto/Filament native scene → ViewTarget/Filament frame → Wayland child surface → Flutter/AGL compositorという境界を、各境界で相関可能な診断イベントとして観測する。まず最小の不透明なCubeでFilamentの幾何・カメラ・frameを証明し、その後に既存の透明child-surface合成と本番シーンへ戻って、黒画面が「描画なし」なのか「後ろのsurfaceに隠れている」のかを分離する。production全体を一度に書き換えず、fixture、native描画、WSI/合成、シーン遷移を独立した検証単位として進める。

**Tech Stack:** Yocto/OpenEmbedded, BitBake, AGL Flutter, flutter-auto 2.0, Filament Vulkan, Flutter `filament_scene`, QEMU qemux86-64, Wayland/AGL compositor, macOS Docker devtool, SSH mini PC build receiver, Python/shell evidence checkers.

**Spec:**

- 自作fixtureは `flr0023_fixture_cube` を含むAOT済みアプリとして起動する。
- nativeログで、payload受信、ECS準備、entity作成、renderable作成、`beginFrame`/render/endFrame、swapchain/present、Wayland attach/commitを順序付きで確認する。
- fixture単体では、Cubeまたは不透明な診断clearがQEMU画面の対象領域に現れ、10秒間に対象regionのpixel hashが変化する。起動後10秒時点でアプリプロセスが生存し、異常終了status 139などになっていないことを確認する。
- full-sceneでは、初期画面、Playground、Radar、Settings、Planetarium、Trainsetを、ボタン経由と可能な直接route経由の両方で確認する。少なくともPlanetariumで3D objectのpixel変化を取得する。
- 2D Flutter overlay、scene menu、FPS/動的フレームが生きている場合でも、それを3D成功とは扱わない。3D regionのpixel evidenceを必須とする。
- 各試行は、Mac source revision、bundle hash、mini PC receiver revision、image/rootfs/kernel/qemuboot hash、QEMU profile、guestログ、スクリーンショット/hashを同じevidenceへ記録する。

## Global Constraints

- 作業対象はcanonical repositoryのfeature branch `/private/tmp/flr-0023-active` とする。元のdirty worktreeは変更しない。
- 作業開始時と各milestone前に `bash scripts/assert-canonical-repository.sh`、`git status --short --branch`、必要に応じて `make verify` を実行する。
- `TASKS.md`では非自明な作業を一件だけIn Progressにする。既存FLR-0023のfixture因果境界から外れる新しい表示到達問題は、別ticket（次番号FLR-0026）として記録し、元ticketの証拠を混ぜない。
- patchの作成・修正はMacのDocker/devtoolフローで行う。mini PCは受信したbundleのexact revisionをビルドする権威環境とし、mini PC上で直接patchを編集しない。
- mini PCへの接続情報はlocalのGit-ignored role設定を使い、文書・ログには個人名、IP、hostname、credentialを記録せず `$BUILD_HOST` とrole名で表す。
- `/mnt/yocto/**/{downloads,sstate-cache,tmp}` を削除しない。`bitbake -c cleanall` は実行せず、`cleansstate`も明示承認なしでは実行しない。
- qemux86-64の可視3Dが証明されるまでqemuarm64や実機へscopeを広げない。QEMU qualityを全MACHINEへ無条件適用しない。
- commitはmilestoneごとに行う。pushは行わない。commit前にprivacy checkerとverificationを通す。

## Evidence model and competing paths

### Facts already established

- 自作fixture patch `0016-filament_scene-minimal-3d-fixture-devtool.patch` と camera patch `0017-filament_scene-minimal-3d-fixture-camera-devtool.patch` は存在し、Cube名とAOT markerはpayload側で確認済み。
- r13 imageはmini PCでfull BitBake成功済みだが、QEMUではVulkan/Filament初期化と`lit.filamat`読込後にstatus 139となり、native renderable/frame completionとpixel acceptanceは未確認である。
- full-sceneの既存evidenceでは2D overlayとscene menuは動く一方、3D regionは黒く、Playgroundでは長時間処理後にFPS 0/白画面になる。

### Hypotheses to keep separate

1. **描画パイプライン仮説:** payload/camera/materialがnativeで不完全、またはentity/renderableが作られる前にクラッシュしている。検証は不透明Cube・marker sequence・backtraceで行う。
2. **表示合成仮説:** Filamentはframeを完成しているが、透明swapchain、child surfaceの位置、parentとのz-order、Wayland attach/commit、Flutter surfaceとの合成で背後に隠れている。検証はopaque full-surface、Wayland protocol、region hashで行う。
3. **シーン遷移仮説:** 初期view messageやframe eventのready時点が画面ごとに異なり、button遷移時だけpayload/active camera/animationが壊れる。検証はfixture直起動、初期画面、button、direct routeの差分で行う。

実装は、まず描画パイプライン仮説を最小fixtureで判定し、次に表示合成仮説を判定し、最後にシーン遷移仮説へ進む。既存の透明surfaceを保ったまま直す方法と、診断専用opaque surfaceを一時的に用いて境界を証明する方法を比較し、前者をproduction fix、後者を診断fixtureとして明確に分ける。

## File map

- Ticket/log: `TASKS.md`, `work/tickets/FLR-0026-fluorite-3d-display.md`, `work/logs/2026-08-30-flr0026.md`
- Evidence: `work/evidence/FLR-0026-*.md`
- Demo recipe: `layers/meta-fluorite-trial/recipes-graphics/flutter-apps/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo_git.bb`
- Dart fixture/scene patches: `layers/meta-fluorite-trial/recipes-graphics/flutter-apps/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/0016-filament_scene-minimal-3d-fixture-devtool.patch`, `0017-filament_scene-minimal-3d-fixture-camera-devtool.patch`, `0014-filament_scene-throttle-planetarium-frame-commands.patch`, `0007-filament_scene-v2-scene-camera-adapter.patch`, `0015-filament_scene-restore-root-camera-ecs-registration.patch`
- Native frame/WSI patches: `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0042-filament-view-schedule-software-frame-without-recursive-onframe.patch`, `0045-filament-view-process-initial-view-target-messages.patch`, `0047-filament-view-send-frame-event-without-reply.patch`, `0049-filament-view-dispatch-frame-event-on-platform-runner.patch`, `0013-filament-view-start-wayland-frame-callback.patch`, `0025-filament-view-place-surface-above-parent.patch`, `0028-filament-view-transparent-clear.patch`, `0029-filament-view-transparent-swapchain.patch`, `0035-filament-view-schedule-software-successor-after-drawing.patch`
- Native recipe inclusion: `layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend`
- Existing flow scripts: `scripts/run-mac-devtool.sh`, `scripts/setup-mac-devtool-source.sh`, `scripts/assert-canonical-repository.sh`, `scripts/check-repository-privacy.sh`, `scripts/check-repository-shell.sh`, `scripts/check-markdown-links.py`

## Implementation tasks

### Task 1: 新ticketとacceptance matrixを作り、既存baselineを凍結する

- [ ] `TASKS.md`を読み、FLR-0026をInboxへ追加し、現在のIn ProgressがFLR-0023のままならFLR-0023を検証完了または次工程へ明示してから、FLR-0026だけをIn Progressへ移す。
- [ ] `work/tickets/FLR-0026-fluorite-3d-display.md`に、目的、scope、4W1H、既知のFacts、H1/H2/H3、成功条件、非目標、rollback条件を記録する。
- [ ] `work/evidence/FLR-0026-baseline-2026-08-30.md`に、現行revision、r13 image hashes、既存QEMUログへの参照、未証明の境界を記録する。ticketの結論はpixel evidenceがない限り`UNKNOWN`とする。
- [ ] `work/logs/2026-08-30-flr0026.md`にPlan/Do/Check/Actの最初の記録を追加し、privacy checkにかける。

**Verification:** `bash scripts/assert-canonical-repository.sh`; `git diff --check`; `rg -n 'FLR-0026|In Progress|UNKNOWN' TASKS.md work/tickets/FLR-0026-fluorite-3d-display.md`; `make verify`。

### Task 2: QEMUのpixel採取とscene操作を再現可能にする

- [ ] 既存のQEMU launch script/documentを確認し、固定profile（qemux86-64/q35、TCG multi-thread、2048 MiB、12 vCPU、qemu64 with SSSE3/SSE4/POPCNT、virtio-vga、Cocoa、USB tablet/kbd、snapshot disk）を一つの再実行可能なcommand setとしてevidenceに記録する。
- [ ] guestログ取得、QEMUスクリーンショット取得、対象3D regionのcrop/hash、10秒間のhash系列、プロセス生存確認を行うshell/Python helperを追加する。helperは秘密情報を出力せず、失敗時は期待したregionと実測値を示す。
- [ ] キーボード/マウスのbutton操作を実画面で再現し、Scenes menuからPlayground/Radar/Settings/Planetarium/Trainsetへ遷移する手順を固定する。可能ならDart側のdirect routeを診断専用に追加し、button routeと同じscene payloadを比較する。
- [ ] まず無変更r13 imageで初期画面とPlanetariumを採取し、2D-only変化と3D-region変化を別hashとして保存する。

**Verification:** 同じimage/profileで2回実行し、boot marker、Application Id、Vulkan/Filament backend、scene名、screenshot dimensions、3D region hash系列、process statusが同じ形式で収集されること。再現できない場合は原因をUNKNOWNとして次taskへ進めない。

### Task 3: Dart payloadからnative renderableまでの診断markerを追加する

- [ ] Mac devtoolでfixture patchを複製して診断用patchを作り、既存の`flr0023_fixture_cube` markerを維持したまま、scene payload生成、active camera、shape/material payloadの要約（GUID/count/typeのみ）を時系列markerとして追加する。
- [ ] native側は`ViewTarget`、ECS scene deserializer、shape/renderable生成、camera適用の実際の関数をsource checkoutで確認してから、payload受信、ECS ready、entity handle、renderable完成、camera viewportを同じrun idで記録する。関数名を推測してpatchを作らない。
- [ ] `0045`/`0043`/shape関連patchと`0016`/`0017`のpatch順を確認し、markerが重複しても順序が崩れないようにする。ログはbounded rateで出し、毎frameの大量出力は避ける。
- [ ] Mac Docker image `fluorite-yocto-devtool:22.04` と既存 `run-mac-devtool.sh` / `setup-mac-devtool-source.sh` を使ってpatchを作成し、bundleを作る。mini PCでexact receiver revisionをcheckoutし、`bitbake -e agl-ivi-image-flutter`、対象recipeの`do_patch`、`do_compile`を先に通す。
- [ ] full image buildはparse/対象task成功後に開始し、build開始時刻と再利用したDL/SSTATE role pathをworking logに記録する。

**Verification:** `bitbake -e agl-ivi-image-flutter`でpatchが有効、対象recipeのdo_patch/do_compile成功、AOT markerがimage内に存在、native markerがguestログへ出ること。entity/renderableまで到達しない場合はframe/WSI修正へ進まず、最初に失敗した境界をticketへ記録する。

### Task 4: 不透明な最小fixtureでFilamentの幾何・カメラ・frameを証明する

- [ ] `poGetMinimal3dFixtureScene()`のCubeを、診断モードで画面中央に収まる既知のtransform、明るい不透明material、default directional/point light、near/farとviewportが明示されたcameraにする。production sceneのmodel assetやanimationを依存させない。
- [ ] 透明clear/swapchainを一時的に切り替えられるcompile-timeまたはruntime診断variantを追加し、(i) opaque solid clearのみ、(ii) opaque Cube、(iii) Cubeなしの既存透明surfaceを各々別runで試す。変更はfixtureまたはdiagnostic patchに限定する。
- [ ] `ViewTarget::DrawFrame`周辺のbeginFrame、render、endFrame、swapchain/present相当のmarkerを追加し、Filament APIのreturn/errorを記録する。segfaultが続く場合はguest core/backtraceまたはgdb/lldb相当の最低限のsymbolized地点を採取する。
- [ ] solid clearが見えてCubeが見えない場合はcamera/frustum/material/entityの順に一つずつ変え、各runの差分を保存する。solid clearも見えない場合は合成やWSIへ戻る。

**Verification:** fixture runで、`payload → native scene ready → entity → renderable → beginFrame → render → endFrame/present`の順序が成立し、対象regionに既知色のsolid clearまたはCubeの非背景pixelが現れる。hash変化だけでなく、既知色のpixel割合とbounding boxを保存する。ここが未達ならfull-scene成功とは判定しない。

### Task 5: Wayland child surfaceと表示領域/z-orderを切り分ける

- [ ] Task 4でFilament frameが成功した場合、`wl_surface`生成、role/parent設定、buffer attach、damage、commit、frame callback、surface geometry/scaleを観測する。guestで利用可能な`WAYLAND_DEBUG`、compositor debug、既存AGLログのうち一つを選び、過剰ログを避ける。
- [ ] `0025`のparentより上に置く処理、`0028`/`0029`の透明設定、viewport/activation areaをそれぞれ単独variantで比較する。黒い領域が背後のFlutter surfaceなのかを判定するため、背景を既知色にした上でchild surfaceの矩形を変える。
- [ ] 画面全体opaque、child rectangle opaque、透明child + 2D parentの3種類で同じCubeを表示し、スクリーンショットcropの位置と色を比較する。
- [ ] Wayland commitはあるが画面pixelが変わらない場合、surface geometry/scale/z-orderを一次原因候補にし、rendering failureへ逆戻りしない。commit自体がない場合はnative WSI lifecycleへ戻る。

**Verification:** child surfaceのattach/commitと画面上の対象矩形が一致し、opaque診断variantでCubeまたはsolid clearが視認できる。透明variantでのみ黒くなるなら合成問題として最小production patchを決める。どのvariantでもpixelが変わらない場合はUNKNOWNを維持する。

### Task 6: 初期表示とbutton/direct scene遷移を検証する

- [ ] fixture直起動をbaselineとし、releaseされたfull-scene Example Demoを初期画面で起動する。同じimage/profileでPlayground、Radar、Settings、Planetarium、Trainsetをbutton routeで一つずつ開き、各sceneを10秒保持する。
- [ ] direct routeまたはdiagnostic scene selectorを追加できる場合は、button routeと同じscene payload、camera GUID、shape/model count、frame rate、pixel hashを比較する。direct routeが本番UIを壊さないよう診断buildに限定する。
- [ ] Planetariumは`0014`のframe command throttleを有効にした状態と、既存値を変えない状態を比較し、slow QEMUでFPS 0/白画面にならず、scene objectのpixel変化が継続するかを確認する。
- [ ] 一つのsceneでクラッシュした場合は他sceneの成功を推測せず、route、payload、native marker、last frame、screen hashを別々に記録する。

**Verification:** 各sceneでbutton/directのroute一致、native renderable/frame marker、process生存、2D overlay recurring、3D-region pixel evidenceを確認する。少なくともPlanetariumとfixtureの双方で可視3Dが成立しなければ本目標は未達とする。

### Task 7: 最小production fixをMac→mini PC→QEMUで反映する

- [ ] Task 3–6の証拠から一つの原因だけを選び、production patchは一件ずつに分離する。候補はready後のinitial view message処理、renderable作成順、frame scheduling、surface parent/z-order、transparent swapchainのいずれかとし、複数原因を一つのpatchで直さない。
- [ ] Mac Docker/devtoolでpatchとrecipe inclusionを更新し、qemux86-64専用の必要がない限り既存MACHINEへ展開しない。QEMU quality patchのscopeは維持する。
- [ ] bundleを生成し、mini PCのisolated receiverへ転送してhash照合する。既存canonical checkoutは変更せず、`bitbake -e`、recipe do_patch/do_compile、full `bitbake agl-ivi-image-flutter`を順に実行する。失敗時はbuild artifactを削除せずログだけ保存する。
- [ ] exact imageを固定QEMU profileで起動し、Task 2のautomated pixel/scene harnessを再実行する。修正前後のnative marker、status、surface commit、region hashを横並びにする。

**Verification:** patch revision、bundle hash、receiver revision、rootfs/kernel/qemuboot hashが一致し、修正が対象境界を動かした証拠がある。pixel acceptanceが増えない変更は成功とせず、次の仮説へ戻る。

### Task 8: 可視3Dのacceptance、回帰、commitを確定する

- [ ] fixtureでopaque Cube、full-sceneでPlanetariumと他4sceneを固定profileで再実行し、各10秒のscreen hash系列とログを保存する。
- [ ] no-crash、native frame sequence、Wayland commit、2D overlay、3D pixel bounding box、direct/button route、image provenanceの全成功条件をticketへ反映する。未取得項目は`UNKNOWN`と明記する。
- [ ] Task 1で記録したbaseline revision `b4ee149`を基準に、`make verify`、`git diff --check b4ee149..HEAD`、`PRIVACY_GIT_RANGE=b4ee149..HEAD bash scripts/check-repository-privacy.sh`、shell checker、Markdown link checkerを実行する。
- [ ] evidenceと実装をmilestone commitへまとめ、`git status --short --branch`がcleanであることを確認する。pushはせず、commit hashとmini PC/QEMU evidenceをユーザーへ報告する。

**Verification:** 成功条件の全項目がPASSで、PDCA checkerとprivacy checkerがFAIL/UNKNOWNでないこと。pixel evidenceがない場合はticketをDoneにせず、失敗境界と次の仮説を明記して目標を継続する。

## Execution order and stopping rules

1. Task 1–2でscopeと再現性を固定する。
2. Task 3–4でFilament内の失敗境界を確定する。
3. Task 5で「表示されているが後ろに隠れている」可能性を確定する。
4. Task 6でbutton/direct routeとPlanetariumを含むfull-sceneを確認する。
5. Task 7で証拠に対応する最小production fixだけを反映する。
6. Task 8でpixel acceptanceと回帰を確定する。

次の条件では実装を拡張せず停止してevidenceを更新する: (a) mini PC exact revision/hashが一致しない、(b)対象recipeのparse/do_patch/do_compileが未確認、(c) native markerより前の失敗地点が未確定、(d)画面pixelを取得できない、(e) privacy checkerがFAIL、(f)既存dirty worktreeを安全に分離できない。
