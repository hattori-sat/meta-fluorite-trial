# FLR-0386 — Current-Image LIT Fixture Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Keep the top-level 3D objective active; a fixture pass is not production Sequoia acceptance.

**Goal:** Determine whether the FLR-0385 `FEngine::loop` / unmatched-present fault is shared by the exact current image or specific to production Sequoia.

**Architecture:** Run one manual Example Demo replay on the exact FLR-0385 rootfs. The valid historical fixture requires pure-fixture, minimal-geometry, local-camera, fixture-light, and force-render behavior flags; use its parameterized material branch and QMP-only evidence.

**Tech Stack:** Yocto candidate rootfs; existing Mini `runqemu` and runtime harness; serial guest execution; Flutter 3.32.5; Filament LIT fixture; QMP; FFmpeg review-media conversion.

**Spec:** `work/tickets/FLR-0386-replay-lit-fixture-on-0385-image.md`

## Global Constraints

- Reuse the fixed Mini receiver, build directory, TMPDIR, caches, and exact FLR-0385 artifacts; do not rebuild or clean caches.
- Use exactly one run directory: `$BUILD_EVIDENCE/flr0386-0001/qemu`; use one headless QEMU at 6144 MiB and ports 10930–10932.
- Use the existing manual Flutter path as UID 1001 `agl-driver`; do not modify a reusable launcher.
- Set the five FLR-0286/0367 functional flags: `FLUORITE_NATIVE_PURE_FIXTURE=1`, `FLUORITE_NATIVE_MINIMAL_GEOMETRY=1`, `FLUORITE_NATIVE_FIXTURE_LOCAL_CAMERA=1`, `FLUORITE_NATIVE_FIXTURE_LIGHT=1`, and `FLR0026_FORCE_RENDER_ON_SKIPPED_FRAME=1`. Keep `FLUORITE_NATIVE_HARDCODED_MATERIAL_COLOR` unset for the parameterized material. Leave Sequoia/model selectors and production-light overrides unset.
- Capture complete QMP evidence while the recorded PID/UID/start-time is live immediately before and after still/video capture; if the app faults first, label any later frame post-fault and non-positive.
- Keep raw PPM, guest logs, and runtime artifacts on Mini. Stream only QMP-derived PNG/MP4 review media to the local evidence folder.
- Stop at the first matching Oops/unmatched-present fault or after the decisive capture; no blind retries, profile-B lighting, source edits, or builds.
- Commit only ticket/log/plan/dashboard changes locally after checks; never push.

---

### Task 1: Establish the exact target and evidence run

**Files:**
- Create/update: `work/tickets/FLR-0386-replay-lit-fixture-on-0385-image.md`
- Create/update: `work/logs/2026-10-01-flr0386.md`
- Create/update: `TASKS.md`
- Runtime evidence: `$BUILD_EVIDENCE/flr0386-0001/qemu/`

- [x] **Step 1: Verify repository/task authority.** Canonical guard passed; FLR-0386 was sole active ticket on `feature-flr-0386-current-image-lit-fixture-control`.
- [x] **Step 2: Verify artifact identity and single-run resources.** Exact kernel/rootfs/qemuboot hashes matched; one new QEMU directory, 6144 MiB, ports 10930–10932, zero target processes, and free ports verified.
- [x] **Step 3: Copy and verify the committed helpers.** The two Mini helper copies matched their committed SHA-256 values.
- [x] **Step 4: Start one QEMU and pass guest preflight.** Harness preflight/start/guest-ready passed. Guest UID, Wayland/compositor, bundle `app_id=fluorite`, and no stale Flutter app passed.

### Task 2: Replay the historical parameterized LIT fixture

**Files:**
- Run-scoped commands/output in `$BUILD_EVIDENCE/flr0386-0001/qemu/`
- Local review media in `work/evidence/FLR-0386-0001/`

- [x] **Step 1: Launch the control manually.** One app was launched as UID 1001 with a 60-second bound, but four required functional flags were missing; this is recorded as an invalid-profile deviation.
- [x] **Step 2: Arm the capture before readiness.** PID/UID/start-time were recorded. The readiness command had top-level `exit`, closed the serial shell, and lost the harness completion marker; the saved output retained the `READY=NO` counts and Oops.
- [x] **Step 3: Capture QMP evidence.** The app exited before a live-PID gate. One full 1280×800 post-Oops still and eight frames were captured and analyzed; they are explicitly not a liveness-bracketed fixture result.
- [x] **Step 4: Save bounded runtime evidence.** Present counts, Oops/call-trace excerpt, coredump listing, and exact PID state were retained on Mini; no full app log was copied.
- [x] **Step 5: Stop at the gate.** No second profile or retry was run. The app and wrapper had already exited; QEMU was stopped through its exact QMP socket.

### Task 3: Classify, clean up, and close the unit

- [x] **Step 1: Convert review media without copying raw PPM files.** QMP PPMs were streamed from Mini directly through local FFmpeg; only PNG/MP4 derivatives are local. The full image was visually inspected and uniformly black.
- [x] **Step 2: Apply the exact interpretation gate.** The profile was incomplete, so the pixel result cannot classify fixture/material behavior. Only ordinary startup's present/Oops sequence is established.
- [x] **Step 3: Tear down one exact run.** Exact QMP quit and independent harness postflight verified zero QEMU/runqemu/Flutter processes, absent socket, free ports, and unchanged image hashes.
- [x] **Step 4: Record and validate.** Canonical guard, repository privacy, file-size, FLR-0387 checkpoint contract, shell-command syntax, and whitespace checks passed. Repository-wide Markdown links still report 9 pre-existing missing FLR-0338/0339 evidence targets; no FLR-0385–0387 link errors remain. FLR-0386 stays Waiting because its runtime fixture verdict is UNKNOWN.
- [x] **Step 5: Open a separate ticket for the unresolved fixture verdict.** [FLR-0387](../../../work/tickets/FLR-0387-replay-parameterized-lit-on-current-image.md) owns the corrected exact-profile parameterized replay; no profile was retried in FLR-0386.
