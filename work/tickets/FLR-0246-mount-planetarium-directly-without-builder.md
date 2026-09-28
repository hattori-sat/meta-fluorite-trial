# FLR-0246 — mount Planetarium directly without Builder rebuild

- Status: Done
- Priority: High
- Owner: Planetarium lifecycle and stable Flutter/native composition boundary
- Created: 2026-09-21
- Predecessor: FLR-0245

## Objective

Replace the diagnostic direct `SizedBox` with a direct
`PlanetariumSceneView` child, without `ValueListenableBuilder`, while keeping
the native `SceneView`, parent `Stack`, QMP input coordinates, and pixel ROIs
unchanged. Verify that Planetarium lifecycle execution can coexist with the
2D HUD and self-made native 3D without triggering the Builder white frame.

## Facts

- FLR-0235 proves simultaneous 2D HUD and self-made native 3D pixels.
- FLR-0244 proves a stable-child `ValueListenableBuilder` rebuild whites the
  HUD while native 3D remains chromatic.
- FLR-0245 proves direct mounting without the Builder preserves both HUD and
  native 3D through the same QMP button sequence.
- `PlanetariumSceneView.build` currently returns `SizedBox.shrink()` and its
  lifecycle is separately observable through `StatefulSceneViewState`.
- FLR-0246 direct-mounted `PlanetariumSceneView` preserved `2883` chromatic HUD
  pixels and `100800` chromatic native-ROI pixels through button-up.
- The runtime contained 21 native `FLR0026_SHAPE_READY` markers and render /
  readback markers, but zero `FLR0241_PLANETARIUM_LIFECYCLE_INERT onCreate`
  markers.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Direct Planetarium lifecycle is composition-safe | Direct `PlanetariumSceneView` preserves HUD and native ROI | Its lifecycle may issue frame callbacks even with an inert build |
| 2 | Any StatefulSceneView lifecycle crosses the composition boundary | Direct Planetarium mount whites HUD or changes native ROI | Would require lifecycle callback isolation below the widget tree |
| 3 | Production geometry/camera is independently invalid | HUD remains stable but Planetarium geometry is not visible | Fixture pixels may mask production-scene absence |

## Scope and invariants

- Change only the stable child from `const SizedBox.shrink()` to a direct
  `PlanetariumSceneView` constructed with the existing controllers.
- Do not change native `SceneView`, shapes, camera, light, material, parent
  `Stack`, input coordinates, QMP harness, or ROI thresholds.
- Use the fixed Mac Devtool source history and official generated patch flow.
- Run the exact Mini patch/compile/image gates and one QMP session.

## Success criteria

- [x] Static source inspection confirms the direct lifecycle-only A/B.
- [x] Official Mac Devtool source commit, generated patch, and canonical commit are
  recorded; no hand-authored patch is accepted.
- [x] Mini `do_patch`, compile, and full image gates pass.
- [x] QMP proves HUD/native ROI values through button-up, and bounded lifecycle,
  native, and input markers are saved before teardown.
- [x] Cleanup proves zero residual QEMU/QMP/flutter-auto processes.
- [x] The result states whether lifecycle mounting is safe and whether production
  Planetarium pixels remain UNKNOWN or are visually proven.

## Evidence

- Predecessor: [FLR-0245](FLR-0245-isolate-builder-from-platform-view-composition.md)
- Working log: [2026-09-21-flr0246.md](../logs/2026-09-21-flr0246.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0246/`
- Source commit: `d53ef222db62d67283f223c04f85ad0d3d7ebf6e`.
- Official generated patch:
  `0078-flr0246-mount-planetarium-directly-without-builder-devtool.patch`.
- Patch SHA-256: `8f0873078f76ebe84bb64204dcecb7c0d33d7412dc56419bcb02039711057fc5`.
- Canonical layer commit: `2860e92de793120a7321f262e2d397fed05b4d77`.
- Bundle SHA-256: `46360269646b5935a34d699f08c873a8ebd17d22d5647a6fa1dc1b5864ec1948`.
- Mini rootfs SHA-256: `4c6d243929829cb4e8b375c5dac77db497f663bbf98589453c003b1647ff948d`.
- Mini qemuboot SHA-256: `9b6904bf7ace29b7111243585d1afea0932f4cde21121ef4adab336759e74588`.
- Mini kernel SHA-256: `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QMP initial/up SHA-256: `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`.
- Pixel analysis SHA-256: `e3eb81b41a0300beddd24687696e2a8ef648bc6fa6f6a53af3999e2f8298392b`.
- Bounded app-log SHA-256: `0d5e9605ce148ea88ee90097cd7183ca3e52d08c5f713d0167d4e34d7545d4a4`.
- Cleanup: `qmp_residual=0 qemu_residual=0 app_residual=0`.

## UNKNOWN

- Why the readiness-gated `PlanetariumSceneView.onCreate` callback was not
  observed even though native shape creation and frame rendering succeeded.
- Whether the production Planetarium objects are visible independently of the
  diagnostic native cube.
