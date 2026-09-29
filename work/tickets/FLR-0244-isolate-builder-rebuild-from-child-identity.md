# FLR-0244 — isolate builder rebuild from child identity replacement

- Status: Done
- Priority: High
- Owner: Flutter builder rebuild and composition boundary
- Created: 2026-09-21
- Predecessor: FLR-0243

## Objective

Separate a `ValueListenableBuilder` rebuild that returns the same child
identity from a replacement of the child widget, while keeping the parent
`Stack`, native fixture, notifier location, input coordinates, and QMP contract
unchanged.

## Facts

- FLR-0240 proves child-only mounting of Planetarium whitens the HUD.
- FLR-0242 proves a generic inert `StatefulSceneView` also whitens the HUD.
- FLR-0243 proves a plain `SizedBox` child also whitens the HUD after the same
  button-up event; native ROI remains chromatic.
- FLR-0244's stable-child A/B returned the same `const SizedBox.shrink()`
  child from a notifier-driven `ValueListenableBuilder` rebuild and still
  produced the white HUD after QMP button-up.
- Initial, move-x, move-y, and down frames retained `2883` chromatic HUD
  pixels and `100800` chromatic native-ROI pixels.
- The up frame had `0` chromatic HUD pixels and a uniform `224,224,224` HUD,
  while the native ROI remained `100800` chromatic pixels.
- The runtime marker
  `FLR0244_SCENE_SUBTREE_ACTIVATION id=5 name=StableChildBuilderRebuild`
  was observed, and the native `FLR0026_TARGET_DRAW2`/readback markers were
  present.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Any `ValueListenableBuilder` rebuild invalidates the Flutter composition boundary | notifier toggle with a stable const child also whites HUD | notifier payload must be separated from child value |
| 2 | Replacing the child widget identity triggers the white frame | stable child preserves HUD; a new child reproduces it | Flutter element reuse may mask identity difference |
| 3 | The builder's position or platform-view stacking is the boundary | both stable and replacement cases whiten HUD | requires one more fixed-child control |

The first A/B should toggle a non-visual notifier value while the builder
returns the same `const SizedBox.shrink()` instance. It must not change native
engine, fixture, camera, light, material, parent `Stack`, or QMP stimulus.

## Mac Devtool provenance

- FLR-0243 source baseline: `cf56daaecdf2986048fe1678236c060c983f076a`.
- Source commit created in the fixed Devtool workspace:
  `310436476ad384e1c7d4e44320e434bccc87eb67`.
- Official generated patch:
  `0076-flr0244-isolate-builder-rebuild-from-child-identity-devtool.patch`.
- Generated/canonical patch SHA-256:
  `6e981d0fe75c50e83b50327e87d6d7560adb4b266e8b59776ea19de3427a8d46`.
- The patch changes only `packages/filament_scene/example/lib/main.dart`.

## Success criteria

- [x] Static source inspection identifies the smallest stable-child A/B.
- [x] If a source edit is required, use the fixed Mac Devtool baseline →
  `modify --no-extract` → source edit → source commit → official
  `update-recipe`/finish flow.
- [x] Mini `do_patch`, compile, and full image gates pass for the exact bundle
  tip (`COMPILE_RC=0`, `IMAGE_RC=0`).
- [x] One QEMU run provides QMP initial/button-up frames, bounded markers, hashes,
  and clean teardown.
- [x] The result selects the builder/platform-view composition boundary for the
  next ticket; no diagnostic no-op becomes a production fix.

## Evidence

- Predecessor: [FLR-0243](FLR-0243-isolate-plain-child-replacement.md)
- Working log: [2026-09-21-flr0244.md](../logs/2026-09-21-flr0244.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0244/`
- Mini rootfs SHA-256: `eefa4c67bc150780c23bea53f4bffa768dc1e7e49b0bc8b5a19144618b0decd1`
- Mini qemuboot SHA-256: `0bca4fd7b8f87af7de63589b3359c2327694c33cbdae6bc95b3876d8bc2cb924`
- Mini kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`
- QMP initial SHA-256: `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`
- QMP up SHA-256: `83b474a377d3b8edb59a542f79cd2446961c0daef0fe44b734be22d15349f1fb`
- Pixel analysis SHA-256: `4d1a87aad788634576bc9fb06d1ba1bd7547bb1b45c6b4dc316697de099cf1d8`
- Bounded app-log SHA-256: `575f3beeed63b18b2a087b57e49ec30a8bae34528a0224dc165254682c067fde`
- Cleanup: `qmp_residual=0 qemu_residual=0 app_residual=0`.

## UNKNOWN

- Whether removing the `ValueListenableBuilder` while retaining the same native
  fixture and QMP stimulus preserves the HUD.
- Whether the remaining boundary is the Builder itself or the platform-view/
  Wayland composition beneath it.
