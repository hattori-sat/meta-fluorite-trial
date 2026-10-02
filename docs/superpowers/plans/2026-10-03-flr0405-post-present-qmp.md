# FLR-0405 Post-present QMP Capture Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task with the checkpoints below.

**Goal:** On unchanged production image 0334, obtain a full-screen QMP frame only after the same live flutter-auto process has completed at least two successful, balanced queue-present calls, and correlate the frame with launch, GDB, and kernel evidence.

**Architecture:** This is an observation-path correction, not a product patch. Add launch wall-clock/uptime markers to the existing shared app log, and make the existing guest live gate wait for a bounded, identity-stable successful-present condition. Run one ordinary-profile QEMU boot, capture QMP evidence before and after the present gate, then analyze the post-present pixels locally.

**Tech Stack:** Existing QEMU runtime harness, serial-exec gate, guest dmesg and /proc, GDB, QMP, Mini's pinned QMP pixel helper, local scripts/qemu-pixel-capture.py, and local FFmpeg.

**Spec:** work/tickets/FLR-0405-capture-first-fengine-fault-present-order.md

## Global Constraints

- Use the exact 0334 rootfs SHA-256 80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c, kernel SHA-256 3df534706393cae86cc81340c3f8c77a0be732ab6be494bc5c845cf2fe07bc74, and qemuboot SHA-256 2363530e2f39d4e57465cb89e724327f699b8ab6247d9e1bb75fdc2a60780c10.
- Use exactly one 6144-MiB QEMU, host run ID flr0405-0003, and ports 10930–10932. Recheck process ownership, storage, memory, ports, QMP socket, receiver/layer identity, and image hashes immediately before start.
- Do not run BitBake tasks or alter image/source/cache. The documented bundle helper may perform its bounded metadata check and update only the fixed clean receiver.
- Launch the ordinary Example Demo as agl-driver UID 1001 with only the allow-listed environment. Set no scene/material/light/camera/render/synchronization override and perform no pointer input in this diagnostic.
- Preserve one guest app log for launch timestamps, GDB, present markers, and the bounded observer. QMP stills must be full-screen and bracketed by the same PID/UID/start identity. Do not treat pre-present or post-exit black frames as product-render evidence.
- Readiness requires at least two exact queuePresent result=0 records, at least two begins, and begins = total returns = successful returns, all counted as records from one AWK read of the shared log under the same live process identity. Match the actual diagnostic encoding: BEGIN is followed by a literal \n delimiter in the log (the C format string is \\n), while the returned result has its own fields. The aggregate gate does not prove per-swapchain/index pairing; retain that as UNKNOWN. The wait is capped at 60 half-second samples and a 45-second wall-clock deadline; each dmesg read is capped at 2 seconds, the app log at 900,000 bytes, and the serial-exec caller uses a 75-second deadline. Timeout is an explicit no-present result, not a pass.
- Keep raw logs/PPMs on Mini. Transfer only small QMP review PNGs. If Mini MP4 encoding fails, encode only the QMP PNG sequence on Mac with /opt/homebrew/bin/ffmpeg; never copy the disk image to Mac.
- A positive frame is an intermediate result only. Final acceptance still requires original Sequoia materials/textures/lighting, same-frame HUD, view/depth/occlusion, input/repaint stability, five minutes of healthy present, and two independent boots of the same final image.

---

### Task 1: Make the run's launch and present boundary observable

**Files:**
- Modify: work/commands/FLR-0405-guest-launch.cmd
- Modify: work/commands/FLR-0405-guest-live-gate.cmd
- Modify: work/commands/FLR-0405-guest-monitor-first-boundary.cmd
- Modify: remaining five work/commands/FLR-0405-guest-*.cmd identity/log consumers
- Test: tests/test_flr0405_present_gate.py
- Modify: TASKS.md
- Modify: work/tickets/FLR-0405-capture-first-fengine-fault-present-order.md
- Add: work/tickets/FLR-0407-guard-complete-serial-exec-payload.md (Inbox-only follow-up)
- Modify: work/logs/2026-10-02-flr0405.md
- Test: every FLR-0405 guest command with /bin/sh -n, one-line framing, and the helper's raw-command 4096-byte pre-send limit; separately measure the completion-wrapper overhead.

**Interfaces:**
- The launch command continues to write the existing four-field identity file; do not change its format because GDB/monitor/stop commands read it.
- The live gate appends and emits one FLR0405_LIVE_GATE line to/from the shared app log with status, PID, UID, start token, wall time, uptime, begin count, total-return count, successful-return count, kernel-fault count, and sample count. It exits 0 for an observed state; the caller must parse status=READY, never infer readiness from serial-exec rc=0.

- [x] **Step 1: Add a launch bracket to the current shared app log.** Capture date '+%Y-%m-%dT%H:%M:%S%z' and /proc/uptime immediately before invoking flutter-auto, then capture them again after the PID/UID/start identity is established. Append one FLR0405_LAUNCH_CONTEXT line to the same $log; do not change the identity-file format or launch environment. Refuse launch if the kernel-fault baseline cannot be read as a number.

      launch_before_wall=$(date '+%Y-%m-%dT%H:%M:%S%z')
      launch_before_uptime=$(awk '{print $1}' /proc/uptime)
      launch_identity_wall=$(date '+%Y-%m-%dT%H:%M:%S%z')
      launch_identity_uptime=$(awk '{print $1}' /proc/uptime)
      printf 'FLR0405_LAUNCH_CONTEXT pid=%s uid=%s start=%s fault_baseline=%s before_wall=%s before_uptime=%s identity_wall=%s identity_uptime=%s\n' "$pid" "$uid" "$start" "$fault_baseline" "$launch_before_wall" "$launch_before_uptime" "$identity_wall" "$identity_uptime" >> "$log"

- [x] **Step 2: Replace the one-shot live gate with a bounded read-only wait.** Each of at most 60 iterations (30 seconds of half-second sleeps, under a 45-second wall-clock gate deadline and the serial helper's 75-second command deadline) confirms the unique original PID/UID/start/comm. One AWK pass over the shared log parses every exact marker record, including records separated by literal backslash+n inside one physical line; it counts begins, all returns, and successful returns independently. Malformed/physically split queue-present markers fail closed. Reject return overflow, any nonzero result, or an app log above 900,000 bytes. READY requires begins = total returns = successful returns >= 2. Compare a dmesg read bounded to 2 seconds with the launch fault baseline. Stop early with APP_EXIT, APP_STOPPED, IDENTITY_CHANGED, APP_LOG_INCONSISTENT, APP_LOG_MALFORMED, APP_LOG_TOO_LARGE, PRESENT_FAILED, KERNEL_LOG_ROLLOVER, KERNEL_FAULT, or KERNEL_STATE_UNKNOWN; after either time/sample bound emit TIMEOUT. The process UID/state/start/comm/uniqueness check is last in each sample. A same-count kernel-ring replacement remains a limitation; READY means present-gate readiness, not a complete health pass. Append one final marker including all three present counts to the shared app log and print it. The gate must not touch rendering/input state.


- [x] **Step 3: Run static command validation.** Run /bin/sh -n on every guest command, assert each has exactly one line, assert every internal identity/log path matches `flr0405-0003`, and assert the raw command is within the serial helper's 4096-byte pre-send gate. Measure the exact completion-wrapper bytes separately; do not invent a 4096-byte full-wire ceiling not enforced by the helper or supported by the runtime evidence. Test escaped-emitter records on one physical line, unbalanced begin/return, nonzero return, malformed fields, and a marker name split across a physical line. Verify READY explicitly requires begins = total returns = successes >= 2, missing post baseline is rejected, process checks occur after log/kernel reads, both wait and immediate check outcomes are explicit, and wall/sample/log-read bounds are present. Size the post-capture raw command with its longest valid decimal baseline. Run git diff --check and the FLR-0405 checkpoint.
- [ ] **Step 4: Commit only the scoped FLR-0405 observer files, plan/ticket/log, focused tests, TASKS entry, and the separate FLR-0407 Inbox ticket.** Run privacy and checkpoint checks after staging; use the approved integration-role metadata; do not push.

### Task 2: Transfer the exact observer revision to the fixed Mini receiver

**Files:**
- Read: scripts/handoff-fluorite-bundle.sh
- Read/verify: scripts/reuse-mini-build-receiver.sh

**Interfaces:**
- Bundle from the clean feature branch using the exact fixed-receiver ancestor `9fb2d8c63bda212d4c17ad8f24698226869a2a37` and exact feature tip verified immediately before handoff. Recheck ancestry before invoking the helper.
- The fixed BUILD_* roles remain local-only and are never printed or committed.

- [ ] **Step 1: Run the canonical handoff helper once.** It must verify the exact bundle hash, live effective TOPDIR/TMPDIR, idle/clean receiver, then update that fixed receiver to the feature tip. Stop on any failed precondition; do not manually scp or fetch around the helper.
- [ ] **Step 2: On Mini, run python3 -B tests/test_flr0405_present_gate.py and python3 -B tests/test_qemu_runtime_harness.py.** Require both suites to pass before starting QEMU. Revalidate one-line framing, shell syntax, raw-command limits, the run-ID namespace, and receiver exact-tip/cleanliness outside ignored evidence.

### Task 3: Run one post-present visual discriminator on exact 0334

**Files:**
- Runtime evidence only: one new Mini directory $BUILD_RECEIVER/evidence/flr0405-0003/qemu/.
- Read: work/commands/FLR-0405-guest-*.cmd, scripts/qemu-runtime-harness.sh, and Mini's pinned QMP pixel helper.

- [ ] **Step 1: Repeat the full read-only preflight.** Verify the receiver/layer tip, exact three image hashes, no QEMU/runqemu/Flutter/GDB/BitBake owner, free ports 10930–10932, no run-directory/QMP collision, and adequate RAM/swap/evidence space. Create no directory until all checks pass.
- [ ] **Step 2: Start one headless 6144-MiB QEMU.** Use run ID flr0405-0003; wait for guest readiness; require the run-scoped /run/user/1001/flr0405-0003-* identity/log files absent; run guest preflight and launch the unmodified Example Demo as UID 1001. Every guest command must use that same 0003 identity/log namespace.
- [ ] **Step 3: Capture a full-screen QMP startup still while the exact app identity is live, before GDB.** Bracket the capture with the same identity. Label it pre-present/startup if no successful return has yet occurred; do not use it as the decisive render result.
- [ ] **Step 4: Attach bounded GDB once and preserve its output in the shared guest app log.** Record threads/LWPs, selected stacks, mapped module/build identity, start/end wall-clock and uptime, and stopped-thread count; hard bound is 30 seconds.
- [ ] **Step 5: Execute the bounded present gate.** Call serial-exec with --timeout-seconds 75; proceed only when the returned marker says exactly status=READY and exposes equal begin, total-return, and successful-return counts (each >= 2). On KERNEL_FAULT, APP_EXIT, or IDENTITY_CHANGED, stop the wait and preserve the boundary. On TIMEOUT, record the no-present boundary; do not relabel it as a render failure. Serial-exec rc=0 alone is never readiness.
- [ ] **Step 6: Capture the decisive full-screen QMP still only after a pre-capture status=READY.** Record that marker's present_success as the baseline. Bracket the full still/short-sequence interval with the same immediate gate. In the disposable serial-child command, set FLR0405_GATE_MODE=check; FLR0405_GATE_BASELINE_SUCCESS=<baseline>; before the gate's parenthesized body; do not use invalid VAR=value ( ... ) shell syntax. Verify the raw command remains within the helper's 4096-byte input limit and record the complete wire length after its fixed 99-byte completion suffix. Require pre/post markers to carry the same PID/UID/start; the post marker must be status=PROGRESS_READY, have at least one additional successful return and balanced begin/return/success counts. Independently inspect the bounded kernel/journal window; the gate's equal-count limitation means it alone cannot prove no Oops. If the post-capture marker is NO_PRESENT_PROGRESS, another non-ready status, or has a changed identity, preserve the pixels but label the bracket incomplete/failed and do not infer ongoing presentation. If the pre-capture gate is not READY, capture at most one same-identity diagnostic still labeled with that status. Save dimensions, hashes, and a run manifest.
- [ ] **Step 7: At the first unhealthy boundary, save the bounded wall-clock/kernel/app log evidence before teardown.** Do not wait five minutes after a fault/stall and do not inject pointer input in this diagnostic. Run the five-minute monitor only if one identity-bracketed full-screen QMP frame visibly contains both recognizable Sequoia and CPU/GPU/FPS HUD and the post-capture gate reports PROGRESS_READY. Monitor for at most 300 actual seconds, rechecking the same PID/UID/start, unique owner, successful-present progress within five elapsed seconds, bounded app log, and kernel fault state, including an end-of-window recheck. Record actual elapsed time and all counts. If the QMP frame is negative or ambiguous, record that pixel verdict and stop without spending five minutes on a frame that does not meet the visual entry condition.
- [ ] **Step 8: Stop only this run's app/QEMU.** Verify QMP quit, wrapper/QEMU exit, no residual runtime process, ports free, and unchanged 0334 image hashes. Do not touch any other process/container.

### Task 4: Analyze and close the diagnostic unit

**Files:**
- Modify: work/tickets/FLR-0405-capture-first-fengine-fault-present-order.md
- Modify: work/logs/2026-10-02-flr0405.md
- Modify: TASKS.md

- [ ] **Step 1: Analyze and hash QMP evidence without transferring raw frames.** On Mini, run the pinned `scripts/qemu-pixel-capture.py analyze --input <post-present.ppm> --region full` and retain its JSON result, dimensions, region counts, hashes, and identity/present manifest in the evidence directory. Convert only the review frame/short sequence to PNG on Mini; transfer the small PNG(s) and sanitized manifest to Mac for visual review. Keep raw PPM, full logs, and image files on Mini.
- [ ] **Step 2: Produce the user-viewable sequence locally if needed.** For numbered 1280x800 QMP PNGs, run /opt/homebrew/bin/ffmpeg -y -framerate 2 -i "$REVIEW_DIR/post-present-%03d.png" -c:v libx264 -pix_fmt yuv420p -movflags +faststart "$REVIEW_DIR/post-present.mp4" and verify it with ffprobe.
- [ ] **Step 3: Update Facts/Inferences/Hypotheses/UNKNOWN and Plan/Do/Check/Act.** State whether the post-present frame shows Sequoia/HUD, keep present health separate from pixels, and record all failed commands/encoding outcomes. Do not claim full acceptance from one boot.
- [ ] **Step 4: Run canonical/privacy/checkpoint/diff checks and locally commit the ticket-scoped records.** Keep the QMP review image/video and raw logs out of Git; do not push.

## Iteration 5 closeout — 2026-10-03

- FLR-0405-0003 ran once on the exact 0334 image and ordinary profile. The
  identity-bracketed live QMP image is white with a large black polygon and has
  neither the HUD nor an identifiable Sequoia. Eight QMP samples are identical.
- The first Oops is uptime 166.449039 s; the later live gate fails at uptime
  223.77 s with counts 2/1/1. Present-marker lines have no timestamps, so only
  Oops-before-gate is known; call-level order and causality remain UNKNOWN.
- GDB was late at uptime 1174.50 s; it did not find faulting TID 705. Do not
  treat LWP 691's poll stack as the fault stack.
- QEMU teardown and exact 0334 postflight passed. Current Mini evidence-root
  search did not find the raw FLR-0405-0003 directory or logs. Review PNG/MP4
  hashes are in [the evidence manifest](../../../work/evidence/FLR-0405-0003.md);
  preserve the remote-log retention gap as UNKNOWN.
- FLR-0405 transitions to Waiting because it did not establish causal order or
  the first failing render/synchronization boundary. FLR-0408 separately
  replays the known-positive 0049 model-only condition on the same immutable
  image. No product patch, build, or cache change occurred.
