# Apply constant-color LIT material to Sequoia — Implementation Plan

> Execute each gate in order. Keep material visibility separate from process/present health; preserve a failed result and stop at the first unsafe or failed gate.

**Goal:** Replace Sequoia's parameterized LIT diagnostic color with the current-image fixture's proven constant blue material, then verify Sequoia plus HUD through QMP.

**Architecture:** Edit the fixed persistent Devtool `fluorite-plugins` source only; commit the source change; use `scripts/rebase-fluorite-devtool-component.sh` to invoke official `devtool component-add` and `devtool update-recipe --mode patch --append --no-remove`; register generated patch 0333 after 0332; locally commit the layer; send a verified Git bundle to the fixed Mini receiver; build and run there.

**Spec:** [FLR-0391](../../work/tickets/FLR-0391-apply-constant-lit-material-to-sequoia.md)

## Constraints

- Current branch: `feature-flr-0391-sequoia-constant-lit`; preserve pre-existing working-tree files and do not stage unrelated tickets.
- Only the fixed Podman Devtool container/source/state and existing Mini receiver/build/TMPDIR are in scope. No Docker, new container/state/cache/TMPDIR/build tree, push, Mac QEMU, or image copy.
- Do not hand-author a patch. Source edit must be committed first. The official split-component helper must generate and identify the exact commit's patch.
- Do not change GLB, original textures/PBR, camera, transforms, HUD/composition, model-selection semantics, launch scripts, or the no-override default behavior.
- Use the exact successful fixture expression `material.baseColor.rgb = vec3(0.05, 0.45, 1.0);`, retain `prepareMaterial` and LIT shading, remove the unused parameter/setter, and preserve all-primitive binding/cleanup.
- Reuse the existing production SUN opt-in and saved model-selection controls; do not create FLR0026 artifacts or new legacy variables.
- Capture QMP at first successful present with identity bracketing. If a present stalls while the process remains alive, take one bounded GDB snapshot. Always record teardown and failure evidence.

## Task 1 — Validate ticket/source/toolchain baseline

1. Confirm canonical guard and FLR-0391 is the sole `In Progress` ticket with the checkpoint verifier.
2. Verify the persistent container and one `fluorite-plugins` Devtool registration using the Podman wrapper.
3. Verify source is clean and HEAD equals the post-0332 baseline `b9793ce70deb18081660679796d8288efe90a78a`; record commit/branch and the generated-patch target is unused.
4. Read the active Devtool source around `ModelSystem::setupRenderable`; compare the current parameter expression to patch 0249's exact constant expression.
5. Check free Mini build storage and idle BitBake/QEMU state before handoff/build. Stop on a mismatch; do not clean caches.

## Task 2 — Edit and commit one Devtool source change

**Execution status:** PASS. The one-file change is committed as
`6946d02d61e637dbaf1eb5cbc52bfe3b40b8882e` on
`devtool-FLR-0391-source`; the tree is clean and the patch reverse-applies
against that source HEAD.

1. In only `plugins/filament_view/core/systems/derived/model_system.cc`, change shader source to constant linear blue. Remove `.parameter("color", FLOAT3)` and `setParameter` because the uniform is no longer consumed.
2. Change the material builder name to identify constant LIT; keep the READY prefix and add `source=constant`. Keep build failure and BOUND markers, asset filter, binding every primitive, and onDestroy behavior unchanged.
3. Use wrapper `source-git-diff-check`; assert exactly one modified path and inspect the exact diff. Do not edit `model_system.h` unless the diff proves a necessary declaration change (expected none).
4. Commit exactly that source file with `source-git-commit` on the FLR-0391 source branch; verify clean status and full commit SHA.

## Task 3 — Generate and commit canonical layer patch

**Execution status:** Devtool generation and pre-commit gates PASS; the
canonical layer commit remains pending. Patch 0333 is byte-identical to the
single official generated output, `From` names the source commit, reverse
apply passes, the bbappend has one entry after 0332, the authorized baseline
lock is refreshed, and the repository privacy scan passes. The initial failed
attempts and workspace-alias recovery are in the working log.

1. Run `scripts/rebase-fluorite-devtool-component.sh` with baseline `b9793ce70deb18081660679796d8288efe90a78a`, the exact source commit, new path `0333-flr0391-sequoia-constant-lit-material-devtool.patch`, existing `flutter-auto_2.0.bbappend`, and `ivi-homescreen-plugins` patchdir.
2. Verify official generated patch `From` matches the source commit, exact one-file diff and known expression; compare canonical and generated patch byte-for-byte; verify one registration after 0332 and refreshed authorized baseline lock.
3. Run privacy check, `git diff --check`, patch reverse-check against exact Devtool HEAD, and canonical/checkpoint verification. Stage only FLR-0391 patch, bbappend, baseline lock, ticket, plan, log, and relevant dashboard/historical correction files. Commit locally; do not push.

## Task 4 — Bundle and Mini build

1. Run the fixed `scripts/handoff-fluorite-bundle.sh <base> <tip>` and record local/remote SHA, receiver exact tip, and effective TOPDIR/TMPDIR. Do not copy source trees or image artifacts.
2. Verify Mini is idle and has adequate free space; preserve build/TMPDIR/cache. Run progressive gates on the fixed build: `flutter-auto do_patch`, `flutter-auto do_compile`, then `agl-ivi-image-flutter`.
3. Stop on first failing task. Record concise task/log slices, preserve the raw Mini log, and make no clean/cleanall/cleansstate action.
4. Hash rootfs, kernel, qemuboot and the two official local helper scripts. No Mac QEMU.

## Task 5 — One bounded Sequoia runtime trial

1. Preflight exact artifact/helper hashes, no QEMU/runqemu/flutter-auto residual, free ports 10930–10932, absent fresh run directory, QMP endpoint, and guest readiness.
2. Start exactly one 6144-MiB QEMU with the official Mini harness. Manually launch one Example Demo `flutter-auto` as `agl-driver` UID 1001 with the saved Sequoia model selector, `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE=1`, existing `FLR0305_PRODUCTION_SCENE_LIGHT=1`, and narrow present trace. Remove unrelated fixture/trace flags.
3. Require `READY source=constant`, selected model, expected bound count, SUN setup, and first successful present. At the earliest such frame, capture complete 1280×800 QMP still and short QMP video while PID/UID/start token match before and after. Do not wait for eight presents to save the first image.
4. Separately observe up to eight successful present returns. On mismatch, if app remains alive, attach GDB once with a 15-second bound (`info threads`, `thread apply all bt 2`, detach); collect only bounded journal/coredump evidence. If app has exited, classify any later screenshot as post-exit/failure-only.
5. Stop exact app PID, QMP-quit only the run-owned QEMU, verify zero residual targets/socket/ports, hash evidence, inspect complete still/video, and compute fixed Sequoia/HUD ROI metrics.

## Task 6 — Close or split by observed boundary

1. Update FLR-0391 ticket/log and TASKS with facts, inference, hypotheses, UNKNOWN, all pass/fail/timeout results, source/image hashes, full-frame visual evidence, and teardown.
2. Close only if the diagnostic colored Sequoia and CPU/GPU HUD coexist in the live full frame and the process/present health gates pass. A visual positive plus later crash is recorded as two independent results with health follow-up still open.
3. If geometry is present outside the expected crop, use the complete QMP image to scope a separate camera/visibility ticket. If no live material verdict exists because present fails first, scope the first independently evidenced runtime fault. Do not reflexively revise shell scripts or change texture/light/camera together.

## Official workflow basis

The Yocto Project Reference Manual says `devtool update-recipe` writes patches for source changes after those changes are committed; `--append` writes/updates an append in the specified layer. This project applies that standard to its split `fluorite-plugins` component using the existing deterministic wrapper/helper. See [Yocto Project devtool reference](https://docs.yoctoproject.org/4.0.34/ref-manual/devtool-reference.html#updating-a-recipe).
