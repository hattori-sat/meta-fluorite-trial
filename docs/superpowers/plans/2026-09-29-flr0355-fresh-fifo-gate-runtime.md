# FLR-0355 Fresh-ID FIFO Gate Runtime Implementation Plan

> **For agentic workers:** Execute this plan inline with checkpoints; do not start runtime work until the local red/green and static gates pass. Steps use checkbox syntax.

**Goal:** Pass one fresh run ID consistently from the host runner through QEMU preflight/start, then make one attributable Mini-hosted QEMU attempt that validates the repaired FIFO gate and captures QMP-only screen/video evidence.

**Architecture:** Keep the FLR-0354 actual-FD/object-identity validator and the FLR-0350 production diagnostic profile unchanged. Add a non-mutating starter preflight and pass the same ticket-correlated ID to both preflight and start; transfer the committed harness via the existing Git-bundle receiver workflow, then execute exactly one pinned-image run.

**Tech Stack:** Bash, Python 3/unittest, Yocto `runqemu` on the Mini PC, QEMU QMP, SSH/SCP, FFmpeg.

**Spec:** `work/tickets/FLR-0355-relay-run-id-and-retest-fifo-gate.md`

## Global Constraints

- Run `bash scripts/assert-canonical-repository.sh` in the target worktree before edits.
- Keep FLR-0355 as the sole `In Progress` ticket; FLR-0354 remains a completed predecessor.
- Root the feature branch at `dev-mini-recovery`; preserve the FLR-0354 commits as explicit prerequisites and do not modify the shared dev ref.
- Keep the exact FLR-0344/0348 launch profile and the kernel/rootfs/qemuboot SHA pins unchanged.
- Do not edit product source, recipes, image contents, build caches, deploy artifacts, or Mini `tmp`; this ticket needs no BitBake build or Devtool operation.
- Transfer only through the existing verified Git-bundle workflow; no push.
- Use exactly one fresh runtime ID, `flr0355-0001`, and one QEMU instance. Never reuse the ID after a run directory is created.
- Capture frames only through QMP; do not capture the host desktop or copy QEMU disk images to the Mac.
- Save raw QMP evidence outside Git; transfer only screenshot/video/log evidence needed for review.
- Stop only the recorded app and QEMU instance through the existing targeted cleanup and QMP `quit`; never use process-wide kill.

---

### Task 1: Add a red-capable run-ID wiring test

**Files:**
- Modify: `tests/test_flr0350_launch_gate.py`
- Test: `tests/test_flr0350_launch_gate.py`

**Interfaces:**
- Consumes: the production host runner and `FLR-0350-qemu-start.sh` source text.
- Produces: a regression assertion that one validated `$run_id` reaches both starter preflight and starter start, and that the starter has no consumed-ID fallback.

- [x] Add tests asserting `FLR0350_RUN_ID="$run_id"` is passed to both explicit starter modes before/after the evidence-directory creation point; assert that the start script requires the supplied ID and calls the shared run-ID validator.
- [x] Run `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_flr0350_launch_gate.py` and confirm the new assertions fail against the current scripts because the runner invokes the starter with no mode or ID and the starter defaults to `flr0350-0001`.

### Task 2: Implement the same-ID preflight/start contract

**Files:**
- Modify: `work/commands/FLR-0350-run-sync-producer.sh`
- Modify: `work/commands/FLR-0350-qemu-start.sh`
- Test: `tests/test_flr0350_launch_gate.py`

**Interfaces:**
- Consumes: validated positional `run_id` from `FLR-0350-run-sync-producer.sh`.
- Produces: starter modes `preflight` (read-only) and `start` (launch), both using the identical `FLR0350_RUN_ID`.

- [x] In the runner, invoke `FLR0350_RUN_ID="$run_id" bash "$start_script" preflight` before creating `$parent`; after that parent is created and logged, invoke the same script with `start` and the same ID.
- [x] In the starter, require exactly one mode argument and a nonempty `FLR0350_RUN_ID`; validate it through `scripts/flr0350_launch_gate.py --check-run-id "$run_id"` before deriving target evidence paths or making directories.
- [x] Keep the existing hash pins, process check, fixed ports, memory, and `runqemu` arguments unchanged; in `preflight`, perform those checks without creating the run directory or starting QEMU.
- [x] In `start`, repeat the checks, create the one run directory, save the starter, and run the existing QEMU harness preflight/start. If a repeated check fails after directory creation, the one-shot ID is consumed and is never retried.
- [x] Re-run the focused tests, `bash -n` on both scripts, and `bash work/commands/FLR-0350-run-sync-producer.sh --check`; the static check proves preflight occurs before host evidence mutation and start receives the same ID.

### Task 3: Commit the harness correction and transfer the exact revision

**Files:**
- Modify: `TASKS.md`
- Modify: `work/tickets/FLR-0355-relay-run-id-and-retest-fifo-gate.md`
- Modify: `work/logs/2026-09-29-flr0355.md`

**Interfaces:**
- Consumes: verified local feature tip and `dev-mini-recovery` base.
- Produces: one clean local commit and a Mini receiver at that exact bundle tip.

- [x] Run privacy, staged-whitespace, shell/static, and focused tests; review only the staged FLR-0355 paths.
- [x] Commit locally with the privacy-approved role identity; do not push. The harness fix is committed as `1b3f90c`.
- [ ] Resolve both refs to commit objects, then use `scripts/handoff-fluorite-bundle.sh "$(git rev-parse --verify 'dev-mini-recovery^{commit}')" "$(git rev-parse --verify 'HEAD^{commit}')"` with the already-configured local build-host roles. Role variables are currently unset and targeted local-config searches found no candidate; the helper fail-closed at `BUILD_HOST` before bundle creation/SSH. Resume only when those roles are available; do not invent host/path values.
- [x] Do not run BitBake: this commit changes only the diagnostic harness, not the layer’s image inputs.

### Task 4: Run one pinned-image QEMU attempt and capture evidence

**Files:**
- Execute: `work/commands/FLR-0350-run-sync-producer.sh flr0355-0001`
- Evidence: fixed Mini evidence root under the `flr0355-0001` run ID; local evidence directory outside Git.

**Interfaces:**
- Consumes: exact bundle tip, existing pinned FLR-0335 QEMU artifacts, and the FLR-0350/0354 command set.
- Produces: one serial/GDB runtime record, QMP full-frame still, eight QMP PPM frames, fixed-region pixel analysis, an H.264 MP4 made on the Mac from those frames, SHA-256 values, and teardown verdict.

- [ ] Before launch, verify the Mini receiver is at the exact tip, the run ID has no evidence directory, the QMP path/ports are free, no QEMU/runqemu/Flutter target process is active, and the starter’s pinned artifact hashes match. Stop without launching if any condition fails.
- [ ] Run the command once with `flr0355-0001`. The actual-FD FIFO validator must pass before GDB attach/GO; if it fails, retain the fail-closed result and do not retry this ID.
- [ ] Capture the complete frame and eight one-second QMP frames from the same QEMU instance. Analyze the full frame and fixed 3D ROI `0,200,1280,600`; never infer 3D from logs or static textures.
- [ ] Transfer only the QMP still/frame sequence and bounded evidence logs to the Mac. Convert the still to PNG and frames to H.264 MP4 with the documented FFmpeg command. Record hashes, dimensions, frame count, FPS, and pixel summary; show the actual QMP image/video to the user.
- [ ] Verify targeted app stop, QMP `quit`, QEMU exit, QMP socket removal, and zero matching QEMU/runqemu/Flutter/compositor processes on the Mini.

### Task 5: Close this one-run ticket

**Files:**
- Modify: `work/tickets/FLR-0355-relay-run-id-and-retest-fifo-gate.md`
- Modify: `work/logs/2026-09-29-flr0355.md`
- Modify: `TASKS.md`

**Interfaces:**
- Consumes: observed command exit, target/image identity, QMP evidence, and cleanup results.
- Produces: a bounded PASS/FAIL/UNKNOWN verdict, linked evidence, and a separate next ticket if a new hypothesis or code change is needed.

- [ ] Separate facts, inferences, hypotheses, decisions, and UNKNOWN; distinguish HUD/2D pixels from the 3D ROI and from producer/present markers.
- [ ] Mark this ticket Done only if its one-run acceptance and all cleanup/evidence gates are complete; otherwise use Waiting or keep it In Progress with the exact failure boundary.
- [ ] Create a distinct follow-up ticket before a new hypothesis, display-mode change, or second run ID is attempted.

## Self-review

- The stale-ID defect is tested at the host-runner/starter boundary, not only in the generic ID parser.
- The same pinned image, diagnostic overrides, and QMP-only capture policy remain unchanged.
- The ticket does not claim 3D success unless the QMP screenshot itself contains chromatic/geometry evidence in the defined 3D region.
- The one-run limit and cleanup are explicit. A failed initial side-effect-free
  preflight creates no evidence directory and starts no process. If a repeated
  start-time check fails after the run directory is created, the one-shot ID is
  consumed and must not be retried.
