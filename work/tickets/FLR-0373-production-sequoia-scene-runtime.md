# FLR-0373 — test production Sequoia scene with the 2D HUD

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / direct guest SSH / manual Flutter / QMP evidence roles
- Created: 2026-09-30
- Predecessor: [FLR-0371 candidate LIT/SUN parameter fixture](FLR-0371-lit-parameter-rgb-assignment.md)
- Branch: `feature-flr-0373-production-sequoia-scene` (local, no push)
- Working log: [FLR-0373 working log](../logs/2026-09-30-flr0373.md)
- Candidate image: build output SHA-256
  `3b627cfda1c255783b281a00b469b6c30c7a6bcef4823e8b655ca15c30eb84b3`;
  rootfs SHA-256
  `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`;
  Flutter engine and Example Demo bundle `3.32.5`.

## Objective

Determine whether the production Sequoia scene in the installed Example Demo
can render recognizable vehicle pixels together with the 2D HUD on the exact
candidate image that now displays the self-made LIT/SUN fixture. The preceding
fixture run proves a native 3D geometry+HUD path, not the production vehicle.
This ticket changes no source, image, recipe, or launch script.

## Facts

- FLR-0371 run `flr0371-0004` showed the LIT/SUN parameter branch, dark-blue
  self-made geometry, and HUD in the same full-frame QMP image. See the
  [QMP screenshot](../evidence/FLR-0371-0004-qmp-candidate-parameter.png) and
  the [predecessor ticket](FLR-0371-lit-parameter-rgb-assignment.md).
- The candidate image installs the Example Demo bundle under the `3.32.5`
  release subtree. The prior positive-control image used Flutter engine
  `3.38.3`; keep the version difference explicit in any comparison.
- The current prelaunch screenshot has a `Scenes` control at approximately
  `(1206,40)` on a 1280×800 frame. This is a measured starting point, not proof
  that the control opens a production route.
- Historical FLR-0236 proved the Scenes tap callback could activate a
  Planetarium route, but the post-tap frame lost HUD chroma and did not prove
  Planetarium pixels. FLR-0252 also recorded pointer delivery without a
  production scene transition on a different image. Do not assume the current
  candidate behaves like either run.
- Historical FLR-0286 keeps the native fixture and production Sequoia gates
  separate; its fixture-positive frames do not establish vehicle visibility.

## Hypotheses

1. **The production scene is already selected on startup.** With all fixture
   variables unset, the default full-frame QMP capture contains recognizable
   Sequoia body/texture pixels and the HUD.
2. **The production scene requires a route/menu selection.** The initial frame
   lacks the vehicle, but a measured QMP input to the visible Scenes control
   produces a route marker/menu transition and subsequent Sequoia pixels.
3. **The route/model loads but its rendered output is not visible.** Logs show
   model/scene/draw/present progress while the vehicle ROI remains black,
   clipped, grayscale, or occluded; this would move the next diagnosis to the
   first missing production render/material/composition boundary.

## Scope and success criteria

- Reuse the exact candidate rootfs above and the existing Mini build/TMPDIR.
  No rebuild, cache invalidation, or image transfer to Mac.
- Use one fresh QEMU run ID `flr0373-0001`, 6144 MiB, the existing QEMU helper,
  strict run-pinned guest SSH, and the established port triplet. Refuse to
  start if any prior QEMU/runqemu/flutter-auto target or port remains.
- Verify guest kernel, AGL compositor, Wayland socket, Example Demo `3.32.5`
  bundle, executable, and zero stale Flutter processes before launch.
- Manually launch exactly one `/usr/bin/flutter-auto` as `agl-driver` over
  guest SSH. Leave all diagnostic fixture/light/camera/color overrides unset;
  use only the minimal successful-present trace needed to gate QMP capture.
- Capture a complete QMP frame before input. If the production scene is not
  visible, inspect that frame and the bounded route/menu evidence before any
  input. If needed, send one QMP pointer sequence at the measured Scenes
  control, capture the resulting frame, and inspect it before further input.
- A pass requires recognizable production Sequoia geometry/material color and
  the Flutter HUD in the same 1280×800 QMP frame, plus repeated successful
  presents. A diagnostic cube, asset preview, route callback alone, or HUD-only
  frame is not a pass.
- Save QMP still, 8-frame QMP video, image/app identity, bounded runtime and
  journal evidence, ROI measurements, hashes, and exact teardown result under
  `$BUILD_EVIDENCE/flr0373-0001/qemu/`. Stop only the recorded app PID and
  recorded QEMU through its QMP socket; verify process/socket/port cleanup.
- If the HUD disappears or the route does not activate, record the first
  divergence and stop this run. Do not patch or edit a launcher in this ticket.

## Impact

- **Build-time:** none; reuse the attributable candidate image.
- **Packaging:** none; verify the installed bundle version before launch.
- **Runtime:** one manual production-scene run with fixture overrides absent.
- **Integration risk:** no source/image mutation; any engine-version caveat is
  carried forward. A fixture result remains distinct from a production model
  result.

## Plan / Do / Check / Act

### Plan

Reuse the exact FLR-0371 candidate image and the already proven manual runqemu
→ guest SSH → Flutter → successful-present → QMP sequence. First inspect the
default production screen; only use QMP Scenes input if the initial frame and
bounded app markers show that a route selection is needed. Keep fixture
overrides unset and capture the entire QMP frame before judging.

### Do

- Ticket opened after the FLR-0371 candidate fixture+HUD runtime pass.
- No QEMU run or source/configuration change has been made under this ticket
  yet.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Candidate image identity | Exact FLR-0371 rootfs/kernel/qemuboot hashes | Pending | PENDING |
| Guest readiness | SSH, compositor, Wayland, bundle, and zero stale app | Pending | PENDING |
| Production route | Default Sequoia or measured Scenes transition | Pending | PENDING |
| QMP pixels | Recognizable Sequoia and HUD in one complete frame | Pending | PENDING |
| Teardown | Exact app/QMP shutdown; zero residual process/socket/ports | Pending | PENDING |

### Act

- If Sequoia and HUD are visible, close this runtime gate and move to any
  remaining color/lighting or interaction acceptance in a separate ticket.
- If the screen remains HUD-only or the route loses HUD pixels, preserve the
  first-divergence evidence and create a separate ticket for that boundary.
- Do not infer production success from FLR-0371's diagnostic geometry.

## Visual evidence

- Baseline fixture+HUD control: [FLR-0371 QMP screenshot](../evidence/FLR-0371-0004-qmp-candidate-parameter.png).
- Candidate production run artifacts: `$BUILD_EVIDENCE/flr0373-0001/qemu/`
  (to be populated only by this ticket's single fresh run).

## UNKNOWN

- Whether the production Sequoia route is selected by default in this bundle.
- Whether the current Scenes control activates the production route without
  losing HUD composition.
- Whether the candidate Flutter-engine/bundle version difference from the
  earlier 3.38.3 control changes production model rendering.
- Whether production vehicle texture/material output appears in the visible
  native QMP target.
