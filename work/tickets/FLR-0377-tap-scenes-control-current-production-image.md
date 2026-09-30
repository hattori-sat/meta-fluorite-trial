# FLR-0377 — tap the measured Scenes control on the current production image

- Status: In Progress
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
  HUD, native fixture, and Scenes button together. In that 1280x800 frame the
  button bounds are approximately x=1157..1255, y=24..56; planned tap center is
  `(1206,40)`.
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
- Whether the current packaged build contains the FLR-0236 route callback.
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
  `FLR0236_SCENE_ACTIVATION id=3 name=Planetarium`; claim visible 3D only if
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

- Pending manual QEMU/Flutter/QMP input run.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Candidate and guest preflight | Exact image, compositor/session ready, no stale app | Pending | PENDING |
| Manual app/session | One production app as UID 1001 with explicit session vars | Pending | PENDING |
| Measured QMP input | Exactly one tap at `(1206,40)` with replies saved | Pending | PENDING |
| Route evidence | Planetarium marker and full before/after frames | Pending | PENDING |
| Visual acceptance | Recognizable production 3D plus HUD in one full frame | Pending | PENDING |
| Teardown | Exact PID/QMP cleanup; zero process/socket/ports | Pending | PENDING |
| Scope | No source/script/build edits or coordinate sweep | No edits | PASS |

### Act

- Do not change scripts or patches based on a missing/ambiguous callback.
  Record whether the input reached the route, then split the next test at the
  first evidenced boundary.

- Jira is intentionally not used; this Markdown ticket and working log are
  the source of truth.
- `FLR-0026` identifiers remain historical only.
