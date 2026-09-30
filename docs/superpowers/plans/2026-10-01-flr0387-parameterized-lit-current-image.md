# FLR-0387 Parameterized LIT Fixture Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan task-by-task. Keep the top-level Sequoia visibility objective active; this fixture replay is only a same-image control.

**Goal:** Establish whether the exact FLR-0385 image can render the proven parameterized LIT/RGB fixture independently of the production Sequoia path.

**Architecture:** Reuse the existing Mini QEMU image/profile and manually launch the installed Example Demo under the complete historical fixture environment. Capture bounded runtime markers plus QMP-only full-frame media while the exact app process is live; make no source or build changes.

**Tech Stack:** Existing Yocto rootfs/kernel/qemuboot; Mini `runqemu`; `qemu-runtime-harness.sh`; Example Demo 3.32.5; Filament parameterized LIT/SUN fixture; QMP and FFmpeg preview conversion.

**Spec:** `work/tickets/FLR-0387-replay-parameterized-lit-on-current-image.md`

## Global Constraints

- Reuse rootfs `ff0f801c35e5f67fb83dd73d47cf19242f372c4d981be0dda55531ece5e5a398`, kernel `3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74`, qemuboot `4a82822cea7292210504c09eff6e57ab7ab0977d1dd0712a8df0c1c78c830910`, and Mini receiver tip `fe92b7760deaf9feb2e09b5370565be7798b4eca`.
- Use exactly one Mini run directory `$BUILD_EVIDENCE/flr0387-0001/qemu`, one headless QEMU at 6144 MiB, and ports 10930–10932. Do not create another TMPDIR, build, receiver, or container.
- Set exactly these behavior flags: `FLUORITE_NATIVE_PURE_FIXTURE=1`, `FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`, `FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA=1`, `FLUORITE_NATIVE_FIXTURE_LIGHT=1`, and `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`.
- Set only one targeted observation switch, `FLUORITE_PRESENT_TRACE=1`, to count present enter/return/done markers. Explicitly unset `FLUORITE_VIEWTARGET_FRAME_TRACE`: it logs several records on every `DrawFrame`; verify camera behavior from the explicit camera flag and the existing fixture-camera source wiring instead. Do not enable `FLR0026_SYNC_TRACE`, `WAYLAND_DEBUG`, or broad tracing.
- Explicitly unset `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR`, `FLUORITE_SEQUOIA_LIT_MATERIAL_OVERRIDE`, `FLUORITE_SEQUOIA_UNLIT_MATERIAL_OVERRIDE`, `FLR0026_NATIVE_MODEL_MATCH`, `FLR0026_NATIVE_MODEL_LIMIT`, and `FLR0305_PRODUCTION_SCENE_LIGHT`.
- Do not use top-level `exit` in any serial-exec command file. Accumulate a `status` and end with `test "$status" -eq 0` so the harness always observes its completion marker.
- Launch as UID 1001 `agl-driver` with a 60-second bound. `serial-exec` has a 30-second command deadline, so readiness probes are 15-second chunks, at most three within the 45-second overall gate. Stop each probe at the first Oops, failed present, app exit, or an unmatched present persisting across two one-second samples.
- Keep raw logs, raw PPM, and QEMU disk images on the Mini. Stream only QMP-derived PNG and MP4 previews to `work/evidence/FLR-0387-0001/`; do not commit runtime binaries or screenshots.
- Do not edit/rebuild the product or modify reusable launch/capture helpers. Commit only the ticket/dashboard/plan/working-log record locally; do not push.

---

### Task 1: Establish one exact run target

**Files:**
- Update: `work/tickets/FLR-0387-replay-parameterized-lit-on-current-image.md`
- Update: `work/logs/2026-10-01-flr0387.md`
- Update: `TASKS.md`
- Local run commands: `work/evidence/FLR-0387-0001/*.cmd`
- Mini runtime evidence: `$BUILD_EVIDENCE/flr0387-0001/qemu/`

- [x] **Step 1: Verify repository and active ticket.** Run `bash scripts/assert-canonical-repository.sh`, `git status --short --branch`, confirm FLR-0387 is the sole In Progress ticket, and record the current commit/branch without exposing personal connection values.
- [x] **Step 2: Verify the Mini candidate and ports read-only.** Resolve the kernel path from the candidate qemuboot config, then hash the exact kernel/rootfs/qemuboot and compare with this ticket; prove zero QEMU/runqemu/Flutter targets, zero BitBake activity, and free ports 10930–10932 before creating the one run directory. Record the current receiver tip separately; never substitute its current HEAD for the immutable artifact hashes.
- [x] **Step 3: Verify the existing runtime helpers.** Compare helper SHA-256 with the committed `scripts/qemu-runtime-harness.sh` and `scripts/qemu-pixel-capture.py`; use the fixed receiver/build/TMPDIR, with no build or cleanup.
- [x] **Step 4: Start one 6144 MiB QEMU.** Harness start and guest-ready passed; the guest preflight verified the pinned kernel, UID 1001, Wayland compositor/socket, Example Demo 3.32.5, and no stale Flutter process.

### Task 2: Run the exact parameterized fixture profile

**Files:**
- Create: `work/evidence/FLR-0387-0001/guest-preflight.cmd`
- Create: `work/evidence/FLR-0387-0001/fixture-launch.cmd`
- Create: `work/evidence/FLR-0387-0001/fixture-ready-poll.cmd`
- Create: `work/evidence/FLR-0387-0001/fixture-live-gate.cmd`
- Create: `work/evidence/FLR-0387-0001/fixture-fault-summary.cmd`
- Create: `work/evidence/FLR-0387-0001/fixture-stop.cmd`

- [x] **Step 1: Pass guest preflight.** Exact kernel, UID 1001, Wayland socket/compositor, Example Demo bundle, zero stale `flutter-auto`/`timeout` processes, and readable `journalctl`/`coredumpctl` all passed.
- [x] **Step 2: Launch once with the full checklist.** One app started with all five behavior flags, only the targeted present trace, explicit production/model/color unsets, and recorded PID/UID/start token/wrapper identity.
- [ ] **Step 3: Gate on complete setup, not process start.** Within 45 seconds require the `hardcoded=false shading=lit source=parameter`, pure-fixture, SUN intensity 110000, and minimal-geometry markers. The command must explicitly set `FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA=1`; verify the existing source condition that consumes it. Do not require the camera-applied log marker because it is gated by per-frame `FLUORITE_VIEWTARGET_FRAME_TRACE`.
- [ ] **Step 4: Require repeated healthy rendering.** Count at least eight `FLUORITE_VK_QUEUE_PRESENT_RETURN result=0` and `FLUORITE_VK_PRESENT_DONE` markers, with no Oops or nonzero return. Abort at the first fault or app exit; if enter remains unmatched across two consecutive one-second samples, preserve the first fault window and do not continue polling.

### Task 3: Capture visual evidence and close the exact run

**Files:**
- Update: `work/tickets/FLR-0387-replay-parameterized-lit-on-current-image.md`
- Update: `work/logs/2026-10-01-flr0387.md`
- Create locally: `work/evidence/FLR-0387-0001/qmp-parameterized-lit-live.png`
- Create locally: `work/evidence/FLR-0387-0001/qmp-parameterized-lit-live.mp4`

- [x] **Step 1: Capture a full QMP still and eight frames.** The readiness gate returned `NO` after its first 15-second chunk; a complete QMP still/eight-frame video were captured before QMP quit as failure-only evidence. Capture liveness was not bracketed; do not claim a live black frame.
- [x] **Step 2: Measure fixed ROIs and review the whole frame.** Full QMP image visually inspected; full frame, native ROI, and HUD ROI were all uniformly black. All eight frames have one unique PPM hash.
- [x] **Step 3: Stop only recorded processes.** The app/wrapper were already absent, so no signal was sent. Exact QMP `quit`, target-process/socket cleanup, port postflight, and image hashes passed.
- [x] **Step 4: Record evidence and next discriminator.** Facts, failed attempts, PDCA, exact QMP media/hash/ROI evidence, and UNKNOWNs are recorded. The direct Sequoia material test is a separate ticket.
- [ ] **Step 5: Verify and commit the local record.** Run privacy, file-size, staged-whitespace, ticket-checkpoint, and scoped media-link checks. Commit only ticket/dashboard/plan/log changes, never push.
