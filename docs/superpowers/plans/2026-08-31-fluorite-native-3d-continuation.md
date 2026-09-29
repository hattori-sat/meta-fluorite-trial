# Fluorite Native 3D表示到達・継続実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 自作Flutterモックで確認済みのQMP表示経路を基準に、本番native Filamentシーン、Wayland child surface、シーン遷移、QEMU入力を実画面pixelまで追跡する。

**Architecture:** まず既存の診断パッチ群を保ったままFlutter mockだけをDevtool生成patchで無効化し、native fixtureの最小経路を同じartifact/build/QEMU profileで再現する。次に `shape/renderable → beginFrame/render/endFrame → Wayland attach/commit → QMP region` の最初の未達境界を一変数ずつ検証し、native fixtureが成立してから本番sceneとbutton/direct routeを比較する。

**Tech Stack:** Mac Docker/devtool, Yocto/OpenEmbedded, BitBake, AGL flutter-auto, Filament Vulkan, Wayland/AGL compositor, QEMU qemux86-64, QMP/HMP screendump, shell/Python evidence scripts.

**Spec:** `work/tickets/FLR-0026-fluorite-3d-display.md`

## Global Constraints

- Patchのsource変更はMacの同一永続Devtool workspaceで行い、生成patch本文を直接編集しない。
- mini PCはGit bundleを受け取る固定receiverと固定build directory/TMPDIRだけを再利用する。
- 新しいYocto `TMPDIR`、receiver、Docker container/volumeを作成しない。
- `/mnt/yocto/**/{downloads,sstate-cache,tmp}`を削除しない。`cleanall`と未承認`cleansstate`を実行しない。
- QEMU画面の判定はQMP framebufferのPPMだけを使い、各run後にQMP `quit`と残留process確認を行う。
- native成功の条件は2D overlayやFPSではなく、対象regionの実3D pixelと順序付きnative/Wayland evidenceである。
- pushはせず、作業区切りごとにfeature branchへlocal commitする。

---

### Task 1: native-only diagnostic variantをDevtoolから生成する

**Files:**
- Modify via Devtool source: `packages/filament_scene/example/lib/main.dart`
- Create in project layer: `layers/meta-fluorite-trial/recipes-graphics/flutter-apps/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo/0025-filament_scene-diagnostic-native-only-devtool.patch`
- Modify: `layers/meta-fluorite-trial/recipes-graphics/flutter-apps/toyota-connected-tcna-packages-filament-scene-fluorite-examples-demo_git.bb`
- Record: `work/logs/2026-08-31-flr0026.md`, `work/evidence/FLR-0026-diagnostic-mock-2026-08-31.md`

**Interfaces:**
- Consumes: Devtool source commits through `858e575`, active patches `0022`–`0024`.
- Produces: a generated patch changing only `kFlr0026DiagnosticMock3d` from `true` to `false`, applied after `0024`.

- [ ] Copy the Devtool-managed `main.dart` to one Mac staging file, apply the one-line change with `apply_patch`, copy it back, and verify `git diff --check` in the Devtool source.
- [ ] Commit only that source change in the Devtool local Git with message `diag: run native Filament path without Flutter mock`.
- [ ] Run `devtool finish <recipe> <project-layer-destination> --mode patch`; preserve the generated patch unchanged even if the known read-only `config.toml` cleanup warning occurs.
- [ ] Register the generated patch after `0024` in the app recipe, record source commit and patch SHA256, and commit the layer change.

**Verification:** The recipe source order shows `0022`, `0023`, `0024`, `0025`; the patch applies in a forced app `do_patch`; no Flutter mock label is compiled into the native-only test.

### Task 2: native-only artifactを固定mini PC経路でbuildする

**Files:**
- Modify only Git bundle/remote receiver state; do not edit mini-PC source.
- Record: `work/logs/2026-08-31-flr0026.md`, `work/evidence/FLR-0026-native-only-*.md`

**Interfaces:**
- Consumes: Task 1 feature commit, fixed receiver `/mnt/yocto/flourite-receivers/flr0023-835a04e`, fixed build directory and fixed TMPDIR.
- Produces: exact receiver revision and rootfs/kernel/qemuboot hashes.

- [ ] Run `scripts/assert-canonical-repository.sh`, `git diff --check`, privacy preflight, and create a complete-history Git bundle from the current feature tip.
- [ ] Verify and transfer the bundle to the existing receiver inbox; verify the remote SHA256 and checkout revision.
- [ ] Run `bitbake -e agl-ivi-image-flutter`, app `do_patch`, app `do_compile`, then full `bitbake agl-ivi-image-flutter` in that fixed build directory.
- [ ] Stop at the first failed task and record it; proceed to artifact transfer only if all tasks succeed.
- [ ] Transfer only the timestamped rootfs needed for QEMU and verify its SHA256 against the mini-PC output.

**Verification:** All build stages succeed, no new TMPDIR/receiver/container appears, and artifact identity is recorded before QEMU startup.

### Task 3: native fixtureのfirst-divergence loopを実行する

**Files:**
- Create outside Git: QMP PPMs and serial logs under the existing QEMU evidence root.
- Record: `work/evidence/FLR-0026-native-only-*.md`, `work/logs/2026-08-31-flr0026.md`

**Interfaces:**
- Consumes: Task 2 image identity and fixed QEMU profile.
- Produces: ordered native markers, process-lifetime result, QMP full/candidate pixel statistics.

- [ ] Start exactly one QEMU instance with a unique run directory, fixed 720x400 QMP endpoint, registered Wayland user, and the transferred rootfs.
- [ ] Launch the installed Example Demo as `agl-driver`; capture at boot, startup, and stable 10-second intervals.
- [ ] Extract and order `FLR0026_SHAPE_READY`, `FLR0026_CAMERA_APPLIED`, `FLR0026_FRAME_BEGIN`, `FLR0026_FRAME_END`, Vulkan swapchain/present, and Wayland markers.
- [ ] Compare at least two falsifiable paths: native frame starvation (`beginFrame=false`) versus surface composition (frame succeeds but candidate pixels remain unchanged).
- [ ] Stop via QMP `quit`; verify no `qemu-system-x86_64` remains.

**Verification:** The earliest missing boundary is identified from fresh logs, not inferred from a black screenshot alone. If native frame markers never reach `endFrame`, do not proceed to route testing.

### Task 4: one native/Wayland countermeasure at a time

**Files:**
- Modify only through the native Devtool source workspace when source instrumentation or fix is required.
- Create generated patch under `layers/meta-fluorite-trial/recipes-graphics/toyota/files/00NN-*.patch`.
- Modify `layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend` only to register the unchanged generated patch.

**Interfaces:**
- Consumes: Task 3 first-divergence evidence.
- Produces: one attributed native or Wayland variant per commit.

- [ ] Select one probe based on the first divergence: frame scheduling, opaque swapchain/clear, explicit child commit/flush, or geometry/z-order; state its prediction before editing.
- [ ] Generate the source patch with Devtool, bundle/build through the fixed path, and rerun the same QMP acceptance loop.
- [ ] Keep native render success, surface commit, and visible pixels as separate verdicts; revert only by a new source-derived variant or recipe registration change, never by editing generated patch text.
- [ ] Record build-time, runtime, packaging, and integration impact for each variant.

**Verification:** A countermeasure is accepted only if its predicted boundary and QMP pixel result change; otherwise keep the patch as diagnostic history and test the next ranked hypothesis.

### Task 5: production scene and QEMU input matrix

**Files:**
- Record: `work/evidence/FLR-0026-scene-matrix-*.md`, `work/logs/2026-08-31-flr0026.md`
- Modify source only through Devtool if a diagnostic direct-route selector is needed.

**Interfaces:**
- Consumes: a native fixture run with stable frame/present and visible candidate pixels.
- Produces: button/direct route matrix for initial, Playground, Radar, Settings, Planetarium, and Trainset.

- [ ] Use QEMU input through the existing serial/QMP-compatible route to activate the Scenes control, recording the exact stimulus and resulting route.
- [ ] Hold each route for 10 seconds and collect process survival, native marker sequence, 2D overlay, and 3D-region pixel hash.
- [ ] Compare button route with any diagnostic direct route using the same image/profile; treat route-specific failures independently.
- [ ] Require Planetarium to show a changed 3D-region pixel bounding box before considering production-scene success.

**Verification:** Initial display and every tested route have attributable identity and evidence; the Flutter-only mock is never counted as a production native result.

### Task 6: completion audit and local milestone commit

**Files:**
- Modify: `work/tickets/FLR-0026-fluorite-3d-display.md`
- Modify: `TASKS.md`, `work/logs/2026-08-31-flr0026.md`, relevant evidence files

**Interfaces:**
- Consumes: Task 3–5 fresh target evidence and all artifact provenance.
- Produces: explicit PASS/FAIL/UNKNOWN matrix and clean local feature branch.

- [ ] Run `make verify`, shell checks, Markdown link checks, `git diff --check`, and privacy checks against the recorded baseline.
- [ ] Update ticket success criteria only where evidence proves the exact condition; retain UNKNOWN for native or route gaps.
- [ ] Commit the milestone locally and verify the worktree is clean. Do not push or create a PR.

**Verification:** Mark the ticket complete only when native fixture and required production-scene pixel criteria are all proven; otherwise leave FLR-0026 In Progress with the next falsifiable boundary.

## Evidence gaps identified at plan creation

- Flutter-only QMP display is proven, but native Filament visible pixels are not.
- The current native Devtool source has imported historical changes plus a rejected frame-marker hunk; this must be resolved before generating a new native patch.
- Planetarium and button/direct route input evidence is absent for the current artifact.

## Continuation checkpoint — 2026-09-01

- The fixed Mac Devtool source workspace was reused. The active software-frame
  path was verified from the Mini PC effective source: it calls `DrawFrame()`
  from the `callback == nullptr` loop.
- A source-only Devtool commit (`2dc4927`) added `attachShmProbe()` at the
  common `DrawFrame()` boundary. The generated patch is registered in
  `meta-fluorite-trial` as `0068`; its patch body was not edited.
- The same bundle receiver, build directory, TMPDIR, and QEMU artifact area
  were reused. Forced install/package/rootfs/image tasks were required after
  compile so the rootfs contained the rebuilt flutter-auto package.
- Fresh QMP-only evidence proves the SHM known-color buffer is visible. The
  current native 3D criterion is still not met: attaching that diagnostic
  buffer to the existing surface masks the parent and is not native Filament
  content.
- Next falsifiable step: create an independent small child-surface probe or
  instrument the Vulkan present/buffer identity, then rerun the same QMP loop
  before accepting any production-scene or Planetarium route.

## Continuation checkpoint — 2026-09-02

- Corrected the QEMU launch contract in the workflow: use the installed
  Example Demo BUNDLE as `agl-driver`, allow its `app_id=fluorite`, and do not
  pass the long package name as `--xdg-shell-app-id`.
- Reconfirmed 2D/CPU/FPS output through QMP with the latest native-only image.
  The candidate region remains black, so this is a 2D PASS and native 3D
  FAIL/not-proven, not a general startup failure.
- Opened Scenes by QMP pointer input, captured all five scene names, selected
  Planetarium, held it for eight seconds, and captured a QMP-only frame. The
  route action completed, but its candidate region remained `0/100000`.
- QEMU was stopped through QMP `quit`; no socket or process remained. The next
  falsifiable implementation step is native Vulkan attach/present completion
  instrumentation or repair, followed by the same fixed bundle/build/QMP loop.

## Continuation checkpoint — 2026-09-03

- Added the Devtool-generated `0094` diagnostic patch to dispatch pending
  Wayland events before `beginFrame()`. The fixed bundle workflow reused the
  same receiver, build directory, TMPDIR, and Devtool container; all build
  gates passed and the rootfs hash matched locally and on the Mini PC.
- Fresh QMP-only evidence again proves the 2D HUD, CPU/GPU/FPS metrics, graph,
  Scenes button, and lower controls. The native candidate region changed only
  `213/100000` pixels with bounding box `[200,113,29,66]`; it remains black as
  native 3D evidence.
- Guest logs show pending dispatch succeeded, but only frame 1/2 had
  `started=true`; later frames returned `started=false`. The process later
  crashed in llvmpipe/libLLVM. QMP cleanup was complete.
- A Scenes pointer stimulus was accepted by QMP, but the post-input frame was
  all black and contains no route-specific native marker. Planetarium remains
  unproven and the route matrix stays pending.
- Next falsifiable step: observe Vulkan present/Wayland buffer identity or
  build an offscreen Filament fixture copied into the proven SHM surface. Do
  not repeat the full route matrix until a native pixel is proven.

## Continuation checkpoint — 2026-09-03 (present diagnostic)

- The roundtrip diagnostic (`0095`) was built and run through the same fixed
  Mac Devtool → generated patch → bundle → Mini PC receiver/build/TMPDIR →
  QMP-only loop. Roundtrip responses were received, but native frame
  continuity and native pixels remained unproven.
- The Filament Devtool source then generated `0104` to log commit,
  swapchain-present, and `vkQueuePresentKHR`. The same fixed build produced
  a matching rootfs; runtime repeatedly logged `vkQueuePresentKHR result=0`
  and later completed frames.
- The mandatory QMP-only capture still had `0/100000` changed pixels in the
  native candidate region. This changes the first-divergence hypothesis from
  “present is never called” to “presented image content or Wayland compositor
  handoff is not visible.”
- QEMU cleanup passed. The next implementation boundary is a minimal
  offscreen Filament fixture copied into the proven SHM surface, or direct
  Wayland attach/commit plus buffer-identity tracing. Production scene and
  Planetarium testing remain blocked by the native-pixel success criterion.

## Continuation checkpoint — 2026-09-03 (visible mock control)

- Devtool source commit `83a703b` generated patch `0105`; the project commit
  `7418490` was bundled to the same Mini PC receiver and built with the same
  build directory and TMPDIR.
- An opt-in, self-made perspective cube was rasterized into the independent
  SHM child surface. QMP-only evidence changed `38609/100000` pixels in the
  candidate region with bbox `[200,113,280,167]`; the cube is visibly present
  beside the 2D HUD and CPU/GPU/FPS metrics.
- This proves the visible child-surface/Wayland SHM composition path and
  rules out crop/z-order/compositor impossibility as the sole explanation.
  It does not prove Filament native 3D; the native success criteria remain
  unchecked.
- Stale old ticket-specific Mini PC receiver/build/TMPDIR paths were removed
  only after confirming no active BitBake/QEMU process. The fixed current
  paths and shared caches were retained.
- Next implementation boundary: instrument the Filament readback callback and
  copy real Filament pixels into the proven SHM buffer. Then rerun the native
  candidate gate and only after that repeat the Planetarium route matrix.

## Continuation checkpoint — 2026-09-03 (readback fence wait)

- Devtool source commit `f25fd1b` generated `0116-native-readback-fence-wait-devtool.patch`;
  project commit `4e7634f` registered the unchanged generated patch and updated
  the baseline lock from 146 to 147 layer files.
- The existing bundle, receiver, build directory, TMPDIR, Devtool container,
  and QEMU run directory were reused. All app/image tasks through
  `do_image_complete` succeeded. Mini PC and local rootfs matched at
  `08e9e32d4b79119453891c8caf3e1691ea162ef64ef72cc5ae27d33d62fc4e07`.
- Native readback reached target creation, view render, queue, and Fence
  creation. The bounded 50-ms wait did not produce a readback callback; later
  frames returned `started=false` and the native candidate stayed black.
- QMP-only evidence is
  `$QEMU_ARTIFACT_ROOT/run-native-0058-20260901-0025/native-readback-fence-0116-qmp.ppm`
  with SHA-256
  `6db14bc341f5c617f5949a587545d6ada235a30defaa8efc0f653c4b21815584`.
  The candidate region `[200,100,400,250]` changed `254/100000` pixels with
  bbox `[200,113,29,66]`; visual inspection identifies only 2D metrics text.
- QMP cleanup passed. The separate known-color control still showed the 2D HUD
  and self-made perspective cube, but remains a display-path control rather
  than native Filament evidence.

### Next falsifiable boundary

Keep FLR-0026 In Progress. Do not repeat Planetarium acceptance until a
production native pixel is proven. The next source-only Devtool iteration must
observe the native present/Wayland buffer identity or create a visible
Filament geometry path independent of the current asynchronous readback
callback.

## Continuation checkpoint — 2026-09-03 (native rotated-Cube gate)

- The persistent Devtool source produced commit
  `ccbce761513ad8915b19df45a38c7817860960fd`, which rotates the self-made
  Cube by `(25, 35, 0)` degrees. The generated patch is registered as
  `0032-filament_scene-rotate-emissive-blue-native-fixture-devtool.patch`.
- Project commit `c0bf22c9b4a8a11adc3540fa4a5cf72507db6002` was delivered via
  the same bundle, receiver, build directory, TMPDIR, and persistent
  Devtool container. All app/image tasks through `do_image_complete` passed.
- QMP-only evidence shows the green native surface and three visible Cube
  faces at `(536,298)-(754,493)`, with PPM SHA-256
  `9d125f8e7aae93a6b867069f388b55ab6918434a71b2af54cc36432562d4c31a`.
  The SHM mock switch was absent.
- Native self-made 3D display is now PASS. Production full-scene and
  Planetarium/input acceptance remain pending and must be tested after the
  fixture is restored to the production scene.

## Runtime-first checkpoint — 2026-09-03

- Before another source change, the current 0125 runtime was rechecked with
  Wayland pending-event dispatch. It still reached queue submission and
  stopped at Vulkan present; the candidate region was zero.
- Compared hypotheses: present wait semaphore, Wayland WSI buffer-release or
  shared-display handling, and camera/geometry. The last is lower priority
  because the renderable marker and historical native Cube proof are present.
- Devtool Filament commit f4f4d212 generated patch 0126, an opt-in
  FLR0026_PRESENT_NO_WAIT diagnostic. The fixed Mini PC build passed all
  required gates, but runtime remained blocked before the present result and
  later hit the known LLVM crash. This hypothesis is rejected as a sole fix.
- The same current image produced a QMP-only SHM control frame with the
  self-made three-face Cube and 2D CPU metrics. This is a display-path PASS,
  not native Filament evidence.
- A fullscreen/zoom display A/B did not produce native green/Cube, so
  display size alone is not sufficient.
- Keep the ticket In Progress. The next source experiment must target the
  Wayland WSI buffer-release/shared-display boundary and repeat the runtime
  marker plus QMP-only screenshot procedure.

## Runtime-first checkpoint — corrected unset A/B

- The invalid `FLR0026_NATIVE_CLEAR_PROBE=0` attempt was excluded because
  presence enables the probe.
- A PTY-held rerun with the variable truly unset reached the same
  renderable/queue-submit/present boundary and produced zero native candidate
  pixels. This rejects the pre-present commit as the sole cause.
- QMP cleanup passed. Continue with Wayland WSI buffer-release/shared-display
  instrumentation before a new behavioral patch.

## Runtime-first checkpoint — scene-content skip A/B (2026-09-05)

- QEMU 0197 reused the 0186 rootfs and enabled `FLR0026_NATIVE_SKIP_SCENE_CONTENT` plus the existing
  forced-frame diagnostic. The production sequoia asset reached asset creation, async completion,
  secondary scene insertion, queue submit, queue present, present-boundary completion, and Wayland
  commit repeatedly for about 2300 frames.
- Removing only the scene content made the present path stable while the same GLB preparation and scene
  insertion remained enabled. The QMP-only frame is intentionally black in the native candidate region
  (`0/100000`), so it is not 3D success.
- The current failure boundary is most consistent with `renderer->render(fview_)` consuming production
  renderables/materials/textures/pipelines or the corresponding llvmpipe LLVM command path. Flutter/AOT,
  2D overlay, Wayland surface, Vulkan swapchain/acquire, CPU GLB load, and scene insertion are not the
  leading causes. The first failing renderable/resource remains UNKNOWN.
- Do not create a production patch from this A/B. The next falsifiable experiment is a staged render set
  using a self-made simple geometry or a small GLB through the production `ModelSystem` scene path,
  followed by the fixed bundle/build/QMP-only loop if source changes are required.

## Runtime-first checkpoint — shape/light A/B (2026-09-05)

- QEMU 0198 reused the 0186 rootfs with production models, skybox, and indirect light disabled while
  retaining 37 shapes and 13 lights. All observed shapes reported `renderable=true`.
- The same fence starvation and delayed `FEngine::loop` → `libLLVM.so.18.1` segmentation fault reproduced,
  while QEMU 0197 remained stable only when scene content itself was skipped.
- This lowers the hypotheses for a single GLB, skybox, or indirect light as the sole cause. The next
  falsifiable boundary is shape-only versus light-only content. No production patch should be created
  until that distinction is observed.

## Runtime-first checkpoint — self-made cube recheck (2026-09-05)

- QEMU 0199 re-ran the self-made native cube using the existing 0186 rootfs. The QMP-only late frame
  changed `15212/100000` pixels in the candidate region, with bounding box `[291,139,138,122]`, matching
  the known successful cube hash.
- Queue present and present-boundary completion continued while flutter-auto remained alive. This confirms
  that the current QEMU/Vulkan/Wayland capture path can still display native 3D pixels.
- The fixture mode also emitted repeated `Light not found` handler errors because production lights are not
  created in pure-fixture mode. This is recorded separately and is not counted as a production-scene result.
- Production full-scene and route acceptance remain incomplete. Once Docker/Devtool responds, add only
  shape-only/light-only diagnostic switches through the Devtool source workflow and repeat the fixed
  bundle/build/QMP-only loop.
