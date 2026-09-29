# FLR-0350 Pre-submit Sync Producer Capture Implementation Plan

> **For agentic workers:** Use `executing-plans` to execute inline. Implementation delegation is not authorized; Astra may review decisions only.

**Goal:** Correlate the FLR-0348 Present waiter with Lavapipe's release producer and the same live sync-object generation in one bounded QMP run.

**Architecture:** Keep the exact FLR-0335 image and FLR-0344/0348 diagnostic launch profile. An `agl-driver` shell opens a new run-owned FIFO and blocks in builtin `read`; guest root GDB attaches to that same PID, configures exec/fork handling, and writes a run-owned armed marker. A separate release command checks the marker, GDB's PID as the wrapper's `TracerPid`, exact FIFO/read syscall, wrapper start identity, and then sends only `FLR0350_GO`. GDB must stop at same-PID exec and the Lavapipe library-load boundary, prove the required breakpoints resolved before relevant calls, and invalidate/teardown the run if debugger coverage is lost. A ticket-specific runner reuses the existing QEMU runtime harness and records only sync lifecycle, producer, matching wait, QMP pixels, and teardown evidence.

**Tech Stack:** Yocto FLR-0335 QEMU image, POSIX `/bin/sh`, guest GDB with Python support, existing Mini QEMU/QMP harness, Bash runner, repository ticket/log gates.

**Spec:** `work/tickets/FLR-0350-correlate-lavapipe-sync-release-producer.md`

## Global Constraints

- Use the exact FLR-0335 kernel, rootfs, and qemuboot hashes already pinned in FLR-0344; QEMU memory remains 6144 MiB.
- Reuse the exact FLR-0344/0348 app environment, including `FLR0026_TREAT_UNLINKED_FENCE_READY=1`; all conclusions are diagnostic-profile-specific.
- Start at most one QEMU run, with a fixed evidence ID `flr0350-0001`; no retry or late-attach fallback.
- Stop the observation no later than 10 seconds after the exact matching wait begins. If the wait never appears within the runner's fixed 180-second app window, record UNKNOWN and teardown.
- No BitBake, Devtool, product patch, image rebuild, scene/light/camera/HUD change, broad thread dump, or unfiltered system log.
- Verify wrapper PID continuity across exec, process ownership, fork handling, breakpoint resolution, sync identity/generation, QMP screenshot/video, and zero residual run-owned processes/sockets.
- If any launch, FIFO/read-state, GDB, symbol, callback-coverage, or lifetime gate fails, stop as UNKNOWN; do not switch instrumentation methods during the run. The FIFO prevents exec before authorization; it does not protect against GDB failure after the token, so loss after release invalidates the run.

---

### Task 1: Add a deterministic pre-exec launch gate

**Files:**
- Create: `work/commands/FLR-0350-preflight.cmd`
- Create: `work/commands/FLR-0350-launch-paused-production.cmd`
- Create: `work/commands/FLR-0350-release-go.cmd`

**Interfaces:**
- The QEMU runner sends each file as one serial-exec command, no longer than 4096 bytes.
- The preflight reports exact-image identity, available guest memory, GDB presence, zero app collisions, `/bin/sh` builtin `kill`, readable `/proc/<pid>/syscall`, and free FLR-0350 runtime paths.
- The launcher exports the exact FLR-0344/0348 diagnostic variables, creates a mode-0600 FIFO owned by `agl-driver`, records the wrapper PID and `/proc/<pid>/stat` start identity, and proves that PID is blocked in `read(3)` on that exact FIFO. It does not execute Flutter.
- The release command requires the GDB armed marker, matching `TracerPid`, the same wrapper start identity, exact FIFO descriptor/read syscall, and live guest GDB before writing exactly `FLR0350_GO`; it then verifies same-PID exec to `/usr/bin/flutter-auto` while GDB still traces it.

- [x] Compare every exported rendering/runtime variable and CLI argument against `work/commands/FLR-0344-launch-production.cmd`; only run-specific filenames may differ. Static comparison PASS.
- [x] Implement guest PID/log/FIFO/marker collision checks before creating the wrapper; retain QMP/SSH/serial port and socket collision checks as a separate Mini-host runner preflight.
- [x] Implement the FIFO wrapper with exact-token-only direct exec and no fallback launch; record PID, start identity, UID, `/proc/<pid>/comm`, state, `/proc/<pid>/syscall`, and FIFO descriptor without printing unrelated environment values.
- [x] Implement an independently gated release command that requires verified GDB attachment and catches same-PID exec; do not confuse the pre-exec marker with post-exec library-symbol readiness. Static gate PASS; target GDB marker is still pending Task 2.
- [x] Run `sh -n` against the decoded launcher body and assert the serial command is one line and at most 4096 bytes. All three serial commands and embedded wrapper syntax PASS.

### Task 2: Add pre-submit GDB sync lifecycle instrumentation

**Files:**
- Create: `work/commands/FLR-0350-sync-producer.gdb`
- Create: `work/commands/FLR-0350-attach-pre-submit.cmd`
- Create: `work/commands/FLR-0350-interrupt-gdb.cmd`

**Interfaces:**
- The attach command runs guest `/usr/bin/gdb` as root against the wrapper already blocked in the exact FIFO read and writes one run-owned GDB log/PID pair.
- The GDB script sets `follow-exec-mode same`, `follow-fork-mode parent`, and `detach-on-fork on`; it catches exec/fork events, records the same-PID `flutter-auto` transition, and does not attach to scanner children.
- Pending breakpoints cover `lvp_pipe_sync_init`, `finish`, `signal`, `signal_with_fence`, `reset`, `move`, `wait`, and the relevant Vulkan submit/Present boundary. GDB stops at same-PID exec and `libvulkan_lvp.so` load; required function breakpoints must resolve before continuing past the library-load gate. Events include PID/TID, sync address, field values, generation transitions, and producer entry/return; only the matching Present wait gets a short stack.
- The pre-exec marker proves only attachment and catchpoint/fork policy readiness. The post-exec library-load gate separately proves exact PID/executable and resolved instrumentation before the first relevant Vulkan submission. GDB loss after GO invalidates the run. On any failed gate, capture available QMP state and tear down without fallback.

- [x] Implement GDB Python breakpoint handlers for object init/finish/reset/move, both signal inputs/results, submit boundary, and the exact WSI-associated wait; cap event count and mark truncation. A waiter after an unclassified move or finish is `lifetime=UNKNOWN`, never a false same-generation PASS.
- [x] Add an exact-image guest preflight for pending-breakpoint/catchpoint command syntax and GDB Python API presence, plus exact runtime/debug Build ID checks at the library-load boundary. Target preflight and automatic debug-file resolution remain pending the QEMU attempt.
- [x] Verify attachment to the recorded FIFO-blocked PID and emit the pre-exec marker only after exec/fork/catchpoint policy is configured; same-PID `/usr/bin/flutter-auto` and fork behavior are checked after GO.
- [x] At the Lavapipe load stop, require the expected Build ID and every lifecycle/producer breakpoint location before allowing the first relevant call; unresolved coverage kills the inferior and remains UNKNOWN.
- [x] Add a single bounded interrupt/collection path with exact GDB PID/start identity checks, targeted matched-wait state, and no broad thread dump.
- [x] Run the local static checker: all 7 embedded GDB Python blocks parse, 10 guest commands are one line and <=4096 bytes, and shell syntax passes. Runtime GDB behavior remains pending.

### Task 3: Add the single-run Mini QEMU/QMP runner

**Files:**
- Create: `work/commands/FLR-0350-qemu-start.sh`
- Create: `work/commands/FLR-0350-run-sync-producer.sh`

**Interfaces:**
- The runner consumes only `flr0350-0001`, uses the verified FLR-0335 hashes and existing `qemu-runtime-harness.sh`/`qemu-pixel-capture.py`, and refuses an occupied evidence directory, QEMU process, serial/SSH/telnet port, or QMP socket.
- The runner preserves a full-frame prelaunch still, then one post-observation QMP still and eight one-second QMP frames with fixed full-frame and lower-3D ROI analysis.
- The app wait window is at most 180 seconds; once the matching Present wait marker is recorded, the producer observation is at most 10 seconds.

- [x] Reuse the FLR-0344 exact-artifact/hash preflight and 6144 MiB memory setting; reserve only `/mnt/yocto/evidence/flr0350-0001/`. Read-only Mini preflight found no target process, occupied fixed port, or prior evidence ID, and both helper hashes match.
- [x] Implement QMP prelaunch capture → guest preflight → four-part SHA-checked GDB script transfer → FIFO-blocked launch → GDB attach/arm proof → exact GO token → same-PID exec proof → Lavapipe load/symbol gate → bounded observe → confirmed GDB stop → runtime state/QMP still/eight frames/ROI → exact app stop → QMP quit.
- [x] Bound the app window from the guest GO uptime marker to 180 seconds and start the 10-second watch window from the matched-wait marker after both watchpoints arm. Polls are split into <=16-second guest serial calls to stay below the transport's 30-second deadline.
- [x] On every failure path, interrupt only the recorded GDB. Collect runtime state or QMP frames only after GDB exit is confirmed; otherwise skip guest evidence collection, QMP-quit the owned VM, and report teardown status. Stop only the recorded app PID and remove only the verified run-owned FIFO when debugger exit is confirmed.
- [x] Run `bash -n`, check serial command lengths and transfer chunk boundaries, and run the runner's `--check` mode without starting QEMU.
- [x] Add a static regression gate that rejects cleanup ordering where QMP capture can happen before confirmed GDB stop.

### Task 4: Verify, commit, transfer, and close only the diagnostic unit

**Files:**
- Modify: `work/tickets/FLR-0350-correlate-lavapipe-sync-release-producer.md`
- Modify: `work/logs/2026-09-28-flr0350.md`
- Modify: `TASKS.md`

- [x] Run the canonical repository guard, privacy check, checkpoint, `git diff --check`, and `make verify`.
- [ ] Commit only FLR-0350 plan/commands/ticket/log files locally; do not push.
- [ ] Bundle the committed diagnostics to the fixed Mini receiver and verify remote commit/bundle hashes before the one QEMU run.
- [ ] Record all success and failure output, QMP hashes/preview, producer/wait identity, object generation, profile caveat, and teardown.
- [ ] Close FLR-0350 only if its producer gate and QMP/teardown criteria pass; otherwise retain UNKNOWN/PARTIAL and create a separate Inbox ticket for the next independent gate.

## Review Notes

- Compared normal launch-then-attach, gdbserver launch, self-stopped pre-exec wrapper, and FIFO token gate. Astra's judgment-only review recommends the FIFO token gate because exec authorization is explicit and observable; the pre-exec self-stop alternative has greater ambiguity between its own and GDB's stop/resume. The FIFO design is only fail-closed before GO: debugger loss after authorization invalidates the run and requires teardown.
- FIFO-specific risks are resolved by a new per-run FIFO, mode-0600 ownership, exact token matching, bounded wait, `/proc/<pid>/syscall` plus FD-target proof, process start identity, and no fallback. An unreadable syscall state, stale path, nonmatching token, debugger-marker mismatch, or process handoff means no release/UNKNOWN.
- After GO, catch same-PID exec and stop at the Lavapipe library-load boundary. Pending breakpoint declarations alone are not coverage: verify the exact Build ID and resolved locations before the first relevant call. If GDB cannot prove that ordering, stop UNKNOWN; do not silently change instrumentation.
- The guest serial transport has a 30-second completion deadline; no poll command approaches that limit. The compressed GDB script exceeds the 4096-byte serial-command ceiling, so it is sent in four base64 chunks, decompressed once, and SHA-256 checked on the guest before launch.
