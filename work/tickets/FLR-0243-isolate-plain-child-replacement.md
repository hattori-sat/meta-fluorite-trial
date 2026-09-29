# FLR-0243 — isolate plain child replacement

- Status: Done
- Priority: High
- Owner: Flutter child replacement and composition boundary
- Created: 2026-09-21
- Predecessor: FLR-0242

## Objective

Separate the common `StatefulSceneView` mount from the
`ValueListenableBuilder` child replacement by using a plain inert `Widget`
under the same parent `Stack`, notifier update, native fixture, input
coordinates, and QMP contract.

## Facts

- FLR-0239 proves parent `setState` is sufficient to whiten the HUD.
- FLR-0240 proves child-only mounting of the actual Planetarium widget still
  whitens the HUD while native fixture pixels remain visible.
- FLR-0241 proves Planetarium lifecycle command bodies are not sufficient to
  explain the white frame.
- FLR-0242 proves a generic inert `StatefulSceneView` also whites the HUD after
  the same QMP button-up while the native ROI remains chromatic.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | Any notifier-driven child replacement repaints the parent/composition boundary | plain inert child also whites HUD; native ROI remains visible | notifier type must be generalized from `StatefulSceneView?` to `Widget?` |
| 2 | Common `StatefulSceneView.initState`/callback registration causes white | plain inert child preserves HUD | changing notifier type adds a small source confounder |
| 3 | The `ValueListenableBuilder` itself or key/identity behavior causes white | equivalent plain child still whites HUD | requires keeping builder and parent structure identical |

The A/B must not change the native fixture, engine, camera, light, material,
parent `Stack`, or QMP stimulus.

## Result

Replacing the generic `StatefulSceneView` with a plain `const SizedBox.shrink()`
under the same notifier-driven builder did not change the failure. The initial
QMP frame visibly contains the 2D HUD, Scenes control, and self-made native
cube. After the same button-up event, the HUD is uniform white while the
native ROI remains unchanged and chromatic. `StatefulSceneView.initState`,
callback registration, and Planetarium-specific state are therefore not
sufficient causes.

FLR-0244 now separates a builder rebuild that returns the same child identity
from a replacement of the child widget itself.

## Mac Devtool provenance

- FLR-0242 source baseline: `2b0cc553090dda829acfc7a2d87c4343c03ea960`.
- Source commit created in the fixed Devtool workspace:
  `cf56daaecdf2986048fe1678236c060c983f076a`.
- Official generated patch:
  `0075-flr0243-isolate-plain-child-replacement-devtool.patch`.
- Generated/canonical patch SHA-256:
  `0e44513831fd849881d88c99f087f01277aff64ea3b45dbc357f36ff32efed45`.
- The patch changes only `packages/filament_scene/example/lib/main.dart`.

## Success criteria

- Static source inspection identifies the smallest plain-child A/B.
- If a source edit is required, use the fixed Mac Devtool baseline →
  `modify --no-extract` → source edit → source commit → official
  `update-recipe`/finish flow. Do not hand-author the patch.
- Mini `do_patch`, compile, and full image gates pass for the exact bundle tip.
- One QEMU run provides QMP initial/button-up frames, bounded markers, hashes,
  and clean teardown.
- The result selects the StatefulSceneView boundary or the plain child
  replacement boundary for the next ticket; no diagnostic no-op becomes a
  production fix.

## Evidence

- Predecessor: [FLR-0242](FLR-0242-isolate-stateful-sceneview-mount.md)
- Working log: [2026-09-21-flr0243.md](../logs/2026-09-21-flr0243.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0243/`

## Verification

- Canonical layer commit: `8678c14e50d641f2c88994f1865e800e2c35cf2e`.
- Bundle SHA-256:
  `519f59f4ae3b1fe8e9e34d5efeec7beb303b870e78d29362ff6f480ab7cf057e`.
- Official patch SHA-256:
  `0e44513831fd849881d88c99f087f01277aff64ea3b45dbc357f36ff32efed45`.
- Mini patch gate: `preflight=PASS`, `metadata=PASS`,
  `workdir-reset=PASS`, `do_patch=PASS`.
- Mini compile: `COMPILE_RC=0`; 1,674/1,674 tasks succeeded.
- Mini image: `IMAGE_RC=0`; 11,758/11,758 tasks succeeded.
- Rootfs SHA-256:
  `3acf55e03f0e17df6c31a41ca9d56df8cd3cb6f1646aca4bf4c97ab1e4afec00`.
- Qemuboot SHA-256:
  `2b40d8bbfc9fb128152a50ade4bc875f85a1555a5c8f1ef2f955e814c377be6b`.
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QMP initial frame SHA-256:
  `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`.
- QMP button-up frame SHA-256:
  `83b474a377d3b8edb59a542f79cd2446961c0daef0fe44b734be22d15349f1fb`.
- Pixel-analysis SHA-256:
  `e2a60265deef443cfcae80257aec356d2112175ce6028bf620cb2a9918a6c7fe`.
- Initial/move/down: HUD chromatic `2883`; native ROI chromatic `100800`.
- Button-up: HUD chromatic `0` and uniform white; native ROI chromatic
  `100800` with unchanged region SHA.
- Bounded app/Wayland marker log SHA-256:
  `f2adda3a6ef72af8c3f734ae10dc99386ba0953a992fd71ea7f6f04f8ddf9037`.
- QMP cleanup: `residual_targets=0`, `residual_qmp=0`; recorded flutter-auto
  residual was also `0`.

## UNKNOWN

- Whether a builder rebuild that returns the same child identity preserves the
  2D HUD through button-up.
- Whether child identity replacement is required for the white frame.
