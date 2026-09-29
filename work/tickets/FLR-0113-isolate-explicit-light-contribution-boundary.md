# FLR-0113 — isolate explicit-light contribution boundary

- Status: Waiting
- Priority: High
- Owner: Mac Devtool source + Mini authoritative runtime roles
- Created: 2026-09-12
- Updated: 2026-09-12
- Depends on: [FLR-0112](FLR-0112-qmp-black-pixel-classification.md), [FLR-0078](FLR-0078-isolate-light-scene-attachment-boundary.md)
- Working log: `work/logs/2026-09-12-flr0113.md`

## Work unit

Separate explicit-light **entity/Scene participation** from explicit-light
**direct contribution**. Keep the normal `BuildLight` and `Scene::addEntity`
path active, and add one opt-in runtime control that changes only the
Filament `castLight` value. This is a diagnostic boundary, not a production
default change.

## Problem

On the fixed current image, the Sequoia model is visible when explicit lights
are skipped (`4905/223200`) and remains black when explicit lights are enabled
(`0/223200`). One-light tests for GUID 126 and 128 also remained black. Shadow
casting was disabled in an earlier diagnostic without restoring the model.
The remaining question is whether direct-light contribution triggers the
failure, or whether merely creating/registering light entities changes a later
resource, target, or present path.

## Success criteria

- [x] Inspect the existing source and confirm the diagnostic changes only the
  `LightManager::Builder::castLight` input.
- [x] Edit the persistent Mac Devtool source, not a generated patch body.
- [x] Generate the first recipe patch through the official Yocto Devtool flow
  and preserve it as historical evidence.
- [x] Regenerate the diagnostic against the current
  `vBuildLightAndAddToScene`/`vBuildLight` API and register only the current
  source patch.
- [ ] Commit the layer change to the canonical feature branch and keep
  the source commit and patch SHA-256 in the working log.
- [x] Transfer a self-contained bundle for the committed layer to the fixed
  Mini receiver inbox and verify its SHA-256 and Git prerequisites.
- [ ] Update the fixed Mini receiver to the exact tip after its existing
  user changes are preserved or explicitly cleared; pass `do_patch`,
  component compile, and full image build.
- [ ] Run one fixed-image, one-owner QMP A/B: default direct contribution
  versus `FLUORITE_NATIVE_LIGHT_DISABLE_CONTRIBUTION=1`.
- [ ] Preserve QMP-only frames, videos, native readback result if available,
  markers, hashes, failed attempts, and exact QMP teardown.
- [ ] Classify the boundary as direct-light/material interaction,
  light-entity/Scene participation, or UNKNOWN. Do not call a nonzero metric
  alone a recognizable production 3D success.

## Facts

- FLR-0067 held `DEFAULT` indirect light and skybox skip/clear constant. The
  explicit-light-enabled case was `0/223200`; the light-skipped case was
  `4905/223200`, with model, camera, submit/present, QMP, and teardown evidence.
- FLR-0068 and FLR-0069 showed that GUID 126 and GUID 128 alone each remained
  at `0/223200` under their respective fixed one-light profiles.
- FLR-0048 showed that disabling shadow casting did not restore the model at
  the historical failing light-count boundary.
- Current source performs `BuildLight(light)` followed by `AddLightToScene`
  and `AddLightToScene` calls `scene->addEntity(...)`.
- Current source sends `light.getCastLight()` directly to
  `LightManager::Builder::castLight(...)`.
- The normal default path must remain unchanged when the diagnostic variable
  is absent.
- The historical persistent Devtool source commit is `7774c04`, changing only
  `plugins/filament_view/core/systems/derived/light_system.cc`.
- Official `update-recipe --mode patch --append --no-remove` generated
  `0003-diag-isolate-explicit-light-contribution.patch`. The canonical layer
  copy is `0211-diag-isolate-explicit-light-contribution-devtool.patch` with
  SHA-256
  `f853fb52cba3f13bc4f91fc493aa80a1ebbd3733c1c9a6995d2b23b4b5c0fc5e`.
- The historical generated patch changes only the `castLight` input and its
  opt-in log. It is no longer registered because the current plugin API uses
  `vBuildLight` and the old patch preimage is not applicable.
- The current nested plugin source was edited on Devtool branch
  `devtool-flr0113-light-0229` and committed as `cfad393`. The generated
  current-API patch `0229-diag-isolate-explicit-light-contribution-current-plugin-devtool.patch`
  has SHA-256
  `da5c03fa5839084f09688d0c7e678481d144672fcb60972f299a35b09a07c633`.
  It changes only `LightSystem::vBuildLight()` and adds the `<cstdlib>` include.
- The official `devtool update-recipe` command was run after reconnecting the
  source with `modify --no-extract`; it reported no parent-recipe files to
  update because `ivi-homescreen-plugins` is a separate `SRC_URI` Git source.
  The untouched patch was therefore materialized from that Devtool-managed
  nested Git commit and registered with the recipe's existing `patchdir`.
- After `component-reset --no-clean` removed the temporary `EXTERNALSRC`
  connection, the normal Mac `flutter-auto:do_patch` gate applied `0229` and
  passed all 104 tasks with no patch-fuzz QA error.
- The fixed Mini preflight found one old QEMU instance from a prior run and a
  dirty receiver with tracked and untracked user changes. The QEMU was
  stopped through its recorded QMP socket and the final residual check passed.
  The receiver was not overwritten or checked out.
- The first range bundle transfer was rejected by the Mini's Git because its
  receiver lacked prerequisite commit `530d691`. The same single bundle was
  regenerated as a complete-history bundle, transferred again, and passed
  remote SHA-256 and `git bundle verify`. Its current SHA-256 is recorded in
  the working log outside the repository handoff state.
- FLR-0114 reconciled the inherited recipe baseline and the current patch gate
  now passes. The next implementation step is a current-API Devtool patch,
  not force-applying historical 0211.
- Restarting the reused container exposed a wrapper defect: the disposable
  `/workspace/tmp/work` directory was not recreated before the `status` FIFO
  probe. The wrapper now recreates that directory without touching the
  bind-mounted Yocto state.
- The shared image already inherits the project-owned
  `packagegroup-fluorite-runtime-debug` from FLR-0104. That packagegroup
  explicitly provides GDB, `coredumpctl` through systemd, `llvm-symbolizer`
  through clang, and the targeted graphics/runtime debug packages. The
  previous exact guest image passed the tool probe; the new 0113 image still
  needs a fresh build before its tool presence can be called current-tip
  evidence.
- The first post-registration Mac `do_patch` retry failed before reaching the
  0211 patch: the existing `meta-flutter` patch
  `0001-diag-probe-Flutter-parent-alpha-before-present.patch` rejected hunk 3
  in `shell/backend/wayland_vulkan/wayland_vulkan.cc`. This is a recipe
  baseline/patch-stack failure, not evidence against the 0113 source change.
- A local Git bundle for the current layer tip was created from the last
  transferred FLR-0104 evidence tip and verified successfully. The bundle
  requires base `530d691b86f29f8d425301ea449f3e36cf1651b7`, carries tip
  `2aab0672af20db80756fe1fea4352c295123bbaa`, and has SHA-256
  `bebbfb54a03d696026451f515aa786eba84f16e1c68677028e3f31f0f3049b47`.

## Ranked hypotheses and falsifiers

1. **Direct-light contribution interacts with shaded material/resource work.**
   If disabling only `castLight` restores recognizable model pixels while the
   light entity remains valid and in the Scene, this boundary is supported.
2. **Light entity or Scene participation is sufficient to trigger the failure.**
   If the contribution-disabled case remains black with the same valid light
   entity/Scene counts, the failure is not the direct-light contribution alone.
3. **The A/B is still below the true failing boundary.** If runtime markers,
   readback, or QMP identity differ before the controlled variable is applied,
   classify UNKNOWN and split a smaller output/material task.

## Plan / Do / Check / Act

### Plan

1. Verify the persistent Devtool source and existing container/mount contract.
2. Add the opt-in `castLight` diagnostic to the source file only.
3. Commit that source file through the bounded source-Git operation.
4. Run official Devtool patch generation, register the unchanged patch in the
   canonical layer, and commit the layer.
5. Bundle to Mini and pass progressive build gates before runtime.
6. Run the fixed A/B with QMP-only evidence and synchronized native readback.

### Do

- Ticket created after the FLR-0112 condition matrix identified explicit-light
  participation as the first stable difference.
- Source edit and historical Devtool patch generation: PASS.
- Current-API patch regeneration and Mac `do_patch`: PASS.
- Layer commit and self-contained bundle transfer: PASS.
- Mini receiver checkout, build, and runtime A/B: Waiting on preservation or
  explicit cleanup of the receiver's existing changes.

### Check

- Source default behavior: pending.
- Historical patch provenance: PASS. Current-API patch provenance and layer
  registration: pending.
- Reused Podman machine/container status after the restart-safe wrapper fix:
  PASS.
- FLR-0104 debug-tool prerequisite on the prior exact image: PASS; current
  0113 image tool probe: pending until the patch-stack failure is resolved.
- Local layer bundle creation/verification: PASS; Mini transfer and
  authoritative build: pending.
- Mini `do_patch`/compile/full image: pending.
- QMP/native-readback A/B and cleanup: pending.

### Act

- Keep the diagnostic opt-in until a fixed-image A/B classifies the boundary.
- If direct-light contribution is causal, create a separate production-fix
  ticket after inspecting the actual light/material contract.
- If contribution is not causal, resume FLR-0078 or split the output-target
  boundary; do not broaden this ticket with compositor or camera changes.

## UNKNOWN

- Whether `castLight=false` preserves the exact Filament light/resource state
  needed to isolate direct contribution.
- Whether the full-production target contains geometry before final QMP.
- Whether the one-off trace-visible frame was caused by this operation or by
  an unrelated timing condition.

## Evidence locations

- Mini evidence root: `$QEMU_EVIDENCE_ROOT/flr0113`
- Layer patch: `layers/meta-fluorite-trial/recipes-graphics/toyota/files/`
- Working log: `work/logs/2026-09-12-flr0113.md`
