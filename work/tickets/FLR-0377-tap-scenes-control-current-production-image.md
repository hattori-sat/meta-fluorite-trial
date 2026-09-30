# FLR-0377 — tap the measured Scenes control on the current production image

- Status: Waiting
- Priority: High
- Owner: Mini QEMU / strict guest SSH / `agl-driver` / QMP input / Flutter route roles
- Created: 2026-09-30
- Predecessor: [FLR-0376 manual session-environment replay](FLR-0376-manual-flutter-session-env-replay.md)
- Branch: `feature-flr-0377-scenes-tap-current-production` (local, no push)
- Working log: [FLR-0377 working log](../logs/2026-09-30-flr0377.md)
- Candidate rootfs SHA-256:
  `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`.

## Objective

On the exact current candidate, manually run the production Example Demo with
the verified `agl-driver` Wayland session, then send one measured QMP tap at
the Scenes control's prior known location. Determine whether the packaged app
emits the Planetarium activation marker and whether the full QMP frame changes
to recognizable 3D/2D output. This is a runtime input/route discriminator, not
a patch/build task.

## Facts

- FLR-0376 manually launched the production bundle as UID 1001 with explicit
  XDG/Wayland variables. QMP showed a white field and large black polygon, with
  no HUD or recognizable Sequoia; it matched FLR-0374 byte-for-byte. The
  present/Oops signature recurred.
- FLR-0371 on this exact rootfs and Example Demo version showed the CPU/GPU
  HUD, native fixture, and Scenes button together. In that fixture frame the
  button bounds were approximately x=1157..1255, y=24..56; the planned tap
  center was `(1206,40)`. This does not establish that the control is present
  or hit-testable in the production frame.
- FLR-0236 established that the app callback can emit
  `FLR0236_SCENE_ACTIVATION id=3 name=Planetarium` and call `_setScene(3)`, but
  its post-tap HUD became white and it did not prove Planetarium pixels. That
  older candidate does not establish current-image behavior.
- FLR-0375 validated all 23 embedded PNGs and every production GLB
  texture/material reference; no external image URI is missing.

## 4W1H (excluding Why)

| Dimension | Current evidence | Needed discriminator |
| --- | --- | --- |
| What | Current production frame has no visible control/car/HUD | One measured Scenes tap, route marker, full QMP before/after |
| Where | Exact FLR-0371 candidate rootfs, Example Demo 3.32.5 on Mini QEMU | Same rootfs and bundle; no fixture overrides |
| When | FEngine Oops recurs about 35 seconds after launch | Send once after first successful present and before Oops/exit |
| Who | Flutter route callback should receive guest pointer event | Confirm callback marker; no marker means route is unproven |
| How | Direct SSH, `agl-driver`, explicit XDG/Wayland, one tap at `(1206,40)` | No coordinate sweep, app-launch helper, or script edit |

## Hypotheses

1. **The current Scenes control is active beneath the visually absent/occluded
   UI.** One tap at the measured center emits the Planetarium marker; the
   after-frame may reveal route-specific content.
2. **The production UI surface is not receiving the pointer event.** No route
   marker appears; the tap cannot be interpreted as a Planetarium render test.
3. **The route callback runs but does not fix production output.** The marker
   appears while the QMP frame remains white/black or loses the HUD, separating
   route activation from scene pixels/composition.

## UNKNOWN

- Whether the measured control remains hit-testable when it is not visible in
  the current production QMP frame.
- Whether the current packaged build contains a route callback matching the
  final patch-stack marker `FLR0274_SCENE_TRANSITION`.
- Whether a Planetarium route change makes production 3D pixels visible.

## Scope and success criteria

- Reuse the exact candidate rootfs/kernel/qemuboot; one fresh QEMU, one run
  evidence directory, 6144 MiB, and strict guest SSH. Pin the per-run host key
  only after verifying QEMU owns the forwarded listener.
- Verify compositor, Wayland socket, app bundle, and zero stale Flutter
  processes. Manually launch one production app as `agl-driver` with
  `XDG_RUNTIME_DIR=/run/user/1001`, `WAYLAND_DISPLAY=wayland-0`, and only the
  present trace; no fixture/light/camera/color overrides.
- Save a complete QMP frame before input. Wait for one successful Present or
  a bounded classified Oops/exit. If the app remains alive, send exactly one
  QMP pointer enter/motion/press/release at `(1206,40)`, the measured
  FLR-0371 Scenes-button center; save QMP input replies.
- Capture a complete post-input QMP frame and short sequence. Claim route
  activation only if the runtime emits
  `FLR0274_SCENE_TRANSITION id=3 name=Planetarium`; claim visible 3D only if
  recognizable scene geometry and the HUD appear together in the full frame.
- Preserve bounded app/kernel/process evidence before stopping. Stop only the
  verified app PID and this QEMU through its QMP socket; independently confirm
  zero residual processes/socket/ports.
- No source, recipe, script, Devtool, BitBake, build, or image changes. If the
  marker is absent, stop after this one measured tap; do not sweep coordinates.

## Impact

- **Build-time:** none.
- **Packaging:** none.
- **Runtime:** one app launch and one measured pointer tap.
- **Integration risk:** no software mutation; this may prove only input/route
  activation, not visible Planetarium or Sequoia output.

## Plan / Do / Check / Act

### Plan

Review FLR-0236's callback contract and FLR-0371's same-image button location.
Reuse the direct manual guest route, capture before/after QMP, and send one
input only after the first successful present. Stop at the first route marker,
Oops, app exit, or bounded timeout.

### Do

- The exact candidate was started once. Strict guest SSH preflight passed;
  `agl-driver` UID 1001 manually launched the production Example Demo 3.32.5
  bundle with explicit `XDG_RUNTIME_DIR=/run/user/1001`,
  `WAYLAND_DISPLAY=wayland-0`, and `FLUORITE_PRESENT_TRACE=1`. Fixture,
  light, and camera overrides were absent.
- QMP accepted the one planned pointer sequence at `(1206,40)`. The location
  came from the separate FLR-0371 fixture/HUD frame; the production frame did
  not visibly contain that HUD or a Scenes control. The current run therefore
  cannot prove that Flutter received a control tap.
- Final patch 0091's `FLR0274_SCENE_TRANSITION` marker is present in the
  packaged AOT scan but absent from the runtime log after the tap. Before/after
  QMP PPMs are byte-identical. One queue-present returned `result=0`; the
  second entered without a recorded return, and a guest `FEngine::loop` page
  fault followed. The parent app survived; no coredump was listed.
- The full QMP frame shows a white/gray field and a large black polygon; it
  shows no recognizable Sequoia, HUD, or Scenes button. Native ROI
  `(440,220,400,360)` is `0/144000` chromatic; top-right HUD ROI
  `(1120,0,160,80)` is uniform RGB 224. QMP-only before/after PPM SHA-256:
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
- The guest kernel recorded an Oops at monotonic `333.934`; `dmesg --ctime`
  was unsupported by guest BusyBox, so bounded evidence was recovered with
  `journalctl -k -b -o short-monotonic --no-pager`. No causal claim is made
  between the tap, second present, Oops, or pixels.
- The first QMP client timed out during greeting parsing before sending a
  command. A corrected line reader then performed the single authorized tap.
  The first key-pin command failed local zsh parsing; the first harness start
  failed closed because its run directory had not been created. Both failures
  occurred before the affected remote/runtime operation and are retained in
  the working log.
- Exact app PID and this QEMU were stopped; QMP quit was accepted and
  independent process/socket/port checks found no residuals. No script,
  source, recipe, Devtool, BitBake, build, or image changed.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Candidate and guest preflight | Exact image, compositor/session ready, no stale app | Exact hashes; guest session and zero stale app passed | PASS |
| Manual app/session | One production app as UID 1001 with explicit session vars | PID 665; explicit XDG/Wayland/present trace; fixture overrides absent | PASS |
| Measured QMP input | Exactly one tap at `(1206,40)` with replies saved | QMP accepted one pointer sequence; Flutter callback receipt is unproven because control was not visible | PASS for QMP delivery only |
| Route evidence | Final marker and full before/after frames | `FLR0274_SCENE_TRANSITION` absent at runtime; PPM unchanged | FAIL / callback not established |
| Present/Oops | Bounded present result and kernel context | 2 enters, 1 return; FEngine Oops; no coredump | FAIL for stable production runtime; cause UNKNOWN |
| Visual acceptance | Recognizable production 3D plus HUD in one full frame | White/gray field + black polygon; no recognizable Sequoia/HUD | FAIL |
| Teardown | Exact PID/QMP cleanup; zero process/socket/ports | Exact stop and QMP quit passed; no residuals | PASS |
| Scope | No source/script/build edits or coordinate sweep | No edits | PASS |

### Act

- Keep this ticket Waiting: the bounded input attempt is recorded, but visual
  acceptance failed and the Oops cause remains UNKNOWN. The HUD/control was
  not present, so the tap is not evidence of failed Flutter hit testing or a
  Planetarium-rendering failure. Do not repeat this coordinate.
- FLR-0378 replays the historical no-light/shape/IBL-suppressed Sequoia
  condition manually on the current candidate. FLR-0285-0018 showed a
  production vehicle silhouette under that condition; FLR-0285-0019 restored
  normal light/IBL/shapes and showed HUD but no recognizable vehicle.
- Keep launcher scripts unchanged until the manual current-image condition is
  proven. The overall combined production Sequoia+HUD acceptance remains open.

## Visual evidence

![QMP-only full screen after the measured input: white/gray field and black polygon; no HUD or recognizable Sequoia](../evidence/FLR-0377-0001/FLR-0377-0001-qmp-after-tap.png)

[Open the eight-frame QMP-only replay](../evidence/FLR-0377-0001/FLR-0377-0001-qmp-after-tap.mp4).
The PNG SHA-256 is `dddb1b3e017d85600974be4d48c3b4e57990d9460eb573f24cd8587ff477c19d`;
the MP4 SHA-256 is `614950238f8e6725e1e59ed0cfe10e56250369ce69c3c93e43cecca7a917728f`.
Raw PPMs, runtime logs, and frame sequence remain at the fixed Mini evidence
role path `$EVIDENCE_ROOT/flr0377-0001/qemu/`.

- Jira is intentionally not used; this Markdown ticket and working log are
  the source of truth.
- `FLR-0026` identifiers remain historical only.
