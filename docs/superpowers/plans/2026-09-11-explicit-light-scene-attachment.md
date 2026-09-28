# Isolate explicit-light Scene attachment boundary

> **For the implementation agent:** REQUIRED SUB-SKILL: Use the `executing-plans` skill to implement this plan task-by-task with review checkpoints.

**Goal:** determine whether adding an explicitly built Filament light entity
to the Scene is the first operation that makes the production 3D target
black, while preserving a reproducible Mac Devtool → Mini Yocto → QMP loop.

**Architecture:** add one opt-in diagnostic environment variable in the
persistent Mac Devtool source. `BuildLightAndAddToScene` still builds and
configures the light, but conditionally skips only `Scene::addEntity`. The
official Yocto Devtool flow materializes the patch into
`meta-fluorite-trial`; the Mini remains authoritative for BitBake, image
artifacts, QEMU, and QMP evidence.

**Tech stack:** C++, Filament, Yocto/BitBake, `devtool`, Podman bind mount,
QEMU, QMP, PPM analysis, Git bundle.

## Task 1: establish the ticket and fixed baseline

- Confirm the canonical repository and clean unrelated worktree state.
- Read FLR-0067 and FLR-0077 runtime evidence, including the exact one-light
  launch variables, image hashes, and QMP region definitions.
- Confirm the existing Podman machine and container are reused. A second
  machine, container, named project volume, or temporary workspace is not
  allowed.
- Run the wrapper's canonical-path, ownership-marker, and stale-process
  preflight. Do not begin a Devtool operation while an earlier BitBake server
  or Devtool process remains.
- Record facts, inferences, hypotheses, unknowns, and the fixed baseline in
  the FLR-0078 ticket and working log.

## Task 2: edit the persistent Mac Devtool source

- Inspect `plugins/filament_view/core/systems/derived/light_system.cc` and
  verify the `BuildLight` → `AddLightToScene` call order.
- Add the opt-in variable
  `FLR0026_NATIVE_LIGHT_SKIP_SCENE_ADD`.
- Keep the default path unchanged. When operation tracing is enabled, emit
  bounded markers for build begin, build completion, Scene-add skipped, or
  Scene-add completed. Do not add an unbounded per-frame log.
- Run the source diff check and the focused source repository test/status
  checks. Commit the source change in the Devtool source repository with a
  file-scoped message.

## Task 3: create the official Yocto patch on Mac

- Reuse the existing Devtool state and container.
- If the split component is not active in Devtool, create a fresh baseline
  branch at `32f4fab`, run official `component-add`, then create a source branch
  at the reviewed source commit before `update-recipe`.
- Use the project’s documented Yocto Devtool split-component procedure to
  generate/update the recipe patch. Do not hand-create or hand-edit the patch
  body.
- Register the generated patch after the existing diagnostic patch in the
  `flutter-auto_2.0.bbappend` order.
- Verify the generated patch corresponds exactly to the source diff and that
  `devtool status`/recipe parse show the expected workspace and patch list.
- Commit the layer change in the canonical repository after `make verify`.

## Task 4: bundle and run progressive Mini gates

- Create a Git bundle from the committed canonical tip and transfer it with
  `scripts/handoff-fluorite-bundle.sh` to the fixed receiver.
- Confirm the receiver reaches the exact commit and record bundle and commit
  hashes.
- On the Mini, run the smallest safe gates in order: recipe `do_patch`,
  `do_compile` for the changed component, then the full
  `agl-ivi-image-flutter` build. Do not clean Yocto caches or create a second
  build/TMPDIR.
- Record rootfs, kernel, qemuboot, and artifact-index hashes before QEMU.

## Task 5: execute the one-light QMP A/B

- Use one QEMU at a time, the fixed guest launch contract, and the same
  owner-isolated Wayland profile for both runs.
- Control A: attachment enabled (default diagnostic behavior).
- Control B: set only `FLR0026_NATIVE_LIGHT_SKIP_SCENE_ADD=1`.
- Capture QMP-only screenshots, runtime marker excerpts, frame hashes,
  candidate-region counts/bounding boxes, HUD counts, application liveness,
  negotiated QMP quit, and residual-process/socket checks.
- Preserve invalid launch attempts and failure logs under the ticket evidence
  root with an explicit invalid/failed classification.

## Task 6: classify and split

- If disabling only Scene attachment changes the result from zero to a
  recognizable model, classify the boundary as Scene-attachment-side.
- If both A/B remain zero with healthy markers, classify construction or
  light/material/resource state as unresolved and open the next smallest
  ticket.
- If gates, liveness, or cleanup differ, classify as UNKNOWN and fix the
  harness/process issue before making a rendering claim.
- Update TASKS, ticket, and working log; commit documentation and generated
  layer changes together only when each is independently verified.
