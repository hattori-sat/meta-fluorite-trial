# FLR-0023 — minimal Flutter Engine 3D fixture static evidence

## Facts

- The pinned `tcna-packages` source revision was checked out into an isolated
  detached worktree; the original Mac source clone remained clean.
- The generated diagnostic patch was created by `devtool modify` followed by
  `devtool finish --mode patch` in the pinned AGL environment. Devtool emitted
  `0001-diag-add-deterministic-3d-fixture.patch` from source commit `cef2977`.
- The Devtool patch is mirrored as
  `0016-filament_scene-minimal-3d-fixture-devtool.patch` in the project layer;
  its SHA-256 is
  `3eb2de0be461fb6170990f152a2a5f894d778497a5ef26b113ac6f724966790a`.
- The fixture passes one deterministic blue cube, one default indirect light,
  one white point light, and the first existing camera into `SceneView`.
- The fixture passes no models, HDR environment, animation, or scene-specific
  asset to the native platform view.
- The Devtool patch passes `git apply --check` and apply against a clean source
  worktree at the pinned revision, followed by `git diff --check`.
- Dart formatting was inspected, but the detached source worktree lacks the
  Flutter/package dependency graph required for a meaningful analyzer run. The
  analyzer therefore failed on missing package URIs; this is not a fixture
  compile or runtime PASS.
- The Devtool patch is registered in the fixture candidate demo recipe
  `SRC_URI`; the raw pre-Devtool diff remains only as a comparison artifact.
- The r2 clean worktree was materialized on the mini PC at `e36baf0`; the
  separate candidate build parsed 3337 recipes with zero errors.
- In that candidate build, `bitbake -e` resolved the Devtool patch in the
  active `SRC_URI` and the project layer in `FILESPATH`; the raw patch was not
  active.
- The active demo recipe `do_patch` completed successfully: 104 tasks were
  attempted and all succeeded. The post-task source contained the fixture
  calls and `flr0023_fixture_cube` in the expected Dart files.
- The generated candidate configuration did not include `vulkan` in
  `DISTRO_FEATURES`; this is a separate configuration finding, not evidence
  that Vulkan is active for this candidate.
- The first fixture revision still called `poGetScenesCameras()` and therefore
  retained the old production camera graph. FLR-0020 exposed that graph's
  `TrainsetSceneView.cameras` null exception before native scene creation.
- A second Devtool round trip generated
  `0017-filament_scene-minimal-3d-fixture-camera-devtool.patch` from source
  commit `6e5b9d5`. The generated patch has SHA-256
  `6eeabf4dcb7591d144020c0c932972f6e3ab81ddb765af0f5922dc0d9df0d774` and
  creates one fixed camera without calling `poGetScenesCameras()`.
- The camera-isolated patch was committed as `8bc41b4` on the isolated
  FLR-0023 branch. Git bundle r7 used base `75f49fd` and tip `8bc41b4`; its
  SHA-256 was `1698e20e940b4f89ca6ccf4cfecd08a3313f43b0d755ceb662dea3751cb0d007`.
  SCP transfer and the mini-PC receiver ref
  `feature-flr-0023-runtime-fixture-r7` both resolved to the same tip. The
  mini-PC canonical checkout remained at its prior HEAD with its prior dirty
  entry count.
- Candidate-r3 with the camera patch parsed 3337 recipes and resolved both
  fixture patches in `bitbake -e`. Its recipe-only `do_patch` attempt was
  stopped while BitBake waited for unshared `quilt`/`attr` downloads; this is
  not a `do_patch` PASS.

## Inferences

- The existing demo does have renderable content: its normal path creates
  models, shapes, lights, and cameras. The black viewport cannot be explained
  solely by an empty Dart scene.
- The deterministic fixture removes asset/model/HDR/material randomness and
  therefore separates “no object was created” from the native presentation
  boundary.
- The Devtool round trip proves the patch is reproducible from a committed
  source change rather than only from a manually copied diff.

## Hypotheses

1. If the fixture reaches native entity/renderable creation but still produces
   no child-surface attach/commit, the remaining failure is after Dart payload
   creation in the ECS/frame/WSI path.
2. If the fixture produces no native creation evidence, the Flutter platform
   view/bootstrap or recipe patch registration remains the primary boundary.
3. If the fixture is packaged incorrectly, the recipe task or Flutter asset
   manifest will expose the omission before QEMU runtime testing.

## UNKNOWN

- Whether the camera-isolated fixture patch compiles in the authoritative
  Yocto environment; the previous `do_patch` proof covered the first fixture
  revision only.
- Whether native entity/renderable counters exist in the current plugin logs.
- Whether the fixture crosses the child Wayland surface and compositor boundary.
