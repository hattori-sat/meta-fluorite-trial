# FLR-0385 — transfer the proven LIT material to Sequoia: Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with the checks below. Keep the top-level 3D objective active unless a complete QMP frame proves success.

**Goal:** Apply the already QMP-proven parameterized LIT material to every selected production Sequoia primitive and determine whether colored Sequoia and the CPU/GPU HUD appear together.

**Architecture:** Preserve the existing opt-in all-primitive Sequoia material seam and replace its UNLIT material definition with the FLR-0371 LIT/RGB definition. Build and run through the existing Devtool → committed layer patch → Git bundle → Mini BitBake → manual Flutter/QMP flow. Run material-only profile A first; if still black with a healthy live app, use the existing SUN opt-in for profile B without changing any other input.

**Tech Stack:** C++ / Filament `MaterialBuilder` and `ModelSystem`; Yocto Devtool; `meta-fluorite-trial`; Git bundle; Mini BitBake; QEMU `runqemu`; manual `flutter-auto`; QMP framebuffer capture.

**Spec:** `work/tickets/FLR-0385-apply-lit-material-to-sequoia.md`

## Global Constraints

- Mac's existing Podman Devtool container/source state is the only patch-generation workspace; do not create another container, machine, source tree, volume, TMPDIR, or local index file.
- Mini is the authoritative BitBake/image-build host. Transfer only a verified Git bundle; never copy a QEMU disk image to Mac; do not push.
- Preserve downloads, sstate, TMPDIR, and deploy artifacts. Do not run `cleanall`, `cleansstate`, broad cleanup, or change branches/SRCREV outside this ticket.
- Generated patches come only from official Devtool. Never hand-edit a `.patch`, synthesize one with `format-patch`, or use a different source baseline.
- Keep camera, transform, GLB, texture, HUD/surface, route, renderer, and launch scripts unchanged. No override means unchanged production behavior.
- Keep exactly one `In Progress` ticket. Record facts, inferences, hypotheses, UNKNOWN, commands, results, failures, and evidence in the ticket and dated working log.
- Use one QEMU, one 6144 MiB memory profile, one run directory `flr0385-0001`, manually launched Flutter as `agl-driver`, and full-frame QMP screenshots plus short QMP videos. Preserve raw captures/logs on Mini and verify teardown independently.

---

### Task 1: Establish the ticket and local feature baseline

**Files:**
- Create: `work/tickets/FLR-0385-apply-lit-material-to-sequoia.md`
- Create: `work/logs/2026-09-30-flr0385.md`
- Create: `docs/superpowers/plans/2026-09-30-flr0385-lit-material-sequoia.md`
- Modify: `TASKS.md`
- Modify: `work/tickets/FLR-0383-sequoia-known-material.md`

- [x] **Step 1: Create the local FLR-0385 feature branch from the development baseline.** The current branch is `feature-flr-0385-sequoia-lit-material`, based on the privacy-repaired FLR-0383 candidate; no push occurred.
- [x] **Step 2: Make FLR-0385 the sole In Progress task.** FLR-0385 is the only In Progress task; FLR-0383 is Waiting after its black-ROI result and FLR-0373 remains Waiting because its planned route probe has not run.
- [x] **Step 3: Run canonical, privacy, checkpoint, and whitespace checks.** Canonical guard, privacy scan, checkpoint contract, and `git diff --check` pass. Markdown-link check still reports the same nine preexisting missing FLR-0338/0339/0340 evidence links and no FLR-0385 link errors.

### Task 2: Revalidate the exact persistent Devtool source

**Files:** No source changes in this task.

- [x] **Step 1: Read-only Devtool status.** The existing `fluorite-plugins` component is the only active component and uses the fixed source path. The initial call correctly failed closed because the linked worktree path differed from the pre-existing container's `project-root` label; supplying that exact existing mount contract allowed read-only inspection. No container was created or replaced.
- [x] **Step 2: Verify source Git state.** `source-git-status` shows a clean `devtool-FLR-0383-source`; `source-git-revision` is exactly `4acaa4c0194303227a2207bbbed9ea2249b72efb`.
- [x] **Step 3: Verify patch-stack identity and API context.** Patch 0331's `From` is exactly the source baseline, appears once after 0330, and has the known UNLIT Sequoia binding/teardown implementation. The source's FLR-0371 fixture has the parameterized LIT shader, linear RGB `(0.05,0.45,1.0)`, and SUN values matching existing patch 0305. No workspace reset occurred.

### Task 3: Change only the Sequoia diagnostic material profile

**Files:**
- Modify in the fixed Devtool source: `plugins/filament_view/core/systems/derived/model_system.cc`
- Modify in the fixed Devtool source: `plugins/filament_view/core/systems/derived/model_system.h`
- Test seam: Mini `flutter-auto` compile and live QMP runtime; the C++ unit suite does not instantiate this scene-backed Filament path.

- [x] **Step 1: Preserve the proven fixture contract.** The source uses the exact fragment `material.baseColor.rgb = materialParams.color;`, FLOAT3 `color`, `filament::RgbType::LINEAR`, `{0.05f, 0.45f, 1.0f}`, and `MaterialBuilder::Shading::LIT`. The all-primitive loop remains unchanged.
- [x] **Step 2: Keep the override opt-in.** The selector is `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE`; with it absent, normal GLB materials remain untouched. No light was added or changed; profile B will reuse `FLR0305_PRODUCTION_SCENE_LIGHT`.
- [x] **Step 3: Check the exact Devtool-source diff.** Exactly the two `ModelSystem` files changed; `git diff --check` passed. Camera/scene/HUD/light/texture are untouched. The Devtool source commit is `b9793ce70deb18081660679796d8288efe90a78a`.

### Task 4: Generate and locally commit canonical patch 0332

**Files:**
- Create through Devtool: `layers/meta-fluorite-trial/recipes-graphics/toyota/files/0332-flr0385-sequoia-known-lit-material-devtool.patch`
- Modify through the helper: `layers/meta-fluorite-trial/recipes-graphics/toyota/flutter-auto_2.0.bbappend`
- Refresh through the helper if required: `manifests/baseline-sources.lock`
- Modify: `work/tickets/FLR-0385-apply-lit-material-to-sequoia.md`, `work/logs/2026-09-30-flr0385.md`, `TASKS.md`

- [x] **Step 1: Run the project split-component helper.** `scripts/rebase-fluorite-devtool-component.sh` completed for ticket `FLR-0385`, source recipe `fluorite-plugins`, baseline `4acaa4c0194303227a2207bbbed9ea2249b72efb`, source commit `b9793ce70deb18081660679796d8288efe90a78a`, and canonical patch 0332. The helper ran the official Devtool patch update and refreshed the baseline lock.
- [x] **Step 2: Verify generated-patch provenance.** Patch 0332 `From` equals the new source commit; its file list is exactly `model_system.cc` and `model_system.h`; it is the incremental rename/shading change from patch 0331; registration exists once after 0331; no local-index file was added; baseline lock count is 425 (one new patch file).
- [ ] **Step 3: Run focused local checks and commit layer/docs.** Run canonical/privacy/checkpoint checks and staged whitespace validation excluding the nested unified-diff `.patch` file; verify that generated patch by reverse-applying it against its exact Devtool source HEAD. Mini `do_patch` remains the authoritative forward-application gate. Commit only patch 0332, its one registration, the helper-authorized baseline lock update, and FLR-0385 evidence/docs. Do not push.

### Task 5: Handoff and build on the fixed Mini PC

**Files:** Existing fixed receiver/build/TMPDIR only; no build configuration edits.

- [ ] **Step 1: Revalidate the receiver before transfer.** Confirm exact receiver selected by current `bblayers.conf`, clean worktree, fixed TOPDIR/TMPDIR roles, no active BitBake, free disk space, and current bundle base. Do not scan or clean caches.
- [ ] **Step 2: Create and transfer the verified bundle.** Run `scripts/handoff-fluorite-bundle.sh` with the verified Mini receiver base and new feature tip. Require local/remote bundle hash equality and exact receiver tip; no cherry-pick and no push.
- [ ] **Step 3: Run the bounded recipe patch gate once.** `scripts/run-mini-recipe-patch-gate.sh FLR-0385 flutter-auto`; stop on the first failure and preserve its filtered log and exact task log path.
- [ ] **Step 4: Compile before the image build.** On the same receiver/TMPDIR, run `bitbake -c compile flutter-auto`; stop if it fails. Before the full image task, tell the user the measured free space, reused cache/TMPDIR, expected scope, and stop conditions.
- [ ] **Step 5: Build and identify the candidate.** Run `bitbake agl-ivi-image-flutter`; record exact layer tip and kernel/rootfs/qemuboot SHA-256 values before QEMU.

### Task 6: Compare profiles A and B in one QEMU run

**Files:** One Mini evidence directory: `$BUILD_EVIDENCE/flr0385-0001/qemu/`; one QMP-derived review-media directory locally if needed.

- [ ] **Step 1: Preflight exact image and single-QEMU resources.** Verify image hashes, 6144 MiB, zero QEMU/runqemu/flutter-auto/BitBake processes, free ports `10930`–`10932`, no QMP socket collision, guest user/session contract, app bundle identity, and the single fresh run ID `flr0385-0001`. Use the existing `qemu-runtime-harness.sh`/`runqemu` profile; stop on mismatch.
- [ ] **Step 2: Run profile A manually.** As UID 1001 `agl-driver`, launch exactly one Example Demo process with `XDG_RUNTIME_DIR=/run/user/1001`, `WAYLAND_DISPLAY=wayland-0`, model match `sequoia`, model limit `2`, and `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1`. Explicitly leave `FLR0305_PRODUCTION_SCENE_LIGHT`, fixture, light-suppression, camera, scene-stage, and `WAYLAND_DEBUG` variables unset. Save the effective allowlisted environment and PID/start-time identity.
- [ ] **Step 3: Capture A while live.** Require the LIT READY/BOUND markers and a live PID/UID immediately before and after every QMP capture. Capture the whole 1280×800 QMP screen plus eight short QMP frames; preserve bounded app/kernel/Oops/present evidence before stopping the exact PID. Record HUD ROI `(1120,0,160,80)`, central 3D ROI `(440,220,400,360)`, and historical left-car ROI `(0,100,320,310)` separately.
- [ ] **Step 4: Stop early on success; otherwise test B only if healthy.** If A visibly contains recognizable colored Sequoia and HUD together, stop the material experiment. If A is black but the app remains alive, has material READY/BOUND, and no first-divergence fault, stop A's exact PID and relaunch the same bundle/profile with only `FLR0305_PRODUCTION_SCENE_LIGHT=1` added. Verify its SUN setup marker, then capture the same QMP evidence. Do not run B after an app crash/Oops or identity failure.
- [ ] **Step 5: Teardown and independently verify.** Stop only the recorded Flutter PIDs; quit only the recorded QMP socket; require zero QEMU/runqemu/flutter-auto residuals, absent socket, and free forwarded ports. Keep raw PPM/logs on Mini and copy no image.

### Task 7: Decide from pixels and checkpoint the next step

- [ ] **Step 1: Review the complete QMP frames.** A pass requires recognizable Sequoia body geometry with diagnostic blue and the CPU/GPU HUD in the same full frame; colored HUD alone, black silhouette alone, or READY/BOUND alone is not a pass.
- [ ] **Step 2: Record outcome and artifacts.** Add hashes, run/image identity, environment delta A→B, bounded log counts, present/liveness, ROI counts/bounds, full QMP screenshot, short video, and teardown result to the ticket and working log.
- [ ] **Step 3: Run final gates and commit locally.** Canonical/privacy/checkpoint/staged-whitespace; run relevant tests with the required local-socket permission if available. Record the known sandbox-only localhost test restriction if it persists. Do not push.
- [ ] **Step 4: Choose the next ticket by the first divergent boundary.** If A or B passes, keep the overall goal open for original-material validation but stop this ticket. If both are healthy negatives, create a distinct follow-up focused on the first boundary supported by the runtime/QMP evidence; leave FLR-0373 waiting until that result informs its scene transition.
