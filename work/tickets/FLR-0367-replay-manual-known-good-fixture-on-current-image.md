# FLR-0367 — replay the manual lit-fixture control on the current image

- Status: Waiting
- Priority: High
- Owner: Mini QEMU / direct guest SSH / manual Flutter launch / QMP evidence roles
- Created: 2026-09-29
- Updated: 2026-09-30
- Predecessor: [FLR-0366 GDB fault capture](FLR-0366-capture-fengine-loop-pagefault.md)
- Historical positive control: [FLR-0286 known-good combined fixture](FLR-0286-reproduce-known-good-combined-sequoia-hud.md)
- Current image: rootfs SHA-256 `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`
- Run ID: `flr0367-0001` (one fresh attempt)
- Branch: `feature-flr-0367-manual-known-good-fixture` (local continuation from the unmerged FLR-0366 feature tip; no push)
- Working log: [FLR-0367 working log](../logs/2026-09-29-flr0367.md)

## Objective

Recover the last proven manual Flutter rendering baseline on the exact current
image before editing any launch script. Over direct guest SSH, manually start
the installed Example Demo using FLR-0286's known-positive self-made lit
Filament fixture profile. Capture whether the Flutter HUD and colored native
3D appear together in QMP and whether present continues to complete.

This is a positive-control replay, not production Sequoia acceptance. The
historical FLR-0286 rootfs SHA (`08ee47d01cced5139a724284462c6b3f23bf687c05a342202282a34122a7d65d`) differs from the current pinned image, so the current-image replay is necessary.

## Facts and hypotheses

### Facts

- FLR-0286 run `flr0286-0003` manually launched `/usr/bin/flutter-auto` as
  `agl-driver` from the Example Demo bundle with the opt-in pure/minimal local
  camera, self-made lit fixture, and bounded render/present markers. One QMP
  frame contained both HUD and lit fixture: native ROI had 119,716/144,000
  chromatic pixels; HUD ROI had 2,845 chromatic pixels.
- That positive run used rootfs SHA
  `08ee47d01cced5139a724284462c6b3f23bf687c05a342202282a34122a7d65d`; it is
  not the current rootfs.
- FLR-0365/0366 manually launched the same Example Demo bundle on current
  rootfs SHA `5c8ca...`; production output lacked a visible HUD and
  recognizable Sequoia, and FLR-0366 reproduced a kernel Oops.
- Current-image replay did not render the self-made lit fixture: HUD is visible
  in QMP, but the native 3D ROI is black. The manual app launch and Vulkan
  present path did run; see the 2026-09-30 result below.

### Hypotheses

1. **Shared manual Flutter display path works:** the exact FLR-0286 fixture
   profile produces colored 3D and a changing/visible HUD on the current image,
   with repeated successful queue-present results.
2. **Current image/profile reaches Flutter but not fixture pixels:** HUD,
   fixture setup, draw, and successful present markers appear, while QMP native
   ROI remains black. This is now the observed result; the first pixel-loss
   boundary remains unresolved.
3. **Fixture works but production Example Demo does not:** same-frame fixture
   and HUD pixels return while the production Sequoia run remains a separate
   FEngine/scene/content problem.

## Scope

### In scope

- One fresh QEMU run on the exact pinned current image and direct strict guest
  SSH using the successful FLR-0365 connection procedure.
- One manually entered `flutter-auto` launch using FLR-0286's exact fixture
  environment/profile; verify one `agl-driver` process and no stale app.
- Bounded startup/fixture/draw/present markers, QMP full-frame still/eight
  frames, separate HUD/native ROI pixel review, and exact-run teardown.

### Out of scope

- Editing or creating a Flutter app-launch shell script; do not automate an
  unverified command.
- Source/recipe/patch changes, image build, switching Vulkan/software backend,
  or changes to production Sequoia camera/light/material/texture.
- Treating a fixture pass as production acceptance.

## Success criteria

1. Fresh run uses current pinned rootfs SHA above, has no process/port/run-ID
   collision, and records guest/tool/bundle identity before launch.
2. The known-positive FLR-0286 environment is typed and run manually over
   guest SSH; exactly one `agl-driver` `flutter-auto` process is present.
3. At least one QMP frame contains both the Flutter HUD and identifiable,
   chromatic self-made native 3D fixture pixels; HUD and fixture ROIs are
   reported separately.
4. Bounded logs show multiple present begins with matching successful returns
   (or the exact first divergence is recorded); do not infer activity from a
   live PID or a single static screenshot.
5. Preserve QMP full-frame still and eight-frame video plus hashes; visually
   inspect the whole screenshot.
6. Stop the recorded app, quit only this run's QMP instance, and independently
   verify zero run-owned processes/socket/ports.
7. Do not modify any launcher. Only after a manual known-good run passes may a
   separate task propose codifying that proven command.

## Impact

- **Build-time:** none; use the existing image.
- **Packaging:** none.
- **Runtime:** one manual Flutter app run; the exact historical fixture trace
  profile is retained to maximize comparison validity.
- **Integration risk:** low; no persistent script/source change. Fixture
  success does not prove production Sequoia works.

## Plan / Do / Check / Act

### Plan

- Reuse the existing Mini QEMU harness and pinned image, but launch Flutter
  manually over the verified guest SSH route, not through an app runner.
- Reuse FLR-0286's exact known-positive fixture environment and bundle; change
  no rendering or system backend inputs.
- Capture targeted runtime markers and QMP evidence, then clean up the exact
  recorded run.

### Do

- Run ID `flr0367-0001` evidence directory was created once. Standard QEMU
  harness preflight passed for the exact current kernel/rootfs/qemuboot hashes,
  6144 MiB profile, free ports 10930–10932, empty run-owned QMP slot, and zero
  QEMU/runqemu/flutter-auto targets. QEMU started as Mini supervisor PID
  2755919 / QEMU PID 2755946; the QMP socket and SSH-forward owner were verified.
- Guest SSH banner passed on attempt 2. Port 10931 was owned by PID 2755946;
  run-scoped RSA/ECDSA host keys were pinned and strict SSH as `root` passed.
  Guest preflight found kernel `6.6.111-yocto-standard`, UID 1001
  `agl-driver`, the bundle, Wayland socket, `/usr/bin/flutter-auto`, GDB 14.2,
  and zero running `flutter-auto` processes.
- The prelaunch QMP still was captured with the receiver pixel helper; its
  source and Mini copy SHA-256 both equal
  `992c0428cc85dc61ebdea1e49dc544eed528a961f06faf9dd7fe7de30795ec24`.

### Result — 2026-09-30

The exact FLR-0286 command profile was entered over strict guest SSH and launched
directly as `agl-driver`; no launcher script was used or changed. The full
command profile is preserved at
[`FLR-0286 manual launch command`](../commands/FLR-0286-fixture-lit-light-launch.cmd).

- One `flutter-auto` process (PID 681, UID 1001) ran for 13 minutes. Runtime
  log SHA-256 is
  `47e0f1e4524f4f1b0fe9ef907eabeb7577c951d6848c08dd1b9e0e08fea29a07`
  (85,298,358 bytes; guest `/run` log, summarized before QEMU teardown).
- The app reported pure fixture setup, `shading=lit`, SUN intensity 110000,
  8 vertices / 36 indices, one renderable primitive with a bound material,
  native scene ownership, and camera eye `(0,0,5)` toward `(0,0,0)`.
- Runtime counts: draw submit 1040; draw end 1040; ViewTarget render return
  1040; Vulkan queue-present `result=0` 1040; present-boundary completion
  1040. No matching app error/exception or guest Oops marker was found in the
  bounded queries.
- Full QMP PPM SHA-256:
  `7ff0ec019ce53082697d917c0657cacf7f49770e1f0d5240e0e3942705d08a78`.
  Native ROI `(440,220,400,360)` was entirely black (0 changed / 0 chromatic
  of 144,000 pixels). HUD ROI `(1120,0,160,80)` had 2,845 chromatic pixels.
- The complete 1280x800 screenshot and 8-frame / 8-second video are retained
  below. The whole screenshot was visually inspected: FPS, frametime, CPU, GPU,
  script/system-delay HUD and Scenes button are present; no 3D geometry is
  visible.
- App PID 681 was stopped after rechecking UID/command. The exact QMP socket
  accepted quit; the harness and independent checks found run-owned PIDs 0,
  QMP socket absent, and ports 10930–10932 free.

![FLR-0367 full QMP screenshot — HUD visible, native 3D ROI black](../evidence/FLR-0367-qmp-run-0001.png)

[View the 8-frame QMP video](../evidence/FLR-0367-qmp-run-0001-sequence.mp4).

#### Result interpretation

- **Fact:** Flutter is running, the 2D HUD reaches QMP, the native fixture is
  configured, draw calls return, and Vulkan present succeeds repeatedly.
- **Fact:** the current image does not reproduce FLR-0286's same-frame colored
  3D fixture; QMP native ROI is black.
- **Inference:** this is not a QEMU-boot-only observation, a failed Flutter
  launch, or a stalled present. It places the unresolved boundary between the
  configured native geometry/material and visible native pixels.
- **Hypotheses for the next discriminator:** (1) LIT material/light output is
  the failing branch; (2) the native geometry/target path is regressed even
  without lighting. Do not select between these from metadata or present
  success alone.
- The current rootfs (`5c8ca252…`) differs from the historical positive
  FLR-0286 rootfs (`08ee47d…`); the source/runtime change that separates them is
  UNKNOWN.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Current image/session preflight | Exact rootfs, guest SSH, bundle, tools, no stale app | Exact image hashes; strict SSH as root; bundle, Wayland, GDB, Flutter verified; zero app | PASS |
| Manual fixture launch | One agl-driver app with exact FLR-0286 environment | One direct-SSH launch, PID 681/UID 1001; setup and camera markers present | PASS |
| HUD + fixture QMP pixels | Both visible in same full frame with separate ROI metrics | HUD 2,845 chromatic; native ROI 0/144,000 changed or chromatic | FAIL — 3D not reproduced |
| Repeated present | Multiple begins with matching successful returns, or first divergence | 1,040 draw submit/end, render-return, result=0 present, and boundary-done records | PASS |
| QMP still/video | Full-screen evidence saved, hashed, visually reviewed | 1280x800 PNG and 8-frame/8-second MP4 retained and inspected | PASS |
| Teardown | Recorded app/QEMU/socket/ports absent | App stopped; QMP quit accepted; exact PIDs/socket absent; ports free | PASS |

### Act

- The positive-control gate did not pass, so keep FLR-0367 Waiting. FLR-0368
  owns the next one-variable manual test: unset only
  `FLUORITE_NATIVE_FIXTURE_LIGHT` to compare the same fixture as UNLIT on the
  same rootfs. Stop after setup, a bounded set of completed presents, and QMP
  capture; do not repeat FLR-0367's 13-minute observation window.
- Do not edit a launcher or source based on this result. A successful UNLIT
  control would isolate the LIT/light branch; an all-black UNLIT control would
  move the investigation to native geometry/target output.

## Evidence

- Historical positive QMP evidence: FLR-0286 ticket and `$EVIDENCE_ROOT/flr0286-0003`.
- Current run Mini evidence: `$EVIDENCE_ROOT/flr0367-0001/qemu`.
- Full-frame source PPM SHA-256:
  `7ff0ec019ce53082697d917c0657cacf7f49770e1f0d5240e0e3942705d08a78`.
- Mac-visible PNG SHA-256:
  `a8af4ef1443811644d80843cefe511d81b68f529ccef4d357c34627c9cca17f5`.
- Eight-frame / eight-second MP4 SHA-256:
  `a8af20ef2231291bf18ed049938ffa76a51a1c8a94d1dd3ef9f9def85d918ca0`.

## UNKNOWN

- Why the same lit fixture produced chromatic pixels on the historical rootfs
  but not on the current pinned rootfs despite setup/draw/present success.
- Whether a current-image fixture pass would restore production Sequoia; the
  two paths remain separate until measured.
