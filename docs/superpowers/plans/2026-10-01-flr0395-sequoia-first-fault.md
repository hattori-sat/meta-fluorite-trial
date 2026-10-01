# Capture the first fault in the Sequoia known-material run — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** On the exact image containing the known constant-blue LIT override, capture the first Sequoia runtime fault and a contemporaneous QMP frame so the next change follows the failing boundary.

**Architecture:** Reuse the image and Mini QEMU profile proven by FLR-0391/0394. Start the Sequoia-selected Flutter process under GDB with SIGSEGV stopping enabled before inferior startup; capture the first stop and QMP while the VM remains live. Diagnostic only; no rebuild or source change.

**Tech Stack:** Yocto-built AGL image, Mini runqemu, strict guest SSH, GDB, QMP, scripts/qemu-runtime-harness.sh, scripts/qemu-pixel-capture.py.

**Spec:** [FLR-0395 ticket](../../work/tickets/FLR-0395-capture-first-sequoia-fault.md)

## Global Constraints

- Exact rootfs/kernel/qemuboot are inherited from FLR-0391; verify hashes before launch.
- Reuse one Mini QEMU, fixed build/TMPDIR, one evidence directory, and the existing 6144-MiB profile.
- Do not modify source, patch, recipe, build cache, image, or launch-profile variables.
- Keep the FLR-0391 Sequoia selector, constant-LIT override, production-SUN control, and Example Demo 3.32.5 bundle unchanged.
- Capture QMP only from the QEMU framebuffer; bracket it with the recorded Flutter identity.
- Stop only the recorded app/debugger and QEMU; verify no residual process, QMP socket, or forwarded-port listener.
- Store raw logs/media outside Git tracking; commit only focused evidence, checksums, and ticket updates.

---

### Task 1: Verify the current ticket and inherited image

**Files:**
- Read: TASKS.md
- Read: work/tickets/FLR-0395-capture-first-sequoia-fault.md
- Read: work/evidence/FLR-0391-0001.md
- Read: work/evidence/FLR-0394-0001.md
- Test: scripts/assert-canonical-repository.sh

- [ ] Run bash scripts/assert-canonical-repository.sh and scripts/runtime-checkpoint.sh verify --ticket FLR-0395 --log work/logs/2026-10-01-flr0395.md.
- [ ] Verify rootfs, kernel, and qemuboot checksums against the fixed Mini artifacts; stop if any differs.
- [ ] Confirm BitBake is idle, no runqemu/QEMU/Flutter process remains, QMP socket is absent, and ports 10930–10932 are free.
- [ ] On the guest, check command -v gdb, the Example Demo 3.32.5 bundle, and the existing guest user. If GDB is absent, do not install/rebuild here; record the blocker and open a toolchain ticket.

### Task 2: Launch the exact Sequoia profile under GDB

**Files:**
- Read: work/commands/FLR-0391-sequoia-lit-sun-launch-0002.cmd
- Create outside Git tracking: one ticket-scoped GDB transcript and one run identity record
- Test: scripts/qemu-runtime-harness.sh

- [ ] Start one 6144-MiB QEMU through the existing QMP-first harness with verified artifacts and fixed Mini build directory.
- [ ] As the existing guest Flutter user, export the same runtime and Sequoia/material/SUN variables from FLR-0391; do not set fixture flags or create selectors.
- [ ] Start /usr/bin/flutter-auto as the GDB inferior; configure set pagination off and handle SIGSEGV stop print nopass; only then issue run.
- [ ] Record inferior PID, UID, /proc start token, GDB PID, QEMU PID, and monotonic launch time.
- [ ] Observe focused READY/BOUND/material/present markers and the first GDB stop. Do not dump the complete guest log.

### Task 3: Capture the first stop and live QMP frame

**Files:**
- Write outside Git tracking: GDB transcript, QMP PPM/PNG, focused present/fault slices
- Test: scripts/qemu-pixel-capture.py

- [ ] If GDB stops, record the stop reason and run info threads, thread apply all bt 30, info registers, info sharedlibrary, info symbol $pc, and x/12i $pc before resuming or terminating the inferior.
- [ ] While the inferior is stopped and QEMU remains live, capture one full-frame QMP image. If a successful present occurs first, capture immediately and retain a second frame only if the first fault follows.
- [ ] Record Sequoia ROI (440,220,400,360), HUD ROI (0,0,320,200), pixel counts, bounding box, and SHA-256.
- [ ] If no signal/stop occurs within 180 seconds, record the bounded no-stop outcome and a live QMP frame; do not call this fixed or healthy from timeout alone.

### Task 4: Clean up and close this diagnostic unit

**Files:**
- Modify: work/tickets/FLR-0395-capture-first-sequoia-fault.md
- Modify: work/logs/2026-10-01-flr0395.md
- Create: work/evidence/FLR-0395-0001.md
- Modify: TASKS.md

- [ ] Stop the exact recorded inferior/debugger and send QMP quit to the recorded QEMU instance.
- [ ] Verify exact PIDs are gone, QMP socket is absent, ports 10930–10932 are free, and guest-process postflight is empty.
- [ ] Update the evidence manifest with image identity, timestamp/UNKNOWN, QMP media hashes, GDB result, first divergence, counters, and teardown.
- [ ] Run canonical guard, runtime-checkpoint verification, privacy scan, git diff --check, and make verify; commit only FLR-0395 ticket/log/evidence/dashboard/context changes.
- [ ] If the material is still invisible or the fault remains, create a new ticket for the smallest evidence-supported countermeasure; do not change camera, textures, light, and composition together.

## Alternatives considered

- Repeat the same material edit/build: rejected because patch 0333 already contains the constant-blue LIT expression and the exact image was built from it.
- Change texture, camera, or composition: rejected for this ticket because FLR-0394 isolates a positive native fixture on the same image and the Sequoia run has an earlier unresolved fault.
- Pre-arm GDB on the exact Sequoia run: selected because it preserves first-fault state while holding image, material, selector, and runtime profile constant.
