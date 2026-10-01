# FLR-0399 — one-run live Sequoia capture on the 0334 image

> Reuse the exact FLR-0396 Mini image. Fix the observation/evidence path only;
> do not modify Sequoia material, camera, texture, light, app composition, or
> build inputs. Gate A (colored Sequoia) and Gate B (HUD+Sequoia composition)
> are independent.

**Ticket:** `work/tickets/FLR-0399-capture-live-sequoia-on-0334-image.md`

**Branch:** `feature-flr-0399-live-qmp-capture` (local only)
**Image rootfs SHA-256:** `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`

## Chosen implementation path

Compared two options:

1. **Manual-only path edit:** point the old READY gate at the GDB log. This is
   the smallest change, but it leaves PID bracketing, live-vs-post-exit
   classification, persistence-before-teardown, and one-time cleanup as manual
   steps that can drift again.
2. **Ticket-scoped one-run controller over the existing runtime workflow
   (selected):** a small public function accepts bounded guest-state reads,
   process identity, QMP capture, evidence persistence, and teardown adapters.
   Tests exercise the contract with fakes; the Mini run uses the existing
   `qemu-runtime-harness.sh`/serial-exec/QMP interfaces. No new generic QEMU
   framework or image build is introduced.

## Tasks

### 1. Confirm fixed baseline and ticket scope

- [x] Run the canonical repository guard and inspect the FLR-0396-0001
  manifest/command history.
- [x] Confirm the 0334 rootfs/kernel/qemuboot hashes. PASS: all three
  independently rehashed from the fixed Mini deploy role. The old FLR-0396
  run directory and saved start command are absent; zero target processes were
  found. Port checks remain part of the immediate start preflight.
- [ ] Before the new run, recheck hashes and QEMU/port/socket state, then
  allocate one fresh FLR-0399 evidence directory. Never copy the image to Mac.
  A ticket-scoped starter resolves the exact pinned image and creates
  `$BUILD_EVIDENCE/flr0399-0001/qemu` only at start.

### 2. TDD the live-observer contract

- [x] Add failing unit tests for unreadable/missing log, malformed runtime
  sample, READY/live identity capture, first-present capture, process exit,
  deadline, post-exit classification, and teardown-once behavior.
- [x] Implement the smallest FLR-0399 controller that consumes the same
  configured guest-log path for READY/present state and GDB output.
- [x] Verify a missing log emits one specific error before any numeric parse
  or repeated polling; use bounded tails, not whole-log reads.
- [x] Verify every QMP capture is identity-bracketed and the post-exit state
  cannot be labeled live or pass Gate A.
- [x] Keep existing QMP/serial-exec helpers and general runtime harness intact
  unless a focused test proves their contract blocks this one-run path.
- [x] Correct the evidence-root role contract and add the FLR-0399-only
  exact-image starter. Focused tests cover the path mapping and shell syntax;
  no general harness or image change was required.

### 3. Run once on Mini, with no rebuild

- [ ] Review the exact 0334 image hashes and confirm no residual QEMU,
  runqemu, flutter-auto, QMP socket, or forwarded-port listener.
- [ ] Run the committed ticket-specific preflight/start helper on Mini; first
  smoke-test the guest command channel, then launch Example Demo/GDB using the
  ticket-scoped, single-source log path.
- [ ] Trigger one full QMP capture at READY while the exact PID/UID/start
  identity is live; capture again at the first present return only if the same
  process remains live. Record the result and reject any post-exit sample.
- [ ] Before quitting QEMU, transfer bounded GDB/inferior output and focused
  kernel Oops/coredump evidence into the one Mini evidence directory.
- [ ] Record one full frame/video, process identities before/after capture,
  READY/present counters, focused fault excerpt, and artifact hashes. Inspect
  the entire frame and fixed Sequoia/HUD ROIs.
- [ ] Stop only the recorded Flutter/GDB identities and exact QEMU via QMP;
  independently verify no process/socket/port residue.

### 4. Check and close this unit

- [x] Run focused tests, canonical/privacy/checkpoint/diff checks, and
  `make verify`; report the known FLR-0397 test contract independently. The
  15 focused tests and independent MCP/QEMU/Devtool/bundle/file-size gates
  pass. `make verify` reaches 163 tests but fails one existing FLR-0397 test
  invocation missing its required run ID; global Markdown validation also
  reports 11 pre-existing missing FLR-0338/0339/0391/0395 targets. Both are
  kept separate from this ticket.
- [ ] Commit ticket, controller/tests, Mini evidence manifest, and dashboard
  locally. Do not push.
- [ ] If Gate A passes, leave Gate B for FLR-0398 with image/material/camera/
  light held fixed. If the live frame is negative or UNKNOWN, base the next
  ticket on first-fault evidence; do not edit unrelated axes here.

## Validation and evidence requirements

- A colored fixture pixel is not colored production Sequoia.
- READY/binding/SUN markers prove setup reachability, not rendered pixels.
- A live frame requires the same PID, UID, and process start token before and
  after QMP capture. The full screenshot must remain attributable to the exact
  image and run.
- Native-above-parent presentation can hide the HUD while Flutter continues
  running. That visual-isolation measurement does not mean Flutter 2D was
  disabled, and it does not pass HUD+Sequoia composition.
- If the renderer faults before any valid live capture, retain the failure
  state and say Gate A is UNKNOWN; never substitute the post-exit black frame.
