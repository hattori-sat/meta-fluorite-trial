# FLR-0026 — Fluoriteの可視3D表示到達

- Status: Waiting
- Priority: Critical
- Owner: Flutter runtime + Filament bridge + Wayland/compositor + target-validation roles
- Depends on: FLR-0023
- External publication: none
- Follow-up ticket: [FLR-0027 — shape-only/light-only rendering path separation](FLR-0027-shape-light-rendering-separation.md)

The header status and the final scope-closeout section are authoritative. Earlier PDCA entries below are historical snapshots from when this ticket was In Progress.

## Problem

自作Cube fixtureはAOT payloadへの同梱とmini PCでのimage buildまで確認できた。
QEMUではVulkan、llvmpipe、Filament初期化、`lit.filamat`読込まで進むが、
native entity/renderable/frame completion、Wayland child surface commit、画面上の
3D pixelは確認できていない。full-sceneも2D overlayとscene menuは動く一方、
3D regionは黒く、Playground選択後にFPS 0/白画面となる。

## Goal

Macでpatchを作成し、bundleをmini PCへ送り、exact revisionを権威buildしたimageを
Mac QEMUで起動するループを維持しながら、次の順序を証明する。

`Dart payload → native scene/entity/renderable → Filament frame/present → Wayland
attach/commit → compositor region → visible 3D pixel`

自己作成の不透明Cube fixtureで描画経路を先に証明し、その後に既存の透明child
surfaceとfull-sceneへ戻る。初期画面、button route、direct diagnostic route、
Planetariumを含む各sceneを比較し、「描画されていない」と「後ろのsurfaceに隠れている」を分離する。

## 4W1H

- What: 3D objectが画面の対象regionに現れ、10秒間のpixel evidenceを残す。
- When: 固定qemux86-64 profileでfixture・full-scene・scene遷移ごとに実行する。
- Where: Mac QEMU上のAGL graphical session。buildはmini PC、patch作成はMac Docker/devtool。
- Who: primary roleが調査を統合し、build-runnerがmini PC build、target-validation roleがQEMU/pixel evidenceを採取する。

## Facts

- FLR-0023のfixture recipeは`0016`/`0017` patchとAOT markerを含む。
- r13のmini PC image buildは成功済みで、rootfs SHA-256は
  `adf8a9497849a1e1c88b54b343a0772b3b3b8fdcbf3dfb62845e01a40d5c6f91`、
  kernel SHA-256は
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`、
  qemuboot SHA-256は
  `d01d9f726fcb2ac2ceccb4d186835100d9a549e04215f67d8a7da56715763956`である。
- r13 QEMUはVulkan 1.3、Filament Vulkan backend、llvmpipe、`All systems initialized`、
  `lit.filamat`読込まで進んだ後、status 139で終了した。
- 既存full-scene evidenceではscene menuと2D動的表示は動くが、3D regionは黒い。
- 過去の0043安定runでは`FPS: 20 / 60`、CPU/GPU/Scriptの非ゼロ動的値、2D
  controls、Scenes menu、55秒超のprocess生存がPASSだった。
- 2026-08-31のr1ではQMPの720x400 framebufferとmacOSのQEMU window screenshotが
  ともに黒く、5/25/55秒のframe比較でchanged pixelは0だった。r1のguest appは
  material読込後にSIGSEGVし、native entity/renderable/frameとchild Wayland commitは
  まだUNKNOWNである。
- r13のunstripped mini PC binaryで、r2cのSIGSEGVは
  `IndirectLightSystem::setIndirectLight()`のasync callbackから呼ばれる
  `filament::IndirectLight::Builder::radiance()`に対応し、radiance data pointerが
  nullだった。fixtureの`DefaultIndirectLight`経路とproductionの
  `HdrIndirectLight.asset`経路が異なることを確認した。
- 0054のMac devtool生成marker patchをmini PCで適用・compile・full image
  buildまで完了した。QMP-only画面では2D overlayが回復し、native logは
  `FLR0026_SHAPE_READY ... renderable=true`、Wayland surface creation、
  Vulkan swapchain creationを示した。
- 同じ0054 runのcamera markerは
  `head=(0,0,0) target=(0,0,0) dolly=(0,0,0)`だった。central 3D regionは
  黒く、可視3D pixelはまだ未達である。
- 0105のDevtool生成patchを同じbundle/receiver/build/TMPDIRでbuildし、独立した
  SHM child surfaceへ自作の透視投影3面Cubeを表示できた。QMP-only画面の対象regionは
  `38609/100000` changed、bbox `[200,113,280,167]`だった。この結果は表示領域、
  z-order、Wayland SHM合成の成立を証明するが、Filament native 3Dの成功とは数えない。
- 0104では`vkQueuePresentKHR result=0`を確認したが、native候補regionは黒いままだった。
  現在の未達境界は、Filament画像の可視child surfaceへの引き渡しまたは画像内容である。
- 0116ではreadback Fenceの待ち時間を50msへ変更したが、
  `NATIVE_READBACK_RESULT` callbackは発生せず、QMP候補regionは2Dメトリクス以外
  変化しなかった。readback完了待ちだけでは解決しない。

## Current runtime evidence update (2026-09-04)

### Facts

- 現行feature commit `61c3ea9`のOpenGL/EGL診断ビルドは、Mini PCの固定
  receiver/build/TMPDIRでfull image 11,748/11,748 tasks成功、rootfs SHA-256は
  `cbf7ee9d9cab8445de40b3c3610c81b3d219058e563de48d7bd518c49921bd18`。
- 同rootfsをVulkanデフォルトで正しいExample Demo bundle起動したところ、QMP-only
  early/late frameにFluorite title、FPS、Frametime、CPU、GPU、Script、graph、
  Scenes、bottom controlsが表示され、遅延時も`flutter-auto`が生存した。したがって
  現行2D/HUD/CPU表示はPASSであり、今回の3D未達は2Dデグレではない。
- OpenGL診断は`FLR0026_FILAMENT_BACKEND_OVERRIDE requested=OPENGL`、
  `FEngine resolved backend: OpenGL`まで到達したが、
  `Selected backend not supported in this build.`で終了した。OpenGLはproduct
  defaultへ採用しない。
- 次の観測として、Mac Devtool source commit `bd7f145`からsurface pointer identity
  patch `0135`を生成し、`meta-fluorite-trial`の`flutter-auto` patch列へ登録した。
  Mini PCへ転送してruntime比較する前段まで完了している。

### Inference

Flutterの親surface、CPU/HUD、bundle/AOT、native renderable生成までは現行ループで
再現している。可視3Dの残存候補は、Filament Vulkan image/command completionと
Wayland child surfaceへのbuffer handoff/compositionである。

### UNKNOWN

- Filamentが生成した`wl_surface`がpluginのnative surfaceと同一かどうかは、
  `0135`をMini PCでbuild・runtime実行するまで未確認。
- Vulkan submit後のimageがcompositorへattachされるか、attach後に正しいstackingで
 合成されるかは未確認。

## Hypotheses

1. **native lifetime:** fixtureのDefaultIndirectLightが非同期callbackへraw pointerで
   渡され、ownerの変更・破棄後にradianceを読むため起動直後にクラッシュしている。
2. **表示合成:** Filament frameは完成しているが、transparent swapchain、child surfaceの
   attach/commit、geometry/scale/z-orderでFlutter parentの背後に隠れている。
3. **scene遷移:** 初期view message、ready通知、active camera、frame commandがbutton
   routeとsceneごとに異なり、Planetarium等だけで破綻している。
4. **fixture camera:** Dart fixtureの`orbitDistance`/legacy
   `flightStartPosition`がnative active cameraのdollyに反映されず、原点から
   原点を見ているためCubeが視野に入っていない。serialized
   `dollyOffset=(5,0,0)`で検証する。

## Scope closeout and handoff (2026-09-05)

### Check

- This ticket established the current QEMU/2D baseline and proved that a self-made native cube can produce real pixels through the existing Vulkan/Wayland/QEMU path.
- Production 3D is not complete: leaving production shapes/lights enabled still reaches the `libLLVM.so.18.1` crash path. This ticket is therefore not `Done`; its remaining investigation is handed off rather than appended indefinitely.
- QMP-only evidence for runs 0197, 0198, and 0199 is recorded in the working log with image hashes and clean QMP teardown.

### Act

- Status is `Waiting` because the next source-side diagnostic requires the fixed Mac Docker/Devtool container, whose VM backend is currently unavailable.
- The next bounded task is [FLR-0027](FLR-0027-shape-light-rendering-separation.md). It inherits this ticket's baseline and must produce its own QMP-only images and evidence records.

## Visual evidence

| Run | QMP-only image result | What the image shows | Evidence |
| --- | --- | --- | --- |
| 0197 | 3D region unchanged | Present/commit is stable, but scene content is intentionally skipped; this is not a 3D success | `work/logs/2026-08-31-flr0026.md`, evidence ID 0197 |
| 0198 | 3D region `0/100000` changed pixels | 2D path remains present while production shapes/lights lead to the later native crash path | `work/logs/2026-08-31-flr0026.md`, SHA-256 recorded there |
| 0199 | 15,212/100,000 changed pixels; bbox `[291,139,138,122]` | Self-made native cube is visibly rendered through the current Vulkan/Wayland/QEMU path | `work/logs/2026-08-31-flr0026.md`, SHA-256 recorded there |

The raw PPM files remain in the external QEMU evidence store. The ticket keeps the run identity, visual interpretation, and checksum reference without adding large images to Git.

## Success criteria

- [x] fixtureでpayload、native entity、renderable、Filament frame/presentの順序付きmarkerが出る。
- [x] fixtureのopaque clearまたはCubeがQEMU対象regionに現れ、10秒間processが生存する。
- [x] Wayland child surfaceのattach/commitと対象regionの位置が一致する。
- [ ] 透明surfaceへ戻しても、対象regionの3D pixel bounding boxとhash変化を取得できる。
- [ ] 初期画面、Playground、Radar、Settings、Planetarium、Trainsetをbutton routeで確認する。
- [ ] Planetariumでscene遷移後の3D pixel変化を確認し、direct routeとの差分を記録する。
- [ ] 2D overlay/FPS/menuだけを3D成功の代用にしない。
- [x] Mac revision、bundle hash、mini PC receiver revision、image hashes、QEMU profile、
  guest log、screen/hashを同じevidenceへ記録する。
- [ ] `make verify`、privacy、shell、Markdown link、diff checkがPASSする。
- [ ] historical 0043の2D/CPU baselineをfixture crash後にも回復できる。

## Non-goals and safety

- qemux86-64で可視3Dが確定するまでqemuarm64や実機へ拡張しない。
- QEMU quality patchを全MACHINEへ無条件適用しない。
- `/mnt/yocto/**/{downloads,sstate-cache,tmp}`を削除しない。`cleanall`と未承認の`cleansstate`を実行しない。
- mini PCのcanonical checkoutを変更せず、isolated receiverでbuildする。
- pushはせず、milestone commitまでを行う。

## Verification sequence

1. pixel採取、guest log、QEMU固定profile、scene操作を再現可能にする。
2. Mac devtoolでdiagnostic markersとopaque fixture variantを作り、mini PCで対象task/full imageをbuildする。
3. marker sequenceで最初の未達境界を確定する。
4. opaque full-surface、opaque child surface、透明child + 2D parentを比較する。
5. native/WSI evidenceに基づく最小production fixを一件ずつ反映する。
6. Planetariumを含むfull-sceneをbutton/direct routeで再試行し、pixel acceptanceを確定する。

## UNKNOWN

- DefaultIndirectLightのraw pointer crashはsource symbolまで確定済み。修正後に同じ境界が消えるかはUNKNOWN。
- material load後にentity/renderable作成が完了しているか。
- child Wayland surfaceのattach/commitが一度でも発生しているか。
- `dollyOffset`を明示したfixture cameraで3D pixelが現れるか。
- 黒い3D regionが背後のsurfaceなのか、Filament未描画なのか。
- Filamentのreadback callbackがFence完了後も結果を返さなかった理由。

## Iteration 42 result — native rotated-Cube gate

### Facts

- The self-made Cube was rotated with `Quaternion.identity()..setEulerDegrees(25, 35, 0)` through the persistent Mac Devtool source. Devtool commit was
  `ccbce761513ad8915b19df45a38c7817860960fd`; the unchanged generated patch is
  `0032-filament_scene-rotate-emissive-blue-native-fixture-devtool.patch`.
- Project commit `c0bf22c9b4a8a11adc3540fa4a5cf72507db6002` was delivered by bundle to the fixed receiver and built in the same build/TMPDIR. The bundle SHA-256 is
  `40836236ba4ebf4cdabc3d9908a31d62edfe7720b63314911e983292e3a4e40c`; the rootfs SHA-256 is
  `39d404292c8680bc558a64f029470a6f17a48b76390edabf97b566f567b493d1`.
- All app/image tasks through `do_image_complete` passed. Runtime logged Vulkan/llvmpipe, `FLR0026_SHAPE_READY ... renderable=true`, native surface creation, swapchain creation, and successful queue presents.
- With the SHM mock switch absent, QMP-only evidence
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/native-rotated-0125-qmp-late.ppm` shows the green native surface and a three-face Cube. Its SHA-256 is
  `9d125f8e7aae93a6b867069f388b55ab6918434a71b2af54cc36432562d4c31a`; the Cube bbox is `(536,298)-(754,493)` with 32,088 non-green pixels.

### Verdict

- Native self-made 3D fixture display: **PASS**.
- 2D HUD/CPU/GPU/Frametime display: **PASS**.
- QMP-only evidence and QMP cleanup: **PASS**.
- Production full-scene and Planetarium route matrix: **PENDING**.

### Inference

The prior black square was a front-facing projection with an unhelpful dark output. The rotated fixture proves that the visible native path can carry actual Filament geometry, not only Flutter 2D or the SHM mock.

### Next action

Restore the production Example Demo scene through the same Devtool → generated patch → bundle → fixed build/TMPDIR flow, then test Scenes and Planetarium navigation/input while retaining the native fixture as the regression gate.

## Iteration 43 result — production Example Demo restoration

### Facts

- The production Example Demo scene was restored through the persistent
  Devtool source and generated patch 0033. Project commit
  `fbf86909a01d45538dd913bfccc5ec0dc6aedffc` contains the recipe registration.
- The same bundle, fixed receiver, build directory, TMPDIR, Devtool
  container, and QEMU run directory were reused. App/image tasks through
  `do_image_complete` passed. Rootfs SHA-256:
  `05b0c66fd8779467abcd8e4de006819b88e12252e736dbc55e32cc3bb13ad00b`.
- Production runtime loaded `lit.filamat`, created multiple renderables,
  initialized Vulkan/llvmpipe, and stayed alive during the observed run.
- QMP-only initial evidence has SHA-256
  `134d8aaa85f41abffeae61ef2601fda2aae2dced9d4a96e1e9ce6d69f46089a8` and
  shows the historical 2D HUD/CPU/GPU/Frametime/Scenes controls. The native
  candidate region has no 3D object.
- Scenes input was retried with QMP absolute axes normalized to 0–32767, but
  the menu did not visibly open. Planetarium selection is not claimed.

### Verdict

- Production scene build/startup: **PASS**.
- Production initial native 3D visibility: **FAIL / not observed**.
- Scenes/Planetarium input matrix: **UNKNOWN / pending**.
- Historical 2D regression gate: **PASS**.

### Next action

Investigate production camera arbitration through one Devtool source change at
a time. Keep the rotated native fixture as the regression gate and repeat the
same QMP-only evidence before proceeding to Planetarium.

## 2026-09-03 runtime-first continuation

### Facts

- Runtime analysis preceded patching. The current image reached
  renderable=true, command submission result=0, and then stopped at the
  Vulkan present call. Existing Wayland dispatch and roundtrip probes had
  already failed to change this boundary.
- Devtool-generated patch 0126 tested removal of the present wait semaphore
  only under FLR0026_PRESENT_NO_WAIT=1. The fixed Mini PC build passed
  14/14, 856/856, and 11748/11748. Runtime still stopped before the present
  result and later hit the known libLLVM crash.
- The current image's SHM display control was captured by QMP and visibly
  showed the self-made three-face Cube together with the 2D/CPU metrics.
- The historical native rotated-Cube QMP proof remains valid as a separate
  native-pixel gate; current 0126 does not supersede it.

### Inferences

- The present-wait semaphore is not the sole cause.
- The remaining native failure is most consistent with the Wayland WSI
  buffer-release/shared-display boundary, but the root cause is UNKNOWN.

### Status

- 2D HUD/CPU/GPU/Frametime: PASS.
- Self-made 3D display control: PASS.
- Historical self-made native Filament Cube: PASS.
- Current native Filament 3D under 0126: FAIL / not reproduced.
- Production Example Demo and Planetarium route matrix: PENDING.
- Keep FLR-0026 In Progress.

## 2026-09-03 corrected unset runtime A/B

- The invalid `FLR0026_NATIVE_CLEAR_PROBE=0` run was excluded because the
  implementation treats variable presence as enabled.
- With the variable truly unset, runtime still reached renderable=true and
  queue submission, then stopped at present; QMP candidate pixels remained
  zero. The pre-present commit is not the sole cause.
- Continue with Wayland WSI buffer-release/shared-display instrumentation.

## Current runtime split — 2026-09-04

### Facts

- The latest Devtool-generated observation patch (`0135`) and the resulting
  fixed Mini PC image were verified end to end. Rootfs SHA-256:
  `4c80d26695bc96229b5c85326767639e11d030ca8546014a118326a74b451e50`.
- In the same runtime, the plugin Wayland `surface_ptr` and Filament
  `wl_surface` pointer matched exactly. This rules out the current
  surface-identity mismatch hypothesis.
- QMP-only captures show the 2D HUD/CPU/GPU/Script metrics, while the native
  3D region remains black. Native renderable creation and queue submission
  succeed; present completion remains unobserved.

### Status

- Runtime analysis before patch: **PASS**.
- 2D HUD/CPU/GPU/Frametime: **PASS**.
- Native surface identity: **PASS / same object**.
- Native self-made 3D pixels in the current fixed run: **FAIL**.
- Scenes/Planetarium route matrix: **PENDING until native fixture gate passes**.
- FLR-0026: **In Progress**.

### Next action

Instrument the Vulkan present return and Wayland subsurface commit/stacking
boundary with one more opt-in Devtool-generated change. Compare the two
remaining explanations—no pixels produced versus pixels hidden by
composition—before any repair patch.

## Iteration 56 result — Wayland stacking A/B (2026-09-04)

### Facts

- The native setup's `wl_subsurface_place_above` target was analyzed before
  patching. The existing parent target is not a sibling; a first candidate
  `0136` using the target's own surface also produced a compositor protocol
  error (`place_above ... is not a parent or sibling`).
- Devtool patch `0137` added an opt-in `FLR0026_WAYLAND_SKIP_STACK=1` path.
  The fixed build passed all three gates, and the runtime reached native
  renderable creation and queue submission without the protocol error.
- QMP-only early/late frames still show the 2D HUD and black native region.

### Verdict

- Stacking error observed and explained: **PASS**.
- Omitting the stacking call as a sufficient repair: **FAIL**.
- Native self-made 3D pixels in the current run: **FAIL**.
- QMP evidence and cleanup: **PASS**.

### Inference

The `place_above` target defect is real but not sufficient to explain the
current black output. Present completion or Vulkan image/Wayland attach
ownership remains the active fault domain.

### Next action

Keep `0136` and `0137` diagnostic-only and do not use either as a product fix.
Continue with a single Devtool-generated observation around Vulkan present
return and Wayland attach/commit ordering. Keep route testing pending until
the native fixture gate passes.

## Iteration 57 result — synchronized Wayland subsurface A/B (2026-09-04)

### Facts

- Devtool patch `0138` tested synchronized Wayland subsurface behavior using
  `FLR0026_WAYLAND_SYNC=1`; default desync behavior was preserved.
- The fixed build and runtime reached `renderable=true` and queue submission.
  QMP-only early/late captures retained the 2D HUD/metrics but showed no
  native 3D pixels.

### Verdict

- 2D HUD/CPU/GPU/Frametime: **PASS**.
- Synchronized subsurface as sufficient repair: **FAIL**.
- Native self-made 3D in the current run: **FAIL**.
- QMP evidence and cleanup: **PASS**.

### Inference

The black native region is not explained by child subsurface sync mode alone.
The active fault domain remains Vulkan present completion, swapchain image
content, or WSI attach/commit ownership.

### Next action

Keep `0138` diagnostic-only. Use the existing SHM 3D fixture to validate
composition and route/input behavior separately, while retaining native 3D
as an unresolved gate.

## Iteration 58 result — SHM 3D composition and Scenes input probe (2026-09-04)

### Facts

- The explicit SHM fixture controls displayed the self-made perspective Cube
  together with the Fluorite HUD and CPU/GPU/Script metrics in a QMP-only
  frame.
- QMP mouse and keyboard input commands were accepted, but no visible Scenes
  or Planetarium transition was observed.

### Verdict

- Self-made 3D composition control: **PASS / SHM mock only**.
- 2D HUD/metrics: **PASS**.
- Scenes/Planetarium route transition: **UNKNOWN**.
- Native Filament 3D: **NOT ESTABLISHED**.

### Inference

The QEMU capture path and child-surface composition can show a 3D-looking
object, so the black native region is not a whole-window capture limitation.
The mock does not exercise Vulkan native pixels, and the input probe is not
enough evidence of a route transition.

### Next action

Continue native diagnosis at swapchain image content and WSI attach/commit
completion. Keep route testing pending until an explicit route state change
can be observed.

## Iteration 61/62 — readPixels call-path trace (2026-09-04)

### Facts

- Devtool-generated Filament patches `0141` and `0142` were registered under
  `meta-fluorite-trial`; project commits are `e2e73ee7` and `6e2ed5c1`.
- The fixed Mini PC build passed all requested gates, including Filament
  104/104 patch, 1965/1965 compile, flutter-auto 104/104 patch and 2686/2686
  compile, and the image 11748/11748 gate.
- Runtime 0211 reached `renderable=true`, the native readback target, the
  public Renderer readPixels marker, FRenderer, RendererUtils, and the
  recorded markers. Vulkan command submission and end-frame recording also
  succeeded.
- Runtime 0211 did not reach the VulkanDriver readPixels marker or the
  native readback callback. QMP-only evidence still shows the 2D HUD and a
  black native region.

### Inferences

- Application/API reachability and command recording are no longer the
  leading fault hypotheses. The active boundary is command-stream dispatch
  before `VulkanDriver::readPixels`.

### Hypotheses

1. The readback command is recorded but not dispatched by the concrete
   CommandStream dispatcher.
2. Command ordering or command-buffer lifetime prevents this command from
   executing while end-frame commands execute.
3. UNKNOWN: the exact concrete-dispatcher entry behavior.

### Verdict

- 2D HUD and runtime metrics: **PASS**.
- Self-made SHM 3D control: **PASS / SHM mock only**.
- Public-to-RendererUtils readPixels path: **PASS**.
- Native Vulkan readback dispatch: **NOT OBSERVED**.
- Native Filament 3D: **NOT ESTABLISHED**.
- QMP evidence and cleanup: **PASS**.

### Next action

After Docker Desktop recovery, use the same persistent Devtool container to
add one diagnostic-only concrete-dispatcher trace, regenerate the patch,
bundle it to the same receiver, and rerun the fixed build/runtime loop. Do
not change rendering behavior until that boundary is evidenced.

## Iteration 63/64 — Docker recovery and concrete readPixels dispatcher trace (2026-09-04)

### Facts

- Docker Desktop responded after the user's restart. The persistent
  fluorite-mac-devtool container was stopped only because its fixed bind
  mount had disappeared; restoring that same mount allowed the existing
  container and Devtool workspaces to be reused.
- The diagnostic source edit was made on the Mac-side copy, copied into the
  persistent Devtool workspace, and committed there as
  88c61a5a928bd15b24aec96943b21237d2972341. The generated patch was copied
  unchanged into meta-fluorite-trial as
  0143-filament-readpixels-dispatcher-devtool.patch.
- Project commit ca171a6f040925a1b2bdae5d36d0d3bb8e378c06 registered the
  patch. The complete-history bundle was transferred to the fixed receiver,
  which checked out that exact commit. The existing build directory and
  TMPDIR were reused.
- Mini PC gates passed: Filament do_patch 104/104, Filament do_compile
  1965/1965, and agl-ivi-image-flutter 11748/11748. The transferred QEMU
  rootfs SHA-256 is
  eff036c475ba05aa025e76dfeda40f209a16d62234899ba31f496ee7062b1e5a.
- With FLR0026_NATIVE_READBACK_PROBE=1 and the explicit installed BUNDLE
  launch, the guest logged Application Id: fluorite,
  SHAPE_READY ... renderable=true, the public/FRenderer/RendererUtils
  readPixels path, FLR0026_READPIXELS_DISPATCH_BEGIN, Vulkan readback
  command recording, queue submit result 0, task posting, driver exit, and
  FLR0026_READPIXELS_DISPATCH_DONE.
- The same native run later hit the known libLLVM.so.18.1 segmentation
  fault. Its QMP-only screenshot
  $QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/dispatcher-0143-readback-qmp.ppm
  has SHA-256
  a4972e7e976c35a3231772ee2e8b178ef588884dcd734859f7dcf0a519beb90e;
  the candidate region [200,100,400,250] changed 0/100000 pixels.
- As a separate current-build control, FLR0026_SHM_PROBE=1 and
  FLR0026_3D_SHM_MOCK=1 produced a visible self-made perspective cube and
  the 2D HUD/CPU/GPU/Script metrics in
  $QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/dispatcher-0143-mock-qmp.ppm.
  Its SHA-256 is
  6093b9a93a12dfcd489b470f55233354cacd5135644b94621e8149c2ad93be32;
  the candidate region changed 38400/100000 pixels with bounding box
  [240,120,240,160].
- Both QEMU sessions were terminated through QMP quit; no QMP socket
  remained.

### Inferences

- The missing concrete-dispatcher hypothesis is rejected. The readPixels
  command is dispatched and reaches Vulkan readback code, including a
  successful queue submission.
- The QMP capture path and Wayland SHM composition are independently
  functional. The native black region is therefore not explained by a
  whole-window capture failure.
- The active native boundary is after Vulkan readback submission and before
  visible native pixels reach the compositor, with the LLVM crash as a
  separate runtime stability concern.

### UNKNOWN

- Whether the submitted readback contains non-black pixels before the
  callback/compositor handoff.
- Whether the LLVM crash is caused by the existing TCG/llvmpipe path or is
  triggered by the native readback workload.
- Whether the Planetarium route changes this native-surface boundary.

### Verdict

| Boundary | Verdict |
| --- | --- |
| Mac Devtool → generated patch → bundle → fixed receiver | PASS |
| Filament patch and compile gates | PASS |
| Concrete readPixels dispatcher execution | PASS |
| Native Vulkan pixels in QMP screenshot | FAIL / black |
| Current-build SHM mock cube and 2D HUD | PASS / control only |
| QMP evidence and cleanup | PASS |
| Native Filament 3D acceptance | NOT ESTABLISHED |

### Next action

Keep 0143 diagnostic-only. The next runtime-first step is to identify the
readback result content and the WSI/compositor handoff, while separately
reproducing the LLVM crash with the smallest native probe. Do not treat the
SHM mock as native Filament proof or broaden route acceptance yet.

## Related evidence

- `work/evidence/FLR-0023-qemu-r12-runtime-2026-08-30.md`
- `work/evidence/FLR-0023-full-scene-comparison-2026-08-30.md`
- `work/evidence/FLR-0023-fixture-static-2026-08-25.md`
- `work/evidence/FLR-0026-qemu-r1-screen-2026-08-31.md`
- `work/evidence/FLR-0026-camera-origin-2026-08-31.md`

## Iteration 65/66 — buffer readback build and historical A/B (2026-09-04)

### Facts

- The persistent Mac Devtool source was changed through the agreed workflow.
  Devtool commits `3ef9412f8` and `eb03a5027` introduced Vulkan buffer
  staging and corrected the `VkBufferImageCopy` field (`extent` to
  `imageExtent`) plus an unused lambda capture. Devtool generated patches
  0144 and 0145; unchanged copies were registered here. Project commits
  `9448932` and `419c809` recorded the two steps.
- The complete-history bundle was sent to the fixed receiver. The existing
  receiver, build directory, and TMPDIR were reused; the receiver was
  restored to `419c8096dd3a10f63351556f38d9c421a507d49d` after the historical
  A/B.
- Filament patching passed 104/104 tasks, Filament compilation passed
  1965/1965 tasks, and the full image passed 11748/11748 tasks. The current
  rootfs SHA-256 is
  `c98824c0c3e07ef0349aa3d1ece7790b1ec3a5dbff6750a0c30db0b3ba8c85f4`.
- Current native runtime reached shape creation (`renderable=true`),
  readPixels dispatch, Vulkan command recording, queue submit `result=0`,
  task posting, and driver exit. It then reached `FENCE_WAIT_BEGIN` but no
  fence completion, map, reshape, callback, or work-complete marker appeared.
- Current QMP-only captures remained black in `[200,100,400,250]` with
  `0/100000` changed pixels. The no-probe 720x400, forced 1280x800, and
  duplicate-video PPM SHA-256 values are respectively
  `1e1012ac6aa3ae96b5f69df203993442f032c70ba7a8a3b2b6378f771bf161fa`,
  `87662fe35a973dc3041d26324ce7b3279d43978922a80664c2fe62bc8ab2f481`, and
  `4e95932b7324cd4bdae875cac5385be4d626b834e9aea47c17c39c84bf4f2037`.
  They visibly retain the 2D HUD/CPU/GPU metrics while the native region is
  black.
- Historical commit `c0bf22c` was rebuilt through the same fixed receiver,
  build, and TMPDIR. Its rootfs SHA-256 was
  `605348273f27fcdc07ae8a9e9b152bf9b9129f976f1e3528ed92bf5593e71d88`.
  Its late QMP-only PPM SHA-256 was
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c` and
  was also black in the native region. The earlier green rotated-Cube
  capture remains historical evidence but was not reproduced.
- The SHM control still displays the self-made cube and 2D HUD, proving that
  QMP capture and child-surface composition are not globally broken. Every
  QEMU run was terminated through QMP `quit`; no process or QMP socket remains.

### Inferences

- Buffer staging is source/build-valid but is not a sufficient runtime fix for
  visible native 3D.
- The black result is not caused solely by the readback probe, display size,
  or duplicate VGA configuration. The SHM control rejects a whole-window
  capture failure.
- The frame-start/WSI sequence is now the leading runtime hypothesis: after
  surface creation, later frame logs report `started=false`, and no complete
  present/readback result is observed. This is not yet a proven root cause.

### UNKNOWN

- Whether `started=false` blocks a usable native present or is a symptom of an
  earlier llvmpipe/WSI failure.
- Which runtime condition produced the earlier green native capture.
- Whether the submitted Vulkan buffer contains non-black content before its
  callback and compositor handoff.

### Verdict

| Boundary | Verdict |
| --- | --- |
| Mac Devtool → generated patch → bundle → fixed receiver | PASS |
| Filament patch/compile/full image gates | PASS |
| Current native Vulkan 3D pixels in QMP | FAIL / black |
| Historical-success A/B under current fixed runtime | NOT REPRODUCED |
| SHM self-made cube and 2D HUD control | PASS / control only |
| QMP evidence and cleanup | PASS |
| Fluorite native 3D acceptance | NOT ESTABLISHED |

### Next action

Keep FLR-0026 In Progress. Before another behavioral patch, add one bounded
diagnostic through the persistent Mac Devtool that correlates frame-start
acceptance, native surface readiness, swapchain creation, and present
completion. Only after that boundary is proven should a behavioral fix be
attempted.

## Iteration 67 — forced render after skipped frames (2026-09-04)

### Facts

- No source, patch, bundle, build, or rootfs change was made for this test.
  The existing current rootfs and fixed QEMU run directory were reused.
- Runtime-only `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1` caused
  `FLR0026_FRAME_FORCED_AFTER_SKIP` to appear from sequence 3 onward, proving
  that the skipped-frame branch was bypassed and rendering work was attempted.
- Runtime still reached `VK_QUEUE_PRESENT_BEGIN` without present completion.
  The QMP-only PPM is
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/force-skip-0167-qmp.ppm`,
  SHA-256 `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`.
  At 1280x800, the native candidate region changed `0/100000` pixels.
- QMP `quit` returned `reason=host-qmp-quit`; the QMP socket and QEMU process
  were absent after cleanup.

### Inferences

- `started=false` is a real gating condition, but bypassing that gate is not
  sufficient to produce a visible native 3D frame.
- The remaining failure is after forced frame execution and at or before
  completed Vulkan present/llvmpipe WSI progress. A source change that only
  forces skipped frames is therefore not justified as the fix.

### Verdict

| Boundary | Verdict |
| --- | --- |
| Forced frame execution | PASS / observed |
| Native present completion | FAIL |
| Native 3D pixels in QMP | FAIL / black |
| QMP capture and cleanup | PASS |

### Next action

Keep the experiment as diagnostic evidence only. Instrument the exact
`beginFrame` return, swapchain image acquisition, queue submission, and
  `vkQueuePresentKHR` return in one ordered trace before changing behavior.

## Iteration 68/69 — present mode and acquire-wait runtime A/B (2026-09-04)

### Facts

- The existing current rootfs and fixed QEMU run directory were reused; no
  source or build change was made.
- `FLR0026_PRESENT_MODE=immediate` selected mode 0 and acquire returned
  `result=0`, but runtime still stopped at `VK_QUEUE_PRESENT_BEGIN` and the
  native candidate region remained `0/100000` in QMP.
- Combining forced skipped-frame rendering with `FLR0026_PRESENT_MODE=immediate`
  also produced forced-frame markers but no present completion or native
  pixels.
- Combining forced rendering with `FLR0026_ACQUIRE_NO_WAIT=1` and
  `FLR0026_PRESENT_NO_WAIT=1` logged both semaphore waits disabled, but still
  stopped at `VK_QUEUE_PRESENT_BEGIN`. Its QMP PPM
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/acquire-nowait-0170-qmp.ppm`
  has SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c` and
  changed `0/100000` pixels in the native region.
- Each QEMU run ended through QMP `quit`; no QMP socket or QEMU process
  remained.

### Inferences

- FIFO present mode is not the sole cause, because immediate mode has the same
  boundary.
- The acquire image-ready semaphore and present finished semaphore are not
  sufficient explanations; disabling both waits did not produce pixels.
- The common remaining boundary is Vulkan queue execution/WSI integration
  under the current guest runtime, after command submission and before
  `vkQueuePresentKHR` returns.

### Verdict

| Boundary | Verdict |
| --- | --- |
| Immediate present mode selection/acquire | PASS / observed |
| Semaphore-wait bypass | PASS / observed |
| Native present completion | FAIL |
| Native 3D pixels in QMP | FAIL / black |
| QMP evidence and cleanup | PASS |

### Next action

Do not add a workaround for present mode or semaphore waits. The next source
diagnostic should correlate the queue submission fence with the present call
and capture the first Vulkan result that fails or blocks.

## Iteration 70 — extent-matched 1280x720 runtime A/B (2026-09-04)

### Facts

- The existing current rootfs and fixed QEMU run directory were reused with
  kernel display mode `1280x720`; no source or build change was made.
- Guest Wayland surface and Vulkan swapchain both reported `1280x720`, and
  `vkAcquireNextImageKHR` returned `0`.
- Runtime still reported later `started=false` frames and stopped at
  `VK_QUEUE_PRESENT_BEGIN` without completion. The QMP-only capture
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/match-1280x720-0172-qmp.ppm`
  is 1280x720, SHA-256
  `847b7f79e03d5c6627ebab623434be40bbabe552c8a3566755c717d621598486`, and
  the native candidate region changed `0/100000` pixels.
- QMP `quit` completed with the socket and QEMU process absent afterward.

### Inferences

- Extent mismatch is rejected as the primary cause. Matching QEMU, Wayland,
  and swapchain dimensions did not change the frame/present boundary.

### Verdict

| Boundary | Verdict |
| --- | --- |
| QEMU/Wayland/swapchain extent match | PASS |
| Native present completion | FAIL |
| Native 3D pixels in QMP | FAIL / black |
| QMP evidence and cleanup | PASS |

### Next action

Proceed to the diagnostic source change only after preserving these runtime
results: correlate the submission fence, command execution, and present call
in one ordered trace.

## Iteration 71 — extended wait at extent-matched 1280x720 (2026-09-04)

### Facts

- The current rootfs and fixed QEMU run directory were reused without source
  or build changes. QEMU display and Wayland/Vulkan swapchain were both
  `1280x720`.
- Intermediate and extended late QMP-only captures had the same SHA-256
  `847b7f79e03d5c6627ebab623434be40bbabe552c8a3566755c717d621598486`.
  Both native candidate regions changed `0/100000` pixels.
- Guest logs showed two completed initial frames, repeated `started=false`,
  and one `VK_QUEUE_PRESENT_BEGIN` with no return or later frame completion.
  Waiting longer did not produce native pixels.
- QMP `quit` completed with the socket and QEMU process absent afterward.

### Inferences

- The result is not a short startup delay. The first native submission/present
  remains uncompleted for the extended observation window.
- The native failure is localized to Vulkan command execution/WSI progress or
  resource ownership before `vkQueuePresentKHR` returns. Timing-only changes
  are not justified.

### Verdict

| Boundary | Verdict |
| --- | --- |
| Extent-matched long runtime | PASS / observed |
| Delayed native present completion | FAIL |
| Native 3D pixels in QMP | FAIL / black |
| QMP evidence and cleanup | PASS |

### Next action

Move to a minimal Devtool-generated diagnostic in the Vulkan command
submission path that records the submission fence status immediately before
and after the present boundary. Keep it opt-in and do not alter scene content.

## Iteration 71 — extended wait at extent-matched 1280x720 (2026-09-04)

### Facts

- The current rootfs and fixed QEMU run directory were reused without source
  or build changes. The QEMU display and Wayland/Vulkan swapchain were both
  `1280x720`.
- QMP-only captures at the intermediate and extended late points had the same
  SHA-256 `847b7f79e03d5c6627ebab623434be40bbabe552c8a3566755c717d621598486`.
  Both native candidate regions changed `0/100000` pixels.
- Guest logs showed two completed initial frames, then repeated
  `started=false`, followed by one `VK_QUEUE_PRESENT_BEGIN` with no return or
  later frame completion. Waiting longer did not produce native pixels.
- QMP `quit` completed and no QEMU process or QMP socket remained.

### Inferences

- The result is not a short startup delay. The first native submission/present
  remains uncompleted for the extended observation window.
- The native failure is now localized to Vulkan command execution/WSI progress
  or a resource ownership defect before `vkQueuePresentKHR` returns. A further
  timing-only workaround is not justified.

### Verdict

| Boundary | Verdict |
| --- | --- |
| Extent-matched long runtime | PASS / observed |
| Delayed native present completion | FAIL |
| Native 3D pixels in QMP | FAIL / black |
| QMP evidence and cleanup | PASS |

### Next action

Move from runtime-only timing tests to a minimal Devtool-generated diagnostic
in the Vulkan command submission path that records the submission fence status
immediately before and after the present boundary. Keep the change opt-in and
do not alter scene content.

## Iteration 81 — native renderer with scene content detached (2026-09-04)

### Facts

- Devtool commit `7efcfbb155d335a68ae956e5b6622403b19f2144` generated
  `0166-diag-render-native-without-scene-content-devtool.patch` (SHA-256
  `5ac65de16c7abc39ee9f2fc3697b528005bd33d7c27345338ccc565da1a3b408`).
  Project commit `a08c8a668d06033e17a5588cdf385cdfbd657300` registered it.
- The fixed bundle/build loop passed: bundle SHA-256
  `4d12aa074c6b2acb06c6740e17a034a7dc7959678ed1a58d5d777e9fb53d6f5f`,
  `do_patch` 104/104, `do_compile` 2686/2686, full image 11748/11748, and
  rootfs SHA-256
  `ddcc1dc248363f1f8e830287ea2b76bda486b04544b9a61d6f3b4ac284c0af99`.
- With `FLR0026_NATIVE_SKIP_SCENE_CONTENT=1`, the native view scene was
  temporarily detached while `renderer->render(fview_)` executed, then
  restored. The late QMP-only frame was
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/scene-content-skip-0166-qmp-late.ppm`,
  SHA-256 `355f151ef464a1ad63c2939a72e4c640cba78a1ed039415d0f8ef81e1070bcc8`.
  Native region `[200,100,400,250]` was `0/100000`; the 2D HUD remained
  visible. QMP cleanup passed.

### Inferences

- The result weakens “fixture material/geometry alone blocks native output,”
  but does not prove that the empty-scene render emits the same presentable
  command stream as the production scene.
- QMP and 2D composition remain valid controls. Native 3D acceptance is still
  unmet.

### Hypotheses

1. Native renderer/driver handoff or WSI progress remains the primary fault.
2. The empty-scene path does not submit a presentable native buffer, so a
   driver-side minimal-clear trace is required before a behavior fix.

### Verdict

| Boundary | Result |
| --- | --- |
| Devtool → bundle → fixed Mini PC build | PASS |
| 2D HUD / QMP capture | PASS |
| Native renderer with detached scene | OBSERVED |
| Native 3D pixels | FAIL / `0/100000` |
| QMP cleanup | PASS |

### Next action

Keep 0166 diagnostic-only. Add one Devtool-generated driver-execution trace
around a minimal native clear/render submission, then repeat the same fixed
bundle/build/QMP loop. Do not close FLR-0026 until native 3D pixels are visible.
## 2026-09-04 — Iteration 82: Graphics Pipeline生成での一次障害

### Facts

- 既存rootfs・既存QEMU run directoryを再利用し、ソース/build変更なしの
  `FLR0026_PIPELINE_TRACE=1` ランタイム解析を実施した。
- QMP-only画面では2D HUD、CPU/GPU/FPS等は表示されたが、native候補領域は
  長時間後でも `49/100000`、クラッシュ後は `0/100000` だった。
- traceは `GRAPHICS_PIPELINE_CREATE_BEGIN` で止まり、ゲストの
  `flutter-auto` は `libLLVM.so.18.1` 内でSIGSEGV終了した。直前にqueue submit
  は `result=0`、その後presentは開始したが完了記録がない。

### Inferences

- 現在の一次切り分けは、黒画面やWayland合成ではなく、production sceneの
  Graphics Pipeline生成中のLLVMクラッシュである。
- 2D表示が維持されるため、前回までの2D退行仮説は今回も支持されない。

### UNKNOWN

- LLVMクラッシュを起こす具体的なshader/material/state入力。
- pipelineを最小化した場合にnative 3D pixelとpresent完了が得られるか。

### Status

FLR-0026はIn Progress。native 3D表示のSuccess criteriaは未達であり、QMP-onlyの
2D証跡を3D成功とは数えない。

### Next action

Devtoolで最小の単色geometry/pipeline診断を作成し、production pipelineを避けた
native Filament描画を検証する。成功後にPlanetarium等のproduction sceneへ戻り、
QEMU入力と画素変化を確認する。
## 2026-09-04 — Iteration 83: native Filament 3D pixel到達

### Facts

- Devtool sourceから生成した`0167`で、native側に独立Filament Scene、8頂点36
  インデックスのcube、単色Unlit materialを追加した。変更は環境変数でのみ有効で、
  production sceneは変更しない。
- 固定Mini PC buildは`do_patch` 104/104、`do_compile` 2686/2686、full image
  11748/11748がPASS。rootfsはSHA-256
  `21a45278b3fa86e121bd6615f275e442ba00c70c359403409490e1dbd2932411`。
- QMP-only 720x400画面でnative候補regionは`15212/100000`、bbox
  `[291,139,138,122]`。中央に青い立体cubeが表示され、10秒後も同一frame hashで
  維持された。ログはnative geometry ready、frame completion、present result `0`を
  示し、SIGSEGVはない。

### Inferences

- 目標の第一段階である「自作native Filament 3Dを実画面へ表示」は達成した。
  SHM mockやFlutter 2Dではなく、Filament geometry→Vulkan→Wayland→QMPの実経路である。
- したがって、現在のproduction scene未表示は、QMP画面が黒い・Dockerが古い・2Dが
  壊れた、という説明ではなく、production pipeline入力またはscene固有問題として
  次に切り分けるべきである。

### UNKNOWN

- production sceneで`libLLVM.so.18.1`をクラッシュさせる具体的shader/material/state。
- Planetarium routeをproduction scene復帰後に表示できるか。

### Status

FLR-0026はIn Progress。native fixture Success criterionはPASSへ更新できるが、
production sceneとPlanetariumのSuccess criteriaは未達のためticketは完了しない。

### Next action

production sceneを戻すvariantを作り、最小native cubeを回帰ゲートとして同一QMP loopで
初期画面・Scenes・Planetariumを確認する。production pipelineが落ちる場合は、最初に
落ちるshader/material/stateを特定してから一つずつ簡素化する。

## Latest validation — production route and opaque A/B (2026-09-04)

### Facts

- `0051`でExample Demoのproduction `models/scene/shapes/cameras`をDevtool生成パッチとして
  復元し、固定receiver/build/TMPDIRでapp patch/compileとfull imageを成功させた。
- 本番起動ではasset load、renderable、pipeline、submit、frame完了、2D HUD/CPU表示を確認した。
  QMP専用PPMの3D候補regionは初期`0/100000`、pipeline後`3/100000`でnative objectは未確認。
- QMP入力でScenesの5項目を表示し、Planetariumクリック後にcamera 214 active化を確認した。
  Planetarium後の3D候補regionは`3/100000`で、route入力は通るがnative 3Dは未達。
- `0168`の環境変数限定opaque分岐でA/Bしたが、opaqueログとframe完了後も3D候補は`9/100000`。
  透明surfaceのz-order単独原因は支持されない。
- 各runのQMP-only PPM、bundle/rootfs/patch SHA、QMP cleanupを記録済み。QEMUは残していない。

### Inferences

自作native Filament cubeのQMP pixel PASSとproductionの黒い候補regionを比較できたため、
「QEMU画面取得」「Docker再起動」「2D退行」を主因とする切り分けは完了した。production側の
renderable参加、bounds/camera、material/stateのどれかが次の境界である。

### Status / Success criteria

| Criterion | Status |
| --- | --- |
| 自作native Filament 3DをQMP実画素で表示 | PASS |
| 2D HUD/FPS/CPU/GPU/Scenes | PASS |
| production Example Demo build/startup | PASS |
| Scenes menu and Planetarium input | PASS |
| production initial native 3D | FAIL |
| Planetarium native 3D pixel change | FAIL |
| 透明surface単独仮説のopaque A/B | NOT SUPPORTED |
| ticket completion | PENDING |

### Next action

production sceneのentity/renderableがactive Sceneへ登録された時点、model bounds、active cameraの
projectionをruntime markerで収集する。そこで可視性が確認できるまで、material簡素化やmock化を
先行させず、最小native cubeを回帰ゲートとして同一QMP loopを維持する。

## Latest runtime-first analysis — current rootfs fixture and display-size A/B (2026-09-05)

### Facts

- 既存の固定rootfs（SHA-256 `2d73ec5d6e362aae4744710962813053652a66c1f95bb5c94e1f0a095496f05f`）を再利用し、追加build・追加container・追加TMPDIRは作成していない。
- `FLR0026_NATIVE_MINIMAL_GEOMETRY=1`で自作geometryの生成、renderable、frame begin/end、queue submit result=`0`まで確認した。
- 通常表示のRun 0178はQMP `1280x800`で、native候補`[200,100,400,250]`が`0/100000`だった。QMP-only PPMは
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/current-0178-minimal-final-qmp.ppm`、SHA-256は
  `a37c544c863d6327e72d6f1d8968e7b5d880ecfd0856c691f02479c0a1238ad9`。
- `virtio-vga,xres=720,yres=400`だけを追加したRun 0179では、QMPが`720x400`となり2D変更画素は`7274`だったが、native 3Dは出なかった。
  QMP-only PPMは `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/current-0179-720x400-qmp.ppm`、SHA-256は
  `355f151ef464a1ad63c2939a72e4c640cba78a1ed039415d0f8ef81e1070bcc8`。
- `FLR0026_NATIVE_MINIMAL_GEOMETRY`はviewのScene差し替えであり、production GLBの読み込み停止ではない。自作scene設定後もproduction asset読み込みが続くため、今回のA/Bは完全なfixture隔離ではない。
- 両RunはQMP `quit`で終了し、socketとホスト側QEMU/flutter-auto残留プロセスはない。

### Inferences

- QMP表示を過去の成功条件に合わせてもnative pixelが出ないため、単純な表示領域・解像度問題は棄却する。
- 現行rootfsでは、production asset resource/pipeline処理を含むdriver側の停止、またはWayland Vulkan WSI停止が残っている。
- 2D HUD/CPU/GPU/FPSとSHM mockの表示は、native Filament presentの成功を意味しない。

### UNKNOWN

- production asset loadingを完全に抑止した純粋な自作fixtureで、現行rootfsのpresentが完了するか。
- 現行rootfsでdriverが停止する正確な関数境界。

### Next action

Macのpersistent Devtool sourceでproduction asset loadingをopt-in停止し、自作native geometryだけを初期化する診断分岐を作る。
生成patchをlayerへそのまま登録し、bundle→固定Mini PC build→QMP-only runtimeで検証する。純粋fixtureのpresent完了を確認してから、production sceneとPlanetariumへ戻る。

## Runtime boundary review — process and Flutter/native split (2026-09-05)

### Facts

- Mini PCに`qemu-system-x86_64`、`flutter-auto`、Wayland compositor、`applaunchd`の残留はなく、
  QMP socketと`bitbake.lock`も残っていない。固定TMPDIRは保持している。
- Macは永続Devtoolコンテナ1個を再利用中。dangling imageは確認したが、解析中は削除していない。
- `ModelSystem`は`updateAsyncAssetLoading()`でproduction GLBの非同期loadを継続するため、
  `FLR0026_NATIVE_MINIMAL_GEOMETRY`はscene差し替えであってasset loading抑止ではない。
- `ViewTarget`の`beginFrame()`がfalseになるruntime markerは、Filament`FrameSkipper`の
  Fence status=`TIMEOUT_EXPIRED`と一致する。Flutter例外やDart route失敗を示すmarkerではない。
- 2D HUD/CPU/GPU/FPS、SHM mock、Wayland親surface、Vulkan surface生成、swapchain acquire、
  queue submit result=`0`は確認済み。native 3Dのdriver dispatch/present完了は未確認。

### Conclusion

現時点で「Flutterの中だけの問題」とは断定しない。Dart/package/親surfaceまでは通っており、
主な未達はFlutter-Auto native pluginからFilament driver queue、Vulkan Wayland WSI、child surface
合成へ進む境界にある。次はproduction assetを完全に除いた純粋fixtureで同じrootfsを再実行し、
asset/pipeline起因かdriver/WSI起因かを分ける。

## Runtime result — pure native fixture on Mini PC-built rootfs 0177 (2026-09-05)

### Facts

- Mac Devtool source commit `21b79a71e2d486edffd8951ad2bcd24497e77afd`から、Devtool内部の公式patch抽出APIで`0177`を生成した。patch SHA-256は
  `dcf9d988e545a84ec05b4a930206139522659fba16846b79d276ec35552f89bb`である。
- project commit `b8542631235fa86611339d5e0f177304aeb34cda`をbundleで固定Mini PC receiverへ渡し、同じbuild/TMPDIRを再利用した。metadata、`do_patch`、`do_compile`、full image buildはすべて成功した。
- `FLR0026_NATIVE_PURE_FIXTURE=1`でproduction asset setupを抑止し、`FLR0026_NATIVE_MINIMAL_GEOMETRY=1`で自作Filament cubeを生成した。
- runtimeはWayland/Vulkan surface、swapchain acquire、queue submit、`vkQueuePresentKHR`のresult=`0`、present boundary return/done、連続frame commitまで出力した。
- QMP-only PPMは`$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/pure-fixture-0177-qmp.ppm`。720x400、native候補regionの変更は`15212/100000`、bboxは`[291,139,138,122]`、SHA-256は
  `9294659aeb9743c8d36d3076ec70161ce6a3f2b6d77a2b05e77674db1df73471`。青い3D cubeの実画素を確認した。
- QMP `quit`後、socketと対象プロセスは残っていない。

### Inferences

- Flutter/Dart起動、親surface、native fixture、Vulkan acquire/submit/present completionはこの経路で通っている。
- したがって以前の黒いnative regionは、QMP、解像度だけ、またはFlutter UI全体停止だけでは説明できない。production asset/resource/pipeline setupが、現在の最重要な差分である。

### Hypotheses / UNKNOWN

- 第一仮説は、productionの非同期asset/resourceまたはpipeline処理がFilament/driver queueを停滞させること。
- 代替仮説は、productionのlight/entity setup等の特定commandがdriver/WSI相互作用を引き起こすこと。
- 正確な最初の該当command/resourceはUNKNOWN。rootfs `0177`でのproduction initial sceneとPlanetarium比較を次に行う。

### Act

純粋fixtureでpresentと3D実画素が通ったため、次は同じrootfs・同じQEMUプロファイルでfixture flagだけを外し、production initial sceneをA/Bする。その後Scenes/Planetarium遷移をQMP-only captureで確認する。fixtureで意図的にlight setupを省略しているため、`Light not found`は既知の診断ノイズとして扱う。

## Production comparison result on rootfs 0177 (2026-09-05)

### Facts

- `FLR0026_NATIVE_PURE_FIXTURE`を外し、診断cubeを残したA/Bでは、production GLB読込後にqueue submitまでは進んだが、runtime logに`FLR0026_VK_QUEUE_PRESENT result=0`と`FLR0026_VK_PRESENT_BOUNDARY_DONE`が無く、HUDだけが残った。QMP-only PPMは`$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/production-0177-qmp.ppm`、SHA-256は`f2f2de9f51701657defe1dfeda165232cf693e6e04a09c0858858649787a6b36`、native候補は`0/100000`だった。
- 診断cubeも外したproduction scene単独でも、AOT、GLB、active camera、Vulkan surface/swapchain、queue submit、initial frameまでは到達した。QMP-only PPMは`$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/production-actual-0177-qmp.ppm`、SHA-256は`b57b601e781d0b2b234737493e4625f2c6a10d64ff86cba2c4eefbc5f3d539f6`、native候補は`0/100000`だった。
- production比較画面は2D HUDを表示している。最初のA/BではFPS、Frametime、CPU、GPU、Script、Scenes、操作ボタンを確認した。
- production QEMUは両runともQMP `quit`で停止し、socketと対象プロセスは残っていない。

### Inferences

- 同一rootfs・同一QEMU profileで、production asset setupを有効にしたときだけnative presentが再び止まる。したがって、失敗はFlutter全体ではなく、production native resource/pipeline/scene command経路に絞られた。
- 診断cubeをviewへ設定してもproduction asset setupがqueueを塞ぐため、単純なproduction modelのbounds/cameraだけでは説明できない可能性が高い。

### UNKNOWN

- 最初に詰まる対象が特定GLB/resource upload、material/pipeline creation、light/entity setup、または累積command量のどれかは未特定。
- rootfs `0177`でのPlanetarium遷移とnative 3Dは未確認。既存のScenes/Planetarium 2D証跡とは分離して扱う。

### Act

次はproduction asset setupの工程をさらに分解する。候補ごとにruntime markerを追加し、まずasset loadを抑止したままproduction scene entity/cameraを残すA/B、次にmodel単位の投入を1つずつ行う。結果をQMP-only pixelとpresent markerで判定し、Planetariumはpresentが安定する工程まで待って同じinput/capture loopへ戻す。

### Pipeline trace follow-up

変更なしの短時間runtime traceでは、production pipelineが`GRAPHICS_PIPELINE_CREATE_DONE result=0`まで進み、queue submit/end-frameも出たが、`QUEUE_PRESENT`完了は出なかった。QMP-only PPMのnative候補は`0/100000`（SHA-256 `830e88a326c07320712421b90329de0dce4b6bc01bf258d14a951b91e60178ab`）。過去に確認した`libLLVM.so.18.1` SIGSEGVはこの短いrunでは再現していないため、現時点の直接原因はUNKNOWNのままとする。pipeline create成功をnative画素成功とは扱わない。

### Diagnostic patch 0178 prepared

runtime結果を受け、Mac Devtool source commit `750e918`から、`setUpLoadingModels()`だけを環境変数`FLR0026_NATIVE_SKIP_MODEL_LOAD`で抑止する診断patchをDevtool公式APIで生成した。skybox/light/indirect-light/shape/entity setupは残す。patch SHA-256は`42e678c0c513a15efb72f998554707a40d8db0de9073a23f27e58fdede1c0287`で、Mini PC build/runtimeは未実施。

### 0178 runtime result

0178はMini PCの同じbuild/TMPDIRでfull imageまで成功した。`FLR0026_NATIVE_SKIP_MODEL_LOAD=1`と`FLR0026_NATIVE_MINIMAL_GEOMETRY=1`で、modelだけを抑止し他のproduction setupを残したが、QMP-only native候補は`0/100000`だった。PPM SHA-256は`bc65af6c420662fe1afc1de935fba1b17cc25fa0d93090a06a2ac9b5aebefaca`。従ってmodel load単独原因とは未確定で、次はskybox/indirect-light、lights、shapesを順に分ける。

### Diagnostic patch 0179 prepared

次はMac Devtool source commit `112b128`から、skyboxとindirect-lightだけを`FLR0026_NATIVE_SKIP_ENVIRONMENT`で抑止するpatchを公式APIで生成した。model loadは0178と同じくruntime flagで抑止し、lights/shapes/entitiesは残す。patch SHA-256は`533e78f97b1aa5ab967c900a1822e4367904e512628438a69607f44bfcea7e1f`。Mini PC build/runtimeは未実施。

### 0179 runtime result

0179は同じMini PC build/TMPDIRでbuild・QMP実行を完了した。`FLR0026_NATIVE_SKIP_MODEL_LOAD=1`と`FLR0026_NATIVE_SKIP_ENVIRONMENT=1`を有効にし、lights/shapes/entitiesを残したところ、`QUEUE_PRESENT result=0`、`PRESENT_BOUNDARY_DONE`、`COMMIT_DONE`が連続して出た。QMP-only PPMはnative候補`15212/100000`、bbox`[291,139,138,122]`、SHA-256は`9294659aeb9743c8d36d3076ec70161ce6a3f2b6d77a2b05e77674db1df73471`で、青い自作3D cubeを確認した。

これはproduction environment setup（skybox/indirect-light）またはmodel/resourceとの相互作用が、native present未達の第一候補であることを強く示す。ただし製品仕様としてenvironmentを削除する修正ではなく、次はmodel loadとenvironment setupを独立に戻すmatrixで真因を分ける。

### Environment-only skip matrix result

0179 rootfsでmodel loadingを戻し、`FLR0026_NATIVE_SKIP_ENVIRONMENT=1`だけを有効にしたruntime-only A/Bでは、present/commit境界は復旧した。しかしQMP-only画像は全288000画素が同一RGB `(13,115,255)` のuniform clearで、cube輪郭もproduction objectも無かった。従って「present復旧」はPASSだが、「3D object表示」は未達であり、3D PASSとは扱わない。

次はskyboxとindirect-lightを独立したflagで分け、model loadingを抑止した状態で各段階を個別に戻す。これにより、environment内のどの処理がpresentを止めるか、また自作cube表示とproduction object不在を別々に説明できるかを確認する。

### Diagnostic patch 0180 prepared

Mac Devtool sourceで、既存のcombined environment skipを維持しつつ、skyboxとindirect-lightをそれぞれ `FLR0026_NATIVE_SKIP_SKYBOX`、`FLR0026_NATIVE_SKIP_INDIRECT_LIGHT` で抑止できる診断分岐を追加した。Devtool source commitは `f07de3a`、公式patch生成物のSHA-256は `9285674f2a1752bd567a8ae7e28beee6e3a43c215f2d0a5a5c1512e1196f0675`。patchは `meta-fluorite-trial` 配下へ登録済みで、Mini PC build/runtimeで個別matrixを実施する。

### 0180個別runtime matrix result

0180 rootfsで、model skip + indirect-light skip（skybox復元）はpresentと自作blue cubeが復旧した。一方、model skip + skybox skip（indirect-light復元）は`FRAME_BEGIN started=false`が続き、QMP native候補は`0/100000`だった。よって、present阻害の第一候補はindirect-light側へ移った。

model loadingを戻してindirect-lightだけskipしたvariantは、起動直後に一度presentした後、model/resource処理の進行に伴って`started=false`へ戻った。QMP画像は全画素が同じRGB `(13,115,255)` のclearで、cube輪郭もproduction objectも無かった。indirect-light skipでpresent境界は通っても、production 3D表示は未達である。

静的には、`onSystemInit()`でdefault indirect lightを非同期設定した後、sceneの`DefaultIndirectLight`に対して`RunPostSetupLoad()`が再度builder operationをpostする経路がある。また全production modelをECS strandへ投入し、async load完了後にsceneへ追加するため、両者の相互作用を第一仮説とする。release bundleの実際のindirect-light typeと最初の失敗commandはUNKNOWN。

### Diagnostic patch 0181 prepared

### Diagnostic patch 0182 prepared

release sceneがHDR型と判明したため、HDR asset validation、texture decode、cubemap、reflection、builder、scene assignmentの各段階にruntime markerだけを追加する0182をMac Devtoolで作成した。Devtool source commitは `876d075`、patch SHA-256は `1001ccc7b37721b31b42fdf185dc6dfc5e20b727c3f192516ca79611a8653c60`。patchは `meta-fluorite-trial` 配下へ登録済みで、Mini PC build/runtimeで最初の未達段階を確認する。

### 0182 HDR runtime result

0182 rootfsでHDRのasset valid、texture、cubemap、reflection、IBL builder、scene setは全てmarker到達した。しかしmodel loading skip + skybox skipでも、その後のframeは`started=false`へ移行し、QMP native候補は`0/100000`だった。QMP-only画像は2D HUD（FPS/CPU/GPU/Script）を表示したが、native 3D objectは無かった。従ってHDR処理のCPU側完了は確認できたが、GPU present成功とは扱わない。

次はproduction model投入数を`FLR0026_NATIVE_MODEL_LIMIT`で段階化する0183診断へ進む。1、4、8件程度でQMP pixelとmodel load progressを比較し、全件投入時だけ失敗するかを切り分ける。0183はMac Devtool source commit `0209cc8`から公式patch生成し、SHA-256は `0c6eddedc791ab5e54a2a8ffeeaf2fecde79d003941b6db8fe12775d92082c05`。

sceneのindirect-light typeをruntime markerで記録し、scene側 `DefaultIndirectLight` の再設定だけを `FLR0026_NATIVE_SKIP_SCENE_DEFAULT_INDIRECT_LIGHT` で抑止する0181診断patchをMac Devtoolで作成した。Devtool source commitは `2358e30`、patch SHA-256は `1b4d92d7be4363aa38d767f1e6857b4ee90e3157e14f2c6fed99785b30762630`。patchは `meta-fluorite-trial` 配下へ登録済みで、Mini PC build/runtimeで検証する。

### 0183 model-limit runtime result

- 0183は固定Mini PC receiver/build/TMPDIRで`do_patch` 104/104、`do_compile`
  2686/2686、full image 11748/11748まで成功した。rootfs SHA-256は
  `2e92588e4bc33ad8635ea56b74693a6d735aaa5f42ede8503162c9cfe08e3e95`。
- `su - agl-driver`の内側へ環境変数を置いた正しい起動で、1件・4件・8件の
  すべてについて`MODEL_LOAD_PLAN total=60 limit=N queued=N`を確認した。
- 3条件ともAOT、2D HUD（FPS/Frametime/CPU/GPU/Script）、Wayland surface、
  Vulkan swapchain/acquire、`SHAPE_READY`、自作cube登録、最初の2 frame
  (`started=true`)までは通った。その後`started=false`が継続した。
- QMP-onlyの中央3D候補領域`[200,100,400,250]`は、1件・4件・8件とも
  `0/100000`だった。証跡PPMはそれぞれ
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/model-limit-1-0183-qmp-valid.ppm`
  (SHA-256 `3bce21e7fa126b781b7b5034064d26245d54df3d259380aaf8a4d2241d5b79ca`)、
  `model-limit-4-0183-qmp.ppm` (SHA-256
  `1380cb1765c821fd9f36c7cb346ff5ed47a75a05c62a56829286923992537cb8`)、
  `model-limit-8-0183-qmp.ppm` (SHA-256
  `7a31811555a5d99a1f531ac608f529dd45d5074f418b3ce81fdc9a6ab743b594`)。
- よって「60件を一括投入したこと」だけでは説明できず、1件以下でも発生する
  model/resource async loadまたはsoftware Vulkanとの相互作用が次の調査対象である。
  indirect-lightはskipしているため、HDRだけを原因と断定することもできない。
- 3回ともQMP `quit`後にsocketと対象QEMU/シリアル接続の消失を確認した。

### 0183 verdict

| Criterion | Result |
| --- | --- |
| Correct model-limit delivery | PASS |
| Flutter 2D / CPU metrics | PASS |
| Native surface / swapchain / acquire | PASS |
| Model limits 1 / 4 / 8 | OBSERVED |
| Native 3D pixels | FAIL: `0/100000` for all three |
| QMP evidence / cleanup | PASS |

次は同じrootfsを使い、位置ではなくasset単位で最初のmodel/resourceを選択できる診断へ進む。どのGLBまたはmaterial uploadで`started=false`へ遷移するかを特定してから、製品修正を判断する。

## Runtime process and boundary audit (2026-09-05)

### Facts

- 現在のMacでは固定Devtoolコンテナだけが稼働し、BitBake、QEMU、flutter-auto、Westonの残留プロセスはない。Mini PC側にも同じ実行系の残留プロセスはない。
- productionの保存済みruntime logでは、AOT、Wayland surface、Vulkan surface/swapchain/acquire、10個のGLB読込、shape生成、Flutter frame begin/endまで到達した。command queueは`queued=23`から`queued=677`まで増えた。
- 同logではdriver側の`beginFrame`は14回、`endFrame`は7回までで、`FLR0026_VK_QUEUE_PRESENT`およびpresent boundary return/doneは観測されなかった。production QMP-only PPMの中央候補領域は`0/100000`で、HUDだけが表示された。
- production logにはアプリ由来の`Exception in handler`、`SIGSEGV`、`libLLVM`はない。一方、pure fixture logの`Light not found`反復は、fixtureでproduction lightを省いたことによる既知の診断ノイズである。
- 同じQEMU/Wayland/Vulkan profileのpure fixtureでは、present boundary completionと青いcubeのQMP実画素が確認済みである。

### Inferences

- Flutter/DartのAOT、2D HUD、CPU/GPU/FPS表示、Wayland合成、QMP capture全体は疎通している。従って現時点で「Flutter内部の問題」とは判定しない。
- productionだけで、asset/resource commandの処理後にdriver側が遅れ、present前で詰まっている。表示できない主因はproduction native render pathに絞られた。

### Hypotheses / UNKNOWN

- 第一仮説は、最初の特定GLBのtexture/material uploadまたはpipeline compilationがsoftware Vulkan/llvmpipeを停滞させていること。
- 代替仮説は、複数assetのasync load、scene insertion、indirect-light commandの相互作用または累積command量によるback-pressureである。
- 最初に停止するassetと正確なGLB/resource/pipeline/scene insertion境界はUNKNOWN。例外がないことはdriver内部の待機・未完了commandがないことを意味しない。

### Act

追加パッチと再buildは一旦保留する。既存rootfsと固定QMP-only loopを使い、asset単位の最初の未達をruntime evidenceで特定してから、必要最小限のDevtool-generated patchへ進む。

## Iteration 113 — production asset runtime failure (2026-09-05)

### Facts

- 0184 rootfs（SHA-256 `fe6e54ada5259642ca1b3d26ddaa8dda2bd0d60d4cb90e760f22178486aa5cc1`）を固定QEMU profileで起動した。
- `su - agl-driver`の内側へ`FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`と
  `FLR0026_NATIVE_MODEL_MATCH=sequoia_ngp.glb`を渡し、minimal geometryは無効にした。
- AOT、Flutterの`Native is ready`、Wayland surface、Vulkan swapchain/acquire、
  production sceneのcamera適用まで到達した。
- selectorは`assets/models/sequoia_ngp.glb`を16件選び、
  `MODEL_LOAD_PLAN total=60 limit=60 match=sequoia_ngp.glb inspected=60 queued=16`を出した。
  実際のGLB読込ログは`Reading: .../assets/models/sequoia_ngp.glb`である。
- `FRAME_BEGIN seq=1/2 started=true`の後、`seq=3`以降は`started=false`が継続した。
  QMP-only PPMは720x400、中央候補領域`[200,100,400,250]`が`0/100000`で、
  PPM SHA-256は`c3ae06666df658982411443e613bc0e8117f74a12f37face732b8b464fa097f2`。
  画面はHUD（FPS、Frametime、CPU、GPU、Script）とScenesボタンのみで、production
  3D objectは無かった。
- 約121秒後、ゲストkernelが
  `FEngine::loop[867]: ... segfault ... in libLLVM.so.18.1`を報告した。
  保存したシリアル証跡は`$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/serial-model-sequoia-prod-0184.log`。
- 試行後はQMP `quit`を使い、QMP socketとserial接続を閉じた。不要なQEMUは残っていない。

### Inferences

- Flutter/Dart、2D UI、CPU/GPU/FPS metrics、Wayland合成、Vulkan surface/swapchain/acquireは
  疎通している。今回の直接エラーはFlutter内部ではなく、Filament driver threadが
  production GLBのresource/pipeline処理中にllvmpipeの`libLLVM.so.18.1`でsegfaultしたものと判定する。
- minimal geometryだけを有効にしたA/Bでは同じrootfs/profileで青いcubeがQMPに出るため、
  QEMU画面・camera・native surfaceだけではproduction black screenを説明できない。
- 現時点の最小再現は「production scene + `sequoia_ngp.glb`投入」であり、assetの
  texture/material/pipeline内容、またはFilamentのasset uploadとllvmpipeの相互作用が第一候補である。

### Hypotheses / UNKNOWN

- 第一仮説: `sequoia_ngp.glb`の特定texture/material/primitiveがllvmpipeのLLVM pathをクラッシュさせる。
- 代替仮説: GLB単体ではなく、scene insertionまたはasync resource uploadの順序とllvmpipeの
  driver queueが組み合わさってクラッシュさせる。
- UNKNOWN: segfaultを発生させるGLB内部要素、Filament関数、LLVM call siteは未特定。
  `FRAME_BEGIN=false`はFrameSkipperの結果であり、根本原因の位置そのものとはまだ断定しない。

### Act

- 追加patchと再buildはこの結果だけでは作らない。次は同じ0184 rootfsで`Fox.glb`、
  `radar_cone.glb`などをproduction sceneへ1件ずつ選択し、クラッシュのasset依存性を
  QMP-only PPMとシリアルkernel logで比較する。

## Iteration 114 — second production asset comparison (2026-09-05)

### Facts

- 同じ0184 rootfs・QEMU profileで、minimal geometryを無効にし、
  `FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`と`FLR0026_NATIVE_MODEL_MATCH=Fox.glb`を
  `agl-driver`へ渡した。
- selectorは`assets/models/Fox.glb`を3件選び、
  `MODEL_LOAD_PLAN total=60 limit=60 match=Fox.glb inspected=60 queued=3`を記録した。
  GLB読込も`Reading: .../assets/models/Fox.glb`まで到達した。
- `FRAME_BEGIN seq=1/2 started=true`の後、`seq=3`以降は`started=false`が継続した。
  QMP-only PPMは中央候補`0/100000`、SHA-256は
  `b4d706bc8386394126d0df077d98b1812cd0fd3f991c632660ce9e24634e1c7b`で、
  HUDとScenesボタンだけだった。
- 試行後はQMP `quit`で終了し、QMP socketは消失した。Fox比較中にはkernel segfaultは
  まだ発生していないが、sequoiaで確認済みのllvmpipe/LLVM segfault仮説を否定するものではない。

### Inferences

- sequoiaだけのasset破損よりも、production GLBをFilamentへ投入した時点で共通する
  async resource/pipelineまたはdriver queue経路が、2D表示とは独立して失敗している可能性が高い。
- `queued=16`のsequoiaと`queued=3`のFoxの双方で同じframe skipが出たため、単純な投入数だけでは説明できない。

### Hypotheses / UNKNOWN

- 共通候補はGLBのmaterial/texture upload、Filament asset completion待ち、または
  renderableのscene insertion後に発生するllvmpipe command処理である。
- Foxが長時間後に同じLLVM segfaultへ進むか、asset内容ごとに異なる失敗点になるかはUNKNOWN。

### Act

- 追加patch・再buildはまだ行わず、既存0184 runtime evidenceを基準にする。
  次は`radar_cone.glb`を比較し、production GLB共通の再現性を確認する。

## Iteration 115 — third production asset comparison (2026-09-05)

### Facts

- 同じ0184 rootfs・QEMU profileで、minimal geometryを無効にし、
  `FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`と`FLR0026_NATIVE_MODEL_MATCH=radar_cone.glb`を
  `agl-driver`へ渡した。
- selectorは`assets/models/radar_cone.glb`を4件選び、
  `MODEL_LOAD_PLAN total=60 limit=60 match=radar_cone.glb inspected=60 queued=4`を記録した。
  GLB読込も`Reading: .../assets/models/radar_cone.glb`まで到達した。
- `FRAME_BEGIN seq=1/2 started=true`の後、`seq=3`以降は`started=false`が継続した。
  QMP-only PPMは中央候補`0/100000`、SHA-256は
  `dd3d8d762a35adf3b8dd001500654d8b0d2cf6d8c269afe3ef5170cd1d1a9869`で、
  HUDとScenesボタンだけだった。
- 試行後はQMP `quit`で終了し、QMP socketは消失した。

### Inferences

- sequoia、Fox、radarの3種類で、個別GLBの選択・読込直後に同じ`started=false`と
  native pixel `0/100000`が再現した。production GLB共通のFilament resource/driver
  経路が、Flutter/Dartや個別asset破損より優先度の高い原因候補になった。
- sequoiaでの`libLLVM.so.18.1` segfaultは、その共通経路がasset内容に応じて最終的に
  driver thread crashへ進む実証として扱う。

### Hypotheses / UNKNOWN

- 共通候補はGLBの非同期resource upload、material/textureまたはpipeline生成後の
  Filament driver command処理である。
- 3種類とも長時間LLVM segfaultへ進むか、どのasset属性がsequoiaのクラッシュを誘発するかはUNKNOWN。

### Act

- runtime-only asset選択での共通再現が取れたため、次はDevtool sourceでasset load完了・
  material/texture/pipeline・scene insertionの各境界を記録する最小診断変更を作る。
  そのpatchは公式Devtool生成→layer登録→bundle→固定Mini PC buildの順で進める。

## Iteration 116 — production asset stage trace (2026-09-05)

### Facts

- 0185のMini PC buildで生成したrootfs SHA-256は
  `03acff5722fe6b75729b1b2008fde85dbb5d5cc3a456b60a00ba1a36d42dd8fa`。
- 同じ固定QEMU profileで、`FLR0026_MODEL_STAGE_TRACE=1`、
  `FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`、`FLR0026_NATIVE_MODEL_MATCH=sequoia_ngp.glb`を
  `agl-driver`環境へ渡した。AOT、Wayland surface、Vulkan swapchain/acquire、2D HUDは
  これまでと同じく成功した。
- asset stage markerは順に次を記録した。
  `MODEL_STAGE_ASSET_CREATED bytes=13671064 entities=22`、
  `MODEL_STAGE_ASYNC_BEGIN`、`MODEL_STAGE_INSTANCE_READY`、progress `1`、
  `MODEL_STAGE_COMPLETE`、および16個の`MODEL_STAGE_SCENE_ADD_BEGIN/DONE`。
  したがってCPU側のasset生成、async開始、instance生成、load完了、scene insertionは
  少なくともアプリ側ログ上で完了している。
- `FRAME_BEGIN seq=1/2`は`started=true`、`seq=3`以降は`started=false`だった。
  QMP-only PPM `model-stage-sequoia-0185-qmp.ppm`は720x400、SHA-256は
  `efa03d2ea0c4ada1e8e3d83b0046dbc65461355ded07e986b62804bb1ca3fc84`、
  中央候補領域`[200,100,400,250]`は`0/100000`だった。画面には2D HUDとCPU/GPU/FPS等が
  残ったが、production 3D object pixelは無かった。
- 約147秒後、guest kernelは`FEngine::loop[874]`の
  `segfault ... in libLLVM.so.18.1`を報告した。アプリ側のFlutter exceptionは確認されなかった。
  実行後はQMP `quit`で停止し、対象QMP socketとQEMU processは消失した。

### Inferences

- 疎通はFlutter/Dart AOT、2D描画、性能HUD、Wayland合成、Vulkan surface/swapchain/acquire、
  FilamentのCPU側asset/scene準備まで成立している。
- 「Flutterの中で3Dを描けていない」と大きく括る段階は終わった。最初の未達は、
  CPU側scene insertion完了後にFilament driverがresource/commandを消費し、次のpresentへ戻る
  境界である。直接観測されたクラッシュはllvmpipe LLVM側である。

### Hypotheses / UNKNOWN

- 第一候補は、scene insertion後のrenderable material/texture uploadまたはpipeline compileが
  software Vulkan/llvmpipeを停止させること。
- 代替候補は、Filament driver queueのback-pressure、非同期resource完了待ち、または
  `sequoia_ngp.glb`内の特定primitive/materialがLLVM pathを誘発すること。
- UNKNOWN: 最初に詰まるFilament関数、GPU command、texture/material/pipelineの具体的対象。
  `started=false`はFrameSkipperの観測結果であり、それ自体を根本原因とは断定しない。

### Act

- 0185は原因境界の証拠として固定し、いったん追加の製品修正を入れない。次の診断は
  Filamentのrenderable/resource/pipeline境界を、同じDevtool source→公式patch→bundle→
  固定Mini PC buildの流れで最小限記録する。3D表示とPlanetarium遷移の再試行は、
  driver/present側の未達をもう一段狭めてから行う。

## Iteration 117 — production scene with zero model load (2026-09-05)

### Facts

- 0185 rootfs（SHA-256
  `03acff5722fe6b75729b1b2008fde85dbb5d5cc3a456b60a00ba1a36d42dd8fa`）を変更せず、
  `FLR0026_NATIVE_MODEL_LIMIT=0`と`FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`でruntime-only A/Bを行った。
- selectorは`MODEL_LOAD_PLAN total=60 limit=0 match= inspected=1 queued=0`となり、GLB読込と
  scene insertionを除外できた。AOT、Vulkan backend/llvmpipe、Wayland surface、Vulkan
  swapchain/acquire、2D HUDは成立した。
- model 0件でも`FRAME_BEGIN seq=1/2 started=true`、`seq=3`以降`started=false`が継続した。
  ログにはqueue submit result=0とWayland surface creationがあるが、present完了は無かった。
- QMP-only PPM `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/model-limit-zero-0186-qmp.ppm`は
  720x400、SHA-256 `59d00671d1c8bbc3244cbe1ff1d0aa046e36a19204cf05572609c8fac9d6d11a`、
  中央候補領域`[200,100,400,250]`は`0/100000`だった。2D HUDは表示されたが、native
  3D pixelは無かった。
- 試行後はQMP `quit`で停止し、QMP socket、QEMU、flutter-autoの残留は無かった。

### Inferences

- production GLBを1件も投入しなくても同じ`started=false`が再現したため、単一GLBの破損だけを
  原因とは扱えない。失敗条件はproduction sceneの初期化、またはモデル以外のFilament
  resource/driver commandにも及ぶ。
- Flutter/Dart、2D表示、Wayland、Vulkan surface/swapchain/acquire、submitまでは引き続き
  疎通している。present未達の層はFilament driver/software Vulkan側に残る。

### Hypotheses / UNKNOWN

- 第一候補は、production sceneで生成されるmodel以外のresource（light、skybox、material、
  pipeline等）またはその初期化順序がdriver queueを停滞させること。
- 代替候補は、production sceneを選択した時点で発生するFilament command queueの状態、
  frame synchronization、またはllvmpipe固有の初期化問題である。
- UNKNOWN: model 0件でも発行される最初のGPU commandと、それを消費するFilament関数。

## Iteration 118 — llvmpipe single-thread production-only runtime (2026-09-05)

### Facts

- 0185 rootfsを変更せず、`LP_NUM_THREADS=1`、`FLR0026_NATIVE_MODEL_LIMIT=1`、
  `FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`でminimal geometryを無効にしたproduction-only実行を行った。
- selectorは`MODEL_SELECTED ordinal=0 asset=assets/models/sequoia_ngp.glb`、
  `MODEL_LOAD_PLAN total=60 limit=1 inspected=2 queued=1`を記録した。Filament material読込と
  `assets/models/sequoia_ngp.glb`の読込開始まで到達した。
- `FRAME_BEGIN seq=1/2 started=true`の後、`seq=3`以降は`started=false`が続き、production-onlyの
  `QUEUE_PRESENT`、present boundary、commit完了は観測できなかった。
- QMP-only PPM `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/llvmpipe-single-production-only-0189-qmp.ppm`
  は720x400、SHA-256 `a4972e7e976c35a3231772ee2e8b178ef588884dcd734859f7dcf0a519beb90e`。
  中央候補領域`[200,100,400,250]`は`0/100000`、全画面も`0/288000`で、3D object pixelは無かった。
- 追加のシリアル出力では約210秒後に`FEngine::loop`のsegmentation faultが発生し、
  `libLLVM.so.18.1`内の命令位置が示された。Flutter/Dart由来のexceptionは確認されなかった。
- 直前の同一0189 QEMUでminimal geometryを併用したA/Bでは、約45秒後にpresent完了が反復し、
  QMP中央候補は`15212/100000`、既知の青いcubeと同一だった。従って`LP_NUM_THREADS=1`だけでは
  production object表示の成功とは言えない。
- 試行後はQMP `quit`で終了し、QMP socket、QEMU、flutter-auto、WestonはMacとMini PCの双方で残っていない。
  固定Devtool container `fluorite-mac-devtool`だけは再利用状態で稼働している。

### Inferences

- Flutter/Dart AOT、2D UI、CPU/GPU/FPS HUD、Wayland composition、Vulkan surface/swapchain/acquireは
  既存の成功証拠と今回の起動ログから成立している。したがって「Flutter全体の描画機能が壊れている」とは判定しない。
- 今回はGLBのCPU側読込開始後にframeが停滞し、最終的にFilament engine loopからllvmpipe LLVMへ落ちた。
  失敗境界はFlutter widgetではなく、Filament driverのresource/pipeline command処理とsoftware Vulkan
  実装の接点にさらに絞られた。
- llvmpipeを単一スレッドにしてもproduction-onlyは回復せず、単純なthread数過多だけでは説明できない。
  minimal cubeが同一profileで出るため、QMP capture、camera、native surfaceの問題も優先度は低い。

### Hypotheses / UNKNOWN

- 第一候補は、GLBのmaterial/texture/pipeline uploadまたはそれに続くrenderable登録がllvmpipeのLLVM経路を
  長時間占有またはクラッシュさせること。
- 代替候補は、production sceneのasync resource queueとframe synchronizationの相互作用である。
- UNKNOWN: 最初にLLVMへ到達するFilament関数、GPU command、GLB内の具体的material/texture/primitive。

### Act

- 0189の結果をもってruntime-only解析を一旦固定する。今回の結果だけで製品修正patchは作らない。
- 次の変更が必要な場合は、Filamentのrenderable/resource/pipeline completion境界だけをDevtool sourceで
  記録し、公式Devtool extraction→`meta-fluorite-trial` patch登録→bundle→Mini PC build→QMP-only検証の
  既定フローを維持する。

## Iteration 119 — deferred async source release runtime A/B (2026-09-05)

### Facts

- Devtool source commit `1418671`で、非同期モデルロード直後の`releaseSourceData()`をシーン登録後へ
  遅延する変更を作成した。Devtool公式抽出patch SHA-256は
  `5dfd2b95e2da16916dc5ea7108630670404c5bd5b816fa0bb7d7079b2cf53d17`で、
  `meta-fluorite-trial`側の登録はproject commit `f8afd1f`、bundle SHA-256は
  `9c8b9cf04754305777d57e5d783a2889f48a977c240e238b5fd6556b0c06e099`。
- 固定Mini PCで`do_patch` 104/104、`do_compile` 2686/2686、full image 11748/11748を完了した。
  使用rootfs SHA-256は`fdcafd0365fe9dd0ae9a65b8aa196a6b34fcc36453f715d3799cab0dbe008a50`。
- QEMU 0192を一つだけ起動し、`FLR0026_MODEL_STAGE_TRACE=1`、
  `FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`、`FLR0026_NATIVE_MODEL_LIMIT=2`で実行した。
  AOT、Filament Vulkan/llvmpipe、Wayland surface、swapchain、acquire、GLB 2件の
  asset created、async begin、instance ready、progress=1、completeまで到達した。
- 選択モデルは`sequoia_ngp.glb`と`Fox.glb`。ただし`MODEL_STAGE_SCENE_ADD_BEGIN/DONE`は一度も出ず、
  `FRAME_BEGIN seq=1/2 started=true`の後は`started=false`が継続した。
- QMP-only PPMは
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/release-source-model-limit2-0192-qmp.ppm`、
  720x400、SHA-256 `76695a150f4671c3cc786d365cf60057f085ee9f15037f6a3f7fe7bbcd579692`。
  中央候補`[200,100,400,250]`は`0/100000`、bounding boxなしだった。
- 0192はQMP `quit`で停止し、QMP socket、QEMU、flutter-auto、Westonは残っていない。
  Mini PC側にもQEMU、flutter-auto、Weston、BitBake、Devtoolの残留はなかった。

### Inferences

- 0186のsource変更はビルド・起動を壊していないが、今回の条件では3D画素を回復しなかった。
  `asyncBeginLoad`直後のsource解放は有力な候補ではあるものの、現時点で真因とは言えない。
- Flutter/Dart AOT、2D UI、Wayland接続、Vulkan surface/swapchain/acquire、およびCPU側のGLB
  asset/instance準備は成立している。したがって「Flutter全体の問題」とは判定しない。
- 今回は2モデルのロード完了後にシーン追加マーカーが無く、present完了とnative 3D画素も無い。
  失敗境界は、少なくともFlutter widgetより下、Filamentのmodel-to-scene登録またはその後の
  renderable/resource/driver command処理にある。

### Hypotheses / UNKNOWN

- 第一候補は、`loadingInstances`からシーン登録へ進む条件またはinstancing modeの状態が、
  asset load完了時点で期待値になっていないこと。
- 代替候補は、シーン登録は別経路で行われているが、Filament driverのresource/pipeline処理が
  `started=false`とsoftware Vulkan LLVM境界の停止を引き起こすこと。
- UNKNOWN: 0192でシーン追加が行われなかった正確な条件、ならびに最初に停止するFilament関数・
  GPU command。今回の実行時間内では新たなLLVM segfaultは観測しなかった。

### Act

- 0186の変更は「仮説A/Bが3D表示を回復しなかった」証拠として固定する。追加の製品patchはまだ作らない。
- 次は`ModelSystem::updateAsyncAssetLoading`のinstancing mode、`loadingInstances`、scene entity
  登録条件を、既存のsourceとruntime markerの対応でさらに狭める。必要な変更だけを同じ
  Devtool source→公式patch→layer→bundle→Mini PC build→QMP-onlyの手順で検証する。

## Iteration 120 — scene insertion reached, llvmpipe crash reproduced (2026-09-05)

### Facts

- 0186 rootfsを再利用し、パッチを追加せず`FLR0026_MODEL_STAGE_TRACE=1`、
  `FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`、`FLR0026_NATIVE_MODEL_LIMIT=8`でruntime-only確認を行った。
- selectorは`sequoia_ngp.glb`、`Fox.glb`、`radar_cone.glb`、`half_torus.glb`、`cb_floor.glb`、
  `garagescene.glb`の6 assetを作成した。重複モデルを含む8件を選択し、asset created、async begin、
  instance ready、progress=1まで到達した。
- `Fox.glb`と`sequoia_ngp.glb`のsecondary、`garagescene.glb`のnoneについて、
  `MODEL_STAGE_SCENE_ADD_BEGIN/DONE`を実際に確認した。したがって、model limit=2で観測されなかった
  scene insertionは、primaryだけを選んだことによるものであり、常に未到達とは言えない。
- scene insertion後も`FRAME_BEGIN seq=1/2 started=true`の後は`started=false`が継続した。
  約138秒後、guest kernelが`FEngine::loop`から`libLLVM.so.18.1`へのsegmentation faultを報告し、
  flutter-autoは終了した。Flutter/Dart exceptionは確認しなかった。
- QMP-only PPMは
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/release-source-model-limit8-0193-qmp.ppm`、
  720x400、SHA-256 `e1e232cba44b39e0bcc4ffc7d2b33bd94f312eea3ad5f7663cf778c672858f82`。
  中央候補`[200,100,400,250]`は`0/100000`、bounding boxなし。2D HUDは画素として残っていた。
- 0193はQMP `quit`で停止し、QMP socket、QEMU、flutter-auto、Westonは残っていない。

### Inferences

- `primary`だけでなく`secondary`/`none`のscene insertionまで通過しても3D画素がゼロであるため、
  現在の主な失敗境界はmodel selectionやFlutter widgetではなく、scene insertion後のFilament
  renderable/resource/driver command処理にある。
- AOT、2D HUD、Wayland surface、Vulkan swapchain/acquire、CPU側GLB処理、Filament scene insertion
  は成立している。したがって「Flutterの中全体の問題」とは判定しない。
- `started=false`はframe開始後の同期停止として現れ、最終的な直接エラーはllvmpipeのLLVM経路に出ている。
  ただし、LLVM segfaultを根本原因と断定せず、先行するFilament command/resource状態はUNKNOWNとする。

### Hypotheses / UNKNOWN

- 第一候補は、scene insertion後に作られるrenderable/material/texture/pipeline commandがllvmpipeの
  driver queueを停滞させること。
- 代替候補は、Filamentのframe synchronizationとllvmpipe LLVM JITの相互作用である。
- UNKNOWN: 最初に不正状態になる具体的なrenderable、material、GPU command、Filament関数。
  0193でscene insertionそのものの到達は確認できたが、scene内のどのassetが最初に失敗するかは未分解。

### Act

- 0192の「scene insertion未到達」という解釈を修正し、0193でscene insertion到達後の停止として固定する。
- 追加patchはまだ作らない。次は既存runtimeの資産数・種類をさらに絞り、scene insertion後のどの
  renderable/resourceが最初にllvmpipe停止を誘発するかをruntime-only A/Bで分解する。

## Iteration 121 — single sequoia asset reaches present boundary (2026-09-05)

### Facts

- 0186 rootfsを再利用し、`FLR0026_NATIVE_MODEL_MATCH=sequoia`、
  `FLR0026_NATIVE_MODEL_LIMIT=2`、indirect light skip、stage traceで単一asset A/Bを行った。
  selectorは同じ`sequoia_ngp.glb`のprimaryとsecondaryだけを選び、asset created、async begin、
  instance ready、progress=1、secondaryの`MODEL_STAGE_SCENE_ADD_BEGIN/DONE`まで到達した。
- scene insertion後は`FRAME_BEGIN seq=1/2 started=true`、seq=3以降は`started=false`となった。
  ログ上は`VK_QUEUE_PRESENT_BEGIN`、`FINISHED_SIGNAL_ACQUIRE_DONE present=true`まで到達したが、
  正常なpresent完了マーカーは得られなかった。
- 約151秒後、guest kernelが`FEngine::loop`から`libLLVM.so.18.1`へのsegmentation faultを再現した。
  異常後もflutter-auto threadが残ったため、QMP専用画面を追加採取してからQMP `quit`で停止した。
- QMP-only PPM（遅延採取）は
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/release-source-match-sequoia-0194-late-qmp.ppm`、
  720x400、SHA-256 `a4972e7e976c35a3231772ee2e8b178ef588884dcd734859f7dcf0a519beb90e`。
  中央候補`[200,100,400,250]`は`0/100000`、bounding boxなしだった。
- 0194停止後、QMP socket、QEMU、flutter-auto、Westonは残っていない。

### Inferences

- 混在assetを除いても同じ停止とLLVM segfaultが出たため、`garagescene`など特定の大型assetだけを
  原因とする説明は弱くなった。sequoiaのscene insertion後に、renderable/resource/pipelineまたは
  そのdriver command経路で停止する可能性が高い。
- `VK_QUEUE_PRESENT_BEGIN`まで通るため、Wayland surface、swapchain acquire、queue submit、scene
  insertion、present入口は成立している。`present入口後の完了`とsoftware Vulkan LLVM境界が未成立である。
- 0192のscene insertion未到達という推定は、0193・0194で完全に修正された。

### Hypotheses / UNKNOWN

- 第一候補は、sequoiaのmaterial/texture/pipelineまたはrenderable commandがllvmpipe LLVM JITと
  相互作用し、present完了を阻害すること。
- 代替候補は、present wait/fenceとFilament driver threadの同期状態である。
- UNKNOWN: present完了直前に実行される具体的GPU command、material/primitive、LLVMの呼出元。

### Act

- 0194は単一assetでも再現するruntime証拠として固定する。追加patchはまだ作らない。
- 次は同じscene insertion経路で、sequoia以外の小型assetまたは自作GLBを使い、asset内容と
  driver/present停止を分離するruntime A/Bを行う。

## Iteration 122 — forcing skipped frames does not recover production 3D (2026-09-05)

### Facts

- 0186 rootfsを再利用し、`FLR0026_SYNC_TRACE=1`、
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`、`FLR0026_NATIVE_MODEL_MATCH=sequoia`、
  `FLR0026_NATIVE_MODEL_LIMIT=2`でruntime-only A/Bを行った。
- `FrameSkipper`はseq=1/2では`NO_FENCE`、seq=3以降では`linked=false`と`TIMEOUT_EXPIRED`相当を
  記録したが、force-renderにより`FRAME_END`まで継続して実行された。
- `VK_QUEUE_SUBMIT_DONE result=0`、`VK_PRESENT_BOUNDARY_BEGIN`、`VK_QUEUE_PRESENT_BEGIN`まで到達した。
  しかし約97秒後に`FEngine::loop`から`libLLVM.so.18.1`へのsegmentation faultを再現した。
- QMP-only PPMは
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/force-render-sequoia-0196-qmp.ppm`、
  720x400、SHA-256 `cbc03723aa3bc264d6e3de50bb43b1a2aafe627ebc733cb3be62e41530c09689`。
  中央候補`[200,100,400,250]`は`0/100000`、bounding boxなしだった。
- 0196はQMP `quit`で停止し、QMP socket、QEMU、flutter-auto、Westonは残っていない。

### Inferences

- `started=false`を強制的に回避しても3D画素とpresent完了は回復せず、FrameSkipperだけを修正しても
  本番3D表示の解決にはならない。
- fence未リンクは実際の同期異常として存在するが、同時にFilament driver commandの処理が
  llvmpipe LLVMで停止するため、症状と根因を分離して扱う必要がある。
- Flutter/Dart、Wayland、Vulkan acquire/submit、scene insertionは成立し、失敗境界は引き続き
  Filament Vulkan driverとllvmpipeのcommand/present完了区間にある。

### Hypotheses / UNKNOWN

- 第一候補は、scene render commandまたはpresent commandがllvmpipe側で完了せず、fenceがリンクされないこと。
- 代替候補は、Filamentのqueue flush/present待機順序とllvmpipe LLVM JITの相互作用である。
- UNKNOWN: fence未リンクを作る最初のcommandと、LLVM segfaultの直接呼出元。

### Act

- FrameSkipper強制解除を製品修正として採用しない。追加patchはまだ作らない。
- 次は自作の単純geometryをproduction `ModelSystem`のscene insertion経路へ通す、または既存小型GLBを
  その経路で単独投入し、resource種類とdriver commandの差を確認する。

### Act

- 追加パッチはまだ作らない。次は既存sourceを読み、production scene setupのうちmodel以外の
  light/skybox/material/pipelineをruntime markerなしで分解して確認する。必要になった場合だけ、
  その境界に限定したDevtool source変更を作成する。

## Iteration 123 — scene-content skip isolates stable present path (2026-09-05)

### Facts

- 0186 rootfsを再利用し、`FLR0026_NATIVE_SKIP_SCENE_CONTENT=1`、
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`、sequoia match、model limit 2、同期traceで
  runtime-only A/Bを行った。
- sequoiaのasset created、async begin、instance ready、progress=1、complete、secondaryの
  scene add begin/doneを確認した。GLBのCPUロードとscene insertionは成立している。
- seq=3以降はfence未リンクによる`started=false`が発生したが、force-renderによりフレーム処理を継続した。
- シーン内容を外した状態では、`vkQueueSubmit result=0`、`vkQueuePresent result=0`、
  `PRESENT_BOUNDARY_DONE`、`COMMIT_DONE`が約2300フレーム継続した。flutter-autoも実行中だった。
- QMP-only PPMは
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/skip-scene-content-0197-qmp.ppm`、
  720x400、SHA-256 `a4972e7e976c35a3231772ee2e8b178ef588884dcd734859f7dcf0a519beb90e`。
  中央候補`[200,100,400,250]`は`0/100000`だった。scene contentを描画していないため、
  3D表示成功の証拠には数えない。
- QMP `quit`後、QMP socket、QEMU、flutter-auto、Westonは残っていない。

### Inferences

- scene contentを外すとsubmit/presentが安定するため、Wayland surface、swapchain acquire、
  queue/present全体の恒常故障だけでは説明できない。
- 0193/0194の本番sceneでscene insertion後に停止・LLVM segfaultが出て、0197では同じasset準備と
  frame/presentが安定したことから、最有力の境界は`renderer->render(fview_)`が本番sceneの
  renderable/material/texture/pipelineを消費する区間である。
- Flutter widget/AOT、2D HUD、CPU側GLBロード、scene insertionは主因ではない。現時点で「Flutter内部の
  問題」とは判定しない。

### Hypotheses / UNKNOWN

- 第一候補は本番GLBのmaterial/texture/pipelineまたはrenderable commandがllvmpipe LLVM JITを
  停滞・クラッシュさせること。
- 代替候補は、scene content commandとFilament frame fence/queue同期の相互作用である。
- UNKNOWN: scene render内で最初に失敗するrenderable、material、texture、pipeline、GPU command、
  Filament関数。

### Act

- 0197は「scene contentを除くとpresentが安定する」切り分け証拠として固定し、製品patchはまだ作らない。
- 次は既存の固定rootfsで、scene contentを描画する対象を自作単純geometryまたは小型GLBへ段階的に
  置換・限定し、どのrenderable/resourceから失敗するかをruntime-onlyで確認する。

## Iteration 124 — shapes/lights remain a production failure trigger (2026-09-05)

### Facts

- 0186 rootfsを再利用し、`FLR0026_NATIVE_SKIP_MODEL_LOAD=1`、
  `FLR0026_NATIVE_SKIP_SKYBOX=1`、`FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`、force-render、
  同期traceでruntime-only A/Bを行った。
- モデル、skybox、indirect lightを除外したことをログで確認した。一方、production sceneの
  37 shapeと13 lightは残り、全shapeの`SHAPE_READY ... renderable=true`を確認した。
- seq=1/2は`started=true`、seq=3以降はfence未リンクの`started=false`となり、約102秒後に
  `FEngine::loop`から`libLLVM.so.18.1`へのsegmentation faultを再現した。
- QMP-only PPMは
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/no-model-skybox-indirect-0198-qmp.ppm`、
  720x400、SHA-256 `a4972e7e976c35a3231772ee2e8b178ef588884dcd734859f7dcf0a519beb90e`。
  中央候補`[200,100,400,250]`は`0/100000`だった。
- QMP `quit`後、QMP socket、QEMU、flutter-auto、Westonは残っていない。

### Inferences

- 0198は、特定GLB、skybox、indirect lightのいずれか単独が必須条件ではないことを示す。
  scene contentを描画しない0197だけが安定し、shape/lightを残した0198で停止したため、
  shape/lightのrender command、またはproduction scene contentに共通するFilament処理が有力である。
- Flutter/AOT、2D HUD、Wayland、Vulkan surface/swapchain/acquire、llvmpipeの一般的なpresent入口だけを
  原因とする説明は弱くなった。ただしshapeとlightのどちらが先かは未分解である。

### Hypotheses / UNKNOWN

- 第一候補はproduction shapeのmaterial/primitive/renderable commandまたはshape/light setup順序。
- 代替候補はshape/lightを含むFilament sceneの共通frame commandとllvmpipe LLVM JITの相互作用。
- UNKNOWN: shapeだけ、lightだけ、または最初の具体的なrenderable/material/GPU commandのどれが
  停止を発生させるか。

### Act

- 0198はshape/lightを残したproduction content経路の失敗証拠として固定し、製品patchはまだ作らない。
- 次はshapeだけ、lightだけの順で無効化する診断境界を追加し、自作geometryの既知成功経路と比較する。

## Iteration 125 — self-made native cube still produces real pixels (2026-09-05)

### Facts

- 0186 rootfsを再利用し、`FLR0026_NATIVE_PURE_FIXTURE=1`、
  `FLR0026_NATIVE_MINIMAL_GEOMETRY=1`、force-render、同期traceで自作native cubeを再実行した。
- QMP-only late captureは720x400、中央候補`[200,100,400,250]`で`15212/100000` changed pixels、
  bounding box `[291,139,138,122]`を得た。PPM SHA-256は
  `9294659aeb9743c8d36d3076ec70161ce6a3f2b6d77a2b05e77674db1df73471`で、既知成功cubeと一致した。
- 同じ実行では`vkQueuePresent result=0`、`PRESENT_BOUNDARY_DONE`が継続し、flutter-autoも生存していた。
- fixtureモードではproduction lightを生成していないため、`Entity(...): Light not found`が反復した。
  これはfixture固有の診断エラーであり、本番scene失敗の証拠とは分離する。
- QMP `quit`後、QMP socket、QEMU、flutter-auto、Westonは残っていない。

### Inferences

- 自作cubeは同じVulkan/Wayland/QEMU表示経路で実画素を生成できるため、表示領域・QMP capture・
  native surface全体の故障ではない。
- 本番sceneだけがscene content描画後に停止するという切り分けを補強する。ただしfixtureはproduction
  ModelSystem/shape/light資産を使っていないため、本番3D成功とは扱わない。

### Hypotheses / UNKNOWN

- 本番shape/lightのどちらが最初にllvmpipe LLVM停止を誘発するかはUNKNOWN。
- fixtureの`Light not found`は別の既知問題だが、今回のcube pixel生成を妨げていない。

### Act

- 自作native 3D pixelの再現証拠として固定する。
- Docker/Devtoolが復旧後、shape-only/light-only診断スイッチをsource側へ追加し、生成patchから権威buildへ進める。
