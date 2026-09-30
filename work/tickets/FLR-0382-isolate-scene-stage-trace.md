# FLR-0382 — isolate scene-stage tracing against the live gray baseline

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / strict guest SSH / `agl-driver` / Flutter runtime / QMP evidence roles
- Created: 2026-09-30
- Work unit: One manual, one-variable runtime comparison; no launcher or product-code changes
- Predecessors: [FLR-0378 no-light Sequoia silhouette](FLR-0378-replay-sequoia-no-light-on-current-candidate.md), [FLR-0381 live gray frame](FLR-0381-replay-no-light-without-wayland-debug.md)
- Branch: `feature-flr-0382-isolate-scene-stage-trace` (local, no push; fast-forwarded to the completed FLR-0381 evidence commit)
- Working log: [FLR-0382 working log](../logs/2026-09-30-flr0382.md)
- Candidate kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- Candidate rootfs SHA-256: `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`
- Candidate qemuboot SHA-256: `8582ac80d4c58fc9e852abed0e6fd6e6077bf6e5f0f7727341033fb405d0a17c`
- Run ID: `flr0382-0001`

## Purpose

Determine whether adding only `FLR0026_SCENE_STAGE_TRACE=1` to the exact
FLR-0381 manual no-light profile changes the live QMP pixels or present/process
sequence. FLR-0378 used this trace and showed an achromatic Sequoia silhouette;
FLR-0381 did not set it and showed a live uniform-gray frame. This is a
diagnostic comparison, not production acceptance and not a new texture, light,
camera, compositor, or general 3D investigation.

## Facts

- FLR-0378 manually launched Example Demo 3.32.5 on this candidate with the
  no-light Sequoia profile and `FLR0026_SCENE_STAGE_TRACE=1`; QMP showed a black
  Sequoia silhouette on gray, with zero car chroma and no HUD. Its raw log
  contained 143,284 repeated asset-ready records and was lost with the guest
  session before transfer; only its size, hash, and summary counts remain.
- FLR-0381 used the same pinned candidate and no-light profile without
  `WAYLAND_DEBUG` or scene-stage trace. One capture passed the live-process
  gate and showed uniform gray across the full frame and all eight video frames;
  neither vehicle nor HUD pixels were present. See its QMP evidence manifest.
- FLR-0382 run `flr0382-0001` manually used the same profile with only
  `FLR0026_SCENE_STAGE_TRACE=1` added and `WAYLAND_DEBUG` absent. The guest
  launcher recorded timeout status `124`; the outer SSH invocation also ended
  with `124`. Its bounded runtime log is 3,065,644 bytes / 27,832 lines, with
  13,409 `ASSET_READY` records, two `QUEUE_PRESENT_RETURN result=0` records,
  then a third present-enter without a recorded return. The QMP still and all
  eight video frames were captured after the app timeout; they are black and
  hash-identical to the pre-Flutter frame
  (`d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`).
  This is not a live-render observation and does not decide whether trace
  changes the rendered scene.
- The owned QEMU was quit through QMP; both recorded PIDs, the QMP socket, and
  forwarded ports were absent in the independent post-teardown check.
- The registered diagnostic patch `0279-diag-trace-current-production-scene-stages-devtool.patch`
  gates additional `spdlog::info` records on this environment variable. It
  logs draw boundaries and scene/model state; `ASSET_READY` is emitted from
  the repeated asset-loading update. Static diff shows no intended render-state
  mutation, so any pixel change would indicate timing/logging correlation,
  not a direct geometry fix.
- The observed difference is not enough to establish that tracing changes
  graphics behavior; logging overhead, run variation, and missing raw FLR-0378
  output remain possible factors.
- Sequoia's embedded GLB textures and material references were already
  verified complete in FLR-0375. Do not repeat that static inventory here.

## Stratification — 4W1H excluding Why

| Dimension | Evidence | This run |
| --- | --- | --- |
| What | FLR-0378 silhouette; FLR-0381 live uniform gray | Whether adding only the stage trace changes QMP pixels or runtime sequence |
| Where | Exact pinned Mini candidate; installed Example Demo 3.32.5 | Same image, bundle, Wayland session, and no-light Sequoia path |
| When | Capture at first returned present while app is alive; bounded at 45 seconds | One QMP still plus eight-frame video, with liveness checked around capture |
| Who | Guest app as `agl-driver`; compositor and QEMU roles | One manually launched `/usr/bin/flutter-auto` process |
| How | Existing Mini `runqemu` path, strict guest SSH, QMP, bounded marker analysis | Add only `FLR0026_SCENE_STAGE_TRACE=1`; no other profile or script change |

## Hypotheses

1. **Trace-enabled execution correlates with the historical silhouette.**
   Prediction: the live QMP vehicle ROI regains achromatic edges matching the
   FLR-0378 silhouette; HUD and chroma are scored independently.
2. **The scene-stage trace is observational only.** Prediction: the live QMP
   frame remains uniform gray while stage markers appear, with no material
   change to the present sequence.
3. **High-volume trace output changes timing or causes an incomplete capture.**
   Prediction: present/process evidence stalls or the liveness gate fails; that
   is UNKNOWN for visual causality, not a successful or failed lighting test.

## Scope and success criteria

- Reuse the exact candidate, existing Mini QEMU/runtime harness, bundle, and
  evidence roles. Use unique run directories (`flr0382-0001` was the first
  attempt; the planned retry uses `flr0382-0002`); do not create a second
  build/TMPDIR or copy a disk image to Mac.
- Before launch, check canonical branch, one active ticket, no residual QEMU,
  QMP socket/ports, guest session/bundle, helper identity, candidate hashes,
  and available Mini storage. Fail closed before Flutter if any check fails.
- Manually launch `/usr/bin/flutter-auto` as `agl-driver` with the exact
  FLR-0381 no-light variables. Add only `FLR0026_SCENE_STAGE_TRACE=1`; keep
  `WAYLAND_DEBUG` absent. Do not enable camera, texture, material, route,
  force-render, light, or frame-event overrides.
- Preserve raw logs and PPMs on Mini in the persistent run evidence directory
  while the guest session is alive; do not copy high-volume logs to Mac.
  Bound log growth at 256 MiB and the app run at 45 seconds. Capture the QMP
  full frame and eight-frame video while Flutter is confirmed alive. Transfer
  only those QMP-derived PNG/MP4 review artifacts.
- Score the full 1280×800 frame, vehicle ROI `(0,100,320,310)`, and HUD ROI
  `(960,0,320,120)` for edges/chroma and compare to FLR-0378/0381 evidence.
  Record scene-stage/present event counts and exact app/timeout/SSH statuses;
  collect a bounded Oops/core summary before teardown.
- QMP-quit only the owned QEMU and stop only the verified app. Independently
  verify no residual processes, socket, or forwarded ports.
- Diagnostic completion means valid manual run, live QMP still/video, bounded
  runtime evidence, and exact teardown. It does not mean the 3D goal succeeded.
- No source, patch, Devtool, BitBake, image, or persistent script changes.

## Impact

- **Build-time / packaging:** none.
- **Runtime:** one bounded manual app run on the unchanged image.
- **Log/storage:** scene-stage trace previously produced about 127 MB of raw
  output; keep it on Mini and enforce the run-directory size bound.
- **Integration risk:** none from software mutation. A silhouette recurrence
  is correlation only and still does not establish 2D+3D acceptance.

## Plan / Do / Check / Act

### Plan

1. Verify the canonical repo, sole active ticket/checkpoint, exact image and
   helpers, available Mini storage, and zero residual QEMU/app state.
2. Reuse the proven Mini runqemu path; manually invoke Flutter with the
   FLR-0381 profile, adding only the stage-trace variable.
3. Persist the bounded raw log on Mini while the session is alive; capture
   full QMP still/video with process liveness checked before/after; score
   vehicle/HUD/full-frame pixels separately.
4. Save only QMP review media to this repo, classify evidence and unknowns,
   QMP-quit the owned VM, and verify teardown.

### Do

- Reused the existing Mini QEMU/runtime harness and exact candidate hashes;
  started one QEMU and manually launched `/usr/bin/flutter-auto` as
  `agl-driver` with the FLR-0381 no-light profile plus only
  `FLR0026_SCENE_STAGE_TRACE=1`. No source, build, patch, or persistent script
  changed.
- The direct guest launch was bounded at 45 seconds. The app status file and
  outer SSH invocation both reported `124`; raw runtime log and PPMs remain on
  Mini. Selected log summary: 13,409 `ASSET_READY`, two present returns with
  result `0`, then a present-enter with no captured return.
- Captured one post-timeout QMP still and eight post-timeout QMP frames before
  teardown. Converted only those QMP artifacts to workspace-local PNG/MP4
  review copies; raw PPMs/log remain on Mini and the image/video extensions
  remain intentionally ignored by Git.
- QMP-quit the exact run and independently verified zero recorded QEMU/runqemu
  PIDs, zero forwarded ports, and no residual QMP socket.

### Check

- **Live-capture gate: NOT MET.** The Flutter process had already timed out
  before the saved QMP images; therefore these pixels cannot establish its
  live output. The post-timeout still and all eight video frames are black and
  byte-hash-identical to the pre-Flutter frame. No vehicle, HUD, or chroma is
  visible in those post-timeout frames.
- **Runtime sequence:** the bounded log recorded two successful present
  returns (`result=0`) followed by a present-enter with no recorded return;
  app/outer-SSH status was `124`. This does not identify why the third return
  was absent or whether a live frame briefly differed.
- **Teardown: PASS.** QMP quit was accepted; recorded PIDs, socket, and
  forwarded ports were absent afterward.

## Visual evidence

- Post-timeout QMP full-frame PNG review copy is workspace-local at
  `work/evidence/FLR-0382-0001-post-timeout.png` (intentionally ignored by
  `.gitignore`); SHA-256
  `3e25a09ca6defc8efa884ff9945f86dea746b99e7fd6c70fdfdfa8109877351a`.
- Eight-frame post-timeout QMP MP4 review copy is workspace-local at
  `work/evidence/FLR-0382-0001-post-timeout.mp4` (intentionally ignored by
  `.gitignore`); SHA-256
  `e1cd12d484871c53ac253c5ceb850c3f7448fe459317031354eae8b4fb56103f`.
- Authoritative raw PPMs and runtime log remain under the Mini role path
  `$BUILD_EVIDENCE/flr0382-0001/qemu`; raw media are not committed.
- Both are explicitly post-timeout, not live Flutter acceptance evidence. All
  eight raw QMP PPM hashes equal the pre-Flutter frame hash above.

### Act

- Keep this ticket In Progress: its live-QMP acceptance gate was not met. For
  the same one-variable comparison, use a fresh run ID (`flr0382-0002`) and
  start the bounded QMP/liveness observer before manually invoking Flutter, so
  capture is triggered during the process lifetime. Do not change the trace
  profile, source, or persistent scripts in that retry.
- Do not reopen the already completed texture inventory or broad camera/light
  sweeps. Use a valid live frame plus the present/stage sequence to choose the
  next boundary.
- Production colored Sequoia and the 2D HUD in one QMP frame remain the goal.

## UNKNOWN

- Whether stage-trace logging is the relevant difference between the 0378
  silhouette and 0381 live gray frame.
- Whether high-volume trace output alters the app's timing or process lifetime.
- Whether the production Sequoia and 2D HUD can appear together on this image.
