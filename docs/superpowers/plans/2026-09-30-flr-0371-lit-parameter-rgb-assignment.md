# FLR-0371 LIT Parameter RGB Assignment Implementation Plan

> **For agentic workers:** Execute inline with review checkpoints using the
> `executing-plans` skill. Mark each checkbox after its evidence gate passes.

**Goal:** Render the self-made LIT/SUN fixture from its runtime color parameter
while preserving the 2D Flutter HUD in one QMP frame.

**Architecture:** Reuse the current recipe's committed patch stack through the
existing persistent Mac Podman Devtool container. Because the native plugin
is a separate nested Git `SRC_URI`, import the exact Mini post-`do_patch`
plugin source as a Devtool baseline, register it with official
component-scoped `devtool add`, change only the parameter branch's GLSL
assignment, and generate the patch with official `devtool update-recipe`.
Build on the Mini PC from a Git bundle. Start Flutter manually over strict
guest SSH and judge the result from full-frame QMP evidence, not boot or
process liveness.

**Tech Stack:** Yocto/OpenEmbedded Devtool, Podman, Git, BitBake, Mini PC
receiver/build, QEMU, SSH, QMP, PNG/MP4 evidence.

**Spec:** [FLR-0371 ticket](../../../work/tickets/FLR-0371-lit-parameter-rgb-assignment.md)

## Global Constraints

- Use one existing Podman container, its existing project bind, source state,
  downloads, sstate, TMPDIR, Mini receiver, and Mini build directory.
- Never run Docker, initialize another Podman machine/container, create another
  source checkout, or delete caches/deploy evidence.
- Do not edit a shell launcher, `tmp/work`, or any generated patch body.
- The only source behavior change is parameter assignment to
  `material.baseColor.rgb`; all fixture, LIT/SUN, camera, setter, and runtime
  inputs stay fixed.
- Use local feature branches and role-only commit identity. Do not push or
  cherry-pick.
- For runtime acceptance, manually SSH as the guest runtime role and launch
  exactly one `/usr/bin/flutter-auto`; screenshots must be QMP-only.
- Keep the existing mounted worktree's original branch
  `devtool-flr-0371-mount` at `a3e779976d5dc74b777918d151835cf4c14cfd57`
  untouched. Create a separate local layer-work branch for the generated
  patch commit; return the mounted checkout to its original branch and clean
  state after the active feature branch is fast-forwarded.
- Do not edit runtime/app-launch scripts during this experiment. First run the
  proven manual procedure on the candidate image and retain the exact command,
  readiness gate, output, and QMP evidence. Script automation can be proposed
  only after repeated manual success and in a separate ticket.
- Never run `bitbake -c cleanall`; do not use `cleansstate` or delete shared
  downloads, sstate, active TMPDIR, or evidence.

---

## File and workspace map

- Devtool source (persistent workspace):
  `/workspace/state/build/workspace/sources/fluorite-plugins`, the existing
  fixed source path. Its current contents are incomplete. Rehydrate it in
  place from Mini's exact post-`do_patch` nested plugin source at
  `PLUGINS_COMMIT=2163242e9973336153871ed63b34bb5ed8282145`; exclude only
  Quilt-generated `.pc/` and root `patches/` metadata. Commit the effective
  source as baseline, then use official `component-add` for recipe
  `fluorite-plugins`. Do not retry parent recipe `modify flutter-auto`.
- Generated layer artifact:
  `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0330-flr0371-lit-parameter-rgb-assignment-devtool.patch`
- Registration:
  `layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend`
- Work record: `TASKS.md`, the FLR-0371 ticket, and its dated working log.
- Existing-image manual control output: QMP PPM SHA-256
  `65ccb48597d2f227bd80c9dab23a541a6a79feba6fc4d7b8bbb2cbf1312aed07`, with
  8-frame QMP video SHA-256
  `bb2389c55c7ca927f52d43513ed8d2b393b2d2be8d9f6984cf21eac6825b06cf`.
  Original QMP captures remain on the Mini under
  `$BUILD_EVIDENCE/flr0371-0001/qemu/`; local previews are temporary and are
  not Git inputs.
- The existing container mounts a sibling worktree that shares this
  repository's Git common directory. Its project layer was compared with the
  active FLR-0371 commit and is identical. Run Devtool there. Keep its original
  branch at the recorded commit; commit the generated layer change on a new
  local branch, fast-forward the active feature branch, then switch the mount
  back to the original branch and verify it is clean.

## Task 1: Verify the mounted checkout before using Devtool

**Files:** no source edits.

- [x] Confirm the active branch is
  `feature-flr-0371-lit-parameter-rgb-assignment` and its starting commit is
  `a3e7799`.
- [x] Confirm the existing Podman container is running and its project bind is
  a different, clean worktree sharing the same Git common directory.
- [x] Compare all `layers/meta-fluorite-trial` files between the mounted
  worktree and commit `a3e7799`; result: identical.
- [x] Record the mounted worktree's original branch and full HEAD in the
  working log. Confirm its status is clean and that the mounted copies of
  `run-podman-devtool.sh` and `finish-fluorite-devtool-patch.sh` match the
  active committed revisions.
- [x] Reuse the already-existing temporary local branch in the mounted
  worktree at `a3e7799`; it was clean, so no duplicate branch was created.

## Task 2: Materialize and verify the split-component Devtool baseline

**Files:** existing persistent Devtool state only; no tracked source edits yet.

- [x] Official recipe-level `modify flutter-auto` was attempted once and
  stopped at the nested-source Git commit for existing patch 0013. Do not
  retry; its failure boundary and source identity are recorded in the log.
- [x] Mini's fixed recipe gate performed recipe-scoped clean and current
  `do_patch` passed at the pinned source pair and exact canonical layer tree.
- [x] Rehydrate the existing fixed `fluorite-plugins` path from Mini's fresh
  effective nested source, excluding only Quilt metadata. Do not create a
  second temporary or source workspace.
- [x] Preserve upstream base `2163242...`, commit the patch-applied plugin
  tree as the Devtool baseline, then run official `component-add
  fluorite-plugins <source-tree>`. The complete source/index count is 478;
  the effective recipe changes 16 tracked source files and current
  registration includes patch stack through 0327.
- [x] Confirm `devtool status` contains exactly the component/source pair and
  the baseline tree is clean before editing.

## Task 3: Make the one-line source change and generate the official patch

**Files:** Devtool source `plugins/filament_view/core/scene/view_target.cc`.

- [x] Keep the existing dynamic parameter expression and change only:

  ```cpp
  "  material.baseColor = vec4(materialParams.color, 1.0);"
  ```

  to:

  ```cpp
  "  material.baseColor.rgb = materialParams.color;"
  ```

- [x] Verify the Devtool source diff is exactly this one assignment line; run
  the source repository's whitespace check.
- [x] Stage and commit the changed source file in the existing Devtool Git with
  the role-only identity. Confirm the commit's parent is the complete
  patch-applied baseline. Baseline `599bf4ea…`, source commit `7548f28b…`.
- [x] Run `scripts/rebase-fluorite-devtool-component.sh` with the exact
  baseline and source commit IDs. It performs official component reset/add and
  `devtool update-recipe --mode patch --append --no-remove`, selects the patch
  matching the source commit, and copies/registers it unchanged exactly once
  in the 2.0 bbappend. Never hand-author the patch.
- [x] Verify patch header, exact source path, single assignment delta, patch
  SHA-256 (`069420d5…`), and ordered `SRC_URI`. Never edit the generated patch
  text. First helper attempt stopped safely at a branch precondition; correcting
  branch ancestry made the same helper pass without losing the source commit.

## Task 4: Validate and commit the mounted feature branch, then fast-forward

**Files:** the generated patch and
`layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend`.

- [x] Run privacy, staged whitespace, and patch-registration checks. Commit
  only the generated patch, its registration, and refreshed baseline lock on
  the separate local layer-work branch; preserve `devtool-flr-0371-mount` at
  its original commit. Layer-only commit:
  `0e8aa99190a248784ab811bfe0008d2d0827db79` (role identity corrected after
  privacy gate; tree and parent are unchanged).
- [x] From the active FLR-0371 worktree, fast-forward its branch to that local
  commit (no cherry-pick). Verify the layer patch bytes and registration are
  identical in both worktrees.
- [x] Restore the mounted project worktree to its recorded original branch and
  verify its original commit/clean status. Retain the new feature commit in the
  shared Git history.

## Task 5: Transfer and build on the authoritative Mini PC

**Files:** no additional source edits; one bundle and external build evidence.

- [ ] Create a bundle from the verified pre-change base to the FLR-0371 feature
  tip; verify the bundle and SHA-256 before transfer to the fixed receiver.
- [ ] Confirm the receiver checks out the exact feature tip and that the active
  Mini `MACHINE`, `DISTRO`, `BBLAYERS`, recipe `SRC_URI`, `DL_DIR`,
  `SSTATE_DIR`, and `TMPDIR` match the recorded build profile.
- [ ] Record free disk space and expected build duration before the long image
  build. Preserve all caches and prior artifacts.
- [ ] Run the target recipe `do_patch`, `do_compile`, and
  `agl-ivi-image-flutter` in order. Stop at the first failure; record task log
  identity and the produced rootfs/kernel/qemuboot checksums.

## Task 6: Manually launch Flutter and verify QMP pixels

**Files:** one ticket-scoped QMP PNG, short MP4, and selected-log summary.

The existing-image LIT/constant-color control was replayed manually before
building this candidate. This directly proved the SSH→Flutter→present→QMP
procedure and displayed the fixture with HUD in one frame. It is not the
RGB-assignment result and does not satisfy the new-image acceptance gate; see
the working log. No launch script was changed.

- [ ] Confirm the exact new image hashes, free QEMU slot, strict guest SSH,
  Example Demo bundle, Wayland socket, and zero stale Flutter processes.
- [ ] Start one QEMU using the approved existing QEMU procedure. Over strict
  guest SSH, manually start exactly one `/usr/bin/flutter-auto` as
  `agl-driver` with the FLR-0367 fixture profile. Keep
  `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR` unset and preserve LIT/SUN.
- [ ] Verify the startup/material branch, SUN, geometry, camera, and present
  markers. Capture only selected marker counts/hash; do not stream or copy the
  repeated full log.
- [ ] At the first decisive frame or no later than 8 completed presents/45s,
  capture a full-frame 1280×800 QMP screenshot and short QMP video. Inspect the
  entire image and report native ROI `(440,220,400,360)` and HUD ROI
  `(1120,0,160,80)` separately.
- [ ] Immediately stop the recorded Flutter PID after capture, before evidence
  transfer/conversion. If it exited first, inspect bounded guest journal,
  kernel, and coredump records; record UNKNOWN if exit cause is not provable.
- [ ] Send QMP `quit` only to the recorded QEMU socket. Independently verify
  zero run-owned QEMU/runqemu/flutter-auto processes, socket, and ports.

## Task 7: Decide the ticket and create the next unit

- [ ] If RGB-only parameter assignment shows visible geometry with HUD under
  LIT/SUN, preserve it and open a separate production Sequoia same-frame test;
  do not claim production success.
- [ ] If it remains black while constant LIT stays positive, record the
  falsification and open a separate parameter-binding/shader discriminator.
- [ ] Attach the full-frame QMP PNG and short MP4, checksums, runtime identity,
  facts/inferences/hypotheses/UNKNOWN, and all failed commands to FLR-0371.
- [ ] Run checkpoint, privacy, whitespace, file-size, and link checks; commit
  the verified records locally. Do not push.

## Self-review

- The plan covers the exact one-line hypothesis test, official Devtool patch
  generation, mounted-worktree identity, Mini build, manual Flutter runtime,
  full QMP visual check, immediate app stop, and QEMU teardown.
- No generated patch is hand-edited; no image build runs on Mac; no launcher
  script is changed; no protected cache or evidence is deleted.
- The acceptance gate distinguishes fixture pixels from production Sequoia
  acceptance and requires a real QMP frame, not process startup alone.
