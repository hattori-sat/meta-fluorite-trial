# FLR-0373 — test production Sequoia scene with the 2D HUD

- Status: Waiting
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
- FLR-0366's QMP pre-fault and post-fault raw PPMs both have SHA-256
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
  FLR-0373 reproduces that exact frame hash on the new candidate image.
- FLR-0366 recorded two Vulkan queue-present begins and one return, then a
  later `FEngine::loop` kernel Oops. FLR-0373 has the same 2-enter/1-return
  count, but its raw guest app log was not saved before VM shutdown; current
  Oops recurrence is UNKNOWN.

## Hypotheses

1. **The known FEngine/present failure state recurs.** The unmatched second
   queue-present and exact FLR-0366 frame recur before the display freezes; the
   candidate may later produce the same kernel Oops.
2. **Production route/model output is separately incomplete.** The image
   contains a large monochrome polygon but no recognizable Sequoia or HUD;
   scene/resource/camera/composition could be an independent boundary.
3. **A light-only fault explains the result.** This is currently weaker: the
   HUD is absent and output is frozen at the present boundary, so a Light
   change alone is not yet a clean discriminator.

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
- Reused candidate build output SHA-256
  `3b627cfda1c255783b281a00b469b6c30c7a6bcef4823e8b655ca15c30eb84b3`,
  rootfs `949921c8bed28c540bd06a593cf37bbb9d94591985a2e9c7e31aaa35af9b4086`,
  kernel `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`,
  and qemuboot
  `8582ac80d4c58fc9e852abed0e6fd6e6077bf6e5f0f7727341033fb405d0a17c`.
- Fresh run `flr0373-0001` used unchanged QEMU helper SHA
  `088e8e39ed1fc7dce175ad0fd2a027325b04815c68337a9e52fead2c9fb64fee`,
  6144 MiB, and ports 10930–10932. Start passed; PID 2851396 was the Python
  supervisor, child PID 2851423 was `qemu-system-x86`, and that child owned
  forwarded SSH port 10931. The supervisor/PID-type assumption was corrected
  before key pinning.
- Strict guest SSH directly as `agl-driver` was rejected by public-key auth.
  The historical route is strict SSH as guest `root`, then `su` to
  `agl-driver`; this succeeded. Guest kernel `6.6.111-yocto-standard`, active
  compositor, Wayland socket, Example Demo 3.32.5, and zero stale Flutter
  processes were verified. Fixture overrides were unset.
- Captured pre-Flutter QMP, then manually launched one `/usr/bin/flutter-auto`
  as UID 1001 with only `FLUORITE_PRESENT_TRACE=1`. PID 710/start-time 44677
  remained alive at the bounded 45-second gate.
- Gate result: 2 `FLUORITE_VK_QUEUE_PRESENT_ENTER`, 1
  `FLUORITE_VK_QUEUE_PRESENT_RETURN`, and only 1 successful return. App log
  size at the gate was 103,693 bytes. The second present had no return during
  the 45-second window.
- Full QMP PPM SHA-256 is
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`,
  exactly matching both FLR-0366 pre-fault and post-fault PPMs. All eight
  0.1-second QMP frames have this hash. The frame is a gray-white field with a
  large black polygon: no recognizable vehicle, HUD text, or chromatic pixels.
  Against the black pre-Flutter frame, 598,250/1,024,000 pixels changed;
  native ROI `(440,220,400,360)` remained 0/144,000 changed/chromatic; HUD ROI
  `(1120,0,160,80)` changed to uniform RGB 224 with 0/12,800 chromatic pixels.
  Pixel geometry does not identify the polygon as Sequoia.
- The guest app log lived under `/run/user/1001` and was lost when QEMU shut
  down. Only the 45-second marker/count summary remains; this run's kernel
  Oops, coredump, and fault-time stack are UNKNOWN. FLR-0374 fixes this
  evidence-retention gap before shutdown.
- After QMP still/eight-frame capture, exact PID 710 received SIGTERM and the
  guest reported zero remaining `flutter-auto`. The first QMP quit did not
  produce cleanup; independent checks found the QEMU/socket/ports still
  active. A second QMP quit was accepted; independent checks then confirmed
  both PIDs absent, socket absent, and ports 10930–10932 free.
- Direct SSH-as-agl-driver and several guest-wrapper command attempts stopped
  before app execution; corrected steps used root→`su` and a `guest_ssh`
  function. Initial SCP omitted `-r` for the frames directory; corrected
  recursive download succeeded. Raw QMP evidence remains on Mini; only QMP
  review images/video were copied locally. No rootfs/kernel/QEMU image was
  transferred.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Candidate image identity | Exact FLR-0371 rootfs/kernel/qemuboot hashes | All matched | PASS |
| Guest readiness | Strict pinned root SSH, compositor, Wayland, bundle, and zero stale app | Pass; UID 1001 confirmed through `su` | PASS |
| Manual production launch | One app, fixture overrides unset, minimal present trace | PID 710/start 44677; only `FLUORITE_PRESENT_TRACE=1` | PASS |
| Successful present gate | Repeated completed queue presents within 45 s | 2 enters, 1 return, 1 successful; second return absent | FAIL — first divergence |
| QMP pixels | Recognizable Sequoia and HUD in one complete frame | Exact FLR-0366 PPM hash; black polygon/gray-white field, HUD absent, zero chroma | FAIL — production acceptance |
| Guest log retention | Bounded runtime/kernel evidence saved before shutdown | Marker summary saved; raw guest app log/current-run Oops evidence lost | FAIL — process improvement required |
| Teardown | Exact app/QMP shutdown; zero residual process/socket/ports | App stop passed; first QMP quit incomplete; second quit and independent checks passed | PASS after correction |

### Act

- Keep this ticket Waiting: the bounded production attempt ended, but its
  acceptance criteria failed and current-run Oops evidence remains UNKNOWN.
- FLR-0374 owns one fresh same-image present/Oops correlation with bounded app
  log, kernel tail, and thread-state evidence saved before QEMU shutdown. Keep
  GDB detached during its timed no-debugger observation.
- Do not patch lighting, camera, or production app code from this screenshot
  alone; it exactly reproduces the previously recorded FEngine failure image.

## Visual evidence

- Baseline fixture+HUD control: [FLR-0371 QMP screenshot](../evidence/FLR-0371-0004-qmp-candidate-parameter.png).
- Production run screenshot: [full QMP frame](../evidence/FLR-0373-0001-qmp-production.png),
  PNG SHA-256
  `dddb1b3e017d85600974be4d48c3b4e57990d9460eb573f24cd8587ff477c19d`.
- [Eight-frame QMP review video](../evidence/FLR-0373-0001-qmp-production-sequence.mp4),
  SHA-256 `186acbdddf9e84a0466b8ac4c8941d7ad085b27bea010de3aed9f0e38777aef5`;
  all eight source PPMs are identical.
- Raw pre-Flutter QMP PPM SHA-256
  `d4e96a65fd4f8c97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`;
  production full-frame PPM SHA-256
  `f686a3c2769cb2bc59b362bdc1d956c2d1d128cbcbfa6ea45ffe2eb92b4a5265`.
- Raw PPMs, eight frames, helper copies, selected gate/identity/stop records,
  and QEMU logs remain under `$BUILD_EVIDENCE/flr0373-0001/qemu/`. The
  production PPM hash was verified directly against Mini's FLR-0366
  `pre-fault.ppm` and `post-fault.ppm` (both exact matches).

## UNKNOWN

- Whether the large black polygon is a Sequoia renderable or a different
  native fragment; pixel shape alone cannot identify it.
- Whether the second unmatched Vulkan present causes the HUD/scene freeze,
  follows another `FEngine::loop` fault, or is only correlated.
- Whether a kernel Oops/coredump occurred (raw guest log was not saved before
  QEMU shutdown).
- Whether the current 3.32.5 candidate shares the exact FLR-0366 mechanism,
  despite the byte-identical QMP result and same present counts.
