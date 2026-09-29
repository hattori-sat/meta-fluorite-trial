# FLR-0022 — remote sync and Flutter/Filament static evidence

## Scope

This evidence records a read-only comparison between the Mac canonical clone,
the configured mini-PC build-host role, and the mini-PC's current uncommitted
Flutter/Filament patch set. The later bundle handoff changes only Git receiver
refs and temporary inbox files; it does not change the dirty working tree.

## Facts

- The Mac canonical repository guard passes.
- The Mac checkout is on a scratch FLR-0019 feature branch with existing
  staged and untracked changes.
- The mini-PC role also passes the canonical repository guard.
- The mini-PC checkout is on a different FLR-0019 feature branch and has
  staged-free but dirty tracked and untracked changes.
- The configured expected revision does not equal the mini-PC HEAD.
- No reset, checkout, commit, push, or SCP transfer was performed during this
  comparison.
- The mini-PC patch set contains changes in `filament_view` that address:
  - recursive software-frame scheduling before the current frame completes;
  - waiting for the Dart frame-event reply on the ECS/render strand;
  - blocking platform-view registration on scene/ECS initialization;
  - ordering ECS system creation before view registration;
  - draining initial `ViewTarget` messages; and
  - dispatching frame events through Flutter's platform runner.
- The mini-PC `flutter-auto_2.0.bbappend` registers several of these patches,
  but the inspected registration list does not include the available 0041 and
  0044 patch files. The effect of that omission must be verified with the
  exact recipe-expanded `SRC_URI`; source presence alone is not build proof.
- The demo recipe contains explicit Dart-side payload adaptations for the v2
  native contract: active camera placement, camera ECS initialization
  suppression, material normalization, frame-event map conversion, and native
  frame timing.

## Inferences

- The Flutter Engine side is not absent. There is an existing platform-view,
  MethodChannel, ECS-strand, and platform-runner implementation path.
- A plausible root cause is that the code capable of creating a ViewTarget or
  renderable exists in source but is not reached, is reached before the native
  systems/channels are ready, or is not included in the effective recipe
  patchset. This is consistent with Vulkan initialization and parent-surface
  activity coexisting with zero child-surface buffer commits.
- The strongest current static boundary is bootstrap ordering and patch
  registration, not the homescreen major version by itself.

## Hypotheses

1. A view/scene message is queued before `ViewTargetSystem` or its channels
   are ready and is lost. Prediction: a minimal fixture with explicit native
   creation counters will show a missing or late ViewTarget/renderable event.
2. The relevant patch exists in the checkout but is absent from effective
   `SRC_URI`. Prediction: `bitbake -e flutter-auto` or the recipe task log will
   omit that patch from `do_patch` even though its file exists.
3. The fixture creates a renderable and completes a frame, but the transparent
   Wayland child-surface/WSI path still prevents visible composition. Prediction:
   native creation and render counters become positive while child attach/commit
   remains zero.

## UNKNOWN

- The exact effective patch order in the authoritative build until
  `bitbake -e` and the recipe-scoped `do_patch` are run against the same
  revision.
- Whether the current mini-PC dirty patch set has been built into its latest
  rootfs.
- Whether the Dart fixture's scene/model/shape payload reaches native entity
  and renderable creation on the current image.
- Whether a completed opaque diagnostic frame can cross the production
  transparent child-surface composition path.

## Synchronization decision

Do not overwrite the mini-PC checkout while it is dirty and its expected
revision is stale. First create an explicit Mac feature revision, verify its
bundle and manifest locally, then transfer only that bundle to a separate
receiver inbox. The receiver must verify the bundle and inspect its dirty
checkout before any checkout or build operation is authorized.

## Recipe-scoped parse attempt

### Facts

- The mini-PC Yocto build directory and pinned AGL environment were located by
  read-only inspection.
- A recipe-scoped `bitbake -e flutter-auto` followed by the demo recipe parse
  was started against the current mini-PC dirty branch, not against the clean
  FLR-0022 bundle ref.
- The BitBake client/server remained in config-update wait for more than two
  minutes with negligible CPU and produced no effective `SRC_URI` output.
- Only the client/server processes started by this check were terminated by
  exact PID. No `cleanall`, `cleansstate`, cache deletion, checkout, or reset
  was performed.

### Result

The effective recipe patch list is **UNKNOWN**. The static registration gap
observed in the dirty checkout (available 0041/0044 files not appearing in the
inspected append list) remains a hypothesis until a completed `bitbake -e` or
recipe task log proves the effective `SRC_URI`.

## Build-directory layer gate

### Facts

- A clean detached worktree for the imported FLR-0019 candidate was created on
  the mini PC without changing the dirty canonical checkout.
- The existing build directory's `conf/bblayers.conf` contains only the three
  base Poky layers visible in the file.
- That configuration does not visibly include the AGL layers, the project
  `meta-fluorite-trial` layer, or the external Vulkan layer.

### Inference

The existing build directory is not sufficient evidence for an authoritative
Fluorite/AGL recipe parse. Running BitBake there cannot prove that the imported
candidate's layer, recipe, or patch order is effective. This is a build-config
boundary problem, distinct from the runtime 3D boundary.

### Decision

Do not edit or reuse this configuration for a product build. Create a separate
build directory through the pinned AGL `aglsetup.sh` flow, add the candidate
worktree and locked external layers, verify `bitbake-layers show-layers` and
`bitbake -e` for the target recipe, and keep the existing downloads/sstate/tmp
roles mounted without deletion.

## Candidate AGL layer-graph verification

### Facts

- A separate candidate build directory was generated with the pinned AGL setup
  script for `qemux86-64` using the demo/devel/Flutter feature set.
- `bitbake-layers show-layers` confirmed AGL core/BSP/demo/Flutter layers,
  `meta-vulkan`, and the imported `meta-fluorite-trial` candidate at revision
  `75f49fd`.
- `bitbake -p flutter-auto` and the Fluorite demo recipe parse completed with
  3337 recipes parsed and zero errors.
- Effective `flutter-auto` `SRC_URI` contains the registered 0002–0049 patch
  sequence, including the platform-runner and ECS bootstrap patches, but does
  not contain the available 0041 or 0044 patch files from the separate dirty
  checkout.
- Effective demo `SRC_URI` contains the Dart payload and frame-event patches,
  including 0037.
- The final `DISTRO_FEATURES` did not contain `vulkan` because the project
  `fluorite-common.inc` include was not active in this AGL-generated build
  configuration. Consequently `filament-vk` and `vulkan-loader` were skipped.
- Passing a temporary `DISTRO_FEATURES` value containing `wayland opengl
  vulkan` resolved both dependencies during `bitbake -e`; this was not written
  to the source repository or the existing build directory.
- A recipe-scoped `flutter-auto -c patch` then reached the uninative download
  prerequisite but stalled at a zero-byte external download. The task and the
  exact BitBake server started for it were stopped; the download `.tmp` and
  lock files were not deleted.

### Result

The layer graph and recipe metadata are now proven for the candidate, while
the patch task itself is **NOT CHECKED** because the host lacks the required
uninative download. The missing Vulkan feature activation and unregistered
0041/0044 files are separate integration findings; neither is promoted as a
runtime 3D fix without a completed recipe task and QEMU evidence.

## Bundle handoff result

### Facts

- The fixture/tooling branch is clean at tip `70514babc7667a27169088683d1ae8bca84c2975`.
- The first updated bundle used `origin/main` as its base. The mini-PC
  repository contained the base object but did not have that base as a
  receiver ref, so that bundle was not used for import.
- A replacement bundle was created with the already imported receiver ref
  `826146ed14bca3ba4bb1987dc81072f22a5d5420` as its base.
- The replacement bundle passed local `git bundle verify`, manifest validation,
  and SHA-256 verification with
  `5091468fd5e1c545a8a5371f6e5cad05f4d44c40f4c8fe6afad26c9316946b8f`.
- SCP completed. The mini-PC verified the same SHA-256, passed
  `git bundle verify`, and imported receiver ref
  `feature-flr-0022-devtool-sync-r6` at the exact tip commit.
- The mini-PC's dirty canonical checkout remained on its existing branch with
  its pre-existing tracked and untracked changes; no checkout, reset, merge,
  commit, or source-tree patch application was performed.

### Result

The Mac-to-mini-PC revision handoff is **PASS for the separate receiver ref**.
The dirty canonical checkout is intentionally **NOT SWITCHED**; a build from
the imported ref requires a separately materialized clean worktree/build
directory and the FLR-0024 layer gate before any authoritative BitBake task.
