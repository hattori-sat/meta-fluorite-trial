# FLR-0408 — replay known-positive Sequoia model-only profile on exact 0334

- Status: In Progress
- Priority: High
- Created: 2026-10-03
- Owner: Mini QEMU / UID-1001 Example Demo / shared app log / QMP and kernel evidence
- Branch: `feature-flr-0408-replay-sequoia-0334`
- Depends on: [FLR-0405](FLR-0405-capture-first-fengine-fault-present-order.md); patch-0334 rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`
- Plan: [FLR-0408 bounded model-only replay](../../docs/superpowers/plans/2026-10-03-flr0408-known-positive-model-profile.md)
- Working log: [FLR-0408 working log](../logs/2026-10-03-flr0408.md)

## Objective and boundary

Replay the model-only conditions that produced visible production Sequoia
pixels in FLR-0049, now on the immutable 0334 image. Change only the guest
launch profile; do not edit source, patch, image, camera, lighting, material,
or the capture/observer implementation during this runtime attempt.

This is a single bounded Gate-A discriminator. Even if Sequoia pixels appear,
it does not establish original lighting, simultaneous Flutter HUD composition,
viewpoint interaction, repaint/input stability, five-minute present health, or
two-boot reproducibility. Those remain separate gates toward the user's full
product objective.

## Facts

- FLR-0049 iteration 10 used Sequoia model selection with limit 2; the readback
  probe was unset, and environment, skybox, indirect light, shapes, and lights
  were skipped. It reached `MODEL_STAGE_SCENE_ADD_DONE`, reported 25 Scene
  entities/14 renderables and successful present markers, and full-screen QMP
  images visibly contained production vehicle pixels and red lamps. The native
  surface was above the Flutter parent, so that run did not show the HUD in the
  same frame. Its image/runtime is historical, not the current 0334 candidate.
  See [FLR-0049](FLR-0049-production-model-render-boundary.md) and [its working
  log](../logs/2026-09-08-flr0049.md).
- FLR-0404 and FLR-0405-0003 used the exact 0334 artifacts with ordinary
  Example Demo launch and no optional selectors. Their identity-bound QMP
  frames showed a white field and black polygon, without recognizable Sequoia
  or HUD. FLR-0405-0003 also recorded an Oops before a later unhealthy present
  gate, with call-level event ordering UNKNOWN.
- Current expected artifact hashes, independently checked before this ticket:
  rootfs `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`,
  kernel `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`,
  qemuboot `2363530e2f39d4e57465cb89e724327f699b8ab6247d9e1bb75fdc2a60780c10`.
  They must be rehashed immediately before QEMU startup.
- The 0408 commands use the new run-local
  `/run/user/1001/fluorite-0408-0001.*` namespace. Existing `FLR0026_*`
  controls and emitted markers are reused only to reproduce FLR-0049; no new
  legacy path, marker, or control is introduced.

## Inferences

- On one immutable image, this replay compares the ordinary launch with the
  historical explicit model selection and environment/skybox/indirect-light/
  shape/light skips. It does not isolate which of those several skip controls
  is necessary.
- Scene insertion and process liveness are intermediate signals only. The
  pixel verdict requires recognizable production Sequoia in a live,
  identity-bracketed full-screen QMP capture.

## Hypotheses

1. **The historical model-only profile produces Sequoia pixels on 0334.**
   Support: exact profile, `SCENE_ADD_DONE`, identifiable vehicle geometry or
   texture/red-lamp pixels in QMP, and a live matching app identity. Refute:
   scene insertion is reached but QMP contains no recognizable car.
2. **The 0334 renderer/presentation path remains unhealthy with this profile.**
   Support: scene-add completes but QMP stays white/black/blank, or an Oops or
   present fault precedes usable pixels. Refute: visible production geometry
   and progressing successful presents during the bounded capture.
3. **The historical profile is not reproduced in the current runtime.**
   Support: launch, process identity, asset selection, or scene-add gate fails
   before the expected marker. This makes the visual result UNKNOWN, not proof
   that the renderer cannot draw Sequoia.

## UNKNOWN

- Whether the historical model-only profile is sufficient to produce visible
  Sequoia pixels on the current 0334 artifact set.
- Which individual model/environment/light/shape control mattered in FLR-0049;
  this ticket deliberately does not split those controls.
- Whether original lighting/material behavior, Flutter HUD composition,
  interactive camera/depth, pointer/repaint stability, five-minute health, or
  two independent boots pass.
- Whether any current Oops/present symptom shares a cause with the older
  FLR-0049 renderer observations.

## 4W1H (Why excluded)

| Dimension | Evidence target |
| --- | --- |
| What | production Sequoia scene-add, full-screen QMP pixels, present counts, first kernel fault |
| Where | Mini fixed qemux86-64 artifacts, QEMU guest UID 1001, QMP framebuffer |
| When | one fresh QEMU boot; capture after the secondary Sequoia scene-add marker |
| Who | runtime operator, Example Demo/Filament scene owner, QEMU evidence owner |

## Success criteria — Gate-A experiment only

1. Immediately before startup, confirm no conflicting QEMU/runqemu/Flutter/
   BitBake owner, ports 10930–10932 free, evidence directory unused, active
   source/build/receiver roles unchanged, and all three 0334 hashes exact.
2. Start exactly one QEMU with the fixed runqemu harness and 6144 MiB. Launch
   exactly one `flutter-auto` as UID 1001 with `env -i` and only required
   HOME/PATH/XDG/Wayland settings plus the six historical controls:
   `MODEL_MATCH=sequoia`, `MODEL_LIMIT=2`, `SKIP_SKYBOX=1`,
   `SKIP_INDIRECT_LIGHT=1`, `SKIP_SHAPES=1`, `SKIP_LIGHTS=1`, and
   `MODEL_STAGE_TRACE=1`. `NATIVE_READBACK_PROBE` stays unset. No camera,
   material, global environment-skip, input, or sync override is permitted.
3. Require the same live PID/UID/start token around a full-screen QMP still
   immediately after `MODEL_STAGE_SCENE_ADD_DONE` and eight QMP frames 0.5 s
   apart. Preserve raw PPMs, command/serial/app/kernel evidence on the Mini
   before teardown; record their hashes in the evidence manifest.
4. Report separate `SCENE_ADD`, `GATE_A_PIXELS`, `PRESENT_HEALTH`, and
   `RUNTIME_FAULT` verdicts. Pixel PASS requires recognizable production
   Sequoia, not a diagnostic shape or black polygon. Present health here is a
   short-window observation, not the five-minute gate.
5. Stop only the recorded app identity, QMP-quit only this QEMU, prove exact
   process/socket/port cleanup and unchanged deploy hashes, and preserve
   failures and UNKNOWNs in the ticket, working log, and evidence manifest.

## Plan / Do / Check / Act

### Plan

- Reuse the exact 0334 runtime image without bundle transfer or build.
- Replay FLR-0049 iteration 10 as one combined model-only control; change no
  source, artifact, camera, material, or observer variable.
- Bracket full-screen QMP evidence with guest PID/UID/start identity and keep
  scene-add, visual pixels, present health, and kernel-fault verdicts separate.
- Stop at the first abnormal boundary; do not extend a short capture into a
  stability claim.

### Do

- The six one-line commands are in `work/commands/FLR-0408-guest-*.cmd`; their
  paths are confined to the 0408 run namespace.
- `python3 -B tests/test_flr0408_profile.py` passed 4/4.
- Initial read-only baseline: branch
  `feature-flr-0408-replay-sequoia-0334` at checkpoint
  `ffafe4394a73d44db2644438338d11c6de089ba3`. No FLR-0408 QEMU or build has
  started; revalidate remote ownership and artifact facts before runtime.

### Check

- Pending full local repository gates and one bounded runtime attempt. No
  product or image acceptance is claimed.

### Act

- If Gate A passes, create a separate ticket to restore original lights and
  environment one factor at a time, then separately validate same-frame HUD
  composition and final input/repaint/five-minute/two-boot criteria.
- If scene-add is reached but vehicle pixels fail, use the same run's first-
  fault/log/QMP evidence to choose one smaller render-versus-present
  discriminator; do not repeat this profile without new evidence.
- If launch or scene-add fails before reproducing the intended profile, record
  UNKNOWN and choose the next test from that exact boundary.
