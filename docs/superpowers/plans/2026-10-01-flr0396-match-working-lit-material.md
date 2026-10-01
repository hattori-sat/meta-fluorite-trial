# FLR-0396 — match the known-positive LIT material on Sequoia

> **Goal:** Make Sequoia use the exact material definition proven by the
> self-created constant-LIT fixture, then prove or reject colored Sequoia output
> in a native-only visual-isolation QMP frame. The separate same-frame
> Sequoia+HUD composition gate is FLR-0398.

**Ticket:** `work/tickets/FLR-0396-match-working-lit-material-on-sequoia.md`
**Branch:** `feature-flr-0396-match-working-lit-material` (local only; no push)
**Base source:** post-0333 Devtool commit `6946d02d61e637dbaf1eb5cbc52bfe3b40b8882e`
**Patch output:** `0334-flr0396-match-working-lit-material-interface-devtool.patch`

## Evidence boundary

- FLR-0394 is a live-QMP positive fixture+HUD control on the exact FLR-0391
  rootfs, not a Sequoia success.
- The fixture retains `.parameter("color", FLOAT3)` and a linear RGB setter
  even when its constant shader branch is selected.
- Patch 0333 copied the constant LIT source to Sequoia but omitted those two
  material-interface operations. Restoring them is a narrow parity experiment;
  it is not yet a root-cause claim.
- FLR-0049 Iteration 23 is a historical production-Sequoia native-only visual
  reference: the native surface was above the Flutter parent, so the HUD was
  masked. Its image is not a matched current-image run.
- The current recipe registers patch 0198 before 0333/0334. Its default
  stacking branch places native above the Flutter parent; the below-parent
  path is opt-in. Keep that existing default and do not set a legacy stacking
  override for FLR-0396.
- The user supplied a 1280x800 same-frame HUD/vehicle-fragment image. It is
  stored as `work/evidence/FLR-0398-user-provided-composition-reference.jpg`
  (SHA-256 `df30ba433b979f631c552328c0db29ef95a8a6dfefe795e3d5976ddd4b4cd3d3`);
  run identity is unavailable. `Shapes: On` and `Colliders: Off` are visible;
  Shape-visualization origin is likely but not proven.
- Keep camera, geometry, model selector, SUN, Flutter widget tree, and renderer
  settings fixed. For FLR-0396 only, use the documented native-above-parent
  presentation so HUD visibility/composition is explicitly not the success
  criterion.

## Task 1 — verify the one active ticket and the fixed Devtool source

- [x] Run `bash scripts/assert-canonical-repository.sh` and
  `scripts/runtime-checkpoint.sh verify --ticket FLR-0396 --log work/logs/2026-10-01-flr0396.md`.
- [x] Confirm only FLR-0396 is `In Progress`; FLR-0395 waits, FLR-0397 remains
  Inbox.
- [x] Use the existing fixed Podman machine/container/state only. The machine
  was already running; sandboxed loopback failure is not a reason to start or
  create another machine. Use the established approved wrapper access.
- [x] Read `devtool-status`. If the component is registered, call only
  `component-reset fluorite-plugins`; immediately reread `devtool-status` and
  use the newly reported attic source path. Do not reuse a path invalidated by
  `devtool reset`.
- [x] Verify the source tree is clean on the exact post-0333 HEAD
  `6946d02d61e637dbaf1eb5cbc52bfe3b40b8882e`. Record the resolved source
  branch and commit, but do not commit host-specific paths.

## Task 2 — edit source and generate official patch 0334

- [x] In `plugins/filament_view/core/systems/derived/model_system.cc`, add
  `.parameter("color", filament::backend::UniformType::FLOAT3)` to the
  Sequoia constant-LIT builder.
- [x] After creating the Sequoia `MaterialInstance`, call
  `setParameter("color", filament::RgbType::LINEAR,
  filament::math::float3{0.05f, 0.45f, 1.0f})` before READY/binding. Preserve
  constant shader source, shading, target/platform, material lifecycle, and
  all-primitive assignment. Change only the READY marker enough to distinguish
  this interface if existing evidence requires it.
- [x] Review the exact Devtool source diff; require one file and only the
  declared parameter/setter (plus the minimal marker if needed). Commit the
  source change on the ticket source branch before updating the recipe.
- [x] Run
  `scripts/rebase-fluorite-devtool-component.sh FLR-0396 fluorite-plugins <current-container-source-path> 6946d02d61e637dbaf1eb5cbc52bfe3b40b8882e <source-commit> layers/meta-fluorite-trial/recipes-graphics/toyota/files/0334-flr0396-match-working-lit-material-interface-devtool.patch layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend ivi-homescreen-plugins`.
- [x] Verify generated patch comes only from official Devtool output, is
  nonempty, has the exact source commit in its `From` header, is registered
  once after 0333, and the layer baseline lock reflects the layer changes.

## Task 3 — commit, bundle, and build on the Mini

- [x] Run privacy, canonical, baseline-lock, and `git diff --check` gates.
- [x] Commit the patch/registration/lock locally on this
  feature branch. Do not push.
- [x] Create and verify one bundle from the current Mini receiver tip through
  the existing handoff helper; transfer to the fixed inbox/receiver only.
- [x] Verify the Mini receiver's exact bundle tip and clean layer state, then
  run progressive `flutter-auto:do_patch`, component compile, and the full
  `agl-ivi-image-flutter` image build. Reuse the fixed build/TMPDIR/caches; do
  not copy the VM image to Mac.
- [x] Record exact new rootfs/kernel/qemuboot hashes and the focused task
  results before QEMU.

## Task 4 — run Sequoia, capture QMP, and clean up

- [x] Check Mini QEMU/process/port/socket state and the exact image hashes.
  Use one fresh QEMU through the existing harness; no Mac QEMU.
- [ ] Verify the registered patch-0198 default-above-parent presentation and
  preserve it; do not set the legacy below-parent override or invent a HUD-off
  flag. Keep Shape/Collider visualization controls fixed and record their
  effective state. Confirm from the live QMP ROI whether the HUD is actually
  absent before calling the frame native-only. The missing live QMP frame means
  this was not verified for FLR-0396.
- [x] Manually launch the existing Example Demo as the established guest user
  with the saved Sequoia LIT/SUN profile. Keep fixture-specific controls off.
  Confirm the marker reports the constant shader plus linear FLOAT3 parameter
  before treating the new branch as selected.
- [x] GDB existed and was armed before Flutter. The raw log was not persisted;
  preserve this as an evidence gap. Retain a bounded kernel Oops/journal window
  independently. Do not assume ptrace can catch a kernel Oops.
- [ ] Capture a complete live 1280×800 QMP frame and short QMP video. Bracket
  capture with exact Flutter PID/UID/start identity. Capture at first
  successful present, or while the process is live at the first useful READY
  point if the renderer faults first. The observer mismatch prevented this.
- [x] Compute ROI counts and hashes for the available post-exit frame and
  visually inspect it. It is uniformly black, but is not live evidence and
  cannot satisfy colored-Sequoia acceptance or classify the presentation.
- [x] Stop the exact Flutter process and QEMU. Independently verify no
  QEMU/runqemu/flutter-auto process, QMP socket, or forwarded-port residue.
- [x] Save ignored media outside Git and add a tracked manifest with exact
  checksums, runtime counters, faults, and cleanup results. Update PDCA and
  `TASKS.md`; the final ticket close-out is committed locally.

## Close-out

- [x] Run canonical guard, checkpoint verifier, privacy check, diff check, and
  full `make verify`. The actual verifier result is 147/148, NOT PASS; keep
  FLR-0397's stale test separate.
- [x] Commit local ticket/evidence updates. No push.
- [x] Close this as a bounded material-parity experiment with live visual
  outcome UNKNOWN. The post-exit black frame is not a negative live render
  result. FLR-0399 owns a new exact-0334 live-capture/first-fault observation;
  no texture/camera/light/composition changes are justified here.
- [ ] If the native-only Sequoia gate passes, FLR-0398 owns a separate same-image
  test with the Flutter HUD visible and composition active.
