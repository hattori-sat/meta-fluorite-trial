# FLR-0358 Serial Capture Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing `serial-exec` command capture only its requested guest command while preserving the strict FLR-0350 observation parser and identity gate.

**Architecture:** Exercise the public `qemu-runtime-harness.sh serial-exec` interface against a local fake TCP serial console, then feed its captured gate output to the existing `flr0350_launch_gate.py --validate` command. Accept only a positively completed `stty -echo` exchange whose known command echo and single expected prompt form the entire setup response; fail closed on unexpected or trailing bytes before starting a fresh command capture.

**Tech Stack:** Bash, embedded Python socket client, Python unittest, existing FLR-0350 validator, Mini QEMU/QMP runtime scripts.

**Spec:** [FLR-0358 ticket](../../../work/tickets/FLR-0358-clear-serial-buffer-before-command.md).

## Global Constraints

- Work only in the canonical repository on the FLR-0358 feature branch; preserve all existing work.
- Do not relax the official marker parser or process/FIFO identity predicates.
- Validate the exact echo-off handshake; never discard arbitrary unverified serial bytes.
- The change is host-side QEMU harness only; do not change product source, Yocto recipe/layer, image, or build state.
- Use the existing Mac-to-Mini Git bundle flow and pinned Mini QEMU image; do not build another image.
- Use one fresh Mini runtime ID only after local checks and exact bundle/preflight; never reuse a consumed ID.
- Capture QMP still/eight frames, pixel summary, bounded logs, and exact cleanup; a pre-GO black frame is not a render verdict.

---

### Task 1: Add a public-interface serial capture regression

**Files:**
- Modify: `tests/test_qemu_runtime_harness.py`
- Test: `RuntimeHarnessTests.test_serial_exec_capture_passes_strict_gate_without_setup_preamble`
- Test: `RuntimeHarnessTests.test_serial_exec_fails_closed_on_unexpected_echo_off_response`

**Seam:** Invoke the real `serial-exec` CLI and real FLR-0350 validator. A loopback TCP server represents the external QEMU serial endpoint and sends a login prompt, the `stty -echo` response/prompt, and one deterministic gate marker. It does not mock or replace either production Python implementation.

- [x] Start a loopback listener in a test-owned thread and drive the actual helper through initial prompt, echo-off setup, and requested command.
- [x] Seed the echo-off reply with the observed setup transcript (`stty -echo` echo plus the expected prompt); send a valid launch marker and complete gate observation as the command result.
- [x] Assert the output file excludes the validated setup response and the official validator accepts the fresh gate output. Run against current code and observe the expected `marker-not-first` failure.
- [x] Add a case where unexpected text accompanies the echo-off response; assert the helper exits nonzero before sending the requested command. Current helper incorrectly sends it and returns PASS.

### Task 2: Implement the smallest validated capture boundary

**Files:**
- Modify: `scripts/qemu-runtime-harness.sh::serial_exec`
- Test: the two public-interface tests from Task 1

- [x] Validate that the echo-off reply contains exactly one expected prompt at the end and only the allowed `stty -echo` echo / CR-LF setup bytes before it; return `echo-off-response-unexpected` for unexpected or trailing bytes.
- [x] Only after that exact setup exchange passes, discard those verified setup bytes and send the requested wrapped command.
- [x] Keep existing prompt wait bounds, completion marker, return-code parsing, command limits, and strict host validator unchanged.
- [x] Run both tests; valid capture and strict validator pass, while unexpected setup response fails closed.

### Task 3: Run local gates and commit the harness-only change

**Files:**
- Verify: `scripts/qemu-runtime-harness.sh`, `tests/test_qemu_runtime_harness.py`, ticket, log, `TASKS.md`, this plan

- [x] Run focused and full Python tests, `bash -n scripts/qemu-runtime-harness.sh`, `bash tests/test-qemu-runtime-harness.sh`, and `bash work/commands/FLR-0350-run-sync-producer.sh --check`.
- [x] Run canonical guard, ticket checkpoint, privacy, file-size, staged-whitespace, and scoped Markdown-link checks; record the unrelated repository-wide missing-link baseline without repairing unrelated tickets. Canonical/checkpoint/privacy/file-size/staged whitespace/scoped links pass; global Markdown has nine unrelated existing failures.
- [x] Commit only FLR-0358 files locally on `feature-flr-0358-clear-serial-buffer`; do not push (`3a54e83`).

### Task 4: Transfer and validate once on Mini QEMU

**Files:**
- Use: `scripts/handoff-fluorite-bundle.sh`, `scripts/reuse-mini-build-receiver.sh`, `work/commands/FLR-0350-run-sync-producer.sh`, existing QMP capture/pixel/cleanup harnesses

- [ ] Transfer the exact committed tip as a Git bundle to the established Mini receiver; verify bundle hash, receiver tip/cleanliness, pinned image artifacts, ports/processes, and a fresh absent evidence directory before launch.
- [ ] Use one fresh FLR-0358 run ID and the existing Mini QEMU image; no BitBake, Devtool, product build, or image change is in scope.
- [ ] Require the official FIFO gate to pass before GDB attach/GO. If it fails, retain evidence and stop without retrying that ID.
- [ ] Capture QMP full-frame still/eight frames, analyze the fixed 3D ROI, preserve the bounded serial/GDB result, and prove targeted QEMU/QMP/app cleanup.
- [ ] Classify every screen as pre-GO or post-GO. Only post-GO product pixels may update the Sequoia/2D+3D capability verdict.

**Acceptance:** The serial helper cannot carry the verified echo-off preamble into the observer capture, cannot silently discard an unexpected setup response, the unchanged official FIFO/identity gate is exercised once on Mini, and runtime evidence distinguishes a harness stop from a production render result.
