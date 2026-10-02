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
- The marker-gated capture remains the only path to a Gate-A pass. If the committed scene gate fails on its documented log-size cap and the exact scene-add marker is absent in the preserved summary, an explicitly supplemental diagnostic may use unchanged QMP capture tooling plus manual, read-only PID/UID/start/fault/present checks immediately before and after one full-screen still and exactly eight frames. Label it `diagnostic-no-scene-add`; it cannot satisfy scene-add or Gate-A. Do not modify or deploy the observer/gate commands during this running attempt.
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
- Each guest command is one POSIX-shell line. Stream the committed file into the guest's `/bin/sh -s` over the fixed guest-SSH forward and save output on the Mini. Serial-exec is acceptable only when its setup gate passes; if it fails before dispatch, preserve the setup transcript and use guest SSH rather than blindly retrying the same request.
- Run-local identity/log paths use `/run/user/1001/fluorite-0408-0001.*`; the identity file stores `pid uid start-token kernel-fault-baseline`.
- `scene-gate` returns one explicit `FLUORITE0408_SCENE_GATE status=...` record; only `status=READY` permits the after-scene QMP capture.
- `identity` validates the saved PID/UID/start token, unique `flutter-auto` owner, bounded app-log size, and kernel-fault count before/after QMP capture.
- `export` writes the bounded full app log and selected kernel/journal fault slice into a Mini evidence output file; it does not print full logs into the assistant transcript.

- [x] **Step 1: Write the six run-scoped POSIX guest command files.** Built from the already validated FLR-0405 direct-launch/identity/stop contracts; only run-local paths and the explicit historical 0049 model-only profile differ. `scene-gate` is bounded and checks identity/kernel faults; `stop` targets only the saved PID/UID/start token.
- [x] **Step 2: Add a focused profile regression test.** It checks one-line POSIX syntax, run namespace, the exact historical profile, the required `env -i` allowlist, and exclusion of broad environment/material/camera/readback/input overrides.
- [x] **Step 3: Run the focused static gates.** After tightening the detached launch, exact secondary-Sequoia scene gate, new-kernel-fault rejection, and bounded oversized-log export: focused test 6/6; all six command files pass `/bin/sh -n`, single-line, and size checks; privacy, file sizes (2,096 files), shell syntax (59 files), canonical guard, `git diff --check`, and runtime checkpoint pass. `make check-markdown` reports only the 11 known historical missing targets outside FLR-0408; no current link fails.
- [x] **Step 4: Commit the ticket-scoped profile and records locally.** Initial ticket/plan/profile checkpoint committed as `3e8727d`; follow-up Mini preflight record as `29dd087`; launch, scene, fault, and bounded-export gates as `58d8d3e`. Integration-role metadata used; all remain local and unpushed.

### Task 2: Recheck Mini ownership and immutable image before one QEMU

**Files:**
- Read: `docs/environment.md`
- Read: `scripts/qemu-runtime-harness.sh`
- Read: active Mini source's `scripts/qemu-runtime-harness.sh` and `scripts/qemu-pixel-capture.py`
- Runtime outputs: `/mnt/yocto/evidence/flr0408-0001/qemu/`

**Interfaces:**
- Use the existing active Mini layer checkout only after confirming it remains clean at the expected local feature commit; do not update the separate staging receiver for this runtime-only task.
- Resolve `$BUILD_DIR`, effective `$BUILD_TMPDIR`, `oe-init-build-env`, `runqemu`, and exact qemuboot/kernel/rootfs paths from current fixed roles and deploy metadata; do not guess from directory names.

- [x] **Step 1: Revalidate the current machine roles.** Confirmed the canonical Mac checkout and feature tip, active Mini layer tip/cleanliness, fixed build directory/MACHINE/TMPDIR and active BBLAYERS target. Recorded the separate clean receiver and bundle head; no role was mutated.
- [x] **Step 2: Rehash the three deploy artifacts.** Rootfs, kernel, and qemuboot hashes matched the exact patch-0334 values; qemuboot identifies qemux86-64/ext4 and the same artifact set.
- [x] **Step 3: Run the read-only runtime preflight immediately before QEMU.** Ownership, ports, evidence collision, RAM/swap/disk, and 6144-MiB allocation predicates passed before startup.
- [x] **Step 4: Create exactly one evidence/run directory after preflight passes.** Created `/mnt/yocto/evidence/flr0408-0001/qemu/` and transferred only six committed guest command files; all remote hashes and shell syntax matched. No second build/TMPDIR/QEMU directory was created.
- [x] **Step 5: Run the harness preflight and start once.** Existing runqemu profile started once at 6144 MiB; QMP and guest SSH became ready, and harness/serial/console/boot logs were retained. The later guest serial-exec setup gate failed before command dispatch; the same read-only preflight passed over guest SSH.

### Task 3: Launch exact 0049 profile and capture at secondary scene-add

**Files:**
- Read/run: `work/commands/FLR-0408-guest-preflight.cmd`
- Read/run: `work/commands/FLR-0408-guest-launch.cmd`
- Read/run: `work/commands/FLR-0408-guest-scene-gate.cmd`
- Read/run: `work/commands/FLR-0408-guest-identity.cmd`
- Read/run: `scripts/qemu-pixel-capture.py`

**Interfaces:**
- The guest app is a single UID-1001 `flutter-auto` whose PID/UID/start token remain constant before the still, across all video frames, and after capture.
- The Gate-A path uses QMP `capture` after scene-gate READY and `video` for exactly 8 more PPM frames at 0.5-second intervals. Supplemental diagnostics use distinct filenames and remain outside the marker-gated verdict.

- [x] **Step 1: Run guest preflight and launch.** Serial-exec first failed at the setup gate before dispatch, so its transcript was preserved and the documented SSH guest path was used. Guest preflight and `FLUORITE0408_LAUNCH=PASS` succeeded with the existing `nohup` plus `/dev/null` detach contract; a fresh SSH confirmed the launch survived session teardown. No GDB or additional profile variables were enabled.
- [x] **Step 2: Run the bounded scene gate once.** The original committed gate returned `LOG_INVALID` at its first sample because the app log exceeded 900,000 bytes; a bounded full-log snapshot then counted zero exact secondary Sequoia scene-add markers. Preserve this as an observer failure plus scene-marker absence at that snapshot; do not interpret it as a product pixel failure or repeat the same gate.
- [x] **Step 3: Bracket and capture the first full QMP still.** Not run: before a fresh pre-capture identity could be established, PID 765 had already SIGSEGV'd. No stale/post-exit framebuffer was substituted; Gate-A pixels remain UNKNOWN.
- [x] **Step 4: Capture the short QMP sequence without user input.** Not run because the still's live-identity precondition failed. The 22:15:38Z live snapshot was not followed promptly by capture; the 22:35:52Z crash preceded the 22:46:07Z pre-capture check. Record this as a missed capture window and correct sequencing in the next ticket.
- [x] **Step 5: Save bounded runtime logs before stop.** The bounded full-log snapshot/export, identity snapshots, crash summary, coredump metadata, exact executable identity, and GDB core transcript were saved in the single Mini run directory. The compressed core is retained outside the guest snapshot; hashes are in the ticket and evidence manifest.

### Supplemental diagnostic branch (not Gate-A)

- [x] With the observer/gate implementation unchanged, take a fresh manual read-only guest snapshot. At `2026-10-02T22:46:07Z`, it returned `IDENTITY_CHANGED`: saved PID 765 absent, no UID-1001 `flutter-auto`, scene-add 0, present `663/662/662`, kernel faults 0 vs baseline 0. The snapshot was retained in the existing Mini run directory.
- [x] The conditional still/eight-frame diagnostic was correctly skipped because the matching app identity was absent before capture. Do not substitute a post-exit/stale framebuffer.
- [x] Post-snapshot was not run because the precondition failed. Preserve the result as an interrupted diagnostic branch; profile reproduction and pixels remain UNKNOWN, and this branch cannot satisfy Gate A.

### Task 4: Classify Gate A, display review media, and close the runtime

**Files:**
- Modify: `work/tickets/FLR-0408-replay-known-positive-sequoia-profile-on-0334.md`
- Modify: `work/logs/2026-10-03-flr0408.md`
- Modify: `TASKS.md`
- Create: `work/evidence/FLR-0408-0001.md`

- [x] **Step 1: Review only full-screen QMP evidence.** No still or video exists because the pre-capture identity gate failed after process exit. There is no visual artifact to review; do not infer black pixels or visible Sequoia.
- [x] **Step 2: Separate pixel and health verdicts.** Current classification: `GATE_A_PIXELS=UNKNOWN`, `SCENE_ADD=UNKNOWN`, `PRESENT_HEALTH=FAIL at process termination` (662 successful returns accumulated, with one begin/return mismatch unchanged between snapshots; process later SIGSEGV'd), `RUNTIME_FAULT=YES` (SIGSEGV, not a kernel Oops/OOM in the bounded evidence). This does not establish crash causality or original-light/HUD behavior.
- [x] **Step 3: Preserve failure evidence, then stop only this QEMU.** The compressed core and bounded debugger/build-ID records were saved outside the guest snapshot. The existing Mini helper negotiated QMP `quit`; it reported zero residual target processes and QMP socket. Ports 10930–10932 were free and deploy hashes remained unchanged.
- [x] **Step 4: Record outcome, all failed steps, and evidence hashes.** Ticket, working log, evidence manifest, and TASKS are updated. Gate-A pixels remain UNKNOWN and the runtime fault is YES. A separate follow-up ticket must resolve the core against exact matching symbols; no product regression or rendering cause is claimed.
- [ ] **Step 5: Re-run local gates and make a push-free record commit.** Re-ran canonical, privacy, focused profile test (6/6), Markdown/link, file-size (2,098 files), checkpoint (`active=1`), shell syntax, and `git diff --check`; all pass except `make check-markdown`, which reports only the same 11 historical missing targets in FLR-0338/0339/0340/0391/0395. No FLR-0408 link fails. Commit only this ticket's files with integration-role metadata; do not push.

## Self-review

- Spec coverage: the exact historical launch controls ran on the immutable 0334 image. The old scene-gate overflowed, the later manual live-identity precondition failed after SIGSEGV, and no QMP frame was captured. Therefore this attempt has no pixel verdict; original lighting, HUD composition, camera interaction, final stability, and two-boot acceptance remain unproven.
- The latest runtime evidence locates an unmapped-pointer dereference in the stripped `flutter-auto` executable, but not the pointer's origin, responsible function, or any render/present/driver cause. The delayed live capture is a process-sequencing failure to correct, not a pixel verdict.
- No product-source patch, material override, build, cache cleanup, image transfer, input suppression, or second QEMU is included.
