# FLR-0358 — clear serial receive bytes before each command

- Status: Waiting
- Priority: High; blocks the next bounded production runtime observation
- Owner: QEMU serial harness / runtime-gate roles
- Created: 2026-09-29
- Discovered by: [FLR-0356](FLR-0356-stage-fifo-observer-before-qemu.md)
- Parent retrospective: [FLR-0357](FLR-0357-refresh-3d-visibility-retrospective.md)
- Plan: [FLR-0358 plan](../../docs/superpowers/plans/2026-09-29-flr0358-serial-capture-boundary.md)
- Working log: [FLR-0358 log](../logs/2026-09-29-flr0358.md)
- Branch: `feature-flr-0358-clear-serial-buffer` (created from the FLR-0357 closeout commit)
- Follow-up: [FLR-0359 — use the committed QEMU runtime helper](FLR-0359-use-committed-qemu-runtime-helper.md)

## Objective

Keep each `serial-exec` output file scoped to the requested command. Positively
observe completion of the echo-off setup and its expected prompt, consume only
that completed setup response, and establish a fresh capture boundary before
sending the requested command. Do not blindly discard arbitrary serial bytes.
Preserve the strict FLR-0350 marker parser and process/FIFO identity checks.

## Facts

- FLR-0356 staged all 11 serial commands before QEMU start and successfully ran
  the FIFO observer command.
- The observer record's PID, start time, UID, command, read syscall, and FIFO
  device/inode match the launch record and run-owned gate.
- The host rejected the serial file with `marker-not-first`. The captured file
  begins with the prior `stty -echo` response and prompt before the observer
  marker.
- `scripts/qemu-runtime-harness.sh` clears its receive buffer before sending
  `stty -echo`, accumulates that response/prompt, then sends the requested
  command without clearing it. `scripts/flr0350_launch_gate.py` intentionally
  requires the marker as the first token.
- `flr0356-0001` is consumed. Its QMP screenshot was taken before GO and is not
  a renderer verdict.
- The loopback red/green tests invoke the public serial helper and unchanged
  validator. Before the fix, the valid setup transcript reproduced
  `marker-not-first`, and unexpected setup chatter was accepted with
  `serial-exec=PASS`.
- FLR-0358's exact bundle reached the clean fixed Mini receiver at commit
  `5456ed220d5a657fc14a8012691c8448c8472434` (SHA-256
  `15c71ea1d97ef7dc60de6af1ea839f472e7866534d9213bbec1fd39b9f61f87c`).
- The one runtime attempt, `flr0358-0001`, staged all 11 guest commands and
  reached `FLR0350_LAUNCH_WRAPPER=READY`, but the official validator stopped at
  `marker-not-first` before GDB attach or GO. Its captured stream had three
  tokens before the observer marker; the first was `stty`.
- Runtime provenance explains the repeat: both the runner and QEMU starter
  selected the prior FLR-0335 evidence copy (`339472336f14387fd1b72c3d702e510de19ff710c5c203441733a7a59d79aa6d`),
  while the committed helper in the exact receiver was
  `088e8e39ed1fc7dce175ad0fd2a027325b04815c68337a9e52fead2c9fb64fee`.
  Therefore the new serial capture boundary was not exercised on this QEMU run.
- The live receiver's pre-handoff HEAD was `51100f50cef01f88cfd048ae2c30344ad342b0e1`,
  not the historical `5e46a1e…` cited by FLR-0351. Comparing its layer tree
  with the received tip shows an added committed `0327` diagnostic patch and
  bbappend registration, with no layer-file deletions; the exact receiver
  update passed and the post-handoff HEAD is the bundle tip.

## Visual evidence

- QMP-only full-frame still: `$EVIDENCE_ROOT/flr0358-0001/qemu/post-run.ppm`
  (1280×800; SHA-256
  `d4e96a65fd4f8e97bc1d762fc90cf2593bc2efb53a3125a72502fdae0f09395c`).
- The frame was captured during cleanup before GO. It is uniformly black:
  1,024,000 full-frame pixels and 768,000 pixels in the fixed lower 3D ROI,
  all black; chromatic pixels 0. The eight QMP frames have one unique hash.
- This is a pre-GO harness-stop frame, not evidence that the renderer or
  production Sequoia failed. The raw still and eight frames remain on Mini;
  the complete still was shown in the task. A local 8-second preview derived
  from the eight identical frames is outside Git.
- Teardown: QMP `quit` accepted; app stopped (`flutter_processes=0`),
  run-owned FIFO removed, QMP socket absent, and residual QEMU/runqemu/
  flutter-auto/BitBake processes 0.

## Competing approaches

1. **Selected: consume the response only after confirming the echo-off setup
   completion/prompt, then start a fresh command capture.** This preserves
   strict marker parsing and fixes the earliest proven seam without hiding an
   incomplete or unexpected serial handshake.
2. **Defer: accept shell-prompt text before a marker in the parser.** This
   weakens the output contract and could hide stale/unrelated serial bytes.

## Scope

- Add a red regression seeded with the echo-off response and prompt. It must
  prove the current path contaminates the next capture, and the fix starts the
  capture only after the expected setup boundary; unexpected/missing setup
  completion must fail closed rather than discard arbitrary bytes.
- Require the requested command's observer marker exactly once, as the first
  captured token, and verify that its complete record still passes the
  unchanged strict parser and identity checks.
- Apply the smallest serial-helper change; preserve command status framing,
  serial prompt handling, and all FLR-0350 launch/FIFO identity predicates.
- Run local focused tests, shell syntax, runner `--check`, privacy,
  checkpoint, and staged-diff checks.
- Make the established bundle preflight work with the actual split Mini layout:
  resolve the AGL `external/poky` environment from a bounded, unique candidate
  matched to the fixed build's persisted `TEMPLATECONF`; stop with a specific
  reason before receiver mutation if it is missing, mismatched, or ambiguous.
- After exact committed bundle handoff and Mini preflight, use exactly one new
  run ID. Require the official FIFO gate to pass before GDB attach/GO; if any
  later gate fails, retain evidence and create a new task rather than reusing
  the ID.
- Capture QMP still/eight frames/video and fixed full/3D ROI pixel summaries;
  prove targeted app/FIFO/QMP/QEMU cleanup.

## Out of scope

- Flutter/Filament source, product recipes, camera/light/material/texture,
  image/profile changes, BitBake/Devtool/build, parser relaxation, and any
  consumed run ID.
- Treating a successful serial gate or a pre-GO black frame as 3D acceptance.

## Success criteria

- The regression is red against current behavior with the retained echo-off
  response/prompt, then green after the explicit setup/capture boundary fix.
- The fixed helper does not accept a missing/ambiguous setup prompt by clearing
  the buffer; it fails closed. The fresh capture contains exactly one marker
  and no setup preamble.
- The strict parser accepts a fresh observer log only when the launch/process/
  actual-FD/FIFO identity predicates all match.
- One fresh Mini run reaches the official gate and then the next bounded
  diagnostic boundary, or records one precise fail-closed reason without retry.
- QMP evidence and zero-residue teardown are recorded; production 3D status is
  decided only from pixels captured after GO.

## Impact and risk

- Build-time: none; this changes only the Mac/Mini host-side diagnostic runner.
- Packaging: none; no recipe, package, rootfs, or image changes.
- Product runtime: none. The helper may now fail closed before GDB/GO if the
  guest emits an undocumented echo-off transcript; that is preferable to
  accepting a contaminated observation and must be diagnosed from a fresh
  one-shot run.
- Integration risk: bounded to the serial prompt protocol. The loopback
  regression fixes the accepted transcript shape; Mini evidence must confirm
  the same deployed console response before interpreting the gate result.

## Runtime attempt disposition

The local fix and tests are committed, but the fresh Mini runtime selected a
pinned previous-run helper rather than the exact committed helper. The
independent source-selection correction and its new one-shot runtime gate will
be tracked by FLR-0359. `flr0358-0001` is consumed and must not be retried.
