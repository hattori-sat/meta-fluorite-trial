# FLR-0120 Camera API Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with review checkpoints.

**Goal:** Deliver the self-made Flutter Auto 3D fixture's initial camera state to native Filament before scene initialization and prove visible geometry in the QMP framebuffer.

**Architecture:** Keep the existing ECS initialization and scene-deserialization path, but register the generated `FilamentViewApi` handlers before the asynchronous scene load can trigger Dart camera calls. Compare the native reorder against a Dart readiness/replay gate, then validate the selected boundary through the fixed Mac Devtool → layer commit → bundle → Mini BitBake → one-QEMU QMP loop.

**Tech Stack:** Yocto/OpenEmbedded, BitBake, `devtool`, C++ Flutter desktop plugin, Dart fixture demo, rootful Podman, QEMU QMP, Git bundles.

**Spec:** `work/tickets/FLR-0120-register-filament-camera-api-before-fixture-init.md`

## Global Constraints

- Edit only the persistent Mac Devtool source; never edit `tmp/work`, a Mini build tree, or a generated patch body.
- Reuse `fluorite-mac-devtool`, `/tmp/fluorite-mac-devtool-state`, the fixed Mini receiver, and the existing build/TMPDIR/cache.
- Generate the layer patch with the official Yocto Devtool update boundary for the split component, then copy it unchanged into `layers/meta-fluorite-trial`.
- Keep exactly one `In Progress` Markdown ticket and exactly one QEMU instance.
- Use QMP-only screenshots for pixel claims and terminate the recorded QEMU with negotiated QMP `quit`.
- Do not delete downloads, sstate-cache, active TMPDIR, evidence, or deploy artifacts.
- Commit locally; do not push.

---

### Task 1: Establish the pre-change red-capable fixture gate

**Files:**
- Read: `work/tickets/FLR-0119-fix-ecs-platform-channel-init-race.md`
- Read: `work/logs/2026-09-13-flr0120.md`
- Read: `layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend`
- Read: `/tmp/fluorite-mac-devtool-state/build/workspace/sources/fluorite-plugins/plugins/filament_view/filament_view_plugin.cc`

**Interfaces:**
- Consumes: FLR-0119 image identity and QMP evidence showing camera `channel-error` plus central black pixels.
- Produces: a source/order baseline and one falsifiable acceptance signal for FLR-0120.

- [x] Confirm the current source order is `DeserializeDataAndSetupMessageChannels` before `FilamentViewApi::SetUp` and confirm the two camera channel errors in the predecessor evidence.
- [x] Compare the native reorder with a Dart readiness/replay gate. Select native reorder because it changes one native initialization boundary and preserves the public Dart API; reject it if plugin lifetime or registrar ownership proves unsafe.
- [x] Define the falsifier: if both camera calls are delivered after the change but `[300,250,620,400]` remains black, camera delivery is not sufficient and the ticket must remain non-successful.

### Task 2: Apply and commit the minimal native source change in Devtool

**Files:**
- Modify: `/tmp/fluorite-mac-devtool-state/build/workspace/sources/fluorite-plugins/plugins/filament_view/filament_view_plugin.cc`
- Generate: `/tmp/fluorite-mac-devtool-state/build/workspace/appends/fluorite-plugins-camera-order/0001-*.patch`

**Interfaces:**
- Consumes: the post-FLR-0119 Devtool source baseline.
- Produces: one source commit containing only the registration-order change and one official Devtool-generated patch.

- [ ] Move construction of `FilamentViewPlugin`, `FilamentViewApi::SetUp`, `registrar->AddPlugin`, and `setupMessageChannels` before `DeserializeDataAndSetupMessageChannels` while retaining the existing first-registration guard.
- [ ] Run the source Git whitespace check and inspect the diff to confirm no generated files or unrelated diagnostics changed.
- [ ] Commit the source file through the wrapper with a message identifying camera API registration ordering.
- [ ] Use the split-component official Devtool update path to materialize the patch; do not edit its body, hunk offsets, or headers.
- [ ] Record the source commit, generated patch path, patch SHA-256, and Mac recipe-task result in FLR-0120.

### Task 3: Register the untouched patch and create the canonical checkpoint

**Files:**
- Create: `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0232-register-filament-camera-api-before-fixture-init-devtool.patch`
- Modify: `layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend`
- Modify: `work/tickets/FLR-0120-register-filament-camera-api-before-fixture-init.md`
- Modify: `work/logs/2026-09-13-flr0120.md`
- Modify: `TASKS.md`

**Interfaces:**
- Consumes: the exact official Devtool patch from Task 2.
- Produces: a reproducible canonical layer revision ready for bundle transfer.

- [ ] Copy the generated patch byte-for-byte under the recipe `files/` directory and register it after patch 0231 with the existing `patchdir` contract.
- [ ] Run the repository guard, privacy check, `git diff --check`, and `make verify`; refresh only the authorized baseline lock if the tracked-file count changes.
- [ ] Run the Mac `flutter-auto do_patch` gate in the fixed container and record the result.
- [ ] Commit the patch, registration, ticket, log, and verification metadata as one FLR-0120 checkpoint.

### Task 4: Transfer the exact layer commit and build authoritatively on Mini PC

**Files:**
- Evidence outside Git: `$EVIDENCE_ROOT/flr0120-<tip>/`

**Interfaces:**
- Consumes: the canonical FLR-0120 layer commit and its predecessor commit.
- Produces: exact receiver revision, effective metadata, task results, artifact checksums.

- [ ] Create and verify one complete-history bundle from `bbdcd607a510ee4d07381ce09fdb679baa063274` to the new tip.
- [ ] Transfer it to the fixed receiver and confirm the receiver is exactly at the tip with a clean status.
- [ ] Capture `bitbake -e` identity and resolved `SRC_URI` before mutation.
- [ ] Run `flutter-auto:do_patch`, `flutter-auto:do_compile`, and the full `agl-ivi-image-flutter` build in order using the existing build/TMPDIR.
- [ ] Record rootfs, kernel, qemuboot, and patch checksums; stop on the first failure.

### Task 5: Validate camera delivery and visible 3D pixels in one QEMU run

**Files:**
- Evidence outside Git: `$EVIDENCE_ROOT/flr0120-<tip>/qemu/`
- Modify: `work/tickets/FLR-0120-register-filament-camera-api-before-fixture-init.md`
- Modify: `work/logs/2026-09-13-flr0120.md`

**Interfaces:**
- Consumes: the exact Mini-built image and the source-selected minimal fixture.
- Produces: runtime logs, coredump status, QMP-only early/late frames, pixel analysis, and teardown evidence.

- [ ] Start exactly one official QEMU instance and launch only the source-selected fixture with the recorded Wayland environment.
- [ ] Confirm the fixture remains alive, both camera calls have no `channel-error`, camera target/dolly delivery markers exist, frame/submit/present markers exist, and coredump remains empty.
- [ ] Capture QMP-only framebuffer evidence and require nonzero geometry in `[300,250,620,400]`; HUD-only pixels do not satisfy the gate.
- [ ] Send QMP `quit`, wait for exit and socket removal, and verify zero residual QEMU/app/compositor targets.
- [ ] If camera delivery succeeds but geometry remains black, record that result and split the next independent boundary into a new ticket instead of claiming completion.

### Task 6: Close the ticket boundary and preserve the next experiment

**Files:**
- Modify: `work/tickets/FLR-0120-register-filament-camera-api-before-fixture-init.md`
- Modify: `work/logs/2026-09-13-flr0120.md`
- Modify: `TASKS.md`

**Interfaces:**
- Consumes: all Task 5 evidence and the completion checker result.
- Produces: a Done or Waiting ticket with explicit Facts/Inferences/Hypotheses/UNKNOWN and a new ticket for any remaining display boundary.

- [ ] Run the applicable verification-before-completion checks and independently review scope, privacy, evidence identity, and unresolved UNKNOWNs.
- [ ] Set FLR-0120 to Done only if camera delivery and central QMP geometry both pass; otherwise set it to Waiting with the first remaining divergence.
- [ ] Create the next Markdown ticket before starting any new hypothesis, such as surface alpha/compositor stacking, production scene transition, or QEMU input routing.

