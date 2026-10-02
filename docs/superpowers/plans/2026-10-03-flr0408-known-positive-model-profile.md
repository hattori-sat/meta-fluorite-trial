# FLR-0408 Known-Positive Sequoia Model Profile Replay Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan task-by-task with the checkpoints below. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether the previously QMP-visible production Sequoia model-only profile can still produce Sequoia pixels on the exact patch-0334 image.

**Architecture:** Reuse one immutable Mini PC image and the historical 0049 profile that selected the secondary Sequoia instance while skipping environment/lighting/shapes and leaving readback disabled. A same-process scene-add gate triggers full-screen QMP still/video capture. This is Gate A only; it neither changes product source nor proves original lighting, HUD composition, input stability, or final acceptance.

**Tech Stack:** Mini PC Yocto deploy artifacts, existing `scripts/qemu-runtime-harness.sh`, guest serial-exec, `/usr/bin/flutter-auto` 3.32.5, QMP screendump, the pinned `scripts/qemu-pixel-capture.py` capture/video operations, bounded guest `dmesg`/journal queries, and Mac FFmpeg for review copies.

**Spec:** [FLR-0408 ticket](../../../work/tickets/FLR-0408-replay-known-positive-sequoia-profile-on-0334.md)

## Global Constraints

- Use only rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`, kernel SHA-256 `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, and qemuboot SHA-256 `2363530e2f39d4e57465cb89e724327f699b8ab6247d9e1bb75fdc2a60780c10`.
- Start exactly one 6144-MiB QEMU with fresh run ID `flr0408-0001` and ports 10930–10932; never start another QEMU if any QEMU/runqemu/flutter-auto/BitBake owner or port listener exists.
- Reuse the fixed Mini build directory and TMPDIR. Do not run BitBake, Devtool, a build, cleanup, cache operation, branch update, or build-configuration edit.
- Use the installed Example Demo as UID 1001. Do not inject pointer/touch input, disable repaint, or change the camera, material, texture, image, surface order, or synchronization behavior.
- Freeze this profile as one combined condition: `FLR0026_NATIVE_MODEL_MATCH=sequoia`, `FLR0026_NATIVE_MODEL_LIMIT=2`, `FLR0026_NATIVE_SKIP_SKYBOX=1`, `FLR0026_NATIVE_SKIP_INDIRECT_LIGHT=1`, `FLR0027_NATIVE_SKIP_SHAPES=1`, `FLR0027_NATIVE_SKIP_LIGHTS=1`, and `FLR0026_MODEL_STAGE_TRACE=1`. `FLR0026_NATIVE_READBACK_PROBE` remains unset. These are existing historical runtime controls; create no new `FLR0026_*` paths, markers, variables, or evidence names.
- Do not set `FLR0026_NATIVE_SKIP_ENVIRONMENT`; the positive 0049 profile is documented as the separate skybox/indirect-light/shapes/lights skips. If the selected image does not emit those exact applied-control markers, classify profile reproduction as UNKNOWN rather than silently substituting a different profile.
- Keep app/QEMU identity, bounded logs, raw QMP PPMs, serial stream, and the exact runqemu command under the single Mini evidence directory `/mnt/yocto/evidence/flr0408-0001/qemu/`. Do not put raw runtime evidence in Git or under the receiver/build/TMPDIR.
- Transfer only compact QMP review PNG/video to the Mac by streaming from Mini; never copy the rootfs or other deploy image to the Mac. Keep one temporary working area at most; prefer direct streaming without a staging directory.
- Stop on the first abnormal boundary. A scene-add marker, a live process, or a returned present alone is not a pixel pass. Do not run the five-minute monitor because this model-only surface is above the Flutter parent and is expected to hide the HUD.
- Make only push-free local commits for this ticket's commands, plan, evidence, ticket, log, and TASKS row. No push.

---

### Task 1: Freeze and statically validate the historical profile commands

**Files:**
- Create: `work/commands/FLR-0408-guest-preflight.cmd`
- Create: `work/commands/FLR-0408-guest-launch.cmd`
- Create: `work/commands/FLR-0408-guest-scene-gate.cmd`
- Create: `work/commands/FLR-0408-guest-identity.cmd`
- Create: `work/commands/FLR-0408-guest-export.cmd`
- Create: `work/commands/FLR-0408-guest-stop.cmd`
- Create: `tests/test_flr0408_profile.py`
- Create: `work/tickets/FLR-0408-replay-known-positive-sequoia-profile-on-0334.md`
- Create: `work/logs/2026-10-03-flr0408.md`
- Modify: `TASKS.md`

**Interfaces:**
- Each guest command is exactly one POSIX-shell line and is passed as a committed file to the Mini serial-exec helper.
- Run-local identity/log paths use `/run/user/1001/fluorite-0408-0001.*`; the identity file stores `pid uid start-token kernel-fault-baseline`.
- `scene-gate` returns one explicit `FLUORITE0408_SCENE_GATE status=...` record; only `status=READY` permits the after-scene QMP capture.
- `identity` validates the saved PID/UID/start token, unique `flutter-auto` owner, bounded app-log size, and kernel-fault count before/after QMP capture.
- `export` writes the bounded full app log and only the selected kernel/journal fault slice into the Mini evidence directory through serial-exec output files; it does not print full logs into the assistant transcript.

- [x] **Step 1: Write the six run-scoped POSIX guest command files.** Built from the already validated FLR-0405 direct-launch/identity/stop contracts; only run-local paths and the explicit historical 0049 model-only profile differ. `scene-gate` is bounded and checks identity/kernel faults; `stop` targets only the saved PID/UID/start token.
- [x] **Step 2: Add a focused profile regression test.** It checks one-line POSIX syntax, run namespace, the exact historical profile, the required `env -i` allowlist, and exclusion of broad environment/material/camera/readback/input overrides.
- [x] **Step 3: Run the focused static gates.** Focused test 4/4; all six command files pass `/bin/sh -n`; privacy, file sizes (2,096 files), shell syntax (59 files), canonical guard, `git diff --check`, and runtime checkpoint pass. `make check-markdown` has 11 known historical missing targets outside FLR-0408; no current link fails.
- [x] **Step 4: Commit the ticket-scoped profile and records locally.** Initial ticket/plan/profile checkpoint committed as `3e8727d` with integration-role metadata and no push. Follow-up commits remain limited to this FLR-0408 ticket/log/dashboard and evidence manifest.

### Task 2: Recheck Mini ownership and immutable image before one QEMU

**Files:**
- Read: `docs/environment.md`
- Read: `scripts/qemu-runtime-harness.sh`
- Read: active Mini source's `scripts/qemu-runtime-harness.sh` and `scripts/qemu-pixel-capture.py`
- Runtime outputs: `/mnt/yocto/evidence/flr0408-0001/qemu/`

**Interfaces:**
- Use the existing active Mini layer checkout only after confirming it remains clean at the expected local feature commit; do not update the separate staging receiver for this runtime-only task.
- Resolve `$BUILD_DIR`, effective `$BUILD_TMPDIR`, `oe-init-build-env`, `runqemu`, and exact qemuboot/kernel/rootfs paths from current fixed roles and deploy metadata; do not guess from directory names.

- [ ] **Step 1: Revalidate the current machine roles.** Confirm canonical Mac checkout and exact feature tip, active Mini layer tip/cleanliness, the fixed build directory/MACHINE/TMPDIR, and that its bblayers file still points to the clean active layer at the expected commit. Record the separate fixed receiver tip and inbox bundle head; do not mutate them.
- [ ] **Step 2: Rehash the three deploy artifacts.** Hash the versioned rootfs, kernel, and qemuboot; require the three exact values from Global Constraints. Confirm the qemuboot metadata points to the same qemux86-64 machine and artifact set.
- [ ] **Step 3: Run the read-only runtime preflight immediately before QEMU.** Require zero QEMU/runqemu/flutter-auto/GDB/BitBake processes, zero listeners on 10930–10932, no `flr0408-0001` evidence/QMP collision, adequate memory/swap/disk/inodes, and the 6144-MiB allocation. If any owner or mismatch exists, do not start.
- [ ] **Step 4: Create exactly one evidence/run directory after preflight passes.** Use `/mnt/yocto/evidence/flr0408-0001/qemu/`; do not create a second build, TMPDIR, or QEMU run directory. Transfer only the six committed command files there and compare their SHA-256 values with the Mac copies.
- [ ] **Step 5: Run the harness preflight and start once.** Use the exact existing runqemu profile, 6144 MiB, QMP UNIX socket within the evidence directory, snapshot rootfs, slirp, nographic, and ports 10930/10931/10932. Require QMP readiness and guest SSH readiness; preserve the harness's command, serial, console, and boot logs.

### Task 3: Launch exact 0049 profile and capture at secondary scene-add

**Files:**
- Read/run: `work/commands/FLR-0408-guest-preflight.cmd`
- Read/run: `work/commands/FLR-0408-guest-launch.cmd`
- Read/run: `work/commands/FLR-0408-guest-scene-gate.cmd`
- Read/run: `work/commands/FLR-0408-guest-identity.cmd`
- Read/run: `scripts/qemu-pixel-capture.py`

**Interfaces:**
- The guest app is a single UID-1001 `flutter-auto` whose PID/UID/start token remain constant before the still, across all video frames, and after capture.
- QMP `capture` saves one full-screen PPM after scene gate READY. QMP `video` saves exactly 8 more PPM frames at 0.5-second intervals in the same run evidence directory.

- [ ] **Step 1: Run guest preflight and launch.** Use serial-exec with bounded timeouts; require guest preflight PASS and `FLUORITE0408_LAUNCH=PASS`. Save the helper output and launch context in the Mini run directory. Do not enable GDB or additional profile variables.
- [ ] **Step 2: Wait for the one bounded scene gate.** Run `scene-gate` for no more than 45 seconds. Proceed only on `status=READY` with the secondary `assets/models/sequoia_ngp.glb` scene-add marker and matching identity. On fault/exit/identity change, export bounded evidence immediately and stop.
- [ ] **Step 3: Bracket and capture the first full QMP still.** Run the guest identity check, QMP `capture` to `post-scene-add.ppm`, then run the guest identity check again. Require identical PID/UID/start token. Record dimensions and SHA-256 before any image review.
- [ ] **Step 4: Capture the short QMP sequence without user input.** Recheck identity, capture exactly eight QMP frames at 0.5-second intervals with the pinned helper, and recheck identity immediately after. Stop early if an app exit, kernel Oops, or present failure is reported.
- [ ] **Step 5: Save bounded runtime logs before stop.** Run guest `export` once to save the shared app log (up to 900,000 bytes), the first Oops/fault slice from `dmesg`/`journalctl`, the exact app identity, present begin/return/success counts, scene-add/asset/material markers, and the QMP capture bracket. Use Mini-side output files; do not dump full logs into the assistant transcript.

### Task 4: Classify Gate A, display review media, and close the runtime

**Files:**
- Modify: `work/tickets/FLR-0408-replay-known-positive-sequoia-profile-on-0334.md`
- Modify: `work/logs/2026-10-03-flr0408.md`
- Modify: `TASKS.md`
- Create: `work/evidence/FLR-0408-0001.md`

- [ ] **Step 1: Review only full-screen QMP evidence.** Stream the Mini PPM still to Mac FFmpeg as a PNG and stream the eight-frame PPM sequence as an MP4; do not persist raw PPM on Mac or copy any rootfs. Verify the PNG is 1280x800 and MP4 is 4 seconds, 8 frames, 2 fps. Visually classify recognizable production vehicle geometry, texture/material appearance, and red lamps separately from HUD presence.
- [ ] **Step 2: Separate pixel and health verdicts.** Record `GATE_A_PIXELS=PASS|FAIL|UNKNOWN`, `SCENE_ADD=PASS|FAIL|UNKNOWN`, `PRESENT_HEALTH=PASS|FAIL|UNKNOWN`, and `RUNTIME_FAULT=YES|NO|UNKNOWN`. A live Sequoia frame is only an intermediate asset-pixel pass; skipped environment/light stages mean original lighting is untested. A process/scene marker without visible pixels is not a pass.
- [ ] **Step 3: Stop only this app/QEMU and prove cleanup.** Run `guest-stop` only for the saved matching identity, issue negotiated QMP `quit` to the exact run socket, and require zero residual QEMU/runqemu/flutter-auto, zero QMP socket, ports free, and unchanged artifact hashes. Do not stop unrelated containers or processes.
- [ ] **Step 4: Record outcome, all failed steps, and evidence hashes.** Update the ticket, working log, evidence manifest, and TASKS. If Gate A passes, create a later, separate ticket for restoring the lighting stages one condition at a time and then same-frame HUD composition. If Gate A fails after exact scene-add, choose an immediate first-fault capture on that smaller profile. If the profile or scene-add is not reproduced, mark UNKNOWN and do not claim a product regression.
- [ ] **Step 5: Re-run local gates and make a push-free record commit.** Run canonical, privacy, focused profile test, Markdown/link, file-size, checkpoint, and `git diff --check`; record known unrelated historical Markdown failures explicitly. Commit only this ticket's files with integration-role metadata; do not push.

## Self-review

- Spec coverage: this plan tests the historic model-only Sequoia pixels on the exact current image and records same-identity QMP still/video plus bounded present/kernel evidence. It does not claim original lighting, HUD composition, camera interaction, five-minute stability, or two-boot acceptance; those remain explicit downstream gates.
- Hypotheses are discriminated by one fixed profile: a scene-add plus recognizable QMP vehicle supports current-image production asset pixels; scene-add without vehicle pixels locates the failure after insertion; failure to reproduce the exact controls/marker is UNKNOWN.
- No product-source patch, material override, build, cache cleanup, image transfer, input suppression, or second QEMU is included.
