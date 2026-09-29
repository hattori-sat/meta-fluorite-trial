# FLR-0242 — isolate generic StatefulSceneView mount

- Status: Done
- Priority: High
- Owner: Flutter child replacement and StatefulSceneView mount boundary
- Created: 2026-09-21
- Predecessor: FLR-0241

## Objective

Separate a generic inert `StatefulSceneView` mount from the actual
`PlanetariumSceneView` mount while keeping the FLR-0240 `ValueNotifier` child
boundary, parent `Stack`, native fixture, input coordinates, and QMP contract
unchanged.

## Facts

- FLR-0239 proves parent `setState` is sufficient to whiten the HUD.
- FLR-0240 proves child-only mounting of the actual Planetarium widget still
  whitens the HUD while native fixture pixels remain `24178`.
- FLR-0241 disables the Planetarium `onCreate` native commands and all
  `onUpdateFrame` native commands, but reproduces the same result.
- FLR-0241 observed the scene activation marker and Wayland attach, but no
  `FLR0241_PLANETARIUM_LIFECYCLE_INERT` marker; callback invocation timing is
  not yet proven.

## Mac Devtool provenance

- Fixed Devtool source baseline: `7eda35d03d607ac44d1d60c2c12fb149a3f0b26b`.
- Source commit created in the fixed Devtool workspace:
  `2b0cc553090dda829acfc7a2d87c4343c03ea960`.
- Official generated patch: `0074-flr0242-isolate-generic-stateful-sceneview-mount-devtool.patch`.
- Generated/canonical patch SHA-256:
  `eebcb81a5dacc7cbfa48097ecabfbca333593d1c3bf2d82d9cdd5d9172fbbf88`.
- The patch changes only
  `packages/filament_scene/example/lib/main.dart` (42 insertions, 2 deletions).
- The finish helper exposed a missing `source-git-revision` operation in the
  container runner. The runner was corrected before the patch was registered;
  no patch body was hand-authored or edited.

## Hypotheses and alternatives

| Rank | Candidate | Prediction | Risk |
| --- | --- | --- | --- |
| 1 | `PlanetariumSceneView`-specific state or callback registration causes white | generic inert child preserves HUD; Planetarium child whites it | actual callback timing remains unobserved |
| 2 | generic `StatefulSceneView` mount causes white | both generic and Planetarium children whiten HUD | boundary is below the scene subclass |
| 3 | `ValueListenableBuilder` replacement itself causes white | replace with a plain inert widget and compare | child type/identity becomes a confounder |

The first A/B changes only the scene child type. It does not change native
fixture, camera, light, material, engine, or parent composition code.

## Result

The generic inert `StatefulSceneView` produced the same post-input white HUD
as `PlanetariumSceneView`. The initial QMP frame visibly contains the 2D HUD,
Scenes button, and self-made native cube simultaneously. After the same
button-up event, the HUD region becomes uniform white while the native cube
region remains chromatic and unchanged. Planetarium-specific lifecycle bodies,
camera, light, and material are therefore not required for this failure.

The remaining boundary is either the common `StatefulSceneView` mount or the
`ValueListenableBuilder` child replacement itself. FLR-0243 owns that next A/B.

## Success criteria

- Static source inspection identifies the smallest generic inert child that
  satisfies the existing `StatefulSceneView` contract.
- If a source edit is required, generate it through Mac Devtool baseline →
  `modify --no-extract` → edit → source commit → `update-recipe` → finish.
- Mini `do_patch`, compile, and full image gates pass for the exact bundle tip.
- One QEMU run provides QMP initial/post-tap frames, bounded markers, hashes,
  and clean teardown.
- The result selects either the generic mount boundary or the Planetarium
  subclass boundary for the next ticket; no diagnostic no-op is left as a
  production fix.

## Evidence

- Predecessor: [FLR-0241](FLR-0241-isolate-planetarium-lifecycle-callbacks.md)
- Working log: [2026-09-21-flr0242.md](../logs/2026-09-21-flr0242.md)
- Runtime evidence root: `$EVIDENCE_ROOT/FLR-0242/`

## Verification

- Canonical layer commit: `6d797ffc550f12996f875a5cf4200d7ff00f779e`.
- Bundle SHA-256:
  `6e020232d98a62af57c55d3d0d01439cd72a5d1c524fc0b3755930dd90baed88`.
- Mini patch gate: `preflight=PASS`, `metadata=PASS`,
  `workdir-reset=PASS`, `do_patch=PASS`.
- Mini compile: `COMPILE_RC=0`; 1,674/1,674 tasks succeeded.
- Mini image: `IMAGE_RC=0`; 11,758/11,758 tasks succeeded.
- Rootfs SHA-256:
  `36a39f16e95314b84ccdb68b5ec395c5526db77defb308d21d942371d5b13c4d`.
- Qemuboot SHA-256:
  `033e150896da66883724e3f9d03db480cc81702ee20d909171143de49e81cd6d`.
- Kernel SHA-256:
  `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.
- QMP initial frame SHA-256:
  `c2f291fac8013e12fb3695277416f4b9c1e405a9ba2c182fd7f93c8b9e452d01`.
- QMP button-up frame SHA-256:
  `83b474a377d3b8edb59a542f79cd2446961c0daef0fe44b734be22d15349f1fb`.
- Pixel-analysis SHA-256:
  `2a669636c24dd02eb91ff7d48a5ecf49be2da42a3b4b1a8af051a16b3c045bed`.
- Initial/move/down: HUD chromatic `2883`; native ROI chromatic `100800`.
- Button-up: HUD chromatic `0` and uniform white; native ROI chromatic
  `100800` with unchanged region SHA.
- Bounded app/Wayland marker log SHA-256:
  `541bcc88ccf33fbd416b301f9db03cb8d027cf5b601b743e2688d49bc4ee4674`.
- QMP cleanup: `residual_targets=0`, `residual_qmp=0`; recorded flutter-auto
  residual was also `0`.

## UNKNOWN

- Whether a plain inert `Widget` child under the same notifier boundary also
  whitens the HUD.
- Whether the white frame is caused by common `StatefulSceneView.initState` or
  by child replacement/platform-view ownership.
