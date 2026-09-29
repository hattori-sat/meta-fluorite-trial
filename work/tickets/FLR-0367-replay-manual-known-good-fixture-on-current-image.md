# FLR-0367 — replay the manual lit-fixture control on the current image

- Status: In Progress
- Priority: High
- Owner: Mini QEMU / direct guest SSH / manual Flutter launch / QMP evidence roles
- Created: 2026-09-29
- Predecessor: [FLR-0366 GDB fault capture](FLR-0366-capture-fengine-loop-pagefault.md)
- Historical positive control: [FLR-0286 known-good combined fixture](FLR-0286-reproduce-known-good-combined-sequoia-hud.md)
- Current image: rootfs SHA-256 `5c8ca252181fac1a64669ae78de5b3fa590db1048f95f156db306df2f9d821ec`
- Run ID: `flr0367-0001` (one fresh attempt)
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
- Current-image ability to render the self-made lit fixture with the HUD is
  UNKNOWN.

### Hypotheses

1. **Shared manual Flutter display path works:** the exact FLR-0286 fixture
   profile produces colored 3D and a changing/visible HUD on the current image,
   with repeated successful queue-present results.
2. **Current image/profile has regressed below the fixture path:** the manual
   launch reaches Flutter but QMP remains blank/static or present does not
   complete; distinguish launch/session from rendering using process, startup,
   and present evidence.
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

- Ticket opened. Runtime run `flr0367-0001` is pending; no QEMU/app command has
  been issued under this ticket.

### Check

| Gate | Expected | Actual | Result |
| --- | --- | --- | --- |
| Current image/session preflight | Exact rootfs, guest SSH, bundle, tools, no stale app | Pending | PENDING |
| Manual fixture launch | One agl-driver app with exact FLR-0286 environment | Pending | PENDING |
| HUD + fixture QMP pixels | Both visible in same full frame with separate ROI metrics | Pending | PENDING |
| Repeated present | Multiple begins with matching successful returns, or first divergence | Pending | PENDING |
| QMP still/video | Full-screen evidence saved, hashed, visually reviewed | Pending | PENDING |
| Teardown | Recorded app/QEMU/socket/ports absent | Pending | PENDING |

### Act

- If fixture+HUD pass, preserve this exact manual launch as the current-image
  positive control and open a separate production Sequoia task from its
  working state. Only then consider codifying the proven manual launch in a
  separate script ticket.
- If fixture+HUD fail, do not edit a launch script. Use the first verified
  boundary (guest session/startup, native draw, present, or QMP pixels) to
  choose one small follow-up experiment.

## Evidence

- Historical positive QMP evidence: FLR-0286 ticket and `$EVIDENCE_ROOT/flr0286-0003`.
- Current run Mini evidence: `$EVIDENCE_ROOT/flr0367-0001/qemu` (pending).
- Current full-frame still/video and hashes: pending.

## UNKNOWN

- Whether the exact historical manual fixture command still succeeds on the
  current pinned image and whether present completion remains repeatable.
- Whether a current-image fixture pass would restore production Sequoia; the
  two paths remain separate until measured.
