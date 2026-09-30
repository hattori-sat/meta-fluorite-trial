# FLR-0378 — replay the historical Sequoia no-light condition on the current candidate

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / strict guest SSH / `agl-driver` / Flutter runtime / QMP evidence roles
- Created: 2026-09-30
- Predecessor: [FLR-0377 measured route-tap diagnostic](FLR-0377-tap-scenes-control-current-production-image.md)
- Historical controls: [FLR-0285 production silhouette A/B](FLR-0285-trace-production-draw-command-boundary.md), [FLR-0371 current-image LIT/SUN fixture](FLR-0371-lit-parameter-rgb-assignment.md)
- Branch: `feature-flr-0378-replay-sequoia-no-light-current-candidate` (to be created locally; no push)
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
  current bundle, changing only the installed bundle path. The saved evidence
  does not claim that the HUD appeared in that frame.
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

## 4W1H (excluding Why)

| Dimension | Current evidence | Needed discriminator |
| --- | --- | --- |
| What | Current production frame lacks identifiable Sequoia/HUD; older no-light profile showed a vehicle silhouette | Scene-add marker plus complete QMP frame under the recorded no-light profile |
| Where | Exact current FLR-0371 candidate, Example Demo 3.32.5, Mini QEMU | Same rootfs/kernel/qemuboot; no older image or build |
| When | Current default run stalls after second present; prior silhouette run kept frame-event processing enabled | Capture first scene insertion/present and stop at 45 seconds or first classified Oops/exit |
| Who | Guest app as `agl-driver` UID 1001; compositor/Wayland session already verified | Strict guest SSH, one app, explicit session variables, exact process identity |
| How | One manual `flutter-auto` launch with historical scene-selection/setup-suppression controls plus bounded trace | No launcher helper, no tap, no coordinate sweep, no GDB, no script edit |

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
  suppression controls and `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`. Do not
  set `FLR0026_SKIP_FRAME_EVENT`; the prior 0017/0018 A/B showed that disabling
  the frame event prevents the model-add path. Capture the pre-exec allowlisted
  environment and runtime marker values.
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
2. Re-read FLR-0285-0018/0019 environment and this image's patch registration;
   make no guessed profile changes.
3. Manually SSH, launch Flutter as `agl-driver`, capture QMP and bounded runtime
   evidence, then perform exact teardown.
4. Compare first missing marker and pixel regions against the three historical
   controls before choosing a code-level follow-up.

### Do

- Pending.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Canonical/checkpoint | Canonical repository; this is sole active ticket | Pending | PENDING |
| Candidate/preflight | Exact hashes and zero residual targets before run | Pending | PENDING |
| Manual user/session | Exactly one 3.32.5 app as UID 1001; effective profile saved | Pending | PENDING |
| Scene/present | Scene insertion and bounded present/Oops evidence | Pending | PENDING |
| QMP visual | Complete still + eight frames; Sequoia and HUD scored separately | Pending | PENDING |
| Teardown | Exact app/QMP stop; no residual process/socket/ports | Pending | PENDING |
| Scope | No scripts/source/build changed | Pending | PENDING |

### Act

- Pending runtime evidence. Do not change launch scripts until the manual
  profile is proven useful and repeatable.

## UNKNOWN

- Whether the historical no-light condition is supported identically by the
  current 3.32.5 bundle and whether it avoids the current present/Oops fault.
- Whether the historical Sequoia silhouette included any HUD pixels; current
  historical ticket records geometry but does not claim simultaneous HUD.
- Which individual setup control, if any, explains the difference between the
  0018 and 0019 frames; these trials changed several controls together.
