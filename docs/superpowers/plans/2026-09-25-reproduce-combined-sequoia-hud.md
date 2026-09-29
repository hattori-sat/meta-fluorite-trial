# Reproduce Combined Sequoia HUD Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reproduce the previously observed same-frame Flutter HUD, Sequoia geometry, and light-colored pixels before changing the current production render path.

**Architecture:** Use the existing canonical layer and fixed Mini build/QEMU infrastructure. First replay the documented diagnostic positive controls without source changes, then reintroduce lighting one stage at a time while preserving QMP-only visual evidence and one-process teardown.

**Tech Stack:** Yocto/BitBake, existing Devtool-generated `flutter-auto` image, Mini PC QEMU/runqemu harness, guest SSH, QMP framebuffer capture, bounded runtime markers, Git evidence records.

**Spec:** `work/tickets/FLR-0285-trace-production-draw-command-boundary.md` and historical evidence in FLR-0066, FLR-0070, FLR-0050, and FLR-0251.

## Global Constraints

- Use the canonical repository and the existing Mini build/TMPDIR/cache/evidence roles.
- Use one QEMU and one `flutter-auto` process at a time; stop only through the recorded QMP socket.
- Use 4096 MiB unless a separate memory experiment is explicitly required.
- Do not edit source, generated patches, Mini build trees, `tmp`, downloads, or sstate during the reproduction gate.
- Use guest SSH rather than the unreliable serial-login path.
- A visual PASS requires QMP pixels for HUD, recognizable Sequoia geometry, and non-grayscale light-colored pixels in the same frame.

### Task 1: Freeze the reproduction contract

**Files:**
- Read: `TASKS.md`
- Read: `work/tickets/FLR-0285-trace-production-draw-command-boundary.md`
- Read: `work/logs/2026-09-24-flr0285.md`
- Read: `work/commands/FLR-0285-production-sequoia-current-launch.cmd`
- Record: `work/tickets/FLR-0286-reproduce-known-good-combined-sequoia-hud.md`

- [ ] Confirm canonical repository, branch, clean status, active ticket, current rootfs/kernel/qemuboot identity, and fixed receiver/build/TMPDIR roles.
- [ ] Record the historical expected pixels and hashes from FLR-0066 and FLR-0070 without treating either diagnostic side effect as a product fix.
- [ ] Create FLR-0286 with one acceptance gate: one QMP frame containing HUD, Sequoia geometry, and colored light pixels.

### Task 2: Replay the known-good diagnostic positive

**Files:**
- Use: existing QEMU harness and guest SSH launch path
- Evidence: fixed Mini evidence directory for FLR-0286
- Update: `work/tickets/FLR-0286-reproduce-known-good-combined-sequoia-hud.md`
- Update: `work/logs/2026-09-25-flr0286.md`

- [ ] Start one QEMU from the existing image with 4096 MiB and prove guest SSH readiness.
- [ ] Launch exactly one `flutter-auto` as `agl-driver` with `XDG_RUNTIME_DIR=/run/user/1001` and `WAYLAND_DISPLAY=wayland-0`.
- [ ] First run the documented combined diagnostic profile: Sequoia model limit/match, skipped skybox/indirect light/lights/shapes, forced frame rendering, and the existing compositor/frame controls required by the retained FLR-0066 evidence.
- [ ] Capture an early and settled QMP frame, analyze the fixed HUD and native regions, inspect the image visually, and retain runtime marker counts and hashes.
- [ ] Classify the result PASS, FAIL, or UNKNOWN; do not proceed to lighting reintroduction if the diagnostic positive itself is not reproduced.
- [ ] Stop the exact application and QEMU through QMP and verify zero residual QEMU/runqemu/flutter-auto/QMP sockets.

### Task 3: Reintroduce light in controlled stages

**Files:**
- Reuse: `work/tickets/FLR-0286-reproduce-known-good-combined-sequoia-hud.md`
- Reuse: `work/logs/2026-09-25-flr0286.md`

- [ ] Repeat the positive profile with one explicit light and the documented light-operation trace condition used by FLR-0070 p9.
- [ ] Repeat the same profile without the trace and with the trace's timing-only control, preserving all other variables.
- [ ] If the trace-only case is the first colored result, record it as a timing/observation side effect and do not call it a fix.
- [ ] Restore environment, indirect light, direct lights, and shapes one stage at a time; record the first stage that removes vehicle or colored pixels.
- [ ] Capture QMP-only screenshots and bounded logs for every condition in the same evidence unit.
- [ ] Teardown and residual-check after each QEMU session.

### Task 4: Decide whether source work is justified

**Files:**
- Modify only if the first divergent operation is source-attributed: existing Mac Devtool source workspace
- Register only if justified: `layers/meta-fluorite-trial/...`
- Update: `work/tickets/FLR-0286-reproduce-known-good-combined-sequoia-hud.md`

- [ ] If the failure is still a runtime condition or missing evidence, stop at diagnosis and create a narrower follow-up ticket.
- [ ] If a source boundary is proven, make one minimal Mac Devtool source change, commit the source baseline/change, run official `devtool update-recipe`/`finish` flow, and register the untouched generated patch in `meta-fluorite-trial`.
- [ ] Commit the layer change locally, bundle the exact layer tip to the fixed Mini receiver, pass `do_patch`, component compile, full image, artifact identity, and QMP runtime gates.
- [ ] Do not claim completion until one same-frame QMP image shows the requested HUD, Sequoia, and light-colored pixels under the intended non-diagnostic path.

## Self-review

- This plan separates historical reproduction from source modification.
- It covers the requested combined visual gate, light isolation, QMP evidence, process cleanup, and Mac-to-Mini build flow.
- No placeholder step is used; an unproven source cause remains explicitly UNKNOWN.
