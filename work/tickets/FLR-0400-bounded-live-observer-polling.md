# FLR-0400 — bounded live-observer polling

- Status: In Progress
- Priority: High
- Created: 2026-10-02
- Owner: Mini QEMU / guest Flutter+GDB / serial-exec / QMP evidence roles
- Branch: `feature-flr-0400-snapshot-deadline-polling` (local only; no push)
- Milestone base: `dev-flr-0396`
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
  helpers. The milestone base remains `dev-flr-0396`; this local stacked branch
  is a documented exception to the normal feature-from-dev rule. Review only
  the diff from the FLR-0399 dependency commit.

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
- The first identity-bracketed live frame now gets a full still and one
  four-frame/one-second QMP video. Later READY/PRESENT captures remain stills;
  no more than one live video is produced per run.
- Allowed fresh run `flr0400-0001` through the shared FLR-0399 observer/start
  implementation. Its run directory and QMP socket are ticket-scoped
  (`flr0400-0001/qemu/qmp-0400.sock`); FLR-0399 module/protocol markers remain
  implementation names only. No product source, image, or build input changed.
- TDD red/green covered WAITING preservation, one-shot guest commands, unique
  READY/PRESENT serial labels, WAITING→READY→PRESENT, the same deadline across
  both gates, one early video, no post-deadline read/capture, and evidence
  preservation before exactly-once teardown. Current focused result: 44/44.
- GPT-6.1 Sol's read-only review caught the repeated-PRESENT evidence-label
  collision; numbered labels and an adapter-level WAITING→PRESENT regression
  were added before continuing.

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
- Mac read-only process scan found no QEMU/runqemu/BitBake; the existing
  Podman machine and Docker helper were not touched. Mini ownership and
  process/port state still require a fresh preflight before any QEMU run.
- Official bundle handoff, fresh Mini preflight, one QEMU run, full-frame still
  and video review, runtime-evidence preservation, and independent cleanup
  checks remain pending.

### Act

- If a live frame is captured, classify its full-frame and Sequoia/HUD regions
  without promoting READY or a diagnostic fixture to product success.
- If still UNKNOWN, use the preserved first boundary to open the next focused
  ticket; never retry `flr0399-0001` or weaken the serial protocol.

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
FLR-0400 run ID is used. Never retry this ID after any start/observer attempt.

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
