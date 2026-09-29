# FLR-0050 — Flutter parent alpha and frame-loop boundary

- Status: Waiting
- Priority: High
- Owner: runtime diagnosis + Flutter embedder + target-validation roles
- Created: 2026-09-08
- Updated: 2026-09-09
- Work unit: Flutter親swapchainのalpha実値と、native 3Dを隠す合成境界およびフレーム更新停止を独立に判定する
- Depends on: [FLR-0049](FLR-0049-production-model-render-boundary.md)
- Working log: `work/logs/2026-09-08-flr0050.md`
- Unblocked after: [FLR-0052 — canonical repository reproducibility gate](FLR-0052-canonical-repository-reproducibility.md)
- Runtime prerequisite: [FLR-0056](FLR-0056-runtime-preflight-false-cleanup.md) corrected residual detection; use working guest SSH, not the unresolved serial late-attach path.

## Problem

FLR-0049で、production Sequoiaのscene追加とnative 3D画素はQMPで確認できた。
しかし、Flutter HUDを含む2D親とnative 3D childを同時に正しく見せることは未達で、
さらにフレーム開始が`started=false`へ遷移する境界も残っている。親alphaと
frame-loopを同じ原因と仮定せず、最初の発散点を分離する。

## Stratification — 4W1H excluding Why

| Dimension | Observation | Evidence |
| --- | --- | --- |
| What | Flutter親のalpha値、native childの上下関係、frame開始状態 | FLR-0049 Iteration 22/23 |
| Where | Mac Devtool由来のflutter-auto Wayland Vulkan embedderとQEMU runtime | fixed container source / QMP |
| When | Flutter初期描画、native scene-add後、継続frame開始時 | runtime markers |
| Who | Flutter embedder、Wayland compositor、Filament/native runtime、validation role | source/log ownership |
| How | Devtool source change → layer patch → bundle → Mini PC BitBake → QMP-only capture | project runbook |

## Success criteria

- 既存のDevtool container、build directory、TMPDIR、QEMUを再利用する。
- Mac側のDevtool source workspaceでのみ診断ソースを編集し、Yoctoの`devtool finish`
  で生成した未変更patchを`meta-fluorite-trial`へ登録する。
- Flutter親swapchainの実画素について、alphaまたはalpha相当の決定的な観測結果を
  runtime logへ記録する。測れない場合はUNKNOWNとして理由を残す。
- `FRAME_BEGIN started=true/false`と、Vulkan submit/present、QMP画面を同一runで対応付ける。
- 成功・失敗・ビルドエラー・接続ミスを同一run directoryに保存し、SHA-256を記録する。
- QEMUは1台だけ起動し、QMP-only画像または動画を保存して、終了後に残存プロセスとsocketがないことを確認する。
- このticketではroute transitionと製品恒久修正を完了扱いにしない。合成結果の検証は別ticketへ分割する。

## Hypotheses

1. Flutter 2D親swapchainの黒いcontent領域が不透明で、below-parent native childを覆っている。
2. 親alphaは透明でも、`started=false`によりnative childまたはFlutter親の更新が止まり、見える組合せになっていない。
3. Wayland stacking/opaque-regionまたはsurface ownerが親alphaとは別に合成を決めている。

## Plan

1. 既存source、recipe、build identity、FLR-0049 evidenceを再確認する。
2. Flutter Vulkan `PresentCallback`とWayland parent surfaceの実装を静的に確認する。
3. 親swapchain画像を直接観測する最小診断候補を比較し、1つだけ選ぶ。
4. Devtool source commit → `devtool finish` → layer登録 → local commit → bundle → Mini PC buildの順に進める。
5. QMP-onlyでparent alpha probe、frame-loop marker、native model-only controlを比較する。

## Visual evidence

- Baseline / control: `work/latest-mac/flr0049-ccb81ec/model-only-20260908/qmp-final.png`
- Baseline video: `work/latest-mac/flr0049-ccb81ec/model-only-20260908/qmp-model-only.mp4`
- Fresh baseline result: 2D HUD/metrics PASS. Production Sequoia-only 3D also
  PASS on the exact ad8e1cd image using the historical diagnostic controls;
  its QMP PPM hash matches the FLR-0049 successful frame. Combined 2D+3D and
  parent-alpha A/B remain UNKNOWN (working log Iteration 7).
- Evidence files stay outside Git; ticket records role-based paths and hashes.

## PDCA

### Do

- Record all commands and results in `work/logs/2026-09-08-flr0050.md`.
- Do not hand-edit generated patches or create a second container/TMPDIR.

### Check

| Criterion | Expected | Actual | Evidence | Result |
| --- | --- | --- | --- | --- |
| Parent alpha | Direct observation or explicit UNKNOWN | Corrected positive control established; stacking/clear A/B next | Iteration 7 | UNKNOWN |
| Frame loop | Correlate begin/render/present/pixels | Forced-render control produces vehicle pixels despite started=false; stable pacing unproven | Iteration 7 | UNKNOWN |
| Combined 2D+3D | Both HUD and production vehicle visible | Not yet tested in this ticket | follow-up ticket | PENDING |

### Act

- Continue with official runqemu on the same image and one guest. Do not block
  runtime diagnosis on optional serial or custom capture integration work.
- If a new composition or route boundary is found, create another Markdown ticket before changing scope.

## Unknowns

- Flutter parent swapchain alpha at the compositor boundary.
- Whether frame-start failure is caused by fence handoff, event-loop pacing, or a separate runtime condition.
- Whether a parent-alpha fix is sufficient for simultaneous HUD and production 3D.

## PDCA checker

- Status: UNKNOWN
- Checked by: runtime validation role
- Findings: Current-image 2D and isolated production 3D controls proven;
  combined composition and parent-alpha boundary remain under investigation.

## Iteration 8 — clear skipped default Skybox

### Facts

- The native source is the nested `ivi-homescreen-plugins` component. Its
  reviewed Devtool source commit is `5351c15`; the baseline used for the
  component-scoped registration is `8c362d1`.
- Official component-scoped Devtool generation produced
  `0204-diag-clear-skipped-default-skybox-devtool.patch`; generated and
  registered SHA-256 is
  `c62db940dd2434772368d38d2393e0166c78830be460dddb592112bc94c89466`.
- The previous parent-alpha patch removed by an incorrect direct finish was
  restored from the last canonical Git revision and remains registered.

### Decision

Use the 0204 diagnostic as the next single runtime variable. It calls the
existing transparent-skybox API only when both the existing skip control and
the new opt-in flag are present. Do not interpret this diagnostic as a
production fix until a QMP frame shows both the HUD and vehicle.

### UNKNOWN

Whether the remaining Skybox renderable is the full-screen opaque layer, and
whether removing it is sufficient for combined Flutter/native composition,
remain UNKNOWN pending the Mini PC build and QMP evidence.

## Iteration 9 — refresh 0204 against the effective baseline (2026-09-09)

### Facts

- The Mini PC recipe gate rejected 0204 with `patch-fuzz`: its hunk applied at
  offset 2 with fuzz 1, and `do_qa_patch` stopped the task. The failure is
  recorded under `$BUILD_TMPDIR/work/corei7-64-agl-linux/flutter-auto/2.0/temp/`.
- The quilt backup immediately before 0204 contains the earlier
  `skip_lights`/`skip_shapes` changes from the recipe patch series. The original
  Devtool component baseline did not contain those lines, so the generated
  patch context was incomplete even though the source change itself was correct.
- The same Mac Devtool container was reused. Its source now has baseline commit
  `ccbcc3c4f5afbcacdd0970444b9837c7a088aea5` followed by source commit
  `49332e7e21c6738c242e509de8e1fd37ad63dccd` containing only the 0204 change.
- Official `devtool update-recipe --mode patch --append --no-remove
  --force-patch-refresh --initial-rev <baseline>` generated the replacement
  patch. The layer copy is byte-for-byte unchanged from Devtool output and has
  SHA-256 `483cf9045eba1cfe20074e47e682b0b7de2e98d2174f3dac2ba6e87580e0117e`.
- The Mac wrappers now expose component reset/add/update operations with path
  validation and the same fixed operation lock. No second container or TMPDIR
  was created.

### Inferences

The previous QA failure was caused by a Devtool baseline/context mismatch, not
by the 0204 source logic. The replacement patch should apply with fuzz 0 after
the earlier layer patches.

### Check / UNKNOWN

- Replacement patch application, compile, full image, combined QMP pixels, and
  runtime marker `FLR0026_NATIVE_CLEAR_SKYBOX_ON_SKIP` are UNKNOWN until the
  new layer commit is delivered and rebuilt on the Mini PC.
- The old generated patch in the Devtool `attic` is not evidence for the new
  result; only the `workspace/appends` output was accepted.

### Act / Next action

Update the layer baseline lock, run `make verify`, commit the layer and wrapper
change locally, then send that exact tip with the existing bundle helper. Run
`flutter-auto:do_patch` first and require a fuzz-free pass before compile or
full-image build. Do not start QEMU until the full image gate passes.

## Iteration 10 — compile API visibility correction (2026-09-09)

### Facts

- The first fuzz-free `do_patch` was followed by `do_compile` failure because
  `SkyboxSystem::setTransparentSkybox()` is private in the existing header.
  The compiler log is the `flutter-auto:do_compile` task log under
  `$BUILD_TMPDIR/work/corei7-64-agl-linux/flutter-auto/2.0/temp/`.
- Two source-level options were compared: making the private method public, or
  calling the existing public `setDefaultSkybox()` method. The latter already
  delegates to the same transparent-skybox operation and keeps the API surface
  unchanged, so it was selected.
- A clean Devtool source branch was created from baseline `ccbcc3c` and contains
  one final source commit `06f421991d58d7387329060e704238637a65ad3b` with the
  diagnostic change using the public API. The intermediate private-API commit
  is not part of the final generated patch series.
- Stale generated Devtool attic metadata was removed after preserving the
  source commits. The source was re-registered at the baseline, then the final
  commit was checked out and exported by official `devtool update-recipe`.
- The final generated patch is one file, copied unchanged to the layer, with
  SHA-256 `e43b6b50a64f375b964f681051773999a578751ff3c30d68e81636d5d2da3722`.

### Inferences

The compile failure was an API visibility mismatch in the diagnostic call, not
a missing dependency or a failure of the transparent-skybox implementation.
The final patch should compile without changing the public header.

### Check / UNKNOWN

- Final source history, generated patch identity, and layer registration are
  PASS.
- Final `do_patch`, `do_compile`, full image, combined QMP pixels, and runtime
  effect remain UNKNOWN until this revision is committed, bundled, and built.

### Act / Next action

Update the baseline lock and append this failed compile plus correction to the
working log, run `make verify`, commit locally, refresh the single bundle, and
rerun `do_patch` then `do_compile`. Proceed to full image only after both pass.

## Iteration 11 — final patch compile gate passed (2026-09-09)

### Facts

- Commit `d68fe6d4f509b4c0a30b03e396361dd7657cd9b9` was delivered through the existing single
  bundle. Bundle SHA-256: `14d221a251a0d649feda48440f82a49d3542798a0e2782aa756ee3dd60ee4863`.
- The fixed Mini PC build directory and TMPDIR were reused; no additional container, TMPDIR, or
  QEMU was started.
- The latest `flutter-auto:do_patch` task log reached `do_qa_patch finished` without the prior
  0204 fuzz/offset failure. Existing `Upstream-Status` warnings remain as non-blocking QA notes.
- The latest `flutter-auto:do_compile` task log completed the `shell/flutter-auto` link and ended
  with `DEBUG: Shell function do_compile finished`. The public-API version of 0204 passes the
  compile gate.

### Inferences

The effective-source baseline correction removed the patch-context defect, and switching the
diagnostic call to the existing public API removed the compile visibility defect. These are two
separate failure modes and both are now evidenced as resolved.

### Check / UNKNOWN

- PASS: canonical repository, official Devtool patch generation, layer registration, bundle
  delivery, fuzz-free do_patch, and do_compile.
- UNKNOWN: full image, runtime marker, QMP combined HUD+vehicle frame, and route/input transition.

### Next action

Run the full image build in the same Mini PC build directory/TMPDIR. Only after that succeeds,
start one QEMU instance, enable the opt-in 0204 diagnostic flag, and retain QMP-only screenshots
and runtime logs as evidence.

## Iteration 12 — final image and combined QMP diagnostic boundary (2026-09-09)

### Facts

- Local commit `d88d600cf7c3d1cb429975efb58e65c2684fb5b0` passed `make verify`.
  The same single bundle reached the fixed receiver; bundle SHA-256 is
  `3cf87913e45c55659f0843da1c1ef487831eddc1358d41e9b97626a7739349ee`.
- The existing Mini PC build directory/TMPDIR produced the full image with
  11748 attempted tasks, 11728 not rerun, all succeeded, and 21 warnings. The
  rootfs, qemuboot, and kernel SHA-256 values are recorded in the working log.
- The bounded harness removed one pre-existing QEMU through negotiated QMP quit,
  then ran exactly one QEMU under evidence run id
  `flr0050-d88d600-20260909`.
- With transparent skipped-skybox clearing, forced frame rendering, Sequoia
  model limit 2, and shapes/lights/indirect light skipped, all 20 QMP frames
  had 3783 changed pixels in the candidate region and bbox `[336,96,544,304]`.
  The framebuffer visibly contains the 2D CPU/GPU/FPS HUD and diagnostic native
  3D wireframe/red-lamp content. PPM, runtime-log, and QMP-video hashes are
  recorded in the working log.
- Same-QEMU A/B results were: lights enabled/shapes skipped = 0 candidate
  pixels; shapes enabled/lights skipped = 4905 candidate pixels; both enabled =
  0 candidate pixels. Each condition has its own QMP PPM and runtime log.
- The app was stopped and the harness QMP teardown reported
  `capabilities=negotiated`, `quit=accepted`, `residual_targets=0`, and
  `residual_qmp=0`.

### Inferences

- The 0204 diagnostic crosses the parent-composition boundary for a stable
  20-frame combined framebuffer. This does not prove a numeric alpha value or a
  full production shaded-car result.
- Present/commit continues under forced rendering after `started=false`, while
  the enabled production lights make the candidate region black. The next
  smallest runtime boundary is the production light/resource/material path.

### Check / UNKNOWN

- PASS: full image, bundle/receiver, QMP-only combined capture, native markers,
  20-frame stability, A/B captures, and teardown.
- PASS WITH CONDITIONS: diagnostic wireframe/red-lamp result only; full shaded
  production 3D is not yet accepted.
- UNKNOWN: direct numeric alpha, current-image light threshold, full shaded car,
  and Radar/Planetarium route/input transition.

### Next action

Continue in [FLR-0057 — production lit 3D and route transition](FLR-0057-production-lit-3d-and-route.md).
Do not add lighting or route changes to this ticket.
