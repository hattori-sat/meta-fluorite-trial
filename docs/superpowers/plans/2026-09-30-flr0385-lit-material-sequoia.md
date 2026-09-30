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
- [x] **Step 3: Run focused local checks and commit layer/docs.** Canonical/privacy/checkpoint passed; staged whitespace passed with only the generated nested unified-diff patch excluded, and `git apply --reverse --check` passed against the exact Devtool source HEAD. Mini `do_patch` remains the authoritative forward-application gate. Patch 0332, its one registration, the helper-authorized baseline lock update, and FLR-0385 evidence/docs were locally committed as `c4be4e997f5926b26dfb3c3df429ca1961308545`; no push.

### Task 5: Handoff and build on the fixed Mini PC

**Files:** Existing fixed receiver/build/TMPDIR only; no build configuration edits.

- [x] **Step 1: Revalidate the receiver before transfer.** The active QEMU build's `bblayers.conf` selects the fixed clean receiver at exact base `748978266c9a9c66dd1a5301b56927896ae9cb2f`; its configured TMPDIR is the existing build's `tmp`, BitBake is idle, and the build filesystem has 63 GiB free. `TEMPLATECONF` selects exactly one existing AGL source root. The handoff helper will recheck effective TOPDIR/TMPDIR before updating the receiver. No cache was scanned or cleaned.
- [x] **Step 2: Create and transfer the verified bundle.** The standard handoff transferred the verified bundle to the existing Mini inbox and advanced the clean fixed receiver to `fe92b7760deaf9feb2e09b5370565be7798b4eca`; no cherry-pick or push.
- [x] **Step 3: Run the bounded recipe patch gate once.** `flutter-auto do_patch` passed on the fixed receiver/TMPDIR.
- [x] **Step 4: Compile before the image build.** `flutter-auto do_compile` passed, reusing the existing build and caches.
- [x] **Step 5: Build and identify the candidate.** `agl-ivi-image-flutter` passed with 11,898 tasks and seven recorded warnings. Rootfs SHA-256 `ff0f801c35e5f67fb83dd73d47cf19242f372c4d981be0dda55531ece5e5a398`; qemuboot `4a82822cea7292210504c09eff6e57ab7ab0977d1dd0712a8df0c1c78c830910`; kernel `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`.

### Task 6: Compare profiles A and B in one QEMU run

**Files:** One Mini evidence directory: `$BUILD_EVIDENCE/flr0385-0001/qemu/`; one QMP-derived review-media directory locally if needed.

- [x] **Step 1: Preflight exact image and single-QEMU resources.** Image hashes, 6144 MiB, process checks, ports 10930–10932, QMP socket, guest user/session, app bundle, and the fixed `flr0385-0001` run directory were verified. The existing QEMU harness was used.
- [x] **Step 2: Run profile A manually.** A1–A3 used UID 1001, Example Demo 3.32.5, Sequoia model match/limit 2, `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1`, and production lighting unchanged. A3 identity was PID 905, UID 1001, start 219737.
- [ ] **Step 3: Capture A while live.** A1/A2 missed a live QMP capture. A3 reached `READY=1`/`BOUND=24`, but the live gate ran after its 180-second timeout and found the PID gone. The post-exit 1280×800 frame is uniformly black (SHA-256 `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`) and is invalid for visual acceptance. Central 3D, HUD, and left-vehicle ROIs had 0 changed, edge, and chromatic pixels. Raw PPM/frames remain on Mini; only a QMP-derived PNG and 8-frame MP4 were streamed locally for review.
- [x] **Step 4: Stop early on success; otherwise test B only if healthy.** No visual success was claimed. B was not run because the second present was unmatched and A3 recorded an `FEngine::loop` kernel Oops; the healthy-negative precondition was not met.
- [x] **Step 5: Teardown and independently verify.** QMP `quit` passed; zero QEMU/runqemu/flutter-auto and BitBake/pseudo/image-task residuals; QMP socket absent; ports 10930–10932 free. No QEMU disk image or raw PPM was copied to Mac.

### Task 7: Decide from pixels and checkpoint the next step

- [x] **Step 1: Review the complete QMP frames.** Reviewed the complete A3 post-exit frame; it is black and cannot prove the live app's rendering. No live frame passes the success criterion.
- [x] **Step 2: Record outcome and artifacts.** Recorded the candidate hashes, A3 identity, READY/BOUND, present divergence, timeout, bounded Oops/coredump result, post-exit QMP hash/ROI, retained video, and teardown. The visual gate remains UNKNOWN.
- [ ] **Step 3: Run final gates and commit locally.** Canonical/privacy/checkpoint/staged-whitespace; run relevant tests with the required local-socket permission if available. Record the known sandbox-only localhost test restriction if it persists. Do not push.
- [ ] **Step 4: Choose the next ticket by the first divergent boundary.** The live visual gate remains incomplete, so keep FLR-0385 active; do not start a separate lighting/camera/texture ticket yet. Any same-profile retry must have its QMP capture prearranged at the known material-ready window. Keep the top-level 3D goal active.
