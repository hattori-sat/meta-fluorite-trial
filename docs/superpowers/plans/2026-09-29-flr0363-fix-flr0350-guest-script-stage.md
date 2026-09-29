# FLR-0363 Implementation Plan

## Goal

Repair the deterministic guest-helper staging path and obtain one attributable post-launch runtime observation. Distinguish “QEMU/guest booted,” “Flutter process launched,” “Flutter HUD rendered,” and “native 3D visible” as separate checkpoints.

## Architecture

Mac canonical repository and regression test → exact committed Git bundle → existing Mini receiver and pinned QEMU image → guest helper stage → run-bound FIFO/GDB/GO gate → `agl-driver`-owned `/usr/bin/flutter-auto` and bounded app log → QMP post-launch still plus eight frames → separate HUD and 3D classification.

## Tech Stack

Bash runner, Python `unittest`, existing Git-bundle handoff helper, Mini `runqemu`/QEMU QMP harness, existing pinned qemux86-64 artifacts. No image build is required for this runner-only change.

## Specification

- The runner must pass the already prepared local filename variable `"$install_file"` to `guest_run`; it must not expand the generated shell command held in `$install` as a path.
- The regression test must fail on the present call site and pass only when the prepared filename is used.
- Preserve the exact FLR-0350 launch profile and all existing FIFO/PID/start/UID/GDB checks. Do not bypass or weaken them.
- QEMU readiness is not application readiness. Require the guest launch marker, one `agl-driver` wrapper, GO, and same-PID exec to `/usr/bin/flutter-auto` with the expected UID before treating a frame as post-launch evidence.
- Retain bounded startup/render/error markers and their log hash before teardown. Capture QMP 1280x800 still plus eight 1-second frames after the app has had its bounded render observation; inspect the HUD and 3D region independently and inspect the full frame visually.
- This runner uses a diagnostic profile. Even a colored Sequoia/HUD frame proves only that profile; it does not close neutral-production lighting or overall product acceptance.

## Global Constraints

- One Markdown ticket per validation unit; FLR-0362 remains Waiting and FLR-0363 is the sole `In Progress` item.
- Work only in the canonical linked worktree and the FLR-0363 feature branch. Commit locally; do not push. Transfer the exact commit with the established bundle workflow.
- Use a fresh, unused run ID (`flr0363-0001`) once. Never retry it after its evidence directory exists.
- The normal Mini runtime runner already runs its static suite. Do not invoke an additional Mini `--check` before the same run.
- Do not rebuild the image, run BitBake/Devtool, alter product code, delete caches, copy VM images to Mac, or launch a second QEMU.
- If any pre-GO predicate fails, preserve the first named failure and stop. A pre-launch QMP frame cannot classify Flutter or 3D.

## Tasks

### 1. Establish the red regression

- [ ] Add a concise static regression for the `guest_run` stage call.
- [ ] Run only that test and record the expected failure on the old call site. Avoid assertion output that dumps the full runner source.

### 2. Apply the one-line countermeasure

- [ ] Change the path argument to `"$install_file"`; do not alter the payload, profile, command ordering, or other gates.
- [ ] Confirm the focused regression passes, then run the runner's full local `--check` once (it includes the complete static suite).
- [ ] Run shell syntax, privacy, file-size, Markdown-link, runtime-checkpoint, and diff checks. Record the existing nine unrelated FLR-0338/0339/0340 link failures without expanding scope.

### 3. Exact Mini runtime and evidence

- [ ] Commit the ticket-scoped source/test/docs locally, create the exact bundle, and verify Mini receiver tip plus effective `TOPDIR`/`TMPDIR`.
- [ ] Invoke the normal runner once with `flr0363-0001`; it runs the static suite itself, so do not repeat it separately on Mini.
- [ ] Require `agl-driver` launch identity, GO, exact same-PID `/usr/bin/flutter-auto` exec/UID, bounded app log markers, and clean GDB transition before accepting post-launch capture.
- [ ] Preserve the QMP full-frame still and eight-frame sequence, checksums, full-frame/3D ROI analysis, and bounded startup/render/fault log before QMP teardown.
- [ ] Inspect the screenshot. Report whether CPU/FPS/Scenes HUD is visible and whether recognizable colored 3D is visible in that same frame. Keep diagnostic-profile observations distinct from neutral production.
- [ ] Stop at the first named failure; verify run-owned app/QEMU/QMP cleanup and zero residuals. Do not retry the consumed ID.

### 4. Close and hand off

- [ ] Record facts, inferences, hypotheses, UNKNOWN, PDCA, commands, successful and failed markers, screenshots/video, and hashes in this ticket/log.
- [ ] If Flutter starts but the 3D ROI is black, create the next ticket around the first observed renderer boundary; do not call this staging ticket a rendering fix.
- [ ] Keep FLR-0362 Waiting until its own read-0 gate outcome is evidenced or explicitly superseded by the new runtime result.
