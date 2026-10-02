# FLR-0400 — bounded live-observer polling

- Status: In Progress
- Priority: High
- Created: 2026-10-02
- Owner: Mini QEMU / guest Flutter+GDB / serial-exec / QMP evidence roles
- Branch: `feature-flr-0400-snapshot-deadline-polling` (local only; no push)
- Milestone base: `dev-flr-0396-sequoia-material-parity` at `b0b7f8ede77178412240475dd582ffa5641c309d`
- Immediate dependency: FLR-0399 at `9db57cfe92deddf4bc2037e53c871ac7acdb0657`
- Plan: [FLR-0400 implementation plan](../../docs/superpowers/plans/2026-10-02-flr0400-snapshot-deadline-polling.md)
- Working log: [FLR-0400 working log](../logs/2026-10-02-flr0400.md)
- Related failed observation: [FLR-0399](FLR-0399-capture-live-sequoia-on-0334-image.md), run `flr0399-0001`
- Reused image: FLR-0396 patch 0334; rootfs SHA-256 `80935c3f9fa81da66f068821637f512749602c701baa37e91bf777b8cf15c44c`
- Fresh run reserved: `flr0400-0001`

## Objective

On the same already-built 0334 candidate, make a bounded and attributable live
QMP observation possible even when Flutter has not yet emitted READY. Each
guest serial request must return one state snapshot; the host polls under one
monotonic deadline, captures the first identity-bracketed WAITING frame, then
retains the existing READY/first-PRESENT captures and evidence-before-teardown
contract.

This is an observer/runtime-evidence task, not a product-rendering fix. Do not
change scene/material/texture/camera/light, Flutter behavior, recipes, image,
build inputs, or the Mini cache. Do not rebuild. Gate A remains PASS only for
recognizable colored production Sequoia pixels in a complete live frame; a
WAITING frame is diagnostic evidence only. Gate B (same-frame HUD+Sequoia)
remains separately owned by FLR-0398 after Gate A is established.

## Facts, hypotheses, and unknowns

### Facts

- FLR-0399 used the exact 0334 image and launched `/usr/bin/flutter-auto` as
  UID 1001. The sampled process remained live while READY and present counters
  were zero and SUN setup was recorded.
- The guest state gate can loop 100 times with several `grep`/`awk` processes
  and `sleep 0.2` per iteration. The host serial request is capped at 40
  seconds; the outer FLR-0399 observer deadline was 48 seconds.
- FLR-0399's ready request timed out at 39.5266 seconds. The next serial call
  correctly rejected a late `WAITING` response as unexpected echo-off output.
  Evidence collection failed, teardown passed, and no live Flutter frame was
  captured. The post-launch visual result is UNKNOWN.
- The parser currently converts valid WAITING to TIMEOUT and the controller
  returns rather than polling it. The serial fail-closed contract itself is
  not implicated and must remain strict.
- Source changes are stacked on FLR-0399 because the new observer depends on
  its committed exact-image startup, process-identity, serial, QMP, and cleanup
  helpers. The actual milestone base is
  `dev-flr-0396-sequoia-material-parity` at `b0b7f8e…`; the previous shorthand
  `dev-flr-0396` was incorrect. This local stacked branch is a documented
  exception to the normal feature-from-dev rule. Review only the diff from the
  FLR-0399 dependency commit.

### Hypotheses

1. The long guest-side polling transaction is the immediate orchestration
   defect: its response can outlive the 40-second parent transaction and
   contaminate the next serial phase. One-snapshot requests plus host-side
   polling should remove this failure mode.
2. Serial framing or guest responsiveness may independently be slow or broken.
   If a one-snapshot request still times out, its bounded setup/command logs
   will distinguish that from the removed guest loop; do not relax echo,
   marker, or identity validation.

### UNKNOWN

- Whether the exact 0334 image shows colored production Sequoia while Flutter
  is live.
- Whether the first failure was solely guest-loop latency or also involved
  serial framing/guest responsiveness.
- Whether current Flutter HUD and Sequoia can coexist in the same frame; this
  is not measured by this ticket's visual-isolation observation.

## Plan / Do / Check / Act

### Plan

- Replace the in-guest polling loop with one bounded snapshot per serial call.
- Poll every 2 seconds on the host with one absolute monotonic deadline of
  120 seconds and a maximum 15-second state-request timeout. WAITING never
  resets the deadline.
- Capture a complete QMP still and one short four-frame video at the first
  live sample (WAITING if that is first, otherwise READY); use stills at later
  READY/first-PRESENT points. Bracket each capture by the same PID/UID/start
  token. Preserve bounded guest/kernel evidence before exact teardown.
- Keep implementation and product results separate. No BitBake build; use
  `flr0400-0001` only after fresh Mini preflight.

### Do

- Replaced the guest's 100-pass READY/PRESENT loop with one state snapshot per
  serial request. WAITING remains a live state; the host polls READY and
  PRESENT every 2 seconds under one absolute 120-second monotonic deadline.
- Capped each state snapshot at 15 seconds and gave repeated READY and PRESENT
  requests unique immutable evidence labels. Strict echo/marker checks and
  evidence overwrite rejection remain unchanged.
- Captured the first identity-bracketed live QMP frame as a full still plus
  four-frame/one-second video; later READY/PRESENT frames are stills. No more
  than one live video is produced per run.
- Transferred the committed observer by the official bundle helper. Fresh Mini
  preflight verified the exact 0334 image and run inputs, clean ownership,
  free ports/socket, and unused `flr0400-0001`; no build was run.
- Ran exactly one Mini QEMU observation on the existing image. The observer
  reached a PID/UID/start-bracketed READY frame, then stopped at its one
  120-second deadline when Present had not returned. No retry or second QEMU
  was started.
- No product source, image, build input, or Mini cache changed.

### Check

- Focused observer tests: 44/44 PASS. Canonical guard, privacy, shell syntax
  across 59 files, MCP smoke (52/52), and 2,048-file size gate PASS.
- `make verify`: 194/195 tests pass; one pre-existing, unrelated FLR-0397
  stale run-ID invocation fails in
  `test_serial_exec_capture_passes_strict_gate_without_setup_preamble`.
- QEMU harness, runtime-log-slice, Devtool finish/rebase, Mini recipe-patch,
  and Mini bundle-handoff independent gates PASS. Markdown check has 11
  historical missing targets outside this ticket/plan/log.
- Initial runtime-checkpoint gate correctly rejected the working log's
  noncanonical `Inference and competing hypothesis` / `Check / Act` headings;
  a second check required explicit `UNKNOWN` in the working log. Both were
  corrected, and the checkpoint now passes with exactly one active ticket.
  After the final documentation update, checkpoint, privacy, canonical, and
  staged-whitespace checks all PASS.
- Fresh Mini preflight and official bundle receiver validation passed. One
  QEMU run produced `PRESENT_DEADLINE_EXPIRED`; `READY=1`,
  `PRESENT_BEGIN=1`, `PRESENT_RETURN=0`, and `SUN=1` were sampled against the
  same live PID/UID/start identity.
- The WAITING full frame is black and byte-identical to the pre-launch frame.
  The READY full frame shows the CPU/GPU/FPS HUD and Scenes control, while the
  fixed Sequoia ROI `(440,220,400,360)` is uniformly black (0 changed, edge,
  or chromatic pixels). This run therefore does not pass the colored-Sequoia
  visual gate; it does establish visible Flutter HUD output on this image and
  profile. See [FLR-0400 evidence](../evidence/FLR-0400-0001.md).
- The bounded kernel journal contains an `FEngine::loop` page-fault/Oops at
  `02:44:30 UTC`; the focused coredump query is `EMPTY`. The instruction bytes
  include `ff <cf>` and low RSP bits match CR2, but these signatures do not
  identify the faulting operation or cause. Do not infer LLVM/WSI causality.
- The GDB log has no selected stack: `/usr/bin/gdb --batch -ex run` was still
  executing the inferior when the observer collected evidence, so the queued
  `thread apply all bt 8` did not execute. This is the next debugger-supervision
  discriminator, not evidence against WSI or another FEngine path.
- QMP quit, exact target cleanup, and independent postflight passed: no target
  process, QMP socket, or forwarded-port residue. The existing Mac Podman
  machine and Docker helper were not touched. No image was copied to Mac.
- The QMP still/video derivatives are small local review artifacts; the raw
  Mini PPMs and runtime logs remain under the fixed `$BUILD_EVIDENCE` role.

### Act

- The observer repair is demonstrated on one exact-image run: WAITING/READY
  polling, full-frame QMP still/video, pre-teardown evidence collection, and
  exact cleanup all completed or ended at the declared deadline. The product
  renderer did not pass: the Sequoia ROI is black, Present is unmatched, and
  an Oops is recorded. These are separate results, not one established cause.
- Do not retry `flr0400-0001` or weaken the serial protocol. Open the separate
  FLR-0401 task to change only debugger supervision and capture one selected
  live `FEngine::loop` stack at the first identity-stable unmatched Present.
- Keep Gate A (original-material colored Sequoia) and Gate B (same-frame HUD +
  Sequoia) unproven. The overall user goal remains open.

## Fresh-run procedure

After the scoped local commit has been transferred with the official bundle
helper and the exact Mini roles/image/process/port/socket/evidence checks pass:

```sh
FLR0399_RUN_ID=flr0400-0001 bash work/commands/FLR-0399-qemu-start.sh preflight
FLR0399_RUN_ID=flr0400-0001 bash work/commands/FLR-0399-qemu-start.sh start
python3 scripts/flr0399_live_capture.py observe \
  --run-id flr0400-0001 --evidence-root "$BUILD_EVIDENCE" \
  --run-dir "$BUILD_EVIDENCE/flr0400-0001/qemu" \
  --qmp "$BUILD_EVIDENCE/flr0400-0001/qemu/qmp-0400.sock"
```

The helper variable retains its FLR-0399 name for compatibility; only the new
FLR-0400 run ID is used. This procedure has already consumed
`flr0400-0001`; never run it again or retry that ID. Use a new ticket/run ID
for every later observation.

## Impact and acceptance

- **Build-time / packaging:** none; exact existing image reused.
- **Runtime:** observer timing only; no product rendering or input suppression.
- **Integration risk:** run-ID and artifact uniqueness, repeated-poll labels,
  deadline enforcement, and identity bracketing must remain fail-closed.
- **Scoped success:** deterministic tests prove WAITING parsing, prompt one-shot
  guest snapshots, early live capture, monotonic deadline, exactly-once
  evidence preservation/teardown, and no post-deadline read/capture; one
  Mini run records full QMP evidence and clean teardown or a precise stop point.
- **User's product goal:** not complete until original Sequoia material/texture/
  lighting, same-frame HUD composition, view/input/repaint stability, five
  minutes of progressing present, and two independent boots pass on one final
  candidate image. This observer ticket alone cannot satisfy that goal.
