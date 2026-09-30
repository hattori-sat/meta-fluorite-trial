# FLR-0378 — replay the historical Sequoia no-light condition on the current candidate

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / strict guest SSH / `agl-driver` / Flutter runtime / QMP evidence roles
- Created: 2026-09-30
- Predecessor: [FLR-0377 measured route-tap diagnostic](FLR-0377-tap-scenes-control-current-production-image.md)
- Historical controls: [FLR-0285 production silhouette A/B](FLR-0285-trace-production-draw-command-boundary.md), [FLR-0371 current-image LIT/SUN fixture](FLR-0371-lit-parameter-rgb-assignment.md)
- Branch: `feature-flr-0378-replay-sequoia-no-light-current-candidate` (local, no push)
- Working log: [FLR-0378 working log](../logs/2026-09-30-flr0378.md)
- Candidate rootfs SHA-256: `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`

## Objective

On the exact current candidate, manually launch the production Example Demo
over strict guest SSH as `agl-driver` with the historically successful
Sequoia-selection profile that suppresses skybox, indirect light, direct
lights, and shapes—but does not suppress frame events. Determine whether the
current 3.32.5 bundle reaches scene insertion and renders recognizable vehicle
pixels, and compare the complete QMP frame with the normal-light production
baseline and the self-made LIT/SUN+HUD control. This is a single runtime
discriminator, not a patch or automation task.

## Facts

- FLR-0285-0018 used rootfs `0da1a010…`, kernel `3df53470…`, and Example Demo
  3.38.3. With model match `sequoia`, model limit `2`, and skybox, indirect
  light, direct lights, and shapes suppressed, the runtime inserted two
  Sequoia entries and QMP showed the vehicle silhouette. The asynchronous
  frame event remained enabled. Its exact committed launch profile is
  `work/commands/FLR-0285-production-sequoia-current-launch.cmd` (commit
  `e00268cb3f23f96852046738c7746a17a6de1e0a`); it includes
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1` but does not set
  `FLR0026_SKIP_FRAME_EVENT`. Preserve that exact environment contract on the
  current bundle where supported. The saved evidence does not claim that the
  HUD appeared in that frame.
- FLR-0285-0019 restored production light/IBL/skybox/shapes on that same older
  image; the HUD appeared but the recognizable vehicle did not. This is a
  condition comparison, not proof that lighting alone is causal because the
  test changes a group of setup controls.
- FLR-0371-0004 on the current rootfs and Example Demo 3.32.5 manually showed
  a self-made dark-blue LIT/SUN geometry and CPU/GPU HUD together, with 146
  successful presents. This proves current-image native geometry+HUD can
  compose; it does not prove production Sequoia.
- FLR-0377 manually launched the current production bundle with explicit user
  session variables and no fixture/light/camera overrides. It produced a
  white/gray field and black polygon, no visible HUD/control, one successful
  present, then an unmatched second present and FEngine Oops. A tap at the
  coordinate measured on the separate fixture frame cannot establish Flutter
  route input when the control is absent.
- The current layer patch stack includes the historical model-selection and
  skip-control implementations. The run must still verify the effective
  environment at app exec and the corresponding runtime markers; AOT string
  presence alone is not runtime proof.
- Historical FLR-0284 is useful but not the same discriminator: it used rootfs
  `f2b940f0…`, `FLR0026_NATIVE_MODEL_LIMIT=1`, and frame-event skip while
  restoring direct lights. It reached present but stayed zero-chroma. The
  current replay uses rootfs `949921c8…`, model limit `2`, and frame events
  enabled, so a current-image direct-light A/B remains distinct.

## 4W1H (excluding Why)

| Dimension | Current evidence | Needed discriminator |
| --- | --- | --- |
| What | Current normal profile lacks identifiable Sequoia/HUD; the current no-light replay shows a black Sequoia silhouette, but no color or HUD | Restore only direct lights on the same current candidate and score vehicle chroma/HUD separately |
| Where | Exact current FLR-0371 candidate, Example Demo 3.32.5, Mini QEMU | Same rootfs/kernel/qemuboot; no older image or build |
| When | FLR-0377 normal profile stalled after its second present; this no-light replay logged 2 scene-add and 918 present matches with no Oops match | Compare direct-light-only restoration, bounded to 45 seconds or first classified Oops/exit |
| Who | Guest app as `agl-driver` UID 1001; compositor/Wayland session already verified | Strict guest SSH, one app, explicit session variables, exact process identity |
| How | One manual `flutter-auto` launch with historical scene-selection/setup-suppression controls; QMP full frame shows the exact prior silhouette hash | Keep all controls fixed except direct-light restoration; no launcher edit |

## Hypotheses

1. **The current production scene can expose the Sequoia under the historical
   no-light condition.** Prediction: scene insertion and repeated present
   markers appear, and the full QMP frame contains recognizable vehicle
   geometry. HUD visibility is scored separately.
2. **The current bundle/runtime fails before useful scene output regardless of
   setup suppression.** Prediction: the same unmatched present/Oops and
   non-identifiable frame recur despite verified environment and scene-add
   markers.
3. **The prior silhouette depended on frame-event/order behavior rather than
   light suppression.** Prediction: current run does not insert the model or
   diverges before scene-add; no lighting conclusion is warranted.

## Scope and success criteria

- Reuse only the recorded current candidate rootfs/kernel/qemuboot and fixed
  Mini runtime/evidence roles. One QEMU, one run directory, 6144 MiB, one app.
- Before launch, verify zero residual QEMU/runqemu/flutter-auto processes,
  QMP socket and forwarded ports; candidate hashes; guest compositor/session;
  bundle version/path; and no stale app.
- Use strict guest SSH and an interactive `agl-driver` session. Explicitly
  set `XDG_RUNTIME_DIR=/run/user/1001` and `WAYLAND_DISPLAY=wayland-0`.
  Manually invoke `/usr/bin/flutter-auto` with the installed 3.32.5 bundle and
  the historically recorded `sequoia` model match/limit and light/shape/IBL
  suppression controls. Do not set `FLR0026_SKIP_FRAME_EVENT`; the prior
  0017/0018 A/B showed that disabling the frame event prevents the model-add
  path. The historical command also set
  `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`, but its enabling patch 0120 is not
  registered in the current `flutter-auto_2.0.bbappend`; omit this unsupported
  flag and record it as a patch-stack difference. Capture the pre-exec
  allowlisted environment and runtime marker values.
- Wait at most 45 seconds. Capture QMP-only full frame and eight-frame video
  after model insertion/first successful present, or the last bounded frame
  after an earlier classified failure. Save selected app markers, kernel Oops,
  process/thread state, and coredump summary before stopping.
- Score recognizable Sequoia geometry, chromatic vehicle pixels, and HUD in
  separate fixed regions. Geometry-only is a useful partial result, not the
  combined production acceptance. Compare identities and markers to
  FLR-0285-0018/0019 and FLR-0371-0004; explicitly note Flutter 3.38.3 vs
  3.32.5 and rootfs differences.
- Stop only the verified app PID and this QEMU through its QMP socket; confirm
  zero residual processes/socket/ports. Keep raw evidence on Mini and attach
  only QMP-derived review media and concise hashes to this task.
- No source, recipe, script, Devtool, bundle, BitBake, image, or build changes.

## Impact

- **Build-time:** none.
- **Packaging:** none.
- **Runtime:** one bounded manual launch with a recorded scene/light setup
  profile.
- **Integration risk:** no software mutation. If the model is visible only
  with suppression controls, this narrows the production setup boundary but
  does not by itself identify the responsible light/material/composition step.

## Plan / Do / Check / Act

### Plan

1. Verify canonical repository/checkpoint and current candidate/helper identity.
2. Re-read FLR-0285-0018/0019 environment and this image's patch registration:
   model limit/match and setup-suppression controls are registered; legacy
   force-render patch 0120 is not. Make no guessed profile changes.
3. Manually SSH, launch Flutter as `agl-driver`, capture QMP and bounded runtime
   evidence, then perform exact teardown.
4. Compare first missing marker and pixel regions against the three historical
   controls before choosing a code-level follow-up.

### Do

- Run `flr0378-0001` on Mini with the exact recorded candidate: kernel
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`,
  rootfs `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`,
  qemuboot `8582ac80d4c58fc9e852abed0e6fd6e6077bf6e5f0f7727341033fb405d0a17c`,
  and 6144 MiB. One manually invoked `/usr/bin/flutter-auto` ran as
  `agl-driver` UID 1001 over strict guest SSH with explicit
  `XDG_RUNTIME_DIR=/run/user/1001` and `WAYLAND_DISPLAY=wayland-0`; no launch
  script, source, recipe, bundle, image, or build was changed.
- Effective scene profile: model match `sequoia`, model limit `2`, skybox,
  indirect light, direct lights, and shapes suppressed; frame-event processing
  left enabled. The unsupported historical force-render variable and
  `FLR0026_SKIP_FRAME_EVENT` were not set.
- The selected runtime log reported 143284 `ASSET_READY`, 2 `SCENE_ADD`, 918
  `QUEUE_PRESENT`, and 0 `Oops` matches. At capture it was 127412716 bytes,
  SHA-256 `3445350f90f29681e8d651b611822cb1f224ed6797d43814e376ae6070696d32`.
  It lived only under `/run/user/1001` and disappeared when that user session
  ended; the raw log was not archived. Preserve this as an evidence-handling
  failure. The count/hash were captured before cleanup.
- QMP-only full frame: [PNG](../evidence/FLR-0378-0001/FLR-0378-0001-qmp-final.png),
  1280x800, PNG SHA-256
  `2cea7c5a9049ee8f9509ca4becf5be6f74f8b648c024283b6e5b5bd8eb22c8cf`.
  Its underlying PPM SHA-256 is
  `3c2769cbcff1eb225e9115968663da97433e1d8026c6065be34bdb6edbbebede`, an
  exact match for FLR-0285-0018's historical no-light frame. The visible
  result is a black vehicle silhouette at the left on a uniform light-gray
  field; it has no recognizable color/material detail and no HUD.
- In vehicle ROI `(0,100,320,310)`, 51180/99200 pixels differed from the
  background, with 4446 edge pixels, 0 chromatic pixels, and max chroma 17.
  HUD-side ROI `(960,0,320,120)` was uniform RGB `(224,224,224)` with zero
  edges/chroma. All eight captured QMP frames had the same PPM SHA. The
  [8-frame MP4](../evidence/FLR-0378-0001/FLR-0378-0001-qmp-8frames.mp4) is
  1280x800, 1.6 seconds, SHA-256
  `9e29c04ec1b0fef566a581d1a2b4d06c8f681c253d497478b8ae272da5e25164`.
- The app was stopped by its verified PID. The existing QMP helper accepted
  `quit`; its cleanup reported zero residual targets and zero socket. A
  separate Mini check confirmed no QEMU/runqemu/flutter-auto, QMP socket, or
  ports 10930–10932 remained.
- Command recoveries/failures: a Mac-local SSH attempt wrongly targeted
  `localhost:10931` (the port exists on Mini); recovered by routing through
  Mini. One nested awk/grep summary failed due to shell quoting and emitted no
  useful records; recovered with bounded keyword counts. A first cleanup check
  mistakenly ran Linux `ps -C`/`ss` on macOS; it was rerun on Mini and passed.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Canonical/checkpoint | Canonical repository; this is sole active ticket | PASS | PASS |
| Candidate/preflight | Exact hashes and zero residual targets before run | Exact kernel/rootfs/qemuboot; 64 GiB free; no residuals before launch | PASS |
| Manual user/session | Exactly one 3.32.5 app as UID 1001; effective profile saved | One direct manual app; UID 1001; explicit Wayland session; supported variables only | PASS |
| Scene/present | Scene insertion and bounded present/Oops evidence | 2 scene-add matches, 918 present matches, 0 Oops matches; raw log later lost from `/run/user/1001` | PASS with evidence-retention gap |
| QMP visual | Complete still + eight frames; Sequoia and HUD scored separately | Black Sequoia silhouette; 0 chroma; HUD ROI uniform; full frame exactly matches FLR-0285-0018 | PASS for silhouette replay; combined color+HUD acceptance FAIL |
| Teardown | Exact app/QMP stop; no residual process/socket/ports | Verified app stopped; helper quit PASS; independent Mini residual check zero | PASS |
| Scope | No scripts/source/build changed | Only runtime/evidence/docs; no product or launcher edits | PASS |

### Act

- This bounded replay is complete: current 3.32.5 reached scene-add and
  repeated present and reproduced the historical black silhouette, but did
  not produce color or HUD. The no-light profile intentionally suppresses
  illumination, so this is not evidence of a broken texture path.
- Next discriminator is a separate ticket: repeat on the same current candidate
  and restore only direct lights, leaving skybox, indirect light, shapes,
  model selection, and frame events unchanged. Archive the bounded runtime log
  to Mini's persistent run evidence before stopping the user session. Do not
  change a launcher script until the manually executed flow is useful and
  repeatable.

## UNKNOWN

- Whether the historical control flags have identical internal semantics in
  Flutter 3.38.3 and 3.32.5; empirically, current 3.32.5 did scene-add and
  present without an Oops under this profile.
- Whether any production Sequoia condition can share a frame with the Flutter
  HUD on this current image; this frame has no HUD and historical 0018 made no
  HUD claim.
- Which individual setup control, if any, explains the difference between the
  0018 and 0019 frames; these trials changed several controls together.
